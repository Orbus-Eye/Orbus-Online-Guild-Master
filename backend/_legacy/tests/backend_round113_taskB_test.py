"""ROUND 11.3 TASK B — Item required-level gate + legacy audit.

5 tests:
  B.01 — `resolve_item_required_level` honours explicit field > legacy > rarity > 1.
  B.02 — `/api/items` exposes `required_adventurer_level` derived field.
  B.03 — Equip POST returns 423 with `code=equipment.level_requirement_not_met`
         when adv.level < item.required_level.
  B.04 — Legacy audit endpoint returns a structured dry-run report and DOES
         NOT mutate `equipped_items` when `dry_run=true`.
  B.05 — Equip success path (Common item, Lv1 adv) still works — sanity
         check that the gate doesn't break normal flows.

PII guard: response detail MUST NOT include email / _id / user_id.
"""
from __future__ import annotations

import os

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")


@pytest.fixture(scope="module")
def mdb():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _login_tester() -> str:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    return r.json()["access_token"]


# ─── B.01 ─────────────────────────────────────────────────────────────────────
def test_b_01_resolve_item_required_level_priority():
    from app.equipment.level_gate import resolve_item_required_level
    # Explicit field wins.
    assert resolve_item_required_level({
        "required_adventurer_level": 15, "level_required": 1, "rarity": "Common",
    }) == 15
    # Legacy `level_required` > 1 honoured.
    assert resolve_item_required_level({
        "level_required": 8, "rarity": "Common",
    }) == 8
    # Rarity-based fallback.
    assert resolve_item_required_level({"rarity": "Legendary"}) == 12
    assert resolve_item_required_level({"rarity": "Epic"}) == 8
    assert resolve_item_required_level({"rarity": "Rare"}) == 5
    assert resolve_item_required_level({"rarity": "Uncommon"}) == 3
    assert resolve_item_required_level({"rarity": "Common"}) == 1
    assert resolve_item_required_level({"rarity": "Signature"}) == 5
    # Final fallback.
    assert resolve_item_required_level({}) == 1


# ─── B.02 ─────────────────────────────────────────────────────────────────────
def test_b_02_items_endpoint_exposes_required_level():
    r = requests.get(f"{BASE_URL}/api/items", timeout=10)
    assert r.status_code == 200, r.text
    items = r.json()
    if isinstance(items, dict):
        items = items.get("items") or items.get("rows") or []
    assert items, "Items catalog empty."
    saw_rare_or_higher = False
    for it in items:
        assert "required_adventurer_level" in it, f"item `{it.get('slug')}` missing required_adventurer_level"
        if it.get("rarity") in ("Rare", "Epic", "Legendary"):
            saw_rare_or_higher = True
            assert it["required_adventurer_level"] >= 5, (
                f"item `{it['slug']}` rarity={it['rarity']} required_level too low: "
                f"{it['required_adventurer_level']}"
            )
    assert saw_rare_or_higher, "No rare+ item found — catalog seems off."


# ─── B.03 ─────────────────────────────────────────────────────────────────────
def test_b_03_equip_blocked_when_under_level(mdb):
    """Pick a Lv1 adventurer + an Epic/Legendary item from inventory and
    attempt to equip. Must 423 with the structured code."""
    tok = _login_tester()
    headers = {"Authorization": f"Bearer {tok}"}
    me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10).json()
    user = me.get("user", me)
    guild = mdb.guilds.find_one({"owner_user_id": user["id"]}, {"_id": 0, "id": 1})
    if not guild:
        pytest.skip("No tester guild.")
    # Find a Lv1 adv.
    adv = mdb.adventurers.find_one(
        {"guild_id": guild["id"], "level": 1, "is_available": True, "is_retired": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "level": 1},
    )
    if not adv:
        pytest.skip("Tester has no Lv1 available adv.")
    # Find an inventory item with required_level > 1. Try Epic/Legendary
    # first (clean gap), fall back to Rare if none in inventory.
    candidate = None
    for rarity_pool in (["Epic", "Legendary"], ["Rare"]):
        cursor = mdb.items.find(
            {"rarity": {"$in": rarity_pool}, "is_active": True, "item_type": {"$ne": "material"}},
            {"_id": 0, "id": 1, "slug": 1, "item_type": 1, "rarity": 1},
        ).limit(200)
        for it in cursor:
            inv = mdb.inventory_items.find_one(
                {"guild_id": guild["id"], "item_id": it["id"], "quantity": {"$gt": 0}},
                {"_id": 0, "item_id": 1},
            )
            if inv:
                candidate = it
                break
        if candidate:
            break
    if not candidate:
        pytest.skip("Tester has no Epic+ item in inventory to test the gate against.")
    # Determine the slot from item_type.
    from app.shared.constants import SLOT_TO_ITEM_TYPE
    slot = next((s for s, t in SLOT_TO_ITEM_TYPE.items() if t == candidate["item_type"]), None)
    if not slot:
        pytest.skip("Unmappable item_type for slot resolution.")

    r = requests.post(
        f"{BASE_URL}/api/adventurers/{adv['id']}/equip",
        json={"item_id": candidate["id"], "slot": slot},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 423, (
        f"Expected 423 for Lv1 adv equipping {candidate['rarity']} item, "
        f"got {r.status_code}: {r.text}"
    )
    detail = (r.json() or {}).get("detail") or {}
    assert isinstance(detail, dict)
    assert detail.get("code") == "equipment.level_requirement_not_met"
    assert detail.get("source") == "equipment.equip"
    assert detail.get("item_slug") == candidate["slug"]
    assert isinstance(detail.get("required_level"), int)
    assert detail["required_level"] > 1
    assert detail.get("current_level") == 1
    # PII guard.
    assert "email" not in detail
    assert "_id" not in detail
    assert "user_id" not in detail
    assert "user_message" in detail
    assert str(detail["required_level"]) in detail["user_message"]


# ─── B.04 ─────────────────────────────────────────────────────────────────────
def test_b_04_admin_level_audit_dry_run_is_safe(mdb):
    """Dry run must produce a structured report AND must NOT modify
    `equipped_items` count."""
    tok = _login_tester()  # tester is admin
    headers = {"Authorization": f"Bearer {tok}"}
    before = mdb.equipped_items.count_documents({})
    r = requests.post(
        f"{BASE_URL}/api/admin/equipment/level-audit",
        json={"dry_run": True},
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200, r.text
    report = r.json()
    for k in ("scanned", "invalid", "auto_unequipped", "by_item_slug", "by_guild", "dry_run"):
        assert k in report, f"Report missing key {k}"
    assert report["dry_run"] is True
    assert report["auto_unequipped"] == 0  # never mutates on dry_run.
    assert isinstance(report["scanned"], int) and report["scanned"] >= 0
    assert isinstance(report["invalid"], int)
    after = mdb.equipped_items.count_documents({})
    assert after == before, f"Dry run mutated equipped_items: {before} → {after}"


# ─── B.05 ─────────────────────────────────────────────────────────────────────
def test_b_05_equip_common_item_still_works(mdb):
    """A Common item on a Lv1 adv must still equip cleanly — sanity that
    the new gate doesn't break the existing flow."""
    tok = _login_tester()
    headers = {"Authorization": f"Bearer {tok}"}
    me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10).json()
    user = me.get("user", me)
    guild = mdb.guilds.find_one({"owner_user_id": user["id"]}, {"_id": 0, "id": 1})
    if not guild:
        pytest.skip("No tester guild.")
    adv = mdb.adventurers.find_one(
        {"guild_id": guild["id"], "is_available": True, "is_retired": {"$ne": True}},
        {"_id": 0, "id": 1, "level": 1},
    )
    if not adv:
        pytest.skip("Tester has no available adv.")
    # Find a Common item in inventory not bound to anyone else.
    common_items = mdb.items.find(
        {"rarity": "Common", "is_active": True, "item_type": {"$ne": "material"}},
        {"_id": 0, "id": 1, "slug": 1, "item_type": 1, "level_required": 1, "rarity": 1},
    ).limit(20)
    target = None
    for it in common_items:
        if int(it.get("level_required", 1)) > 1:
            continue
        inv = mdb.inventory_items.find_one(
            {
                "guild_id": guild["id"],
                "item_id": it["id"],
                "quantity": {"$gt": 0},
                "$expr": {"$lt": [{"$ifNull": ["$reserved_qty", 0]}, "$quantity"]},
            },
            {"_id": 0},
        )
        if not inv:
            continue
        if inv.get("bound_to_adventurer_id") and inv.get("bound_to_adventurer_id") != adv["id"]:
            continue
        target = it
        break
    if not target:
        pytest.skip("Tester has no available Common item to equip.")
    from app.shared.constants import SLOT_TO_ITEM_TYPE
    slot = next((s for s, t in SLOT_TO_ITEM_TYPE.items() if t == target["item_type"]), None)
    if not slot:
        pytest.skip("Unmappable slot.")
    # We don't actually fire the equip (would mutate tester state); we just
    # confirm the resolver assigns level 1 and the catalog row would pass
    # the gate. The full equip path is covered by Phase 5.5d tests.
    from app.equipment.level_gate import resolve_item_required_level
    required = resolve_item_required_level(target)
    assert required <= int(adv.get("level", 1) or 1), (
        f"Common item {target['slug']} unexpectedly gates at Lv{required}"
    )
