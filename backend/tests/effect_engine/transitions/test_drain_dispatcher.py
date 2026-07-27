"""RT2-B-2B-2-1 · Drain dispatcher tests (FakeStore · lease/fencing/CAS/dedup).

Copertura: full flow · replay/dedup · payload mismatch · races (B2B2Q10/Q11) ·
fold receipt (B2B2Q14) · lifecycle aggregation · receipt cap · lease failure ·
retry limit · feature gating (B2B2Q13) · test-user fail-closed · allowlist ·
legacy invariance · audit mapping (B2B2Q15).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.stats.runtime.state_store.fake_store import FakeExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    DrainStatus,
    EventReceipt,
    ExpeditionRuntimeState,
    RuntimeStatus,
)
from app.stats.runtime.state_store.results import CasResult, CasResultCode
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.drain import coerce_drains
from app.stats.runtime.transitions.models import (
    ClassEventType,
    TransitionResultCode as RC,
)
from app.stats.runtime.transitions.state_machine import RECEIPT_CAP_ORDINARY
from app.stats.runtime.wiring.coordinator import ExpeditionRuntimeCoordinator
from tests.effect_engine.transitions.conftest import (
    make_event,
    run,
    trusted_context,
)

ADV = "adv-cdv-01"
TGT = "target-boss-01"


def _dispatch(store, event, ctx=None):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-test", now_fn=store._clock)
    return run(disp.dispatch(event, trusted_context=ctx or trusted_context()))


def _apply_mark(store, exp_id, adventurer=ADV, target=TGT):
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer, target_id=target)
    out = _dispatch(store, ev)
    assert out.result.code is RC.SUCCESS
    return out


def _start_drain(store, exp_id, adventurer=ADV, target=TGT, event_id=None):
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer, target_id=target,
                    event_id=event_id)
    return _dispatch(store, ev), ev


def _complete_drain(store, exp_id, drain_id, adventurer=ADV, event_id=None):
    ev = make_event(ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer,
                    drain_execution_id=drain_id, event_id=event_id)
    return _dispatch(store, ev), ev


def _get_state(store, exp_id):
    return run(store.get_state(exp_id)).state


def _cs(store, exp_id, adventurer=ADV):
    return _get_state(store, exp_id).class_state_for(adventurer)


# ═══════ Full flow ═══════
def test_d01_full_flow_start_complete(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, _ = _start_drain(store, exp_id)
    assert out.result.code is RC.DRAIN_STARTED
    drain_id = out.result.drain_execution_id
    assert drain_id and drain_id.startswith("drn-")
    out2, _ = _complete_drain(store, exp_id, drain_id)
    assert out2.result.code is RC.DRAIN_COMPLETED
    assert out2.result.fragment_gain_applied == 1
    cs = _cs(store, exp_id)
    assert cs.fragment_count == 1
    drains = coerce_drains(cs)
    assert drains[0].runtime_status is DrainStatus.RESOLVED
    assert drains[0].completion_payload is not None
    # state_version +1 exactly once per event batch (1 create + 3 events)
    st = _get_state(store, exp_id)
    assert st.state_version == 4
    # 3 receipt ORDINARY totali (mark + start + complete) · MAI un secondo
    # slot per il completion payload (B2B2Q07)
    assert len(st.processed_event_keys) == 3


def test_d02_start_replay_returns_prior_execution_id(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, ev = _start_drain(store, exp_id, event_id="evt-start-fixed")
    assert out.result.code is RC.DRAIN_STARTED
    prior_id = out.result.drain_execution_id
    replay = _dispatch(store, ev)  # stesso event_id + payload_hash
    assert replay.result.code is RC.DEDUPLICATED_NO_OP
    assert replay.result.drain_execution_id == prior_id  # B2B2Q01 replay
    cs = _cs(store, exp_id)
    assert len(coerce_drains(cs)) == 1  # nessun nuovo Drain


def test_d03_payload_mismatch_rejected(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, ev = _start_drain(store, exp_id, event_id="evt-start-fixed")
    assert out.result.code is RC.DRAIN_STARTED
    tampered = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                          source_adventurer_id=ADV, target_id="target-other",
                          event_id="evt-start-fixed")
    out2 = _dispatch(store, tampered)
    assert out2.result.code is RC.EVENT_ID_PAYLOAD_MISMATCH


def test_d04_duplicate_completion_no_double_fragment(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, _ = _start_drain(store, exp_id)
    drain_id = out.result.drain_execution_id
    out2, _ = _complete_drain(store, exp_id, drain_id, event_id="evt-c1")
    assert out2.result.code is RC.DRAIN_COMPLETED
    # retry con STESSO event → dedup no-op
    replay = _dispatch(store, make_event(
        ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_id, event_id="evt-c1"))
    assert replay.result.code is RC.DEDUPLICATED_NO_OP
    # completion con NUOVO event id → DRAIN_ALREADY_COMPLETED · no mutation
    out3, _ = _complete_drain(store, exp_id, drain_id, event_id="evt-c2")
    assert out3.result.code is RC.DRAIN_ALREADY_COMPLETED
    assert _cs(store, exp_id).fragment_count == 1


def test_d05_race_cancel_first_then_complete(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, _ = _start_drain(store, exp_id)
    drain_id = out.result.drain_execution_id
    cancel = _dispatch(store, make_event(
        ClassEventType.CANCEL_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_id))
    assert cancel.result.code is RC.DRAIN_CANCELLED
    out2, _ = _complete_drain(store, exp_id, drain_id)
    assert out2.result.code is RC.DRAIN_ALREADY_CANCELLED
    assert _cs(store, exp_id).fragment_count == 0  # no Fragment (B2B2Q10)


def test_d06_race_complete_first_then_cancel(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, _ = _start_drain(store, exp_id)
    drain_id = out.result.drain_execution_id
    out2, _ = _complete_drain(store, exp_id, drain_id)
    assert out2.result.code is RC.DRAIN_COMPLETED
    cancel = _dispatch(store, make_event(
        ClassEventType.CANCEL_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_id))
    assert cancel.result.code is RC.DRAIN_ALREADY_COMPLETED
    assert _cs(store, exp_id).fragment_count == 1  # Fragment preservato


def test_d07_mark_expiration_during_drain_folds_into_triggering_receipt(
    initialized_state, clock_fn,
):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, _ = _start_drain(store, exp_id)
    drain_id = out.result.drain_execution_id
    receipts_before = len(_get_state(store, exp_id).processed_event_keys)
    clock_fn.advance(11)  # Mark scade (10s)
    out2, _ = _complete_drain(store, exp_id, drain_id)
    assert out2.result.code is RC.MARK_EXPIRED
    assert out2.result.cancellation_reason == "MARK_EXPIRED"
    st = _get_state(store, exp_id)
    cs = st.class_state_for(ADV)
    assert coerce_drains(cs)[0].runtime_status is DrainStatus.CANCELLED
    # B2B2Q14: UNA sola receipt aggiuntiva (folded) · NO seconda receipt
    assert len(st.processed_event_keys) == receipts_before + 1
    assert cs.fragment_count == 0


def test_d08_phase_end_lifecycle_aggregate_single_reserved_receipt(initialized_state):
    store, exp_id = initialized_state
    targets = ["t1", "t2", "t3"]
    drain_ids = []
    for t in targets:
        _apply_mark(store, exp_id, target=t)
        out, _ = _start_drain(store, exp_id, target=t)
        assert out.result.code is RC.DRAIN_STARTED
        drain_ids.append(out.result.drain_execution_id)
    receipts_before = len(_get_state(store, exp_id).processed_event_keys)
    phase_end = _dispatch(store, make_event(
        ClassEventType.PHASE_END.value, expedition_id=exp_id,
        source_adventurer_id=ADV))
    assert phase_end.result.code is RC.SUCCESS
    assert phase_end.result.drains_cancelled_count == 3
    assert set(phase_end.result.cancelled_drain_execution_ids) == set(drain_ids)
    st = _get_state(store, exp_id)
    # ONE reserved lifecycle receipt per l'INTERO batch (B2B2Q11)
    assert len(st.processed_event_keys) == receipts_before + 1
    assert st.processed_event_keys[-1].event_type == "PHASE_END"
    for d in coerce_drains(st.class_state_for(ADV)):
        assert d.runtime_status is DrainStatus.CANCELLED
        assert d.cancellation_reason == "PHASE_ENDED"
    # later completion → rejected (B2B2Q11)
    ctx = trusted_context()
    ctx["phase_ended"] = True
    out2 = _dispatch(store, make_event(
        ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_ids[0]), ctx)
    assert out2.result.code is RC.PHASE_INACTIVE


def test_d09_completion_first_then_phase_end_keeps_fragment(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id, target="t1")
    _apply_mark(store, exp_id, target="t2")
    out1, _ = _start_drain(store, exp_id, target="t1")
    out2, _ = _start_drain(store, exp_id, target="t2")
    comp, _ = _complete_drain(store, exp_id, out1.result.drain_execution_id)
    assert comp.result.code is RC.DRAIN_COMPLETED
    phase_end = _dispatch(store, make_event(
        ClassEventType.PHASE_END.value, expedition_id=exp_id,
        source_adventurer_id=ADV))
    # Cancella SOLO i Drain ancora STARTED
    assert phase_end.result.drains_cancelled_count == 1
    assert phase_end.result.cancelled_drain_execution_ids == (
        out2.result.drain_execution_id,)
    st = _get_state(store, exp_id)
    by_id = {d.drain_execution_id: d for d in coerce_drains(st.class_state_for(ADV))}
    assert by_id[out1.result.drain_execution_id].runtime_status is DrainStatus.RESOLVED


def test_d10_expedition_terminal_rejects_drain_events(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    out, _ = _start_drain(store, exp_id)
    # Terminalizza expedition
    st = _get_state(store, exp_id)
    run(store.compare_and_update(
        expedition_id=exp_id,
        expected_state_version=st.state_version,
        expected_fencing_token=st.fencing_token,
        mutation={"runtime_status": RuntimeStatus.COMPLETED},
    ))
    out2, _ = _complete_drain(store, exp_id, out.result.drain_execution_id)
    assert out2.result.code is RC.EXPEDITION_TERMINAL_REJECTED
    new_start, _ = _start_drain(store, exp_id, target="t-x")
    assert new_start.result.code is RC.EXPEDITION_TERMINAL_REJECTED


def test_d11_phase_inactive_rejects_start(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    ctx = trusted_context()
    ctx["phase_ended"] = True
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    out = _dispatch(store, ev, ctx)
    assert out.result.code is RC.PHASE_INACTIVE


def test_d12_lease_acquisition_failed(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    # Altro worker detiene la lease
    lease = run(store.reserve_writer(
        expedition_id=exp_id, writer_worker_id="w-other", lease_ttl_seconds=60))
    assert lease.code is CasResultCode.SUCCESS
    out, _ = _start_drain(store, exp_id)
    assert out.result.code is RC.LEASE_ACQUISITION_FAILED


def test_d13_stale_fencing_rejected(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    st = _get_state(store, exp_id)
    res = run(store.apply_event_once(
        expedition_id=exp_id,
        event_id=f"evt-{uuid.uuid4().hex[:12]}",
        event_type="START_DRAIN",
        source_adventurer_id=ADV,
        payload_hash="h1",
        expected_state_version=st.state_version,
        expected_fencing_token=st.fencing_token + 99,  # stale/forged token
        mutation={},
    ))
    assert res.code is CasResultCode.STALE_WRITER_REJECTED


def test_d14_retry_limit_reached_on_persistent_cas_conflict(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)

    class _ConflictStore:
        """Proxy: apply_event_once fallisce sempre con STATE_VERSION_CONFLICT."""

        def __init__(self, inner):
            self._inner = inner
            self.apply_calls = 0

        def __getattr__(self, name):
            return getattr(self._inner, name)

        async def apply_event_once(self, **kwargs):
            self.apply_calls += 1
            return CasResult(code=CasResultCode.STATE_VERSION_CONFLICT)

    proxy = _ConflictStore(store)
    disp = ClassTransitionDispatcher(store=proxy, worker_id="w-test", now_fn=store._clock)
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    out = run(disp.dispatch(ev, trusted_context=trusted_context()))
    assert out.result.code is RC.RETRY_LIMIT_REACHED
    assert proxy.apply_calls == 3  # max automatic retries = 3 (B2B2Q12)


def test_d15_receipt_cap_reached_fail_closed(fake_store, clock_fn):
    exp_id = f"exp-{uuid.uuid4().hex[:12]}"
    now = clock_fn()
    filler = tuple(
        EventReceipt(
            event_id=f"evt-fill-{i}", event_type="APPLY_MARK",
            source_adventurer_id=ADV, payload_hash=f"h{i}",
            assigned_event_sequence=i + 1, result_code="SUCCESS",
            state_version_after=i + 2, processed_at="2026-02-01T12:00:00Z",
        )
        for i in range(RECEIPT_CAP_ORDINARY)
    )
    shell = ExpeditionRuntimeState(
        expedition_id=exp_id, state_version=1, fencing_token=0,
        created_at="2026-02-01T12:00:00Z", updated_at="2026-02-01T12:00:00Z",
        expires_at=(now + timedelta(hours=6)).isoformat().replace("+00:00", "Z"),
        runtime_status=RuntimeStatus.ACTIVE,
        adventurer_class_states=(), processed_event_keys=filler,
        last_event_sequence=len(filler),
    )
    assert run(fake_store.create_state(exp_id, shell)).success
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    out = _dispatch(fake_store, ev)
    assert out.result.code is RC.RECEIPT_CAP_REACHED  # no mutation · fail-closed


def test_d16_state_rejection_codes(initialized_state):
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    unknown = f"drn-{uuid.uuid4()}"
    out, _ = _complete_drain(store, exp_id, unknown)
    assert out.result.code is RC.DRAIN_NOT_STARTED
    cancel = _dispatch(store, make_event(
        ClassEventType.CANCEL_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=unknown))
    assert cancel.result.code is RC.DRAIN_NOT_STARTED


def test_d17_start_rejections_via_dispatcher(initialized_state):
    store, exp_id = initialized_state
    # MARK_NOT_FOUND (nessun Mark)
    out, _ = _start_drain(store, exp_id)
    assert out.result.code is RC.MARK_NOT_FOUND
    # TARGET_INVALID (self target)
    _apply_mark(store, exp_id)
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=ADV)
    assert _dispatch(store, ev).result.code is RC.TARGET_INVALID
    # DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR
    ok, _ = _start_drain(store, exp_id)
    assert ok.result.code is RC.DRAIN_STARTED
    dup, _ = _start_drain(store, exp_id)
    assert dup.result.code is RC.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR
    # nessuna mutation dalle rejection
    assert len(coerce_drains(_cs(store, exp_id))) == 1


# ═══════ Feature gating (B2B2Q13) · fail-closed boundaries ═══════
@pytest.fixture
def coordinator(initialized_state):
    store, exp_id = initialized_state
    return ExpeditionRuntimeCoordinator(store, "orbus_r16_rt2b_test"), store, exp_id


class _CountingStore:
    def __init__(self, inner):
        self._inner = inner
        self.calls = 0

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if callable(attr):
            def _wrapper(*a, **k):
                self.calls += 1
                return attr(*a, **k)
            return _wrapper
        return attr


def test_d18_drain_flag_off_zero_db_zero_audit_zero_mutation(
    initialized_state, caplog,
):
    store, exp_id = initialized_state
    counting = _CountingStore(store)
    coord = ExpeditionRuntimeCoordinator(counting, "orbus_r16_rt2b_test")
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    ctx = trusted_context()
    ctx["drain_feature_enabled"] = False  # kill-switch Drain OFF
    with caplog.at_level(logging.INFO, logger="orbus.rt2_b_2a.wiring"):
        out = run(coord.dispatch_class_state_event(ev, ctx))
    assert out.result.code is RC.FEATURE_DISABLED
    assert counting.calls == 0  # Drain DB calls = 0
    assert not [r for r in caplog.records if "cdv_drain" in r.getMessage()]  # audit = 0
    assert _cs(store, exp_id) is None  # mutations = 0


def test_d19_drain_flag_off_does_not_disable_mark_fragment(initialized_state):
    store, exp_id = initialized_state
    coord = ExpeditionRuntimeCoordinator(store, "orbus_r16_rt2b_test")
    ctx = trusted_context()
    ctx["drain_feature_enabled"] = False
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    out = run(coord.dispatch_class_state_event(ev, ctx))
    assert out.result.code is RC.SUCCESS  # kill-switch surgical


def test_d20_non_test_user_fail_closed(coordinator):
    coord, store, exp_id = coordinator
    _apply_mark(store, exp_id)
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    ctx = trusted_context(test_user_verified=False)
    ctx["drain_feature_enabled"] = True
    out = run(coord.dispatch_class_state_event(ev, ctx))
    assert out.result.code is RC.TEST_USER_BOUNDARY_VIOLATION
    assert len(coerce_drains(_cs(store, exp_id))) == 0


def test_d21_db_not_allowlisted_rejected(initialized_state):
    store, exp_id = initialized_state
    coord = ExpeditionRuntimeCoordinator(store, "orbus_r16")  # FORBIDDEN db
    assert coord.is_target_db_allowlisted is False
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    ctx = trusted_context()
    ctx["drain_feature_enabled"] = True
    out = run(coord.dispatch_class_state_event(ev, ctx))
    assert out.result.code is RC.DB_NOT_ALLOWLISTED


def test_d22_composite_gate_feature_disabled(coordinator):
    coord, store, exp_id = coordinator
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    ctx = trusted_context(feature_enabled=False)  # transient/class OFF
    ctx["drain_feature_enabled"] = True
    out = run(coord.dispatch_class_state_event(ev, ctx))
    assert out.result.code is RC.FEATURE_DISABLED


def test_d23_env_flag_default_off(coordinator):
    """Senza override nel trusted_context il flag env (default OFF) governa."""
    from app.stats.runtime import feature_flags as ff
    ff.reset_cache()
    assert ff.is_enabled("cdv_drain_transitions_enabled") is False
    coord, store, exp_id = coordinator
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT)
    out = run(coord.dispatch_class_state_event(ev, trusted_context()))
    assert out.result.code is RC.FEATURE_DISABLED


# ═══════ Audit mapping (B2B2Q15 · 10 event ids) ═══════
@pytest.fixture
def audit_recorder(monkeypatch):
    """Registra gli audit event ids emessi dal coordinator (B2B2Q15)."""
    import app.stats.runtime.wiring.coordinator as coord_mod
    recorded: list[str] = []
    real_emit = coord_mod.emit_audit_event

    def _spy(audit_id, record):
        recorded.append(audit_id)
        return real_emit(audit_id, record)

    monkeypatch.setattr(coord_mod, "emit_audit_event", _spy)
    return recorded


def test_d24_audit_ids_full_lifecycle(coordinator, audit_recorder):
    coord, store, exp_id = coordinator
    ctx = trusted_context()
    ctx["drain_feature_enabled"] = True

    def _go(ev):
        return run(coord.dispatch_class_state_event(ev, ctx))

    # Mark via coordinator (wall-clock coerente con il dispatcher interno)
    assert _go(make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                          source_adventurer_id=ADV, target_id=TGT)
               ).result.code is RC.SUCCESS
    # started
    out = _go(make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                         source_adventurer_id=ADV, target_id=TGT))
    drain_id = out.result.drain_execution_id
    # start_rejected (pair hard-lock)
    _go(make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                   source_adventurer_id=ADV, target_id=TGT))
    # completed (+ fragment_batch_applied supplementare)
    _go(make_event(ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
                   source_adventurer_id=ADV, drain_execution_id=drain_id))
    # duplicate_completion
    _go(make_event(ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
                   source_adventurer_id=ADV, drain_execution_id=drain_id))
    # cancellation_rejected (già completato)
    _go(make_event(ClassEventType.CANCEL_DRAIN.value, expedition_id=exp_id,
                   source_adventurer_id=ADV, drain_execution_id=drain_id))
    # completion_rejected (unknown id)
    _go(make_event(ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
                   source_adventurer_id=ADV, drain_execution_id=f"drn-{uuid.uuid4()}"))
    # cancelled (nuovo drain su nuovo target)
    _go(make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                   source_adventurer_id=ADV, target_id="t2"))
    out2 = _go(make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                          source_adventurer_id=ADV, target_id="t2"))
    _go(make_event(ClassEventType.CANCEL_DRAIN.value, expedition_id=exp_id,
                   source_adventurer_id=ADV,
                   drain_execution_id=out2.result.drain_execution_id))
    ids = audit_recorder
    assert "cdv_drain_started" in ids
    assert "cdv_drain_start_rejected" in ids
    assert "cdv_drain_completed" in ids
    assert "cdv_drain_fragment_batch_applied" in ids
    assert "cdv_drain_duplicate_completion" in ids
    assert "cdv_drain_cancellation_rejected" in ids
    assert "cdv_drain_completion_rejected" in ids
    assert "cdv_drain_cancelled" in ids


def test_d25_audit_overflow_and_conflict_ids(coordinator, audit_recorder):
    coord, store, exp_id = coordinator
    ctx = trusted_context()
    ctx["drain_feature_enabled"] = True

    def _go(ev):
        return run(coord.dispatch_class_state_event(ev, ctx))

    # Porta fragment_count a 5 (cap) con 5 drain completions
    for i in range(5):
        t = f"t-{i}"
        _go(make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                       source_adventurer_id=ADV, target_id=t))
        out = _go(make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                             source_adventurer_id=ADV, target_id=t))
        _go(make_event(ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
                       source_adventurer_id=ADV,
                       drain_execution_id=out.result.drain_execution_id))
    assert _cs(store, exp_id).fragment_count == 5
    # 6° completion → overflow discarded. Riusa il Mark attivo di t-0
    # (il Drain precedente è RESOLVED · terminale · non blocca il nuovo start)
    out = _go(make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                         source_adventurer_id=ADV, target_id="t-0"))
    assert out.result.code is RC.DRAIN_STARTED
    ovf = _go(make_event(ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
                         source_adventurer_id=ADV,
                         drain_execution_id=out.result.drain_execution_id))
    assert ovf.result.code is RC.DRAIN_COMPLETED
    assert ovf.result.fragment_overflow_discarded == 1
    # conflict id: lease detenuta da altro worker
    lease = run(store.reserve_writer(
        expedition_id=exp_id, writer_worker_id="w-other", lease_ttl_seconds=60))
    assert lease.code is CasResultCode.SUCCESS
    _apply_mark_blocked = _go(make_event(
        ClassEventType.START_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id="t-1"))
    assert _apply_mark_blocked.result.code is RC.LEASE_ACQUISITION_FAILED
    ids = audit_recorder
    assert "cdv_drain_fragment_overflow_discarded" in ids
    assert "cdv_drain_transition_conflict" in ids


# ═══════ Legacy invariance ═══════
def test_d26_legacy_mark_fragment_flow_unchanged(initialized_state):
    """Legacy response/reward invariance: il percorso Mark+GAIN_FRAGMENT
    (trusted fixture RT2-B-2B-1) resta byte-compatibile con il gate Drain
    presente ma OFF."""
    from tests.effect_engine.transitions.conftest import make_trusted_receipt
    store, exp_id = initialized_state
    _apply_mark(store, exp_id)
    receipt = make_trusted_receipt(source_adventurer_id=ADV, target_id=TGT,
                                   expedition_id=exp_id)
    ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, amount=1,
                    trusted_drain_receipt=receipt)
    out = _dispatch(store, ev)
    assert out.result.code is RC.SUCCESS
    assert out.result.fragment_count_after == 1
    # segment legacy apre con prefisso legacy "seg-" (invariato)
    assert out.result.resource_segment_id.startswith("seg-")
    assert out.result.success is True
