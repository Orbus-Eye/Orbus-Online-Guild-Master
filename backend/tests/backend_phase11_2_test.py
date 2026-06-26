"""Phase 11.2 — Soft Gates + Recruitment Refresh Limit tests.

Hits live REACT_APP_BACKEND_URL. Mutates guild docs directly via pymongo
for deterministic state (max_team_power_ever, refresh window backdating).
"""
import os
import time
import uuid
from datetime import datetime, timezone, timedelta
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


def _register_fresh_user(tag_prefix="p112"):
    tag = f"{tag_prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "username": tag, "password": "Test12345!"},
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r2 = requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"Guild_{tag}", "description": ""},
        headers=h, timeout=15,
    )
    assert r2.status_code in (200, 201), r2.text
    return {"email": email, "token": token, "headers": h, "tag": tag}


# ─── PART A — Soft Gates ────────────────────────────────────────────────────


class TestPhase112Gates:
    def test_fresh_guild_sees_t2_t3_locked_with_reason(self):
        # Updated for Round 5 §I (Phase 17.5) — wipe the auto-seeded starter
        # roster so peak-power / adv-count gates stay at 0 (pre-Round-5 fresh
        # guild equivalent).
        u = _register_fresh_user("gates")
        owner = _user_id_from_token(u["token"])
        db = MongoClient(MONGO_URL)[DB_NAME]
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        db.adventurers.delete_many({"guild_id": gid})
        r = requests.get(f"{BASE_URL}/api/dungeons", headers=u["headers"], timeout=15)
        assert r.status_code == 200
        dungeons = r.json() if isinstance(r.json(), list) else r.json().get("dungeons", [])
        by_slug = {d["slug"]: d for d in dungeons}

        # T1 goblin-warrens always unlocked
        assert by_slug["goblin-warrens"]["unlocked"] is True

        # T2 new dungeons locked
        for slug in ("druid-grove", "cursed-mines", "sunken-library", "shadow-crypts"):
            d = by_slug[slug]
            assert d["unlocked"] is False, f"{slug} should be locked for fresh guild"
            assert d.get("unlock_reason"), f"{slug} missing unlock_reason"

        # T3 dungeons locked
        for slug in ("lich-sanctum", "storm-spire", "dragons-hoard"):
            d = by_slug[slug]
            assert d["unlocked"] is False, f"{slug} should be locked for fresh guild"
            assert d.get("unlock_reason"), f"{slug} missing unlock_reason"

    def test_dispatch_on_locked_dungeon_returns_403(self, db):
        u = _register_fresh_user("disp_lock")
        guild = db.guilds.find_one({"owner_user_id": _user_id_from_token(u["token"])})
        # Bypass adventurer creation to force pure gate check; we supply made-up ids
        r = requests.post(
            f"{BASE_URL}/api/expeditions",
            headers=u["headers"], timeout=15,
            json={
                "dungeon_id": db.dungeons.find_one({"slug": "lich-sanctum"})["id"],
                "adventurer_ids": ["aaaaaaaa", "bbbbbbbb", "cccccccc"],
            },
        )
        assert r.status_code == 403, r.text
        assert "Dungeon locked" in r.text or "locked" in r.text.lower()

    def test_unlock_t2_when_peak_meets_threshold(self, db):
        """Backdate max_team_power_ever on the guild — druid-grove (45+) unlocks."""
        u = _register_fresh_user("unlock_t2")
        owner = _user_id_from_token(u["token"])
        db.guilds.update_one(
            {"owner_user_id": owner},
            {"$set": {"max_team_power_ever": 50}},
        )
        # Need ≥3 adventurers for the gate AND-rule
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        for i in range(3):
            db.adventurers.insert_one({
                "id": str(uuid.uuid4()), "guild_id": gid,
                "name": f"Bot_{i}", "adventurer_class_id": "x",
                "class_name": "Warrior", "class_role": "Tank",
                "rarity": "Common", "level": 1, "experience": 0,
                "strength": 5, "agility": 5, "intellect": 5,
                "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
                "traits": [], "is_available": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })

        r = requests.get(f"{BASE_URL}/api/dungeons", headers=u["headers"], timeout=15)
        by_slug = {d["slug"]: d for d in (
            r.json() if isinstance(r.json(), list) else r.json().get("dungeons", [])
        )}
        assert by_slug["druid-grove"]["unlocked"] is True  # peak 50 >= 45
        assert by_slug["cursed-mines"]["unlocked"] is True  # peak 50 >= 50
        assert by_slug["sunken-library"]["unlocked"] is False  # peak 50 < 55
        assert by_slug["lich-sanctum"]["unlocked"] is False  # need 60 or lvl 2
        assert by_slug["storm-spire"]["unlocked"] is False

    def test_dragons_hoard_sticky_invariant(self, db):
        """Phase 8 sticky semantics: peak >= 65 → unlock, even at guild lvl 1."""
        u = _register_fresh_user("dh_sticky")
        owner = _user_id_from_token(u["token"])
        db.guilds.update_one(
            {"owner_user_id": owner},
            {"$set": {"max_team_power_ever": 70, "level": 1}},
        )
        r = requests.get(f"{BASE_URL}/api/dungeons", headers=u["headers"], timeout=15)
        by_slug = {d["slug"]: d for d in (
            r.json() if isinstance(r.json(), list) else r.json().get("dungeons", [])
        )}
        assert by_slug["dragons-hoard"]["unlocked"] is True

    def test_shadow_crypts_gate_unchanged(self, db):
        """Phase 7 invariant: shadow-crypts requires lvl≥1 AND adv_count≥3."""
        # Updated for Round 5 §I (Phase 17.5) — wipe the auto-seeded starter
        # roster so we can exercise the "0 advs → locked" state explicitly.
        u = _register_fresh_user("sc_gate")
        owner = _user_id_from_token(u["token"])
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        db.adventurers.delete_many({"guild_id": gid})
        # 0 adventurers initially → locked
        r = requests.get(f"{BASE_URL}/api/dungeons", headers=u["headers"], timeout=15)
        by_slug = {d["slug"]: d for d in (
            r.json() if isinstance(r.json(), list) else r.json().get("dungeons", [])
        )}
        assert by_slug["shadow-crypts"]["unlocked"] is False
        # Add 3 adventurers → unlocked (level is default 1)
        for i in range(3):
            db.adventurers.insert_one({
                "id": str(uuid.uuid4()), "guild_id": gid,
                "name": f"X_{i}", "adventurer_class_id": "x",
                "class_name": "Warrior", "class_role": "Tank",
                "rarity": "Common", "level": 1, "experience": 0,
                "strength": 5, "agility": 5, "intellect": 5,
                "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
                "traits": [], "is_available": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        r2 = requests.get(f"{BASE_URL}/api/dungeons", headers=u["headers"], timeout=15)
        by_slug2 = {d["slug"]: d for d in (
            r2.json() if isinstance(r2.json(), list) else r2.json().get("dungeons", [])
        )}
        assert by_slug2["shadow-crypts"]["unlocked"] is True

    def test_goblin_warrens_always_unlocked(self):
        """Phase 7 invariant: goblin-warrens unlocked for any guild, any state."""
        u = _register_fresh_user("gw")
        r = requests.get(f"{BASE_URL}/api/dungeons", headers=u["headers"], timeout=15)
        by_slug = {d["slug"]: d for d in (
            r.json() if isinstance(r.json(), list) else r.json().get("dungeons", [])
        )}
        assert by_slug["goblin-warrens"]["unlocked"] is True


def _user_id_from_token(token: str) -> str:
    r = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    body = r.json()
    return body.get("id") or body["user"]["id"]


# ─── PART B — Recruitment Refresh Limit ─────────────────────────────────────


class TestPhase112Refresh:
    def test_new_guild_has_3_free_refreshes(self):
        u = _register_fresh_user("ref_new")
        r = requests.get(
            f"{BASE_URL}/api/recruitment/candidates",
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert d["refreshes_remaining_today"] == 3
        assert d["next_refresh_cost_gold"] == 0
        assert d["can_refresh"] is True
        assert "next_refresh_reset_at" in d

    def test_get_candidates_does_not_consume_refresh(self):
        u = _register_fresh_user("ref_view")
        for _ in range(5):
            r = requests.get(
                f"{BASE_URL}/api/recruitment/candidates",
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 200
            assert r.json()["refreshes_remaining_today"] == 3

    def test_3_free_refreshes_then_paid_10g(self):
        u = _register_fresh_user("ref_3free")
        # 3 free refreshes
        for i in range(3):
            r = requests.post(
                f"{BASE_URL}/api/recruitment/refresh",
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["refresh_cost_paid"] == 0
            assert d["refreshes_remaining_today"] == 2 - i
        # 4th refresh: 10 gold
        r = requests.post(
            f"{BASE_URL}/api/recruitment/refresh",
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["refresh_cost_paid"] == 10
        assert d["next_refresh_cost_gold"] == 20

    def test_paid_scaling_10_20_30_cap(self):
        u = _register_fresh_user("ref_scale")
        # consume 3 free + 1st paid (10g)
        for _ in range(3):
            requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        r1 = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        assert r1.json()["refresh_cost_paid"] == 10
        r2 = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        assert r2.json()["refresh_cost_paid"] == 20
        r3 = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        assert r3.json()["refresh_cost_paid"] == 30
        r4 = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        assert r4.json()["refresh_cost_paid"] == 30  # cap at 30

    def test_insufficient_gold_402(self, db):
        u = _register_fresh_user("ref_poor")
        owner = _user_id_from_token(u["token"])
        # consume 3 free, then drain gold below 10
        for _ in range(3):
            requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        db.guilds.update_one(
            {"owner_user_id": owner}, {"$set": {"gold": 5}},
        )
        r = requests.post(
            f"{BASE_URL}/api/recruitment/refresh",
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 402, r.text
        # Gold not scaled
        g = db.guilds.find_one({"owner_user_id": owner})
        assert g["gold"] == 5

    def test_daily_reset_simulated(self, db):
        u = _register_fresh_user("ref_reset")
        owner = _user_id_from_token(u["token"])
        # consume 3 free
        for _ in range(3):
            requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        # Backdate window to yesterday
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        db.guilds.update_one(
            {"owner_user_id": owner},
            {"$set": {"recruitment_refresh_window_start_utc": yesterday.isoformat()}},
        )
        # Next refresh should be free again (reset semantics)
        r = requests.post(
            f"{BASE_URL}/api/recruitment/refresh",
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert d["refresh_cost_paid"] == 0
        assert d["refreshes_remaining_today"] == 2

    def test_refresh_state_isolated_between_guilds(self):
        u1 = _register_fresh_user("ref_iso1")
        u2 = _register_fresh_user("ref_iso2")
        # u1 consumes all 3 free
        for _ in range(3):
            requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u1["headers"], timeout=15)
        # u2 still has 3 free
        r2 = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=u2["headers"], timeout=15)
        assert r2.json()["refreshes_remaining_today"] == 3

    def test_recruit_after_refresh_works(self):
        u = _register_fresh_user("ref_recruit")
        r1 = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        cand_id = r1.json()["candidates"][0]["candidate_id"]
        r2 = requests.post(
            f"{BASE_URL}/api/recruitment/recruit",
            json={"candidate_id": cand_id},
            headers=u["headers"], timeout=15,
        )
        assert r2.status_code == 201, r2.text
        assert "adventurer" in r2.json()

    def test_no_negative_gold_on_refresh(self, db):
        u = _register_fresh_user("ref_neg")
        owner = _user_id_from_token(u["token"])
        # Consume all free → next costs 10g
        for _ in range(3):
            requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        # Set gold to exactly 9 (below the 10g cost)
        db.guilds.update_one({"owner_user_id": owner}, {"$set": {"gold": 9}})
        r = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=u["headers"], timeout=15)
        assert r.status_code == 402
        g = db.guilds.find_one({"owner_user_id": owner})
        assert g["gold"] == 9  # unchanged
