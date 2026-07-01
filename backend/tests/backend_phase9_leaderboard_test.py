"""Phase 9.1 — Public Guild Leaderboard regression smoke + privacy + sort tests.

Hits live REACT_APP_BACKEND_URL. Uses pymongo for direct fixture seeding to
control sort-order edge cases without depending on expedition lifecycle.
"""
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or os.environ.get(
    "BACKEND_URL", "http://localhost:8001"
)
BASE_URL = BASE_URL.rstrip("/")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def _utc_iso(delta_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=delta_minutes)).isoformat()


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


@pytest.fixture(scope="module")
def seeded_guilds(db):
    """Insert 4 distinct guilds with controlled sort fields. Cleanup on teardown."""
    tag = f"p91_{uuid.uuid4().hex[:8]}"
    base_iso = _utc_iso()
    guilds = [
        # Highest peak power
        {
            "id": str(uuid.uuid4()),
            "owner_user_id": str(uuid.uuid4()),
            "name": f"{tag}_alpha",
            "description": "",
            "level": 3,
            "reputation": 20,
            "gold": 100,
            "max_team_power_ever": 250,
            "created_at": _utc_iso(-300),
            "updated_at": base_iso,
        },
        # Same peak as alpha, lower level → tie-break by level
        {
            "id": str(uuid.uuid4()),
            "owner_user_id": str(uuid.uuid4()),
            "name": f"{tag}_bravo",
            "description": "",
            "level": 2,
            "reputation": 30,
            "gold": 100,
            "max_team_power_ever": 250,
            "created_at": _utc_iso(-200),
            "updated_at": base_iso,
        },
        # Lower peak
        {
            "id": str(uuid.uuid4()),
            "owner_user_id": str(uuid.uuid4()),
            "name": f"{tag}_charlie",
            "description": "",
            "level": 5,
            "reputation": 50,
            "gold": 100,
            "max_team_power_ever": 100,
            "created_at": _utc_iso(-100),
            "updated_at": base_iso,
        },
        # Zero peak — should appear last
        {
            "id": str(uuid.uuid4()),
            "owner_user_id": str(uuid.uuid4()),
            "name": f"{tag}_delta",
            "description": "",
            "level": 1,
            "reputation": 0,
            "gold": 100,
            "max_team_power_ever": 0,
            "created_at": _utc_iso(-50),
            "updated_at": base_iso,
        },
    ]
    db.guilds.insert_many([dict(g) for g in guilds])
    yield {"tag": tag, "guilds": guilds}
    db.guilds.delete_many({"id": {"$in": [g["id"] for g in guilds]}})


class TestPhase91Leaderboard:
    def test_endpoint_is_public_no_auth(self):
        """Phase 9.1: leaderboard is fully public — no JWT required."""
        r = requests.get(f"{BASE_URL}/api/leaderboard/guilds", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "entries" in body and "total" in body and "limit" in body

    def test_default_limit_is_50(self):
        r = requests.get(f"{BASE_URL}/api/leaderboard/guilds", timeout=15)
        assert r.status_code == 200
        assert r.json()["limit"] == 50

    def test_limit_max_100_rejects_higher(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=200", timeout=15
        )
        assert r.status_code in (400, 422)

    def test_limit_min_1_rejects_zero(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=0", timeout=15
        )
        assert r.status_code in (400, 422)

    def test_offset_negative_rejected(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?offset=-1", timeout=15
        )
        assert r.status_code in (400, 422)

    def test_offset_above_cap_rejected(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?offset=5000", timeout=15
        )
        assert r.status_code in (400, 422)

    def test_sort_by_peak_power_desc(self, seeded_guilds):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=100", timeout=15
        )
        assert r.status_code == 200
        entries = r.json()["entries"]
        tag = seeded_guilds["tag"]
        ours = [e for e in entries if e["guild_name"].startswith(tag)]
        # alpha + bravo (250) come before charlie (100) come before delta (0)
        peaks = [e["max_team_power_ever"] for e in ours]
        assert peaks == sorted(peaks, reverse=True), peaks

    def test_tie_break_by_level(self, seeded_guilds):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=100", timeout=15
        )
        entries = r.json()["entries"]
        tag = seeded_guilds["tag"]
        # alpha (level 3) before bravo (level 2) — same peak 250
        alpha = next(e for e in entries if e["guild_name"] == f"{tag}_alpha")
        bravo = next(e for e in entries if e["guild_name"] == f"{tag}_bravo")
        assert alpha["rank"] < bravo["rank"]

    def test_privacy_no_sensitive_fields(self, seeded_guilds):
        """Critical: never leak owner_user_id, email, password_hash, is_admin, gold."""
        forbidden = {
            "owner_user_id",
            "email",
            "password_hash",
            "is_admin",
            "gold",
            "_id",
            "description",
        }
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=100", timeout=15
        )
        body = r.json()
        for e in body["entries"]:
            leaked = forbidden.intersection(set(e.keys()))
            assert not leaked, f"leaked fields: {leaked} in {e}"

    def test_entry_required_shape(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=5", timeout=15
        )
        body = r.json()
        if body["entries"]:
            e = body["entries"][0]
            required = {
                "rank",
                "guild_id",
                "guild_name",
                "level",
                "reputation",
                "max_team_power_ever",
                "highest_dungeon_slug",
                "total_expeditions_completed",
                "created_at",
            }
            assert required.issubset(set(e.keys())), set(e.keys())

    def test_ranks_are_progressive_and_absolute(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=10&offset=0", timeout=15
        )
        body = r.json()
        if len(body["entries"]) >= 2:
            ranks = [e["rank"] for e in body["entries"]]
            # progressive, no gaps, starts at 1
            assert ranks[0] == 1
            for i in range(1, len(ranks)):
                assert ranks[i] == ranks[i - 1] + 1

    def test_pagination_offset_yields_absolute_rank(self):
        """offset=2 → first entry has rank=3 (rank is absolute, not page-relative)."""
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=1&offset=2", timeout=15
        )
        body = r.json()
        if body["entries"]:
            assert body["entries"][0]["rank"] == 3

    def test_total_count_reflects_all_guilds(self, seeded_guilds):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=1", timeout=15
        )
        body = r.json()
        # We seeded 4 guilds; total must be at least 4
        assert body["total"] >= 4

    def test_openapi_includes_leaderboard_path(self):
        """OpenAPI surface must expose the new leaderboard path."""
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        assert "/api/leaderboard/guilds" in paths

    def test_guilds_me_still_exposes_max_team_power_ever(self):
        """Phase-8 invariant: /api/guilds/me must still include max_team_power_ever."""
        # Login as tester
        login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "tester@orbus.test", "password": "password123"},
            timeout=15,
        )
        if login.status_code != 200:
            pytest.skip("Tester login unavailable in this env")
        token = login.json()["access_token"]
        gr = requests.get(
            f"{BASE_URL}/api/guilds/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if gr.status_code != 200:
            pytest.skip("Tester has no guild yet")
        guild = gr.json()
        # Field may be at root or under 'guild' wrapper
        if "guild" in guild and isinstance(guild["guild"], dict):
            guild = guild["guild"]
        assert "max_team_power_ever" in guild
