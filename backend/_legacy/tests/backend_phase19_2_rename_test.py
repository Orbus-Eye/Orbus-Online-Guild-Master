"""Phase 19.2 — Adventurer rename endpoint tests.

Endpoint under test: `PATCH /api/adventurers/{id}/name`

Covers:
  - success: first rename increments counter to 1, name updated
  - success: second rename increments counter to 2
  - 409: third rename blocked (limit reached)
  - 422: invalid name (digits/symbols, too short)
  - 404: cross-guild access denied (no leak)
  - case-insensitive name uniqueness within guild
"""
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


def _user(hint="p192"):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P192 {tag[-5:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=h, timeout=15).json()["adventurers"]
    return {"headers": h, "guild_id": g["id"], "advs": advs, "tag": tag}


class TestAdventurerRename:
    def test_rename_success_first(self):
        ctx = _user("rn1")
        assert ctx["advs"], "starter party should not be empty"
        adv = ctx["advs"][0]
        assert adv["rename_count"] == 0
        assert adv["renames_remaining"] == 2

        new_name = f"Aria {uuid.uuid4().hex[:4]}"
        r = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv['id']}/name",
            json={"name": new_name},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()["adventurer"]
        assert body["name"] == new_name
        assert body["rename_count"] == 1
        assert body["renames_remaining"] == 1

    def test_rename_success_second_then_409_third(self):
        ctx = _user("rn2")
        adv = ctx["advs"][0]
        # First
        n1 = f"Brando {uuid.uuid4().hex[:4]}"
        r1 = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv['id']}/name",
            json={"name": n1}, headers=ctx["headers"], timeout=15,
        )
        assert r1.status_code == 200
        assert r1.json()["adventurer"]["rename_count"] == 1
        # Second
        n2 = f"Cyra {uuid.uuid4().hex[:4]}"
        r2 = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv['id']}/name",
            json={"name": n2}, headers=ctx["headers"], timeout=15,
        )
        assert r2.status_code == 200
        body2 = r2.json()["adventurer"]
        assert body2["name"] == n2
        assert body2["rename_count"] == 2
        assert body2["renames_remaining"] == 0
        # Third blocked
        n3 = f"Drago {uuid.uuid4().hex[:4]}"
        r3 = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv['id']}/name",
            json={"name": n3}, headers=ctx["headers"], timeout=15,
        )
        assert r3.status_code == 409, r3.text
        assert "limite rinomine" in r3.json()["detail"].lower()

    def test_rename_validation_too_short(self):
        ctx = _user("rn3")
        adv = ctx["advs"][0]
        r = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv['id']}/name",
            json={"name": "A"},
            headers=ctx["headers"], timeout=15,
        )
        # Pydantic min_length=2 → 422
        assert r.status_code == 422, r.text

    def test_rename_validation_bad_chars(self):
        ctx = _user("rn4")
        adv = ctx["advs"][0]
        r = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv['id']}/name",
            json={"name": "Bob123!@#"},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code == 422, r.text
        # rename_count NOT incremented on validation failure
        advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
        same = next(a for a in advs if a["id"] == adv["id"])
        assert same["rename_count"] == 0

    def test_rename_cross_guild_404(self):
        # Guild A owns the adventurer; Guild B tries to rename → 404 (no leak)
        ctx_a = _user("rnA")
        ctx_b = _user("rnB")
        adv_id = ctx_a["advs"][0]["id"]
        r = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv_id}/name",
            json={"name": "Hacker"},
            headers=ctx_b["headers"], timeout=15,
        )
        assert r.status_code == 404, r.text

    def test_rename_duplicate_name_within_guild_409(self):
        ctx = _user("rn5")
        # Pick two adventurers from same guild
        if len(ctx["advs"]) < 2:
            pytest.skip("starter party has <2 adventurers")
        a1, a2 = ctx["advs"][0], ctx["advs"][1]
        # Rename a1 to a unique base name
        target = f"Eira {uuid.uuid4().hex[:4]}"
        r1 = requests.patch(
            f"{BASE_URL}/api/adventurers/{a1['id']}/name",
            json={"name": target}, headers=ctx["headers"], timeout=15,
        )
        assert r1.status_code == 200
        # Rename a2 to the SAME name (case-insensitive) → 409
        r2 = requests.patch(
            f"{BASE_URL}/api/adventurers/{a2['id']}/name",
            json={"name": target.upper()}, headers=ctx["headers"], timeout=15,
        )
        assert r2.status_code == 409, r2.text
        assert "esiste già" in r2.json()["detail"].lower()

    def test_rename_unauthenticated_401(self):
        # No token → 401/403
        adv_id = str(uuid.uuid4())
        r = requests.patch(
            f"{BASE_URL}/api/adventurers/{adv_id}/name",
            json={"name": "Anon"}, timeout=15,
        )
        assert r.status_code in (401, 403), r.text
