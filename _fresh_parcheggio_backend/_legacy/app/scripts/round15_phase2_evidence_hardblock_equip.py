"""ROUND 15 — Fase 2 / Evidence script for hard-block equip.

Demonstrates the server-side HTTP 400 + `reason_it` Italian rejection
when a Mage tries to equip a heavy-armour piece.

Procedure:
    1. Create (idempotent upsert) a test-only item template
       `legacy-plate-cuirass-test-r15` with `armor_tags=["heavy"]` and
       `is_universal=false`. Marked `is_test=true` so production catalog
       queries never surface it.
    2. Grant 1 unit of that item to the tester guild's inventory.
    3. Login as tester via API → POST equip on a Mage adventurer.
    4. Print the full HTTP response (status + body).
    5. NO hard delete: the test item stays in inventory (unequipped),
       and the catalog row is soft-flagged inactive at the end. Idempotent.

Run:
    cd /app/backend
    python3 -m app.scripts.round15_phase2_evidence_hardblock_equip
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone

import requests
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv


TEST_ITEM_SLUG = "legacy-plate-cuirass-test-r15"


async def _ensure_test_item(db) -> dict:
    existing = await db.items.find_one({"slug": TEST_ITEM_SLUG}, {"_id": 0})
    if existing:
        # Reactivate + ensure level_requirement allows L1 mage (override
        # rarity-derived default in level_gate.py).
        await db.items.update_one(
            {"slug": TEST_ITEM_SLUG},
            {"$set": {
                "is_active": True,
                "rarity": "Common",
                "required_adventurer_level": 1,
                "level_required": 1,
                "level_requirement": 1,
                "level_band": "T1",
                "armor_tags": ["heavy", "plate"],
                "is_universal": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        return await db.items.find_one({"slug": TEST_ITEM_SLUG}, {"_id": 0})

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "slug": TEST_ITEM_SLUG,
        "name": "Plate Cuirass (R15 test)",
        "item_type": "armor",
        "slot": "armor",
        "rarity": "Common",
        "armor_tags": ["heavy", "plate"],
        "stat_tags": ["endurance"],
        "recommended_classes": ["warrior", "paladin", "berserker"],
        "class_tags": ["warrior", "paladin", "berserker"],
        "role_tags": ["tank"],
        "is_universal": False,
        "required_class_optional": None,
        "endurance_bonus": 4,
        "strength_bonus": 2,
        "intellect_bonus": 0,
        "agility_bonus": 0,
        "faith_bonus": 0,
        "affects_combat": True,
        "affects_economy": False,
        "is_active": True,
        "is_test": True,
        "required_adventurer_level": 1,
        "level_required": 1,
        "level_requirement": 1,
        "level_band": "T1",
        "created_at": now,
        "updated_at": now,
    }
    await db.items.insert_one(doc)
    return doc


async def _grant_inventory(db, guild_id: str, item_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": item_id},
        {
            "$inc": {"quantity": 1},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "instance_id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item_id,
                "acquired_at": now,
                "source": "r15_phase2_evidence",
                "bind_state": "unbound",
                "is_bound": False,
                "disenchanted_at": None,
                "refinement_level": 0,
                "enchants": [],
                "affixes": [],
                "reroll_count": 0,
            },
        },
        upsert=True,
    )


async def main():
    load_dotenv("/app/backend/.env")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
    mage = await db.adventurers.find_one(
        {"guild_id": guild["id"], "class_name": "Mage"}, {"_id": 0},
    )
    print(f"=== Targets ===")
    print(f"  guild: {guild['name']} ({guild['id']})")
    print(f"  mage:  {mage.get('name')} (id={mage['id']}, level={mage.get('level')})")

    item = await _ensure_test_item(db)
    await _grant_inventory(db, guild["id"], item["id"])
    print(f"  test item granted: {item['slug']} (id={item['id']}, armor_tags={item['armor_tags']})")
    print()

    # ── Login and call equip ─────────────────────────────────────────────
    api_url = "http://localhost:8001/api"
    sess = requests.Session()
    r = sess.post(
        f"{api_url}/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    # CSRF double-submit: the login response already set the csrf cookie on
    # the session jar; we still call /auth/csrf to materialise the token
    # value (NOT httpOnly) and echo it in the X-CSRF-Token header.
    rc = sess.get(f"{api_url}/auth/csrf", timeout=10)
    csrf = rc.json().get("csrf_token", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf,
    }

    print(f"=== POST /api/adventurers/{mage['id']}/equip (heavy armour on Mage) ===")
    r = sess.post(
        f"{api_url}/adventurers/{mage['id']}/equip",
        json={"item_id": item["id"], "slot": "armor"},
        headers=headers,
        timeout=15,
    )
    print(f"  HTTP status: {r.status_code}")
    try:
        body = r.json()
    except Exception:
        body = r.text
    print(f"  body: {json.dumps(body, indent=2, ensure_ascii=False)}")
    print()

    # ── Cleanup: soft-disable the test template; inventory row stays. ────
    await db.items.update_one(
        {"slug": TEST_ITEM_SLUG},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    print(f"=== Cleanup: test item soft-disabled (is_active=false), inventory row preserved (no hard delete). ===")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
