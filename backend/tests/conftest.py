"""Pytest fixtures shared by Orbus backend tests."""
import logging
import os
import re
from pathlib import Path

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient

# Load backend .env early so DB_NAME / MONGO_URL / APP_ENV are visible to
# the cleanup safety rails. Without this the conftest would see whatever
# vars the shell happened to export, which on CI defaults to nothing.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger("orbus.test.cleanup")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[orbus.test] %(levelname)s %(message)s"))
    logger.addHandler(h)


# Whitelist of patterns (regex) treated as test-pollution. Anchored where
# possible. Each tuple is (collection, field, pattern, description).
TEST_POLLUTION_PATTERNS = [
    # Users created by registration helpers in tests
    ("users", "email", r"^([a-z][a-z0-9]{0,8}_[a-z0-9]{6,}@orbus\.test|test_|tester_|OrbusE2E|orbusE2E|e2e\d?_|smoke_|playtest_|uitest|reg_|p\d|pr\d|ref_|gates_|disp_|unlock_|dh_|sc_|gw_)", "test users"),
    # Guilds named with test patterns
    ("guilds", "name", r"^(TEST_|G_p\d|G_p93|G_p13|G_p931|G_OrbusE2E|TestGuild_|Test G|p\d+_|P\d+Guild|ExpG_|Guild_\d|Smoke|UI Tes|GA_|GB_|E2E_)", "test guilds"),
    # Adventurers spawned by test helpers
    ("adventurers", "name", r"^(Phase13Hero|P13Hero_|AdvP931_|TestAdv_|p\d+Hero_|SmokeAdv_)", "test adventurers"),
    # Items/Dungeons/Classes the admin test seeded with Test* prefix
    ("items", "slug", r"^(itm-|test_|TEST_|cosmetic-ok-|patch-test-|pure-[a-z0-9]+$|premium-test-|prem_test-)", "test items"),
    ("items", "name", r"^Test", "test items by name"),
    ("dungeons", "name", r"^Test", "test dungeons"),
    ("adventurer_classes", "name", r"^Test", "test classes"),
    ("traits", "name", r"^Test", "test traits"),
    # Inventory rows referencing the test items we just nuked
    # (handled in a separate pass — orphan cleanup)
    # Expeditions belonging to test guilds get nuked by their guild_id below.
    # Password reset tokens & email outbox entries scoped to test users
    ("password_reset_tokens", "email", r"^(p\d+_|p93_|p13_|p931_|pr6_|test_|OrbusE2E|orbusE2E)", "test reset tokens"),
]


def _is_test_db() -> bool:
    app_env = (os.environ.get("APP_ENV") or "").lower().strip()
    if app_env in {"test", "testing", "ci"}:
        return True
    if "test" in (os.environ.get("MONGO_URL") or "").lower():
        return True
    if "test" in (os.environ.get("DB_NAME") or "").lower():
        return True
    return False


def _run_pollution_sweep(db) -> dict:
    """Run all whitelist patterns; return per-collection deletion counts."""
    deleted: dict[str, int] = {}
    for coll, field, pattern, _desc in TEST_POLLUTION_PATTERNS:
        try:
            rx = re.compile(pattern)
            res = db[coll].delete_many({field: {"$regex": rx.pattern}})
            if res.deleted_count:
                deleted[f"{coll}.{field}"] = deleted.get(f"{coll}.{field}", 0) + res.deleted_count
        except Exception as exc:  # noqa: BLE001
            logger.warning("cleanup failed on %s.%s: %s", coll, field, exc)
    # Orphan inventory rows: rows whose item_id no longer exists in items
    try:
        item_ids = {d["id"] for d in db.items.find({}, {"id": 1, "_id": 0})}
        if item_ids:
            orph = db.inventory_items.delete_many({"item_id": {"$nin": list(item_ids)}})
            if orph.deleted_count:
                deleted["inventory_items.orphan"] = orph.deleted_count
    except Exception as exc:  # noqa: BLE001
        logger.warning("orphan inventory cleanup failed: %s", exc)
    # Orphan expedition_members: members whose adventurer_id no longer exists
    try:
        adv_ids = {d["id"] for d in db.adventurers.find({}, {"id": 1, "_id": 0})}
        if adv_ids:
            res = db.expedition_members.delete_many({"adventurer_id": {"$nin": list(adv_ids)}})
            if res.deleted_count:
                deleted["expedition_members.orphan"] = res.deleted_count
    except Exception as exc:  # noqa: BLE001
        logger.warning("orphan members cleanup failed: %s", exc)
    return deleted


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_pollution():
    """Session fixture — kept as a no-op shim.

    The real cleanup now runs in `pytest_configure` (once globally, before
    xdist forks workers). This fixture exists only so that direct imports
    of `_cleanup_test_pollution` keep working and to document the design.
    """
    yield


def pytest_configure(config):
    """Runs ONCE per pytest invocation, BEFORE xdist forks workers.

    Safe place to clean pollution because there are no concurrent test
    sessions yet. Skipped on non-test databases (production safety).
    """
    # Skip on xdist workers — only run in the controller process to avoid
    # double-execution and cross-worker interference.
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    if not _is_test_db():
        logger.warning(
            "Test pollution cleanup SKIPPED (DB doesn't look like a test DB). "
            "Set APP_ENV=test or use a DB_NAME containing 'test' to enable."
        )
        return
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        return
    client = MongoClient(mongo_url)
    try:
        db = client[db_name]
        deleted = _run_pollution_sweep(db)
        if deleted:
            logger.info("pre-suite cleanup removed: %s", deleted)
        else:
            logger.info("pre-suite cleanup: DB already clean")
    finally:
        client.close()


__all__ = [
    "_cleanup_test_pollution",
    "_run_pollution_sweep",
    "_is_test_db",
    "TEST_POLLUTION_PATTERNS",
]

# ----------------------------------------------------------------------
# Pattern 2 (FUTURE — not implemented)
# ----------------------------------------------------------------------
# A more aggressive approach would be to give every xdist worker its own
# isolated DB, e.g. `${DB_NAME}_w${PYTEST_XDIST_WORKER}`. That would fully
# eliminate cross-worker interference (the root cause of the flaky phase7
# tests). It requires either patching `app.core.database.db` to honour
# the worker id, or running each worker in its own process group with
# different env. Out of scope for Phase 13.1 — documented for a follow-up.
