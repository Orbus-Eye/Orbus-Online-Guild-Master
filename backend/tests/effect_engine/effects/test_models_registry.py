from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.stats.runtime.effects.models import (
    EffectDuration,
    EffectPrimitive,
    EffectResultCode,
    EffectStacking,
    EffectTrigger,
)
from app.stats.runtime.effects.registry import (
    DEFAULT_EFFECT_REGISTRY,
    EffectDefinitionError,
    EffectRegistry,
    RUNTIME_STAT_KEYS,
    validate_definition,
)
from tests.effect_engine.effects.conftest import make_definition


def test_result_code_inventory_is_exactly_ten():
    assert len(EffectResultCode) == 10


def test_runtime_stat_whitelist_is_exactly_canonical_five():
    assert RUNTIME_STAT_KEYS == {
        "strength",
        "agility",
        "intellect",
        "endurance",
        "faith",
    }


def test_definition_is_immutable(definition):
    with pytest.raises(FrozenInstanceError):
        definition.magnitude = 99


def test_default_registry_contains_no_gameplay_definition():
    assert DEFAULT_EFFECT_REGISTRY.definitions == ()


def test_constructing_registry_does_not_mutate_default(definition):
    local = EffectRegistry((definition,))
    assert local.get(definition.effect_id, 1) == definition
    assert DEFAULT_EFFECT_REGISTRY.definitions == ()


def test_registry_rejects_mutable_definition_container(definition):
    with pytest.raises(
        EffectDefinitionError,
        match="REGISTRY_DEFINITIONS_NOT_IMMUTABLE_TUPLE",
    ):
        EffectRegistry([definition])


def test_duplicate_definition_rejected(definition):
    with pytest.raises(EffectDefinitionError, match="DUPLICATE_DEFINITION"):
        EffectRegistry((definition, definition))


@pytest.mark.parametrize(
    "definition,error",
    [
        (make_definition(target_key="cost"), "STAT_KEY_UNREGISTERED"),
        (
            make_definition(duration=EffectDuration.INSTANT),
            "TEMPORARY_STAT_REQUIRES_DURATION",
        ),
        (make_definition(magnitude=0), "STAT_MAGNITUDE_ZERO"),
        (
            make_definition(
                duration=EffectDuration.USE_COUNT,
                use_count=11,
            ),
            "USE_COUNT_INVALID",
        ),
        (
            make_definition(
                stacking=EffectStacking.ADDITIVE_CAPPED,
                stack_cap=6,
            ),
            "STACK_CAP_INVALID",
        ),
    ],
)
def test_invalid_definition_contract(definition, error):
    assert error in validate_definition(definition)
    with pytest.raises(EffectDefinitionError, match=error):
        EffectRegistry((definition,))


@pytest.mark.parametrize(
    "definition",
    [
        make_definition(
            effect_id="test.tag.apply",
            primitive=EffectPrimitive.STATE_TAG_APPLY,
            target_key="marked",
            magnitude=0,
        ),
        make_definition(
            effect_id="test.tag.remove",
            primitive=EffectPrimitive.STATE_TAG_REMOVE,
            target_key="marked",
            magnitude=0,
            duration=EffectDuration.INSTANT,
        ),
        make_definition(
            effect_id="test.resource.generate",
            primitive=EffectPrimitive.RESOURCE_GENERATE,
            target_key="fragments",
            magnitude=1,
            duration=EffectDuration.INSTANT,
        ),
        make_definition(
            effect_id="test.resource.consume",
            primitive=EffectPrimitive.RESOURCE_CONSUME,
            target_key="fragments",
            magnitude=1,
            duration=EffectDuration.INSTANT,
        ),
        make_definition(
            effect_id="test.feedback",
            primitive=EffectPrimitive.FEEDBACK_ONLY,
            target_key=None,
            magnitude=0,
            duration=EffectDuration.INSTANT,
            trigger=EffectTrigger.ON_EXPEDITION_END,
        ),
    ],
)
def test_all_authorized_primitives_can_be_registered(definition):
    assert validate_definition(definition) == ()
    assert EffectRegistry((definition,)).definitions == (definition,)


def test_arbitrary_state_tag_and_resource_are_rejected():
    tag = make_definition(
        primitive=EffectPrimitive.STATE_TAG_APPLY,
        target_key="arbitrary.path",
        magnitude=0,
    )
    resource = make_definition(
        primitive=EffectPrimitive.RESOURCE_GENERATE,
        target_key="gold",
        magnitude=1,
        duration=EffectDuration.INSTANT,
    )
    assert "STATE_TAG_UNREGISTERED" in validate_definition(tag)
    assert "RESOURCE_KEY_UNREGISTERED" in validate_definition(resource)


def test_mutable_tag_list_is_rejected(definition):
    mutable = make_definition(tags=["one"])
    assert "TAGS_NOT_IMMUTABLE_TUPLE" in validate_definition(mutable)
