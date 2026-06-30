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

# ROUND 6B FASE A — also load `tests/.env.test` so credential-style values
# the test suite consumes (TEST_USER_PASSWORD, TEST_SMTP_*) live outside the
# source tree. The file is gitignored; `.env.test.example` is the committed
# template. Real `.env.test` values OVERRIDE backend/.env on key conflicts.
load_dotenv(Path(__file__).resolve().parent / ".env.test", override=True)

logger = logging.getLogger("orbus.test.cleanup")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[orbus.test] %(levelname)s %(message)s"))
    logger.addHandler(h)


# ── PERMANENT ALLOWLIST (Phase 14.5-hotfix, 2026-06-25) ─────────────────────
# Single source of truth. ANY cleanup operation that deletes/flags users or
# guilds MUST honour these sets. The pollution sweep below applies them as a
# post-filter on every delete_many call.
ALLOWLIST_EMAILS = frozenset({
    "mr.gualmini@gmail.com",
    "gianluca.brandi42@gmail.com",
    "tester@orbus.test",  # tester sandbox admin (seeded in dev only)
    "clean_onboarding@orbus.test",  # R16.1 Phase 4 — pristine onboarding fixture (auto-seeded in dev/preview)
    "samuelemazzini1994@gmail.com",  # Harambes owner — confirmed 2026-06-26
    "ginnyo.gear@gmail.com",         # Magmorella — Il Regno di Lanafuoco — confirmed 2026-06-26
    "lordcoby87@gmail.com",          # Crociata d'Argento owner — confirmed 2026-06-26
    "kyrie.shepard@gmail.com",       # Eclipse Vanguard owner — confirmed 2026-06-27 (Phase 19.2)
})
ALLOWLIST_GUILDS_LOWER = frozenset({
    "sentiero di efreto",
    "drakarys",
    "harambes",  # real prod player (owner email pending)
    "the loremaster",  # CONFIRMED real player (mr.gualmini@gmail.com) — 2026-06-26
    "il regno di lanafuoco",  # CONFIRMED real player — 2026-06-26 (owner email TBD)
    "crociata d'argento",  # CONFIRMED new real tester — 2026-06-26 (owner email TBD, rank 1 prod)
    "eclipse vanguard",  # CONFIRMED real player (kyrie.shepard@gmail.com) — 2026-06-27 (Phase 19.2)
})


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


def _allowlist_user_ids(db) -> set:
    """Snapshot user.id values for all allowlisted emails (case-insensitive)."""
    rows = list(db.users.find(
        {"email": {"$in": [e for e in ALLOWLIST_EMAILS]}},
        {"id": 1, "_id": 0},
    ))
    return {r["id"] for r in rows if r.get("id")}


def _run_pollution_sweep(db) -> dict:
    """Run all whitelist patterns; return per-collection deletion counts.

    Safety rails (Phase 14.5-hotfix):
      - Each delete_many gets a $nin filter over ALLOWLIST_EMAILS / lowered
        guild names so the regex CANNOT match a protected account even if a
        future pattern accidentally widens the net.
      - Adventurer/inventory/expedition deletes use guild_id $nin allowlist.
    """
    deleted: dict[str, int] = {}
    allow_user_ids = _allowlist_user_ids(db)
    allow_guild_ids = {
        g["id"]
        for g in db.guilds.find(
            {"$expr": {"$in": [{"$toLower": "$name"}, list(ALLOWLIST_GUILDS_LOWER)]}},
            {"id": 1, "_id": 0},
        )
        if g.get("id")
    }
    for coll, field, pattern, _desc in TEST_POLLUTION_PATTERNS:
        try:
            rx = re.compile(pattern)
            q = {field: {"$regex": rx.pattern}}
            # Belt-and-suspenders allowlist filter per collection.
            if coll == "users":
                q["email"] = {"$regex": rx.pattern, "$nin": list(ALLOWLIST_EMAILS)}
            elif coll == "guilds":
                # Exclude guilds whose lowered name is in the allowlist OR
                # whose owner is allowlisted.
                q = {
                    "$and": [
                        {field: {"$regex": rx.pattern}},
                        {"$expr": {"$not": {"$in": [{"$toLower": "$name"}, list(ALLOWLIST_GUILDS_LOWER)]}}},
                        {"owner_user_id": {"$nin": list(allow_user_ids)}},
                    ]
                }
            elif coll in ("adventurers", "expedition_members") and allow_guild_ids:
                q = {"$and": [{field: {"$regex": rx.pattern}}, {"guild_id": {"$nin": list(allow_guild_ids)}}]}
            res = db[coll].delete_many(q)
            if res.deleted_count:
                deleted[f"{coll}.{field}"] = deleted.get(f"{coll}.{field}", 0) + res.deleted_count
        except Exception as exc:  # noqa: BLE001
            logger.warning("cleanup failed on %s.%s: %s", coll, field, exc)
    # Orphan inventory rows: rows whose item_id no longer exists in items.
    # Still safe — even if Drakarys had inventory, this only nukes rows whose
    # referenced item has already been deleted.
    # ROUND 6C — signature items are now seeded into `db.items` as part of
    # the boot lifecycle, so they normally resolve. As an extra safety net
    # (catalog edits, race conditions during a test run), we also exclude
    # rows that carry a `bound_reason` — these are always considered
    # intentional (signature, dev seed, crafting, etc.) and must NEVER be
    # treated as orphans.
    try:
        item_ids = {d["id"] for d in db.items.find({}, {"id": 1, "_id": 0})}
        if item_ids:
            orph = db.inventory_items.delete_many({
                "item_id": {"$nin": list(item_ids)},
                "$or": [
                    {"bound_reason": {"$exists": False}},
                    {"bound_reason": None},
                ],
            })
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
    "ALLOWLIST_EMAILS",
    "ALLOWLIST_GUILDS_LOWER",
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
