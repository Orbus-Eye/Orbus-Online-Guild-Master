"""RT2-B-2A · Test shadow lifecycle (CREATE → TERMINALIZE).

Pattern: `def test_` + `asyncio.run(go())`.

Copre B2Q02 (shell state creation), B2Q04 (3 terminal outcomes), B2Q09 (no
class transitions), B2Q10 (DB allowlist enforcement).
"""
from __future__ import annotations

import asyncio

from app.stats.runtime.state_store import (
    CasResultCode,
    FakeExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import RuntimeStatus
from app.stats.runtime.wiring.coordinator import (
    ExpeditionRuntimeCoordinator,
    TerminalOutcome,
)


def test_create_shell_state_success(fake_coordinator_allowlisted):
    """T-2A-07: shell state creation con DB allowlisted → SUCCESS."""
    async def go():
        res = await fake_coordinator_allowlisted.create_shell_state(
            expedition_id="exp-lifecycle-001",
            test_user_id="user-test-001",
            evaluation_payload={"expedition_id": "exp-lifecycle-001", "delta": 0},
        )
        assert res["result_code"] == CasResultCode.SUCCESS.value
        assert res["state_version"] == 1
        assert res["fencing_token"] == 0
        assert "evaluation_hash" in res
    asyncio.run(go())


def test_create_shell_state_is_empty_no_transitions(fake_coordinator_allowlisted):
    """T-2A-08: shell state contiene shell vuoto (B2Q09 no class transitions)."""
    exp_id = "exp-lifecycle-002"
    async def go():
        await fake_coordinator_allowlisted.create_shell_state(
            expedition_id=exp_id, test_user_id="uid-1",
        )
        read = await fake_coordinator_allowlisted._store.get_state(exp_id)
        assert read.code == CasResultCode.SUCCESS
        state = read.state
        assert state is not None
        assert state.adventurer_class_states == ()
        assert state.processed_event_keys == ()
        assert state.last_event_sequence == 0
        assert state.runtime_status == RuntimeStatus.ACTIVE
    asyncio.run(go())


def test_create_shell_state_idempotent(fake_coordinator_allowlisted):
    """T-2A-09: duplicate create → ALREADY_EXISTS silent (B2Q08 no partial mutation)."""
    exp_id = "exp-idempotent-001"
    async def go():
        first = await fake_coordinator_allowlisted.create_shell_state(
            expedition_id=exp_id, test_user_id="uid-1",
        )
        assert first["result_code"] == CasResultCode.SUCCESS.value
        second = await fake_coordinator_allowlisted.create_shell_state(
            expedition_id=exp_id, test_user_id="uid-1",
        )
        assert second["result_code"] == CasResultCode.ALREADY_EXISTS.value
    asyncio.run(go())


def test_terminalize_completed(fake_coordinator_allowlisted):
    """T-2A-10: terminalize COMPLETED (B2Q04)."""
    exp_id = "exp-terminalize-001"
    async def go():
        await fake_coordinator_allowlisted.create_shell_state(
            expedition_id=exp_id, test_user_id="uid-1",
        )
        res = await fake_coordinator_allowlisted.terminalize(
            expedition_id=exp_id, outcome=TerminalOutcome.COMPLETED,
        )
        assert res["result_code"] in (
            CasResultCode.SUCCESS.value, CasResultCode.DEDUPLICATED_NO_OP.value,
        )
        assert res["outcome"] == "COMPLETED"
    asyncio.run(go())


def test_terminalize_completed_with_failure(fake_coordinator_allowlisted):
    """T-2A-11: terminalize COMPLETED_WITH_FAILURE (B2Q04)."""
    exp_id = "exp-fail-001"
    async def go():
        await fake_coordinator_allowlisted.create_shell_state(
            expedition_id=exp_id, test_user_id="uid-1",
        )
        res = await fake_coordinator_allowlisted.terminalize(
            expedition_id=exp_id, outcome=TerminalOutcome.COMPLETED_WITH_FAILURE,
        )
        assert res["result_code"] in (
            CasResultCode.SUCCESS.value, CasResultCode.DEDUPLICATED_NO_OP.value,
        )
        assert res["outcome"] == "COMPLETED_WITH_FAILURE"
    asyncio.run(go())


def test_terminalize_cancelled(fake_coordinator_allowlisted):
    """T-2A-12: terminalize CANCELLED (B2Q04)."""
    exp_id = "exp-cancel-001"
    async def go():
        await fake_coordinator_allowlisted.create_shell_state(
            expedition_id=exp_id, test_user_id="uid-1",
        )
        res = await fake_coordinator_allowlisted.terminalize(
            expedition_id=exp_id, outcome=TerminalOutcome.CANCELLED,
        )
        assert res["result_code"] in (
            CasResultCode.SUCCESS.value, CasResultCode.DEDUPLICATED_NO_OP.value,
        )
    asyncio.run(go())


def test_terminalize_missing_state_cleanup_deferred(fake_coordinator_allowlisted):
    """T-2A-13: terminalize su state inesistente → cleanup deferred (B2Q08)."""
    async def go():
        res = await fake_coordinator_allowlisted.terminalize(
            expedition_id="exp-nonexistent-9999", outcome=TerminalOutcome.COMPLETED,
        )
        assert res["result_code"] == CasResultCode.NOT_FOUND.value
    asyncio.run(go())


def test_db_forbidden_no_op(fake_coordinator_forbidden):
    """T-2A-14: DB forbidden (B2Q10) → coordinator no-op silenzioso."""
    assert fake_coordinator_forbidden.is_target_db_allowlisted is False
    async def go():
        res = await fake_coordinator_forbidden.create_shell_state(
            expedition_id="exp-forbidden-001", test_user_id="uid-1",
        )
        assert res["result_code"] == "DB_NOT_ALLOWLISTED"
        read = await fake_coordinator_forbidden._store.get_state("exp-forbidden-001")
        assert read.code == CasResultCode.NOT_FOUND
    asyncio.run(go())


def test_terminalize_forbidden_db_deferred(fake_coordinator_forbidden):
    """T-2A-15: terminalize su DB forbidden → cleanup_deferred senza mutation."""
    async def go():
        res = await fake_coordinator_forbidden.terminalize(
            expedition_id="exp-forbidden-002", outcome=TerminalOutcome.COMPLETED,
        )
        assert res["result_code"] == "DB_NOT_ALLOWLISTED"
    asyncio.run(go())


def test_store_infra_error_isolation():
    """T-2A-16: store raise Exception → coordinator ritorna STORE_INFRA_ERROR (B2Q08)."""
    class _BrokenStore(FakeExpeditionRuntimeStateStore):
        async def create_state(self, *a, **kw):
            raise RuntimeError("simulated store failure")
        async def expire_state(self, *a, **kw):
            raise RuntimeError("simulated store failure")

    coord = ExpeditionRuntimeCoordinator(
        store=_BrokenStore(), target_db_name="orbus_r16_rt2b_test",
    )

    async def go():
        res1 = await coord.create_shell_state(expedition_id="exp-broken-001", test_user_id="uid")
        assert res1["result_code"] == "STORE_INFRA_ERROR"
        res2 = await coord.terminalize(
            expedition_id="exp-broken-001", outcome=TerminalOutcome.COMPLETED,
        )
        assert res2["result_code"] == "STORE_INFRA_ERROR"
    asyncio.run(go())
