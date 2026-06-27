"""ROUND 6B.2a — Backend tests: adventurer cap, retire, require_unlocked.

Coverage:
  • cap_state helper math (no HTTP)
  • POST /api/recruitment/recruit cap guard (422 detail)
  • POST /api/adventurers/{id}/retire edge cases:
        already_retired, in_expedition, in_squad, equipped (with/without force)
  • require_unlocked → 423 with full payload across the 14 gated endpoints.
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


def _fresh_user(db, prefix="r6b2a"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R6B2A {tag[-6:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    return h, g


def _seed_dorm_level(db, guild_id, level):
    """Set the dormitories level on guild_structures for cap tests."""
    requests.get(f"{BASE_URL}/api/territory",
                 headers={"Authorization": "Bearer fake"}, timeout=5)  # noop
    # The doc was lazy-created by something — ensure it exists then patch.
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            f"structures.dormitories.level": level,
            f"structures.dormitories.is_unlocked": level >= 1,
        }},
        upsert=True,
    )


def _set_structure(db, guild_id, slug, level):
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            f"structures.{slug}.level": level,
            f"structures.{slug}.is_unlocked": level >= 1,
        }},
        upsert=True,
    )


# ─── Cap guard ────────────────────────────────────────────────────────────

def test_recruitment_cap_reached_blocks_with_422(db):
    h, g = _fresh_user(db, "cap")
    # Force the lazy doc creation
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    # Onboarding already seeds 5 starter adventurers; with dormitories Lv1
    # (cap=5), the user is already at or above cap. No need to insert more.
    _set_structure(db, g["id"], "dormitories", 1)
    cand = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15)
    candidate_id = cand.json()["candidates"][0]["candidate_id"]
    r = requests.post(f"{BASE_URL}/api/recruitment/recruit",
                      json={"candidate_id": candidate_id}, headers=h, timeout=15)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["code"] == "recruitment.cap_reached"
    assert detail["cap"] == 5
    assert detail["current"] >= 5
    assert detail["dormitory_level"] == 1
    assert "Roster pieno" in detail["user_message"]


# ─── Retire edge cases ────────────────────────────────────────────────────

def _adv(db, guild_id):
    """Insert a fake adventurer with all minimum stats; returns its id."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    aid = str(uuid.uuid4())
    db.adventurers.insert_one({
        "id": aid, "guild_id": guild_id, "name": "Retire Test",
        "class_slug": "warrior", "level": 1, "experience": 0,
        "strength": 5, "agility": 5, "intellect": 5,
        "endurance": 5, "faith": 5, "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": False,
        "is_test_user_data": True,
        "adventurer_class_id": None,
        "class_name": "Warrior", "class_role": "Tank",
        "rarity": "Common", "traits": [],
        "rename_count": 0,
        "created_at": now, "updated_at": now,
    })
    return aid


def test_retire_already_retired_is_409(db):
    h, g = _fresh_user(db, "ret_idem")
    aid = _adv(db, g["id"])
    db.adventurers.update_one({"id": aid}, {"$set": {"is_retired": True}})
    r = requests.post(f"{BASE_URL}/api/adventurers/{aid}/retire",
                      json={}, headers=h, timeout=15)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "adventurer.already_retired"


def test_retire_in_expedition_is_409(db):
    h, g = _fresh_user(db, "ret_exp")
    aid = _adv(db, g["id"])
    db.expeditions.insert_one({
        "id": str(uuid.uuid4()), "guild_id": g["id"],
        "adventurer_ids": [aid], "status": "in_progress",
        "is_test_user_data": True,
    })
    r = requests.post(f"{BASE_URL}/api/adventurers/{aid}/retire",
                      json={}, headers=h, timeout=15)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "adventurer.in_expedition"


def test_retire_in_squad_is_409(db):
    h, g = _fresh_user(db, "ret_squad")
    aid = _adv(db, g["id"])
    db.squads.insert_one({
        "id": str(uuid.uuid4()), "guild_id": g["id"],
        "name": "Test Squad", "name_lower": "test squad",
        "squad_type": "dungeon_3", "adventurer_ids": [aid, "x", "y"],
        "is_archived": False, "is_test_user_data": True,
    })
    r = requests.post(f"{BASE_URL}/api/adventurers/{aid}/retire",
                      json={}, headers=h, timeout=15)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "adventurer.in_squad"
    assert len(detail["squads"]) == 1


def test_retire_equipped_blocks_without_force(db):
    h, g = _fresh_user(db, "ret_eq")
    aid = _adv(db, g["id"])
    db.equipped_items.insert_one({
        "id": str(uuid.uuid4()),
        "instance_id": str(uuid.uuid4()), "adventurer_id": aid,
        "guild_id": g["id"], "slot": "weapon",
        "is_test_user_data": True,
    })
    r = requests.post(f"{BASE_URL}/api/adventurers/{aid}/retire",
                      json={}, headers=h, timeout=15)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "adventurer.equipped"


def test_retire_equipped_with_force_unequip_succeeds(db):
    h, g = _fresh_user(db, "ret_force")
    aid = _adv(db, g["id"])
    db.equipped_items.insert_one({
        "id": str(uuid.uuid4()),
        "instance_id": str(uuid.uuid4()), "adventurer_id": aid,
        "guild_id": g["id"], "slot": "weapon",
        "is_test_user_data": True,
    })
    r = requests.post(f"{BASE_URL}/api/adventurers/{aid}/retire",
                      json={"force_unequip": True, "reason": "test"},
                      headers=h, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["adventurer_id"] == aid
    assert body["retired_at"]
    assert len(body["equipment_returned"]) == 1
    # Verify the adventurer is now retired and excluded from default listing.
    r2 = requests.get(f"{BASE_URL}/api/adventurers", headers=h, timeout=15)
    assert r2.status_code == 200, r2.text
    ids = [a["id"] for a in r2.json()["adventurers"]]
    assert aid not in ids
    # Include retired: should reappear
    r3 = requests.get(f"{BASE_URL}/api/adventurers?include_retired=true",
                      headers=h, timeout=15)
    assert r3.status_code == 200, r3.text
    ids = [a["id"] for a in r3.json()["adventurers"]]
    assert aid in ids


def test_retire_404_for_unknown_adventurer(db):
    h, _ = _fresh_user(db, "ret_404")
    r = requests.post(f"{BASE_URL}/api/adventurers/nonexistent/retire",
                      json={}, headers=h, timeout=15)
    assert r.status_code == 404


# ─── require_unlocked → 423 on the 14 gated endpoints ─────────────────────

# (endpoint method/path, body sample, expected required_structure)
# All 14 calls should return 423 when the relevant structure is Lv0.
GUARDED_ENDPOINTS = [
    ("POST", "/api/shop/buy",                       {"slug": "x", "quantity": 1}, "market_stall"),
    ("POST", "/api/shop/sell",                      {"slug": "x", "quantity": 1}, "market_stall"),
    ("POST", "/api/auction/listings",               {"instance_id": "x", "price_gold": 1}, "auction_house"),
    ("POST", "/api/auction/listings/dummy/buy",     {}, "auction_house"),
    ("POST", "/api/inventory/dummy/refine",         {}, "forge"),
    ("POST", "/api/inventory/dummy/enchant",        {"enchant_slug": "x"}, "forge"),
    ("POST", "/api/inventory/dummy/disenchant",     {}, "forge"),
    ("POST", "/api/inventory/dummy/reroll-affixes", {}, "forge"),
    ("POST", "/api/recipes/dummy/craft",            {}, "workshop"),
    ("POST", "/api/raids/start",                    {"slug": "x", "parties": []}, "war_room"),
    ("POST", "/api/consortiums",                    {"name": "TestCons"}, "consortium_hall"),
    ("POST", "/api/consortiums/dummy/join",         {}, "consortium_hall"),
    ("POST", "/api/chat/global",                    {"message_text": "x"}, "communication_hall"),
    ("POST", "/api/chat/consortium/dummy",          {"message_text": "x"}, "communication_hall"),
]


@pytest.mark.parametrize("method,path,body,required_structure", GUARDED_ENDPOINTS)
def test_guard_returns_423_when_structure_locked(db, method, path, body, required_structure):
    """Every gated endpoint must return 423 with the canonical payload when
    its structure is locked. We force ALL relevant structures to Lv0."""
    h, g = _fresh_user(db, f"gd_{required_structure[:6]}")
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    # Reset all unlock-relevant structures to Lv0.
    for slug in ("market_stall", "auction_house", "forge", "workshop",
                 "war_room", "consortium_hall", "communication_hall"):
        _set_structure(db, g["id"], slug, 0)
    r = requests.request(method, f"{BASE_URL}{path}", json=body, headers=h, timeout=15)
    assert r.status_code == 423, f"{path} expected 423, got {r.status_code}: {r.text[:200]}"
    detail = r.json()["detail"]
    assert detail["code"] == "feature.locked"
    assert detail["required_structure"] == required_structure
    assert "Visita il Territorio" in detail["user_message"]


def test_guard_allows_passthrough_when_unlocked(db):
    """Chat global endpoint with communication_hall Lv1 should NOT 423.
    (It may still 400/422 due to other validations, but never 423.)"""
    h, g = _fresh_user(db, "gd_pass")
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    _set_structure(db, g["id"], "communication_hall", 1)
    r = requests.post(f"{BASE_URL}/api/chat/global",
                      json={"message_text": "happy path"}, headers=h, timeout=15)
    assert r.status_code in (201, 200), r.text
