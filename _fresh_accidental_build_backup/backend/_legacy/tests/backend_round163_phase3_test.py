"""ROUND 16.3 Phase 3 — Continent events + Site contracts V1 tests."""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


def _login(email, password="password123"):
    r = requests.post(f"{API_BASE}/api/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login("tester@orbus.test")


@pytest.fixture(scope="module")
def clean_headers():
    return _login("clean_onboarding@orbus.test")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


async def _cleanup_phase3_state():
    """Rimuove event instances di test + ledger rows del giorno per il tester."""
    from app.core.database import db
    await db.continent_event_instances.delete_many(
        {"event_slug": {"$in": ["boom_commerciale", "carestia",
                                "clima_mite", "maledizione", "stagione_fertile"]}}
    )
    guild = await db.guilds.find_one({"name": "The Iron Lantern"},
                                     {"_id": 0, "id": 1})
    if guild:
        await db.guild_site_income_ledger.delete_many({"guild_id": guild["id"]})


@pytest.fixture(scope="module", autouse=True)
def _pre_suite_cleanup():
    # Ensure Phase 3 seeds are present (conftest wipes DB before suite).
    from app.world_events import seed_continent_event_catalog
    from app.site_contracts import seed_site_income_config, ensure_indexes
    _run(seed_continent_event_catalog())
    _run(seed_site_income_config())
    _run(ensure_indexes())
    _run(_cleanup_phase3_state())
    yield
    _run(_cleanup_phase3_state())


async def _get_tester_guild_id() -> str:
    from app.core.database import db
    g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                  {"_id": 0, "id": 1})
    return g["id"]


# ── T01/T02/T03 catalog seed ──────────────────────────────────────
def test_catalog_seed_creates_12_events():
    from app.core.database import db
    async def _c():
        n = await db.continent_event_catalog.count_documents({})
        assert n == 12, f"expected 12 catalog rows, got {n}"
        slugs = sorted(await db.continent_event_catalog.distinct("slug"))
        assert "boom_commerciale" in slugs
        assert "carestia" in slugs
        assert "frattura_del_vuoto" in slugs
    _run(_c())


def test_catalog_seed_idempotent():
    from app.core.database import db
    from app.world_events import seed_continent_event_catalog
    async def _c():
        r1 = await seed_continent_event_catalog()
        r2 = await seed_continent_event_catalog()
        assert r2["inserted"] == 0
        assert r1["total"] == 12
        n = await db.continent_event_catalog.count_documents({})
        assert n == 12
    _run(_c())


def test_catalog_modifier_ranges_within_bounds():
    from app.core.database import db
    async def _c():
        docs = await db.continent_event_catalog.find({}, {"_id": 0}).to_list(50)
        for d in docs:
            mv = d.get("modifier_value") or 0
            assert -30 <= int(mv) <= 30, f"{d['slug']} out of bounds: {mv}"
    _run(_c())


# ── T04-T07 event admin flow ──────────────────────────────────────
def test_admin_create_event_scheduled(admin_headers):
    now = _now()
    body = {"continent_slug": "ambash", "event_slug": "boom_commerciale",
            "starts_at": _iso(now + timedelta(hours=1)),
            "ends_at": _iso(now + timedelta(days=2))}
    r = requests.post(f"{API_BASE}/api/admin/world-events",
                       json=body, headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()["instance"]
    assert data["status"] == "scheduled"
    assert data["continent_slug"] == "ambash"


def test_admin_activate_event(admin_headers):
    # Create fresh scheduled
    now = _now()
    body = {"continent_slug": "velur", "event_slug": "clima_mite",
            "starts_at": _iso(now),
            "ends_at": _iso(now + timedelta(days=1))}
    r = requests.post(f"{API_BASE}/api/admin/world-events",
                       json=body, headers=admin_headers, timeout=10)
    assert r.status_code == 200
    eid = r.json()["instance"]["id"]
    # Activate
    r2 = requests.post(f"{API_BASE}/api/admin/world-events/{eid}/activate",
                       headers=admin_headers, timeout=10)
    assert r2.status_code == 200, r2.text
    assert r2.json()["instance"]["status"] == "active"


def test_admin_activate_conflict_when_another_active(admin_headers):
    # First already-active on velur — try create-with-activate a second one
    now = _now()
    body = {"continent_slug": "velur", "event_slug": "stagione_fertile",
            "starts_at": _iso(now),
            "ends_at": _iso(now + timedelta(days=1)),
            "activate_now": True}
    r = requests.post(f"{API_BASE}/api/admin/world-events",
                       json=body, headers=admin_headers, timeout=10)
    assert r.status_code == 409, r.text


def test_admin_expire_event(admin_headers):
    # velur currently has active clima_mite; expire it
    r = requests.get(f"{API_BASE}/api/admin/world-events/all?continent_slug=velur",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    active = [i for i in r.json()["instances"] if i["status"] == "active"]
    assert active, "expected one active event on velur"
    eid = active[0]["id"]
    r2 = requests.post(f"{API_BASE}/api/admin/world-events/{eid}/expire",
                       headers=admin_headers, timeout=10)
    assert r2.status_code == 200
    assert r2.json()["instance"]["status"] == "expired"


# ── T08 max 1 active per continent ────────────────────────────────
def test_only_one_active_event_per_continent(admin_headers):
    # Now velur has no active event → create with activate_now succeeds
    now = _now()
    body = {"continent_slug": "velur", "event_slug": "stagione_fertile",
            "starts_at": _iso(now),
            "ends_at": _iso(now + timedelta(days=1)),
            "activate_now": True}
    r = requests.post(f"{API_BASE}/api/admin/world-events",
                       json=body, headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["instance"]["status"] == "active"
    # Try second one same continent, activate_now=True → 409
    body2 = {**body, "event_slug": "clima_mite"}
    r2 = requests.post(f"{API_BASE}/api/admin/world-events",
                        json=body2, headers=admin_headers, timeout=10)
    assert r2.status_code == 409


# ── T09-T13 site income daily row ─────────────────────────────────
def test_site_income_today_creates_row(admin_headers):
    r = requests.get(f"{API_BASE}/api/site-income/today",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "day_bucket" in data
    assert data["total_amount"] >= 0
    assert "breakdown" in data


def test_site_income_breakdown_structure(admin_headers):
    r = requests.get(f"{API_BASE}/api/site-income/today",
                     headers=admin_headers, timeout=10).json()
    b = r["breakdown"]
    for k in ("base", "level_bonus", "reputation_bonus", "event_bonus",
              "event_modifier_pct"):
        assert k in b, f"missing key {k}"


def test_site_income_hard_cap_respected():
    """Direct compute: hard_cap_daily=500 caps aggressive multipliers."""
    from app.site_contracts import _compute_breakdown
    config = {"base_income": 100, "level_bonus_per_level": 50,
              "hard_cap_daily": 500, "reputation_multiplier_max": 1.2}
    guild = {"guild_level": 20, "reputation": 5000}
    out = _compute_breakdown(config, guild, event_mod_pct=30)
    assert out["total_amount"] == 500, f"expected cap 500 got {out['total_amount']}"


def test_site_income_level_bonus_applied():
    from app.site_contracts import _compute_breakdown
    config = {"base_income": 20, "level_bonus_per_level": 5,
              "hard_cap_daily": 500, "reputation_multiplier_max": 1.2}
    lvl1 = _compute_breakdown(config, {"guild_level": 1, "reputation": 0}, 0)
    lvl10 = _compute_breakdown(config, {"guild_level": 10, "reputation": 0}, 0)
    # lv 1 = 20, lv 10 = 20 + 5*9 = 65
    assert lvl1["total_amount"] == 20
    assert lvl10["total_amount"] == 65


def test_site_income_reputation_multiplier_applied():
    from app.site_contracts import _compute_breakdown
    config = {"base_income": 100, "level_bonus_per_level": 0,
              "hard_cap_daily": 10000, "reputation_multiplier_max": 1.2}
    zero = _compute_breakdown(config, {"reputation": 0}, 0)
    high = _compute_breakdown(config, {"reputation": 200}, 0)
    max_rep = _compute_breakdown(config, {"reputation": 100000}, 0)
    # 0 rep → 100, 200 rep → +20% → 120, cap 1.2 → 120 stays
    assert zero["total_amount"] == 100
    assert high["total_amount"] == 120
    assert max_rep["total_amount"] == 120


# ── T14-T16 claim flow (idempotent) ───────────────────────────────
def test_claim_credits_gold_once(admin_headers):
    # Ensure fresh row for today (delete then re-create via /today)
    async def _reset():
        gid = await _get_tester_guild_id()
        from app.core.database import db
        from datetime import datetime, timezone
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        await db.guild_site_income_ledger.delete_many(
            {"guild_id": gid, "day_bucket": day})
    _run(_reset())
    # Get gold before
    async def _gold():
        gid = await _get_tester_guild_id()
        from app.core.database import db
        g = await db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})
        return g["gold"]
    gold_before = _run(_gold())
    today = requests.get(f"{API_BASE}/api/site-income/today",
                          headers=admin_headers, timeout=10).json()
    amount = today["total_amount"]
    r = requests.post(f"{API_BASE}/api/site-income/claim",
                       headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["amount"] == amount
    gold_after = _run(_gold())
    assert gold_after == gold_before + amount, \
        f"expected {gold_before}+{amount}={gold_before+amount}, got {gold_after}"


def test_claim_idempotent_retry(admin_headers):
    r = requests.post(f"{API_BASE}/api/site-income/claim",
                       headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "skipped"
    assert r.json()["reason"] == "already_claimed"


def test_claim_gold_not_double_credited(admin_headers):
    # Second retry — gold count should not increase
    async def _gold():
        gid = await _get_tester_guild_id()
        from app.core.database import db
        g = await db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})
        return g["gold"]
    before = _run(_gold())
    requests.post(f"{API_BASE}/api/site-income/claim",
                   headers=admin_headers, timeout=10)
    after = _run(_gold())
    assert after == before


# ── T17-T18 history ───────────────────────────────────────────────
def test_history_returns_recent_rows(admin_headers):
    r = requests.get(f"{API_BASE}/api/site-income/history?days=7",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert "rows" in r.json()
    assert len(r.json()["rows"]) >= 1


def test_history_capped_at_30_days(admin_headers):
    r = requests.get(f"{API_BASE}/api/site-income/history?days=999",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    # We only inserted 1-2 rows, but the days param should be capped internally
    assert len(r.json()["rows"]) <= 30


# ── T19-T21 audit ─────────────────────────────────────────────────
def test_audit_site_income_claimed_emitted():
    from app.core.database import db
    async def _c():
        n = await db.audit_log.count_documents({"event_type": "SITE_INCOME_CLAIMED"})
        assert n >= 1, "no SITE_INCOME_CLAIMED audit rows"
    _run(_c())


def test_audit_continent_event_created_emitted():
    from app.core.database import db
    async def _c():
        n = await db.audit_log.count_documents({"event_type": "CONTINENT_EVENT_CREATED"})
        assert n >= 1
    _run(_c())


def test_audit_whitelist_accepts_new_events(admin_headers):
    for et in ["CONTINENT_EVENT_CREATED", "CONTINENT_EVENT_ACTIVATED",
               "CONTINENT_EVENT_EXPIRED", "SITE_INCOME_CLAIMED",
               "SITE_INCOME_CONFIG_UPDATED"]:
        r = requests.get(f"{API_BASE}/api/admin/audit/events",
                         params={"event_type": et, "limit": 5},
                         headers=admin_headers, timeout=10)
        assert r.status_code == 200, f"{et}: {r.status_code} {r.text}"


# ── T22 admin config PATCH audit ──────────────────────────────────
def test_admin_config_patch_audits(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/site-income/config",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    original = r.json()["config"]
    orig_base = original.get("base_income", 20)
    # Change base income
    r2 = requests.patch(f"{API_BASE}/api/admin/site-income/config",
                         json={"base_income": orig_base}, headers=admin_headers,
                         timeout=10)
    assert r2.status_code == 200
    # Verify audit
    from app.core.database import db
    async def _c():
        n = await db.audit_log.count_documents(
            {"event_type": "SITE_INCOME_CONFIG_UPDATED"})
        assert n >= 1
    _run(_c())


# ── T23-T24 on-visit fallback expiry ──────────────────────────────
def test_on_visit_fallback_expires_stuck_event(admin_headers):
    # Force-create an "active" event with ends_at in the past on ergolat
    from app.core.database import db
    now = _now()
    eid = str(uuid.uuid4())

    async def _insert():
        await db.continent_event_instances.insert_one({
            "id": eid, "continent_slug": "ergolat",
            "event_slug": "clima_mite", "status": "active",
            "starts_at": _iso(now - timedelta(days=2)),
            "ends_at": _iso(now - timedelta(hours=1)),
            "activated_at": _iso(now - timedelta(days=2)),
            "created_at": _iso(now - timedelta(days=2)),
        })
    _run(_insert())
    # Public visit triggers expire
    r = requests.get(f"{API_BASE}/api/world-events/continent/ergolat/active",
                     timeout=10)
    assert r.status_code == 200
    async def _fetch():
        return await db.continent_event_instances.find_one({"id": eid}, {"_id": 0})
    doc = _run(_fetch())
    assert doc["status"] == "expired", f"expected expired, got {doc['status']}"


def test_recovery_script_expires_stuck_events():
    from app.core.database import db
    # Insert one active with ends_at in the past
    now = _now()
    eid = str(uuid.uuid4())

    async def _setup():
        await db.continent_event_instances.insert_one({
            "id": eid, "continent_slug": "irthe",
            "event_slug": "carestia", "status": "active",
            "starts_at": _iso(now - timedelta(days=1)),
            "ends_at": _iso(now - timedelta(minutes=5)),
            "activated_at": _iso(now - timedelta(days=1)),
            "created_at": _iso(now - timedelta(days=1)),
        })
    _run(_setup())
    from app.scripts.expire_stuck_continent_events import _run as script_run
    result = _run(script_run(apply=True))
    assert result["flipped"] >= 1
    async def _fetch():
        return await db.continent_event_instances.find_one({"id": eid}, {"_id": 0})
    doc = _run(_fetch())
    assert doc["status"] == "expired"


# ── T25 no hard delete ────────────────────────────────────────────
def test_no_hard_delete_on_expire():
    from app.core.database import db
    async def _c():
        total = await db.continent_event_instances.count_documents({})
        expired = await db.continent_event_instances.count_documents(
            {"status": "expired"})
        assert total > 0
        assert expired >= 1
        # No status==deleted expected
        deleted = await db.continent_event_instances.count_documents(
            {"status": "deleted"})
        assert deleted == 0
    _run(_c())


# ── T26 regression ────────────────────────────────────────────────
def test_regression_previous_modules_still_importable():
    from app.world_boss import resolve_stuck_world_boss_event
    from app.world import has_world_access
    from app.raids.recovery import resolve_stuck_raid
    assert callable(resolve_stuck_world_boss_event)
    assert callable(has_world_access)
    assert callable(resolve_stuck_raid)


# ── T27 OpenAPI ───────────────────────────────────────────────────
def test_openapi_has_phase3_paths():
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    paths = r.json()["paths"]
    required = [
        "/api/world-events/continent/{slug}/active",
        "/api/world-events/mine",
        "/api/site-income/today",
        "/api/site-income/claim",
        "/api/site-income/history",
        "/api/admin/world-events",
        "/api/admin/world-events/all",
        "/api/admin/world-events/{eid}/activate",
        "/api/admin/world-events/{eid}/expire",
        "/api/admin/site-income/config",
        "/api/admin/site-income/stats",
    ]
    for p in required:
        assert p in paths, f"missing {p}"


# ── T28 event modifier applied to today (integration) ─────────────
def test_event_modifier_reflected_in_today(admin_headers):
    """Se un evento site_income_pct è active sul continente della gilda,
    /today deve mostrare event_modifier_pct != 0."""
    async def _setup():
        gid = await _get_tester_guild_id()
        from app.core.database import db
        now = _now()
        now_iso = _iso(now)
        # Ensure tester has active presence on ambash (idempotent)
        await db.guild_world_presence.update_many(
            {"guild_id": gid, "status": "active"},
            {"$set": {"status": "archived", "archived_at": now_iso}},
        )
        await db.guild_world_presence.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": gid, "continent_slug": "ambash",
            "joined_at": now_iso, "last_changed_at": now_iso,
            "next_change_available_at": _iso(now + timedelta(days=30)),
            "change_count": 0, "status": "active",
            "created_at": now_iso, "updated_at": now_iso,
            "_test_setup": True,
        })
        # Expire any active event on ambash
        await db.continent_event_instances.update_many(
            {"continent_slug": "ambash", "status": "active"},
            {"$set": {"status": "expired", "expired_at": now_iso}},
        )
        # Insert new active boom_commerciale
        await db.continent_event_instances.insert_one({
            "id": str(uuid.uuid4()),
            "continent_slug": "ambash",
            "event_slug": "boom_commerciale",
            "status": "active",
            "starts_at": _iso(now - timedelta(hours=1)),
            "ends_at": _iso(now + timedelta(days=1)),
            "activated_at": now_iso,
            "created_at": now_iso,
        })
        # Delete today's ledger row so it gets recomputed
        day = now.strftime("%Y-%m-%d")
        await db.guild_site_income_ledger.delete_many(
            {"guild_id": gid, "day_bucket": day})
    _run(_setup())
    r = requests.get(f"{API_BASE}/api/site-income/today",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    b = r.json()["breakdown"]
    assert b["event_modifier_pct"] == 15, \
        f"expected +15%, got {b['event_modifier_pct']}"
    assert b["event_bonus"] > 0
