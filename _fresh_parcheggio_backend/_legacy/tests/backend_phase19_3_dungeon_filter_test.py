"""Phase 19.3 — Dungeon filter tests."""
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


@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user(hint="p193d"):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P193D {tag[-5:]}"}, headers=h, timeout=15)
    return {"headers": h, "tag": tag}


class TestDungeonFilters:
    def test_D1_team_size_5_only(self):
        ctx = _user("d1")
        r = requests.get(f"{BASE_URL}/api/dungeons?team_size=5",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["filters_applied"]["team_size"] == 5
        for d in body["dungeons"]:
            assert d["required_team_size"] == 5

    def test_D2_pwr_range(self):
        ctx = _user("d2")
        r = requests.get(f"{BASE_URL}/api/dungeons?pwr_min=50&pwr_max=100",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        for d in r.json()["dungeons"]:
            assert 50 <= d["recommended_power"] <= 100

    def test_D3_combined_team_and_difficulty(self):
        ctx = _user("d3")
        r = requests.get(
            f"{BASE_URL}/api/dungeons?team_size=5&difficulty=facile",
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code == 200
        for d in r.json()["dungeons"]:
            assert d["required_team_size"] == 5
            assert d["difficulty"] == 1

    def test_D4_reset_no_params_returns_all(self):
        ctx = _user("d4")
        all_r = requests.get(f"{BASE_URL}/api/dungeons",
                             headers=ctx["headers"], timeout=15).json()
        # Should be all active dungeons
        assert all_r["count"] >= 10  # baseline catalog
        # Sanity: same as no filters
        all_count = all_r["count"]
        r2 = requests.get(f"{BASE_URL}/api/dungeons",
                          headers=ctx["headers"], timeout=15).json()
        assert r2["count"] == all_count

    def test_D5_empty_state_impossible_filter(self):
        ctx = _user("d5")
        r = requests.get(f"{BASE_URL}/api/dungeons?pwr_min=9000&pwr_max=9999",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        assert r.json()["count"] == 0
        assert r.json()["dungeons"] == []

    def test_D6_validation_422(self):
        ctx = _user("d6")
        # Invalid team_size
        r = requests.get(f"{BASE_URL}/api/dungeons?team_size=4",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 422
        # Invalid difficulty alias
        r = requests.get(f"{BASE_URL}/api/dungeons?difficulty=impossibile",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 422
        # pwr_min > pwr_max
        r = requests.get(f"{BASE_URL}/api/dungeons?pwr_min=500&pwr_max=100",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 422
        # Invalid status
        r = requests.get(f"{BASE_URL}/api/dungeons?status=in_cooldown",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 422

    def test_D7_no_regression_unfiltered_call(self):
        """Ensure the existing UI (no params) still gets the same shape."""
        ctx = _user("d7")
        r = requests.get(f"{BASE_URL}/api/dungeons",
                         headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "dungeons" in body
        assert isinstance(body["dungeons"], list)
        if body["dungeons"]:
            d0 = body["dungeons"][0]
            for k in ("id", "slug", "name", "difficulty", "required_team_size", "recommended_power", "unlocked"):
                assert k in d0, f"missing {k}"
