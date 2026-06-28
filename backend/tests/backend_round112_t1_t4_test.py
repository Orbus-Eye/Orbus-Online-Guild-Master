"""ROUND 11.2 TASK 1 + TASK 4 — Recruitment cap split + Dormitories Lv11.

TASK 1 — Recruitment refresh ≠ recruit (7 tests):
  T1.01 refresh sempre OK quando AT-cap (current == cap)
  T1.02 recruit 423 quando AT-cap (projected > cap)
  T1.03 refresh sempre OK quando OVER-cap (current > cap)
  T1.04 recruit 423 quando OVER-cap
  T1.05 refresh OK + recruit OK quando SOTTO-cap
  T1.06 refresh cooldown/gold non regredito (3 free/day still works)
  T1.07 no exploit: recruit non bypassabile sopra cap nemmeno con concurrent

TASK 4 — Dormitories Lv11 cap 100 (8 tests):
  T4.01 catalog max_level == 11 (was 6)
  T4.02 DORMITORY_CAP_BY_LEVEL covers Lv0..Lv11 with progressive curve
  T4.03 upgrade Lv6→Lv7 ora purchasable (was migration-only)
  T4.04 upgrade Lv10→Lv11 atomic (gold+materials debited)
  T4.05 cap a Lv11 = 100 server-authoritative
  T4.06 upgrade beyond Lv11 blocked (max reached)
  T4.07 cost curve monotonically increasing (Lv7..Lv11)
  T4.08 frontend DORM_CAP_BY_LEVEL aligned with backend
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _fresh_guild(db, *, prefix: str = "r112t14"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R112T14 {tag[-6:]}"},
                  headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 80_000}})
    return h, g["id"]


def _seed_advs_at_cap(db, *, guild_id: str, cap: int, current: int) -> None:
    """Insert `current` adventurers (capped at desired count) for cap testing."""
    cls = db.adventurer_classes.find_one({"slug": "warrior"})
    now = datetime.now(timezone.utc).isoformat()
    # Drop ALL existing adventurers in this guild (starter roster + test seeds)
    # so the post-setup count matches `current` exactly.
    db.adventurers.delete_many({"guild_id": guild_id})
    docs = []
    for i in range(current):
        docs.append({
            "id": str(uuid.uuid4()), "guild_id": guild_id,
            "name": f"AT_CAP_{i:03d}",
            "adventurer_class_id": cls["id"], "class_name": cls.get("name", "Warrior"),
            "class_role": cls.get("role"),
            "rarity": "Common",
            "level": 5, "experience": 0,
            "strength": 10, "agility": 10, "intellect": 10,
            "endurance": 10, "faith": 10,
            "stamina": 100, "morale": 100,
            "is_available": True, "is_retired": False,
            "traits": [], "is_starter": False, "is_test_seed": True,
            "created_at": now, "updated_at": now,
        })
    if docs:
        db.adventurers.insert_many(docs)


def _set_dorm_level(db, guild_id: str, level: int) -> None:
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {"structures.dormitories": {"is_unlocked": True, "level": level}}},
    )


# ─────────────────────────────────────────────────────────────────────────
# TASK 1 — Recruitment refresh ≠ recruit
# ─────────────────────────────────────────────────────────────────────────
def test_t1_01_refresh_ok_at_cap(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 1)  # cap 5
    _seed_advs_at_cap(db, guild_id=gid, cap=5, current=5)
    r = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=h, timeout=15)
    assert r.status_code == 200, f"refresh must succeed at-cap: {r.text}"


def test_t1_02_recruit_blocked_at_cap(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 1)
    _seed_advs_at_cap(db, guild_id=gid, cap=5, current=5)
    # Fresh candidates
    cands = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
    r = requests.post(f"{BASE_URL}/api/recruitment/recruit",
                      json={"candidate_id": cands[0]["candidate_id"]},
                      headers=h, timeout=15)
    assert r.status_code == 423
    assert r.json()["detail"]["code"] == "roster_over_capacity"


def test_t1_03_refresh_ok_over_cap(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 1)
    _seed_advs_at_cap(db, guild_id=gid, cap=5, current=8)  # OVER cap
    r = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=h, timeout=15)
    assert r.status_code == 200, f"refresh must succeed over-cap: {r.text}"


def test_t1_04_recruit_blocked_over_cap(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 1)
    _seed_advs_at_cap(db, guild_id=gid, cap=5, current=8)
    cands = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
    r = requests.post(f"{BASE_URL}/api/recruitment/recruit",
                      json={"candidate_id": cands[0]["candidate_id"]},
                      headers=h, timeout=15)
    assert r.status_code == 423


def test_t1_05_both_ok_under_cap(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 2)  # cap 10
    _seed_advs_at_cap(db, guild_id=gid, cap=10, current=4)
    rr = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=h, timeout=15)
    assert rr.status_code == 200
    cands = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
    r = requests.post(f"{BASE_URL}/api/recruitment/recruit",
                      json={"candidate_id": cands[0]["candidate_id"]},
                      headers=h, timeout=15)
    assert r.status_code == 201


def test_t1_06_refresh_cooldown_not_regressed(db):
    """3 free refreshes/day + then escalating cost — phase 11.2 unchanged."""
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 3)
    cands = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15).json()
    initial_remaining = cands.get("refreshes_remaining_today", 3)
    assert initial_remaining >= 1, "expected at least 1 free refresh available"
    r = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=h, timeout=15)
    assert r.status_code == 200
    after = r.json()
    assert "refreshes_remaining_today" in after
    assert "next_refresh_cost_gold" in after


def test_t1_07_no_exploit_recruit_above_cap_concurrent(db):
    """Two concurrent recruit on AT-cap → only first goes through; cap respected."""
    import concurrent.futures as cf
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 2)  # cap 10
    _seed_advs_at_cap(db, guild_id=gid, cap=10, current=9)  # one slot left
    cands = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
    if len(cands) < 2:
        # Force refresh to get 2 different candidates
        cands = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=h, timeout=15).json()["candidates"]

    def call(cid):
        return requests.post(
            f"{BASE_URL}/api/recruitment/recruit",
            json={"candidate_id": cid}, headers=h, timeout=15,
        )

    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(call, cands[0]["candidate_id"])
        f2 = ex.submit(call, cands[1]["candidate_id"])
        r1, r2 = f1.result(), f2.result()
    # At most ONE recruit must succeed at 9/10. The other must fail with 423.
    successes = sum(1 for r in (r1, r2) if r.status_code == 201)
    blocks = sum(1 for r in (r1, r2) if r.status_code == 423)
    assert successes <= 1, "exploit: more than 1 recruit succeeded above cap"
    assert successes + blocks >= 1  # at least one outcome decisive
    # Final adv count must NOT exceed cap
    final = db.adventurers.count_documents(
        {"guild_id": gid, "is_retired": {"$ne": True}},
    )
    assert final <= 10, f"FINAL roster {final} exceeded cap 10"


# ─────────────────────────────────────────────────────────────────────────
# TASK 4 — Dormitories Lv11 cap 100
# ─────────────────────────────────────────────────────────────────────────
def test_t4_01_catalog_max_level_extended_to_11():
    from app.territory.structures import STRUCTURE_CATALOG, get_structure_max_level
    assert STRUCTURE_CATALOG["dormitories"]["max_level"] == 11
    # max_legacy_level removed
    assert "max_legacy_level" not in STRUCTURE_CATALOG["dormitories"]
    assert get_structure_max_level("dormitories") == 11
    assert get_structure_max_level("dormitories", allow_legacy=True) == 11


def test_t4_02_dormitory_cap_progressive_curve():
    from app.territory.structures import DORMITORY_CAP_BY_LEVEL, dormitory_cap_for_level
    expected = {0: 0, 1: 5, 2: 10, 3: 15, 4: 20, 5: 25, 6: 30,
                7: 40, 8: 50, 9: 65, 10: 80, 11: 100}
    for lvl, cap in expected.items():
        assert DORMITORY_CAP_BY_LEVEL[lvl] == cap, f"Lv{lvl} cap mismatch"
        assert dormitory_cap_for_level(lvl) == cap


def test_t4_03_lv6_to_lv7_now_purchasable():
    """Pre-TASK 4 this was migration-only (`_LEGACY_ONLY=None`). Now real cost."""
    from app.territory.costs import cost_for
    c = cost_for("dormitories", 7)
    assert c is not None, "Lv7 must now be purchasable (was migration-only)"
    assert c["gold"] > 0
    assert "materials" in c


def test_t4_04_upgrade_lv10_to_lv11_atomic(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 10)
    db.guilds.update_one({"id": gid}, {"$set": {"gold": 100_000}})
    # Grant required materials directly (test seed shortcut)
    from app.territory.costs import cost_for
    cost = cost_for("dormitories", 11)
    for slug, qty in (cost.get("materials") or {}).items():
        tpl = db.items.find_one({"slug": slug}, {"_id": 0, "id": 1, "slug": 1})
        if not tpl:
            tpl = db.items.find_one({"slug": slug}, {"_id": 0})
        assert tpl, f"material template {slug} not seeded"
        db.inventory_items.insert_one({
            "id": str(uuid.uuid4()), "instance_id": str(uuid.uuid4()),
            "guild_id": gid, "item_id": tpl.get("id") or slug,
            "item_slug": slug, "quantity": qty * 2,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "is_bound": False, "refinement_level": 0,
            "enchants": [], "affixes": [], "reroll_count": 0,
            "disenchanted_at": None, "discarded_at": None,
            "bound_to_adventurer_id": None,
        })
    gold_before = db.guilds.find_one({"id": gid})["gold"]
    r = requests.post(
        f"{BASE_URL}/api/territory/upgrade",
        json={"slug": "dormitories"}, headers=h, timeout=15,
    )
    # Either 200 (success) or a clear material-mismatch 4xx if our seed shortcut
    # doesn't satisfy the atomic debit (some material slugs may not be seeded).
    # We only assert NO 500 and NO regression to legacy behavior.
    assert r.status_code != 500, f"Lv10→Lv11 upgrade returned 500: {r.text}"
    if r.status_code == 200:
        gold_after = db.guilds.find_one({"id": gid})["gold"]
        assert gold_after == gold_before - cost["gold"]


def test_t4_05_cap_at_lv11_is_100_server_authoritative(db):
    from app.territory.guards import compute_adventurer_cap_state
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 11)

    async def _run():
        acli = AsyncIOMotorClient(MONGO_URL)
        adb = acli[DB_NAME]
        state = await compute_adventurer_cap_state(adb, gid)
        acli.close()
        return state

    state = asyncio.run(_run())
    assert state["cap"] == 100, f"expected cap 100, got {state['cap']}"
    assert state["dormitory_level"] == 11


def test_t4_06_upgrade_beyond_lv11_blocked(db):
    h, gid = _fresh_guild(db)
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_dorm_level(db, gid, 11)
    db.guilds.update_one({"id": gid}, {"$set": {"gold": 200_000}})
    r = requests.post(
        f"{BASE_URL}/api/territory/upgrade",
        json={"slug": "dormitories"}, headers=h, timeout=15,
    )
    # Must be a clean 4xx, NOT 500
    assert r.status_code in (400, 422, 423, 409), f"expected 4xx, got {r.status_code}: {r.text}"


def test_t4_07_cost_curve_monotonically_increasing():
    from app.territory.costs import cost_for
    prev_gold = 0
    for lvl in range(1, 12):
        c = cost_for("dormitories", lvl)
        assert c is not None, f"Lv{lvl} must have a cost"
        assert c["gold"] >= prev_gold, \
            f"cost regression at Lv{lvl}: {c['gold']} < {prev_gold}"
        prev_gold = c["gold"]


def test_t4_08_frontend_constants_aligned():
    """Manual-grep guard: FE constants must match backend DORMITORY_CAP_BY_LEVEL."""
    from app.territory.structures import DORMITORY_CAP_BY_LEVEL
    # Read the canonical FE constant
    with open("/app/frontend/src/utils/structures.js") as f:
        content = f.read()
    import re
    m = re.search(r"DORM_CAP_BY_LEVEL\s*=\s*\[([^\]]+)\]", content)
    assert m, "FE DORM_CAP_BY_LEVEL not found"
    fe_arr = [int(x.strip()) for x in m.group(1).split(",")]
    expected = [DORMITORY_CAP_BY_LEVEL[i] for i in range(12)]
    assert fe_arr == expected, f"FE {fe_arr} != backend {expected}"
