from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.stats.runtime import feature_flags
from app.stats.runtime.effects.dispatcher import EffectDispatcher
from app.stats.runtime.effects.models import (
    EffectDefinition,
    EffectDuration,
    EffectLifecycleEvent,
    EffectPrimitive,
    EffectRequest,
    EffectResultCode,
    EffectStacking,
    EffectTargetScope,
    EffectTrigger,
)
from app.stats.runtime.effects.registry import EffectRegistry
from app.stats.runtime.state_store.fake_store import (
    FakeExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import ExpeditionRuntimeState
from app.stats.runtime.state_store.results import CasResultCode
from app.stats.runtime.wiring.feature_flags import EffectGateContext


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _definition(**overrides):
    values = {
        "effect_id": "p2.dispatch.intellect",
        "version": 1,
        "primitive": EffectPrimitive.STAT_FLAT_TEMPORARY,
        "trigger": EffectTrigger.ON_EVENT_COMPLETION,
        "duration": EffectDuration.UNTIL_PHASE_END,
        "target_scope": EffectTargetScope.SELF,
        "target_key": "intellect",
        "magnitude": 5,
        "i18n_key": "effects.p2.dispatch_intellect",
        "stacking": EffectStacking.NONE,
    }
    values.update(overrides)
    return EffectDefinition(**values)


def _request(definition, **overrides):
    values = {
        "expedition_id": "exp-dispatch-p2",
        "event_id": "evt-dispatch-p2",
        "root_event_sequence": 1,
        "effect_id": definition.effect_id,
        "effect_version": definition.version,
        "trigger": definition.trigger,
        "source_adventurer_id": "adv-p2",
        "target_id": "adv-p2",
        "application_id": "app-p2",
        "idempotency_key": "idem-p2",
    }
    values.update(overrides)
    return EffectRequest(**values)


def _state():
    return ExpeditionRuntimeState(
        expedition_id="exp-dispatch-p2",
        state_version=1,
        created_at="2026-07-28T12:00:00Z",
        updated_at="2026-07-28T12:00:00Z",
        expires_at="2026-07-28T13:00:00Z",
    )


def _context(**overrides):
    values = {
        "is_test_user": True,
        "environment_is_localhost_isolated": True,
        "mongo_target_allowlisted": True,
    }
    values.update(overrides)
    return EffectGateContext(**values)


@pytest.fixture(autouse=True)
def _flags_off(monkeypatch):
    for flag in feature_flags.ALL_FLAGS:
        monkeypatch.delenv(
            f"ORBUS_FLAG_{flag.upper()}",
            raising=False,
        )
    feature_flags.reset_cache()
    yield
    feature_flags.reset_cache()


def _enable(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    monkeypatch.setenv("ORBUS_FLAG_ITEM_EFFECT_ENGINE_ENABLED", "true")
    feature_flags.reset_cache()


class _ExplodingStore:
    def __getattr__(self, name):
        raise AssertionError(f"store accessed while gate/preflight closed: {name}")


def test_gate_off_makes_zero_store_calls():
    definition = _definition()
    dispatcher = EffectDispatcher(
        store=_ExplodingStore(),
        registry=EffectRegistry((definition,)),
        gate_context=_context(),
    )
    outcome = asyncio.run(dispatcher.dispatch(_request(definition)))
    assert not outcome.resolution.accepted
    assert outcome.gate_reason == "TRANSIENT_STATE_DISABLED"


@pytest.mark.parametrize(
    "context_change,reason",
    [
        ({"is_test_user": False}, "TEST_USER_BOUNDARY_VIOLATION"),
        (
            {"environment_is_localhost_isolated": False},
            "ENVIRONMENT_NOT_LOCALHOST_ISOLATED",
        ),
        ({"mongo_target_allowlisted": False}, "DB_NOT_ALLOWLISTED"),
    ],
)
def test_each_runtime_boundary_fails_before_store(
    monkeypatch,
    context_change,
    reason,
):
    _enable(monkeypatch)
    definition = _definition()
    dispatcher = EffectDispatcher(
        store=_ExplodingStore(),
        registry=EffectRegistry((definition,)),
        gate_context=_context(**context_change),
    )
    outcome = asyncio.run(dispatcher.dispatch(_request(definition)))
    assert outcome.gate_reason == reason


def test_effect_flag_off_fails_before_store(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    feature_flags.reset_cache()
    definition = _definition()
    dispatcher = EffectDispatcher(
        store=_ExplodingStore(),
        registry=EffectRegistry((definition,)),
        gate_context=_context(),
    )
    outcome = asyncio.run(dispatcher.dispatch(_request(definition)))
    assert outcome.gate_reason == "ITEM_EFFECT_ENGINE_DISABLED"


def test_dispatch_persists_effect_and_unchanged_receipt(monkeypatch):
    _enable(monkeypatch)
    definition = _definition()

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        assert (await store.create_state("exp-dispatch-p2", _state())).success
        dispatcher = EffectDispatcher(
            store=store,
            registry=EffectRegistry((definition,)),
            gate_context=_context(),
        )
        outcome = await dispatcher.dispatch(_request(definition))
        assert outcome.resolution.accepted
        assert outcome.cas_result_code is CasResultCode.SUCCESS
        assert outcome.assigned_event_sequence == 1
        assert outcome.state_version_after == 2
        read = await store.get_state("exp-dispatch-p2")
        assert len(read.state.active_effect_instances) == 1
        assert read.state.active_effect_instances[0].effect_id == definition.effect_id
        assert len(read.state.processed_event_keys) == 1
        assert read.state.processed_event_keys[0].event_type == "EFFECT_APPLY"
        assert read.state.MAX_PROCESSED_EVENTS == 512

    asyncio.run(go())


def test_dispatch_replay_is_store_deduplicated_noop(monkeypatch):
    _enable(monkeypatch)
    definition = _definition()

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        await store.create_state("exp-dispatch-p2", _state())
        dispatcher = EffectDispatcher(
            store=store,
            registry=EffectRegistry((definition,)),
            gate_context=_context(),
        )
        first = await dispatcher.dispatch(_request(definition))
        replay = await dispatcher.dispatch(_request(definition))
        assert first.cas_result_code is CasResultCode.SUCCESS
        assert replay.cas_result_code is CasResultCode.DEDUPLICATED_NO_OP
        assert replay.resolution.mutation_intents == ()
        read = await store.get_state("exp-dispatch-p2")
        assert read.state.state_version == 2
        assert len(read.state.active_effect_instances) == 1
        assert len(read.state.processed_event_keys) == 1

    asyncio.run(go())


def test_same_event_changed_payload_is_rejected_without_second_write(monkeypatch):
    _enable(monkeypatch)
    definition = _definition(target_scope=EffectTargetScope.TARGET)

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        await store.create_state("exp-dispatch-p2", _state())
        dispatcher = EffectDispatcher(
            store=store,
            registry=EffectRegistry((definition,)),
            gate_context=_context(),
        )
        request = _request(definition)
        await dispatcher.dispatch(request)
        mismatch = await dispatcher.dispatch(replace(request, target_id="other-target"))
        assert not mismatch.resolution.accepted
        assert mismatch.cas_result_code is CasResultCode.EVENT_ID_PAYLOAD_MISMATCH
        read = await store.get_state("exp-dispatch-p2")
        assert read.state.state_version == 2
        assert len(read.state.processed_event_keys) == 1

    asyncio.run(go())


@pytest.mark.parametrize(
    "primitive,target_key,magnitude",
    [
        (EffectPrimitive.RESOURCE_GENERATE, "fragments", 1),
        (EffectPrimitive.RESOURCE_CONSUME, "fragments", 1),
        (EffectPrimitive.STATE_TAG_REMOVE, "marked", 0),
    ],
)
def test_unintegrated_instant_mutations_fail_before_store(
    monkeypatch,
    primitive,
    target_key,
    magnitude,
):
    _enable(monkeypatch)
    definition = _definition(
        primitive=primitive,
        target_key=target_key,
        magnitude=magnitude,
        duration=EffectDuration.INSTANT,
    )
    dispatcher = EffectDispatcher(
        store=_ExplodingStore(),
        registry=EffectRegistry((definition,)),
        gate_context=_context(),
    )
    outcome = asyncio.run(dispatcher.dispatch(_request(definition)))
    assert (
        outcome.resolution.result_code is EffectResultCode.EFFECT_PRIMITIVE_UNSUPPORTED
    )


def test_feedback_only_persists_receipt_but_no_active_instance(monkeypatch):
    _enable(monkeypatch)
    definition = _definition(
        effect_id="p2.feedback.only",
        primitive=EffectPrimitive.FEEDBACK_ONLY,
        duration=EffectDuration.INSTANT,
        target_key=None,
        magnitude=0,
        trigger=EffectTrigger.ON_EXPEDITION_END,
    )

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        await store.create_state("exp-dispatch-p2", _state())
        dispatcher = EffectDispatcher(
            store=store,
            registry=EffectRegistry((definition,)),
            gate_context=_context(),
        )
        outcome = await dispatcher.dispatch(_request(definition))
        assert outcome.resolution.accepted
        read = await store.get_state("exp-dispatch-p2")
        assert read.state.active_effect_instances == ()
        assert len(read.state.processed_event_keys) == 1

    asyncio.run(go())


def test_phase_lifecycle_removes_effect_atomically(monkeypatch):
    _enable(monkeypatch)
    definition = _definition()

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        await store.create_state("exp-dispatch-p2", _state())
        dispatcher = EffectDispatcher(
            store=store,
            registry=EffectRegistry((definition,)),
            gate_context=_context(),
        )
        await dispatcher.dispatch(_request(definition))
        lifecycle = EffectLifecycleEvent(
            expedition_id="exp-dispatch-p2",
            event_id="evt-phase-end",
            root_event_sequence=1,
            trigger=EffectTrigger.ON_PHASE_END,
        )
        outcome = await dispatcher.dispatch_lifecycle(lifecycle)
        assert outcome.resolution.accepted
        assert len(outcome.resolution.removed_instances) == 1
        read = await store.get_state("exp-dispatch-p2")
        assert read.state.active_effect_instances == ()
        assert len(read.state.processed_event_keys) == 2
        assert read.state.state_version == 3

    asyncio.run(go())


def test_use_count_lifecycle_decrements_then_removes(monkeypatch):
    _enable(monkeypatch)
    definition = _definition(
        duration=EffectDuration.USE_COUNT,
        use_count=2,
        stacking=EffectStacking.REFRESH,
    )

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        await store.create_state("exp-dispatch-p2", _state())
        dispatcher = EffectDispatcher(
            store=store,
            registry=EffectRegistry((definition,)),
            gate_context=_context(),
        )
        await dispatcher.dispatch(_request(definition))
        read = await store.get_state("exp-dispatch-p2")
        instance_id = read.state.active_effect_instances[0].effect_instance_id
        first = EffectLifecycleEvent(
            expedition_id="exp-dispatch-p2",
            event_id="evt-use-1",
            root_event_sequence=1,
            trigger=EffectTrigger.ON_EVENT_COMPLETION,
            consumed_instance_ids=(instance_id,),
        )
        await dispatcher.dispatch_lifecycle(first)
        read = await store.get_state("exp-dispatch-p2")
        assert read.state.active_effect_instances[0].remaining_uses == 1
        await dispatcher.dispatch_lifecycle(replace(first, event_id="evt-use-2"))
        read = await store.get_state("exp-dispatch-p2")
        assert read.state.active_effect_instances == ()

    asyncio.run(go())


def test_unknown_definition_fails_before_store(monkeypatch):
    _enable(monkeypatch)
    definition = _definition()
    dispatcher = EffectDispatcher(
        store=_ExplodingStore(),
        registry=EffectRegistry(),
        gate_context=_context(),
    )
    outcome = asyncio.run(dispatcher.dispatch(_request(definition)))
    assert outcome.resolution.result_code is EffectResultCode.EFFECT_DEFINITION_UNKNOWN


def test_invalid_lifecycle_event_fails_before_store(monkeypatch):
    _enable(monkeypatch)
    definition = _definition()
    dispatcher = EffectDispatcher(
        store=_ExplodingStore(),
        registry=EffectRegistry((definition,)),
        gate_context=_context(),
    )
    invalid = EffectLifecycleEvent(
        expedition_id="exp-dispatch-p2",
        event_id="",
        root_event_sequence=1,
        trigger=EffectTrigger.ON_PHASE_END,
    )
    outcome = asyncio.run(dispatcher.dispatch_lifecycle(invalid))
    assert outcome.resolution.result_code is EffectResultCode.EFFECT_REQUEST_INVALID
