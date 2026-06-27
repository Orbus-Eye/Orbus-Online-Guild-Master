"""ROUND 6B.1 — Territory endpoint tests (e2e via HTTP).

Covers:
  - lazy creation of guild_structures on first GET
  - purchase: valid → 200; invalid slug → 422; already unlocked → 409;
    prereq unmet → 423; gold insufficient → 422
  - upgrade: locked → 423; max-level → 409; legacy-only level → 422
  - 401 without JWT
  - PII guard: no email / no _id / no owner_user_id in response payload
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


def _fresh_user(db, prefix="r6b1"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R6B1 {tag[-6:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    # Give plenty of gold so cost checks pass
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 50000}})
    return token, h, g, email


def _give_material(db, guild_id, slug, qty):
    """ROUND 6B.3 regression — atomic-debit needs real material rows. Helper
    matches the one in `backend_round6b3_territory_atomicity_test.py`."""
    tpl = db.items.find_one({"slug": slug}, {"id": 1})
    assert tpl, f"material template '{slug}' not seeded"
    existing = db.inventory_items.find_one(
        {"guild_id": guild_id, "item_id": tpl["id"]},
        {"id": 1, "quantity": 1},
    )
    if existing:
        db.inventory_items.update_one(
            {"id": existing["id"]},
            {"$inc": {"quantity": int(qty)}},
        )
    else:
        db.inventory_items.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": guild_id,
            "item_id": tpl["id"],
            "instance_id": str(uuid.uuid4()),
            "quantity": int(qty),
            "is_bound": True,
            "acquired_at": "2026-06-27T00:00:00+00:00",
        })


def test_get_territory_lazy_creates_doc(db):
    _, h, g, _ = _fresh_user(db, "r6b1_get")
    r = requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    territory = body["territory"]
    assert territory["guild_id"] == g["id"]
    structs = territory["structures"]
    # All 11 slugs present
    expected = {
        "guild_hall", "dormitories", "expedition_board", "war_room",
        "market_stall", "auction_house", "workshop", "forge",
        "consortium_hall", "communication_hall", "training_grounds",
    }
    assert set(structs.keys()) == expected
    # Defaults: 3 unlocked Lv1, rest locked Lv0
    assert structs["guild_hall"]["level"] == 1
    assert structs["dormitories"]["level"] == 1
    assert structs["expedition_board"]["level"] == 1
    assert structs["forge"]["level"] == 0
    assert structs["forge"]["is_unlocked"] is False
    # Doc actually persisted
    assert db.guild_structures.find_one({"guild_id": g["id"]}) is not None


def test_get_territory_no_pii(db):
    _, h, g, email = _fresh_user(db, "r6b1_pii")
    r = requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    body = r.json()
    territory = body["territory"]
    serialized = repr(body)
    assert email not in serialized
    assert "owner_user_id" not in serialized
    # ObjectId field check: top-level doc must NOT carry `_id` key.
    assert "_id" not in territory
    for slug, st in territory["structures"].items():
        assert "_id" not in st, f"_id leaked in {slug}"


def test_get_territory_requires_auth():
    r = requests.get(f"{BASE_URL}/api/territory", timeout=15)
    assert r.status_code in (401, 403)


def test_purchase_invalid_slug(db):
    _, h, _, _ = _fresh_user(db, "r6b1_inv")
    r = requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "totally_fake"}, headers=h, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "structure_slug.invalid"


def test_purchase_market_stall_then_already_unlocked(db):
    _, h, _, _ = _fresh_user(db, "r6b1_mk")
    # First purchase succeeds — guild_hall Lv1 satisfies the prerequisite.
    r1 = requests.post(f"{BASE_URL}/api/territory/purchase",
                       json={"structure_slug": "market_stall"}, headers=h, timeout=15)
    assert r1.status_code == 200, r1.text
    ms = r1.json()["territory"]["structures"]["market_stall"]
    assert ms["level"] == 1 and ms["is_unlocked"] is True
    assert ms["acquired_via"] == "purchase"
    # Second purchase → 409 already_unlocked
    r2 = requests.post(f"{BASE_URL}/api/territory/purchase",
                       json={"structure_slug": "market_stall"}, headers=h, timeout=15)
    assert r2.status_code == 409
    assert r2.json()["detail"]["code"] == "structure.already_unlocked"


def test_purchase_forge_prerequisites_unmet(db):
    _, h, _, _ = _fresh_user(db, "r6b1_fpre")
    # Forge requires guild_hall Lv2 + workshop Lv1 — both unmet at start.
    r = requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "forge"}, headers=h, timeout=15)
    assert r.status_code == 423
    detail = r.json()["detail"]
    assert detail["code"] == "structure.prerequisites_unmet"
    structures_unmet = {x["structure"] for x in detail["unmet"]}
    assert {"guild_hall", "workshop"}.issubset(structures_unmet)


def test_upgrade_locked_structure_returns_423(db):
    _, h, _, _ = _fresh_user(db, "r6b1_uplock")
    # war_room is locked (Lv0) at start → upgrade should refuse.
    r = requests.post(f"{BASE_URL}/api/territory/upgrade",
                      json={"structure_slug": "war_room"}, headers=h, timeout=15)
    assert r.status_code == 423
    assert r.json()["detail"]["code"] == "structure.locked"


def test_upgrade_market_stall_lv1_to_lv2(db):
    _, h, g, _ = _fresh_user(db, "r6b1_upok")
    requests.post(f"{BASE_URL}/api/territory/purchase",
                  json={"structure_slug": "market_stall"}, headers=h, timeout=15)
    # ROUND 6B.3 regression — Lv2 needs iron_shard 3 (atomic debit now enforced).
    _give_material(db, g["id"], "iron_shard", 3)
    r = requests.post(f"{BASE_URL}/api/territory/upgrade",
                      json={"structure_slug": "market_stall"}, headers=h, timeout=15)
    assert r.status_code == 200, r.text
    ms = r.json()["territory"]["structures"]["market_stall"]
    assert ms["level"] == 2
    assert ms["upgraded_at"] is not None


def test_upgrade_gold_insufficient(db):
    _, h, g, _ = _fresh_user(db, "r6b1_gold")
    # Drain gold to 0 — first upgrade cost is at least 50g.
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 0}})
    r = requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "market_stall"}, headers=h, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "resources.gold_insufficient"


def test_purchase_requires_auth():
    r = requests.post(f"{BASE_URL}/api/territory/purchase",
                      json={"structure_slug": "market_stall"}, timeout=15)
    assert r.status_code in (401, 403)


def test_audit_event_written_on_purchase(db):
    _, h, g, _ = _fresh_user(db, "r6b1_audit")
    requests.post(f"{BASE_URL}/api/territory/purchase",
                  json={"structure_slug": "market_stall"}, headers=h, timeout=15)
    row = db.audit_log.find_one({
        "actor_guild_id": g["id"],
        "event_type": "guild_structure_purchased",
    })
    assert row is not None
    assert row["metadata"]["structure_slug"] == "market_stall"
    assert row["metadata"]["to_level"] == 1


def test_dormitory_legacy_lv7_cannot_be_user_upgraded(db):
    """Even with infinite gold, an end-user cannot reach dormitories Lv7
    via the upgrade endpoint — that level is migration-only."""
    _, h, g, _ = _fresh_user(db, "r6b1_legacy")
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 10**9}})
    # ROUND 6B.3 regression — Lv5 needs iron_shard 8, Lv6 needs iron_shard 16.
    # Seed plenty so all 5 upgrades succeed with atomic material debit.
    _give_material(db, g["id"], "iron_shard", 100)
    # Walk dormitories Lv1 → Lv6 via 5 upgrades.
    for i in range(5):
        r = requests.post(f"{BASE_URL}/api/territory/upgrade",
                          json={"structure_slug": "dormitories"}, headers=h, timeout=15)
        assert r.status_code == 200, f"upgrade {i+1} failed: {r.text}"
    # Now we're at Lv6 (max for user). Attempting Lv6→Lv7 must refuse.
    r7 = requests.post(f"{BASE_URL}/api/territory/upgrade",
                       json={"structure_slug": "dormitories"}, headers=h, timeout=15)
    # The catalog max_level for users is 6, so we expect 409 already_max_level
    # (NOT 422 upgrade_not_available — that path is taken when target_level
    # exists in the cost table but is None; here the catalog max_level=6 is
    # hit first).
    assert r7.status_code == 409
    assert r7.json()["detail"]["code"] == "structure.already_max_level"
