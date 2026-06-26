"""Phase 14 — Daily Quests backend tests."""
import os
import uuid
from datetime import datetime, timedelta, timezone
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


def _seed_user_with_guild(db):
    tag = f"p14_{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"G_{tag}", "description": ""}, headers=h, timeout=15,
    )
    gid = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]["id"]
    return {"headers": h, "guild_id": gid, "tag": tag}


def _seed_3_advs(db, gid):
    aids = []
    roles = [("Tank", "Warrior"), ("Healer", "Priest"), ("DPS", "Rogue")]
    for i, (role, klass) in enumerate(roles):
        aid = str(uuid.uuid4())
        db.adventurers.insert_one({
            "id": aid, "guild_id": gid,
            "name": f"P14Hero_{i}", "adventurer_class_id": "x",
            "class_name": klass, "class_role": role,
            "rarity": "Common", "level": 5, "experience": 0,
            "strength": 12, "agility": 10, "intellect": 8,
            "endurance": 10, "faith": 8,
            "stamina": 100, "morale": 100, "traits": [],
            "is_available": True, "phase13_unbaked": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        aids.append(aid)
    return aids


# ──────────────────────────────────────────────────────────────────────
class TestAuth:
    def test_today_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/quests/today", timeout=15)
        assert r.status_code in (401, 403)

    def test_claim_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/quests/claim/equip", timeout=15)
        assert r.status_code in (401, 403)


class TestFreshState:
    def test_fresh_user_has_three_zero_quests(self, db):
        ctx = _seed_user_with_guild(db)
        r = requests.get(f"{BASE_URL}/api/quests/today", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert len(d["quests"]) == 3
        for q in d["quests"]:
            assert q["progress"] == 0
            assert q["claimed"] is False
            assert q["completed"] is False
            assert q["can_claim"] is False


class TestProgressIncrements:
    def test_expedition_complete_increments_progress(self, db):
        ctx = _seed_user_with_guild(db)
        aids = _seed_3_advs(db, ctx["guild_id"])
        dungeons = requests.get(f"{BASE_URL}/api/dungeons", headers=ctx["headers"], timeout=15).json()["dungeons"]
        gw = next(d for d in dungeons if d["slug"] == "goblin-warrens")
        r = requests.post(
            f"{BASE_URL}/api/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": aids},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code in (200, 201), r.text
        exp_id = r.json()["expedition"]["id"]
        past = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        db.expeditions.update_one({"id": exp_id}, {"$set": {"completes_at": past}})
        requests.get(f"{BASE_URL}/api/expeditions", headers=ctx["headers"], timeout=15)
        d = requests.get(f"{BASE_URL}/api/quests/today", headers=ctx["headers"], timeout=15).json()
        exp_q = next(q for q in d["quests"] if q["id"] == "expedition_complete")
        assert exp_q["progress"] >= 1
        assert exp_q["completed"] is True
        assert exp_q["can_claim"] is True

    def test_recruit_increments_progress(self, db):
        ctx = _seed_user_with_guild(db)
        # give gold to recruit
        db.guilds.update_one({"id": ctx["guild_id"]}, {"$set": {"gold": 9999}})
        offers = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=ctx["headers"], timeout=15).json()
        cid = offers["candidates"][0]["candidate_id"]
        r = requests.post(
            f"{BASE_URL}/api/recruitment/recruit",
            json={"candidate_id": cid},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code in (200, 201), r.text
        d = requests.get(f"{BASE_URL}/api/quests/today", headers=ctx["headers"], timeout=15).json()
        rec_q = next(q for q in d["quests"] if q["id"] == "recruit")
        assert rec_q["progress"] >= 1
        assert rec_q["can_claim"] is True

    def test_equip_increments_progress(self, db):
        ctx = _seed_user_with_guild(db)
        aids = _seed_3_advs(db, ctx["guild_id"])
        # Inject inventory item directly
        item_id = str(uuid.uuid4())
        db.items.insert_one({
            "id": item_id, "slug": f"itm-p14-{item_id[:8]}",
            "name": "P14Weapon", "description": "p14 test",
            "item_type": "weapon", "slot": "weapon", "rarity": "Common",
            "level_required": 1, "power_score": 5,
            "strength_bonus": 5, "agility_bonus": 0, "intellect_bonus": 0,
            "endurance_bonus": 0, "faith_bonus": 0,
            "affects_combat": True, "is_cosmetic": False,
            "affects_economy": False, "affects_ranking": False,
            "can_be_sold_for_gold": True, "can_be_sold_for_real_money": False,
            "is_tradeable": True, "is_active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        db.inventory_items.insert_one({
            "id": str(uuid.uuid4()), "guild_id": ctx["guild_id"], "item_id": item_id,
            "quantity": 1, "reserved_qty": 0,
            "acquired_at": "2026-01-01T00:00:00+00:00",
        })
        r = requests.post(
            f"{BASE_URL}/api/adventurers/{aids[0]}/equip",
            json={"item_id": item_id, "slot": "weapon"},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code in (200, 201), r.text
        d = requests.get(f"{BASE_URL}/api/quests/today", headers=ctx["headers"], timeout=15).json()
        eq_q = next(q for q in d["quests"] if q["id"] == "equip")
        assert eq_q["progress"] >= 1
        assert eq_q["can_claim"] is True


class TestClaim:
    def test_claim_success_grants_gold(self, db):
        ctx = _seed_user_with_guild(db)
        # Force-complete the recruit quest progress directly in DB to isolate claim
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db.guilds.update_one(
            {"id": ctx["guild_id"]},
            {"$set": {
                "daily_quest_state": {
                    "window_start_utc": today,
                    "quests": {
                        "expedition_complete": {"progress": 0, "claimed": False},
                        "recruit": {"progress": 1, "claimed": False},
                        "equip": {"progress": 0, "claimed": False},
                    },
                },
                "gold": 100,
            }},
        )
        r = requests.post(
            f"{BASE_URL}/api/quests/claim/recruit", headers=ctx["headers"], timeout=15
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["reward_gold_granted"] == 5
        assert d["guild_gold"] == 105
        # Quest now claimed
        cur = db.guilds.find_one({"id": ctx["guild_id"]})
        assert cur["daily_quest_state"]["quests"]["recruit"]["claimed"] is True

    def test_double_claim_returns_409(self, db):
        ctx = _seed_user_with_guild(db)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db.guilds.update_one(
            {"id": ctx["guild_id"]},
            {"$set": {
                "daily_quest_state": {
                    "window_start_utc": today,
                    "quests": {
                        "expedition_complete": {"progress": 1, "claimed": False},
                        "recruit": {"progress": 0, "claimed": False},
                        "equip": {"progress": 0, "claimed": False},
                    },
                },
                "gold": 100,
            }},
        )
        r1 = requests.post(
            f"{BASE_URL}/api/quests/claim/expedition_complete",
            headers=ctx["headers"], timeout=15,
        )
        assert r1.status_code == 200
        r2 = requests.post(
            f"{BASE_URL}/api/quests/claim/expedition_complete",
            headers=ctx["headers"], timeout=15,
        )
        assert r2.status_code == 409, r2.text

    def test_claim_not_completed_returns_422(self, db):
        ctx = _seed_user_with_guild(db)
        r = requests.post(
            f"{BASE_URL}/api/quests/claim/equip", headers=ctx["headers"], timeout=15
        )
        assert r.status_code == 422, r.text

    def test_unknown_quest_id_404(self, db):
        ctx = _seed_user_with_guild(db)
        r = requests.post(
            f"{BASE_URL}/api/quests/claim/not_real",
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code == 404

    def test_concurrent_claim_only_one_succeeds(self, db):
        """CAS guarantee: two concurrent claims on a completed quest →
        exactly one 200, the other 409 (or 422 if it races just before)."""
        ctx = _seed_user_with_guild(db)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db.guilds.update_one(
            {"id": ctx["guild_id"]},
            {"$set": {
                "daily_quest_state": {
                    "window_start_utc": today,
                    "quests": {
                        "expedition_complete": {"progress": 1, "claimed": False},
                        "recruit": {"progress": 0, "claimed": False},
                        "equip": {"progress": 0, "claimed": False},
                    },
                },
                "gold": 50,
            }},
        )
        import concurrent.futures as cf
        def claim():
            return requests.post(
                f"{BASE_URL}/api/quests/claim/expedition_complete",
                headers=ctx["headers"], timeout=15,
            )
        with cf.ThreadPoolExecutor(max_workers=2) as ex:
            results = [f.result() for f in [ex.submit(claim), ex.submit(claim)]]
        statuses = sorted(r.status_code for r in results)
        assert statuses[0] == 200, f"first must succeed, got {statuses}"
        assert statuses[1] in (409, 422), f"second must reject, got {statuses}"
        # Gold should be +10 exactly (single grant)
        cur = db.guilds.find_one({"id": ctx["guild_id"]})
        assert cur["gold"] == 60


class TestResetAndIsolation:
    def test_stale_window_resets_on_read(self, db):
        ctx = _seed_user_with_guild(db)
        # Set window to yesterday with claimed=true & progress=1
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        db.guilds.update_one(
            {"id": ctx["guild_id"]},
            {"$set": {
                "daily_quest_state": {
                    "window_start_utc": yesterday,
                    "quests": {
                        "expedition_complete": {"progress": 5, "claimed": True},
                        "recruit": {"progress": 3, "claimed": True},
                        "equip": {"progress": 1, "claimed": True},
                    },
                },
            }},
        )
        d = requests.get(f"{BASE_URL}/api/quests/today", headers=ctx["headers"], timeout=15).json()
        for q in d["quests"]:
            assert q["progress"] == 0
            assert q["claimed"] is False
        today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert d["window_start_utc"] == today_iso

    def test_cross_user_isolation(self, db):
        ctx_a = _seed_user_with_guild(db)
        ctx_b = _seed_user_with_guild(db)
        # Force A to have progress
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db.guilds.update_one(
            {"id": ctx_a["guild_id"]},
            {"$set": {
                "daily_quest_state": {
                    "window_start_utc": today,
                    "quests": {
                        "expedition_complete": {"progress": 1, "claimed": False},
                        "recruit": {"progress": 0, "claimed": False},
                        "equip": {"progress": 0, "claimed": False},
                    },
                },
            }},
        )
        # B sees ZERO
        d_b = requests.get(f"{BASE_URL}/api/quests/today", headers=ctx_b["headers"], timeout=15).json()
        for q in d_b["quests"]:
            assert q["progress"] == 0
        # B trying to claim A's quest_id is a no-op for its own state → 422
        r = requests.post(
            f"{BASE_URL}/api/quests/claim/expedition_complete",
            headers=ctx_b["headers"], timeout=15,
        )
        assert r.status_code == 422


class TestOpenAPI:
    def test_paths_count_is_53(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = r.json().get("paths", {})
        # Phase 16: +7 endpoints (chronicle +1, consortiums +6) → 60
        assert len(paths) == 69, f"expected 69, got {len(paths)}"
        assert "/api/quests/today" in paths
        assert "/api/quests/claim/{quest_id}" in paths
