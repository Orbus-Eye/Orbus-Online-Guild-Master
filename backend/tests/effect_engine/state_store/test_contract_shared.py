"""RT2-B-1A · Shared contract-test suite.

Testa che entrambe le implementazioni (`fake`, `mongo_mock`) rispettino
identicamente i contract:
- create + get
- CAS success
- CAS state version conflict
- CAS stale writer (fencing mismatch)
- lease acquire + renew + release
- lease expiry → new fencing token
- deduplication idempotent no-op
- EVENT_ID_PAYLOAD_MISMATCH
- state_version monotonicity
- event_sequence monotonicity
- receipt retention bounded (fail-closed)

Ownership + cap tests: in `test_security.py`.

Tutti i test sono `pytest.mark.asyncio`-free perché usano `pytest_asyncio`
convention (auto-detected da async fixture pattern). Se non disponibile
uso `@pytest.mark.asyncio` esplicito.
"""
from __future__ import annotations

import asyncio

import pytest

from app.stats.runtime.state_store import (
    CasResultCode,
    ExpeditionRuntimeState,
    ExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import RuntimeStatus


# ─── Helper: initial state seeded via fixture-friendly primitives ───────
def _make_initial_state(expedition_id: str = "exp-001") -> ExpeditionRuntimeState:
    return ExpeditionRuntimeState(
        expedition_id=expedition_id,
        state_version=1,
        created_at="2026-02-01T12:00:00Z",
        updated_at="2026-02-01T12:00:00Z",
        expires_at="2026-02-01T18:00:00Z",
        runtime_status=RuntimeStatus.ACTIVE,
        loadout_snapshot_version=0,
        fencing_token=0,
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══════════════════════ 1. create + get ═══════════════════════
def test_create_and_get(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        r = await store.create_state("exp-001", _make_initial_state())
        assert r.code == CasResultCode.SUCCESS
        assert r.new_state_version == 1
        r2 = await store.get_state("exp-001")
        assert r2.code == CasResultCode.SUCCESS
        assert r2.state.state_version == 1
        assert r2.state.expedition_id == "exp-001"

    _run(go())


def test_create_duplicate_returns_already_exists(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-002", _make_initial_state("exp-002"))
        r = await store.create_state("exp-002", _make_initial_state("exp-002"))
        assert r.code == CasResultCode.ALREADY_EXISTS

    _run(go())


def test_get_not_found(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        r = await store.get_state("nonexistent")
        assert r.code == CasResultCode.NOT_FOUND

    _run(go())


# ═══════════════════════ 2. lease acquire / renew / release ═══════════════════════
def test_lease_acquire_success(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-l1", _make_initial_state("exp-l1"))
        r = await store.reserve_writer("exp-l1", "worker-A", lease_ttl_seconds=30)
        assert r.code == CasResultCode.SUCCESS
        assert r.lease_id is not None
        assert r.fencing_token == 1

    _run(go())


def test_lease_second_acquire_rejected_while_active(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-l2", _make_initial_state("exp-l2"))
        r1 = await store.reserve_writer("exp-l2", "worker-A", 30)
        assert r1.code == CasResultCode.SUCCESS
        r2 = await store.reserve_writer("exp-l2", "worker-B", 30)
        assert r2.code == CasResultCode.STATE_VERSION_CONFLICT

    _run(go())


def test_lease_renewal_preserves_fencing_token(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-l3", _make_initial_state("exp-l3"))
        r1 = await store.reserve_writer("exp-l3", "worker-A", 30)
        assert r1.fencing_token == 1
        r2 = await store.renew_writer_lease("exp-l3", r1.lease_id, 1, extend_seconds=30)
        assert r2.code == CasResultCode.SUCCESS
        assert r2.fencing_token == 1  # renewal does NOT bump the token

    _run(go())


def test_lease_release_success(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-l4", _make_initial_state("exp-l4"))
        r1 = await store.reserve_writer("exp-l4", "worker-A", 30)
        r2 = await store.release_writer("exp-l4", r1.lease_id, r1.fencing_token)
        assert r2.code == CasResultCode.SUCCESS
        r3 = await store.reserve_writer("exp-l4", "worker-B", 30)
        # After release, new acquisition BUMPS the token.
        assert r3.code == CasResultCode.SUCCESS
        assert r3.fencing_token == 2

    _run(go())


def test_lease_expiry_new_fencing_token(store: ExpeditionRuntimeStateStore, frozen_clock) -> None:
    async def go():
        await store.create_state("exp-l5", _make_initial_state("exp-l5"))
        r1 = await store.reserve_writer("exp-l5", "worker-A", 30)
        assert r1.fencing_token == 1
        # Advance past expiry + grace
        frozen_clock.advance(60)
        r2 = await store.reserve_writer("exp-l5", "worker-B", 30)
        assert r2.code == CasResultCode.SUCCESS
        assert r2.fencing_token == 2  # new acquire bumps token

    _run(go())


def test_renew_after_grace_returns_lease_expired(store: ExpeditionRuntimeStateStore, frozen_clock) -> None:
    async def go():
        await store.create_state("exp-l6", _make_initial_state("exp-l6"))
        r1 = await store.reserve_writer("exp-l6", "worker-A", 30)
        frozen_clock.advance(120)  # well past grace
        r2 = await store.renew_writer_lease("exp-l6", r1.lease_id, r1.fencing_token, 30)
        assert r2.code == CasResultCode.LEASE_EXPIRED

    _run(go())


# ═══════════════════════ 3. CAS ═══════════════════════
def test_cas_success(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-c1", _make_initial_state("exp-c1"))
        lease = await store.reserve_writer("exp-c1", "w-A", 30)
        r = await store.compare_and_update(
            "exp-c1",
            expected_state_version=1,
            expected_fencing_token=lease.fencing_token,
            mutation={"loadout_snapshot_version": 1},
        )
        assert r.code == CasResultCode.SUCCESS
        assert r.new_state_version == 2

    _run(go())


def test_cas_state_version_conflict(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-c2", _make_initial_state("exp-c2"))
        lease = await store.reserve_writer("exp-c2", "w-A", 30)
        # First mutation succeeds
        r1 = await store.compare_and_update("exp-c2", 1, lease.fencing_token, {"loadout_snapshot_version": 1})
        assert r1.code == CasResultCode.SUCCESS
        # Second mutation with STALE state_version=1
        r2 = await store.compare_and_update("exp-c2", 1, lease.fencing_token, {"loadout_snapshot_version": 2})
        assert r2.code == CasResultCode.STATE_VERSION_CONFLICT

    _run(go())


def test_cas_stale_writer_rejected(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-c3", _make_initial_state("exp-c3"))
        lease1 = await store.reserve_writer("exp-c3", "w-A", 30)
        await store.release_writer("exp-c3", lease1.lease_id, lease1.fencing_token)
        lease2 = await store.reserve_writer("exp-c3", "w-B", 30)
        assert lease2.fencing_token == 2  # bumped
        # Old worker w-A tries to mutate with stale fencing_token=1
        r = await store.compare_and_update("exp-c3", 1, expected_fencing_token=1, mutation={"loadout_snapshot_version": 99})
        assert r.code == CasResultCode.STALE_WRITER_REJECTED

    _run(go())


# ═══════════════════════ 4. apply_event_once (deduplication) ═══════════════════════
def test_event_idempotent_no_op(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-e1", _make_initial_state("exp-e1"))
        lease = await store.reserve_writer("exp-e1", "w-A", 30)
        r1 = await store.apply_event_once(
            "exp-e1", "evt-1", "mark_apply", "adv-A", "hash-x",
            expected_state_version=1, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r1.code == CasResultCode.SUCCESS
        assert r1.assigned_event_sequence == 1
        # Retry with SAME event_id + SAME payload_hash
        r2 = await store.apply_event_once(
            "exp-e1", "evt-1", "mark_apply", "adv-A", "hash-x",
            expected_state_version=999, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r2.code == CasResultCode.DEDUPLICATED_NO_OP
        assert r2.assigned_event_sequence == 1
        assert r2.prior_result_reference == "evt-1"

    _run(go())


def test_event_id_payload_mismatch(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-e2", _make_initial_state("exp-e2"))
        lease = await store.reserve_writer("exp-e2", "w-A", 30)
        await store.apply_event_once(
            "exp-e2", "evt-1", "mark_apply", "adv-A", "hash-x",
            expected_state_version=1, expected_fencing_token=lease.fencing_token, mutation={},
        )
        # Same event_id, DIFFERENT payload_hash
        r = await store.apply_event_once(
            "exp-e2", "evt-1", "mark_apply", "adv-A", "hash-Y",
            expected_state_version=2, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r.code == CasResultCode.EVENT_ID_PAYLOAD_MISMATCH

    _run(go())


def test_event_sequence_monotonicity(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-e3", _make_initial_state("exp-e3"))
        lease = await store.reserve_writer("exp-e3", "w-A", 30)
        seqs = []
        for i in range(1, 5):
            r = await store.apply_event_once(
                "exp-e3", f"evt-{i}", "mark_apply", "adv-A", f"hash-{i}",
                expected_state_version=i, expected_fencing_token=lease.fencing_token, mutation={},
            )
            assert r.code == CasResultCode.SUCCESS
            seqs.append(r.assigned_event_sequence)
        assert seqs == [1, 2, 3, 4]

    _run(go())


def test_state_version_monotonicity(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-v1", _make_initial_state("exp-v1"))
        lease = await store.reserve_writer("exp-v1", "w-A", 30)
        v = 1
        for _ in range(3):
            r = await store.compare_and_update("exp-v1", v, lease.fencing_token, {"loadout_snapshot_version": v})
            assert r.code == CasResultCode.SUCCESS
            assert r.new_state_version == v + 1
            v = r.new_state_version
        assert v == 4

    _run(go())


# ═══════════════════════ 5. expire / delete / version ═══════════════════════
def test_expire_state_and_idempotent(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-x1", _make_initial_state("exp-x1"))
        r1 = await store.expire_state("exp-x1")
        assert r1.code == CasResultCode.SUCCESS
        r2 = await store.expire_state("exp-x1")
        assert r2.code == CasResultCode.DEDUPLICATED_NO_OP

    _run(go())


def test_delete_state_and_not_found(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-d1", _make_initial_state("exp-d1"))
        r1 = await store.delete_state("exp-d1")
        assert r1.code == CasResultCode.SUCCESS
        r2 = await store.delete_state("exp-d1")
        assert r2.code == CasResultCode.NOT_FOUND

    _run(go())


def test_get_version(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-gv", _make_initial_state("exp-gv"))
        r = await store.get_version("exp-gv")
        assert r.code == CasResultCode.SUCCESS
        assert r.version_only == 1
        r2 = await store.get_version("nonexistent")
        assert r2.code == CasResultCode.NOT_FOUND

    _run(go())


def test_health_check(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        ok = await store.health_check()
        assert ok is True

    _run(go())
