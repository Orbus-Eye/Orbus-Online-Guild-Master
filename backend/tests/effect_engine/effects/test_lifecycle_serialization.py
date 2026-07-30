from __future__ import annotations

from dataclasses import replace

import pytest

from app.stats.runtime.effects.models import (
    EffectDuration,
    EffectLifecycleEvent,
    EffectLifecycleStatus,
    EffectMutationAction,
    EffectResultCode,
    EffectStacking,
    EffectTargetScope,
    EffectTrigger,
)
from app.stats.runtime.effects.registry import EffectRegistry
from app.stats.runtime.effects.resolver import (
    MAX_ACTIVE_INSTANCES,
    resolve_effect,
    resolve_lifecycle_event,
)
from app.stats.runtime.effects.serialization import (
    ACTIVE_EFFECT_BSON_BUDGET,
    BASELINE_FULL_CAP_BSON_BYTES,
    PROJECTED_FULL_CAP_TARGET_BYTES,
    measure_bson_feasibility,
    project_layout_a,
    project_layout_b,
    project_layout_c,
)
from tests.effect_engine.effects.conftest import make_definition, make_request


def _create(definition, request=None):
    registry = EffectRegistry((definition,))
    request = request or make_request(effect_id=definition.effect_id)
    return registry, resolve_effect(request, registry).created_instances[0]


def test_phase_end_removes_phase_effect_and_reverses_stat():
    definition = make_definition()
    registry, instance = _create(definition)
    event = EffectLifecycleEvent(
        expedition_id="exp-1",
        event_id="phase-end-1",
        root_event_sequence=2,
        trigger=EffectTrigger.ON_PHASE_END,
    )
    out = resolve_lifecycle_event(event, registry, (instance,))
    assert out.accepted
    assert out.removed_instances[0].lifecycle_status is EffectLifecycleStatus.REMOVED
    assert out.mutation_intents[0].action is EffectMutationAction.REMOVE
    assert out.mutation_intents[0].amount == -5


def test_phase_end_keeps_expedition_effect():
    definition = make_definition(duration=EffectDuration.UNTIL_EXPEDITION_END)
    registry, instance = _create(definition)
    event = EffectLifecycleEvent(
        expedition_id="exp-1",
        event_id="phase-end-1",
        root_event_sequence=2,
        trigger=EffectTrigger.ON_PHASE_END,
    )
    out = resolve_lifecycle_event(event, registry, (instance,))
    assert out.removed_instances == ()


def test_expedition_end_removes_all_active_durations():
    definitions = (
        make_definition(effect_id="effect.phase"),
        make_definition(
            effect_id="effect.expedition",
            duration=EffectDuration.UNTIL_EXPEDITION_END,
        ),
    )
    registry = EffectRegistry(definitions)
    instances = tuple(
        resolve_effect(
            make_request(
                effect_id=definition.effect_id,
                event_id=f"evt-{index}",
                application_id=f"app-{index}",
                idempotency_key=f"idem-{index}",
            ),
            registry,
        ).created_instances[0]
        for index, definition in enumerate(definitions)
    )
    event = EffectLifecycleEvent(
        expedition_id="exp-1",
        event_id="exp-end-1",
        root_event_sequence=3,
        trigger=EffectTrigger.ON_EXPEDITION_END,
    )
    out = resolve_lifecycle_event(event, registry, instances)
    assert len(out.removed_instances) == 2
    assert len(out.feedback_events) == 2


def test_use_count_decrements_then_removes():
    definition = make_definition(
        duration=EffectDuration.USE_COUNT,
        use_count=2,
        stacking=EffectStacking.REFRESH,
    )
    registry, instance = _create(definition)
    first = EffectLifecycleEvent(
        expedition_id="exp-1",
        event_id="use-1",
        root_event_sequence=2,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        consumed_instance_ids=(instance.effect_instance_id,),
    )
    out1 = resolve_lifecycle_event(first, registry, (instance,))
    assert out1.updated_instances[0].remaining_uses == 1
    second = replace(first, event_id="use-2", root_event_sequence=3)
    out2 = resolve_lifecycle_event(second, registry, out1.updated_instances)
    assert len(out2.removed_instances) == 1


def test_unknown_consumed_instance_fails_closed(registry):
    event = EffectLifecycleEvent(
        expedition_id="exp-1",
        event_id="use-1",
        root_event_sequence=2,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        consumed_instance_ids=("fx_missing",),
    )
    out = resolve_lifecycle_event(event, registry, ())
    assert out.result_code is EffectResultCode.EFFECT_INSTANCE_NOT_FOUND


def test_layouts_are_deterministic(registry, effect_request):
    instance = resolve_effect(effect_request, registry).created_instances[0]
    reversed_pair = (
        replace(instance, effect_instance_id="fx_b"),
        replace(instance, effect_instance_id="fx_a"),
    )
    for projection in (project_layout_a, project_layout_b, project_layout_c):
        assert projection(reversed_pair) == projection(tuple(reversed(reversed_pair)))


def test_layout_b_is_target_keyed(registry, effect_request):
    instance = resolve_effect(effect_request, registry).created_instances[0]
    projection = project_layout_b((instance,))
    target_token = next(iter(projection["t"]))
    assert target_token.startswith("t_")
    assert "t" not in projection["t"][target_token][0]


def test_layout_b_never_uses_raw_target_as_mongo_field(registry, effect_request):
    unsafe_target = "enemy.$boss"
    request = replace(effect_request, target_id=unsafe_target)
    definition = make_definition(
        target_scope=EffectTargetScope.TARGET,
    )
    local_registry = EffectRegistry((definition,))
    instance = resolve_effect(request, local_registry).created_instances[0]
    projection = project_layout_b((instance,))
    assert unsafe_target not in projection["t"]
    assert all("." not in key and "$" not in key for key in projection["t"])


def test_all_three_layouts_measure_real_bson(registry, effect_request):
    instance = resolve_effect(effect_request, registry).created_instances[0]
    for layout in ("A", "B", "C"):
        result = measure_bson_feasibility((instance,), layout=layout)
        assert result.active_effect_bytes > 0
        assert result.passed


def test_layout_b_full_cap_stays_inside_effect_and_state_budgets(
    registry, effect_request
):
    template = resolve_effect(effect_request, registry).created_instances[0]
    instances = tuple(
        replace(
            template,
            effect_instance_id=f"fx_{index:032x}",
            application_id=f"app-{index}",
            root_event_sequence=index + 1,
        )
        for index in range(MAX_ACTIVE_INSTANCES)
    )
    result = measure_bson_feasibility(instances, layout="B")
    assert result.active_effect_bytes <= ACTIVE_EFFECT_BSON_BUDGET
    assert result.projected_full_cap_bytes == (
        BASELINE_FULL_CAP_BSON_BYTES + result.active_effect_bytes
    )
    assert result.projected_full_cap_bytes <= PROJECTED_FULL_CAP_TARGET_BYTES
    assert result.passed


def test_layout_b_worst_case_identifiers_and_unique_targets_stays_in_budget():
    definition = make_definition(
        effect_id="e" * 64,
        duration=EffectDuration.USE_COUNT,
        use_count=10,
        stacking=EffectStacking.ADDITIVE_CAPPED,
        stack_cap=5,
        magnitude=10_000,
        priority=10_000,
        target_scope=EffectTargetScope.TARGET,
    )
    registry = EffectRegistry((definition,))
    template = resolve_effect(
        make_request(
            effect_id=definition.effect_id,
            source_adventurer_id="s" * 64,
            target_id="s" * 64,
            application_id="a" * 32,
        ),
        registry,
    ).created_instances[0]
    instances = tuple(
        replace(
            template,
            effect_instance_id=f"fx_{index:032x}",
            target_id=f"{index:02d}" + "t" * 62,
            root_event_sequence=index + 1,
            stack_count=5,
        )
        for index in range(MAX_ACTIVE_INSTANCES)
    )
    result = measure_bson_feasibility(instances, layout="B")
    assert result.active_effect_bytes <= ACTIVE_EFFECT_BSON_BUDGET
    assert result.projected_full_cap_bytes <= PROJECTED_FULL_CAP_TARGET_BYTES
    assert result.passed


def test_non_active_instance_cannot_enter_active_projection(registry, effect_request):
    instance = resolve_effect(effect_request, registry).created_instances[0]
    removed = replace(instance, lifecycle_status=EffectLifecycleStatus.REMOVED)
    with pytest.raises(ValueError, match="ONLY_ACTIVE_INSTANCES"):
        project_layout_b((removed,))


def test_serialization_rejects_more_than_sixteen(registry, effect_request):
    template = resolve_effect(effect_request, registry).created_instances[0]
    instances = tuple(
        replace(template, effect_instance_id=f"fx_{index:032x}")
        for index in range(MAX_ACTIVE_INSTANCES + 1)
    )
    with pytest.raises(ValueError, match="ACTIVE_INSTANCE_CAP_EXCEEDED"):
        measure_bson_feasibility(instances)


def test_serialization_unknown_layout_rejected():
    with pytest.raises(ValueError, match="UNKNOWN_LAYOUT"):
        measure_bson_feasibility((), layout="Z")
