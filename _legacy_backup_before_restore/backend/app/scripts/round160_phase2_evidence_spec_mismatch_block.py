"""ROUND 16.0 — Phase 2 evidence: equip validator v2 spec-mismatch BLOCK.

Demonstrates that a tester adventurer holding `specialization_slug =
berserker_spec` (Warrior class) is HARD-BLOCKED when attempting to
equip an item that requires `assassin_spec` (Rogue class).

The script is idempotent and **non-destructive**:
  * Creates a temporary item in `items` with a uuid id (no slug
    collision with seeded content).
  * Grants ONE copy to the tester's inventory (`inventory_items`).
  * Calls the live POST /equip endpoint.
  * Soft-deletes the temp inventory row by setting `deactivated_at`
    (NEVER deletes from `items` catalog).

Usage:
    python -m app.scripts.round160_phase2_evidence_spec_mismatch_block
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


TESTER_EMAIL = "tester@orbus.test"
TESTER_PASSWORD = "password123"


async def _setup() -> tuple[str, str, str, str]:
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]

    # 1. Find tester guild + a Warrior+berserker_spec adventurer.
    user = await db.users.find_one({"email": TESTER_EMAIL}, {"_id": 0, "id": 1})
    guild = await db.guilds.find_one({"owner_user_id": user["id"]},
                                     {"_id": 0, "id": 1})
    adv = await db.adventurers.find_one(
        {"guild_id": guild["id"],
         "class_slug": "warrior",
         "specialization_slug": "berserker_spec"},
        {"_id": 0, "id": 1, "name": 1, "class_slug": 1,
         "specialization_slug": 1, "level": 1},
    )
    assert adv, "No warrior+berserker_spec adventurer found on tester"
    print(f"[setup] Adventurer: {adv['name']} (Lv{adv.get('level')}) "
          f"class={adv['class_slug']} spec={adv['specialization_slug']}")

    # 2. Create temp item — rogue weapon requiring assassin_spec.
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    temp_item = {
        "id": item_id,
        "slug": f"r160-evidence-spec-mismatch-{item_id[:8]}",
        "name": "Lama del Patto Spettrale",
        "name_it": "Lama del Patto Spettrale",
        "item_type": "weapon",
        "rarity": "rare",
        "level_requirement": 1,
        "required_level": 1,
        "class_tags": ["rogue"],
        "recommended_classes": ["rogue"],
        "specialization_unlocks": ["assassin_spec"],
        "weapon_tags": ["dagger", "poison"],
        "armor_tags": [],
        "stats": {"agility": 3, "strength": 1},
        "is_test": True,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        # Round 16.0 evidence flag (lets us locate & sweep later).
        "round160_evidence": True,
    }
    await db.items.insert_one(temp_item)
    print(f"[setup] Temp item created id={item_id}")

    # 3. Grant 1 copy in tester inventory.
    inv_id = str(uuid.uuid4())
    inv_doc = {
        "id": inv_id,
        "guild_id": guild["id"],
        "item_id": item_id,
        "quantity": 1,
        "is_bound": False,
        # R6B schema uses `acquired_at` (the canonical timestamp).
        "acquired_at": now,
        "obtained_from": "round160_evidence_script",
        "is_test": True,
        "created_at": now,
        "updated_at": now,
    }
    await db.inventory_items.insert_one(inv_doc)
    print(f"[setup] Inventory grant id={inv_id}")

    return user["id"], adv["id"], item_id, inv_id


def _login() -> str:
    r = requests.post(
        f"{os.environ.get('BACKEND_URL', 'http://localhost:8001')}/api/auth/login",
        json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _attempt_equip(token: str, adv_id: str, item_id: str) -> dict:
    base = os.environ.get("BACKEND_URL", "http://localhost:8001")
    r = requests.post(
        f"{base}/api/adventurers/{adv_id}/equip",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={"item_id": item_id, "slot": "weapon"},
        timeout=10,
    )
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}
    return {"http_status": r.status_code, "body": body}


async def _teardown(inv_id: str, item_id: str) -> None:
    """Soft-delete: deactivate temp inventory row and temp item.
    NEVER hard-delete (R16 invariant)."""
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    now = datetime.now(timezone.utc)
    await db.inventory_items.update_one(
        {"id": inv_id},
        {"$set": {"deactivated_at": now, "is_active": False}},
    )
    await db.items.update_one(
        {"id": item_id},
        {"$set": {"is_active": False, "deactivated_at": now}},
    )


async def main() -> int:
    load_dotenv()
    user_id, adv_id, item_id, inv_id = await _setup()
    try:
        token = _login()
        result = _attempt_equip(token, adv_id, item_id)
        print()
        print("=" * 60)
        print("EQUIP ATTEMPT (spec_mismatch BLOCK expected)")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        # Expect a 4xx with reason that hints at the required spec.
        ok = result["http_status"] >= 400 and result["http_status"] < 500
        if not ok:
            print("\n!! UNEXPECTED: equip did NOT block. Investigate.")
            return 2
        return 0
    finally:
        await _teardown(inv_id, item_id)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
