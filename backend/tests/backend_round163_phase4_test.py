"""ROUND 16.3 Phase 4 — Continent Resources + Leaderboards V0 tests."""
from __future__ import annotations
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

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


def _now(): return datetime.now(timezone.utc)
def _iso(dt): return dt.isoformat()


async def _cleanup():
    from app.core.database import db
    guild = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
    if guild:
        await db.resource_gathering_missions.delete_many({"guild_id": guild["id"]})
        await db.inventory_items.delete_many(
            {"guild_id": guild["id"], "item_id": {"$regex": ".*"}},
        )
    await db.continent_leaderboard_snapshots.delete_many({})


@pytest.fixture(scope="module", autouse=True)
def _pre_suite():
    from app.resources import seed_resource_catalog, ensure_indexes
    from app.world_events import seed_continent_event_catalog
    from app.site_contracts import seed_site_income_config
    _run(seed_resource_catalog())
    _run(ensure_indexes())
    _run(seed_continent_event_catalog())
    _run(seed_site_income_config())
    # Reset tester to ambash if needed
    from app.scripts.reset_test_account_world_state import _reset
    _run(_reset("tester@orbus.test", "ambash"))
    _run(_cleanup())
    yield
    _run(_cleanup())


async def _get_tester_guild_id():
    from app.core.database import db
    g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                  {"_id": 0, "id": 1})
    return g["id"]


# ── T01-T03 catalog seed
def test_catalog_seed_creates_8_resources():
    from app.core.database import db
    async def _c():
        n = await db.continent_resource_catalog.count_documents({})
        assert n == 8
    _run(_c())


def test_catalog_seed_idempotent():
    from app.resources import seed_resource_catalog
    async def _c():
        r1 = await seed_resource_catalog()
        r2 = await seed_resource_catalog()
        assert r1["total"] == 8
        assert r2["inserted_catalog"] == 0
    _run(_c())


def test_catalog_rarity_distribution():
    from app.core.database import db
    async def _c():
        epic = await db.continent_resource_catalog.count_documents({"rarity": "epic"})
        rare = await db.continent_resource_catalog.count_documents({"rarity": "rare"})
        assert epic == 5 and rare == 3, f"epic={epic} rare={rare}"
    _run(_c())


def test_catalog_is_active_filter():
    r = requests.get(f"{API_BASE}/api/resources/catalog", timeout=10)
    assert r.status_code == 200
    assert len(r.json()["resources"]) == 8


# ── T04-T08 gather + resolve
def test_gather_starts_mission(admin_headers):
    # Get tester's adventurers idle
    from app.core.database import db
    async def _prep():
        gid = await _get_tester_guild_id()
        # Free 3 adventurers
        advs = await db.adventurers.find(
            {"guild_id": gid}, {"_id": 0, "id": 1}
        ).limit(3).to_list(3)
        ids = [a["id"] for a in advs]
        await db.adventurers.update_many(
            {"id": {"$in": ids}},
            {"$set": {"status": "idle", "current_mission_id": None}},
        )
        return ids
    ids = _run(_prep())
    r = requests.post(f"{API_BASE}/api/resources/gather",
                       json={"resource_slug": "cristallo_di_ambash",
                             "adventurer_ids": ids},
                       headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    m = r.json()["mission"]
    assert m["status"] == "in_progress"
    assert m["success_chance"] >= 20
    assert m["drop_rate"] >= 3


def test_gather_locks_adventurers(admin_headers):
    from app.core.database import db
    async def _c():
        gid = await _get_tester_guild_id()
        busy = await db.adventurers.count_documents(
            {"guild_id": gid, "status": "resource_gathering"})
        assert busy == 3
    _run(_c())


def test_gather_cross_continent_rejected(admin_headers):
    from app.core.database import db
    async def _adv():
        gid = await _get_tester_guild_id()
        advs = await db.adventurers.find(
            {"guild_id": gid}, {"_id": 0, "id": 1}).limit(3).to_list(3)
        return [a["id"] for a in advs]
    ids = _run(_adv())
    # velur resource on ambash guild → 400
    r = requests.post(f"{API_BASE}/api/resources/gather",
                       json={"resource_slug": "cenere_di_velur",
                             "adventurer_ids": ids},
                       headers=admin_headers, timeout=10)
    assert r.status_code == 400
    assert "resource_not_in_current_continent" in r.text


def test_resolve_success_grants_resource():
    """Force success roll → grant."""
    from app.core.database import db
    from app.resources import _resolve_mission
    import random
    async def _create():
        gid = await _get_tester_guild_id()
        now = _now()
        m = {"id": str(uuid.uuid4()), "guild_id": gid,
             "continent_slug": "ambash",
             "resource_slug": "cristallo_di_ambash",
             "adventurers": [], "status": "in_progress",
             "started_at": _iso(now - timedelta(hours=1)),
             "completes_at": _iso(now - timedelta(minutes=5)),
             "duration_seconds": 1800, "team_power": 100,
             "success_chance": 100, "drop_rate": 100,
             "resolution_started_at": None,
             "resources_obtained": 0, "outcome": None,
             "created_at": _iso(now)}
        await db.resource_gathering_missions.insert_one(m)
        return m
    m = _run(_create())
    rng = random.Random(42)
    result = _run(_resolve_mission(m, rng=rng))
    assert result["status"] == "completed"
    assert result["resources_obtained"] == 1
    # Verify inventory
    async def _inv():
        gid = await _get_tester_guild_id()
        item = await db.items.find_one({"slug": "cristallo_di_ambash"}, {"_id": 0, "id": 1})
        inv = await db.inventory_items.find_one(
            {"guild_id": gid, "item_id": item["id"]}, {"_id": 0})
        return inv
    inv = _run(_inv())
    assert inv is not None and inv["quantity"] >= 1


def test_resolve_failure_no_drop():
    from app.core.database import db
    from app.resources import _resolve_mission
    import random
    async def _create():
        gid = await _get_tester_guild_id()
        now = _now()
        m = {"id": str(uuid.uuid4()), "guild_id": gid,
             "continent_slug": "ambash",
             "resource_slug": "cristallo_di_ambash",
             "adventurers": [], "status": "in_progress",
             "started_at": _iso(now - timedelta(hours=1)),
             "completes_at": _iso(now - timedelta(minutes=5)),
             "duration_seconds": 1800, "team_power": 20,
             "success_chance": 0, "drop_rate": 0,  # force failure
             "resolution_started_at": None,
             "resources_obtained": 0, "outcome": None,
             "created_at": _iso(now)}
        await db.resource_gathering_missions.insert_one(m)
        return m
    m = _run(_create())
    result = _run(_resolve_mission(m, rng=random.Random(1)))
    assert result["status"] == "failed"
    assert result["resources_obtained"] == 0


# ── T09-T10 idempotent resolve
def test_resolve_idempotent_retry():
    """Second _resolve_mission call on same mission returns current state."""
    from app.core.database import db
    from app.resources import _resolve_mission
    import random
    async def _one():
        gid = await _get_tester_guild_id()
        now = _now()
        m = {"id": str(uuid.uuid4()), "guild_id": gid,
             "continent_slug": "ambash",
             "resource_slug": "cristallo_di_ambash",
             "adventurers": [], "status": "in_progress",
             "started_at": _iso(now), "completes_at": _iso(now),
             "duration_seconds": 1800, "team_power": 100,
             "success_chance": 100, "drop_rate": 100,
             "resolution_started_at": None,
             "resources_obtained": 0, "outcome": None,
             "created_at": _iso(now)}
        await db.resource_gathering_missions.insert_one(m)
        return m
    m = _run(_one())
    r1 = _run(_resolve_mission(m, rng=random.Random(1)))
    q1 = int(r1["resources_obtained"])
    r2 = _run(_resolve_mission(m, rng=random.Random(999)))
    # 2nd call: state persistent, no additional grant
    assert r2["resources_obtained"] == q1


def test_missions_mine_on_visit_expiry(admin_headers):
    """/missions/mine triggers on-visit expiry."""
    from app.core.database import db
    async def _stuck():
        gid = await _get_tester_guild_id()
        now = _now()
        eid = str(uuid.uuid4())
        await db.resource_gathering_missions.insert_one({
            "id": eid, "guild_id": gid, "continent_slug": "ambash",
            "resource_slug": "cristallo_di_ambash", "adventurers": [],
            "status": "in_progress",
            "started_at": _iso(now - timedelta(hours=2)),
            "completes_at": _iso(now - timedelta(minutes=30)),
            "duration_seconds": 1800, "team_power": 60,
            "success_chance": 50, "drop_rate": 5,
            "resolution_started_at": None, "resources_obtained": 0,
            "outcome": None, "created_at": _iso(now)})
        return eid
    eid = _run(_stuck())
    r = requests.get(f"{API_BASE}/api/resources/missions/mine",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    async def _check():
        return await db.resource_gathering_missions.find_one(
            {"id": eid}, {"_id": 0})
    doc = _run(_check())
    assert doc["status"] in ("completed", "failed")


# ── T11 recovery script
def test_recovery_script_resolves_stuck():
    from app.scripts.recover_stuck_resource_missions import _run as sr
    from app.core.database import db
    async def _stuck():
        gid = await _get_tester_guild_id()
        now = _now()
        eid = str(uuid.uuid4())
        await db.resource_gathering_missions.insert_one({
            "id": eid, "guild_id": gid, "continent_slug": "ambash",
            "resource_slug": "cristallo_di_ambash", "adventurers": [],
            "status": "in_progress",
            "started_at": _iso(now - timedelta(hours=2)),
            "completes_at": _iso(now - timedelta(minutes=30)),
            "duration_seconds": 1800, "team_power": 60,
            "success_chance": 50, "drop_rate": 5,
            "resolution_started_at": None, "resources_obtained": 0,
            "outcome": None, "created_at": _iso(now)})
        return eid
    eid = _run(_stuck())
    result = _run(sr(apply=True))
    assert result["resolved"] >= 1


# ── T12 team release
def test_adventurers_released_after_resolve():
    from app.core.database import db
    async def _c():
        gid = await _get_tester_guild_id()
        busy = await db.adventurers.count_documents(
            {"guild_id": gid, "status": "resource_gathering"})
        # After all previous tests resolved, no team should be locked
        assert busy == 0, f"expected 0 locked adventurers, got {busy}"
    _run(_c())


# ── T13 event modifier boost
def test_event_boost_drop_rate():
    from app.resources import _drop_rate_for
    from app.resources import _event_drop_bonus
    # Force active event on ambash
    from app.core.database import db
    async def _setup_boom():
        now = _now()
        await db.continent_event_instances.update_many(
            {"continent_slug": "ambash", "status": "active"},
            {"$set": {"status": "expired", "expired_at": _iso(now)}},
        )
        await db.continent_event_instances.insert_one({
            "id": str(uuid.uuid4()),
            "continent_slug": "ambash",
            "event_slug": "boom_commerciale",
            "status": "active",
            "starts_at": _iso(now - timedelta(hours=1)),
            "ends_at": _iso(now + timedelta(days=1)),
            "activated_at": _iso(now), "created_at": _iso(now),
        })
    _run(_setup_boom())
    bonus = _run(_event_drop_bonus("ambash"))
    assert bonus == 2, f"expected +2 bonus with boom, got {bonus}"
    base = _drop_rate_for("epic")
    assert base + bonus == 5


# ── T14-T15 leaderboards V0
def test_leaderboard_snapshot_computed_on_visit(admin_headers):
    r = requests.get(
        f"{API_BASE}/api/continent-leaderboards/ambash/resource_gathering_count",
        timeout=10)
    assert r.status_code == 200
    snap = r.json()["snapshot"]
    assert snap["continent_slug"] == "ambash"
    assert snap["leaderboard_type"] == "resource_gathering_count"
    assert isinstance(snap["entries"], list)


def test_leaderboard_freshness_reuses_snapshot():
    """Second call within 24h should reuse the same snapshot."""
    r1 = requests.get(
        f"{API_BASE}/api/continent-leaderboards/ambash/resource_gathering_count",
        timeout=10).json()["snapshot"]
    r2 = requests.get(
        f"{API_BASE}/api/continent-leaderboards/ambash/resource_gathering_count",
        timeout=10).json()["snapshot"]
    assert r1["computed_at"] == r2["computed_at"]


def test_leaderboard_top_capped_at_20():
    from app.resources import _compute_leaderboard, LEADERBOARD_TOP_N
    snap = _run(_compute_leaderboard("ambash", "resource_gathering_count"))
    assert len(snap["entries"]) <= LEADERBOARD_TOP_N


def test_leaderboard_admin_recompute(admin_headers):
    r = requests.post(
        f"{API_BASE}/api/admin/continent-leaderboards/ambash/site_income_total/recompute",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["snapshot"]["leaderboard_type"] == "site_income_total"


def test_leaderboard_summary():
    r = requests.get(f"{API_BASE}/api/continent-leaderboards/ambash/summary",
                     timeout=10)
    assert r.status_code == 200
    lb = r.json()["leaderboards"]
    assert "resource_gathering_count" in lb
    assert "site_income_total" in lb


# ── T20 audits
def test_audit_resource_events_emitted():
    from app.core.database import db
    async def _c():
        for et in ["RESOURCE_MISSION_STARTED", "RESOURCE_GRANTED",
                   "LEADERBOARD_SNAPSHOT_COMPUTED"]:
            n = await db.audit_log.count_documents({"event_type": et})
            assert n >= 1, f"no {et} audit rows"
    _run(_c())


# ── T21 whitelist
def test_audit_whitelist_accepts_phase4(admin_headers):
    for et in ["RESOURCE_MISSION_STARTED", "RESOURCE_MISSION_COMPLETED",
               "RESOURCE_MISSION_FAILED", "RESOURCE_GRANTED",
               "LEADERBOARD_SNAPSHOT_COMPUTED"]:
        r = requests.get(f"{API_BASE}/api/admin/audit/events",
                         params={"event_type": et, "limit": 5},
                         headers=admin_headers, timeout=10)
        assert r.status_code == 200, f"{et}: {r.text}"


# ── T22 admin toggle
def test_admin_toggle_resource_no_hard_delete(admin_headers):
    r1 = requests.patch(
        f"{API_BASE}/api/admin/resources/catalog/cristallo_di_ambash",
        json={"is_active": False}, headers=admin_headers, timeout=10)
    assert r1.status_code == 200
    # Public catalog now shows 7 (1 hidden)
    r2 = requests.get(f"{API_BASE}/api/resources/catalog", timeout=10)
    assert len(r2.json()["resources"]) == 7
    # Restore
    r3 = requests.patch(
        f"{API_BASE}/api/admin/resources/catalog/cristallo_di_ambash",
        json={"is_active": True}, headers=admin_headers, timeout=10)
    assert r3.status_code == 200
    from app.core.database import db
    async def _c():
        n = await db.continent_resource_catalog.count_documents({})
        assert n == 8  # no hard delete
    _run(_c())


# ── T23 admin dev grant
def test_admin_dev_grant_gated(admin_headers):
    async def _guild():
        return await _get_tester_guild_id()
    gid = _run(_guild())
    r = requests.post(
        f"{API_BASE}/api/admin/resources/dev/grant/{gid}/osso_di_irthe?qty=2",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["qty"] == 2


# ── T24 admin gathering stats
def test_admin_gathering_stats(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/resources/gathering-stats?window_days=7",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert "groups" in r.json()


# ── T25-T26 regression: previous modules importable
def test_regression_previous_modules_still_importable():
    from app.world_boss import resolve_stuck_world_boss_event
    from app.world import has_world_access
    from app.raids.recovery import resolve_stuck_raid
    from app.world_events import seed_continent_event_catalog
    from app.site_contracts import seed_site_income_config
    assert all(callable(f) for f in [
        resolve_stuck_world_boss_event, has_world_access, resolve_stuck_raid,
        seed_continent_event_catalog, seed_site_income_config])


def test_regression_no_hard_delete_on_missions():
    from app.core.database import db
    async def _c():
        # After all tests, missions must still exist (in various statuses)
        total = await db.resource_gathering_missions.count_documents({})
        assert total >= 3
    _run(_c())


# ── T27 OpenAPI
def test_openapi_has_phase4_paths():
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    paths = r.json()["paths"]
    required = [
        "/api/resources/catalog",
        "/api/resources/mine",
        "/api/resources/gather",
        "/api/resources/missions/mine",
        "/api/resources/missions/{mission_id}",
        "/api/continent-leaderboards/{continent_slug}/summary",
        "/api/continent-leaderboards/{continent_slug}/{ltype}",
        "/api/admin/resources/catalog/{slug}",
        "/api/admin/resources/gathering-stats",
        "/api/admin/resources/dev/grant/{guild_id}/{resource_slug}",
        "/api/admin/continent-leaderboards/{continent_slug}/{ltype}/recompute",
    ]
    for p in required:
        assert p in paths, f"missing {p}"


# ── T28 formulas
def test_success_chance_formula():
    from app.resources import _success_chance
    assert _success_chance(60) == 50
    assert _success_chance(0) == 20  # capped
    assert _success_chance(200) == 90  # capped


# ── T29 non-admin blocked from admin endpoints
def test_non_admin_blocked(clean_headers):
    for path in [
        "/api/admin/resources/gathering-stats",
        "/api/admin/resources/dev/grant/xxx/cristallo_di_ambash",
    ]:
        method = "post" if "/grant/" in path else "get"
        r = getattr(requests, method)(f"{API_BASE}{path}",
                                       headers=clean_headers, timeout=10)
        assert r.status_code == 403, f"{path}: expected 403, got {r.status_code}"


# ── T30 gather insufficient adventurers
def test_gather_insufficient_adventurers_400(admin_headers):
    r = requests.post(f"{API_BASE}/api/resources/gather",
                       json={"resource_slug": "cristallo_di_ambash",
                             "adventurer_ids": ["a", "b"]},  # only 2
                       headers=admin_headers, timeout=10)
    assert r.status_code == 422  # pydantic validation min_length=3
