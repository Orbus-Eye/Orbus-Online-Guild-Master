from __future__ import annotations

from dataclasses import replace

import pytest

from app.stats.runtime.effects.models import (
    EffectDuration,
    EffectFeedbackKind,
    EffectMutationAction,
    EffectPrimitive,
    EffectResultCode,
    EffectStacking,
    EffectTrigger,
)
from app.stats.runtime.effects.registry import EffectRegistry
from app.stats.runtime.effects.resolver import (
    MAX_ACTIVE_INSTANCES,
    deterministic_instance_id,
    resolve_effect,
    resolve_effects,
)
from tests.effect_engine.effects.conftest import make_definition, make_request


def test_resolve_creates_active_instance_and_three_descriptors(
    registry, effect_request
):
    result = resolve_effect(effect_request, registry)
    assert result.accepted
    assert result.result_code is EffectResultCode.EFFECT_RESOLVED
    assert len(result.created_instances) == 1
    assert len(result.mutation_intents) == 1
    assert len(result.feedback_events) == 1
    assert len(result.audit_intents) == 1
    assert result.receipt_payload.created_count == 1


def test_identity_is_deterministic_and_bounded(effect_request):
    first = deterministic_instance_id(effect_request)
    second = deterministic_instance_id(effect_request)
    assert first == second
    assert len(first.encode("utf-8")) <= 40
    assert first.startswith("fx_")


def test_deterministic_replay_is_noop(registry, effect_request):
    first = resolve_effect(effect_request, registry)
    replay = resolve_effect(effect_request, registry, first.created_instances)
    assert replay.accepted
    assert replay.created_instances == ()
    assert replay.mutation_intents == ()
    assert replay.feedback_events[0].kind is EffectFeedbackKind.DEDUPLICATED


def test_unknown_definition_fails_closed(effect_request):
    out = resolve_effect(effect_request, EffectRegistry())
    assert not out.accepted
    assert out.result_code is EffectResultCode.EFFECT_DEFINITION_UNKNOWN
    assert out.mutation_intents == ()


def test_version_mismatch_fails_closed(registry, effect_request):
    out = resolve_effect(replace(effect_request, effect_version=2), registry)
    assert out.result_code is EffectResultCode.EFFECT_VERSION_MISMATCH
    assert out.mutation_intents == ()


def test_trigger_mismatch_fails_closed(registry, effect_request):
    out = resolve_effect(
        replace(effect_request, trigger=EffectTrigger.ON_PHASE_END), registry
    )
    assert out.result_code is EffectResultCode.EFFECT_REQUEST_INVALID


def test_self_target_mismatch_fails_closed(registry, effect_request):
    out = resolve_effect(replace(effect_request, target_id="adv-2"), registry)
    assert out.result_code is EffectResultCode.EFFECT_REQUEST_INVALID


def test_utf8_identifier_bounds_are_bytes_not_characters(registry, effect_request):
    out = resolve_effect(replace(effect_request, target_id="🚀" * 17), registry)
    assert out.result_code is EffectResultCode.EFFECT_REQUEST_INVALID
    assert "TARGET_ID_TOO_LONG" in out.audit_intents[0].reason_codes


@pytest.mark.parametrize("depth,accepted", [(0, True), (1, True), (2, False)])
def test_trigger_depth_cap(registry, effect_request, depth, accepted):
    out = resolve_effect(replace(effect_request, trigger_depth=depth), registry)
    assert out.accepted is accepted
    if not accepted:
        assert out.result_code is EffectResultCode.EFFECT_TRIGGER_DEPTH_EXCEEDED


def test_stacking_none_rejects_second_application(registry, effect_request):
    first = resolve_effect(effect_request, registry)
    second = resolve_effect(
        replace(effect_request, event_id="evt-2", idempotency_key="idem-2"),
        registry,
        first.created_instances,
    )
    assert second.result_code is EffectResultCode.EFFECT_STACKING_REJECTED


def test_refresh_updates_without_duplicate_stat_mutation(effect_request):
    definition = make_definition(stacking=EffectStacking.REFRESH)
    registry = EffectRegistry((definition,))
    first = resolve_effect(effect_request, registry)
    second_request = replace(
        effect_request,
        event_id="evt-2",
        root_event_sequence=2,
        application_id="app-2",
        idempotency_key="idem-2",
    )
    second = resolve_effect(second_request, registry, first.created_instances)
    assert second.accepted
    assert second.created_instances == ()
    assert len(second.updated_instances) == 1
    assert second.mutation_intents == ()
    assert second.feedback_events[0].kind is EffectFeedbackKind.REFRESHED


def test_replace_reverses_old_and_applies_new(effect_request):
    definition = make_definition(stacking=EffectStacking.REPLACE)
    registry = EffectRegistry((definition,))
    first = resolve_effect(effect_request, registry)
    second = resolve_effect(
        replace(
            effect_request,
            event_id="evt-2",
            root_event_sequence=2,
            application_id="app-2",
            idempotency_key="idem-2",
        ),
        registry,
        first.created_instances,
    )
    assert len(second.created_instances) == 1
    assert len(second.removed_instances) == 1
    assert [intent.action for intent in second.mutation_intents] == [
        EffectMutationAction.REMOVE,
        EffectMutationAction.APPLY,
    ]
    assert [intent.amount for intent in second.mutation_intents] == [-5, 5]


def test_additive_capped_applies_only_incremental_stack(effect_request):
    definition = make_definition(
        stacking=EffectStacking.ADDITIVE_CAPPED,
        stack_cap=2,
    )
    registry = EffectRegistry((definition,))
    first = resolve_effect(effect_request, registry)
    second_request = replace(
        effect_request,
        event_id="evt-2",
        application_id="app-2",
        idempotency_key="idem-2",
        root_event_sequence=2,
    )
    second = resolve_effect(second_request, registry, first.created_instances)
    assert second.updated_instances[0].stack_count == 2
    assert second.mutation_intents[0].amount == 5
    third = resolve_effect(
        replace(
            second_request,
            event_id="evt-3",
            application_id="app-3",
            idempotency_key="idem-3",
            root_event_sequence=3,
        ),
        registry,
        second.updated_instances,
    )
    assert third.result_code is EffectResultCode.EFFECT_STACKING_REJECTED


@pytest.mark.parametrize(
    "primitive,expected",
    [
        (EffectPrimitive.RESOURCE_GENERATE, 2),
        (EffectPrimitive.RESOURCE_CONSUME, -2),
    ],
)
def test_resource_intents_have_canonical_sign(primitive, expected):
    definition = make_definition(
        effect_id=f"test.{primitive.value}",
        primitive=primitive,
        duration=EffectDuration.INSTANT,
        target_key="fragments",
        magnitude=2,
    )
    registry = EffectRegistry((definition,))
    effect_request = make_request(effect_id=definition.effect_id)
    out = resolve_effect(effect_request, registry)
    assert out.mutation_intents[0].amount == expected
    assert out.created_instances == ()


def test_feedback_only_has_zero_gameplay_mutation():
    definition = make_definition(
        effect_id="fixture.void_echo",
        primitive=EffectPrimitive.FEEDBACK_ONLY,
        trigger=EffectTrigger.ON_EXPEDITION_END,
        duration=EffectDuration.INSTANT,
        target_key=None,
        magnitude=0,
        i18n_key="effects.fixture.void_echo",
    )
    registry = EffectRegistry((definition,))
    effect_request = make_request(
        effect_id=definition.effect_id,
        trigger=EffectTrigger.ON_EXPEDITION_END,
    )
    out = resolve_effect(effect_request, registry)
    assert out.accepted
    assert out.mutation_intents == ()
    assert out.created_instances == ()


def test_active_instance_cap_is_fail_closed(registry, effect_request):
    created = resolve_effect(effect_request, registry).created_instances[0]
    instances = tuple(
        replace(
            created,
            effect_instance_id=f"fx_{index:032x}",
            effect_id=f"other.effect.{index}",
        )
        for index in range(MAX_ACTIVE_INSTANCES)
    )
    out = resolve_effect(
        replace(effect_request, event_id="evt-cap", idempotency_key="idem-cap"),
        registry,
        instances,
    )
    assert out.result_code is EffectResultCode.EFFECT_CAP_EXCEEDED


def test_malformed_scalar_types_fail_closed(registry, effect_request):
    out = resolve_effect(
        replace(effect_request, root_event_sequence="one"),
        registry,
    )
    assert out.result_code is EffectResultCode.EFFECT_REQUEST_INVALID


def test_batch_above_eight_is_rejected_for_every_request(registry, effect_request):
    requests = tuple(
        replace(
            effect_request,
            event_id=f"evt-{index}",
            application_id=f"app-{index}",
            idempotency_key=f"idem-{index}",
        )
        for index in range(9)
    )
    out = resolve_effects(requests, registry)
    assert len(out) == 9
    assert all(r.result_code is EffectResultCode.EFFECT_CAP_EXCEEDED for r in out)


def test_batch_order_uses_priority_sequence_and_identity():
    low = make_definition(effect_id="effect.low", priority=20)
    high = make_definition(effect_id="effect.high", priority=10)
    registry = EffectRegistry((low, high))
    requests = (
        make_request(effect_id=low.effect_id, event_id="low"),
        make_request(effect_id=high.effect_id, event_id="high"),
    )
    out = resolve_effects(requests, registry)
    assert out[0].receipt_payload.effect_id == "effect.high"


def test_batch_with_invalid_request_does_not_raise(registry, effect_request):
    invalid = replace(effect_request, root_event_sequence="one")
    out = resolve_effects((invalid,), registry)
    assert out[0].result_code is EffectResultCode.EFFECT_REQUEST_INVALID
