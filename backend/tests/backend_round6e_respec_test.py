"""ROUND 6E — Respec endpoint integration tests.

Covers `POST /api/training/respec/{adventurer_id}` (new in 6E):

  1. cost_scaling_first_respec        — count 0 → 800g + 1 dust
  2. cost_scaling_second_respec       — count 1 → 1200g + 2 dust
  3. cost_scaling_third_plus_respec   — count 2+ → 2000g + 3 dust (cap)
  4. cooldown_enforced                — 24h block + structured detail
  5. signature_must_discard_blocks    — checkbox-required guard
  6. retired_blocked + class_not_eligible + audit_log_written

Uses the same DB-direct helpers as the 6C test to bypass gold debits
that aren't the focus of the respec flow.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

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


def _fresh_guild(db, *, prefix: str = "r6e", gold: int = 50_000):
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
        f"{BASE_URL}/api/guilds", json={"name": f"6E {tag[-6:]}"},
        headers=h, timeout=15,
    )
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": gold}})
    return h, g["id"], email


def _unlock_training(db, guild_id: str, *, level: int = 3, headers=None) -> None:
    if headers is not None:
        requests.get(f"{BASE_URL}/api/territory", headers=headers, timeout=15)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {"structures.training_grounds": {
            "is_unlocked": True, "level": level,
        }}},
    )


def _give_materials(db, guild_id: str, slug: str, qty: int) -> None:
    """Seed enough inventory of `slug` for the respec material debit."""
    tpl = db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
    assert tpl, f"item template {slug} not seeded"
    db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": tpl["id"]},
        {"$set": {
            "id": str(uuid.uuid4()),
            "guild_id": guild_id, "item_id": tpl["id"],
            "quantity": qty, "is_bound": False,
            "refinement_level": 0, "enchants": [], "affixes": [],
            "reroll_count": 0, "disenchanted_at": None,
            "bound_to_adventurer_id": None,
        }},
        upsert=True,
    )


def _seed_specialized_adv(
    db, *, guild_id: str, spec_slug: str = "spec_difensore",
    class_slug: str = "warrior", respec_count: int = 0,
    last_respec_at: str | None = None,
) -> str:
    """Create an already-specialized adventurer ready for respec.

    Includes the embedded specialization snapshot the respec service
    reads to compute the cooldown and pre-existing-signature check.
    """
    cls = db.adventurer_classes.find_one(
        {"slug": class_slug}, {"_id": 0, "id": 1, "name": 1, "role": 1, "slug": 1},
    )
    adv_id = str(uuid.uuid4())
    sig_id = str(uuid.uuid4())
    now = "2026-06-28T08:00:00+00:00"
    db.adventurers.insert_one({
        "id": adv_id, "guild_id": guild_id,
        "name": f"R6E_{adv_id[:6]}",
        "adventurer_class_id": cls["id"],
        "class_name": cls.get("name"), "class_role": cls.get("role"),
        "class_slug": class_slug,
        "rarity": "Common", "level": 8, "experience": 0,
        "strength": 12, "agility": 10, "intellect": 8,
        "endurance": 12, "faith": 10,
        "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": False,
        "traits": [], "is_starter": False, "is_test_seed": True,
        "specialization": {
            "slug": spec_slug, "name_it": "Difensore", "name_en": "Defender",
            "tier": "starter",
            "applied_at": now, "applied_at_level": 8,
            "signature_item_id": sig_id,
            "modifiers": {"endurance": 2, "strength": 1},
            "applied_by_user_id": "seed",
            "training_grounds_level_at_apply": 3,
        },
        "specialization_respec_count": respec_count,
        "last_respec_at": last_respec_at,
        "created_at": now, "updated_at": now,
    })
    # Seed the signature inventory row so the discard path actually flips
    # `discarded_at` (and the must-discard guard finds it).
    db.inventory_items.insert_one({
        "id": sig_id, "instance_id": sig_id, "guild_id": guild_id,
        "item_id": "spec_signature_aegis_of_the_defender",
        "acquired_at": now, "quantity": 1, "is_bound": True,
        "refinement_level": 0, "enchants": [], "affixes": [],
        "reroll_count": 0, "disenchanted_at": None, "discarded_at": None,
        "bound_to_adventurer_id": adv_id,
        "bound_reason": "specialization_signature", "bound_at": now,
        "signature": {"spec_slug": spec_slug},
    })
    return adv_id, sig_id


# ─── 1-3. Cost scaling ───────────────────────────────────────────────────


def test_respec_cost_scaling_first_respec(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    _give_materials(db, gid, "lesser_arcane_dust", 5)
    adv_id, sig_id = _seed_specialized_adv(db, guild_id=gid, respec_count=0)

    g_before = db.guilds.find_one({"id": gid})["gold"]
    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cost_paid"] == {"gold": 800,
                                 "materials": {"lesser_arcane_dust": 1}}
    assert body["respec_count_after"] == 1
    assert body["signature_discarded"] is True
    assert body["previous_signature_item_id"] == sig_id
    g_after = db.guilds.find_one({"id": gid})["gold"]
    assert g_after == g_before - 800
    # Old signature soft-discarded
    old_sig = db.inventory_items.find_one({"id": sig_id})
    assert old_sig["discarded_at"] is not None
    assert old_sig["discard_reason"] == "specialization_respec"
    assert old_sig["bound_to_adventurer_id"] is None


def test_respec_cost_scaling_second_respec(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    _give_materials(db, gid, "lesser_arcane_dust", 5)
    adv_id, _ = _seed_specialized_adv(db, guild_id=gid, respec_count=1)

    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cost_paid"] == {"gold": 1200,
                                 "materials": {"lesser_arcane_dust": 2}}
    assert body["respec_count_after"] == 2


def test_respec_cost_scaling_third_plus_respec_capped(db):
    h, gid, _ = _fresh_guild(db, gold=10_000)
    _unlock_training(db, gid, level=3, headers=h)
    _give_materials(db, gid, "lesser_arcane_dust", 10)
    # Already done 5 respecs — must still cap at 2000g/3 dust
    adv_id, _ = _seed_specialized_adv(db, guild_id=gid, respec_count=5)

    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cost_paid"] == {"gold": 2000,
                                 "materials": {"lesser_arcane_dust": 3}}
    assert body["respec_count_after"] == 6


# ─── 4. Cooldown ─────────────────────────────────────────────────────────


def test_respec_cooldown_enforced(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    _give_materials(db, gid, "lesser_arcane_dust", 5)
    # Last respec 1h ago → cooldown active
    last_iso = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    adv_id, _ = _seed_specialized_adv(
        db, guild_id=gid, respec_count=1, last_respec_at=last_iso,
    )

    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "training.respec_cooldown"
    assert "next_allowed_at" in detail
    assert detail["cooldown_hours"] == 24


# ─── 5. Signature must discard ───────────────────────────────────────────


def test_respec_signature_must_discard_blocks(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    _give_materials(db, gid, "lesser_arcane_dust", 5)
    adv_id, sig_id = _seed_specialized_adv(db, guild_id=gid, respec_count=0)
    g_before = db.guilds.find_one({"id": gid})["gold"]

    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": False},  # NOT checked
        headers=h, timeout=15,
    )
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "training.respec_signature_must_discard"
    assert detail["current_signature_item_id"] == sig_id
    # No debits happened
    assert db.guilds.find_one({"id": gid})["gold"] == g_before
    assert db.inventory_items.find_one({"id": sig_id})["discarded_at"] is None


# ─── 6. Edge cases + audit log ───────────────────────────────────────────


def test_respec_retired_blocked(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    adv_id, _ = _seed_specialized_adv(db, guild_id=gid, respec_count=0)
    db.adventurers.update_one(
        {"id": adv_id}, {"$set": {"is_retired": True}},
    )
    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "training.adventurer_retired"


def test_respec_class_not_eligible(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    # Warrior cannot become spec_arcanista (eligibility: mage)
    adv_id, _ = _seed_specialized_adv(
        db, guild_id=gid, class_slug="warrior", respec_count=0,
    )
    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_arcanista",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "training.class_not_eligible"


def test_respec_audit_log_written(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    _give_materials(db, gid, "lesser_arcane_dust", 5)
    adv_id, sig_id = _seed_specialized_adv(db, guild_id=gid, respec_count=0)

    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_furia",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text

    # Three audit events should fire
    events = list(db.audit_log.find(
        {"actor_guild_id": gid,
         "event_type": {"$in": [
            "specialization_respec",
            "specialization_signature_item_discarded_on_respec",
            "specialization_signature_item_created",
         ]}},
        {"_id": 0, "event_type": 1, "metadata": 1},
    ))
    types = {e["event_type"] for e in events}
    assert "specialization_respec" in types
    assert "specialization_signature_item_discarded_on_respec" in types
    assert "specialization_signature_item_created" in types

    respec_event = next(e for e in events
                       if e["event_type"] == "specialization_respec")
    md = respec_event["metadata"]
    assert md["from_slug"] == "spec_difensore"
    assert md["to_slug"] == "spec_furia"
    assert md["respec_count_after"] == 1
    assert md["cost_gold"] == 800
    assert md["signature_discarded"] is True


def test_respec_same_slug_rejected(db):
    h, gid, _ = _fresh_guild(db, gold=5_000)
    _unlock_training(db, gid, level=3, headers=h)
    adv_id, _ = _seed_specialized_adv(
        db, guild_id=gid, spec_slug="spec_difensore", respec_count=0,
    )
    r = requests.post(
        f"{BASE_URL}/api/training/respec/{adv_id}",
        json={"new_spec_slug": "spec_difensore",
              "discard_signature_items": True},
        headers=h, timeout=15,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "training.respec_same_slug"
