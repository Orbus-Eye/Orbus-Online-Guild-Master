"""Orbus Online: Guild Master — Phase 8 backend tests.

Covers:
- guilds.max_team_power_ever sticky-peak field (default 0, $max semantics)
- Dragon's Hoard gate now honors max_team_power_ever
- GET /api/expeditions/last-completed
- POST /api/expeditions/replay-last
"""
import os
import uuid
import pytest
import requests
from datetime import datetime, timezone
from pymongo import MongoClient


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"


def _load_dbname():
    if "DB_NAME" in os.environ:
        return os.environ["DB_NAME"]
    with open("/app/backend/.env") as f:
        for line in f:
            if line.startswith("DB_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    return "test_database"


MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = _load_dbname()


def _mongo():
    return MongoClient(MONGO_URL)[DB_NAME]


def _rand_email(prefix="p8"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@orbus.test"


def _register_and_guild():
    email = _rand_email()
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "username": "u_" + uuid.uuid4().hex[:6], "password": "pass1234"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    gg = requests.post(
        f"{API}/guilds",
        json={"name": "G_" + uuid.uuid4().hex[:6], "description": ""},
        headers=h, timeout=15,
    )
    assert gg.status_code == 201, gg.text
    return {"headers": h, "guild": gg.json()["guild"], "email": email}


def _recruit_n(headers, n=3):
    out = []
    while len(out) < n:
        cands = requests.get(
            f"{API}/recruitment/candidates", headers=headers, timeout=15
        ).json()["candidates"]
        for c in cands:
            if len(out) >= n:
                break
            r = requests.post(
                f"{API}/recruitment/recruit",
                json={"candidate_id": c["candidate_id"]},
                headers=headers, timeout=15,
            )
            if r.status_code == 201:
                out.append(r.json()["adventurer"])
    return out


def _dungeons(headers):
    return {
        d["slug"]: d
        for d in requests.get(f"{API}/dungeons", headers=headers, timeout=15).json()["dungeons"]
    }


def _start_and_force_complete(u, dungeon_id, adv_ids, success: bool):
    r = requests.post(
        f"{API}/expeditions",
        json={"dungeon_id": dungeon_id, "adventurer_ids": adv_ids},
        headers=u["headers"], timeout=15,
    )
    assert r.status_code == 201, r.text
    exp = r.json()["expedition"]
    _mongo().expeditions.update_one(
        {"id": exp["id"]},
        {"$set": {
            "success_chance": 100 if success else 0,
            "completes_at": "2000-01-01T00:00:00+00:00",
        }},
    )
    # Trigger lazy sweep
    requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15)
    return exp["id"], exp


# ─── A. max_team_power_ever field semantics ─────────────────────────────────
class TestMaxTeamPowerEver:
    def test_initial_value_is_zero(self):
        u = _register_and_guild()
        g = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert "max_team_power_ever" in g
        assert g["max_team_power_ever"] == 0

    def test_set_after_first_expedition(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201
        exp = r.json()["expedition"]
        g = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert g["max_team_power_ever"] == int(exp["final_team_power"])
        assert g["max_team_power_ever"] > 0

    def test_max_is_monotonic_never_decreases(self):
        """A subsequent expedition with LOWER team_power must NOT lower the peak.

        We achieve a lower second power by manually setting the first run's
        max_team_power_ever above the natural roll, then dispatching another
        expedition (same team, no equipment changes) and asserting the field is
        not decremented by $max semantics.
        """
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]

        # Complete first expedition normally
        exp_id, _ = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)

        # Inflate max_team_power_ever to 999 to simulate an earlier higher peak
        _mongo().guilds.update_one(
            {"id": u["guild"]["id"]}, {"$set": {"max_team_power_ever": 999}}
        )

        # Start another expedition (team_power will be much lower than 999)
        r2 = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
            headers=u["headers"], timeout=15,
        )
        assert r2.status_code == 201
        g = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert g["max_team_power_ever"] == 999, (
            "max_team_power_ever was decreased by a lower run; $max semantics broken"
        )

    def test_dragons_hoard_unlocks_via_max_team_power_ever(self):
        """If the guild's peak team_power ever is >= 65, Dragon's Hoard is
        unlocked even when CURRENT best-three is below the threshold."""
        u = _register_and_guild()
        # No adventurers at all → current best-three = 0
        # Manually set peak; guild level stays at 1
        _mongo().guilds.update_one(
            {"id": u["guild"]["id"]}, {"$set": {"max_team_power_ever": 70}}
        )
        ds = _dungeons(u["headers"])
        dh = ds["dragons-hoard"]
        assert dh["unlocked"] is True
        assert dh["unlock_reason"] is None

    def test_dragons_hoard_lock_message_mentions_peak(self):
        """Fresh guild, no recruits, no peak → locked with message that
        references the new peak criterion."""
        # Updated for Round 5 §I (Phase 17.5) — wipe starter roster so peak
        # power calc (best-3 sum) stays 0 and the dungeon remains locked.
        u = _register_and_guild()
        _mongo().adventurers.delete_many({"guild_id": u["guild"]["id"]})
        ds = _dungeons(u["headers"])
        dh = ds["dragons-hoard"]
        assert dh["unlocked"] is False
        reason = dh["unlock_reason"].lower()
        # Must mention both legacy criteria and new peak criterion
        assert "level 2" in reason
        assert "65" in reason
        assert "peak" in reason

    def test_max_updated_via_replay_too(self):
        """A replay dispatch must also bump max_team_power_ever ($max op)."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        exp_id, first = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)
        # Sanity: peak == first run's final_team_power
        g0 = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert g0["max_team_power_ever"] == int(first["final_team_power"])
        # Reset peak artificially to 0, then replay → must rise again
        _mongo().guilds.update_one(
            {"id": u["guild"]["id"]}, {"$set": {"max_team_power_ever": 0}}
        )
        r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r.status_code == 201, r.text
        g1 = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert g1["max_team_power_ever"] > 0


# ─── B. Replay endpoints ────────────────────────────────────────────────────
class TestReplayLastRun:
    def test_last_completed_404_for_fresh_guild(self):
        u = _register_and_guild()
        r = requests.get(f"{API}/expeditions/last-completed", headers=u["headers"], timeout=15)
        assert r.status_code == 404
        assert "no completed" in r.json()["detail"].lower()

    def test_replay_last_404_for_fresh_guild(self):
        u = _register_and_guild()
        r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r.status_code == 404

    def test_last_completed_after_one_run(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        exp_id, _ = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)

        r = requests.get(f"{API}/expeditions/last-completed", headers=u["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["expedition"]["id"] == exp_id
        assert body["expedition"]["status"] == "completed"
        assert set(body["adventurer_ids"]) == set(a["id"] for a in advs)
        assert body["can_replay"] is True
        assert body["cannot_replay_reason"] is None

    def test_replay_happy_path(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)

        r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r.status_code == 201, r.text
        body = r.json()
        new_exp = body["expedition"]
        assert new_exp["status"] == "in_progress"
        assert new_exp["dungeon_id"] == gw["id"]
        # Replay flag set
        assert new_exp.get("is_replay") is True
        # Members are the same 3 originals
        new_member_ids = {m["adventurer_id"] for m in body["members"]}
        assert new_member_ids == {a["id"] for a in advs}

    def test_replay_recomputes_team_power_with_current_equipment(self):
        """After completing a run with no equipment, equip one item then replay.
        The new expedition's equipment_power_bonus must be > 0 (recomputed
        fresh from CURRENT equipment, not snapshotted from the original run)."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        exp_id, first = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)
        assert first["equipment_power_bonus"] == 0

        # Pick a weapon with KNOWN non-zero power (goblin-dagger: +2 AGI, power_score=2)
        items = requests.get(f"{API}/items", timeout=15).json()["items"]
        weapon = next(i for i in items if i["slug"] == "goblin-dagger")
        db = _mongo()
        db.inventory_items.update_one(
            {"guild_id": u["guild"]["id"], "item_id": weapon["id"]},
            {
                "$inc": {"quantity": 1},
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "guild_id": u["guild"]["id"],
                    "item_id": weapon["id"],
                    "acquired_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            upsert=True,
        )
        # Equip on first adventurer
        first_adv = advs[0]
        r_eq = requests.post(
            f"{API}/adventurers/{first_adv['id']}/equip",
            json={"item_id": weapon["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert r_eq.status_code == 201, r_eq.text

        # Replay
        r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r.status_code == 201, r.text
        new_exp = r.json()["expedition"]
        assert new_exp["equipment_power_bonus"] > 0, (
            "Replay should reflect CURRENT equipment, not the original snapshot"
        )
        # And the original expedition must remain unchanged
        original = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
        assert original["equipment_power_bonus"] == 0

    def test_replay_blocked_when_adventurer_in_other_expedition(self):
        """Run #1 completes, then we start a NEW expedition (locking 2 of the
        3 originals) without resolving it. Replay must 400 because one of the
        originals is now is_available=False."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        # Recruit 2 extra so we can build a different team for the in-progress run
        _recruit_n(u["headers"], 2)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        # Run #1 completed
        _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)
        # Verify last-completed
        last = requests.get(f"{API}/expeditions/last-completed", headers=u["headers"], timeout=15).json()
        assert last["can_replay"] is True

        # Now lock one original by sending it on a new expedition (we'll just
        # mark it unavailable in the DB to simulate any locked state)
        _mongo().adventurers.update_one(
            {"id": advs[0]["id"]}, {"$set": {"is_available": False}}
        )

        # last-completed should now report can_replay=False with reason mentioning the adventurer
        last2 = requests.get(f"{API}/expeditions/last-completed", headers=u["headers"], timeout=15).json()
        assert last2["can_replay"] is False
        assert "another expedition" in last2["cannot_replay_reason"].lower() or "currently" in last2["cannot_replay_reason"].lower()

        # POST /replay-last → 400
        r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r.status_code == 400, r.text
        assert "expedition" in r.json()["detail"].lower() or "available" in r.json()["detail"].lower()

    def test_replay_blocked_when_adventurer_removed(self):
        """If one of the original adventurers no longer exists, replay must 400."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)

        # Remove one adventurer completely
        _mongo().adventurers.delete_one({"id": advs[0]["id"]})

        r = requests.get(f"{API}/expeditions/last-completed", headers=u["headers"], timeout=15).json()
        assert r["can_replay"] is False
        assert "guild" in r["cannot_replay_reason"].lower() or "no longer" in r["cannot_replay_reason"].lower()

        r2 = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r2.status_code == 400

    def test_replay_403_when_dungeon_locked_now(self):
        """If the dungeon becomes locked after the original run (e.g. admin
        sets is_active=false), replay returns 404 (dungeon not found) per
        the eligibility check — accept either 400 or 403/404 with a clear
        message."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)

        # Deactivate the dungeon
        _mongo().dungeons.update_one({"id": gw["id"]}, {"$set": {"is_active": False}})
        try:
            r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
            # Either 400 (no longer available) or 403 (gate failed) is acceptable
            assert r.status_code in (400, 403), r.text
            assert "longer" in r.json()["detail"].lower() or "locked" in r.json()["detail"].lower()
        finally:
            _mongo().dungeons.update_one({"id": gw["id"]}, {"$set": {"is_active": True}})

    @pytest.mark.flaky(reruns=2)  # Phase 19 — xdist DB race; see FLAKY_TESTS_AUDIT.md
    def test_replay_does_not_double_reward_original(self):
        """The original expedition's gold_reward stays unchanged after replay."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        exp_id, _ = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)
        original_before = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
        gold_before = original_before["gold_reward"]

        # Replay
        r = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
        assert r.status_code == 201

        # Original unchanged
        original_after = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
        assert original_after["gold_reward"] == gold_before
        assert original_after["status"] == "completed"
        assert original_after["id"] != r.json()["expedition"]["id"]
