from __future__ import annotations

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


def make_definition(**overrides) -> EffectDefinition:
    values = {
        "effect_id": "test.intellect.spark",
        "version": 1,
        "primitive": EffectPrimitive.STAT_FLAT_TEMPORARY,
        "trigger": EffectTrigger.ON_EVENT_COMPLETION,
        "duration": EffectDuration.UNTIL_PHASE_END,
        "target_scope": EffectTargetScope.SELF,
        "target_key": "intellect",
        "magnitude": 5,
        "i18n_key": "effects.test.intellect_spark",
        "stacking": EffectStacking.NONE,
        "audit_class": "test_effect",
    }
    values.update(overrides)
    return EffectDefinition(**values)


def make_request(**overrides) -> EffectRequest:
    values = {
        "expedition_id": "exp-1",
        "event_id": "evt-1",
        "root_event_sequence": 1,
        "effect_id": "test.intellect.spark",
        "effect_version": 1,
        "trigger": EffectTrigger.ON_EVENT_COMPLETION,
        "source_adventurer_id": "adv-1",
        "target_id": "adv-1",
        "application_id": "app-1",
        "idempotency_key": "idem-1",
        "expected_state_version": 1,
    }
    values.update(overrides)
    return EffectRequest(**values)


@pytest.fixture
def definition():
    return make_definition()


@pytest.fixture
def registry(definition):
    return EffectRegistry((definition,))


@pytest.fixture
def effect_request():
    return make_request()
