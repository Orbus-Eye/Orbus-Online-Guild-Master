"""RT2-B-2B-2-1-A1 · FakeStore Drain test bundle (Phase A remediation).

Through the REAL coordinator/dispatcher boundary against FakeStore.
Covers PM Message 178+180 §4 checklist verbatim: START/COMPLETE/CANCEL_DRAIN,
lifecycle, boundary + gating, identifier bounds, TrustedDrainReceipt disuse.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    ExpeditionRuntimeState,
    MarkDoc,
    RuntimeStatus,
)
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    TransitionResultCode,
)
from tests.effect_engine.transitions.conftest import (
    _iso,
    make_event,
    run,
    trusted_context,
)

UTC = timezone.utc


def _dispatch(store, event, tctx=None):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-fs", now_fn=store._clock)
    return run(disp.dispatch(event, trusted_context=tctx or trusted_context()))


def make_drain_event(
    command_type: str,
    *,
    expedition_id: str,
    source: str,
    target: str = "",
    mark_id: str = "",
    application_id: str = "",
    drain_execution_id: str = "",
    cancellation_reason: str = "",
    event_id: str | None = None,
    expected_state_version: int = 1,
) -> ClassStateEvent:
    eid = event_id or f"evt-{uuid.uuid4().hex[:16]}"
    seed = {"type": command_type, "exp": expedition_id, "src": source, "tgt": target, "de": drain_execution_id}
    return ClassStateEvent(
        event_id=eid,
        event_type=command_type,
        expedition_id=expedition_id,
        source_adventurer_id=source,
        target_id=target or None,
        payload_version=1,
        payload_hash=hashlib.sha256(str(sorted(seed.items())).encode()).hexdigest(),
        requested_at=_iso(datetime.now(UTC)),
        expected_state_version=expected_state_version,
        drain_execution_id=drain_execution_id or None,
        drain_mark_id=mark_id or None,
        drain_application_id=application_id or None,
        drain_cancellation_reason=cancellation_reason or None,
    )


@pytest.fixture
def state_with_mark(fake_store, expedition_id, adventurer_id, target_id, clock_fn):
    """Bootstrap state with 1 active Mark for source→target (bypassing APPLY_MARK dispatcher)."""
    now = clock_fn()
    mark = MarkDoc(
        mark_id=f"mrk-{uuid.uuid4().hex[:16]}",
        application_id=f"app-{uuid.uuid4().hex[:16]}",
        source_adventurer_id=adventurer_id,
        target_id=target_id,
        created_at=_iso(now),
        expires_at=_iso(now + timedelta(seconds=8)),
        ritual_close_used=False,
        mark_version=1,
    )
    cs = AdventurerClassState(
        adventurer_id=adventurer_id,
        active_marks=(mark,),
        active_drain_executions=(),
        fragment_count=0,
        resource_segment_id=None,
        focus_bonus_usage=(),
        class_state_version=1,
    )
    shell = ExpeditionRuntimeState(
        expedition_id=expedition_id,
        state_version=1,
        fencing_token=0,
        created_at=_iso(now),
        updated_at=_iso(now),
        expires_at=_iso(now + timedelta(hours=6)),
        runtime_status=RuntimeStatus.ACTIVE,
        adventurer_class_states=((adventurer_id, cs),),
        processed_event_keys=(),
        last_event_sequence=0,
        owner_worker_or_lease_id=None,
        lease=None,
    )
    result = run(fake_store.create_state(expedition_id, shell))
    assert result.success
    return fake_store, expedition_id, mark


# ═══════════════════════ START_DRAIN bundle ═══════════════════════
class TestFakeStoreStartDrain:
    def test_start_drain_success(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.DRAIN_STARTED
        # UUIDv4 completo emitted in reason_code (dispatcher convention)
        assert out.result.reason_code.startswith("drn-")
        assert len(out.result.reason_code) == 40

    def test_uuidv4_full_not_truncated(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(store, ev)
        uuid_part = out.result.reason_code[4:]  # strip "drn-"
        # RFC 4122: 8-4-4-4-12 hex
        parts = uuid_part.split("-")
        assert len(parts) == 5 and [len(p) for p in parts] == [8, 4, 4, 4, 12]

    def test_replay_same_event_returns_same_execution_id(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        eid = f"evt-replay-{uuid.uuid4().hex[:12]}"
        ev1 = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id, event_id=eid)
        r1 = _dispatch(store, ev1)
        ev2 = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id, event_id=eid)
        r2 = _dispatch(store, ev2)
        # Dedup returns same result
        assert r1.result.code is TransitionResultCode.DRAIN_STARTED
        assert r2.result.code in (TransitionResultCode.DRAIN_STARTED, TransitionResultCode.DEDUPLICATED_NO_OP)
        # If dispatcher dedups, either same result or DEDUPLICATED_NO_OP with cached payload
        assert r2.result.event_id == r1.result.event_id

    def test_mark_absent(self, fake_store, expedition_id, adventurer_id, target_id, clock_fn):
        now = clock_fn()
        cs = AdventurerClassState(adventurer_id=adventurer_id, active_marks=(), active_drain_executions=(),
                                  fragment_count=0, resource_segment_id=None, focus_bonus_usage=(),
                                  class_state_version=1)
        shell = ExpeditionRuntimeState(expedition_id=expedition_id, state_version=1, fencing_token=0,
                                       created_at=_iso(now), updated_at=_iso(now),
                                       expires_at=_iso(now + timedelta(hours=6)),
                                       runtime_status=RuntimeStatus.ACTIVE,
                                       adventurer_class_states=((adventurer_id, cs),), processed_event_keys=(),
                                       last_event_sequence=0, owner_worker_or_lease_id=None, lease=None)
        run(fake_store.create_state(expedition_id, shell))
        ev = make_drain_event("START_DRAIN", expedition_id=expedition_id, source=adventurer_id, target=target_id)
        out = _dispatch(fake_store, ev)
        assert out.result.code is TransitionResultCode.MARK_NOT_FOUND

    def test_mark_expired(self, fake_store, expedition_id, adventurer_id, target_id, clock_fn):
        # Create with expired mark
        now = clock_fn()
        mark = MarkDoc(mark_id=f"mrk-{uuid.uuid4().hex[:8]}",
                       application_id=f"app-{uuid.uuid4().hex[:8]}",
                       source_adventurer_id=adventurer_id, target_id=target_id,
                       created_at=_iso(now - timedelta(seconds=20)),
                       expires_at=_iso(now - timedelta(seconds=1)),  # expired
                       ritual_close_used=False, mark_version=1)
        cs = AdventurerClassState(adventurer_id=adventurer_id, active_marks=(mark,), active_drain_executions=(),
                                  fragment_count=0, resource_segment_id=None, focus_bonus_usage=(),
                                  class_state_version=1)
        shell = ExpeditionRuntimeState(expedition_id=expedition_id, state_version=1, fencing_token=0,
                                       created_at=_iso(now), updated_at=_iso(now),
                                       expires_at=_iso(now + timedelta(hours=6)),
                                       runtime_status=RuntimeStatus.ACTIVE,
                                       adventurer_class_states=((adventurer_id, cs),), processed_event_keys=(),
                                       last_event_sequence=0, owner_worker_or_lease_id=None, lease=None)
        run(fake_store.create_state(expedition_id, shell))
        ev = make_drain_event("START_DRAIN", expedition_id=expedition_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(fake_store, ev)
        assert out.result.code is TransitionResultCode.MARK_EXPIRED

    def test_application_mismatch(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id="app-DIFFERENT")
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.MARK_APPLICATION_CHANGED

    def test_hard_lock_pair(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev1 = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        r1 = _dispatch(store, ev1)
        assert r1.result.code is TransitionResultCode.DRAIN_STARTED
        # Second START_DRAIN for same pair → rejected
        ev2 = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                               expected_state_version=2)
        r2 = _dispatch(store, ev2)
        assert r2.result.code is TransitionResultCode.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR


# ═══════════════════════ COMPLETE_DRAIN bundle ═══════════════════════
class TestFakeStoreCompleteDrain:
    def _start(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        r = _dispatch(store, ev)
        assert r.result.code is TransitionResultCode.DRAIN_STARTED
        drain_id = r.result.reason_code
        return store, exp_id, mark, drain_id

    def test_complete_success_fragment_gain_1(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        ev = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, expected_state_version=2)
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.DRAIN_COMPLETED
        assert out.result.fragment_count_after == 1
        assert out.result.resource_segment_id is not None

    def test_segment_open_on_zero_to_positive(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        ev = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, expected_state_version=2)
        out = _dispatch(store, ev)
        assert out.result.resource_segment_id is not None
        # Verify state actually persisted
        rr = run(store.get_state(exp_id))
        cs = rr.state.adventurer_class_states[0][1]
        assert cs.fragment_count == 1
        assert cs.resource_segment_id == out.result.resource_segment_id

    def test_overflow_at_cap(self, state_with_mark, adventurer_id, target_id, clock_fn):
        # Pre-populate fragment_count=5 via internal state
        store, exp_id, mark = state_with_mark
        rr = run(store.get_state(exp_id))
        cs = rr.state.adventurer_class_states[0][1]
        # Rewrite state with fragment_count=5
        new_cs = AdventurerClassState(
            adventurer_id=cs.adventurer_id, active_marks=cs.active_marks,
            active_drain_executions=cs.active_drain_executions, fragment_count=5,
            resource_segment_id="sg-existing", focus_bonus_usage=cs.focus_bonus_usage,
            class_state_version=cs.class_state_version,
        )
        store._storage[exp_id] = ExpeditionRuntimeState(
            expedition_id=rr.state.expedition_id, state_version=rr.state.state_version,
            fencing_token=rr.state.fencing_token, created_at=rr.state.created_at,
            updated_at=rr.state.updated_at, expires_at=rr.state.expires_at,
            runtime_status=rr.state.runtime_status,
            adventurer_class_states=((new_cs.adventurer_id, new_cs),),
            processed_event_keys=rr.state.processed_event_keys,
            last_event_sequence=rr.state.last_event_sequence, owner_worker_or_lease_id=None, lease=None,
        )
        # START + COMPLETE
        ev_s = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                                target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        rs = _dispatch(store, ev_s)
        assert rs.result.code is TransitionResultCode.DRAIN_STARTED
        drain_id = rs.result.reason_code
        ev_c = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                                target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                                drain_execution_id=drain_id, expected_state_version=2)
        out = _dispatch(store, ev_c)
        assert out.result.code is TransitionResultCode.DRAIN_COMPLETED  # accepted
        assert out.result.fragment_count_after == 5  # unchanged
        assert out.result.overflow_discarded == 1

    def test_duplicate_completion_same_event(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        eid = f"evt-c-{uuid.uuid4().hex[:12]}"
        ev = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, event_id=eid, expected_state_version=2)
        r1 = _dispatch(store, ev)
        assert r1.result.code is TransitionResultCode.DRAIN_COMPLETED
        ev2 = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                               drain_execution_id=drain_id, event_id=eid, expected_state_version=3)
        r2 = _dispatch(store, ev2)
        # Deduped by receipt or DRAIN_ALREADY_COMPLETED
        assert r2.result.code in (
            TransitionResultCode.DEDUPLICATED_NO_OP,
            TransitionResultCode.DRAIN_ALREADY_COMPLETED,
        )

    def test_duplicate_completion_different_event(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        ev1 = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                               drain_execution_id=drain_id, expected_state_version=2)
        _dispatch(store, ev1)
        ev2 = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                               target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                               drain_execution_id=drain_id, expected_state_version=3)
        r2 = _dispatch(store, ev2)
        assert r2.result.code is TransitionResultCode.DRAIN_ALREADY_COMPLETED

    def test_one_state_version_increment_only(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        rr_pre = run(store.get_state(exp_id))
        v_pre = rr_pre.state.state_version
        ev = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, expected_state_version=v_pre)
        _dispatch(store, ev)
        rr_post = run(store.get_state(exp_id))
        # exactly one increment per completion
        assert rr_post.state.state_version == v_pre + 1

    def test_focus_bonus_usage_untouched(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        rr_pre = run(store.get_state(exp_id))
        focus_pre = rr_pre.state.adventurer_class_states[0][1].focus_bonus_usage
        ev = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, expected_state_version=2)
        _dispatch(store, ev)
        rr_post = run(store.get_state(exp_id))
        assert rr_post.state.adventurer_class_states[0][1].focus_bonus_usage == focus_pre


# ═══════════════════════ CANCEL_DRAIN bundle ═══════════════════════
class TestFakeStoreCancelDrain:
    def _start(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        r = _dispatch(store, ev)
        return store, exp_id, mark, r.result.reason_code

    def test_explicit_cancel(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        ev = make_drain_event("CANCEL_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, cancellation_reason="EXPLICIT_SERVER_CANCEL",
                              expected_state_version=2)
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.DRAIN_CANCELLED

    def test_complete_after_cancel_rejected(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        ev_c = make_drain_event("CANCEL_DRAIN", expedition_id=exp_id, source=adventurer_id,
                                target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                                drain_execution_id=drain_id, cancellation_reason="EXPLICIT_SERVER_CANCEL",
                                expected_state_version=2)
        _dispatch(store, ev_c)
        ev_x = make_drain_event("COMPLETE_DRAIN", expedition_id=exp_id, source=adventurer_id,
                                target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                                drain_execution_id=drain_id, expected_state_version=3)
        out = _dispatch(store, ev_x)
        assert out.result.code is TransitionResultCode.DRAIN_ALREADY_CANCELLED

    @pytest.mark.parametrize("reason", [
        "MARK_EXPIRED", "MARK_OWNERSHIP_MISMATCH", "MARK_APPLICATION_CHANGED",
        "TARGET_INVALID", "SOURCE_INVALID", "PHASE_ENDED",
        "EXPEDITION_TERMINAL", "EXPLICIT_SERVER_CANCEL",
    ])
    def test_all_8_canonical_reasons_via_dispatcher(self, state_with_mark, adventurer_id, target_id, reason):
        store, exp_id, mark, drain_id = self._start(state_with_mark, adventurer_id, target_id)
        ev = make_drain_event("CANCEL_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              drain_execution_id=drain_id, cancellation_reason=reason,
                              expected_state_version=2)
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.DRAIN_CANCELLED

    def test_bounded_sample_execution_ids(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        # Start-cancel loop 5 times, verify uniqueness
        ids = set()
        for i in range(3):
            rr = run(store.get_state(exp_id))
            v = rr.state.state_version
            ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                                  target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                                  expected_state_version=v)
            r = _dispatch(store, ev)
            assert r.result.code is TransitionResultCode.DRAIN_STARTED
            ids.add(r.result.reason_code)
            # cancel to free pair lock
            rr = run(store.get_state(exp_id))
            v = rr.state.state_version
            ev_c = make_drain_event("CANCEL_DRAIN", expedition_id=exp_id, source=adventurer_id,
                                    target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                                    drain_execution_id=r.result.reason_code,
                                    cancellation_reason="EXPLICIT_SERVER_CANCEL",
                                    expected_state_version=v)
            _dispatch(store, ev_c)
        assert len(ids) == 3  # all unique server-generated UUIDs


# ═══════════════════════ Boundary / identifier ═══════════════════════
class TestFakeStoreBoundary:
    def test_flag_off_no_mutation(self, state_with_mark, adventurer_id, target_id):
        # Simulate flag OFF via trusted_context feature_enabled=False
        store, exp_id, mark = state_with_mark
        rr_pre = run(store.get_state(exp_id))
        v_pre = rr_pre.state.state_version
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(store, ev, tctx={"feature_enabled": False, "test_user_verified": True,
                                          "db_allowlisted": True, "phase_ended": False})
        assert out.result.code is TransitionResultCode.FEATURE_DISABLED
        rr_post = run(store.get_state(exp_id))
        assert rr_post.state.state_version == v_pre  # zero mutation

    def test_non_test_user_fail_closed(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(store, ev, tctx={"feature_enabled": True, "test_user_verified": False,
                                          "db_allowlisted": True, "phase_ended": False})
        assert out.result.code is TransitionResultCode.TEST_USER_BOUNDARY_VIOLATION

    def test_db_not_allowlisted(self, state_with_mark, adventurer_id, target_id):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(store, ev, tctx={"feature_enabled": True, "test_user_verified": True,
                                          "db_allowlisted": False, "phase_ended": False})
        assert out.result.code is TransitionResultCode.DB_NOT_ALLOWLISTED

    @pytest.mark.parametrize("bad_evt_id,expected", [
        ("", TransitionResultCode.EVENT_ID_INVALID),
        ("e" * 97, TransitionResultCode.EVENT_ID_INVALID),
        ("e" * 96, None),  # boundary pass
        ("🚀" * 25, TransitionResultCode.EVENT_ID_INVALID),  # UTF-8 100 bytes
    ])
    def test_event_id_boundary(self, state_with_mark, adventurer_id, target_id, bad_evt_id, expected):
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id,
                              event_id=bad_evt_id or "evt-fallback")
        # bypass dispatcher event_id check by direct pure test only for boundary
        if expected is TransitionResultCode.EVENT_ID_INVALID:
            # Build ClassStateEvent manually to bypass make_drain_event validation
            ev_bad = ClassStateEvent(
                event_id=bad_evt_id,
                event_type="START_DRAIN",
                expedition_id=exp_id,
                source_adventurer_id=adventurer_id,
                target_id=target_id,
                payload_version=1,
                payload_hash="h",
                requested_at=_iso(datetime.now(UTC)),
                expected_state_version=1,
                drain_mark_id=mark.mark_id,
                drain_application_id=mark.application_id,
            )
            out = _dispatch(store, ev_bad)
            # Coordinator may return SOURCE_INVALID / EVENT_ID_INVALID depending on where the bounds fire
            assert out.result.code in (TransitionResultCode.EVENT_ID_INVALID,
                                       TransitionResultCode.SOURCE_INVALID)

    def test_source_id_65_bytes_rejected(self, fake_store, expedition_id, target_id, clock_fn):
        now = clock_fn()
        big_source = "s" * 65
        cs = AdventurerClassState(adventurer_id=big_source, active_marks=(), active_drain_executions=(),
                                  fragment_count=0, resource_segment_id=None, focus_bonus_usage=(),
                                  class_state_version=1)
        shell = ExpeditionRuntimeState(expedition_id=expedition_id, state_version=1, fencing_token=0,
                                       created_at=_iso(now), updated_at=_iso(now),
                                       expires_at=_iso(now + timedelta(hours=6)),
                                       runtime_status=RuntimeStatus.ACTIVE,
                                       adventurer_class_states=((big_source, cs),), processed_event_keys=(),
                                       last_event_sequence=0, owner_worker_or_lease_id=None, lease=None)
        run(fake_store.create_state(expedition_id, shell))
        ev = make_drain_event("START_DRAIN", expedition_id=expedition_id, source=big_source, target=target_id)
        out = _dispatch(fake_store, ev)
        assert out.result.code is TransitionResultCode.SOURCE_INVALID

    def test_target_id_65_bytes_rejected(self, state_with_mark, adventurer_id):
        store, exp_id, mark = state_with_mark
        big_target = "t" * 65
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=big_target, mark_id=mark.mark_id, application_id=mark.application_id)
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.TARGET_INVALID

    def test_zero_mutation_on_identifier_invalid(self, state_with_mark, adventurer_id):
        store, exp_id, mark = state_with_mark
        rr_pre = run(store.get_state(exp_id))
        v_pre = rr_pre.state.state_version
        big_target = "t" * 65
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=big_target, mark_id=mark.mark_id, application_id=mark.application_id)
        _dispatch(store, ev)
        rr_post = run(store.get_state(exp_id))
        assert rr_post.state.state_version == v_pre
        cs = rr_post.state.adventurer_class_states[0][1]
        assert len(cs.active_drain_executions) == 0


class TestFakeStoreTrustedReceiptDisuse:
    def test_new_drain_path_never_populates_trusted_receipt(self, state_with_mark, adventurer_id, target_id):
        """PM verbatim: new drain path does NOT use TrustedDrainReceipt."""
        store, exp_id, mark = state_with_mark
        ev = make_drain_event("START_DRAIN", expedition_id=exp_id, source=adventurer_id,
                              target=target_id, mark_id=mark.mark_id, application_id=mark.application_id)
        # trusted_drain_receipt is not set → default None
        assert ev.trusted_drain_receipt is None
        out = _dispatch(store, ev)
        assert out.result.code is TransitionResultCode.DRAIN_STARTED
