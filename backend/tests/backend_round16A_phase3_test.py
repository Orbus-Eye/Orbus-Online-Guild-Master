"""ROUND 16.A Phase 3 — Admin read-only audit dashboard tests.

Validates the 3 endpoints under `/api/admin/audit/*`:
  * trigger-emissions (Phase 1 emissions feed)
  * events (Phase 2 audit_log feed, whitelist-guarded)
  * summary (aggregated KPI)

Plus 2 E2E checks on `tester@orbus.test`.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


def _login(email: str, password: str = "password123"):
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login("tester@orbus.test")


@pytest.fixture(scope="module")
def non_admin_headers():
    # Use the seeded clean_onboarding account — guaranteed non-admin.
    return _login("clean_onboarding@orbus.test")


# ── T01 — Non-admin gets 403 on trigger-emissions ────────────────────
def test_admin_audit_trigger_emissions_requires_admin(non_admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/audit/trigger-emissions",
                     headers=non_admin_headers, timeout=10)
    assert r.status_code == 403, r.text


# ── T02 — Filter by event_name returns only matching rows ────────────
def test_admin_audit_trigger_emissions_filters_by_event_name(admin_headers):
    # Seed at least 1 row via the emitter directly so the filter has something.
    from app.core.database import db
    from app.achievements.trigger_emitter import emit_achievement_trigger

    async def _seed():
        await emit_achievement_trigger(
            db, "test-guild-phase3", "item_crafted",
            {"item_slug": "iron_dagger"},
            idempotency_key=f"r16A-p3-{uuid.uuid4()}",
        )

    asyncio.get_event_loop().run_until_complete(_seed())
    r = requests.get(
        f"{API_BASE}/api/admin/audit/trigger-emissions?event_name=item_crafted",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert all(it["event_name"] == "item_crafted" for it in body["items"])
    assert body["total"] >= 1


# ── T03 — Paginates correctly ────────────────────────────────────────
def test_admin_audit_trigger_emissions_paginates(admin_headers):
    r1 = requests.get(
        f"{API_BASE}/api/admin/audit/trigger-emissions?limit=1&offset=0",
        headers=admin_headers, timeout=10)
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["limit"] == 1
    assert len(b1["items"]) <= 1
    if b1["total"] >= 2:
        r2 = requests.get(
            f"{API_BASE}/api/admin/audit/trigger-emissions?limit=1&offset=1",
            headers=admin_headers, timeout=10)
        assert r2.status_code == 200
        b2 = r2.json()
        if b1["items"] and b2["items"]:
            # Different rows on different offsets.
            assert b1["items"][0].get("idempotency_key") != b2["items"][0].get(
                "idempotency_key")


# ── T04 — Non-admin gets 403 on events ───────────────────────────────
def test_admin_audit_events_requires_admin(non_admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/audit/events",
                     headers=non_admin_headers, timeout=10)
    assert r.status_code == 403


# ── T05 — Non-whitelisted event_type rejected ────────────────────────
def test_admin_audit_events_filters_by_event_type_whitelist(admin_headers):
    r = requests.get(
        f"{API_BASE}/api/admin/audit/events?event_type=item_purchased_admin",
        headers=admin_headers, timeout=10)
    # The endpoint MUST return 400 (or 422) — not leak via the SQL-like
    # filter that would have just returned empty.
    assert r.status_code in (400, 422), r.text


# ── T06 — Date range filter narrows the result set ───────────────────
def test_admin_audit_events_date_range_filter(admin_headers):
    far_future = "2099-12-31T00:00:00+00:00"
    r = requests.get(
        f"{API_BASE}/api/admin/audit/events?from={far_future}",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ── T07 — Summary endpoint returns the expected counter shape ────────
def test_admin_audit_summary_returns_counters(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/audit/summary?window_hours=24",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    s = r.json()
    for k in (
        "window_hours", "achievement_unlocked_count",
        "guild_xp_gained_total_amount", "guild_xp_gained_event_count",
        "guilds_graduated_count", "top_trigger_events",
    ):
        assert k in s, f"summary missing key {k}"
    assert isinstance(s["top_trigger_events"], list)
    assert s["window_hours"] == 24


# ── T08 — `window_hours` is clamped to 720 (30 days) ─────────────────
def test_admin_audit_summary_window_clamped(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/audit/summary?window_hours=99999",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["window_hours"] == 720, (
        f"expected clamp to 720, got {s['window_hours']}")
    assert s.get("window_clamped") is True


# ── T09 — E2E: tester graduation emits onboarding_graduated audit ────
def test_e2e_tester_advanced_emits_onboarding_graduated_once(admin_headers):
    """Reset the graduation flag, hit dashboard twice, verify only one
    audit row is emitted."""
    from app.core.database import db

    async def _reset_and_count():
        guild = await db.guilds.find_one({"name": "The Iron Lantern"})
        gid = guild["id"]
        await db.guilds.update_one(
            {"id": gid}, {"$set": {"onboarding_graduated_at": None}})
        await db.audit_log.delete_many({
            "event_type": "onboarding_graduated",
            "actor_guild_id": gid,
        })
        return gid

    gid = asyncio.get_event_loop().run_until_complete(_reset_and_count())

    # Two consecutive dashboard reads.
    requests.get(f"{API_BASE}/api/dashboard/onboarding",
                 headers=admin_headers, timeout=10)
    requests.get(f"{API_BASE}/api/dashboard/onboarding",
                 headers=admin_headers, timeout=10)

    async def _count_rows():
        return await db.audit_log.count_documents({
            "event_type": "onboarding_graduated",
            "actor_guild_id": gid,
        })

    n = asyncio.get_event_loop().run_until_complete(_count_rows())
    assert n == 1, f"expected exactly 1 audit row, got {n}"


# ── T10 — E2E: new player path triggers no onboarding_graduated ──────
def test_e2e_new_player_full_flow():
    """Login as clean_onboarding (no guild). The audit_log MUST NOT
    contain a graduation event for this user's (non-existent) guild."""
    from app.core.database import db

    h = _login("clean_onboarding@orbus.test")
    r = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                     headers=h, timeout=10)
    assert r.status_code in (200, 404)

    async def _check():
        user = await db.users.find_one(
            {"email": "clean_onboarding@orbus.test"})
        guild = await db.guilds.find_one({"owner_user_id": user["id"]})
        if guild is None:
            return  # pristine — trivially OK
        cnt = await db.audit_log.count_documents({
            "event_type": "onboarding_graduated",
            "actor_guild_id": guild["id"],
        })
        assert cnt == 0, (
            f"clean account should not have graduated; found {cnt} rows")

    asyncio.get_event_loop().run_until_complete(_check())
