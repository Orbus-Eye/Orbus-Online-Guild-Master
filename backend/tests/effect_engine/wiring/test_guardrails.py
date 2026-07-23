"""RT2-B-2A · Test guardrails (doppio guardrail FF + is_test_user).

Pattern: `def test_` + `asyncio.run(go())` (coerente con state_store tests).

Copre:
- T-2A-01 · flag OFF → NO-OP puro
- T-2A-02 · flag ON + user non-test → NO-OP puro
- T-2A-03 · flag ON + user test-user → shadow eseguito
- T-2A-04 · boundary Mongo error → fail-closed (return False)
- T-2A-05 · maybe_shadow_dispatch con flag OFF → nessun side-effect
"""
from __future__ import annotations

import asyncio

from app.stats.runtime.wiring.shadow_hooks import (
    _guardrail_check,
    maybe_shadow_dispatch,
    maybe_shadow_terminalize,
)


def test_guardrail_flag_off_returns_false(disable_cdv_flag, fake_db_test_user):
    """T-2A-01: FF OFF → guardrail returns False."""
    async def go():
        allowed, uid = await _guardrail_check(
            fake_db_test_user, {"id": "user-test-001"},
        )
        assert allowed is False
        assert uid is None
    asyncio.run(go())


def test_guardrail_flag_on_test_user_returns_true(enable_cdv_flag, fake_db_test_user):
    """T-2A-02: FF ON + is_test_user=True → allowed."""
    async def go():
        allowed, uid = await _guardrail_check(
            fake_db_test_user, {"id": "user-test-001"},
        )
        assert allowed is True
        assert uid == "user-test-001"
    asyncio.run(go())


def test_guardrail_flag_on_non_test_user_returns_false(enable_cdv_flag, fake_db_test_user):
    """T-2A-03: FF ON + is_test_user=False → NOT allowed."""
    async def go():
        allowed, uid = await _guardrail_check(
            fake_db_test_user, {"id": "user-normal-001"},
        )
        assert allowed is False
        assert uid is None
    asyncio.run(go())


def test_guardrail_missing_user_fail_closed(enable_cdv_flag, fake_db_test_user):
    """T-2A-04: user_id assente/None/inesistente → fail-closed False."""
    async def go():
        allowed, uid = await _guardrail_check(fake_db_test_user, {})
        assert allowed is False
        allowed2, uid2 = await _guardrail_check(fake_db_test_user, {"id": None})
        assert allowed2 is False
        allowed3, uid3 = await _guardrail_check(fake_db_test_user, {"id": "nonexistent"})
        assert allowed3 is False
    asyncio.run(go())


def test_guardrail_db_error_fail_closed(enable_cdv_flag):
    """T-2A-04b: Mongo error nella lookup users → fail-closed."""
    class _BrokenDb:
        class _BrokenColl:
            async def find_one(self, *a, **kw):
                raise ConnectionError("simulated Mongo down")
        users = _BrokenColl()

    async def go():
        allowed, uid = await _guardrail_check(_BrokenDb(), {"id": "any-id"})
        assert allowed is False
    asyncio.run(go())


def test_maybe_shadow_dispatch_flag_off_noop(disable_cdv_flag, fake_db_test_user):
    """T-2A-05: maybe_shadow_dispatch con flag OFF → nessun side-effect."""
    exp_doc = {"id": "exp-001", "team_power": 100, "final_team_power": 100}
    async def go():
        await maybe_shadow_dispatch(
            db=fake_db_test_user,
            current_user={"id": "user-test-001"},
            guild={},
            expedition_doc=exp_doc,
        )
    asyncio.run(go())
    # exp_doc invariato — B2Q08 no partial mutation
    assert exp_doc == {"id": "exp-001", "team_power": 100, "final_team_power": 100}


def test_maybe_shadow_terminalize_flag_off_noop(disable_cdv_flag, fake_db_test_user):
    """T-2A-06: maybe_shadow_terminalize con flag OFF → nessun side-effect."""
    async def go():
        await maybe_shadow_terminalize(
            db=fake_db_test_user,
            current_user={"id": "user-test-001"},
            expedition_doc={"id": "exp-001"},
            success=True,
        )
    asyncio.run(go())
