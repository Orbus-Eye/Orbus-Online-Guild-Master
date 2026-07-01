"""ROUND 16.3 Phase 6 — Trade Pacts + Guild Specialization backend tests.

33+ tests covering seed catalog, cross-continent block, max_3 pacts,
cooldown 7gg unilateral dissolve, specialization gate lvl 8 + free
first choice + reset cost/cooldown 30gg, 8 audit events, admin +
whitelist ≥41.
"""
from __future__ import annotations
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


def _now(): return datetime.now(timezone.utc)
def _iso(dt): return dt.isoformat()
def _run(coro): return asyncio.get_event_loop().run_until_complete(coro)


def _login(email, password="password123"):
    r = requests.post(f"{API_BASE}/api/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# Dedicated Phase 6 players (isolated) — bootstrap on module load
_P6 = {"a": None, "b": None, "cross": None}


def _register(email_prefix, guild_prefix, continent_slug=None):
    email = f"phase6_{email_prefix}_{uuid.uuid4().hex[:8]}@orbus.test"
    r = requests.post(f"{API_BASE}/api/auth/register", json={
        "email": email,
        "username": f"phase6_{email_prefix}_{uuid.uuid4().hex[:6]}",
        "password": "password123"}, timeout=10)
    assert r.status_code in (200, 201), f"register {email}: {r.text}"
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    gname = f"{guild_prefix}_{uuid.uuid4().hex[:5]}"
    rg = requests.post(f"{API_BASE}/api/guilds",
                        json={"name": gname, "description": "phase6"},
                        headers=h, timeout=10)
    assert rg.status_code in (200, 201), f"guild {gname}: {rg.text}"
    gid = (rg.json().get("guild") or rg.json()).get("id")

    async def _presence():
        from app.core.database import db
        if not continent_slug:
            return
        # Inject an active presence directly for testing
        await db.guild_world_presence.update_one(
            {"guild_id": gid},
            {"$set": {"guild_id": gid,
                      "continent_slug": continent_slug,
                      "status": "active",
                      "updated_at": _iso(_now())},
             "$setOnInsert": {"id": str(uuid.uuid4()),
                              "created_at": _iso(_now())}},
            upsert=True)
    _run(_presence())
    return {"email": email, "token": token, "headers": h,
             "guild_id": gid, "guild_name": gname}


def _bootstrap():
    if _P6["a"]:
        return
    _P6["a"] = _register("a", "PactA", "ambash")
    _P6["b"] = _register("b", "PactB", "ambash")
    _P6["cross"] = _register("cross", "CrossX", "irthe")


@pytest.fixture(scope="module")
def admin_headers():
    return _login("tester@orbus.test")


@pytest.fixture(scope="module", autouse=True)
def _seed():
    from app.guild_specialization import seed_guild_specialization_catalog, ensure_indexes
    from app.trade_pacts import ensure_indexes as ep
    _run(seed_guild_specialization_catalog())
    _run(ensure_indexes())
    _run(ep())
    _bootstrap()
    yield


async def _clear_pacts():
    from app.core.database import db
    await db.guild_trade_pacts.delete_many({})


# ── T01-T04 seed ──────────────────────────────────────────────────────
def test_t01_specialization_catalog_seeded_6():
    async def _c():
        from app.core.database import db
        n = await db.guild_specialization_catalog.count_documents({})
        assert n == 6, f"expected 6 specializations, got {n}"
    _run(_c())


def test_t02_specialization_seed_idempotent():
    from app.guild_specialization import seed_guild_specialization_catalog
    a = _run(seed_guild_specialization_catalog())
    b = _run(seed_guild_specialization_catalog())
    assert a["total"] == 6 and b["total"] == 6


def test_t03_all_specialization_slugs_unique():
    async def _c():
        from app.core.database import db
        docs = await db.guild_specialization_catalog.find({}, {"_id": 0, "slug": 1}).to_list(20)
        slugs = [d["slug"] for d in docs]
        assert len(slugs) == len(set(slugs))
    _run(_c())


def test_t04_catalog_endpoint_returns_6():
    r = requests.get(f"{API_BASE}/api/guild-specialization/catalog",
                      headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200
    assert len(r.json()["specializations"]) == 6


# ── T05-T08 trade pact request flow ─────────────────────────────────
def test_t05_request_pact_same_continent_ok():
    _run(_clear_pacts())
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200, r.text
    assert r.json()["pact"]["status"] == "pending_request"
    assert r.json()["pact"]["continent_slug"] == "ambash"


def test_t06_request_self_400():
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['a']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 400
    assert "cannot_request_self" in r.text


def test_t07_cross_continent_blocked():
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['cross']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 400
    assert "cross_continent_block" in r.text


def test_t08_duplicate_request_409():
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 409


# ── T09-T13 accept/reject/dissolve/cooldown ─────────────────────────
def test_t09_accept_pact():
    r_recv = requests.get(f"{API_BASE}/api/trade-pacts/received",
                           headers=_P6["b"]["headers"], timeout=10)
    assert r_recv.status_code == 200
    pact_id = r_recv.json()["pacts"][0]["id"]
    r = requests.post(f"{API_BASE}/api/trade-pacts/{pact_id}/accept",
                       headers=_P6["b"]["headers"], timeout=10)
    assert r.status_code == 200
    assert r.json()["pact"]["status"] == "accepted"
    assert r.json()["pact"]["activated_at"] is not None


def test_t10_partners_shows_active():
    r = requests.get(f"{API_BASE}/api/trade-pacts/partners",
                      headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["partners"][0]["guild_id"] == _P6["b"]["guild_id"]


def test_t11_dissolve_unilateral_starts_cooldown():
    r_mine = requests.get(f"{API_BASE}/api/trade-pacts/mine",
                            headers=_P6["a"]["headers"], timeout=10)
    pact_id = r_mine.json()["pacts"][0]["id"]
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/{pact_id}/dissolve?reason=unilateral",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200
    body = r.json()["pact"]
    assert body["status"] == "dissolved"
    assert body["dissolution_reason"] == "unilateral"
    assert body["cooldown_ends_at"] is not None


def test_t12_cooldown_blocks_new_request():
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 409
    assert "cooldown_active" in r.text


def test_t13_reject_pact_flow():
    # Clear + create new pact + reject it
    _run(_clear_pacts())
    r_req = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    pact_id = r_req.json()["pact"]["id"]
    r = requests.post(f"{API_BASE}/api/trade-pacts/{pact_id}/reject",
                       headers=_P6["b"]["headers"], timeout=10)
    assert r.status_code == 200
    assert r.json()["pact"]["status"] == "rejected"


def test_t14_mutual_dissolve_no_cooldown():
    _run(_clear_pacts())
    r_req = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    pact_id = r_req.json()["pact"]["id"]
    requests.post(f"{API_BASE}/api/trade-pacts/{pact_id}/accept",
                    headers=_P6["b"]["headers"], timeout=10)
    r = requests.post(
        f"{API_BASE}/api/trade-pacts/{pact_id}/dissolve?reason=mutual",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200
    assert r.json()["pact"]["cooldown_ends_at"] is None


# ── T15-T16 max 3 accepted ─────────────────────────────────────────
def test_t15_max_3_accepted_enforcement():
    """Simulate 3 accepted pacts for guild A + attempt 4th → 409."""
    async def _c():
        from app.core.database import db
        await db.guild_trade_pacts.delete_many({})
        # Insert 3 fake accepted pacts for A
        for i in range(3):
            await db.guild_trade_pacts.insert_one({
                "id": str(uuid.uuid4()),
                "guild_a_id": _P6["a"]["guild_id"],
                "guild_b_id": f"fake_partner_{i}",
                "status": "accepted",
                "requested_at": _iso(_now()),
                "responded_at": _iso(_now()),
                "activated_at": _iso(_now()),
                "continent_slug": "ambash",
                "created_at": _iso(_now())})
    _run(_c())
    # A requests to B → B tries to accept → 409 (A has 3 already but here
    # B is target; the check is on the acceptor's side). We simulate
    # attaching 3 accepted to B instead.
    async def _cB():
        from app.core.database import db
        await db.guild_trade_pacts.delete_many({})
        for i in range(3):
            await db.guild_trade_pacts.insert_one({
                "id": str(uuid.uuid4()),
                "guild_a_id": f"fake_partner_{i}",
                "guild_b_id": _P6["b"]["guild_id"],
                "status": "accepted",
                "requested_at": _iso(_now()),
                "activated_at": _iso(_now()),
                "continent_slug": "ambash",
                "created_at": _iso(_now())})
    _run(_cB())
    r_req = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    assert r_req.status_code == 200
    pact_id = r_req.json()["pact"]["id"]
    r = requests.post(f"{API_BASE}/api/trade-pacts/{pact_id}/accept",
                       headers=_P6["b"]["headers"], timeout=10)
    assert r.status_code == 409
    assert "max_accepted_pacts_reached" in r.text


# ── T17-T21 specialization flow ────────────────────────────────────
def test_t17_spec_choose_gated_at_lvl_8():
    # A's guild is level 1 by default
    r = requests.post(
        f"{API_BASE}/api/guild-specialization/choose/incursion",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 403
    assert "guild_level_below_required" in r.text


async def _set_guild_props(gid, level=None, gold=None):
    from app.core.database import db
    upd = {}
    if level is not None: upd["level"] = level
    if gold is not None: upd["gold"] = gold
    if upd:
        await db.guilds.update_one({"id": gid}, {"$set": upd})


def test_t18_spec_choose_first_choice_free():
    _run(_set_guild_props(_P6["a"]["guild_id"], level=9))
    r = requests.post(
        f"{API_BASE}/api/guild-specialization/choose/incursion",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200, r.text
    assert r.json()["choice"]["specialization_slug"] == "incursion"


def test_t19_spec_mine_returns_active():
    r = requests.get(f"{API_BASE}/api/guild-specialization/mine",
                      headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["active_choice"]["specialization_slug"] == "incursion"
    assert body["reset_cost_gold"] == 200000


def test_t20_spec_second_choice_blocked_without_reset():
    r = requests.post(
        f"{API_BASE}/api/guild-specialization/choose/merchant",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 409
    assert "already_has_active_choice" in r.text


def test_t21_spec_reset_requires_gold_and_material():
    # Attempt reset without gold/material → 402
    _run(_set_guild_props(_P6["a"]["guild_id"], level=9, gold=100))
    r = requests.post(
        f"{API_BASE}/api/guild-specialization/reset/merchant",
        headers=_P6["a"]["headers"], timeout=10)
    # Cooldown active first (chosen just now, 30gg)
    assert r.status_code in (402, 409)
    if r.status_code == 409:
        assert "reset_cooldown_active" in r.text


def test_t22_spec_reset_success_bypass_cooldown():
    """Bypass cooldown via direct DB update, then reset with proper funds."""
    async def _prep():
        from app.core.database import db
        past = _iso(_now() - timedelta(days=1))
        await db.guild_specialization_choice.update_one(
            {"guild_id": _P6["a"]["guild_id"], "status": "active"},
            {"$set": {"next_reset_available_at": past}})
        # Grant gold
        await db.guilds.update_one(
            {"id": _P6["a"]["guild_id"]},
            {"$set": {"gold": 300000}})
        # Grant frammento_di_ergolat × 3
        it = await db.items.find_one({"slug": "frammento_di_ergolat"},
                                        {"_id": 0, "id": 1})
        await db.inventory_items.update_one(
            {"guild_id": _P6["a"]["guild_id"], "item_id": it["id"]},
            {"$setOnInsert": {"id": str(uuid.uuid4()),
                                "guild_id": _P6["a"]["guild_id"],
                                "item_id": it["id"],
                                "created_at": _iso(_now())},
             "$inc": {"quantity": 5}},
            upsert=True)
    _run(_prep())
    r = requests.post(
        f"{API_BASE}/api/guild-specialization/reset/merchant",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 200, r.text
    assert r.json()["choice"]["specialization_slug"] == "merchant"
    assert r.json()["choice"]["reset_count"] == 1

    async def _verify_gold():
        from app.core.database import db
        g = await db.guilds.find_one({"id": _P6["a"]["guild_id"]},
                                       {"_id": 0, "gold": 1})
        assert g["gold"] == 100000  # 300k - 200k
    _run(_verify_gold())


def test_t23_spec_reset_insufficient_gold_402():
    """Guild with no gold cannot reset."""
    async def _prep():
        from app.core.database import db
        past = _iso(_now() - timedelta(days=1))
        await db.guild_specialization_choice.update_one(
            {"guild_id": _P6["a"]["guild_id"], "status": "active"},
            {"$set": {"next_reset_available_at": past}})
        await db.guilds.update_one(
            {"id": _P6["a"]["guild_id"]},
            {"$set": {"gold": 100}})
    _run(_prep())
    r = requests.post(
        f"{API_BASE}/api/guild-specialization/reset/exploration",
        headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 402


# ── T24-T27 audit events ────────────────────────────────────────────
def test_t24_audit_trade_pact_requested_emitted():
    async def _c():
        from app.core.database import db
        n = await db.audit_log.count_documents(
            {"event_type": "TRADE_PACT_REQUESTED"})
        assert n >= 1
    _run(_c())


def test_t25_audit_trade_pact_accepted_dissolved():
    async def _c():
        from app.core.database import db
        for ev in ("TRADE_PACT_ACCEPTED", "TRADE_PACT_DISSOLVED",
                     "TRADE_PACT_REJECTED"):
            n = await db.audit_log.count_documents({"event_type": ev})
            assert n >= 1, f"missing {ev}"
    _run(_c())


def test_t26_audit_specialization_chosen_reset():
    async def _c():
        from app.core.database import db
        for ev in ("GUILD_SPECIALIZATION_CHOSEN",
                     "GUILD_SPECIALIZATION_RESET"):
            n = await db.audit_log.count_documents({"event_type": ev})
            assert n >= 1, f"missing {ev}"
    _run(_c())


def test_t27_audit_whitelist_contains_8_new_events():
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    for ev in ("TRADE_PACT_REQUESTED", "TRADE_PACT_ACCEPTED",
                 "TRADE_PACT_REJECTED", "TRADE_PACT_DISSOLVED",
                 "TRADE_PACT_FORCE_DISSOLVED",
                 "GUILD_SPECIALIZATION_CHOSEN",
                 "GUILD_SPECIALIZATION_RESET",
                 "GUILD_SPECIALIZATION_CATALOG_TOGGLED"):
        assert ev in AUDIT_EVENT_WHITELIST, f"missing: {ev}"
    # 33 baseline + 8 phase 6 = 41
    assert len(AUDIT_EVENT_WHITELIST) >= 41


# ── T28-T30 admin routes ────────────────────────────────────────────
def test_t28_admin_stats_trade_pacts(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/trade-pacts/stats",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert "by_status" in r.json()


def test_t29_admin_stats_specialization(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/guild-specialization/stats",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "distribution" in body
    assert body["total_active"] >= 1


def test_t30_admin_patch_catalog_toggle(admin_headers):
    r = requests.patch(
        f"{API_BASE}/api/admin/guild-specialization/catalog/military"
        f"?is_active=false",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["is_active"] is False
    # revert
    requests.patch(
        f"{API_BASE}/api/admin/guild-specialization/catalog/military"
        f"?is_active=true",
        headers=admin_headers, timeout=10)


def test_t31_admin_force_dissolve(admin_headers):
    _run(_clear_pacts())
    # Create pact + accept + force dissolve
    r_req = requests.post(
        f"{API_BASE}/api/trade-pacts/request/{_P6['b']['guild_id']}",
        headers=_P6["a"]["headers"], timeout=10)
    pact_id = r_req.json()["pact"]["id"]
    requests.post(f"{API_BASE}/api/trade-pacts/{pact_id}/accept",
                    headers=_P6["b"]["headers"], timeout=10)
    r = requests.post(
        f"{API_BASE}/api/admin/trade-pacts/{pact_id}/force-dissolve",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["pact"]["status"] == "dissolved"
    assert r.json()["pact"]["dissolution_reason"] == "admin_force"


def test_t32_non_admin_gets_403():
    r = requests.get(f"{API_BASE}/api/admin/trade-pacts/stats",
                      headers=_P6["a"]["headers"], timeout=10)
    assert r.status_code == 403


# ── T33-T35 no-hard-delete + OpenAPI + meta ────────────────────────
def test_t33_no_hard_delete_archived_choices_preserved():
    async def _c():
        from app.core.database import db
        n = await db.guild_specialization_choice.count_documents(
            {"guild_id": _P6["a"]["guild_id"], "status": "archived"})
        assert n >= 1  # from t22 reset
    _run(_c())


def test_t34_openapi_has_15_new_endpoints():
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    paths = list(r.json().get("paths", {}).keys())
    p6 = [p for p in paths if "trade-pacts" in p or "guild-specialization" in p]
    assert len(p6) == 15, f"expected 15 Phase 6 endpoints, got {p6}"


def test_t35_regression_arfus_5b_still_intact():
    """Ensure Phase 5B routes still present (no accidental route stealing)."""
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    paths = list(r.json().get("paths", {}).keys())
    arfus = [p for p in paths if "arfus" in p]
    assert len(arfus) == 9, f"arfus routes broken: {arfus}"
