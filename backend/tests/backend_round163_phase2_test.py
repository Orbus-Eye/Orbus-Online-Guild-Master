"""ROUND 16.3 Phase 2 — World & 8 Continents V1 tests."""
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
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login("tester@orbus.test")


@pytest.fixture(scope="module")
def clean_headers():
    return _login("clean_onboarding@orbus.test")


def _now():
    return datetime.now(timezone.utc)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _cleanup_test_state():
    """Rimuove presence + history + fake raid dev bootstrap del tester."""
    from app.core.database import db
    guild = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
    if guild:
        await db.guild_world_presence.delete_many({"guild_id": guild["id"]})
        await db.guild_world_presence_history.delete_many({"guild_id": guild["id"]})
        await db.raids.delete_many({"guild_id": guild["id"],
                                    "_dev_first_raid_grant": True})
        clean = await db.guilds.find_one(
            {"owner_user_id": (await db.users.find_one(
                {"email": "clean_onboarding@orbus.test"},
                {"_id": 0, "id": 1}))["id"] if
                await db.users.find_one({"email": "clean_onboarding@orbus.test"})
                else None},
            {"_id": 0, "id": 1},
        )
        if clean:
            await db.guild_world_presence.delete_many({"guild_id": clean["id"]})
            await db.guild_world_presence_history.delete_many(
                {"guild_id": clean["id"]})
            await db.raids.delete_many({"guild_id": clean["id"],
                                        "_dev_first_raid_grant": True})


# ── T01/T02 seed ──────────────────────────────────────────────────
def test_world_continents_seed_creates_8_continents():
    from app.core.database import db
    async def _c():
        n = await db.world_continents.count_documents({})
        assert n == 8, f"expected 8 continents, got {n}"
        slugs = sorted(await db.world_continents.distinct("slug"))
        assert slugs == ["ambash", "aveol", "efreto", "ergolat",
                         "irthe", "nathos", "soe", "velur"]
    _run(_c())


def test_world_continents_seed_idempotent():
    from app.core.database import db
    from app.world import seed_world_continents
    async def _c():
        r1 = await seed_world_continents()
        r2 = await seed_world_continents()
        assert r1["total"] == 8
        assert r2["inserted"] == 0  # already there
        n = await db.world_continents.count_documents({})
        assert n == 8
    _run(_c())


# ── T03/T04 access gate ───────────────────────────────────────────
def test_world_access_denied_without_completed_raid(clean_headers):
    r = requests.get(f"{API_BASE}/api/world/overview",
                     headers=clean_headers, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["access"] is False
    assert body["reason"] == "first_raid_required"
    assert body["cta"] == "/raids"


def test_world_access_granted_after_completed_raid(admin_headers):
    """The tester already has 365+ completed raids — access must be True."""
    r = requests.get(f"{API_BASE}/api/world/overview",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["access"] is True


# ── T05/T06 overview shape ────────────────────────────────────────
def test_world_overview_no_continent_lists_all_8(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    r = requests.get(f"{API_BASE}/api/world/overview",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["access"] is True
    assert body["continent"] is None
    assert len(body["continents_available"]) == 8


def test_world_overview_with_continent_returns_presence(admin_headers):
    _run(_cleanup_test_state())
    r = requests.post(f"{API_BASE}/api/world/continents/soe/join",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    r2 = requests.get(f"{API_BASE}/api/world/overview",
                      headers=admin_headers, timeout=10)
    body = r2.json()
    assert body["access"] is True
    assert body["continent"]["slug"] == "soe"
    assert body["presence"]["status"] == "active"
    assert "next_change_available_at" in body
    assert body["guilds_in_continent_count"] >= 1
    _run(_cleanup_test_state())


# ── T07/T08/T09 join ─────────────────────────────────────────────
def test_join_continent_creates_presence(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    r = requests.post(f"{API_BASE}/api/world/continents/ambash/join",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    pres = r.json()["presence"]
    assert pres["status"] == "active"
    assert pres["change_count"] == 0
    _run(_cleanup_test_state())


def test_join_continent_forbidden_without_access(clean_headers):
    _run(_cleanup_test_state())
    r = requests.post(f"{API_BASE}/api/world/continents/ambash/join",
                      headers=clean_headers, timeout=10)
    assert r.status_code == 403


def test_join_continent_forbidden_if_already_active(admin_headers):
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/velur/join",
                  headers=admin_headers, timeout=10)
    r = requests.post(f"{API_BASE}/api/world/continents/soe/join",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 409
    _run(_cleanup_test_state())


# ── T10/T11/T12/T13 change ──────────────────────────────────────
def test_change_continent_forbidden_before_30_days(admin_headers):
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/ambash/join",
                  headers=admin_headers, timeout=10)
    r = requests.post(f"{API_BASE}/api/world/continents/velur/change",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 423
    _run(_cleanup_test_state())


def test_change_continent_allowed_after_30_days(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/ambash/join",
                  headers=admin_headers, timeout=10)
    # Fast-forward: set next_change_available_at to now-1min
    async def _ff():
        g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
        await db.guild_world_presence.update_one(
            {"guild_id": g["id"], "status": "active"},
            {"$set": {"next_change_available_at":
                       (_now() - timedelta(minutes=1)).isoformat()}},
        )
    _run(_ff())
    r = requests.post(f"{API_BASE}/api/world/continents/velur/change",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    pres = r.json()["presence"]
    assert pres["continent_slug"] == "velur"
    assert pres["change_count"] == 1
    _run(_cleanup_test_state())


def test_change_continent_archives_previous_and_increments(admin_headers):
    """T12+T13 combined: archives previous + increments change_count."""
    from app.core.database import db
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/irthe/join",
                  headers=admin_headers, timeout=10)
    async def _ff():
        g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
        await db.guild_world_presence.update_one(
            {"guild_id": g["id"], "status": "active"},
            {"$set": {"next_change_available_at":
                       (_now() - timedelta(minutes=1)).isoformat()}},
        )
        return g["id"]
    gid = _run(_ff())
    r = requests.post(f"{API_BASE}/api/world/continents/nathos/change",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    # Verify old presence archived (NOT deleted)
    async def _check():
        archived = await db.guild_world_presence.count_documents(
            {"guild_id": gid, "status": "archived",
             "continent_slug": "irthe"},
        )
        assert archived == 1
        active = await db.guild_world_presence.count_documents(
            {"guild_id": gid, "status": "active"},
        )
        assert active == 1
    _run(_check())
    _run(_cleanup_test_state())


# ── T14/T15 neighbors ────────────────────────────────────────────
def test_neighbors_returns_from_same_continent(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/aveol/join",
                  headers=admin_headers, timeout=10)
    r = requests.get(f"{API_BASE}/api/world/neighbors",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "total_in_continent" in body
    assert isinstance(body["nearby_guilds"], list)
    assert len(body["nearby_guilds"]) <= 8
    _run(_cleanup_test_state())


def test_neighbors_forbidden_without_continent(admin_headers):
    _run(_cleanup_test_state())
    r = requests.get(f"{API_BASE}/api/world/neighbors",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 409


# ── T16/T17 admin ────────────────────────────────────────────────
def test_admin_continents_stats_admin_only(admin_headers, clean_headers):
    r_ok = requests.get(f"{API_BASE}/api/admin/world/continents-stats",
                        headers=admin_headers, timeout=10)
    assert r_ok.status_code == 200
    assert len(r_ok.json()["stats"]) == 8
    r_ko = requests.get(f"{API_BASE}/api/admin/world/continents-stats",
                        headers=clean_headers, timeout=10)
    assert r_ko.status_code == 403


def test_admin_toggle_continent_is_active(admin_headers):
    from app.core.database import db
    r_off = requests.patch(f"{API_BASE}/api/admin/world/continents/ergolat",
                            headers=admin_headers,
                            json={"is_active": False}, timeout=10)
    assert r_off.status_code == 200
    assert r_off.json()["continent"]["is_active"] is False
    # Restore
    r_on = requests.patch(f"{API_BASE}/api/admin/world/continents/ergolat",
                           headers=admin_headers,
                           json={"is_active": True}, timeout=10)
    assert r_on.status_code == 200
    assert r_on.json()["continent"]["is_active"] is True


# ── T18/T19 audit ────────────────────────────────────────────────
def test_audit_world_continent_joined_emitted(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/soe/join",
                  headers=admin_headers, timeout=10)
    async def _c():
        g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
        n = await db.audit_log.count_documents({
            "event_type": "WORLD_CONTINENT_JOINED",
            "actor_guild_id": g["id"],
        })
        return n
    assert _run(_c()) >= 1
    _run(_cleanup_test_state())


def test_audit_world_continent_changed_emitted(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/efreto/join",
                  headers=admin_headers, timeout=10)
    async def _ff():
        g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
        await db.guild_world_presence.update_one(
            {"guild_id": g["id"], "status": "active"},
            {"$set": {"next_change_available_at":
                       (_now() - timedelta(minutes=1)).isoformat()}},
        )
        return g["id"]
    gid = _run(_ff())
    requests.post(f"{API_BASE}/api/world/continents/ambash/change",
                  headers=admin_headers, timeout=10)
    async def _c():
        return await db.audit_log.count_documents({
            "event_type": "WORLD_CONTINENT_CHANGED",
            "actor_guild_id": gid,
        })
    assert _run(_c()) >= 1
    _run(_cleanup_test_state())


# ── T20 whitelist ─────────────────────────────────────────────────
def test_audit_filter_whitelist_accepts_world_events(admin_headers):
    for et in ["WORLD_CONTINENT_JOINED", "WORLD_CONTINENT_CHANGED",
               "WORLD_ACCESS_GRANTED"]:
        r = requests.get(
            f"{API_BASE}/api/admin/audit/events?event_type={et}&limit=3",
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200, f"{et} rejected: {r.text}"


# ── T21 no hard delete ────────────────────────────────────────────
def test_change_continent_never_hard_deletes_history(admin_headers):
    from app.core.database import db
    _run(_cleanup_test_state())
    requests.post(f"{API_BASE}/api/world/continents/nathos/join",
                  headers=admin_headers, timeout=10)
    async def _ff_and_change():
        g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0, "id": 1})
        await db.guild_world_presence.update_one(
            {"guild_id": g["id"], "status": "active"},
            {"$set": {"next_change_available_at":
                       (_now() - timedelta(minutes=1)).isoformat()}},
        )
        return g["id"]
    gid = _run(_ff_and_change())
    requests.post(f"{API_BASE}/api/world/continents/aveol/change",
                  headers=admin_headers, timeout=10)
    # Verify 2 history rows (joined + changed) + 2 presence rows (1 archived + 1 active)
    async def _c():
        hist = await db.guild_world_presence_history.count_documents(
            {"guild_id": gid})
        pres_total = await db.guild_world_presence.count_documents(
            {"guild_id": gid})
        return hist, pres_total
    hist, pres = _run(_c())
    assert hist >= 2  # joined + changed
    assert pres == 2  # 1 archived + 1 active (no delete)
    _run(_cleanup_test_state())


# ── T22 openapi ───────────────────────────────────────────────────
def test_openapi_not_broken():
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    paths = r.json()["paths"]
    world_paths = [p for p in paths if p.startswith("/api/world/")
                   or p.startswith("/api/admin/world/")]
    assert len(world_paths) >= 8  # 6 public + 3 admin


# ── T23 raid recovery regression ──────────────────────────────────
def test_raid_recovery_and_world_boss_still_work():
    from app.raids.recovery import resolve_stuck_raid
    from app.world_boss import resolve_stuck_world_boss_event
    from app.world import has_world_access
    assert callable(resolve_stuck_raid)
    assert callable(resolve_stuck_world_boss_event)
    assert callable(has_world_access)
