"""ROUND 11.2 TASK 1bis — Adventurer name uniqueness EXCLUDES retired.

Regola corretta:
  Uniqueness vale SOLO tra avventurieri ATTIVI della stessa gilda.
  Retired (`is_retired=True`) mantengono il nome in storia (chronicle,
  expedition_members snapshots, audit) ma non bloccano il riutilizzo.

Coverage (6 backend tests):
  T1bis.01 Recruit nuovo adv + rename a nome di RETIRED → SUCCESS
  T1bis.02 Recruit nuovo adv + rename a nome di ATTIVO → 409 duplicate_active
  T1bis.03 Rename direct a nome di RETIRED → SUCCESS (case-sensitive match)
  T1bis.04 Rename direct a nome di ATTIVO → 409 duplicate_active
  T1bis.05 Case-insensitive: "Alaric" vs "alaric" tra attivi → 409
  T1bis.06 Retired mantiene il nome storico in expedition_members snapshot
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


def _fresh_guild(db, *, prefix: str = "r112t1bis"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R112T1bis {tag[-6:]}"},
                  headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    return h, g["id"]


def _seed_adv(db, *, guild_id: str, name: str, retired: bool = False) -> str:
    cls = db.adventurer_classes.find_one({"slug": "warrior"})
    adv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db.adventurers.insert_one({
        "id": adv_id, "guild_id": guild_id, "name": name,
        "adventurer_class_id": cls["id"], "class_name": cls.get("name", "Warrior"),
        "class_role": cls.get("role"),
        "rarity": "Common",
        "level": 5, "experience": 0,
        "strength": 10, "agility": 10, "intellect": 10, "endurance": 10, "faith": 10,
        "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": retired,
        "retired_at": now if retired else None,
        "rename_count": 0,
        "traits": [], "is_starter": False, "is_test_seed": True,
        "created_at": now, "updated_at": now,
    })
    return adv_id


def _rename(headers: dict, adv_id: str, new_name: str) -> requests.Response:
    return requests.patch(
        f"{BASE_URL}/api/adventurers/{adv_id}/name",
        json={"name": new_name}, headers=headers, timeout=15,
    )


# ─────────────────────────────────────────────────────────────────────────
def test_t1bis_01_rename_to_retired_name_succeeds(db):
    h, gid = _fresh_guild(db)
    _seed_adv(db, guild_id=gid, name="GrahnTheBold", retired=True)
    new_adv = _seed_adv(db, guild_id=gid, name="UnnamedSeed")
    r = _rename(h, new_adv, "GrahnTheBold")
    assert r.status_code == 200, f"expected 200 (retired name reusable): {r.text}"
    fresh = db.adventurers.find_one({"id": new_adv})
    assert fresh["name"] == "GrahnTheBold"
    # The retired adv MUST keep its name unchanged.
    retired_check = db.adventurers.find_one({"guild_id": gid, "is_retired": True})
    assert retired_check["name"] == "GrahnTheBold"


def test_t1bis_02_rename_to_active_name_blocked(db):
    h, gid = _fresh_guild(db)
    _seed_adv(db, guild_id=gid, name="ActiveAlaric", retired=False)
    new_adv = _seed_adv(db, guild_id=gid, name="UnnamedSeed")
    r = _rename(h, new_adv, "ActiveAlaric")
    assert r.status_code == 409, f"expected 409, got {r.status_code}: {r.text}"
    detail = r.json()["detail"]
    if isinstance(detail, dict):
        assert detail.get("code") == "adventurer.name.duplicate_active"
        assert "user_message" in detail
    else:
        # Backward-compat: legacy string detail still works
        assert "già" in detail.lower() or "duplicate" in detail.lower()


def test_t1bis_03_direct_rename_to_retired_name_succeeds(db):
    h, gid = _fresh_guild(db)
    _seed_adv(db, guild_id=gid, name="ShadowKnight", retired=True)
    a = _seed_adv(db, guild_id=gid, name="SeedA")
    r = _rename(h, a, "ShadowKnight")
    assert r.status_code == 200


def test_t1bis_04_direct_rename_to_active_name_blocked(db):
    h, gid = _fresh_guild(db)
    _seed_adv(db, guild_id=gid, name="ActiveSeli", retired=False)
    a = _seed_adv(db, guild_id=gid, name="SeedB")
    r = _rename(h, a, "ActiveSeli")
    assert r.status_code == 409


def test_t1bis_05_case_insensitive_among_active(db):
    h, gid = _fresh_guild(db)
    _seed_adv(db, guild_id=gid, name="Alaric", retired=False)
    a = _seed_adv(db, guild_id=gid, name="SeedC")
    r = _rename(h, a, "alaric")
    assert r.status_code == 409, f"case-insensitive collision missed: {r.text}"


def test_t1bis_06_retired_name_preserved_in_expedition_snapshots(db):
    """Retired adv keeps its name in chronicle/expedition_members. The fix
    MUST NOT modify historical snapshots."""
    h, gid = _fresh_guild(db)
    retired_id = _seed_adv(db, guild_id=gid, name="HistoricHero", retired=True)
    # Seed a chronicle-like snapshot referencing the retired name
    snapshot_id = str(uuid.uuid4())
    db.expedition_members.insert_one({
        "id": snapshot_id, "guild_id": gid,
        "adventurer_id": retired_id,
        "adventurer_name_snapshot": "HistoricHero",
        "expedition_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    # Rename a new active adv to the retired's name
    new_adv = _seed_adv(db, guild_id=gid, name="SeedD")
    r = _rename(h, new_adv, "HistoricHero")
    assert r.status_code == 200
    # Verify the snapshot still carries the retired's historical name.
    snap = db.expedition_members.find_one({"id": snapshot_id})
    assert snap["adventurer_name_snapshot"] == "HistoricHero", \
        "historical snapshot MUST NOT be mutated by the rename fix"
    # Verify retired keeps its own name field too.
    retired = db.adventurers.find_one({"id": retired_id})
    assert retired["name"] == "HistoricHero"
    assert retired.get("is_retired") is True
