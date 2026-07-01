"""ROUND 11.2 TASK 2 — Specialization P0 atomicity + compensating refund.

Coverage:
  1.  Happy path with full audit trail (attempt→committed, NO rolled_back).
  2.  Insufficient gold → 402 specific code, gold UNCHANGED, audit rolled_back
      with refunded=false.
  3.  Invalid spec slug → 422 invalid_spec, no DB writes, no audit attempt.
  4.  Adventurer retired → 422 specific code, gold UNCHANGED.
  5.  Already specialized → 422 requirements_not_met reason=already_specialized.
  6.  Level too low → 422 requirements_not_met reason=adventurer_level_too_low.
  7.  Class not eligible → 422 requirements_not_met reason=class_not_eligible.
  8.  Concurrent specialize race → second request gets refund, gold UNCHANGED
      AFTER subtracting one apply.
  9.  Internal error compensating: monkeypatch `inventory_items.insert_one` to
      raise → 500 internal_error, gold REFUNDED to original, adv NOT
      specialized, audit rolled_back with refunded=true, signature row cleaned.
  10. Refund script idempotency: run --apply twice → only 1 refund audit row
      per attempt.

All 10 tests share the same fresh-guild fixture for isolation.
"""
from __future__ import annotations

import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _fresh_guild(db, *, prefix: str = "r112t2"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R112T2 {tag[-6:]}"},
                  headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 50_000}})
    return h, g["id"], email


def _unlock_training(db, guild_id: str, *, level: int, headers: dict) -> None:
    requests.get(f"{BASE_URL}/api/territory", headers=headers, timeout=15)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {"structures.training_grounds": {
            "is_unlocked": True, "level": level,
        }}},
    )


def _seed_adv(db, *, guild_id: str, class_slug: str = "warrior",
              level: int = 5, retired: bool = False) -> str:
    cls = db.adventurer_classes.find_one({"slug": class_slug})
    assert cls, f"class {class_slug} not seeded"
    adv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db.adventurers.insert_one({
        "id": adv_id, "guild_id": guild_id, "name": f"R112T2_{adv_id[:8]}",
        "adventurer_class_id": cls["id"],
        "class_name": cls.get("name") or class_slug.capitalize(),
        "class_role": cls.get("role"),
        "rarity": "Common",
        "level": level, "experience": 0,
        "strength": 10, "agility": 10, "intellect": 10,
        "endurance": 10, "faith": 10,
        "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": retired,
        "traits": [], "is_starter": False, "is_test_seed": True,
        "created_at": now, "updated_at": now,
    })
    return adv_id


# ─────────────────────────────────────────────────────────────────────────
# 1. Happy path: audit attempt → committed (no rolled_back)
# ─────────────────────────────────────────────────────────────────────────
def test_t2_01_happy_path_writes_attempt_and_committed_audit(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    gold_before = db.guilds.find_one({"id": gid})["gold"]

    r = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                      json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    attempt_id = body["attempt_id"]
    assert attempt_id

    # Gold debited by 500
    gold_after = db.guilds.find_one({"id": gid})["gold"]
    assert gold_after == gold_before - 500

    # Audit trail: attempt + committed present, rolled_back ABSENT
    attempt = db.audit_log.find_one({
        "event_type": "training_specialization_attempt",
        "metadata.attempt_id": attempt_id,
    })
    committed = db.audit_log.find_one({
        "event_type": "training_specialization_committed",
        "metadata.attempt_id": attempt_id,
    })
    rolled = db.audit_log.find_one({
        "event_type": "training_specialization_rolled_back",
        "metadata.attempt_id": attempt_id,
    })
    assert attempt is not None
    assert committed is not None
    assert rolled is None
    assert attempt["metadata"]["status"] == "pending"
    assert attempt["metadata"]["cost_gold"] == 500


# ─────────────────────────────────────────────────────────────────────────
# 2. Insufficient gold: audit rolled_back with refunded=false, gold unchanged
# ─────────────────────────────────────────────────────────────────────────
def test_t2_02_insufficient_gold_rolled_back_no_refund(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    db.guilds.update_one({"id": gid}, {"$set": {"gold": 100}})  # < 500
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    gold_before = db.guilds.find_one({"id": gid})["gold"]

    r = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                      json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r.status_code == 402
    assert r.json()["detail"]["code"] == "training.specialization.insufficient_gold"

    gold_after = db.guilds.find_one({"id": gid})["gold"]
    assert gold_after == gold_before  # UNCHANGED — no debit happened

    # Audit pattern: attempt exists, rolled_back exists with refunded=False
    rolled = db.audit_log.find_one({
        "event_type": "training_specialization_rolled_back",
        "actor_guild_id": gid,
        "metadata.reason": "insufficient_gold",
    })
    assert rolled is not None
    assert rolled["metadata"]["refunded"] is False


# ─────────────────────────────────────────────────────────────────────────
# 3. Invalid spec → no DB writes
# ─────────────────────────────────────────────────────────────────────────
def test_t2_03_invalid_spec_no_writes_no_audit(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    audit_before = db.audit_log.count_documents({
        "event_type": "training_specialization_attempt",
        "actor_guild_id": gid,
    })
    gold_before = db.guilds.find_one({"id": gid})["gold"]

    r = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                      json={"spec_slug": "nonexistent_spec"},
                      headers=h, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "training.specialization.invalid_spec"

    assert db.guilds.find_one({"id": gid})["gold"] == gold_before
    audit_after = db.audit_log.count_documents({
        "event_type": "training_specialization_attempt",
        "actor_guild_id": gid,
    })
    assert audit_after == audit_before  # no attempt written


# ─────────────────────────────────────────────────────────────────────────
# 4. Adventurer retired → no debit
# ─────────────────────────────────────────────────────────────────────────
def test_t2_04_retired_adventurer_blocked_no_debit(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior",
                       level=5, retired=True)
    gold_before = db.guilds.find_one({"id": gid})["gold"]

    r = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                      json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "training.specialization.adventurer_retired"
    assert db.guilds.find_one({"id": gid})["gold"] == gold_before


# ─────────────────────────────────────────────────────────────────────────
# 5. Already specialized → requirements_not_met reason=already_specialized
# ─────────────────────────────────────────────────────────────────────────
def test_t2_05_already_specialized_requirements_not_met(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    r1 = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                       json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r1.status_code == 200
    gold_after_first = db.guilds.find_one({"id": gid})["gold"]
    r2 = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                       json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r2.status_code == 422
    detail = r2.json()["detail"]
    assert detail["code"] == "training.specialization.requirements_not_met"
    assert detail["reason"] == "already_specialized"
    # No double-debit on 2nd attempt
    assert db.guilds.find_one({"id": gid})["gold"] == gold_after_first


# ─────────────────────────────────────────────────────────────────────────
# 6. Level too low → requirements_not_met reason=adventurer_level_too_low
# ─────────────────────────────────────────────────────────────────────────
def test_t2_06_level_too_low_requirements_not_met(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=4)
    gold_before = db.guilds.find_one({"id": gid})["gold"]
    r = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                      json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["code"] == "training.specialization.requirements_not_met"
    assert detail["reason"] == "adventurer_level_too_low"
    assert detail["min_level"] == 5
    assert detail["current_level"] == 4
    assert db.guilds.find_one({"id": gid})["gold"] == gold_before


# ─────────────────────────────────────────────────────────────────────────
# 7. Class not eligible → requirements_not_met reason=class_not_eligible
# ─────────────────────────────────────────────────────────────────────────
def test_t2_07_class_not_eligible_requirements_not_met(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="mage", level=5)
    r = requests.post(f"{BASE_URL}/api/training/specialize/{adv_id}",
                      json={"spec_slug": "spec_difensore"}, headers=h, timeout=15)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["code"] == "training.specialization.requirements_not_met"
    assert detail["reason"] == "class_not_eligible"


# ─────────────────────────────────────────────────────────────────────────
# 8. Concurrent race: 2 parallel specialize on the same adv.
#    Only one succeeds, the loser gets compensated (gold refunded).
# ─────────────────────────────────────────────────────────────────────────
def test_t2_08_concurrent_race_loser_is_refunded(db):
    import concurrent.futures as cf
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    gold_before = db.guilds.find_one({"id": gid})["gold"]

    def call():
        return requests.post(
            f"{BASE_URL}/api/training/specialize/{adv_id}",
            json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
        )

    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        f1, f2 = ex.submit(call), ex.submit(call)
        r1, r2 = f1.result(), f2.result()
    statuses = sorted([r1.status_code, r2.status_code])
    # One winner (200), one loser. Loser could be 422 already_specialized
    # OR 500 internal_error (race detected post-debit → refunded).
    assert statuses[0] == 200
    assert statuses[1] in (422, 500)

    # Final gold: exactly 1 successful debit of 500g (race-loser refunded).
    gold_after = db.guilds.find_one({"id": gid})["gold"]
    assert gold_after == gold_before - 500


# ─────────────────────────────────────────────────────────────────────────
# 9. Internal error compensating: force inventory_items.insert_one to raise
# ─────────────────────────────────────────────────────────────────────────
def test_t2_09_internal_error_compensates_refund_and_audit(db):
    """Directly invoke the service with a monkey-patched insert_one to
    deterministically trigger the compensating path. Sync test that
    drives an asyncio.run loop internally — no pytest-asyncio needed."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.training.services import apply_specialization
    from fastapi import HTTPException

    h, gid, _email = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    gold_before = db.guilds.find_one({"id": gid})["gold"]

    async def _run():
        acli = AsyncIOMotorClient(MONGO_URL)
        adb = acli[DB_NAME]

        # Wrap db: replace ONLY inventory_items collection access with a
        # mock whose insert_one raises. We use object.__setattr__ on a
        # dict-style override because motor caches collection proxies.
        class _MockCol:
            def __init__(self, real):
                self._real = real
            async def insert_one(self, *a, **kw):
                raise RuntimeError("simulated_inventory_insert_failure")
            async def delete_one(self, *a, **kw):
                # Compensate path tries to clean orphan — let it succeed no-op
                return await self._real.delete_one(*a, **kw)
            def __getattr__(self, name):
                return getattr(self._real, name)

        class _DBWrap:
            def __init__(self, real):
                self._real = real
                self._mock_inv = _MockCol(real.inventory_items)
            @property
            def inventory_items(self):
                return self._mock_inv
            def __getattr__(self, name):
                return getattr(self._real, name)

        wrapped = _DBWrap(adb)
        try:
            try:
                await apply_specialization(
                    wrapped, guild_id=gid, actor_user_id="test-actor",
                    adventurer_id=adv_id, spec_slug="spec_difensore",
                )
                return None  # unexpected success
            except HTTPException as e:
                return e
        finally:
            acli.close()

    exc = asyncio.run(_run())
    assert exc is not None, "expected HTTPException, got success"
    assert exc.status_code == 500
    assert exc.detail["code"] == "training.specialization.internal_error"

    # Gold must be refunded to original
    assert db.guilds.find_one({"id": gid})["gold"] == gold_before
    # Adventurer must NOT be specialized
    adv = db.adventurers.find_one({"id": adv_id})
    assert adv.get("specialization") in (None, {}), \
        f"adv should NOT be specialized after rollback, got {adv.get('specialization')}"
    # Audit: rolled_back with refunded=True + reason=internal_error
    rolled = db.audit_log.find_one({
        "event_type": "training_specialization_rolled_back",
        "actor_guild_id": gid,
        "metadata.reason": "internal_error",
        "metadata.refunded": True,
    })
    assert rolled is not None
    assert rolled["metadata"]["error_class"] == "RuntimeError"


# ─────────────────────────────────────────────────────────────────────────
# 10. Refund script idempotency: run --apply twice, only 1 refund audit row.
# ─────────────────────────────────────────────────────────────────────────
def test_t2_10_refund_script_is_idempotent(db):
    """Manually seed an orphan-pointer scenario (Mode A), then run the
    CLI refund script twice; only one refund audit event must result."""
    h, gid, _ = _fresh_guild(db)
    _unlock_training(db, gid, level=1, headers=h)
    adv_id = _seed_adv(db, guild_id=gid, class_slug="warrior", level=5)
    # Forge a spec pointing to a non-existent signature_item_id
    orphan_sig_id = str(uuid.uuid4())
    db.adventurers.update_one(
        {"id": adv_id},
        {"$set": {"specialization": {
            "slug": "spec_difensore",
            "name_it": "Difensore",
            "name_en": "Defender",
            "tier": "starter",
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "applied_at_level": 5,
            "signature_item_id": orphan_sig_id,
            "modifiers": {"endurance": 2, "strength": 1},
            "training_grounds_level_at_apply": 1,
        }}},
    )
    # Drain gold to a known baseline so we can verify the refund delta
    db.guilds.update_one({"id": gid}, {"$set": {"gold": 1000}})
    gold_baseline = db.guilds.find_one({"id": gid})["gold"]

    # Run script twice via subprocess (Mode A — orphan_signature_pointer)
    import subprocess
    for run_idx in range(2):
        proc = subprocess.run(
            ["python", "-m", "app.scripts.refund_failed_specializations",
             "--apply", "--guild-id", gid],
            cwd="/app/backend", capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0, f"run {run_idx} stderr: {proc.stderr}"

    # Verify exactly 1 refund audit event for this adv
    refund_count = db.audit_log.count_documents({
        "event_type": "training_specialization_refund",
        "actor_guild_id": gid,
        "metadata.adventurer_id": adv_id,
    })
    assert refund_count == 1, f"expected 1 refund audit row, got {refund_count}"

    # Verify gold was refunded ONCE (orphan was at TG=1 → cost=500)
    gold_after = db.guilds.find_one({"id": gid})["gold"]
    assert gold_after == gold_baseline + 500, \
        f"expected gold {gold_baseline + 500}, got {gold_after}"

    # Verify the adv's broken specialization pointer was cleared
    adv = db.adventurers.find_one({"id": adv_id})
    assert adv.get("specialization") is None
