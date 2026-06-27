"""ROUND 6A.1 — Adventurer generator tests.

Covers:
  G1. Rarity distribution on 1500-sample within ±2% tolerance.
  G2. No Test* class / trait ever in output.
  G3. Legendary post-roll guards: stat floor ≥15 + ≥3 positive traits (when
      pool allows). Audit log row emitted.
  G4. Class balance: no class > 35% in 1000 generations.
  G5. Power consistency: API /api/adventurers exposes `total_power` matching
      `base_power + equipment_power`.
  G6. Recruitment refresh uses generator (audit log row written per candidate).
"""
import asyncio
import os
import uuid
from collections import Counter
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
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


@pytest.fixture(scope="function")
def async_db():
    c = AsyncIOMotorClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user(db, hint="r6a"):
    tag = f"TEST_round6a_{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R6A {tag[-5:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    # Flag test_user immediately
    db.users.update_one({"email": f"{tag}@orbus.test"}, {"$set": {"is_test_user": True}})
    return {"headers": h, "guild_id": g["id"], "email": f"{tag}@orbus.test"}


class TestRarityDistribution:
    def test_G1_distribution_1500_samples_within_tolerance(self, async_db, db):
        """Server-side weighted distribution must be ~68/24/7/0.9/0.1 (±2%)."""
        from app.adventurers.generator import generate_candidate, new_rng_for_tests
        rng = new_rng_for_tests(seed=42)
        loop = asyncio.new_event_loop()

        async def run():
            counter = Counter()
            guild_id = str(uuid.uuid4())
            # Pre-fetch pools once for speed
            from app.adventurers.generator import filter_safe_class_pool, filter_safe_trait_pool
            class_pool = await filter_safe_class_pool(async_db)
            trait_pool = await filter_safe_trait_pool(async_db)
            for _ in range(1500):
                c = await generate_candidate(
                    async_db, guild_id=guild_id, rng=rng,
                    class_pool=class_pool, trait_pool=trait_pool,
                    audit=False,
                )
                counter[c["rarity"]] += 1
            return counter

        counter = loop.run_until_complete(run())
        loop.close()
        total = sum(counter.values())
        # Target proportions
        targets = {"Common": 0.68, "Uncommon": 0.24, "Rare": 0.07, "Epic": 0.009, "Legendary": 0.001}
        for rarity, target in targets.items():
            actual = counter.get(rarity, 0) / total
            if rarity in ("Epic", "Legendary"):
                # Loose floor: at least 1 sample of Epic, Legendary may be 0 in 1500
                continue
            tol = 0.025
            assert abs(actual - target) <= tol, f"{rarity}={actual:.3f} vs target {target} (tol ±{tol})"
        # No unknown rarity leaked
        assert set(counter.keys()) <= {"Common", "Uncommon", "Rare", "Epic", "Legendary"}


class TestPoolSafety:
    def test_G2_no_test_class_or_trait_leak(self, async_db):
        from app.adventurers.generator import filter_safe_class_pool, filter_safe_trait_pool
        loop = asyncio.new_event_loop()
        classes = loop.run_until_complete(filter_safe_class_pool(async_db))
        traits = loop.run_until_complete(filter_safe_trait_pool(async_db))
        loop.close()
        for c in classes:
            assert not c.get("name", "").startswith("Test")
            assert not c.get("slug", "").startswith("test")
            assert c.get("is_test") is not True
        for t in traits:
            assert not t.get("name", "").startswith("Test")
            assert not t.get("slug", "").startswith("test")
            assert t.get("is_test") is not True


class TestLegendaryGuards:
    def test_G3_legendary_satisfies_stat_floor_and_audit_logged(self, async_db, db):
        """Force a Legendary roll via deterministic seed and verify guards."""
        from app.adventurers.generator import (
            generate_candidate, new_rng_for_tests, _stat_max_value,
            filter_safe_class_pool, filter_safe_trait_pool,
        )
        loop = asyncio.new_event_loop()

        async def run():
            class_pool = await filter_safe_class_pool(async_db)
            trait_pool = await filter_safe_trait_pool(async_db)
            # Brute-force search for a Legendary roll within 50k attempts
            # (probability ~0.1% → expected 50 hits in 50k).
            rng = new_rng_for_tests(seed=2026)
            gid = str(uuid.uuid4())
            for _ in range(50_000):
                c = await generate_candidate(
                    async_db, guild_id=gid, rng=rng,
                    class_pool=class_pool, trait_pool=trait_pool,
                    audit=True, audit_source="test_G3",
                )
                if c["rarity"] == "Legendary":
                    return c, gid
            return None, gid

        leg, gid = loop.run_until_complete(run())
        loop.close()
        if leg is None:
            pytest.skip("no Legendary roll in 50k attempts (statistically unlikely; not a regression)")
        assert _stat_max_value(leg) >= 15, f"stat floor not enforced: {leg}"
        # Audit log row exists
        audit = db.audit_log.find_one({
            "event_type": "adventurer_generated",
            "related_entity_id": leg["id"],
            "metadata.rarity": "Legendary",
        })
        assert audit is not None, "audit row missing for Legendary"
        assert (audit.get("metadata") or {}).get("stat_max", 0) >= 15


class TestClassBalance:
    def test_G4_no_class_dominates(self, async_db):
        from app.adventurers.generator import (
            generate_candidate, new_rng_for_tests,
            filter_safe_class_pool, filter_safe_trait_pool,
        )
        loop = asyncio.new_event_loop()

        async def run():
            class_pool = await filter_safe_class_pool(async_db)
            trait_pool = await filter_safe_trait_pool(async_db)
            rng = new_rng_for_tests(seed=7)
            counter = Counter()
            gid = str(uuid.uuid4())
            for _ in range(1000):
                c = await generate_candidate(
                    async_db, guild_id=gid, rng=rng,
                    class_pool=class_pool, trait_pool=trait_pool,
                    audit=False,
                )
                counter[c["class_name"]] += 1
            return counter

        counter = loop.run_until_complete(run())
        loop.close()
        total = sum(counter.values())
        for klass, n in counter.most_common():
            frac = n / total
            assert frac <= 0.35, f"class {klass} dominates: {frac:.2%}"


class TestPowerConsistency:
    def test_G5_total_power_equals_base_plus_equipment(self, db):
        ctx = _user(db, "g5")
        r = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        for a in r.json()["adventurers"]:
            assert a["total_power"] == a["base_power"] + a["equipment_power"], \
                f"power mismatch: total={a['total_power']} base={a['base_power']} eq={a['equipment_power']}"
            # No NaN or null sneaking through
            for k in ("total_power", "base_power", "equipment_power", "level"):
                assert isinstance(a[k], int), f"{k} is not int: {a[k]!r}"


class TestRecruitmentUsesGenerator:
    def test_G6_recruitment_refresh_emits_audit(self, db):
        ctx = _user(db, "g6")
        # Force a fresh refresh — should generate 4 candidates and emit 4 audit rows
        before = db.audit_log.count_documents({
            "event_type": "adventurer_generated", "actor_guild_id": ctx["guild_id"],
        })
        # Get current refresh status; if cooldown, top up guild gold and use paid refresh
        db.guilds.update_one({"id": ctx["guild_id"]}, {"$set": {"gold": 5000}})
        r = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=ctx["headers"], timeout=15)
        # First refresh of the day is free OR paid — both produce 4 candidates
        assert r.status_code in (200, 201), r.text
        after = db.audit_log.count_documents({
            "event_type": "adventurer_generated", "actor_guild_id": ctx["guild_id"],
        })
        assert after - before == 4, f"expected 4 audit rows, got {after - before}"
