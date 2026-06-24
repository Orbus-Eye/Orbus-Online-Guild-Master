"""Phase 11.3 — Onboarding Tutorial tests.

Hits live REACT_APP_BACKEND_URL. Mutates guild/expedition docs directly via
pymongo for deterministic state.
"""
import os
import uuid
from datetime import datetime, timezone
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


def _register_fresh_user(tag_prefix="p113"):
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


def _owner_id(token):
    r = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    body = r.json()
    return body.get("id") or body["user"]["id"]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class TestPhase113OnboardingDefaults:
    def test_new_guild_starts_step_1(self):
        u = _register_fresh_user("ob_new")
        r = requests.get(f"{BASE_URL}/api/guilds/me", headers=u["headers"], timeout=15)
        assert r.status_code == 200
        g = r.json()["guild"]
        assert g["onboarding_step"] == 1
        assert g["onboarding_completed"] is False
        assert g["onboarding_dismissed"] is False
        assert g["onboarding_suggested_step"] == 1

    def test_suggested_step_2_after_partial_recruit(self, db):
        u = _register_fresh_user("ob_step2")
        owner = _owner_id(u["token"])
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        # Inject 1 adventurer (less than 3)
        db.adventurers.insert_one({
            "id": str(uuid.uuid4()), "guild_id": gid,
            "name": "Solo", "adventurer_class_id": "x",
            "class_name": "Warrior", "class_role": "Tank",
            "rarity": "Common", "level": 1, "experience": 0,
            "strength": 5, "agility": 5, "intellect": 5,
            "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
            "traits": [], "is_available": True,
            "created_at": _now_iso(), "updated_at": _now_iso(),
        })
        r = requests.get(f"{BASE_URL}/api/guilds/me", headers=u["headers"], timeout=15)
        g = r.json()["guild"]
        assert g["onboarding_suggested_step"] == 2

    def test_suggested_step_3_with_3_advs_no_expedition(self, db):
        u = _register_fresh_user("ob_step3")
        owner = _owner_id(u["token"])
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        for i in range(3):
            db.adventurers.insert_one({
                "id": str(uuid.uuid4()), "guild_id": gid,
                "name": f"H_{i}", "adventurer_class_id": "x",
                "class_name": "Warrior", "class_role": "Tank",
                "rarity": "Common", "level": 1, "experience": 0,
                "strength": 5, "agility": 5, "intellect": 5,
                "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
                "traits": [], "is_available": True,
                "created_at": _now_iso(), "updated_at": _now_iso(),
            })
        r = requests.get(f"{BASE_URL}/api/guilds/me", headers=u["headers"], timeout=15)
        g = r.json()["guild"]
        assert g["onboarding_suggested_step"] == 3

    def test_suggested_step_4_after_first_completed_expedition(self, db):
        u = _register_fresh_user("ob_step4")
        owner = _owner_id(u["token"])
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        # Synthesize state: 3 advs + 1 completed expedition
        for i in range(3):
            db.adventurers.insert_one({
                "id": str(uuid.uuid4()), "guild_id": gid,
                "name": f"H_{i}", "adventurer_class_id": "x",
                "class_name": "Warrior", "class_role": "Tank",
                "rarity": "Common", "level": 1, "experience": 0,
                "strength": 5, "agility": 5, "intellect": 5,
                "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
                "traits": [], "is_available": True,
                "created_at": _now_iso(), "updated_at": _now_iso(),
            })
        db.expeditions.insert_one({
            "id": str(uuid.uuid4()), "guild_id": gid,
            "dungeon_id": "x", "dungeon_name": "Goblin Warrens",
            "dungeon_slug": "goblin-warrens",
            "status": "completed", "result_summary": "Success",
            "team_power": 50, "success_chance": 80,
            "loot_item_ids": [],
            "created_at": _now_iso(), "completed_at": _now_iso(),
        })
        r = requests.get(f"{BASE_URL}/api/guilds/me", headers=u["headers"], timeout=15)
        g = r.json()["guild"]
        assert g["onboarding_suggested_step"] == 4


class TestPhase113OnboardingPatch:
    def test_patch_step_monotonic(self):
        u = _register_fresh_user("ob_mono")
        # Advance to step 3
        r = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"step": 3}, headers=u["headers"], timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["onboarding_step"] == 3
        # Try to regress to step 2 → clamped to 3
        r2 = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"step": 2}, headers=u["headers"], timeout=15,
        )
        assert r2.status_code == 200
        assert r2.json()["onboarding_step"] == 3

    def test_patch_dismissed(self):
        u = _register_fresh_user("ob_dismiss")
        r = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"dismissed": True}, headers=u["headers"], timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["onboarding_dismissed"] is True
        # Verify it persists via GET /guilds/me
        g = requests.get(f"{BASE_URL}/api/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert g["onboarding_dismissed"] is True

    def test_patch_completed_is_sticky(self):
        u = _register_fresh_user("ob_complete")
        r = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"completed": True}, headers=u["headers"], timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["onboarding_completed"] is True
        # Try to unset → ignored
        r2 = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"completed": False}, headers=u["headers"], timeout=15,
        )
        assert r2.json()["onboarding_completed"] is True

    def test_patch_validation_step_out_of_range(self):
        u = _register_fresh_user("ob_oor")
        r = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"step": 99}, headers=u["headers"], timeout=15,
        )
        assert r.status_code == 422
        r2 = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"step": 0}, headers=u["headers"], timeout=15,
        )
        assert r2.status_code == 422

    def test_patch_requires_auth(self):
        r = requests.patch(
            f"{BASE_URL}/api/guilds/onboarding",
            json={"step": 2}, timeout=15,
        )
        assert r.status_code in (401, 403)


class TestPhase113LazyMigration:
    def test_mature_guild_auto_completed(self, db):
        u = _register_fresh_user("ob_migrate")
        owner = _owner_id(u["token"])
        gid = db.guilds.find_one({"owner_user_id": owner})["id"]
        # Add 3 advs + 1 completed expedition
        for i in range(3):
            db.adventurers.insert_one({
                "id": str(uuid.uuid4()), "guild_id": gid,
                "name": f"M_{i}", "adventurer_class_id": "x",
                "class_name": "Warrior", "class_role": "Tank",
                "rarity": "Common", "level": 1, "experience": 0,
                "strength": 5, "agility": 5, "intellect": 5,
                "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
                "traits": [], "is_available": True,
                "created_at": _now_iso(), "updated_at": _now_iso(),
            })
        db.expeditions.insert_one({
            "id": str(uuid.uuid4()), "guild_id": gid,
            "dungeon_id": "x", "dungeon_name": "Goblin Warrens",
            "dungeon_slug": "goblin-warrens",
            "status": "completed", "result_summary": "Success",
            "team_power": 50, "success_chance": 80,
            "loot_item_ids": [],
            "created_at": _now_iso(), "completed_at": _now_iso(),
        })
        # Strip onboarding_completed field to simulate pre-11.3 mature guild
        db.guilds.update_one(
            {"id": gid},
            {"$unset": {"onboarding_completed": "", "onboarding_step": ""}},
        )
        # Verify field is gone
        raw = db.guilds.find_one({"id": gid})
        assert "onboarding_completed" not in raw
        # GET /guilds/me triggers lazy migration
        r = requests.get(f"{BASE_URL}/api/guilds/me", headers=u["headers"], timeout=15)
        g = r.json()["guild"]
        assert g["onboarding_completed"] is True, "lazy migration should set completed=true"
        # Verify it persisted
        raw2 = db.guilds.find_one({"id": gid})
        assert raw2["onboarding_completed"] is True


class TestPhase113NoRegressions:
    def test_openapi_paths_count_39(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = r.json().get("paths", {})
        assert len(paths) == 40, f"expected 40, got {len(paths)}"

    def test_onboarding_path_present(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = r.json().get("paths", {})
        assert "/api/guilds/onboarding" in paths

    def test_existing_endpoints_unchanged(self):
        # Spot-check: leaderboard, recruitment/refresh, dungeons all still respond
        r1 = requests.get(f"{BASE_URL}/api/leaderboard/guilds?limit=5", timeout=15)
        assert r1.status_code == 200
        r2 = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = r2.json().get("paths", {})
        for required in (
            "/api/recruitment/refresh",
            "/api/recruitment/candidates",
            "/api/leaderboard/guilds",
            "/api/dungeons",
            "/api/expeditions/replay-last",
        ):
            assert required in paths, f"regression: {required} missing"
