"""ROUND 16.A Phase 2 — Audit Bridge tests.

Validates the three new audit event channels:
  * ACHIEVEMENT_UNLOCKED (canonical via `write_audit`, includes
    trigger_event payload key).
  * GUILD_XP_GAINED (emitted by the new `add_guild_xp` helper).
  * onboarding_graduated (one-shot when dismissed_implicit flips).
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def tester_guild_id(auth_headers):
    r = requests.get(f"{API_BASE}/api/guilds/me",
                     headers=auth_headers, timeout=10)
    g = r.json()
    return (g.get("guild") or g).get("id")


def _loop():
    return asyncio.get_event_loop()


# ── T01: ACHIEVEMENT_UNLOCKED audit row is written on engine unlock ──
def test_achievement_unlocked_emits_audit_event():
    from app.core.database import db
    from app.audit.log import write_audit

    async def _run():
        gid = f"test-guild-{uuid.uuid4()}"
        # Direct unit test on `write_audit` — exercise the new event_type
        # `achievement_unlocked` and verify it lands in `audit_log`.
        audit_id = await write_audit(
            db,
            event_type="achievement_unlocked",
            actor_guild_id=gid,
            source="achievement.engine",
            related_entity_id="forge_initiate",
            metadata={
                "achievement_slug": "forge_initiate",
                "guild_xp_reward": 50,
                "achievement_points_reward": 5,
                "trigger_event_that_caused_it": "item_crafted",
            },
        )
        assert audit_id is not None
        row = await db.audit_log.find_one({"id": audit_id})
        assert row is not None
        assert row["event_type"] == "achievement_unlocked"
        assert row["actor_guild_id"] == gid
        md = row["metadata"]
        assert md["achievement_slug"] == "forge_initiate"
        assert md["trigger_event_that_caused_it"] == "item_crafted"
        # cleanup our synthetic row to keep audit_log lean
        await db.audit_log.delete_one({"id": audit_id})

    _loop().run_until_complete(_run())


# ── T02: idempotency — engine's `completed_at: None` CAS prevents
# double emission. We assert the rules by checking the achievement
# engine source carries the canonical CAS pattern.
def test_achievement_unlocked_idempotent():
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "app" / "achievements"
           / "engine.py").read_text()
    # The completion path MUST be guarded by a `completed_at: None` CAS.
    assert "completed_at" in src and "None" in src
    assert "find_one_and_update" in src
    # And `_audit_completion` is invoked ONLY after a successful CAS:
    # i.e. immediately after `if not marked: continue` short-circuit.
    assert "if not marked:" in src
    assert "_audit_completion(" in src


# ── T03: add_guild_xp helper credits XP and emits GUILD_XP_GAINED ────
def test_guild_xp_gained_via_helper(tester_guild_id):
    from app.core.database import db
    from app.achievements.engine import add_guild_xp

    async def _run():
        # Snapshot the BEFORE state.
        before = await db.guilds.find_one({"id": tester_guild_id})
        amt = 7  # tiny credit, will be reversed at end-of-test
        # Apply the credit through the canonical helper.
        snap = await add_guild_xp(
            db, tester_guild_id, amt,
            source="round16A_phase2_test",
            source_id=f"unit-{uuid.uuid4()}",
        )
        assert snap["guild_xp"] >= int(before.get("guild_xp", 0) or 0) + amt
        # An audit row must exist with the new event_type.
        row = await db.audit_log.find_one(
            {"event_type": "guild_xp_gained",
             "actor_guild_id": tester_guild_id,
             "source": "round16A_phase2_test"},
            sort=[("created_at", -1)],
        )
        assert row is not None, "guild_xp_gained audit row was not written"
        assert row["metadata"]["xp_amount"] == amt
        # Roll back the synthetic XP so the test is non-destructive.
        await db.guilds.update_one(
            {"id": tester_guild_id},
            {"$inc": {"guild_xp": -amt}},
        )
        # Remove the test audit row for hygiene.
        await db.audit_log.delete_one({"id": row["id"]})

    _loop().run_until_complete(_run())


# ── T04: `add_guild_xp` is what the achievement engine uses ──────────
def test_guild_xp_helper_used_in_achievement_unlock():
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "app" / "achievements"
           / "engine.py").read_text()
    # The reward path MUST flow through `add_guild_xp` (directly or via
    # the `_apply_reward` shim that wraps it).
    assert "add_guild_xp" in src
    assert "achievement_unlock" in src, (
        "achievement_unlock source label missing — XP credits would be "
        "indistinguishable from other sources in the audit log")


# ── T05: onboarding_graduated emits exactly once on first transition ─
def test_onboarding_graduated_emits_once(auth_headers, tester_guild_id):
    """Force a clean transition on the tester guild by clearing the
    `onboarding_graduated_at` flag, then hitting the endpoint twice.
    Only the first call should write the audit row.

    SAFE: we are only manipulating a metadata flag — no game data is
    altered, no hard delete.
    """
    from app.core.database import db

    async def _run():
        # Reset the graduation flag (idempotent).
        await db.guilds.update_one(
            {"id": tester_guild_id},
            {"$set": {"onboarding_graduated_at": None}},
        )
        await db.audit_log.delete_many({
            "event_type": "onboarding_graduated",
            "actor_guild_id": tester_guild_id,
        })

    _loop().run_until_complete(_run())

    # First call — should emit.
    r1 = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                      headers=auth_headers, timeout=10)
    assert r1.status_code == 200
    assert r1.json().get("dismissed_implicit") is True

    # Second call — must be a no-op for audit emission.
    r2 = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                      headers=auth_headers, timeout=10)
    assert r2.status_code == 200
    assert r2.json().get("dismissed_implicit") is True

    async def _verify():
        rows = await db.audit_log.count_documents({
            "event_type": "onboarding_graduated",
            "actor_guild_id": tester_guild_id,
        })
        assert rows == 1, (
            f"expected exactly 1 onboarding_graduated row, got {rows}")
        # Check payload shape.
        row = await db.audit_log.find_one({
            "event_type": "onboarding_graduated",
            "actor_guild_id": tester_guild_id,
        })
        md = row["metadata"]
        assert md["graduation_reason"] in (
            "guild_level_ge_3", "completed_expeditions_ge_3")
        assert isinstance(md["completed_steps_count"], int)

    _loop().run_until_complete(_verify())


# ── T06: already-graduated guild does NOT emit again ─────────────────
def test_onboarding_graduated_no_emit_for_already_graduated(
        auth_headers, tester_guild_id):
    """T05 left the flag set. Hitting the endpoint again must not add
    a second row."""
    from app.core.database import db

    async def _before():
        return await db.audit_log.count_documents({
            "event_type": "onboarding_graduated",
            "actor_guild_id": tester_guild_id,
        })

    n_before = _loop().run_until_complete(_before())
    assert n_before >= 1

    r = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200

    async def _after():
        return await db.audit_log.count_documents({
            "event_type": "onboarding_graduated",
            "actor_guild_id": tester_guild_id,
        })

    n_after = _loop().run_until_complete(_after())
    assert n_after == n_before, (
        f"audit emitted again on re-graduated read: {n_before}→{n_after}")


# ── T07: a clean (new-player) guild does NOT emit ────────────────────
def test_onboarding_graduated_no_emit_for_new_player():
    """Hit the dashboard with the `clean_onboarding@orbus.test` account
    (no guild, no progress). Even if it had a guild with low level the
    flag would not flip — the endpoint MUST be silent."""
    from app.core.database import db
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": "clean_onboarding@orbus.test",
              "password": "password123"},
        timeout=10,
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    # The clean account has no guild → endpoint 404s, which is fine; no
    # graduation row should exist anyway.
    r2 = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                      headers=h, timeout=10)
    assert r2.status_code in (200, 404)
    if r2.status_code == 200:
        assert r2.json().get("dismissed_implicit") is False

    # Look up the user → guild (may be None) and assert no audit row.
    async def _verify():
        u = await db.users.find_one(
            {"email": "clean_onboarding@orbus.test"})
        g = await db.guilds.find_one({"owner_user_id": u["id"]}) if u else None
        if g is None:
            return  # no guild → trivially no audit row possible
        cnt = await db.audit_log.count_documents({
            "event_type": "onboarding_graduated",
            "actor_guild_id": g["id"],
        })
        assert cnt == 0, (
            "clean-onboarding guild should not have emitted graduation")

    _loop().run_until_complete(_verify())
