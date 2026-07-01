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

# ROUND 16.3 Iter B (P2.1) — Hard guard-rail: pytest MUST NEVER write to a
# non-test DB. This assertion runs at conftest import time (before ANY test
# module is imported), so a misconfigured environment cannot bypass it.
# Bypass rules:
#   1. DB_NAME must end with "_test" OR contain the token "test" in lowercase
#   2. OR APP_ENV must equal "test" / "testing" / "ci"
# See /app/memory/pytest_db_isolation_policy.md for the full policy.
_pytest_db_name = os.environ.get("DB_NAME", "")
_pytest_app_env = (os.environ.get("APP_ENV") or "").lower()
_db_name_looks_testy = (
    _pytest_db_name.endswith("_test")
    or "test" in _pytest_db_name.lower()
)
_app_env_is_test = _pytest_app_env in {"test", "testing", "ci"}
if not (_db_name_looks_testy or _app_env_is_test):
    raise RuntimeError(
        "REFUSING to run pytest against non-test DB: "
        f"DB_NAME={_pytest_db_name!r} APP_ENV={_pytest_app_env!r}. "
        "Ensure /app/backend/tests/.env.test defines "
        "DB_NAME=<something>_test (e.g. orbus_r16_test) and APP_ENV=test. "
        "See /app/memory/pytest_db_isolation_policy.md."
    )
del _pytest_db_name, _pytest_app_env, _db_name_looks_testy, _app_env_is_test

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
    "isolated_backend_url",
]


# ═════════════════════════════════════════════════════════════════════
# ROUND 16.3 P3.1 — ISOLATED HTTP BACKEND (opt-in)
# ═════════════════════════════════════════════════════════════════════
#
# Problem: previously, tests that hit REACT_APP_BACKEND_URL (the running
# supervised backend on :8001) bypassed the DB isolation guard, because
# the running backend uses backend/.env → DB_NAME=orbus_r16 (dev DB).
#
# Fix: opt-in fixture that spawns a SECOND uvicorn instance on port 8002
# with DB_NAME=orbus_r16_test + APP_ENV=test, then exposes its URL via
# the `isolated_backend_url` fixture. Tests that use this URL never write
# to the prod-dev DB.
#
# Activation: set env `ISOLATED_HTTP_TESTS=1` before invoking pytest.
# When inactive, `isolated_backend_url` falls back to REACT_APP_BACKEND_URL
# (backward compat).
#
# See /app/memory/pytest_db_isolation_policy.md for the full policy.

_ISOLATED_BACKEND_PORT = 8002
_ISOLATED_BACKEND_HOST = "127.0.0.1"
_ISOLATED_BACKEND_URL = f"http://{_ISOLATED_BACKEND_HOST}:{_ISOLATED_BACKEND_PORT}"


def _spawn_isolated_backend():
    """Spawn a uvicorn subprocess bound to orbus_r16_test on port 8002.

    Waits up to 30s for /api/health to return 200 before returning the URL.
    Raises if startup fails, so tests bail out instead of silently hitting
    the wrong backend.
    """
    import subprocess
    import time
    import httpx

    env = os.environ.copy()
    env["DB_NAME"] = os.environ.get("DB_NAME", "orbus_r16_test")
    env["APP_ENV"] = "test"
    # PYTEST_XDIST_WORKER must NOT be propagated: uvicorn is a fresh process.
    env.pop("PYTEST_XDIST_WORKER", None)

    proc = subprocess.Popen(
        ["uvicorn", "server:app",
         "--host", _ISOLATED_BACKEND_HOST,
         "--port", str(_ISOLATED_BACKEND_PORT),
         "--log-level", "warning"],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Health check with timeout.
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"isolated backend died with code {proc.returncode} "
                "before health check succeeded"
            )
        try:
            r = httpx.get(f"{_ISOLATED_BACKEND_URL}/api/health", timeout=1.0)
            if r.status_code == 200:
                logger.info(
                    "isolated backend ready on %s (DB_NAME=%s)",
                    _ISOLATED_BACKEND_URL, env["DB_NAME"],
                )
                return proc
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError(
        f"isolated backend did NOT become healthy within 30s "
        f"(port {_ISOLATED_BACKEND_PORT} may be busy)"
    )


@pytest.fixture(scope="session")
def isolated_backend_url() -> str:
    """URL of the isolated backend spawned for HTTP admin tests.

    - When `ISOLATED_HTTP_TESTS=1` env is set: spawn subprocess uvicorn on
      port 8002 with DB_NAME=orbus_r16_test, return its URL, and teardown
      the process at session end.
    - Otherwise: fall back to REACT_APP_BACKEND_URL (backward compat).

    Test authors: prefer this fixture over REACT_APP_BACKEND_URL for any
    test that mutates DB state via HTTP (POST/PUT/DELETE, admin routes).
    """
    if os.environ.get("ISOLATED_HTTP_TESTS") == "1":
        # Only the xdist controller spawns the subprocess; workers reuse it
        # via the shared port. Guard against per-worker double-spawn.
        if os.environ.get("PYTEST_XDIST_WORKER"):
            yield _ISOLATED_BACKEND_URL
            return
        proc = _spawn_isolated_backend()
        try:
            yield _ISOLATED_BACKEND_URL
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                proc.kill()
            logger.info("isolated backend terminated")
    else:
        yield os.environ.get("REACT_APP_BACKEND_URL") or ""


# Autouse fixture: when ISOLATED_HTTP_TESTS=1, transparently override
# REACT_APP_BACKEND_URL with the isolated backend so pre-existing tests
# that read env directly (via `os.environ["REACT_APP_BACKEND_URL"]`) also
# benefit from the isolation with ZERO code change.
@pytest.fixture(scope="session", autouse=True)
def _apply_isolated_backend_env(isolated_backend_url):
    if os.environ.get("ISOLATED_HTTP_TESTS") == "1":
        prev = os.environ.get("REACT_APP_BACKEND_URL")
        os.environ["REACT_APP_BACKEND_URL"] = isolated_backend_url
        logger.info(
            "REACT_APP_BACKEND_URL overridden with isolated backend: %s",
            isolated_backend_url,
        )
        yield
        if prev is not None:
            os.environ["REACT_APP_BACKEND_URL"] = prev
        else:
            os.environ.pop("REACT_APP_BACKEND_URL", None)
    else:
        yield

# ----------------------------------------------------------------------
# Pattern 2 (FUTURE — not implemented)
# ----------------------------------------------------------------------
# A more aggressive approach would be to give every xdist worker its own
# isolated DB, e.g. `${DB_NAME}_w${PYTEST_XDIST_WORKER}`. That would fully
# eliminate cross-worker interference (the root cause of the flaky phase7
# tests). It requires either patching `app.core.database.db` to honour
# the worker id, or running each worker in its own process group with
# different env. Out of scope for Phase 13.1 — documented for a follow-up.
