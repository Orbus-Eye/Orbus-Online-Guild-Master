"""RT2-B-2B-1 · Atomicity, gating, invariance tests (items 23-37)."""
from __future__ import annotations

import hashlib
import uuid

from app.stats.runtime.state_store.models import (
    EventReceipt,
    ExpeditionRuntimeState,
    RuntimeStatus,
)
from app.stats.runtime.state_store.results import CasResultCode
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    TransitionResultCode,
)
from app.stats.runtime.transitions.state_machine import (
    RECEIPT_CAP_ORDINARY,
    RECEIPT_CAP_RESERVED,
    RECEIPT_CAP_TOTAL,
    STATE_DOC_MAX_BYTES,
    would_receipt_be_accepted,
)
from tests.effect_engine.transitions.conftest import (
    make_event,
    make_trusted_receipt,
    run,
    trusted_context,
)


def _dispatch(store, event, *, ctx: dict | None = None):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-test", now_fn=store._clock)
    return run(disp.dispatch(event, trusted_context=ctx or trusted_context()))


# ═══════════════════════ Event ordering + Dedup (23-25) ═══════════════════════

def test_23_event_ordering_per_expedition(initialized_state, adventurer_id):
    store, exp_id = initialized_state
    seqs = []
    for i in range(4):
        ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                        source_adventurer_id=adventurer_id, target_id=f"target-{i}")
        r = _dispatch(store, ev)
        assert r.result.code is TransitionResultCode.SUCCESS
        seqs.append(r.result.assigned_event_sequence)
    assert seqs == [1, 2, 3, 4]


def test_24_same_id_replay_dedup(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id)
    r1 = _dispatch(store, ev)
    assert r1.result.code is TransitionResultCode.SUCCESS
    r2 = _dispatch(store, ev)
    assert r2.result.code is TransitionResultCode.DEDUPLICATED_NO_OP
    assert r2.result.assigned_event_sequence == r1.result.assigned_event_sequence


def test_25_same_id_payload_mismatch(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id,
                    event_id="fixed-evt-id")
    r1 = _dispatch(store, ev)
    assert r1.result.code is TransitionResultCode.SUCCESS
    ev2 = ClassStateEvent(
        event_id="fixed-evt-id",
        event_type=ClassEventType.APPLY_MARK.value,
        expedition_id=exp_id,
        source_adventurer_id=adventurer_id,
        target_id="target-DIFFERENT",
        payload_version=1,
        payload_hash="f" * 64,
        requested_at="2026-02-01T12:00:00Z",
        expected_state_version=1,
        amount=0,
    )
    r2 = _dispatch(store, ev2)
    assert r2.result.code is TransitionResultCode.EVENT_ID_PAYLOAD_MISMATCH


# ═══════════════════════ Receipt policy (26-29) ═══════════════════════

def test_26_receipt_ordinary_cap_pure():
    receipts = tuple(
        EventReceipt(
            event_id=f"e{i}", event_type=ClassEventType.APPLY_MARK.value,
            source_adventurer_id="a", payload_hash="h", assigned_event_sequence=i,
            result_code="SUCCESS", state_version_after=i, processed_at="t",
        )
        for i in range(RECEIPT_CAP_ORDINARY)
    )
    ok, code = would_receipt_be_accepted(receipts, ClassEventType.APPLY_MARK.value)
    assert not ok
    assert code is TransitionResultCode.RECEIPT_CAP_REACHED


def test_27_receipt_reserved_cap_pure():
    reserved_receipts = tuple(
        EventReceipt(
            event_id=f"r{i}", event_type=ClassEventType.PHASE_END.value,
            source_adventurer_id="a", payload_hash="h", assigned_event_sequence=i,
            result_code="SUCCESS", state_version_after=i, processed_at="t",
        )
        for i in range(RECEIPT_CAP_RESERVED)
    )
    ok, code = would_receipt_be_accepted(reserved_receipts, ClassEventType.PHASE_END.value)
    assert not ok
    assert code is TransitionResultCode.RESERVED_CAPACITY_EXHAUSTED
    ok2, _ = would_receipt_be_accepted(reserved_receipts, ClassEventType.APPLY_MARK.value)
    assert ok2


def test_28_no_eviction(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id,
                    event_id="pin-evt-01")
    _dispatch(store, ev)
    read = run(store.get_state(exp_id))
    assert len(read.state.processed_event_keys) == 1
    for i in range(4):
        ev2 = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                         source_adventurer_id=adventurer_id, target_id=f"t{i}")
        _dispatch(store, ev2)
    read2 = run(store.get_state(exp_id))
    keys = [r.event_id for r in read2.state.processed_event_keys]
    assert "pin-evt-01" in keys


def test_29_state_size_stress_under_256_kib():
    receipts = tuple(
        EventReceipt(
            event_id=f"evt-{uuid.uuid4().hex[:20]}",
            event_type=ClassEventType.APPLY_MARK.value,
            source_adventurer_id=f"adv-{i % 5:02d}",
            payload_hash=hashlib.sha256(str(i).encode()).hexdigest(),
            assigned_event_sequence=i,
            result_code="SUCCESS",
            state_version_after=i + 1,
            processed_at="2026-02-01T12:00:00Z",
        )
        for i in range(RECEIPT_CAP_TOTAL)
    )
    st = ExpeditionRuntimeState(
        expedition_id="exp-stress",
        state_version=RECEIPT_CAP_TOTAL,
        created_at="2026-02-01T12:00:00Z",
        updated_at="2026-02-01T12:00:00Z",
        expires_at="2026-02-01T18:00:00Z",
        runtime_status=RuntimeStatus.ACTIVE,
        processed_event_keys=receipts,
        last_event_sequence=RECEIPT_CAP_TOTAL,
    )
    import json
    from dataclasses import asdict
    data = asdict(st)
    sz = len(json.dumps(data, default=str))
    assert sz < STATE_DOC_MAX_BYTES, f"state doc {sz} bytes exceeds 256 KiB budget"


# ═══════════════════════ Lease + CAS + retry (30-33) ═══════════════════════

def test_30_lease_acquisition(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id)
    out = _dispatch(store, ev)
    assert out.lease_acquired is True
    assert out.lease_id is not None
    assert out.fencing_token is not None


def test_31_stale_fencing_rejected(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    lease1 = run(store.reserve_writer(exp_id, "w-A", lease_ttl_seconds=1))
    stale_token = lease1.fencing_token
    run(store.release_writer(exp_id, lease1.lease_id, lease1.fencing_token))
    lease2 = run(store.reserve_writer(exp_id, "w-B", lease_ttl_seconds=1))
    assert lease2.fencing_token > stale_token
    from app.stats.runtime.state_store.models import AdventurerClassState
    cas = run(store.compare_and_update(
        expedition_id=exp_id,
        expected_state_version=1,
        expected_fencing_token=stale_token,
        mutation={"adventurer_class_states": (("adv-X", AdventurerClassState(adventurer_id="adv-X")),)},
    ))
    assert cas.code is CasResultCode.STALE_WRITER_REJECTED


def test_32_cas_conflict(initialized_state):
    store, exp_id = initialized_state
    lease = run(store.reserve_writer(exp_id, "w-A"))
    from app.stats.runtime.state_store.models import AdventurerClassState
    r1 = run(store.compare_and_update(
        expedition_id=exp_id,
        expected_state_version=1,
        expected_fencing_token=lease.fencing_token,
        mutation={"adventurer_class_states": (("adv-1", AdventurerClassState(adventurer_id="adv-1")),)},
    ))
    assert r1.code is CasResultCode.SUCCESS
    r2 = run(store.compare_and_update(
        expedition_id=exp_id,
        expected_state_version=1,
        expected_fencing_token=lease.fencing_token,
        mutation={"adventurer_class_states": (("adv-2", AdventurerClassState(adventurer_id="adv-2")),)},
    ))
    assert r2.code is CasResultCode.STATE_VERSION_CONFLICT


def test_33_retry_max_3():
    """RETRY_MAX = 3 static verification (PM §8 verbatim)."""
    from app.stats.runtime.transitions import dispatcher as disp_mod
    assert disp_mod.RETRY_MAX == 3


# ═══════════════════════ Feature gating (34-36) ═══════════════════════

def test_34_feature_flag_off_noop(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id)
    ctx = trusted_context(feature_enabled=False)
    out = _dispatch(store, ev, ctx=ctx)
    assert out.result.code is TransitionResultCode.FEATURE_DISABLED
    assert out.lease_acquired is False
    read = run(store.get_state(exp_id))
    assert read.state.state_version == 1
    assert len(read.state.processed_event_keys) == 0


def test_35_non_test_user_fail_closed(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id)
    ctx = trusted_context(test_user_verified=False)
    out = _dispatch(store, ev, ctx=ctx)
    assert out.result.code is TransitionResultCode.TEST_USER_BOUNDARY_VIOLATION
    assert out.lease_acquired is False


def test_36_mongo_allowlist():
    from app.stats.runtime.state_store.fake_store import FakeExpeditionRuntimeStateStore
    from app.stats.runtime.wiring.coordinator import ExpeditionRuntimeCoordinator
    fake = FakeExpeditionRuntimeStateStore()
    coord_allowed = ExpeditionRuntimeCoordinator(store=fake, target_db_name="orbus_r16_rt2b_test")
    assert coord_allowed.is_target_db_allowlisted is True
    coord_it = ExpeditionRuntimeCoordinator(store=fake, target_db_name="orbus_r16_rt2b_it_abc123")
    assert coord_it.is_target_db_allowlisted is True
    coord_forbidden = ExpeditionRuntimeCoordinator(store=fake, target_db_name="orbus_r16")
    assert coord_forbidden.is_target_db_allowlisted is False
    coord_prod = ExpeditionRuntimeCoordinator(store=fake, target_db_name="orbus_r16_test")
    assert coord_prod.is_target_db_allowlisted is False


# ═══════════════════════ Legacy invariance (37) ═══════════════════════

def test_37_legacy_response_and_reward_invariant():
    """Verifica boundary + flag OFF + zero-import da expeditions in transitions/."""
    import app.stats.runtime.transitions as trans_mod
    # transitions/__init__.py path
    disp_path = trans_mod.__file__.replace("__init__.py", "dispatcher.py")
    trans_src = open(disp_path).read()
    assert "from app.expeditions" not in trans_src
    assert "import app.expeditions" not in trans_src
    from app.stats.runtime.feature_flags import is_enabled, ALL_FLAGS
    assert "cdv_class_transitions_enabled" in ALL_FLAGS
    assert is_enabled("cdv_class_transitions_enabled") is False
    # Boundary: no HTTP/env vars in transitions/dispatcher.py
    assert "os.environ" not in trans_src
    assert "fastapi" not in trans_src.lower()
    assert "AsyncIOMotorClient" not in trans_src
    assert "motor" not in trans_src.lower()
    # state_machine.py stessa cosa
    sm_path = disp_path.replace("dispatcher.py", "state_machine.py")
    sm_src = open(sm_path).read()
    assert "from app.expeditions" not in sm_src
    assert "os.environ" not in sm_src
    assert "fastapi" not in sm_src.lower()
