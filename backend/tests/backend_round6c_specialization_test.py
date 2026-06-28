"""ROUND 6C — Specialization apply + retire flow integration tests.

Covers the new endpoints in `app.training.routes` and the Round 6C
extensions of `app.adventurers.retire`:

  * GET /api/training/catalog gating (locked → empty list, unlocked → tier filter)
  * POST /api/training/specialize/{adv_id}:
      - happy path (adv.specialization persisted, signature item created bound,
        guild gold decremented, audit events)
      - 422 adventurer level < 5
      - 422 adventurer already specialized
      - 422 wrong class
      - 402 insufficient gold
  * Retire of a specialized adventurer:
      - 422 `adventurer.has_bound_items` without `discard_signature_items`
      - 200 with `discard_signature_items=true` (signature item soft-discarded,
        adventurer.is_retired=True)
"""
from __future__ import annotations

import os
import uuid

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


def _fresh_guild(db, *, prefix: str = "r6c"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(
        f"{BASE_URL}/api/guilds", json={"name": f"6C {tag[-6:]}"},
        headers=h, timeout=15,
    )
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 50_000}})
    return h, g["id"], email


def _unlock_training(db, guild_id: str, level: int = 1, headers: dict | None = None) -> None:
    """Force the `training_grounds` structure to `level` (unlocked).

    Bypasses the buy/upgrade gold debit — tests are about training, not
    structure economics. We first ping `/api/territory` so the lazy-init
    creates the `guild_structures` doc with a proper `id`; then patch
    only the `training_grounds` sub-field (NO upsert — the doc already
    exists).
    """
    if headers is not None:
        requests.get(f"{BASE_URL}/api/territory", headers=headers, timeout=15)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "structures.training_grounds": {
                "is_unlocked": True,
                "level": level,
            },
        }},
    )


def _seed_adv(db, *, guild_id: str, class_slug: str = "warrior",
              level: int = 5, name: str | None = None) -> str:
    """Insert a level-`level` adventurer in `guild_id`, return adv_id."""
    cls = db.adventurer_classes.find_one(
        {"slug": class_slug}, {"_id": 0, "id": 1, "slug": 1, "role": 1},
    )
    assert cls, f"class {class_slug} not seeded"
    adv_id = str(uuid.uuid4())
    now = "2026-06-28T07:00:00+00:00"
    db.adventurers.insert_one({
        "id": adv_id, "guild_id": guild_id,
        "name": name or f"R6C_{adv_id[:8]}",
        "adventurer_class_id": cls["id"],
        "class_name": cls.get("slug"),
        "class_slug": cls.get("slug"),
        "class_role": cls.get("role"),
        "rarity": "Common",
        "level": level, "experience": 0,
        "strength": 10, "agility": 10, "intellect": 10,
        "endurance": 10, "faith": 10,
        "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": False,
        "traits": [], "is_starter": False, "is_test_seed": True,
        "created_at": now, "updated_at": now,
    })
    return adv_id


# ─── Catalog gate ────────────────────────────────────────────────────────


def test_catalog_locked_when_training_grounds_not_unlocked(db):
    h, _gid, _ = _fresh_guild(db)
    r = requests.get(f"{BASE_URL}/api/training/catalog", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["training_grounds_level"] == 0
    assert data["tier"] is None
    assert data["specs"] == []


def test_catalog_starter_tier_at_lv1(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    r = requests.get(f"{BASE_URL}/api/training/catalog", headers=h, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "starter"
    assert data["apply_cost_gold"] == 500
    tiers = {s["tier"] for s in data["specs"]}
    assert tiers == {"starter"}


def test_catalog_full_tier_at_lv3(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=3, headers=h)
    r = requests.get(f"{BASE_URL}/api/training/catalog", headers=h, timeout=15)
    data = r.json()
    assert data["tier"] == "full"
    assert data["apply_cost_gold"] == 1500
    tiers = {s["tier"] for s in data["specs"]}
    assert tiers == {"starter", "full"}


# ─── Apply specialization ───────────────────────────────────────────────


def test_apply_spec_happy_path(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    g_before = db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})["gold"]

    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"},
        headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["specialization"]["slug"] == "spec_difensore"
    assert body["specialization"]["applied_at_level"] == 5
    assert body["gold_spent"] == 500
    sig_id = body["signature_item"]["id"]

    # adv.specialization persisted
    adv = db.adventurers.find_one({"id": adv_id}, {"_id": 0})
    assert adv["specialization"]["slug"] == "spec_difensore"
    assert adv["specialization"]["signature_item_id"] == sig_id

    # signature item created and bound
    inv = db.inventory_items.find_one({"id": sig_id}, {"_id": 0})
    assert inv is not None
    assert inv["bound_to_adventurer_id"] == adv_id
    assert inv["bound_reason"] == "specialization_signature"
    assert inv["signature"]["spec_slug"] == "spec_difensore"

    # gold debited
    g_after = db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})["gold"]
    assert g_after == g_before - 500


def test_apply_spec_blocks_level_too_low(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=4)
    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "training.adventurer_level_too_low"


def test_apply_spec_blocks_wrong_class(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    # mage cannot take "spec_difensore" (warrior/paladin only)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="mage", level=5)
    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "training.class_not_eligible"


def test_apply_spec_blocks_already_specialized(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    # 1st apply OK
    r1 = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r1.status_code == 200
    # 2nd apply blocked
    r2 = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r2.status_code == 422
    assert r2.json()["detail"]["code"] == "training.adventurer_already_specialized"


def test_apply_spec_blocks_locked(db):
    h, gid, _ = _fresh_guild(db)
    # NB: training grounds NOT unlocked
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "training.locked"


def test_apply_spec_blocks_full_tier_at_starter_unlock(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)  # starter only
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_furia"},  # full tier
        headers=h, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "training.spec_tier_locked"


def test_apply_spec_blocks_insufficient_gold(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    db.guilds.update_one({"id": gid}, {"$set": {"gold": 100}})  # < 500 cost
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r.status_code == 402
    assert r.json()["detail"]["code"] == "training.insufficient_gold"


# ─── Retire ↔ signature item interaction ────────────────────────────────


def test_retire_specialized_blocks_without_discard_flag(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    # Apply spec → signature item bound
    rs = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert rs.status_code == 200

    r = requests.post(
        f"{BASE_URL}/api/adventurers/{adv_id}/retire",
        json={"reason": "test", "force_unequip": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "adventurer.has_bound_items"


def test_retire_specialized_succeeds_with_discard_flag(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    rs = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert rs.status_code == 200
    sig_id = rs.json()["signature_item"]["id"]

    r = requests.post(
        f"{BASE_URL}/api/adventurers/{adv_id}/retire",
        json={
            "reason": "spec retire test",
            "force_unequip": True,
            "discard_signature_items": True,
        },
        headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text

    adv = db.adventurers.find_one({"id": adv_id}, {"_id": 0})
    assert adv["is_retired"] is True

    inv = db.inventory_items.find_one({"id": sig_id}, {"_id": 0})
    assert inv is not None  # NO hard delete
    assert inv.get("discarded_at") is not None
    assert inv.get("discard_reason") == "adventurer_retired"
    assert inv.get("bound_to_adventurer_id") is None
