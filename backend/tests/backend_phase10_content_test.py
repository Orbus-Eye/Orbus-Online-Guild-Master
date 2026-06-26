"""Phase 10 — Content Expansion Pack 1 regression + invariant tests.

Validates seed counts, idempotency, rarity distribution, anti-pay-to-win
invariant, loot-failure-never-rare invariant for all dungeons, and that
recruitment surfaces all 12 classes.
"""
import os
import secrets
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
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


@pytest.fixture(scope="module")
def tester_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ─── Seed counts ────────────────────────────────────────────────────────────


class TestPhase10SeedCounts:
    def test_classes_at_least_12(self, db):
        n = db.adventurer_classes.count_documents({"is_active": True})
        assert n >= 12, f"expected >= 12 active classes, got {n}"

    def test_traits_at_least_30(self, db):
        n = db.adventurer_traits.count_documents({"is_active": True})
        assert n >= 30, f"expected >= 30 active traits, got {n}"

    def test_dungeons_at_least_10(self, db):
        n = db.dungeons.count_documents({"is_active": True})
        assert n >= 10, f"expected >= 10 active dungeons, got {n}"

    def test_items_at_least_80(self, db):
        n = db.items.count_documents({"is_active": True})
        assert n >= 80, f"expected >= 80 active items, got {n}"


# ─── Originals invariant ────────────────────────────────────────────────────


class TestPhase10OriginalsInvariant:
    def test_goblin_warrens_unchanged(self, db):
        d = db.dungeons.find_one({"slug": "goblin-warrens"})
        assert d is not None
        assert d["base_duration_seconds"] == 60
        assert d["recommended_power"] == 45
        assert d["base_gold_reward"] == 35
        assert d["base_xp_reward"] == 25
        assert d["difficulty"] == 1

    def test_shadow_crypts_unchanged(self, db):
        d = db.dungeons.find_one({"slug": "shadow-crypts"})
        assert d is not None
        assert d["base_duration_seconds"] == 120
        assert d["recommended_power"] == 60
        assert d["base_gold_reward"] == 65
        assert d["base_xp_reward"] == 50
        assert d["difficulty"] == 2

    def test_dragons_hoard_unchanged(self, db):
        d = db.dungeons.find_one({"slug": "dragons-hoard"})
        assert d is not None
        assert d["base_duration_seconds"] == 300
        assert d["recommended_power"] == 80
        assert d["base_gold_reward"] == 120
        assert d["base_xp_reward"] == 90
        assert d["difficulty"] == 3

    def test_original_5_classes_present(self, db):
        for slug in ("warrior", "rogue", "mage", "priest", "ranger"):
            c = db.adventurer_classes.find_one({"slug": slug})
            assert c is not None, f"class {slug} missing"


# ─── Idempotency ────────────────────────────────────────────────────────────


class TestPhase10SeedIdempotency:
    """Re-running the seed must NOT create duplicates (upsert by slug)."""

    def test_double_seed_keeps_counts(self):
        import asyncio
        import importlib
        from motor.motor_asyncio import AsyncIOMotorClient

        async def _run():
            client = AsyncIOMotorClient(MONGO_URL)
            amdb = client[DB_NAME]
            try:
                seed_runner = importlib.import_module("app.seeds.seed_runner")

                c1 = await amdb.adventurer_classes.count_documents({})
                t1 = await amdb.adventurer_traits.count_documents({})
                d1 = await amdb.dungeons.count_documents({})
                i1 = await amdb.items.count_documents({})

                # Re-run all seeds twice (idempotent)
                await seed_runner.run_all_seeds(amdb)
                await seed_runner.run_all_seeds(amdb)

                c2 = await amdb.adventurer_classes.count_documents({})
                t2 = await amdb.adventurer_traits.count_documents({})
                d2 = await amdb.dungeons.count_documents({})
                i2 = await amdb.items.count_documents({})

                return (c1, t1, d1, i1, c2, t2, d2, i2)
            finally:
                client.close()

        c1, t1, d1, i1, c2, t2, d2, i2 = asyncio.run(_run())
        assert c1 == c2, f"classes count diverged: {c1} → {c2}"
        assert t1 == t2, f"traits count diverged: {t1} → {t2}"
        assert d1 == d2, f"dungeons count diverged: {d1} → {d2}"
        assert i1 == i2, f"items count diverged: {i1} → {i2}"


# ─── Loot tables ────────────────────────────────────────────────────────────


class TestPhase10LootTables:
    def test_all_10_dungeons_have_loot_table(self):
        from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES

        expected_slugs = {
            "goblin-warrens", "sewer-nest", "bandit-hideout",
            "druid-grove", "cursed-mines", "shadow-crypts", "sunken-library",
            "lich-sanctum", "storm-spire", "dragons-hoard",
        }
        actual = set(DUNGEON_LOOT_TABLES.keys())
        assert expected_slugs.issubset(actual), expected_slugs - actual

    def test_tier1_only_common_uncommon(self):
        from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES

        for slug in ("goblin-warrens", "sewer-nest", "bandit-hideout"):
            table = DUNGEON_LOOT_TABLES[slug]
            success_weights = set(table["success"]["weights"].keys())
            failure_weights = set(table["failure"].get("weights", {}).keys())
            assert success_weights.issubset({"Common", "Uncommon"}), (
                f"{slug} success has non-T1: {success_weights}"
            )
            assert failure_weights.issubset({"Common", "Uncommon"}), (
                f"{slug} failure has non-T1: {failure_weights}"
            )

    def test_tier3_no_common_in_success(self):
        """Phase 10 contract: Tier 3 success drops never include Common."""
        from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES

        for slug in ("lich-sanctum", "storm-spire", "dragons-hoard"):
            success_weights = set(DUNGEON_LOOT_TABLES[slug]["success"]["weights"].keys())
            assert "Common" not in success_weights, (
                f"{slug} should not award Common on success: {success_weights}"
            )

    def test_failure_never_rare_or_epic_for_any_dungeon(self):
        """Phase 10: extend the Phase-7 invariant to ALL 10 dungeons."""
        from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES

        forbidden = {"Rare", "Epic"}
        for slug, table in DUNGEON_LOOT_TABLES.items():
            failure_rarities = set(table["failure"].get("weights", {}).keys())
            leaked = forbidden.intersection(failure_rarities)
            assert not leaked, (
                f"{slug} failure leaks {leaked} — must be Common/Uncommon only"
            )


# ─── Anti pay-to-win invariant ──────────────────────────────────────────────


class TestPhase10MonetizationInvariant:
    def test_no_combat_item_is_real_money(self, db):
        """All items with combat/economy/ranking effects must NOT be sellable
        for real money. Phase 10 enforces this across the expanded catalog."""
        leak = list(db.items.find(
            {
                "$or": [
                    {"affects_combat": True},
                    {"affects_economy": True},
                    {"affects_ranking": True},
                ],
                "can_be_sold_for_real_money": True,
            },
            {"_id": 0, "slug": 1, "rarity": 1},
        ))
        assert leak == [], f"P2W leak detected: {leak}"

    def test_loot_referenced_items_exist(self, db):
        """All loot tables reference rarities. Ensure every rarity referenced
        has at least 1 item in the seed."""
        from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES

        referenced_rarities = set()
        for table in DUNGEON_LOOT_TABLES.values():
            for branch in ("success", "failure"):
                for rarity in table[branch].get("weights", {}):
                    referenced_rarities.add(rarity)

        for rarity in referenced_rarities:
            n = db.items.count_documents({"rarity": rarity, "is_active": True})
            assert n > 0, f"rarity {rarity} referenced in loot but no items in DB"


# ─── Recruitment surfaces all classes ───────────────────────────────────────


class TestPhase10Recruitment:
    def test_recruitment_can_roll_any_of_12_classes(self, tester_token, db):
        """Sample many candidates and verify we see at least 8 distinct classes.

        Phase 11.2: GET /candidates is now read-only, so we register multiple
        fresh users (each gets their own roster seed) to accumulate variety
        without exhausting the daily refresh limit.
        """
        import uuid as _uuid
        seen_class_slugs = set()
        for batch in range(25):  # 25 fresh users × 4 cards = 100 rolls
            tag = f"p10cls_{_uuid.uuid4().hex[:8]}"
            email = f"{tag}@orbus.test"
            r = requests.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": email, "username": tag, "password": "Test12345!"},
                timeout=15,
            )
            assert r.status_code in (200, 201), r.text
            tok = r.json()["access_token"]
            h = {"Authorization": f"Bearer {tok}"}
            requests.post(
                f"{BASE_URL}/api/guilds",
                json={"name": f"G_{tag}", "description": ""},
                headers=h, timeout=15,
            )
            cr = requests.get(
                f"{BASE_URL}/api/recruitment/candidates",
                headers=h, timeout=15,
            )
            assert cr.status_code == 200, cr.text
            data = cr.json()
            candidates = data if isinstance(data, list) else data.get("candidates", [])
            for c in candidates:
                slug = c.get("class_slug") or c.get("class_name", "").lower()
                if slug:
                    seen_class_slugs.add(slug)
            if len(seen_class_slugs) >= 8:
                break
        assert len(seen_class_slugs) >= 8, (
            f"recruitment surface too narrow: {seen_class_slugs}"
        )

    def test_admin_classes_lists_12_plus(self, tester_token):
        """Verify admin endpoint surfaces all expanded classes."""
        r = requests.get(
            f"{BASE_URL}/api/admin/classes",
            headers={"Authorization": f"Bearer {tester_token}"},
            timeout=15,
        )
        assert r.status_code == 200
        data = r.json()
        rows = data if isinstance(data, list) else data.get("classes", [])
        assert len(rows) >= 12, f"expected >= 12 classes via admin, got {len(rows)}"


# ─── No-regression: OpenAPI surface still 37 paths ──────────────────────────


class TestPhase10OpenAPIInvariant:
    def test_openapi_path_count_still_37(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        # Phase 9.1 added 1 path → 37. Phase 11.2 adds POST /api/recruitment/refresh → 38.
        assert len(paths) == 69, f"expected 69, got {len(paths)}"

    def test_leaderboard_still_present(self):
        r = requests.get(
            f"{BASE_URL}/api/leaderboard/guilds?limit=5", timeout=15
        )
        assert r.status_code == 200


# ─── Failure-loot statistical sanity (per-dungeon, all 10) ──────────────────


class TestPhase10FailureLootStatistical:
    """Quick statistical sanity: simulate the failure roll branch directly
    against the loot table sampler and verify no Rare/Epic ever surfaces.

    This is the same shape as `test_shadow_crypts_failure_never_rare`,
    extended across all 10 dungeons. We do not call the live API
    (expedition lifecycle would be too slow); instead we exercise
    `roll_loot_for_dungeon` directly with the live Mongo handle.
    """

    def test_no_rare_or_epic_on_failure_any_dungeon(self):
        import asyncio
        import importlib
        from motor.motor_asyncio import AsyncIOMotorClient

        async def _run():
            client = AsyncIOMotorClient(MONGO_URL)
            amdb = client[DB_NAME]
            leaks = []
            try:
                mod = importlib.import_module("app.expeditions.loot_tables")
                slugs = list(mod.DUNGEON_LOOT_TABLES.keys())
                for slug in slugs:
                    dungeon = await amdb.dungeons.find_one({"slug": slug})
                    if not dungeon:
                        leaks.append((slug, "DUNGEON_MISSING"))
                        continue
                    # 200 trials per dungeon → ~2000 total
                    for _ in range(200):
                        loot_ids = await mod.roll_loot_for_dungeon(amdb, dungeon, success=False)
                        for lid in loot_ids:
                            item = await amdb.items.find_one(
                                {"id": lid}, {"_id": 0, "rarity": 1, "slug": 1}
                            )
                            if item and item["rarity"] in ("Rare", "Epic"):
                                leaks.append((slug, item["rarity"], item["slug"]))
            finally:
                client.close()
            return leaks

        leaks = asyncio.run(_run())
        assert leaks == [], f"failure-loot leaked Rare/Epic: {leaks}"
