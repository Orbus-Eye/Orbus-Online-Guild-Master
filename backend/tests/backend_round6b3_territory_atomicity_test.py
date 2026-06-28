"""ROUND 6B.3 — Territory atomicity tests.

Validates that purchase/upgrade endpoints atomically debit gold + materials,
never go negative, and roll back on partial failure. Catches the P0 economy
exploit reported in the playtest (gold was never scaled).
"""
import asyncio
import os
import uuid
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

# Same pattern as backend_round6b1_territory_test.py: per-user account is
# spawned ad-hoc in the suite. The literal "Test12345!" is the same
# placeholder used by the rest of the round 6B test files — not a real secret.
TEST_PW = "Test12345!"  # noqa: S105 — placeholder, sandbox accounts only


@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _fresh_user(db, prefix="r6b3"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": TEST_PW,
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": TEST_PW,
    }, timeout=15)
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R6B3 {tag[-6:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    # ROUND 6B.3 Wave 3 (TASK 6) — immediately tag the test artifacts so
    # downstream leaderboards / global counts can filter them out, and a
    # later sweep can re-find them deterministically without name-regex
    # heuristics.
    db.users.update_one({"email": email},
                        {"$set": {"is_test_artifact": True, "is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"is_test_artifact": True}})
    return tag, email, h, g["id"]


def _set_guild_gold(db, guild_id, gold):
    db.guilds.update_one({"id": guild_id}, {"$set": {"gold": int(gold)}})


def _grant_prereq_war_room(db, h, guild_id):
    """war_room requires guild_hall Lv2 — set it directly in DB so test
    setup doesn't tangle with the purchase flow itself.

    IMPORTANT: we MUST first trigger lazy doc creation via GET /api/territory
    so the doc contains ALL default structures (war_room=0, market_stall=0,
    ...). A plain upsert here would create a doc with ONLY `guild_hall`,
    breaking the CAS filter on `structures.war_room.level` in the service.
    """
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {"structures.guild_hall": {
            "level": 2, "is_unlocked": True,
            "purchased_at": "2026-06-27T00:00:00+00:00",
            "upgraded_at": "2026-06-27T00:00:00+00:00",
            "acquired_via": "test_setup",
        }}},
    )


def _give_material(db, guild_id, slug, qty):
    """Idempotently top up `guild`'s stack of a given material slug."""
    tpl = db.items.find_one({"slug": slug}, {"id": 1})
    assert tpl, f"material template '{slug}' not seeded"
    existing = db.inventory_items.find_one(
        {"guild_id": guild_id, "item_id": tpl["id"]},
        {"id": 1, "quantity": 1},
    )
    if existing:
        db.inventory_items.update_one(
            {"id": existing["id"]},
            {"$inc": {"quantity": int(qty)}},
        )
    else:
        db.inventory_items.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": guild_id,
            "item_id": tpl["id"],
            "instance_id": str(uuid.uuid4()),
            "quantity": int(qty),
            "is_bound": True,
            "acquired_at": "2026-06-27T00:00:00+00:00",
        })


def _mat_qty(db, guild_id, slug):
    tpl = db.items.find_one({"slug": slug}, {"id": 1})
    row = db.inventory_items.find_one(
        {"guild_id": guild_id, "item_id": tpl["id"]}, {"quantity": 1},
    )
    return int((row or {}).get("quantity", 0))


def _gold(db, guild_id):
    g = db.guilds.find_one({"id": guild_id}, {"gold": 1})
    return int((g or {}).get("gold", 0))


def _audits(db, guild_id, slug):
    return list(db.audit_log.find({
        "actor_guild_id": guild_id,
        "metadata.structure_slug": slug,
    }))


# ──────────────────────────────────────────────────────────────────────
# 12 tests required by Wave 1 spec
# ──────────────────────────────────────────────────────────────────────


class TestTerritoryAtomicity:
    def test_01_purchase_scales_gold(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 200)
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        # market_stall Lv1 cost = 50 gold, no materials
        assert _gold(db, gid) == 150

    def test_02_upgrade_scales_gold(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 500)
        # Buy Lv1 first
        requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        # market_stall Lv2 cost = 200 + 3 iron_shard
        _give_material(db, gid, "iron_shard", 5)
        r = requests.post(f"{BASE_URL}/api/territory/upgrade",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        # After: 500 - 50 (Lv1) - 200 (Lv2) = 250
        assert _gold(db, gid) == 250
        assert _mat_qty(db, gid, "iron_shard") == 2  # 5 - 3

    def test_03_purchase_with_materials_scales_materials(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 200)
        _grant_prereq_war_room(db, h, gid)
        _give_material(db, gid, "iron_shard", 5)
        # war_room Lv1 cost = 100 + 2 iron_shard
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "war_room"}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert _gold(db, gid) == 100
        assert _mat_qty(db, gid, "iron_shard") == 3

    def test_04_upgrade_with_materials_scales_materials(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 1000)
        _grant_prereq_war_room(db, h, gid)
        _give_material(db, gid, "iron_shard", 10)
        # Buy + upgrade war_room: Lv1 cost 100+2 iron, Lv2 cost 250+5 iron
        requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "war_room"}, headers=h, timeout=15)
        r = requests.post(f"{BASE_URL}/api/territory/upgrade",
                          json={"structure_slug": "war_room"}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert _gold(db, gid) == 650
        assert _mat_qty(db, gid, "iron_shard") == 3  # 10 - 2 - 5

    def test_05_gold_insufficient_422_no_changes(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 49)  # market_stall Lv1 costs 50
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "resources.gold_insufficient"
        assert _gold(db, gid) == 49  # UNCHANGED
        t = requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15).json()
        assert t["territory"]["structures"]["market_stall"]["level"] == 0

    def test_06_material_insufficient_422_no_changes(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 500)
        _grant_prereq_war_room(db, h, gid)
        # war_room Lv1 costs 100 gold + 2 iron_shard. Give 1 iron only.
        _give_material(db, gid, "iron_shard", 1)
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "war_room"}, headers=h, timeout=15)
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "resources.material_insufficient"
        assert _gold(db, gid) == 500  # gold refunded
        assert _mat_qty(db, gid, "iron_shard") == 1  # untouched
        t = requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15).json()
        assert t["territory"]["structures"]["war_room"]["level"] == 0

    def test_07_purchase_already_unlocked_409_no_double_debit(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 500)
        requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        # First debit was 50 → balance 450
        assert _gold(db, gid) == 450
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 409
        assert _gold(db, gid) == 450  # NO double debit

    def test_08_upgrade_max_level_409(self, db):
        _, _, h, gid = _fresh_user(db)
        # Manually push market_stall to its non-legacy max (Lv 6)
        db.guild_structures.update_one(
            {"guild_id": gid},
            {
                "$set": {"structures.market_stall": {
                    "level": 6, "is_unlocked": True,
                    "purchased_at": "2026-06-27T00:00:00+00:00",
                    "upgraded_at": "2026-06-27T00:00:00+00:00",
                    "acquired_via": "purchase",
                }},
                "$setOnInsert": {"id": str(uuid.uuid4())},
            },
            upsert=True,
        )
        _set_guild_gold(db, gid, 100000)
        gold_before = _gold(db, gid)
        r = requests.post(f"{BASE_URL}/api/territory/upgrade",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "structure.already_max_level"
        assert _gold(db, gid) == gold_before

    def test_09_parallel_purchases_only_one_succeeds(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 50)  # exactly enough for ONE market_stall

        async def do_call():
            import httpx
            async with httpx.AsyncClient(timeout=15) as c:
                return await c.post(
                    f"{BASE_URL}/api/territory/purchase",
                    json={"structure_slug": "market_stall"},
                    headers=h,
                )

        async def race():
            return await asyncio.gather(do_call(), do_call(), return_exceptions=True)

        results = asyncio.run(race())
        statuses = sorted([r.status_code if hasattr(r, "status_code") else 500 for r in results])
        # Exactly one 200 and one 409 (already_unlocked) OR 422 (gold race)
        assert 200 in statuses
        assert statuses.count(200) == 1
        assert _gold(db, gid) == 0  # exactly one debit of 50

    def test_10_gold_never_negative_edge(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 49)  # cost-1 for market_stall Lv1 (50)
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 422
        assert _gold(db, gid) == 49  # never went below 0

    def test_11_audit_log_has_real_gold_delta(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 1000)
        _grant_prereq_war_room(db, h, gid)
        _give_material(db, gid, "iron_shard", 5)
        requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "war_room"}, headers=h, timeout=15)
        audits = _audits(db, gid, "war_room")
        assert len(audits) == 1
        a = audits[0]
        assert a["event_type"] == "guild_structure_purchased"
        # war_room Lv1 cost = 100 + 2 iron_shard
        assert a["gold_delta"] == -100
        assert a["metadata"]["cost"]["materials"]["iron_shard"] == 2
        assert a["metadata"]["from_level"] == 0
        assert a["metadata"]["to_level"] == 1

    def test_12_response_contains_updated_state(self, db):
        _, _, h, gid = _fresh_user(db)
        _set_guild_gold(db, gid, 500)
        r = requests.post(f"{BASE_URL}/api/territory/purchase",
                          json={"structure_slug": "market_stall"}, headers=h, timeout=15)
        assert r.status_code == 200
        body = r.json()
        # The endpoint returns the full territory snapshot post-update.
        assert "territory" in body
        assert body["territory"]["structures"]["market_stall"]["level"] == 1
        # Cross-check via /api/guilds/me that gold is updated.
        g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
        assert g["gold"] == 450
