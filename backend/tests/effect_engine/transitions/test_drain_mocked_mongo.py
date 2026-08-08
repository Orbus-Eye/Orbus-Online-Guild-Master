"""RT2-B-2B-2-1 · Drain mocked-Mongo tests (adapter CAS semantics · no network).

Verifica sul `MongoExpeditionRuntimeStateStore` con `_InMemoryMongoCollectionMock`:
- serializzazione DrainDoc (+ completion payload) → BSON-friendly dict
- rehydration raw-dict → coercion application-side
- completion-to-Fragment atomic batch su CAS reale ($inc/$set/$push)
- dedup guard su event_id (replay → prior execution ID)
- single receipt slot per completion (B2B2Q07)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.stats.runtime.state_store.models import (
    DrainStatus,
    ExpeditionRuntimeState,
    RuntimeStatus,
)
from app.stats.runtime.state_store.mongo_adapter import MongoExpeditionRuntimeStateStore
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.drain import coerce_drains
from app.stats.runtime.transitions.models import (
    ClassEventType,
    TransitionResultCode as RC,
)
from tests.effect_engine.state_store.conftest import (
    _FrozenClock,
    _InMemoryMongoCollectionMock,
)
from tests.effect_engine.transitions.conftest import (
    make_event,
    run,
    trusted_context,
)

ADV = "adv-cdv-01"
TGT = "target-boss-01"


@pytest.fixture
def mongo_env():
    clock = _FrozenClock(datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc))
    collection = _InMemoryMongoCollectionMock()
    store = MongoExpeditionRuntimeStateStore(collection, clock=clock)
    exp_id = f"exp-mm-{uuid.uuid4().hex[:10]}"
    now = clock()
    shell = ExpeditionRuntimeState(
        expedition_id=exp_id, state_version=1, fencing_token=0,
        created_at=now.isoformat(), updated_at=now.isoformat(),
        expires_at=(now + timedelta(hours=6)).isoformat(),
        runtime_status=RuntimeStatus.ACTIVE,
    )
    res = run(store.create_state(exp_id, shell))
    assert res.success, res.code
    return store, exp_id, clock


def _dispatch(store, event, clock):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-mm", now_fn=clock)
    return run(disp.dispatch(event, trusted_context=trusted_context()))


def test_mm01_full_drain_flow_atomic_on_mongo_mock(mongo_env):
    store, exp_id, clock = mongo_env
    mark = _dispatch(store, make_event(
        ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    assert mark.result.code is RC.SUCCESS
    start = _dispatch(store, make_event(
        ClassEventType.START_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    assert start.result.code is RC.DRAIN_STARTED
    drain_id = start.result.drain_execution_id
    comp = _dispatch(store, make_event(
        ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_id), clock)
    assert comp.result.code is RC.DRAIN_COMPLETED
    assert comp.result.fragment_gain_applied == 1
    # Rehydration raw-dict → coercion + verifica batch atomico persistito
    st = run(store.get_state(exp_id)).state
    cs = st.class_state_for(ADV)
    assert cs.fragment_count == 1
    assert cs.resource_segment_id and cs.resource_segment_id.startswith("sg-")
    drains = coerce_drains(cs)
    assert drains[0].runtime_status is DrainStatus.RESOLVED
    # PM adjudication B2B2Q07: payload 15-campi REALMENTE persistito nella
    # processed-event receipt (roundtrip serialize → rehydrate su Mongo mock)
    comp_receipt = st.processed_event_keys[-1]
    assert comp_receipt.event_type == "COMPLETE_DRAIN"
    p = comp_receipt.result_payload
    assert p is not None and len(p) == 15
    assert p["result_code"] == "SUCCESS"
    assert p["fragment_gain_applied"] == 1
    assert p["state_version_after"] == st.state_version
    # DrainDoc: nessuna copia autoritativa · linkage 1:1
    assert drains[0].completion_payload is None
    assert drains[0].completion_event_id == comp_receipt.event_id
    # 1 sola receipt per la completion (3 totali: mark+start+complete)
    assert len(st.processed_event_keys) == 3
    assert st.state_version == 4  # +1 exactly once per batch


def test_mm02_replay_start_on_mongo_mock_returns_prior_id(mongo_env):
    store, exp_id, clock = mongo_env
    _dispatch(store, make_event(
        ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    ev = make_event(ClassEventType.START_DRAIN.value, expedition_id=exp_id,
                    source_adventurer_id=ADV, target_id=TGT,
                    event_id="evt-start-mm")
    out = _dispatch(store, ev, clock)
    assert out.result.code is RC.DRAIN_STARTED
    replay = _dispatch(store, ev, clock)
    assert replay.result.code is RC.DEDUPLICATED_NO_OP
    assert replay.result.drain_execution_id == out.result.drain_execution_id
    st = run(store.get_state(exp_id)).state
    assert len(coerce_drains(st.class_state_for(ADV))) == 1


def test_mm03_fold_cancellation_persisted_on_mongo_mock(mongo_env):
    store, exp_id, clock = mongo_env
    _dispatch(store, make_event(
        ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    start = _dispatch(store, make_event(
        ClassEventType.START_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    clock.advance(seconds=11)  # Mark scade
    receipts_before = len(run(store.get_state(exp_id)).state.processed_event_keys)
    comp = _dispatch(store, make_event(
        ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV,
        drain_execution_id=start.result.drain_execution_id), clock)
    assert comp.result.code is RC.MARK_EXPIRED
    st = run(store.get_state(exp_id)).state
    cs = st.class_state_for(ADV)
    d = coerce_drains(cs)[0]
    assert d.runtime_status is DrainStatus.CANCELLED
    assert d.cancellation_reason == "MARK_EXPIRED"
    assert cs.fragment_count == 0
    # folded: UNA sola receipt aggiuntiva (B2B2Q14)
    assert len(st.processed_event_keys) == receipts_before + 1


def test_mm04_duplicate_completion_no_double_fragment_on_mongo_mock(mongo_env):
    store, exp_id, clock = mongo_env
    _dispatch(store, make_event(
        ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    start = _dispatch(store, make_event(
        ClassEventType.START_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=TGT), clock)
    drain_id = start.result.drain_execution_id
    c1 = _dispatch(store, make_event(
        ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_id,
        event_id="evt-c1"), clock)
    assert c1.result.code is RC.DRAIN_COMPLETED
    c2 = _dispatch(store, make_event(
        ClassEventType.COMPLETE_DRAIN.value, expedition_id=exp_id,
        source_adventurer_id=ADV, drain_execution_id=drain_id,
        event_id="evt-c2"), clock)
    assert c2.result.code is RC.DRAIN_ALREADY_COMPLETED
    st = run(store.get_state(exp_id)).state
    assert st.class_state_for(ADV).fragment_count == 1


def test_mm05_lifecycle_aggregate_on_mongo_mock(mongo_env):
    store, exp_id, clock = mongo_env
    ids = []
    for t in ("t1", "t2"):
        _dispatch(store, make_event(
            ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
            source_adventurer_id=ADV, target_id=t), clock)
        out = _dispatch(store, make_event(
            ClassEventType.START_DRAIN.value, expedition_id=exp_id,
            source_adventurer_id=ADV, target_id=t), clock)
        ids.append(out.result.drain_execution_id)
    receipts_before = len(run(store.get_state(exp_id)).state.processed_event_keys)
    pe = _dispatch(store, make_event(
        ClassEventType.PHASE_END.value, expedition_id=exp_id,
        source_adventurer_id=ADV), clock)
    assert pe.result.code is RC.SUCCESS
    assert pe.result.drains_cancelled_count == 2
    st = run(store.get_state(exp_id)).state
    assert len(st.processed_event_keys) == receipts_before + 1  # 1 reserved
    for d in coerce_drains(st.class_state_for(ADV)):
        assert d.runtime_status is DrainStatus.CANCELLED
        assert d.cancellation_reason == "PHASE_ENDED"
