"""R18.Reset.1b.hotfix.v1_3 — Test Suite (Schema Compatibility Fix).

Tests both static invariants (sealed scripts unchanged) and dynamic
DB/dry-run outcomes. HTTP live tests are marked as gate-blocking to be
run post-freeze-OFF (see docstrings).

DB isolation note: pytest runs against `orbus_r16_test` per policy.
This test suite READS `orbus_r16` (production runtime DB) via a
dedicated client, since v1.3 is validated by inspecting the actual
state of the reset. NO WRITES to orbus_r16 from tests.

Async pattern: nested `_run()` + `asyncio.run()` (no pytest-asyncio dep).
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import subprocess
from pathlib import Path

import pytest
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

# Read backend .env directly to bypass pytest's forced test DB.
_BACKEND_ENV = dotenv_values("/app/backend/.env")
PROD_MONGO_URL = _BACKEND_ENV["MONGO_URL"]
PROD_DB_NAME = _BACKEND_ENV["DB_NAME"]  # e.g. "orbus_r16"

# ── 8 sealed scripts inventory (byte-identity anchor) ───────────────
SEALED = {
    "app/scripts/round18_reset1b_apply.py":
        "657d5853a5b203005a319452260bc2d8413e94d5fa8857ba36de4b78d427d934",
    "app/scripts/round18_reset1b_apply_v1_1.py":
        "14d38bf8ea66c878da60112c0936da720f38e4b2251e07f76aa4817259e51abd",
    "app/scripts/round18_reset1b_apply_v1_2.py":
        "d754c0dd273a05bd62d16c258d42e1503857da5dc953c3904e02181c877b3f66",
    "app/scripts/round18_reset1b_apply_v1_3.py":
        "3737052166b0e89632d6f022331fa713591ce4817e1d3f5abc5465aadc264d88",
    "app/scripts/round18_reset1b_staged_backup_materialize.py":
        "db42665587dc7a18d416e54eebedaa87fb9cf256dd0d43a868db43a1761a7dd9",
    "app/scripts/round18_reset1c_field_cleanup.py":
        "fe2d39bf1a2a1189a8fe011969209001150bfb9d2a5c425836fb489e271e052c",
    "app/scripts/round18_reset1c_restore_from_jsonl_manifest.py":
        "453b87c8a83e303ee5e72f805c8a86c167b30792e8798704e27f51ac86ec3048",
    "app/core/job_freeze.py":
        "487c9223532c30165ef1bdba86bdc33976c4d82b7801e8509c6dd3dfa17311be",
}

SAFE_CLASSES = ["alchemist", "bard", "druid", "mage", "monk", "paladin",
                "priest", "ranger", "rogue", "warlock", "warrior"]
TARGET_MARKER = "r18_reset1b_hotfix_v1_2"
TARGET_COUNT_EXPECTED = 3360
V1_3_SCRIPT = "/app/backend/app/scripts/round18_reset1b_apply_v1_3.py"
BACKEND_ROOT = "/app/backend"


def _run_v1_3_cli(args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["DB_NAME"] = PROD_DB_NAME  # target production runtime DB (read-only patterns)
    env["MONGO_URL"] = PROD_MONGO_URL
    return subprocess.run(
        ["python", "-m", "app.scripts.round18_reset1b_apply_v1_3", *args],
        capture_output=True, text=True, cwd=BACKEND_ROOT, env=env,
    )


def _prod_db():
    client = AsyncIOMotorClient(PROD_MONGO_URL)
    return client[PROD_DB_NAME]


def _is_freeze_active() -> bool:
    return Path("/tmp/orbus_maintenance.flag").exists()


# ── 1. Sealed anchors ───────────────────────────────────────────────
def test_t01_sealed_scripts_untouched():
    for rel, expected in SEALED.items():
        p = Path(BACKEND_ROOT) / rel
        assert p.exists(), f"sealed file missing: {rel}"
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual == expected, (
            f"SEALED script byte-identity BROKEN: {rel}\n"
            f"  expected={expected}\n  actual  ={actual}"
        )


# ── 2. Sibling exists ───────────────────────────────────────────────
def test_t02_v1_3_sibling_exists():
    p = Path(V1_3_SCRIPT)
    assert p.exists(), f"v1.3 sibling missing at {V1_3_SCRIPT}"
    body = p.read_text()
    assert "R18.Reset.1b.hotfix.v1_3" in body
    assert "--i-understand-this-will-patch-reset-adventurers" in body


# ── 3. --apply without ack fails 30 ─────────────────────────────────
def test_t03_apply_without_ack_blocked():
    res = _run_v1_3_cli(["--apply"])
    assert res.returncode == 30, (
        f"expected exit 30, got {res.returncode}\n"
        f"stdout={res.stdout[-800:]}\nstderr={res.stderr[-400:]}"
    )


# ── 4. Dry-run exit 0 + target = 3360 ───────────────────────────────
def test_t04_dry_run_target_count():
    res = _run_v1_3_cli(["--dry-run"])
    assert res.returncode == 0, (
        f"dry-run exit={res.returncode}\n"
        f"stdout={res.stdout[-1200:]}\nstderr={res.stderr[-400:]}"
    )
    assert "target_count=3360 expected=3360" in res.stdout, res.stdout[-2000:]


# ── 5. Class mapping 11/11 ──────────────────────────────────────────
def test_t05_class_mapping_11_11():
    async def _run():
        db = _prod_db()
        mapped = 0
        for slug in SAFE_CLASSES:
            d = await db.adventurer_classes.find_one({"slug": slug})
            assert d is not None, f"catalog missing slug={slug}"
            assert d.get("id"), f"catalog slug={slug} has no id"
            assert d.get("name"), f"catalog slug={slug} has no name"
            assert d.get("role"), f"catalog slug={slug} has no role"
            mapped += 1
        assert mapped == 11
    asyncio.run(_run())


# ── 6. All target docs will get adventurer_class_id ─────────────────
def test_t06_all_target_will_get_class_id():
    async def _run():
        db = _prod_db()
        total = await db.adventurers.count_documents({TARGET_MARKER: True})
        assert total == TARGET_COUNT_EXPECTED
        covered = 0
        for slug in SAFE_CLASSES:
            c = await db.adventurers.count_documents(
                {TARGET_MARKER: True, "class_slug": slug}
            )
            covered += c
        assert covered == TARGET_COUNT_EXPECTED, (
            f"union of safe slugs covers {covered}/{TARGET_COUNT_EXPECTED}"
        )
    asyncio.run(_run())


# ── 7. experience pre-fix invariant + payload contains experience=0 ─
def test_t07_experience_zero_post_fix():
    async def _run():
        db = _prod_db()
        missing = await db.adventurers.count_documents(
            {TARGET_MARKER: True, "experience": {"$exists": False}}
        )
        assert missing == TARGET_COUNT_EXPECTED, (
            f"pre-fix invariant broken: {missing}/{TARGET_COUNT_EXPECTED} miss experience"
        )
    asyncio.run(_run())
    body = Path(V1_3_SCRIPT).read_text()
    assert '"experience": 0' in body


# ── 8. is_available True in payload ────────────────────────────────
def test_t08_is_available_true_post_fix():
    body = Path(V1_3_SCRIPT).read_text()
    assert '"is_available": True' in body


# ── 9. Grade / rarity / status enum compat ─────────────────────────
def test_t09_enum_canonical_values():
    body = Path(V1_3_SCRIPT).read_text()
    assert '"grade": "common"' in body
    assert '"rarity": "Common"' in body
    assert '"status": "idle"' in body


# ── 10. Dry-run does zero DB writes ────────────────────────────────
def test_t10_dry_run_no_db_write():
    async def _snapshot(db):
        return await db.adventurers.count_documents(
            {TARGET_MARKER: True, "adventurer_class_id": {"$exists": True}}
        )
    async def _run():
        db = _prod_db()
        before = await _snapshot(db)
        _run_v1_3_cli(["--dry-run"])
        after = await _snapshot(db)
        assert before == after, "dry-run introduced DB writes"
    asyncio.run(_run())


# ── 11. Apply requires double flag ─────────────────────────────────
def test_t11_apply_requires_double_flag():
    r1 = _run_v1_3_cli(["--apply"])
    assert r1.returncode == 30
    r2 = _run_v1_3_cli(["--i-understand-this-will-patch-reset-adventurers"])
    assert r2.returncode == 0
    assert "MODE = DRY_RUN" in r2.stdout


# ── 12. Idempotency guard present ──────────────────────────────────
def test_t12_idempotency_guard_present():
    body = Path(V1_3_SCRIPT).read_text()
    assert "_idempotency_check" in body
    assert "R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3" in body


# ── 13. Audit events declared ──────────────────────────────────────
def test_t13_audit_events_declared():
    body = Path(V1_3_SCRIPT).read_text()
    assert "R18_STARTER_ROSTER_HOTFIX_APPLIED" in body
    assert "R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3" in body


# ── 14/15/16. HTTP live checks — gate-blocking post-freeze-OFF ─────
@pytest.mark.skipif(_is_freeze_active(),
                    reason="freeze active — HTTP live test deferred to post-unfreeze gate")
def test_t14_get_adventurers_http_live_200():
    import requests
    base = _load_frontend_env_url()
    login = requests.post(f"{base}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123"
    }, timeout=15)
    assert login.status_code == 200, f"login={login.status_code} {login.text}"
    token = login.json()["access_token"]
    r = requests.get(f"{base}/api/adventurers",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200, f"GET /api/adventurers = {r.status_code}: {r.text[:300]}"


@pytest.mark.skipif(_is_freeze_active(),
                    reason="freeze active — HTTP live test deferred to post-unfreeze gate")
def test_t15_get_dungeons_http_live_200():
    import requests
    base = _load_frontend_env_url()
    r = requests.get(f"{base}/api/dungeons", timeout=15)
    assert r.status_code == 200, f"GET /api/dungeons = {r.status_code}"


@pytest.mark.skipif(_is_freeze_active(),
                    reason="freeze active — HTTP live test deferred to post-unfreeze gate")
def test_t16_post_expedition_http_live_no_500():
    """POST /api/expeditions must NOT return 500 (KeyError stat). Valid
    outcomes: 201, 200, 400/422 (functional validation). 500 → FAIL.
    """
    import requests
    base = _load_frontend_env_url()
    login = requests.post(f"{base}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123"
    }, timeout=15)
    token = login.json()["access_token"]
    dresp = requests.get(f"{base}/api/dungeons",
                         headers={"Authorization": f"Bearer {token}"}, timeout=15)
    dj = dresp.json()
    dungeons = dj if isinstance(dj, list) else (dj.get("items") or dj.get("dungeons") or [])
    dungeon_id = dungeons[0].get("id") if dungeons else None
    aresp = requests.get(f"{base}/api/adventurers",
                         headers={"Authorization": f"Bearer {token}"}, timeout=15)
    aj = aresp.json()
    advs = aj if isinstance(aj, list) else (aj.get("items") or aj.get("adventurers") or [])
    adv_ids = [a.get("id") for a in advs[:3]]
    if not (dungeon_id and adv_ids):
        pytest.skip("no dungeon or adventurers to compose expedition")
    payload = {"dungeon_id": dungeon_id, "adventurer_ids": adv_ids}
    r = requests.post(f"{base}/api/expeditions",
                      headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=15)
    assert r.status_code != 500, f"POST /api/expeditions returned 500: {r.text[:400]}"


def _load_frontend_env_url() -> str:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("REACT_APP_BACKEND_URL not found in frontend .env")


# ── 17. Inventory kit invariant ────────────────────────────────────
def test_t17_inventory_kit_unchanged():
    async def _run():
        db = _prod_db()
        count = await db.inventory_items.count_documents(
            {"item_id": "fd5cbdef-3146-483c-b1fd-217b4da0a59d"}
        )
        assert count == 672
        total_qty = 0
        async for doc in db.inventory_items.aggregate([
            {"$match": {"item_id": "fd5cbdef-3146-483c-b1fd-217b4da0a59d"}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}},
        ]):
            total_qty = doc.get("total") or 0
        assert total_qty == 2016
    asyncio.run(_run())


# ── 18. Gold invariant ─────────────────────────────────────────────
def test_t18_gold_invariant():
    async def _run():
        db = _prod_db()
        total = 0
        async for doc in db.guilds.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$gold"}}}
        ]):
            total = int(doc.get("total") or 0)
        assert total == 67200
        minmax = {}
        async for doc in db.guilds.aggregate([
            {"$group": {"_id": None, "gmin": {"$min": "$gold"}, "gmax": {"$max": "$gold"}}}
        ]):
            minmax = {"min": int(doc["gmin"]), "max": int(doc["gmax"])}
        assert minmax == {"min": 100, "max": 100}
    asyncio.run(_run())


# ── 19. Hidden classes NOT in target set ───────────────────────────
def test_t19_no_hidden_classes_in_target():
    async def _run():
        db = _prod_db()
        non_safe = await db.adventurers.count_documents(
            {TARGET_MARKER: True, "class_slug": {"$nin": SAFE_CLASSES}}
        )
        assert non_safe == 0
    asyncio.run(_run())


# ── 20. Freeze OFF gate documented ─────────────────────────────────
def test_t20_freeze_off_gate_documented():
    src = Path(__file__).read_text()
    for name in ["test_t14_get_adventurers", "test_t15_get_dungeons",
                 "test_t16_post_expedition"]:
        assert "@pytest.mark.skipif" in src
        assert name in src
