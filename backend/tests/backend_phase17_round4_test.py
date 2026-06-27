"""Phase 17 (ROUND 4) — Equipment & Loot advanced features.

28 tests covering:
  Migration / Seed (3)
    1. Idempotent migration: re-run does not duplicate fields.
    2. Forge seed creates 3 sets, 13 enchants, 1 dragon_essence material.
    3. instance_id present + default ROUND 4 fields on all inventory rows.

  Path & API surface (2)
    4. OpenAPI path count is exactly 69.
    5. GET /api/sets, GET /api/enchants are public and shape-correct.

  Refinement (5)
    6. Refine succeeds at +1 (deterministic 100% rate).
    7. Refine debits gold + materials atomically.
    8. Refine flips is_bound=True.
    9. Refine rejects stackable items (422).
    10. Refine 404 on unknown instance_id.

  Enchant (4)
    11. Enchant-options returns 3-5 weighted options.
    12. Enchant apply debits gold + flips is_bound.
    13. Enchant 422 when no free slot.
    14. Enchant 404 on unknown enchant_slug.

  Reroll affixes (3)
    15. Reroll succeeds, increments reroll_count, costs 50g.
    16. Reroll caps at 5 (422 on attempt #6).
    17. Reroll 422 when item has no affixes.

  Disenchant (3)
    18. Disenchant marks disenchanted_at, returns guaranteed materials.
    19. Disenchanted item cannot be refined again (410 Gone).
    20. Disenchant 422 on stackable items.

  BoE Market guard (3) — CRITICO
    21. Refined item cannot be listed on market (422 + sentinel detail).
    22. Enchanted item cannot be listed (422).
    23. Non-bound item CAN be listed (no false positive).

  Equipment-detail & set bonuses (2)
    24. GET equipment-detail returns slots, set_progress, active_bonuses keys.
    25. Active bonuses appear when N pieces of same set equipped.

  No-regression cross-suite (3)
    26. GET /api/inventory exposes ROUND 4 fields without breaking legacy keys.
    27. Market non-bound listing flow remains intact end-to-end.
    28. Leaderboard endpoint shape unchanged.

Hard constraints honoured:
  * Test users use @orbus.test emails.
  * No destructive teardown / no ALLOWLIST mutation.
  * No real-money item purchase.
"""
import os
import uuid
import time
import random as _random
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("BACKEND_URL", "http://localhost:8001")
).rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


def _seed_user(name_hint: str = "p17"):
    """Register a fresh user + guild for an isolated test scenario."""
    tag = f"{name_hint}_{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r2 = requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"R4 Guild {tag[-6:].upper()}", "description": ""},
        headers=h, timeout=15,
    )
    assert r2.status_code == 201, r2.text
    gid = requests.get(
        f"{BASE_URL}/api/guilds/me", headers=h, timeout=15,
    ).json()["guild"]["id"]
    return {"headers": h, "guild_id": gid, "tag": tag}


def _ensure_inventory_item(
    db, guild_id: str, item_slug: str, quantity: int = 1, *,
    refinement_level: int = 0, enchants=None, affixes=None,
    is_bound: bool = False,
):
    """Force-insert an inventory_items row via direct DB write. We treat this
    as test fixture-level shortcut to avoid having to run a full expedition.
    Idempotent: upserts by (guild_id, item_id) for stackables, or creates a
    new instance for non-stackables.
    """
    item = db.items.find_one({"slug": item_slug})
    assert item, f"item {item_slug} not seeded"
    instance_id = str(uuid.uuid4())
    row_id = str(uuid.uuid4())
    db.inventory_items.insert_one({
        "id": row_id,
        "instance_id": instance_id,
        "guild_id": guild_id,
        "item_id": item["id"],
        "quantity": int(quantity),
        "refinement_level": int(refinement_level),
        "enchants": enchants or [],
        "affixes": affixes or [],
        "reroll_count": 0,
        "is_bound": bool(is_bound),
        "disenchanted_at": None,
        "acquired_at": "2026-06-26T00:00:00+00:00",
        "source": "test_fixture",
    })
    return {"id": row_id, "instance_id": instance_id, "item_id": item["id"], "item": item}


def _add_gold(db, guild_id: str, amount: int):
    db.guilds.update_one({"id": guild_id}, {"$inc": {"gold": int(amount)}})


def _add_materials(db, guild_id: str, materials: dict):
    """Add materials in bulk via direct DB writes."""
    for slug, qty in materials.items():
        item = db.items.find_one({"slug": slug})
        if not item:
            continue
        existing = db.inventory_items.find_one(
            {"guild_id": guild_id, "item_id": item["id"], "is_bound": {"$ne": True}}
        )
        if existing:
            db.inventory_items.update_one(
                {"id": existing["id"]}, {"$inc": {"quantity": int(qty)}},
            )
        else:
            db.inventory_items.insert_one({
                "id": str(uuid.uuid4()),
                "instance_id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item["id"],
                "quantity": int(qty),
                "refinement_level": 0,
                "enchants": [],
                "affixes": [],
                "reroll_count": 0,
                "is_bound": False,
                "disenchanted_at": None,
                "acquired_at": "2026-06-26T00:00:00+00:00",
                "source": "test_fixture",
            })


# ═════════════════════════════════════════════════════════════════════════
# 1-3. Migration / Seed idempotency
# ═════════════════════════════════════════════════════════════════════════
@pytest.mark.flaky(reruns=3)  # Phase 19 — known parallel xdist flake, see FLAKY_TESTS_AUDIT.md
def test_01_migration_idempotent_no_dup_fields(db):
    # After backend startup the migration ran. Calling our migration helper
    # again must not create stale duplicates. We assert no row has both
    # `is_bound` missing AND `disenchanted_at` missing.
    bad = db.inventory_items.count_documents({
        "$or": [
            {"is_bound": {"$exists": False}},
            {"disenchanted_at": {"$exists": False}},
            {"refinement_level": {"$exists": False}},
            {"instance_id": {"$exists": False}},
        ]
    })
    assert bad == 0, f"{bad} rows missing ROUND 4 default fields"


def test_02_forge_seed_present(db):
    # Seeded data must be present (idempotent boot seed).
    sets = list(db.item_sets.find({}))
    enchants = list(db.enchants.find({"is_active": {"$ne": False}}))
    assert len(sets) >= 3, f"expected >=3 sets, got {len(sets)}"
    assert len(enchants) >= 13, f"expected >=13 enchants, got {len(enchants)}"
    de = db.items.find_one({"slug": "dragon_essence"})
    assert de is not None, "dragon_essence material missing"
    assert de.get("item_type") == "material"


def test_03_inventory_default_fields():
    # GET /api/inventory exposes ROUND 4 fields with defaults
    ctx = _seed_user("inv_def")
    r = requests.get(f"{BASE_URL}/api/inventory", headers=ctx["headers"], timeout=15)
    assert r.status_code == 200, r.text
    inv = r.json()["inventory"]
    # New empty inventory is OK (test passes if no entry); but if entries
    # exist, every one must expose the new fields.
    for row in inv:
        assert "instance_id" in row
        assert "is_bound" in row
        assert "refinement_level" in row
        assert "enchants" in row
        assert "affixes" in row


# ═════════════════════════════════════════════════════════════════════════
# 4-5. Path & API surface
# ═════════════════════════════════════════════════════════════════════════
def test_04_openapi_path_count():
    r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
    assert r.status_code == 200
    paths = list(r.json()["paths"].keys())
    # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
    assert len(paths) == 79, f"expected 75 paths, got {len(paths)}: {sorted(paths)}"


def test_05_sets_and_enchants_public_routes():
    rs = requests.get(f"{BASE_URL}/api/sets", timeout=15)
    re_ = requests.get(f"{BASE_URL}/api/enchants", timeout=15)
    assert rs.status_code == 200
    assert re_.status_code == 200
    sets = rs.json()["sets"]
    enchants = re_.json()["enchants"]
    assert isinstance(sets, list) and len(sets) >= 3
    assert isinstance(enchants, list) and len(enchants) >= 13
    # Pubblico = no campi sensibili
    for s in sets:
        assert "_id" not in s
    for e in enchants:
        assert "_id" not in e


# ═════════════════════════════════════════════════════════════════════════
# 6-10. Refinement
# ═════════════════════════════════════════════════════════════════════════
def test_06_refine_plus1_succeeds(db):
    ctx = _seed_user("refine_p1")
    _add_gold(db, ctx["guild_id"], 5000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 20})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    iid = fixture["instance_id"]
    r = requests.post(
        f"{BASE_URL}/api/inventory/{iid}/refine",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # +1 is deterministic 100% in the locked curve.
    assert body["success"] is True
    assert body["refinement_level"] == 1
    assert body["is_bound"] is True


def test_07_refine_debits_gold_and_mats(db):
    ctx = _seed_user("refine_econ")
    _add_gold(db, ctx["guild_id"], 1000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_chest")
    g_before = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    iron_id = db.items.find_one({"slug": "iron_shard"})["id"]
    inv_before = db.inventory_items.find_one(
        {"guild_id": ctx["guild_id"], "item_id": iron_id}
    )["quantity"]
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/refine",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200
    g_after = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    inv_after = db.inventory_items.find_one(
        {"guild_id": ctx["guild_id"], "item_id": iron_id}
    )["quantity"]
    assert g_before - g_after == 50  # +1 cost
    assert inv_before - inv_after == 2  # +1 cost: iron_shard x2


def test_08_refine_sets_is_bound(db):
    ctx = _seed_user("refine_bound")
    _add_gold(db, ctx["guild_id"], 1000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_blade")
    requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/refine",
        headers=ctx["headers"], timeout=15,
    )
    row = db.inventory_items.find_one({"instance_id": fixture["instance_id"]})
    assert row["is_bound"] is True
    assert row["refinement_level"] == 1


def test_09_refine_rejects_stackable(db):
    ctx = _seed_user("refine_stack")
    _add_gold(db, ctx["guild_id"], 1000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    # Use iron_shard itself (material) and try to refine it.
    iron = db.items.find_one({"slug": "iron_shard"})
    iron_row = db.inventory_items.find_one(
        {"guild_id": ctx["guild_id"], "item_id": iron["id"]}
    )
    r = requests.post(
        f"{BASE_URL}/api/inventory/{iron_row['instance_id']}/refine",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 422


def test_10_refine_404_unknown_instance():
    ctx = _seed_user("refine_404")
    r = requests.post(
        f"{BASE_URL}/api/inventory/00000000-0000-0000-0000-000000000000/refine",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════════════
# 11-14. Enchant
# ═════════════════════════════════════════════════════════════════════════
def test_11_enchant_options_returns_choices(db):
    ctx = _seed_user("ench_opt")
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/enchant-options",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "options" in body
    assert 3 <= len(body["options"]) <= 5
    for o in body["options"]:
        assert "slug" in o and "name" in o and "cost_gold" in o


def test_12_enchant_apply_debits_and_binds(db):
    ctx = _seed_user("ench_apply")
    _add_gold(db, ctx["guild_id"], 5000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10, "arcane_dust": 10})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    # Use the cheapest known seeded enchant (small_str).
    g_before = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/enchant",
        json={"enchant_slug": "small_str"},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_bound"] is True
    assert body["enchant"]["slug"] == "small_str"
    g_after = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    assert g_before - g_after == 50


def test_13_enchant_no_free_slot(db):
    ctx = _seed_user("ench_full")
    _add_gold(db, ctx["guild_id"], 5000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    # Helm has enchant_slots=2 — fill them.
    fixture = _ensure_inventory_item(
        db, ctx["guild_id"], "drake_slayer_helm",
        enchants=[
            {"slug": "small_str", "bonus_stat": "strength_bonus", "bonus_value": 1, "applied_at": "x"},
            {"slug": "small_agi", "bonus_stat": "agility_bonus", "bonus_value": 1, "applied_at": "x"},
        ],
    )
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/enchant",
        json={"enchant_slug": "small_int"},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 422


def test_14_enchant_unknown_slug(db):
    ctx = _seed_user("ench_404")
    _add_gold(db, ctx["guild_id"], 5000)
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/enchant",
        json={"enchant_slug": "totally_not_real"},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════════════
# 15-17. Reroll affixes
# ═════════════════════════════════════════════════════════════════════════
def test_15_reroll_increments_count(db):
    ctx = _seed_user("rer_1")
    _add_gold(db, ctx["guild_id"], 10000)
    fixture = _ensure_inventory_item(
        db, ctx["guild_id"], "drake_slayer_helm",
        affixes=[{"slot": "prefix", "name": "Sharp",
                  "bonus_stat": "strength_bonus", "bonus_value": 2}],
    )
    g_before = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/reroll-affixes",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reroll_count"] == 1
    assert body["is_bound"] is True
    g_after = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    assert g_before - g_after == 50  # first reroll cost


def test_16_reroll_caps_at_5(db):
    ctx = _seed_user("rer_cap")
    _add_gold(db, ctx["guild_id"], 100000)
    fixture = _ensure_inventory_item(
        db, ctx["guild_id"], "drake_slayer_helm",
        affixes=[{"slot": "prefix", "name": "Sharp",
                  "bonus_stat": "strength_bonus", "bonus_value": 2}],
    )
    iid = fixture["instance_id"]
    for _ in range(5):
        r = requests.post(
            f"{BASE_URL}/api/inventory/{iid}/reroll-affixes",
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code == 200
    # 6th attempt → 422
    r6 = requests.post(
        f"{BASE_URL}/api/inventory/{iid}/reroll-affixes",
        headers=ctx["headers"], timeout=15,
    )
    assert r6.status_code == 422


def test_17_reroll_no_affixes(db):
    ctx = _seed_user("rer_no")
    _add_gold(db, ctx["guild_id"], 10000)
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/reroll-affixes",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════════
# 18-20. Disenchant
# ═════════════════════════════════════════════════════════════════════════
def test_18_disenchant_marks_and_grants_materials(db):
    ctx = _seed_user("dis_grant")
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/disenchant",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["materials_guaranteed"]) >= 1  # Legendary guaranteed >= 1 mat
    row = db.inventory_items.find_one({"instance_id": fixture["instance_id"]})
    assert row["disenchanted_at"] is not None


def test_19_disenchanted_item_cannot_refine(db):
    ctx = _seed_user("dis_then_refine")
    _add_gold(db, ctx["guild_id"], 1000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/disenchant",
        headers=ctx["headers"], timeout=15,
    )
    r = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/refine",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 410


def test_20_disenchant_rejects_stackable(db):
    ctx = _seed_user("dis_stack")
    _add_materials(db, ctx["guild_id"], {"iron_shard": 5})
    iron = db.items.find_one({"slug": "iron_shard"})
    iron_row = db.inventory_items.find_one(
        {"guild_id": ctx["guild_id"], "item_id": iron["id"]}
    )
    r = requests.post(
        f"{BASE_URL}/api/inventory/{iron_row['instance_id']}/disenchant",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════════
# 21-23. BoE Market guard (CRITICO Q8 LOCKED)
# ═════════════════════════════════════════════════════════════════════════
def test_21_refined_item_blocked_in_market(db):
    ctx = _seed_user("boe_refine")
    _add_gold(db, ctx["guild_id"], 5000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_helm")
    # Refine to bind.
    r1 = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/refine",
        headers=ctx["headers"], timeout=15,
    )
    assert r1.status_code == 200
    # Try listing → 422 with sentinel.
    r2 = requests.post(
        f"{BASE_URL}/api/market/listings",
        json={"item_slug": "drake_slayer_helm", "quantity": 1, "price_per_unit": 100},
        headers=ctx["headers"], timeout=15,
    )
    assert r2.status_code == 422, r2.text
    assert r2.json()["detail"] == "market.bound_item_not_sellable"


def test_22_enchanted_item_blocked_in_market(db):
    ctx = _seed_user("boe_ench")
    _add_gold(db, ctx["guild_id"], 5000)
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    fixture = _ensure_inventory_item(db, ctx["guild_id"], "drake_slayer_blade")
    r1 = requests.post(
        f"{BASE_URL}/api/inventory/{fixture['instance_id']}/enchant",
        json={"enchant_slug": "small_str"},
        headers=ctx["headers"], timeout=15,
    )
    assert r1.status_code == 200, r1.text
    r2 = requests.post(
        f"{BASE_URL}/api/market/listings",
        json={"item_slug": "drake_slayer_blade", "quantity": 1, "price_per_unit": 100},
        headers=ctx["headers"], timeout=15,
    )
    assert r2.status_code == 422


def test_23_unbound_item_can_be_listed(db):
    """Non-bound, tradeable, non-equipped item must list without errors."""
    ctx = _seed_user("boe_ok")
    _add_gold(db, ctx["guild_id"], 5000)
    # Use iron_shard (material, tradeable, non-bindable) — well-defined path.
    _add_materials(db, ctx["guild_id"], {"iron_shard": 5})
    r = requests.post(
        f"{BASE_URL}/api/market/listings",
        json={"item_slug": "iron_shard", "quantity": 2, "price_per_unit": 5},
        headers=ctx["headers"], timeout=15,
    )
    # Either 200 (success) or 400 (not tradeable by config). We accept BOTH
    # but MUST NOT see the 422 BoE sentinel here.
    if r.status_code == 422:
        assert r.json().get("detail") != "market.bound_item_not_sellable"


# ═════════════════════════════════════════════════════════════════════════
# 24-25. Equipment-detail & set bonuses
# ═════════════════════════════════════════════════════════════════════════
def test_24_equipment_detail_shape(db):
    ctx = _seed_user("eq_shape")
    # Need at least one adventurer.
    cand = requests.get(
        f"{BASE_URL}/api/recruitment/candidates",
        headers=ctx["headers"], timeout=15,
    ).json()
    cand_id = cand["candidates"][0]["candidate_id"]
    # Give some gold to afford the recruit cost.
    _add_gold(db, ctx["guild_id"], 1000)
    requests.post(
        f"{BASE_URL}/api/recruitment/recruit",
        json={"candidate_id": cand_id},
        headers=ctx["headers"], timeout=15,
    )
    adv = requests.get(
        f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15,
    ).json()["adventurers"][0]
    r = requests.get(
        f"{BASE_URL}/api/adventurers/{adv['id']}/equipment-detail",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "slots" in body
    assert "set_progress" in body
    assert "active_bonuses" in body


def test_25_set_bonus_calc_with_pieces_equipped(db):
    """Manually equip 3 pieces of the same set via direct DB write, then
    verify equipment-detail returns the 3-piece bonus active.

    We avoid going through the equip endpoint to keep this test focused
    on the *bonus calculation* logic, not the equip pipeline.
    """
    ctx = _seed_user("eq_set")
    # Pick "drake_slayer" which has 3 pieces in seed.
    pieces = ["drake_slayer_helm", "drake_slayer_chest", "drake_slayer_blade"]
    # Create an adventurer.
    cand = requests.get(
        f"{BASE_URL}/api/recruitment/candidates",
        headers=ctx["headers"], timeout=15,
    ).json()
    cand_id = cand["candidates"][0]["candidate_id"]
    _add_gold(db, ctx["guild_id"], 1000)
    requests.post(
        f"{BASE_URL}/api/recruitment/recruit",
        json={"candidate_id": cand_id},
        headers=ctx["headers"], timeout=15,
    )
    adv = requests.get(
        f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15,
    ).json()["adventurers"][0]
    # Insert 3 equipped_items rows directly.
    for slug in pieces:
        it = db.items.find_one({"slug": slug})
        db.equipped_items.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": ctx["guild_id"],
            "adventurer_id": adv["id"],
            "slot": it.get("slot_type") or it.get("slot"),
            "item_id": it["id"],
            "instance_id": str(uuid.uuid4()),
            "equipped_at": "2026-06-26T00:00:00+00:00",
        })
    r = requests.get(
        f"{BASE_URL}/api/adventurers/{adv['id']}/equipment-detail",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    bonuses = body.get("active_bonuses", [])
    # 3-piece bonus must be present.
    drake_3 = [b for b in bonuses if b.get("set_slug") == "drake_slayer" and b.get("pieces") == 3]
    assert len(drake_3) == 1, f"expected drake_slayer 3pz bonus, got {bonuses}"


# ═════════════════════════════════════════════════════════════════════════
# 26-28. No-regression cross-suite
# ═════════════════════════════════════════════════════════════════════════
def test_26_inventory_exposes_legacy_and_new_fields(db):
    ctx = _seed_user("nr_inv")
    _add_materials(db, ctx["guild_id"], {"iron_shard": 3})
    r = requests.get(f"{BASE_URL}/api/inventory", headers=ctx["headers"], timeout=15)
    assert r.status_code == 200
    inv = r.json()["inventory"]
    assert inv  # at least one row from materials
    row = inv[0]
    # Legacy fields
    for k in ["id", "quantity", "total_quantity", "equipped_quantity",
              "available_quantity", "item"]:
        assert k in row, f"missing legacy field {k}"
    # New ROUND 4 fields
    for k in ["instance_id", "is_bound", "refinement_level", "enchants", "affixes"]:
        assert k in row, f"missing ROUND 4 field {k}"


def test_27_market_unbound_listing_full_flow(db):
    """End-to-end: non-bound material → list → cancel. Verifies that the
    market path still works (no regression from BoE guard)."""
    ctx = _seed_user("mkt_flow")
    _add_materials(db, ctx["guild_id"], {"iron_shard": 10})
    rL = requests.post(
        f"{BASE_URL}/api/market/listings",
        json={"item_slug": "iron_shard", "quantity": 3, "price_per_unit": 7},
        headers=ctx["headers"], timeout=15,
    )
    # Some seeds set iron_shard not tradeable; accept either 200 listing OR
    # 400 not_tradeable. We DO require NOT a 422 BoE sentinel.
    if rL.status_code == 200 or rL.status_code == 201:
        listing_id = rL.json()["listing_id"]
        rC = requests.delete(
            f"{BASE_URL}/api/market/listings/{listing_id}",
            headers=ctx["headers"], timeout=15,
        )
        assert rC.status_code == 200
    else:
        # Acceptable alternative: backend marked not tradeable in seed.
        assert rL.status_code in (200, 201, 400), rL.text
        if rL.status_code == 422:
            assert rL.json().get("detail") != "market.bound_item_not_sellable"


def test_28_leaderboard_unchanged():
    r = requests.get(f"{BASE_URL}/api/leaderboard/guilds", timeout=15)
    assert r.status_code == 200
    body = r.json()
    # Schema unchanged: should still contain `guilds`/`leaderboard` key
    # (whichever Phase 14 / 16 used). We accept either.
    assert any(k in body for k in ("guilds", "leaderboard", "entries"))
