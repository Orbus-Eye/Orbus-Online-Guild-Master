from __future__ import annotations

import asyncio
import copy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
from unittest.mock import AsyncMock

import pytest

from app.stats.runtime.effects.models import (
    EffectDefinition,
    EffectDuration,
    EffectPrimitive,
    EffectRequest,
    EffectStacking,
    EffectTargetScope,
    EffectTrigger,
)
from app.stats.runtime.effects.registry import EffectRegistry
from app.stats.runtime.effects.resolver import resolve_effect
from app.stats.runtime.effects.serialization import (
    project_layout_b,
    rehydrate_layout_b,
)
from app.stats.runtime.state_store.fake_store import (
    FakeExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    EventReceipt,
    ExpeditionRuntimeState,
    MarkDoc,
    RuntimeStatus,
)
from app.stats.runtime.state_store.mongo_adapter import (
    MongoExpeditionRuntimeStateStore,
    _document_to_state,
    _serialize_effect_instances,
)
from app.stats.runtime.state_store.results import CasResultCode


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _definition(**overrides):
    values = {
        "effect_id": "p2.intellect.spark",
        "version": 1,
        "primitive": EffectPrimitive.STAT_FLAT_TEMPORARY,
        "trigger": EffectTrigger.ON_EVENT_COMPLETION,
        "duration": EffectDuration.UNTIL_PHASE_END,
        "target_scope": EffectTargetScope.SELF,
        "target_key": "intellect",
        "magnitude": 5,
        "i18n_key": "effects.p2.intellect_spark",
        "stacking": EffectStacking.NONE,
    }
    values.update(overrides)
    return EffectDefinition(**values)


def _request(definition, **overrides):
    values = {
        "expedition_id": "exp-p2",
        "event_id": "evt-p2-1",
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


def _state(**overrides):
    values = {
        "expedition_id": "exp-p2",
        "state_version": 1,
        "created_at": "2026-07-28T12:00:00Z",
        "updated_at": "2026-07-28T12:00:00Z",
        "expires_at": "2026-07-28T13:00:00Z",
    }
    values.update(overrides)
    return ExpeditionRuntimeState(**values)


def _base_doc(**overrides):
    values = {
        "_id": "exp-p2",
        "state_version": 1,
        "created_at": "2026-07-28T12:00:00Z",
        "updated_at": "2026-07-28T12:00:00Z",
        "expires_at": "2026-07-28T13:00:00Z",
        "runtime_status": "active",
        "adventurer_class_states": {},
        "processed_event_keys": [],
        "last_event_sequence": 0,
        "fencing_token": 0,
    }
    values.update(overrides)
    return values


def test_layout_b_round_trip_restores_definition_owned_fields():
    definition = _definition(priority=7)
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]
    projection = project_layout_b((instance,))
    restored = rehydrate_layout_b(projection, registry)
    assert restored == (instance,)
    assert restored[0].primitive is EffectPrimitive.STAT_FLAT_TEMPORARY
    assert restored[0].target_key == "intellect"
    assert restored[0].definition_priority == 7


def test_layout_b_read_does_not_mutate_projection():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]
    projection = project_layout_b((instance,))
    snapshot = copy.deepcopy(projection)
    rehydrate_layout_b(projection, registry)
    assert projection == snapshot


def test_legacy_document_without_effect_field_rehydrates_empty():
    state = _document_to_state(_base_doc())
    assert state.active_effect_instances == ()


def test_document_rehydration_requires_exact_injected_definition():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]
    doc = _base_doc(active_effect_instances=project_layout_b((instance,)))
    with pytest.raises(ValueError, match="EFFECT_DEFINITION_UNKNOWN"):
        _document_to_state(doc)
    restored = _document_to_state(doc, registry)
    assert restored.active_effect_instances == (instance,)


def test_corrupt_target_token_fails_closed():
    definition = _definition()
    registry = EffectRegistry((definition,))
    with pytest.raises(ValueError, match="TARGET_TOKEN"):
        rehydrate_layout_b({"v": 1, "t": {"enemy.$boss": []}}, registry)


def test_fake_compare_and_update_persists_top_level_effect_tuple():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        assert (await store.create_state("exp-p2", _state())).success
        result = await store.compare_and_update(
            "exp-p2",
            expected_state_version=1,
            expected_fencing_token=0,
            mutation={"active_effect_instances": (instance,)},
        )
        assert result.code is CasResultCode.SUCCESS
        read = await store.get_state("exp-p2")
        assert read.state.active_effect_instances == (instance,)
        assert read.state.adventurer_class_states == ()

    asyncio.run(go())


def test_fake_non_effect_mutation_preserves_active_effects():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        initial = _state(active_effect_instances=(instance,))
        assert (await store.create_state("exp-p2", initial)).success
        result = await store.compare_and_update(
            "exp-p2",
            expected_state_version=1,
            expected_fencing_token=0,
            mutation={"loadout_snapshot_version": 2},
        )
        assert result.success
        read = await store.get_state("exp-p2")
        assert read.state.active_effect_instances == (instance,)

    asyncio.run(go())


def test_mongo_create_serializes_initial_effects_in_layout_b():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]

    async def go():
        collection = AsyncMock()
        store = MongoExpeditionRuntimeStateStore(
            collection,
            clock=lambda: NOW,
            effect_registry=registry,
        )
        result = await store.create_state(
            "exp-p2",
            _state(active_effect_instances=(instance,)),
        )
        assert result.success
        document = collection.insert_one.await_args.args[0]
        assert document["active_effect_instances"] == project_layout_b((instance,))

    asyncio.run(go())


def test_mongo_get_state_rehydrates_with_injected_registry():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]

    async def go():
        collection = AsyncMock()
        collection.find_one.return_value = _base_doc(
            active_effect_instances=_serialize_effect_instances((instance,))
        )
        store = MongoExpeditionRuntimeStateStore(
            collection,
            clock=lambda: NOW,
            effect_registry=registry,
        )
        read = await store.get_state("exp-p2")
        assert read.code is CasResultCode.SUCCESS
        assert read.state.active_effect_instances == (instance,)

    asyncio.run(go())


def test_mongo_compare_and_update_uses_compact_projection():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]

    async def go():
        collection = AsyncMock()
        collection.find_one_and_update.return_value = {"state_version": 2}
        store = MongoExpeditionRuntimeStateStore(
            collection,
            clock=lambda: NOW,
            effect_registry=registry,
        )
        result = await store.compare_and_update(
            "exp-p2",
            expected_state_version=1,
            expected_fencing_token=3,
            mutation={"active_effect_instances": (instance,)},
        )
        assert result.success
        update = collection.find_one_and_update.await_args.args[1]
        assert update["$set"]["active_effect_instances"] == project_layout_b(
            (instance,)
        )

    asyncio.run(go())


def test_mongo_apply_event_once_keeps_receipt_contract_unchanged():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]

    async def go():
        collection = AsyncMock()
        collection.find_one.return_value = {
            "state_version": 1,
            "fencing_token": 2,
            "last_event_sequence": 0,
            "processed_event_keys": [],
        }
        collection.find_one_and_update.return_value = {"state_version": 2}
        store = MongoExpeditionRuntimeStateStore(
            collection,
            clock=lambda: NOW,
            effect_registry=registry,
        )
        result = await store.apply_event_once(
            expedition_id="exp-p2",
            event_id="evt-p2-1",
            event_type="EFFECT_APPLY",
            source_adventurer_id="adv-p2",
            payload_hash="a" * 64,
            expected_state_version=1,
            expected_fencing_token=2,
            mutation={"active_effect_instances": (instance,)},
        )
        assert result.success
        update = collection.find_one_and_update.await_args.args[1]
        assert update["$set"]["active_effect_instances"] == project_layout_b(
            (instance,)
        )
        receipt = update["$push"]["processed_event_keys"]
        assert set(receipt) == {
            "event_id",
            "event_type",
            "source_adventurer_id",
            "payload_hash",
            "assigned_event_sequence",
            "result_code",
            "state_version_after",
            "processed_at",
        }

    asyncio.run(go())


def test_mongo_serializer_rejects_mutable_effect_container():
    with pytest.raises(
        ValueError,
        match="ACTIVE_EFFECT_INSTANCES_NOT_IMMUTABLE_TUPLE",
    ):
        _serialize_effect_instances([])


def test_use_count_round_trip():
    definition = _definition(
        duration=EffectDuration.USE_COUNT,
        use_count=3,
        stacking=EffectStacking.REFRESH,
    )
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]
    restored = rehydrate_layout_b(project_layout_b((instance,)), registry)
    assert restored[0].remaining_uses == 3


def test_projection_rejects_duration_tampering():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]
    projection = project_layout_b((instance,))
    token = next(iter(projection["t"]))
    projection["t"][token][0]["d"] = "e"
    with pytest.raises(ValueError, match="EFFECT_DURATION_INVALID"):
        rehydrate_layout_b(projection, registry)


def test_projection_rejects_unexpected_entry_fields():
    definition = _definition()
    registry = EffectRegistry((definition,))
    instance = resolve_effect(_request(definition), registry).created_instances[0]
    projection = project_layout_b((instance,))
    token = next(iter(projection["t"]))
    projection["t"][token][0]["$unsafe"] = "value"
    with pytest.raises(ValueError, match="EFFECT_ENTRY_FIELDS_UNEXPECTED"):
        rehydrate_layout_b(projection, registry)


def test_full_cap_512_receipts_plus_16_effects_stays_under_245760():
    from bson import BSON

    source_id = "s" * 64
    target_id = "t" * 64
    effect_id = "e" * 64
    timestamp = "2026-07-28T12:00:00+00:00"
    receipts = tuple(
        EventReceipt(
            event_id=(f"evt-{index:04d}-" + "e" * 80)[:96],
            event_type=("START_DRAIN" if index % 2 == 0 else "COMPLETE_DRAIN"),
            source_adventurer_id=source_id,
            payload_hash=hashlib.sha256(str(index).encode()).hexdigest(),
            assigned_event_sequence=index + 1,
            result_code=("DRAIN_STARTED" if index % 2 == 0 else "DRAIN_COMPLETED"),
            state_version_after=index + 1,
            processed_at=timestamp,
        )
        for index in range(504)
    ) + tuple(
        EventReceipt(
            event_id=f"evt-res-{index:03d}",
            event_type=("EXPEDITION_TERMINAL" if index == 0 else "PHASE_END"),
            source_adventurer_id=source_id,
            payload_hash=hashlib.sha256(f"res-{index}".encode()).hexdigest(),
            assigned_event_sequence=505 + index,
            result_code="RESERVED_LIFECYCLE",
            state_version_after=505 + index,
            processed_at=timestamp,
        )
        for index in range(8)
    )
    definition = _definition(
        effect_id=effect_id,
        duration=EffectDuration.USE_COUNT,
        use_count=10,
        stacking=EffectStacking.ADDITIVE_CAPPED,
        stack_cap=5,
        target_scope=EffectTargetScope.TARGET,
        magnitude=10_000,
        priority=10_000,
    )
    registry = EffectRegistry((definition,))
    template = resolve_effect(
        _request(
            definition,
            source_adventurer_id=source_id,
            target_id=target_id,
            application_id="a" * 32,
        ),
        registry,
    ).created_instances[0]
    effects = tuple(
        replace(
            template,
            effect_instance_id=f"fx_{index:032x}",
            target_id=f"{index:02d}" + "t" * 62,
            root_event_sequence=index + 1,
            stack_count=5,
        )
        for index in range(16)
    )
    class_state = AdventurerClassState(
        adventurer_id=source_id,
        active_marks=(
            MarkDoc(
                mark_id="mrk-" + "m" * 16,
                application_id="app-" + "a" * 16,
                source_adventurer_id=source_id,
                target_id=target_id,
                created_at=timestamp,
                expires_at=timestamp,
            ),
        ),
        fragment_count=5,
        resource_segment_id="sg-" + "g" * 16,
        class_state_version=512,
    )
    doc = {
        "_id": "exp-" + "x" * 60,
        "expedition_id": "exp-" + "x" * 60,
        "state_version": 512,
        "created_at": timestamp,
        "updated_at": timestamp,
        "expires_at": timestamp,
        "runtime_status": RuntimeStatus.ACTIVE.value,
        "owner_worker_or_lease_id": None,
        "lease": None,
        "loadout_snapshot_version": 0,
        "adventurer_class_states": {
            source_id: asdict(class_state),
        },
        "active_effect_instances": _serialize_effect_instances(effects),
        "processed_event_keys": [asdict(receipt) for receipt in receipts],
        "last_event_sequence": 512,
        "fencing_token": 1,
    }
    raw_size = len(BSON.encode(doc))
    print(f"\nP2_FULL_CAP_512_PLUS_16_EFFECTS_BSON_BYTES={raw_size}")
    assert len(receipts) == 512
    assert raw_size <= 245_760
    assert raw_size < 262_144
