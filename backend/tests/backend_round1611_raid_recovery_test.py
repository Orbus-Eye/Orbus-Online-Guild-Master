"""ROUND 16.1.1 Hotfix — Raid stuck recovery tests.

Validates that `resolve_stuck_raid` from `app.raids.recovery`:
  * Resolves a raid stuck `in_progress` with expired `ends_at`.
  * Releases all squad members (is_available=True).
  * Does NOT duplicate rewards/audit on retry (idempotent).
  * Does NOT touch raids still running (`ends_at > now`).
  * Marks recovered raids with `recovered=True` + reason metadata.
  * On-visit fallback via `GET /api/raids` auto-resolves stuck raids
    in the same request that surfaces them.

Test isolation: each test creates its own raid via direct DB insert
to avoid coupling to the `/api/raids/start` flow + roster requirements.
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _seed_raid(
    db, *, guild_id: str, ends_at: datetime, status: str = "in_progress",
    raid_dungeon_id: str = None, raid_dungeon_slug: str = "broken-bastion-siege",
    member_adv_ids: list[str] = None,
) -> dict:
    """Create a fully-formed raid row directly in the DB (bypasses
    /api/raids/start which requires a 20-adv roster).
    """
    if raid_dungeon_id is None:
        rd = await db.raid_dungeons.find_one({"slug": raid_dungeon_slug}, {"_id": 0})
        raid_dungeon_id = rd["id"] if rd else "rd_test"
    raid_id = str(uuid.uuid4())
    now_iso = _now().isoformat()
    doc = {
        "id": raid_id,
        "guild_id": guild_id,
        "raid_dungeon_id": raid_dungeon_id,
        "raid_dungeon_slug": raid_dungeon_slug,
        "status": status,
        "started_at": (ends_at - timedelta(hours=1)).isoformat(),
        "ends_at": ends_at.isoformat(),
        "team_power_combined": 4000,
        "recommended_power_combined": 5000,
        "success_chance_combined": 60,
        "success_chance_per_party": [60, 60, 60, 60],
        "parties_outcome": [],
        "outcome": None,
        "raid_score": 0,
        "rewards": None,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await db.raids.insert_one(doc)
    # Seed participants if provided
    if member_adv_ids:
        for i, adv_id in enumerate(member_adv_ids):
            party_idx = (i // 5) + 1
            await db.raid_participants.insert_one({
                "id": str(uuid.uuid4()),
                "raid_id": raid_id,
                "adventurer_id": adv_id,
                "party_idx": party_idx,
                "role_snapshot": "DPS",
                "class_snapshot": "Warrior",
                "level_snapshot": 5,
            })
            # Block them
            await db.adventurers.update_one(
                {"id": adv_id},
                {"$set": {
                    "is_available": False,
                    "expedition_in_progress": True,
                }},
            )
    return doc


async def _cleanup_raid(db, raid_id: str):
    """Idempotent test teardown."""
    raid = await db.raids.find_one({"id": raid_id}, {"_id": 0})
    if raid:
        # Release any blocked advs
        parts = await db.raid_participants.find(
            {"raid_id": raid_id}, {"_id": 0, "adventurer_id": 1}
        ).to_list(50)
        adv_ids = [p["adventurer_id"] for p in parts]
        if adv_ids:
            await db.adventurers.update_many(
                {"id": {"$in": adv_ids}},
                {"$set": {"is_available": True, "expedition_in_progress": False}},
            )
        await db.raid_participants.delete_many({"raid_id": raid_id})
        await db.raids.delete_one({"id": raid_id})
    await db.audit_log.delete_many({
        "related_entity_id": raid_id,
        "event_type": "raid_recovered",
    })


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── T01 ────────────────────────────────────────────────────────────
def test_raid_in_progress_with_past_ends_at_gets_resolved():
    """Base case: a stuck raid (in_progress + ends_at < now) is resolved."""
    from app.core.database import db
    from app.raids.recovery import resolve_stuck_raid

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            adv_ids = [str(uuid.uuid4()) for _ in range(4)]
            # Insert minimal stub adventurers
            for aid in adv_ids:
                await db.adventurers.insert_one({
                    "id": aid, "guild_id": guild["id"], "name": f"Test {aid[:6]}",
                    "level": 5, "experience": 0,
                    "is_available": False, "expedition_in_progress": True,
                    "_test_raid_recovery_stub": True,
                })
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() - timedelta(minutes=10),
                member_adv_ids=adv_ids,
            )
            return doc["id"], adv_ids

        raid_id, adv_ids = _run(_setup())
        out = _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t01"))
        assert out["action"] == "resolved", out
        assert out["recovered"] is True
        assert out["outcome"] in ("victory", "partial", "wipe")
        async def _check():
            r = await db.raids.find_one({"id": raid_id}, {"_id": 0})
            assert r["status"] == "completed"
            assert r["recovered"] is True
            return r
        _run(_check())
        # Cleanup stub adventurers
        async def _cleanup_stubs():
            await db.adventurers.delete_many({"_test_raid_recovery_stub": True})
        _run(_cleanup_stubs())
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))


# ── T02 ────────────────────────────────────────────────────────────
def test_stuck_raid_releases_squad_members():
    """Recovery must release all blocked adventurers (is_available=True)."""
    from app.core.database import db
    from app.raids.recovery import resolve_stuck_raid

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            adv_ids = [str(uuid.uuid4()) for _ in range(6)]
            for aid in adv_ids:
                await db.adventurers.insert_one({
                    "id": aid, "guild_id": guild["id"], "name": f"Test {aid[:6]}",
                    "level": 5, "experience": 0,
                    "is_available": False, "expedition_in_progress": True,
                    "_test_raid_recovery_stub": True,
                })
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() - timedelta(minutes=5),
                member_adv_ids=adv_ids,
            )
            return doc["id"], adv_ids

        raid_id, adv_ids = _run(_setup())
        out = _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t02"))
        assert out["members_released"] == 6, out

        async def _check_releases():
            still_blocked = await db.adventurers.count_documents({
                "id": {"$in": adv_ids},
                "$or": [{"is_available": False}, {"expedition_in_progress": True}],
            })
            return still_blocked
        assert _run(_check_releases()) == 0
        _run(db.adventurers.delete_many({"_test_raid_recovery_stub": True}))
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))


# ── T03 ────────────────────────────────────────────────────────────
def test_resolve_does_not_duplicate_rewards_on_retry():
    """Calling resolve_stuck_raid twice must apply rewards exactly once."""
    from app.core.database import db
    from app.raids.recovery import resolve_stuck_raid

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            gold_before = guild.get("gold", 0)
            adv_ids = [str(uuid.uuid4()) for _ in range(4)]
            for aid in adv_ids:
                await db.adventurers.insert_one({
                    "id": aid, "guild_id": guild["id"], "name": f"Test {aid[:6]}",
                    "level": 5, "experience": 0,
                    "is_available": False, "expedition_in_progress": True,
                    "_test_raid_recovery_stub": True,
                })
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() - timedelta(minutes=10),
                member_adv_ids=adv_ids,
            )
            return doc["id"], guild["id"], gold_before

        raid_id, gid, gold_before = _run(_setup())

        # 1st call: resolves
        out1 = _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t03_a"))
        assert out1["action"] == "resolved", out1

        async def _get_gold():
            g = await db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})
            return g.get("gold", 0)
        gold_after_first = _run(_get_gold())

        # 2nd call: must skip (status no longer in_progress)
        out2 = _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t03_b"))
        assert out2["action"] == "skipped", out2
        gold_after_second = _run(_get_gold())
        # Gold must NOT have changed between the two calls.
        assert gold_after_second == gold_after_first
        _run(db.adventurers.delete_many({"_test_raid_recovery_stub": True}))
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))


# ── T04 ────────────────────────────────────────────────────────────
def test_resolve_does_not_duplicate_audit_event():
    """Retry must NOT emit a second `raid_recovered` audit row."""
    from app.core.database import db
    from app.raids.recovery import resolve_stuck_raid

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() - timedelta(minutes=10),
            )
            return doc["id"]

        raid_id = _run(_setup())
        _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t04"))
        _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t04_retry"))

        async def _count_audit():
            return await db.audit_log.count_documents({
                "related_entity_id": raid_id,
                "event_type": "raid_recovered",
            })
        assert _run(_count_audit()) == 1
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))


# ── T05 ────────────────────────────────────────────────────────────
def test_raid_still_running_is_not_touched():
    """A raid with `ends_at > now` must NOT be resolved (no-op)."""
    from app.core.database import db
    from app.raids.recovery import resolve_stuck_raid

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() + timedelta(hours=2),
            )
            return doc["id"]

        raid_id = _run(_setup())
        out = _run(resolve_stuck_raid(db, raid_id, dry_run=False, reason="test_t05"))
        assert out["action"] == "skipped"
        assert out["reason"] == "still_running"

        async def _check():
            r = await db.raids.find_one({"id": raid_id}, {"_id": 0})
            assert r["status"] == "in_progress"  # untouched
        _run(_check())
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))


# ── T06 ────────────────────────────────────────────────────────────
def test_score_zero_anomaly_resolved_with_recovered_metadata():
    """Real-world anomaly: status=in_progress, raid_score=0, ends_at past →
    after recovery, `recovered=True` + `recovery_reason` set."""
    from app.core.database import db
    from app.raids.recovery import resolve_stuck_raid

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() - timedelta(days=4),  # ancient stuck raid
            )
            return doc["id"]

        raid_id = _run(_setup())
        out = _run(resolve_stuck_raid(
            db, raid_id, dry_run=False, reason="hotfix_round1611",
        ))
        assert out["action"] == "resolved"
        assert out["recovered"] is True
        assert out["recovery_reason"] == "hotfix_round1611"

        async def _check():
            r = await db.raids.find_one({"id": raid_id}, {"_id": 0})
            assert r["recovered"] is True
            assert r["recovery_reason"] == "hotfix_round1611"
            assert r["status"] == "completed"
            assert "recovery_completed_at" in r
        _run(_check())
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))


# ── T07 ────────────────────────────────────────────────────────────
def test_on_visit_fallback_auto_resolves_expired_raid(admin_headers):
    """Calling GET /api/raids must auto-resolve stuck raids on visit."""
    from app.core.database import db

    raid_id = None
    try:
        async def _setup():
            guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
            doc = await _seed_raid(
                db, guild_id=guild["id"],
                ends_at=_now() - timedelta(minutes=15),
            )
            return doc["id"]

        raid_id = _run(_setup())

        # Hit the list endpoint — fallback should kick in.
        r = requests.get(f"{API_BASE}/api/raids",
                         headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text

        async def _check():
            r2 = await db.raids.find_one({"id": raid_id}, {"_id": 0})
            assert r2["status"] == "completed"
            assert r2.get("recovered") is True
        _run(_check())
    finally:
        if raid_id:
            _run(_cleanup_raid(db, raid_id))
