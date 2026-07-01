"""Phase 19.2 — P0.1 Raid Review smoke test.

Validates that `GET /api/raids/{id}` returns a complete, well-shaped payload
for a raid in `completed` status. This guards against payload regressions
that could break the RaidReport frontend page (the original P0.1 symptom).

Coverage:
  1. Lifecycle: register → guild → seed 20 advs → start raid → force-complete.
  2. GET /api/raids/{id} returns 200 with `raid` + `participants` keys.
  3. `raid.status == "completed"`, `outcome` populated, `rewards` present.
  4. `participants` is a list of 20 entries (5 per party × 4 parties).
  5. Each participant carries the snapshots needed by the frontend:
     `adventurer_id`, `party_idx` (1-4), `role_snapshot`, `class_snapshot`,
     `level_snapshot`, `outcome`, `xp_gained`.
  6. Ownership: a foreign guild gets 404 (no leak).
"""
import copy
import os
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
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user(hint="p192r"):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P192R {tag[-5:]}"}, headers=h, timeout=15)
    gid = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]["id"]
    return {"headers": h, "guild_id": gid, "tag": tag}


def _setup_20_advs(db, guild_id):
    """Clone starter party to reach 20 adventurers (raid minimum)."""
    starter = list(db.adventurers.find({"guild_id": guild_id}, {"_id": 0}))
    if len(starter) >= 20:
        return
    base = starter[0]
    for i in range(20 - len(starter)):
        clone = copy.deepcopy(base)
        clone["id"] = str(uuid.uuid4())
        clone["name"] = f"{base['name']}#bulk{i}"
        clone.pop("_id", None)
        db.adventurers.insert_one(clone)


def _start_and_complete_raid(db, ctx):
    """Helper: starts a broken-bastion raid + force-completes it."""
    _setup_20_advs(db, ctx["guild_id"])
    db.guilds.update_one({"id": ctx["guild_id"]}, {"$set": {"last_raid_completed_at": None}})
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    parties = [{"party_idx": i + 1, "adventurer_ids": aid[i * 5:(i + 1) * 5]} for i in range(4)]
    payload = {"raid_slug": "broken-bastion-siege", "parties": parties}
    rs = requests.post(f"{BASE_URL}/api/raids/start", json=payload, headers=ctx["headers"], timeout=15)
    assert rs.status_code == 201, rs.text
    raid_id = rs.json()["raid"]["id"]
    db.raids.update_one(
        {"id": raid_id},
        {"$set": {"ends_at": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()}},
    )
    rc = requests.post(f"{BASE_URL}/api/raids/{raid_id}/complete", headers=ctx["headers"], timeout=15)
    assert rc.status_code == 200, rc.text
    return raid_id


class TestRaidReviewSmoke:
    def test_get_completed_raid_payload_shape(self, db):
        ctx = _user("rev1")
        raid_id = _start_and_complete_raid(db, ctx)

        # Hit the endpoint the frontend RaidReport.jsx page calls.
        r = requests.get(f"{BASE_URL}/api/raids/{raid_id}", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()

        # Top-level keys
        assert "raid" in body and "participants" in body, body.keys()

        # raid_public shape
        raid = body["raid"]
        for k in [
            "id", "guild_id", "raid_dungeon_slug", "status", "outcome",
            "team_power_combined", "recommended_power_combined",
            "success_chance_combined", "success_chance_per_party",
            "raid_score", "started_at", "ends_at", "completed_at",
            "duration_seconds", "rewards", "parties_outcome",
        ]:
            assert k in raid, f"missing key in raid: {k}"
        assert raid["id"] == raid_id
        assert raid["status"] == "completed"
        assert raid["outcome"] in ("victory", "partial", "wipe")
        assert isinstance(raid["rewards"], dict)
        assert isinstance(raid["parties_outcome"], list)
        assert len(raid["parties_outcome"]) == 4

        # Participants array: 4 parties × 5 advs = 20 rows
        parts = body["participants"]
        assert isinstance(parts, list)
        assert len(parts) == 20, f"expected 20 participants, got {len(parts)}"

        # Each participant has the fields the report UI consumes
        for p in parts:
            for k in [
                "id", "raid_id", "adventurer_id", "party_idx",
                "role_snapshot", "class_snapshot", "level_snapshot",
                "outcome", "xp_gained",
            ]:
                assert k in p, f"missing key in participant: {k}"
            assert p["raid_id"] == raid_id
            assert 1 <= p["party_idx"] <= 4
            assert isinstance(p["xp_gained"], int)
            assert isinstance(p["level_snapshot"], int)

        # All 4 party indices represented
        idx_set = {p["party_idx"] for p in parts}
        assert idx_set == {1, 2, 3, 4}, f"missing parties: {idx_set}"

    def test_get_raid_404_cross_guild(self, db):
        ctx_owner = _user("rev2a")
        ctx_other = _user("rev2b")
        raid_id = _start_and_complete_raid(db, ctx_owner)
        # Foreign guild → 404 (ownership check, no leak)
        r = requests.get(f"{BASE_URL}/api/raids/{raid_id}", headers=ctx_other["headers"], timeout=15)
        assert r.status_code == 404, r.text
        assert r.json().get("detail") == "raid_not_found"

    def test_get_raid_404_unknown_id(self):
        ctx = _user("rev3")
        bogus = str(uuid.uuid4())
        r = requests.get(f"{BASE_URL}/api/raids/{bogus}", headers=ctx["headers"], timeout=15)
        assert r.status_code == 404, r.text

    def test_get_raid_requires_auth(self, db):
        ctx = _user("rev4")
        raid_id = _start_and_complete_raid(db, ctx)
        r = requests.get(f"{BASE_URL}/api/raids/{raid_id}", timeout=15)
        assert r.status_code in (401, 403), r.text
