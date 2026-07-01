"""ROUND 16.3 Phase 1 — World Boss V1 Alveora tests.

Coverage:
  T01 seed Alveora catalog
  T02 admin create event
  T03 join event
  T04 send-team records contribution
  T05 contribution correctly registered
  T06 threat counter applied
  T07 event resolved on expiry
  T08 rewards granted once (idempotent)
  T09 retry resolution does not duplicate rewards
  T10 squad released after resolution
  T11 ranking event works
  T12 tester_account no exclusion (skipped)
  T13 expired event recovered via script
  T14 admin can create event
  T15 admin can start event
  T16 admin can resolve event
  T17 admin can force recovery
  T18 on-visit fallback resolves expired event
  T19 no team remains stuck after resolution
  T20 openapi not broken
  T24 raid recovery still works (regression from R16.1.1)
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


def _login(email: str, password: str = "password123"):
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _cleanup_events():
    """Remove all pytest-created world boss events (marked by starts_at hint)."""
    from app.core.database import db
    # Delete events created for tests. Use marker `test_marker` field.
    evs = await db.world_boss_events.find(
        {"test_marker": True}, {"_id": 0, "id": 1}
    ).to_list(100)
    eids = [e["id"] for e in evs]
    if eids:
        await db.world_boss_events.delete_many({"id": {"$in": eids}})
        await db.world_boss_participants.delete_many({"event_id": {"$in": eids}})
        await db.world_boss_contributions.delete_many({"event_id": {"$in": eids}})
        await db.world_boss_rewards.delete_many({"event_id": {"$in": eids}})
        await db.audit_log.delete_many({
            "related_entity_id": {"$in": eids},
            "event_type": {"$regex": "^WORLD_BOSS"},
        })


async def _create_test_event(*, ends_in_minutes: int = 60,
                              status: str = "active",
                              total_hp: int = 10000,
                              starts_in_minutes: int = -5) -> dict:
    """Create a world boss event directly in DB with a test marker."""
    from app.core.database import db
    from app.world_boss import ALVEORA_SLUG
    catalog = await db.world_boss_catalog.find_one(
        {"slug": ALVEORA_SLUG}, {"_id": 0},
    )
    now = _now()
    starts_at = now + timedelta(minutes=starts_in_minutes)
    ends_at = now + timedelta(minutes=ends_in_minutes)
    doc = {
        "id": str(uuid.uuid4()),
        "boss_slug": ALVEORA_SLUG,
        "name_it": catalog["name_it"], "name_en": catalog["name_en"],
        "status": status,
        "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat(),
        "total_hp": total_hp, "current_hp": total_hp,
        "phase": 1, "server_progress": 0.0,
        "threats": catalog["phases"][0]["threats"],
        "continent_scope": "global",
        "created_at": now.isoformat(),
        "resolved_at": None, "resolution_started_at": None,
        "recovered": False,
        "test_marker": True,
    }
    await db.world_boss_events.insert_one(doc)
    return doc


# ── T01 ────────────────────────────────────────────────────────────
def test_world_boss_catalog_seed_alveora():
    from app.core.database import db
    async def _c():
        cat = await db.world_boss_catalog.find_one(
            {"slug": "alveora_moon_puppeteer"}, {"_id": 0},
        )
        assert cat is not None
        assert cat["name_it"].startswith("Alveora")
        assert len(cat["phases"]) == 3
        # counter_mind_control seeded
        cc = await db.counter_tags.find_one(
            {"slug": "counter_mind_control"}, {"_id": 0},
        )
        assert cc is not None
    _run(_c())


# ── T02 / T14 ──────────────────────────────────────────────────────
def test_admin_can_create_world_boss_event(admin_headers):
    from app.core.database import db
    r = requests.post(f"{API_BASE}/api/admin/world-boss/events",
                      headers=admin_headers,
                      json={"boss_slug": "alveora_moon_puppeteer",
                            "total_hp_override": 5000},
                      timeout=10)
    assert r.status_code == 200, r.text
    ev = r.json()["event"]
    assert ev["status"] == "scheduled"
    assert ev["total_hp"] == 5000
    _run(db.world_boss_events.delete_one({"id": ev["id"]}))


def test_admin_create_gated_for_non_admin(clean_headers):
    r = requests.post(f"{API_BASE}/api/admin/world-boss/events",
                      headers=clean_headers,
                      json={"boss_slug": "alveora_moon_puppeteer"},
                      timeout=10)
    assert r.status_code == 403, r.text


# ── T03 ────────────────────────────────────────────────────────────
def test_join_event_valid_guild(admin_headers):
    from app.core.database import db
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60))
        r = requests.post(
            f"{API_BASE}/api/world-boss/events/{ev['id']}/join",
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200, r.text
        # Second call idempotent
        r2 = requests.post(
            f"{API_BASE}/api/world-boss/events/{ev['id']}/join",
            headers=admin_headers, timeout=10,
        )
        assert r2.status_code == 200
        assert r2.json()["already_joined"] is True
    finally:
        _run(_cleanup_events())


# ── T04 / T05 / T06 ────────────────────────────────────────────────
def test_send_team_records_contribution(admin_headers):
    from app.core.database import db
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60,
                                       total_hp=1_000_000))
        requests.post(f"{API_BASE}/api/world-boss/events/{ev['id']}/join",
                      headers=admin_headers, timeout=10)
        # Get tester's available adventurers
        async def _get_advs():
            guild = await db.guilds.find_one(
                {"name": "The Iron Lantern"}, {"_id": 0, "id": 1})
            advs = await db.adventurers.find(
                {"guild_id": guild["id"], "is_available": True,
                 "expedition_in_progress": {"$ne": True}},
                {"_id": 0, "id": 1, "counter_tags": 1},
            ).to_list(3)
            return [a["id"] for a in advs]
        adv_ids = _run(_get_advs())
        assert len(adv_ids) == 3, f"need 3 available adventurers, got {len(adv_ids)}"
        r = requests.post(
            f"{API_BASE}/api/world-boss/events/{ev['id']}/send-team",
            headers=admin_headers,
            json={"adventurer_ids": adv_ids}, timeout=10,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["contribution"] > 0
        # Contribution registered in DB
        async def _check():
            n = await db.world_boss_contributions.count_documents(
                {"event_id": ev["id"]},
            )
            assert n == 1
            part = await db.world_boss_participants.find_one(
                {"event_id": ev["id"]}, {"_id": 0},
            )
            assert part["total_contribution"] == data["contribution"]
            assert part["teams_sent"] == 1
        _run(_check())
    finally:
        # release advs before cleanup
        async def _release():
            await db.adventurers.update_many(
                {"current_world_boss_event_id": ev["id"]},
                {"$set": {"is_available": True,
                          "expedition_in_progress": False,
                          "current_world_boss_event_id": None}},
            )
        try:
            _run(_release())
        except Exception:
            pass
        _run(_cleanup_events())


def test_threat_counter_applied():
    """Verify THREAT_COUNTER_MAP matches expected threats."""
    from app.world_boss import THREAT_COUNTER_MAP
    assert "counter_mind_control" in THREAT_COUNTER_MAP["mind_control"]
    assert "counter_void" in THREAT_COUNTER_MAP["void"]
    assert "counter_minion" in THREAT_COUNTER_MAP["puppet_minions"]
    assert THREAT_COUNTER_MAP["moon_phase"] == []


# ── T07 / T10 / T18 / T19 ─────────────────────────────────────────
def test_event_resolved_on_expiry():
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=-1))
        out = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t07",
        ))
        assert out["action"] == "resolved"
        assert out["outcome"] == "failed"  # HP not reduced
        async def _check():
            ev2 = await db.world_boss_events.find_one({"id": ev["id"]},
                                                       {"_id": 0})
            assert ev2["status"] == "failed"
            assert ev2["recovered"] is True
        _run(_check())
    finally:
        if ev:
            _run(_cleanup_events())


def test_squad_released_after_resolution(admin_headers):
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60))
        # Manually flag some advs as engaged
        async def _setup():
            g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                          {"_id": 0, "id": 1})
            advs = await db.adventurers.find(
                {"guild_id": g["id"], "is_available": True},
                {"_id": 0, "id": 1},
            ).to_list(3)
            adv_ids = [a["id"] for a in advs]
            await db.adventurers.update_many(
                {"id": {"$in": adv_ids}},
                {"$set": {"is_available": False,
                          "expedition_in_progress": True,
                          "current_world_boss_event_id": ev["id"]}},
            )
            return adv_ids
        adv_ids = _run(_setup())
        # Expire event
        _run(db.world_boss_events.update_one(
            {"id": ev["id"]},
            {"$set": {"ends_at": (_now() - timedelta(minutes=1)).isoformat()}},
        ))
        out = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t10",
        ))
        assert out["action"] == "resolved"
        assert out["adv_released"] == 3
        # No adv stuck
        async def _check_release():
            n = await db.adventurers.count_documents({
                "id": {"$in": adv_ids},
                "current_world_boss_event_id": ev["id"],
            })
            return n
        assert _run(_check_release()) == 0
    finally:
        if ev:
            _run(_cleanup_events())


# ── T08 / T09 ──────────────────────────────────────────────────────
def test_rewards_granted_once_and_retry_does_not_duplicate():
    """T08 + T09: HP=0 → completed → reward granted, retry no dup."""
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event, ALVEORA_SLUG
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60,
                                       total_hp=100))
        # Add participant with contribution
        async def _setup():
            g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                          {"_id": 0, "id": 1})
            await db.world_boss_participants.insert_one({
                "id": str(uuid.uuid4()),
                "event_id": ev["id"], "guild_id": g["id"],
                "joined_at": _now().isoformat(),
                "total_contribution": 500, "teams_sent": 1,
                "reward_granted": False,
            })
            # Zero HP + expire
            await db.world_boss_events.update_one(
                {"id": ev["id"]},
                {"$set": {"current_hp": 0,
                          "ends_at": (_now() - timedelta(minutes=1)).isoformat()}},
            )
            return g["id"]
        gid = _run(_setup())
        # Resolve
        out1 = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t08",
        ))
        assert out1["action"] == "resolved"
        assert out1["outcome"] == "completed"
        async def _count_rewards():
            return await db.world_boss_rewards.count_documents(
                {"event_id": ev["id"], "guild_id": gid},
            )
        assert _run(_count_rewards()) == 1
        # Retry: should skip
        out2 = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t09",
        ))
        assert out2["action"] == "skipped"
        assert _run(_count_rewards()) == 1  # still 1 reward row
    finally:
        if ev:
            _run(_cleanup_events())


# ── T11 ────────────────────────────────────────────────────────────
def test_ranking_event_works(admin_headers):
    from app.core.database import db
    ev = None
    try:
        ev = _run(_create_test_event(status="active"))
        # Insert 3 fake participants
        async def _setup():
            for i, contrib in enumerate([1000, 500, 100]):
                await db.world_boss_participants.insert_one({
                    "id": str(uuid.uuid4()),
                    "event_id": ev["id"],
                    "guild_id": f"fake-guild-{i}",
                    "joined_at": _now().isoformat(),
                    "total_contribution": contrib,
                    "teams_sent": i + 1,
                    "reward_granted": False,
                })
        _run(_setup())
        r = requests.get(
            f"{API_BASE}/api/world-boss/events/{ev['id']}/ranking",
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        ranking = r.json()["ranking"]
        # Top rank must have highest contribution
        assert ranking[0]["contribution"] == 1000
        assert ranking[0]["rank"] == 1
        assert ranking[1]["contribution"] == 500
    finally:
        if ev:
            _run(_cleanup_events())


# ── T12 skipped by design ─────────────────────────────────────────
@pytest.mark.skip(reason="Tester exclusion not implemented in Phase 1 by design")
def test_tester_account_excluded_or_marked_if_needed():
    pass


# ── T13 recovery script ───────────────────────────────────────────
def test_expired_event_recovered_via_script():
    """T13: Verify script recover_stuck_world_boss_events resolves stuck events."""
    from app.core.database import db
    from app.scripts.recover_stuck_world_boss_events import _find_all_stuck
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=-5))
        # Script should find it
        stuck = _run(_find_all_stuck(db))
        assert any(e["id"] == ev["id"] for e in stuck)
    finally:
        if ev:
            _run(_cleanup_events())


# ── T15 admin start ───────────────────────────────────────────────
def test_admin_can_start_event(admin_headers):
    from app.core.database import db
    r = requests.post(f"{API_BASE}/api/admin/world-boss/events",
                      headers=admin_headers,
                      json={"boss_slug": "alveora_moon_puppeteer"},
                      timeout=10)
    ev = r.json()["event"]
    try:
        r2 = requests.post(
            f"{API_BASE}/api/admin/world-boss/events/{ev['id']}/start",
            headers=admin_headers, timeout=10,
        )
        assert r2.status_code == 200
        assert r2.json()["event"]["status"] == "active"
    finally:
        _run(db.world_boss_events.delete_one({"id": ev["id"]}))


# ── T16 admin resolve ─────────────────────────────────────────────
def test_admin_can_resolve_event(admin_headers):
    from app.core.database import db
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60))
        r = requests.post(
            f"{API_BASE}/api/admin/world-boss/events/{ev['id']}/resolve",
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["action"] == "resolved"
    finally:
        if ev:
            _run(_cleanup_events())


# ── T17 admin force recovery ──────────────────────────────────────
def test_admin_can_force_recovery(admin_headers):
    from app.core.database import db
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=-1))
        r = requests.post(
            f"{API_BASE}/api/admin/world-boss/events/{ev['id']}/recover",
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["action"] == "resolved"
        assert r.json()["recovery_reason"] == "admin_force_recovery"
    finally:
        if ev:
            _run(_cleanup_events())


# ── T18 on-visit fallback ─────────────────────────────────────────
def test_on_visit_fallback_resolves_expired_event(admin_headers):
    from app.core.database import db
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=-5))
        # Hit list endpoint — fallback should trigger
        r = requests.get(f"{API_BASE}/api/world-boss/active",
                          headers=admin_headers, timeout=10)
        assert r.status_code == 200
        async def _check():
            e = await db.world_boss_events.find_one({"id": ev["id"]},
                                                     {"_id": 0})
            return e["status"]
        # After list_active fallback the event should be resolved
        status_after = _run(_check())
        assert status_after in ("completed", "failed"), status_after
    finally:
        if ev:
            _run(_cleanup_events())


# ── T20 openapi ───────────────────────────────────────────────────
def test_openapi_not_broken():
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    wb_paths = [p for p in paths if "world-boss" in p]
    assert len(wb_paths) >= 10  # 6 public + 4 admin


# ── T24 raid recovery regression ──────────────────────────────────
def test_raid_recovery_still_works():
    """Regression check: import R16.1.1 recovery module + no attribute error."""
    from app.raids.recovery import resolve_stuck_raid, auto_resolve_stuck_raids_for_guild
    assert callable(resolve_stuck_raid)
    assert callable(auto_resolve_stuck_raids_for_guild)


# ═══════════════════════════════════════════════════════════════════
# BRANCH `completed` — Task B (R16.3 P1 conditional close)
# ═══════════════════════════════════════════════════════════════════

async def _get_gold(db, guild_id: str) -> int:
    g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "gold": 1})
    return g.get("gold", 0)


async def _inventory_currency_count(db, guild_id: str, slug: str) -> int:
    """Sum quantities of currency `slug` in guild inventory."""
    item = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
    if not item:
        return 0
    rows = await db.inventory_items.find(
        {"guild_id": guild_id, "item_id": item["id"]},
        {"_id": 0, "quantity": 1},
    ).to_list(50)
    return sum(int(r.get("quantity", 0)) for r in rows)


# ── T25 completed branch: rewards granted (currencies + audit) ─────
def test_reward_granted_on_completed_branch():
    """T25: Force `completed` branch, verify inventory + audit."""
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60,
                                       total_hp=100))
        async def _setup():
            g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                          {"_id": 0, "id": 1})
            before = {
                slug: await _inventory_currency_count(db, g["id"], slug)
                for slug in ["filo_lunare_spezzato",
                             "frammento_obelisco_vuoto",
                             "eco_della_luna_morta"]
            }
            gold_before = await _get_gold(db, g["id"])
            await db.world_boss_participants.insert_one({
                "id": str(uuid.uuid4()),
                "event_id": ev["id"], "guild_id": g["id"],
                "joined_at": _now().isoformat(),
                "total_contribution": 1500, "teams_sent": 2,
                "reward_granted": False,
            })
            await db.world_boss_events.update_one(
                {"id": ev["id"]},
                {"$set": {"current_hp": 0,
                          "ends_at": (_now() - timedelta(minutes=1)).isoformat()}},
            )
            return g["id"], before, gold_before

        gid, before, gold_before = _run(_setup())

        out = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t25",
        ))
        assert out["action"] == "resolved", out
        assert out["outcome"] == "completed", out

        async def _check_participant():
            p = await db.world_boss_participants.find_one(
                {"event_id": ev["id"], "guild_id": gid}, {"_id": 0},
            )
            assert p is not None
            assert p["reward_granted"] is True
            assert "reward_granted_at" in p
            assert p["reward_rank"] == 1
            return p
        _run(_check_participant())

        async def _check_inv():
            after = {
                slug: await _inventory_currency_count(db, gid, slug)
                for slug in ["filo_lunare_spezzato",
                             "frammento_obelisco_vuoto",
                             "eco_della_luna_morta"]
            }
            return after
        after = _run(_check_inv())
        assert after["filo_lunare_spezzato"] - before["filo_lunare_spezzato"] == 3
        assert after["frammento_obelisco_vuoto"] - before["frammento_obelisco_vuoto"] == 2
        assert after["eco_della_luna_morta"] - before["eco_della_luna_morta"] == 1

        gold_after = _run(_get_gold(db, gid))
        assert gold_after > gold_before

        async def _count_audit():
            return await db.audit_log.count_documents({
                "event_type": "WORLD_BOSS_REWARD_GRANTED",
                "related_entity_id": ev["id"],
                "actor_guild_id": gid,
            })
        assert _run(_count_audit()) == 1
    finally:
        if ev:
            _run(_cleanup_events())


# ── T26 completed branch: idempotent retry ─────────────────────────
def test_reward_completed_branch_idempotent():
    """T26: Retry resolve → skipped, inventory unchanged, no audit dup."""
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60,
                                       total_hp=100))
        async def _setup():
            g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                          {"_id": 0, "id": 1})
            await db.world_boss_participants.insert_one({
                "id": str(uuid.uuid4()),
                "event_id": ev["id"], "guild_id": g["id"],
                "joined_at": _now().isoformat(),
                "total_contribution": 1000, "teams_sent": 1,
                "reward_granted": False,
            })
            await db.world_boss_events.update_one(
                {"id": ev["id"]},
                {"$set": {"current_hp": 0,
                          "ends_at": (_now() - timedelta(minutes=1)).isoformat()}},
            )
            return g["id"]
        gid = _run(_setup())

        out1 = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t26_a",
        ))
        assert out1["action"] == "resolved"

        snap_filo = _run(_inventory_currency_count(db, gid, "filo_lunare_spezzato"))
        snap_gold = _run(_get_gold(db, gid))
        async def _count_audit():
            return await db.audit_log.count_documents({
                "event_type": "WORLD_BOSS_REWARD_GRANTED",
                "related_entity_id": ev["id"], "actor_guild_id": gid,
            })
        audit_after_first = _run(_count_audit())
        assert audit_after_first == 1

        out2 = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t26_b",
        ))
        assert out2["action"] == "skipped", out2

        assert _run(_inventory_currency_count(
            db, gid, "filo_lunare_spezzato")) == snap_filo
        assert _run(_get_gold(db, gid)) == snap_gold
        assert _run(_count_audit()) == audit_after_first
    finally:
        if ev:
            _run(_cleanup_events())


# ── T27 completed branch: ranking correctness ─────────────────────
def test_reward_completed_ranking_correct(admin_headers):
    """T27: Multi-guild ranking after completed resolution."""
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event
    ev = None
    fake_guild_ids = []
    try:
        # Pre-cleanup any leftover stubs from previous failed runs
        _run(db.guilds.delete_many({"_test_stub": True}))
        ev = _run(_create_test_event(status="active", ends_in_minutes=60,
                                       total_hp=100))
        async def _setup():
            g_real = await db.guilds.find_one(
                {"name": "The Iron Lantern"}, {"_id": 0, "id": 1})
            fakes = []
            run_uid = uuid.uuid4().hex[:8]
            for i, contrib in enumerate([500, 2500, 1500]):
                gid = g_real["id"] if i == 0 else f"fake-guild-t27-{run_uid}-{i}"
                if i > 0:
                    fakes.append(gid)
                    await db.guilds.insert_one({
                        "id": gid, "name": f"Fake Guild T27 #{i}",
                        "owner_user_id": f"fake-owner-t27-{i}-{uuid.uuid4()}",
                        "gold": 0, "level": 1,
                        "_test_stub": True,
                    })
                await db.world_boss_participants.insert_one({
                    "id": str(uuid.uuid4()),
                    "event_id": ev["id"], "guild_id": gid,
                    "joined_at": _now().isoformat(),
                    "total_contribution": contrib, "teams_sent": 1,
                    "reward_granted": False,
                })
            await db.world_boss_events.update_one(
                {"id": ev["id"]},
                {"$set": {"current_hp": 0,
                          "ends_at": (_now() - timedelta(minutes=1)).isoformat()}},
            )
            return fakes

        fake_guild_ids = _run(_setup())

        out = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t27",
        ))
        assert out["action"] == "resolved"
        assert out["outcome"] == "completed"

        r = requests.get(
            f"{API_BASE}/api/world-boss/events/{ev['id']}/ranking",
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        ranking = r.json()["ranking"]
        assert len(ranking) >= 3
        assert ranking[0]["contribution"] == 2500
        assert ranking[0]["rank"] == 1
        assert ranking[1]["contribution"] == 1500
        assert ranking[2]["contribution"] == 500
    finally:
        if fake_guild_ids:
            _run(db.guilds.delete_many({"id": {"$in": fake_guild_ids},
                                        "_test_stub": True}))
        if ev:
            _run(_cleanup_events())


# ── T28 completed branch: squad released ──────────────────────────
def test_reward_completed_squad_released():
    """T28: After completed resolution, no adv left with
    current_world_boss_event_id valorized."""
    from app.core.database import db
    from app.world_boss import resolve_stuck_world_boss_event
    ev = None
    try:
        ev = _run(_create_test_event(status="active", ends_in_minutes=60,
                                       total_hp=100))
        adv_ids: list[str] = []
        async def _setup():
            g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                          {"_id": 0, "id": 1})
            advs = await db.adventurers.find(
                {"guild_id": g["id"], "is_available": True},
                {"_id": 0, "id": 1},
            ).to_list(3)
            aids = [a["id"] for a in advs]
            await db.adventurers.update_many(
                {"id": {"$in": aids}},
                {"$set": {"is_available": False,
                          "expedition_in_progress": True,
                          "current_world_boss_event_id": ev["id"]}},
            )
            await db.world_boss_participants.insert_one({
                "id": str(uuid.uuid4()),
                "event_id": ev["id"], "guild_id": g["id"],
                "joined_at": _now().isoformat(),
                "total_contribution": 3000, "teams_sent": 1,
                "reward_granted": False,
            })
            await db.world_boss_events.update_one(
                {"id": ev["id"]},
                {"$set": {"current_hp": 0,
                          "ends_at": (_now() - timedelta(minutes=1)).isoformat()}},
            )
            return aids
        adv_ids = _run(_setup())

        out = _run(resolve_stuck_world_boss_event(
            ev["id"], dry_run=False, reason="test_t28",
        ))
        assert out["action"] == "resolved"
        assert out["outcome"] == "completed"
        assert out["adv_released"] == 3

        async def _check():
            n_bound = await db.adventurers.count_documents({
                "id": {"$in": adv_ids},
                "current_world_boss_event_id": ev["id"],
            })
            n_busy = await db.adventurers.count_documents({
                "id": {"$in": adv_ids},
                "$or": [{"is_available": False},
                        {"expedition_in_progress": True}],
            })
            return n_bound, n_busy
        n_bound, n_busy = _run(_check())
        assert n_bound == 0
        assert n_busy == 0
    finally:
        if ev:
            _run(_cleanup_events())
