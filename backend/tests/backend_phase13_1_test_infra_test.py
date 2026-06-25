"""Phase 13.1 — Test infrastructure self-tests.

These tests verify the cleanup fixture in conftest.py behaves correctly:
* safety rails block cleanup on production-looking environments
* the sweep is idempotent
* canonical seeds (real classes/traits/dungeons/items) are NOT touched
"""
import os
import uuid
from importlib import reload
from unittest import mock

import pytest
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


@pytest.fixture
def db():
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


class TestSafetyRails:
    def test_cleanup_skipped_when_production_env(self):
        """If APP_ENV=production and DB_NAME doesn't contain 'test',
        _is_test_db() must return False."""
        from tests import conftest as ctf
        with mock.patch.dict(os.environ, {
            "APP_ENV": "production",
            "MONGO_URL": "mongodb://prod.example.com:27017",
            "DB_NAME": "orbus_live",
        }, clear=False):
            # Need to re-evaluate since _is_test_db reads env at call time
            assert ctf._is_test_db() is False

    def test_cleanup_enabled_when_app_env_test(self):
        from tests import conftest as ctf
        with mock.patch.dict(os.environ, {
            "APP_ENV": "test", "DB_NAME": "orbus_live", "MONGO_URL": "mongodb://x"
        }, clear=False):
            assert ctf._is_test_db() is True

    def test_cleanup_enabled_when_db_name_contains_test(self):
        from tests import conftest as ctf
        with mock.patch.dict(os.environ, {
            "APP_ENV": "production", "DB_NAME": "orbus_test_db", "MONGO_URL": "mongodb://x"
        }, clear=False):
            assert ctf._is_test_db() is True


class TestIdempotency:
    def test_double_sweep_no_growth(self, db):
        """Running the sweep twice in a row must yield the same DB state."""
        from tests.conftest import _run_pollution_sweep
        # Inject a known pollution doc
        uid = uuid.uuid4().hex[:8]
        db.users.insert_one({
            "id": str(uuid.uuid4()), "email": f"test_smoke_{uid}@orbus.test",
            "username": "test_smoke", "password_hash": "x",
            "is_admin": False, "is_premium": False,
        })
        first = _run_pollution_sweep(db)
        second = _run_pollution_sweep(db)
        # First run deletes ≥1 user matching test_, second must delete 0 users
        assert first.get("users.email", 0) >= 1
        assert second.get("users.email", 0) == 0


class TestSeedPreservation:
    def test_canonical_classes_traits_dungeons_survive(self, db):
        """Cleanup must not touch the canonical seed (12 classes, 30 traits,
        10 dungeons)."""
        from tests.conftest import _run_pollution_sweep
        n_classes_before = db.adventurer_classes.count_documents({"is_active": True})
        n_traits_before = db.traits.count_documents({"is_active": True})
        n_dungeons_before = db.dungeons.count_documents({"is_active": True})
        _run_pollution_sweep(db)
        assert db.adventurer_classes.count_documents({"is_active": True}) == n_classes_before
        assert db.traits.count_documents({"is_active": True}) == n_traits_before
        assert db.dungeons.count_documents({"is_active": True}) == n_dungeons_before
        # Tester admin must survive
        tester = db.users.find_one({"email": "tester@orbus.test"})
        assert tester is not None, "tester@orbus.test must NOT be deleted by cleanup"
