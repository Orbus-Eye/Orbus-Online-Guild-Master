"""Static, fail-closed definition registry for RT2-C-P1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from .models import (
    EffectDefinition,
    EffectDuration,
    EffectPrimitive,
    EffectStacking,
    EffectTargetScope,
    EffectTrigger,
    EffectVisibility,
)


RUNTIME_STAT_KEYS = frozenset(
    ("strength", "agility", "intellect", "endurance", "faith")
)
DEFAULT_STATE_TAG_KEYS = frozenset(("marked", "drain_in_progress"))
DEFAULT_RESOURCE_KEYS = frozenset(("fragments",))

EFFECT_ID_MAX_BYTES = 64
IDENTIFIER_MAX_BYTES = 64
I18N_KEY_MAX_BYTES = 96
TAG_MAX_BYTES = 32
MAX_DEFINITION_TAGS = 8
MAX_STACK_CAP = 5
MAX_USE_COUNT = 10
MAX_ABS_MAGNITUDE = 10_000


class EffectDefinitionError(ValueError):
    """Raised when a static definition violates the P1 contract."""


def _byte_len(value: str) -> int:
    return len(value.encode("utf-8"))


def _bounded_nonempty(value: object, *, name: str, max_bytes: int) -> Optional[str]:
    if not isinstance(value, str) or not value:
        return f"{name}_EMPTY"
    if _byte_len(value) > max_bytes:
        return f"{name}_TOO_LONG"
    return None


def validate_definition(
    definition: EffectDefinition,
    *,
    state_tag_keys: frozenset[str] = DEFAULT_STATE_TAG_KEYS,
    resource_keys: frozenset[str] = DEFAULT_RESOURCE_KEYS,
) -> Tuple[str, ...]:
    """Return all definition violations without mutating or normalizing input."""

    errors: list[str] = []
    for value, name, bound in (
        (definition.effect_id, "EFFECT_ID", EFFECT_ID_MAX_BYTES),
        (definition.i18n_key, "I18N_KEY", I18N_KEY_MAX_BYTES),
        (definition.audit_class, "AUDIT_CLASS", IDENTIFIER_MAX_BYTES),
    ):
        error = _bounded_nonempty(value, name=name, max_bytes=bound)
        if error:
            errors.append(error)

    if type(definition.version) is not int or definition.version < 1:
        errors.append("VERSION_INVALID")
    if type(definition.priority) is not int or not 0 <= definition.priority <= 10_000:
        errors.append("PRIORITY_INVALID")
    if type(definition.magnitude) is not int:
        errors.append("MAGNITUDE_INVALID")
    elif abs(definition.magnitude) > MAX_ABS_MAGNITUDE:
        errors.append("MAGNITUDE_OUT_OF_BOUNDS")
    if not isinstance(definition.tags, tuple):
        errors.append("TAGS_NOT_IMMUTABLE_TUPLE")
        tags = ()
    else:
        tags = definition.tags
    if len(tags) > MAX_DEFINITION_TAGS:
        errors.append("TAGS_CAP_EXCEEDED")
    string_tags = tuple(tag for tag in tags if isinstance(tag, str))
    if len(set(string_tags)) != len(string_tags):
        errors.append("TAGS_DUPLICATED")
    for tag in tags:
        error = _bounded_nonempty(tag, name="TAG", max_bytes=TAG_MAX_BYTES)
        if error:
            errors.append(error)
    if not isinstance(definition.primitive, EffectPrimitive):
        errors.append("PRIMITIVE_UNSUPPORTED")
    if not isinstance(definition.trigger, EffectTrigger):
        errors.append("TRIGGER_INVALID")
    if not isinstance(definition.duration, EffectDuration):
        errors.append("DURATION_INVALID")
    if not isinstance(definition.stacking, EffectStacking):
        errors.append("STACKING_INVALID")
    if not isinstance(definition.target_scope, EffectTargetScope):
        errors.append("TARGET_SCOPE_INVALID")
    if not isinstance(definition.visibility, EffectVisibility):
        errors.append("VISIBILITY_INVALID")

    if definition.duration is EffectDuration.USE_COUNT:
        if (
            type(definition.use_count) is not int
            or not 1 <= definition.use_count <= MAX_USE_COUNT
        ):
            errors.append("USE_COUNT_INVALID")
    elif definition.use_count is not None:
        errors.append("USE_COUNT_UNEXPECTED")

    if definition.stacking is EffectStacking.ADDITIVE_CAPPED:
        if (
            type(definition.stack_cap) is not int
            or not 2 <= definition.stack_cap <= MAX_STACK_CAP
        ):
            errors.append("STACK_CAP_INVALID")
    elif definition.stack_cap != 1:
        errors.append("STACK_CAP_UNEXPECTED")

    primitive = definition.primitive
    key = definition.target_key
    if primitive is EffectPrimitive.STAT_FLAT_TEMPORARY:
        if key not in RUNTIME_STAT_KEYS:
            errors.append("STAT_KEY_UNREGISTERED")
        if definition.duration is EffectDuration.INSTANT:
            errors.append("TEMPORARY_STAT_REQUIRES_DURATION")
        if definition.magnitude == 0:
            errors.append("STAT_MAGNITUDE_ZERO")
    elif primitive in (
        EffectPrimitive.STATE_TAG_APPLY,
        EffectPrimitive.STATE_TAG_REMOVE,
    ):
        if key not in state_tag_keys:
            errors.append("STATE_TAG_UNREGISTERED")
        if definition.magnitude != 0:
            errors.append("STATE_TAG_MAGNITUDE_MUST_BE_ZERO")
        if (
            primitive is EffectPrimitive.STATE_TAG_REMOVE
            and definition.duration is not EffectDuration.INSTANT
        ):
            errors.append("STATE_TAG_REMOVE_MUST_BE_INSTANT")
    elif primitive in (
        EffectPrimitive.RESOURCE_GENERATE,
        EffectPrimitive.RESOURCE_CONSUME,
    ):
        if key not in resource_keys:
            errors.append("RESOURCE_KEY_UNREGISTERED")
        if definition.magnitude <= 0:
            errors.append("RESOURCE_MAGNITUDE_NOT_POSITIVE")
        if definition.duration is not EffectDuration.INSTANT:
            errors.append("RESOURCE_EFFECT_MUST_BE_INSTANT")
    elif primitive is EffectPrimitive.FEEDBACK_ONLY:
        if key is not None:
            errors.append("FEEDBACK_TARGET_KEY_FORBIDDEN")
        if definition.magnitude != 0:
            errors.append("FEEDBACK_MAGNITUDE_MUST_BE_ZERO")
        if definition.duration is not EffectDuration.INSTANT:
            errors.append("FEEDBACK_MUST_BE_INSTANT")
    else:
        errors.append("PRIMITIVE_UNSUPPORTED")

    if (
        definition.duration is EffectDuration.INSTANT
        and definition.stacking is not EffectStacking.NONE
    ):
        errors.append("INSTANT_STACKING_FORBIDDEN")
    return tuple(errors)


@dataclass(frozen=True)
class EffectRegistry:
    """Immutable tuple-backed registry; constructing one never mutates globals."""

    definitions: Tuple[EffectDefinition, ...] = ()
    state_tag_keys: frozenset[str] = DEFAULT_STATE_TAG_KEYS
    resource_keys: frozenset[str] = DEFAULT_RESOURCE_KEYS

    def __post_init__(self) -> None:
        if not isinstance(self.definitions, tuple):
            raise EffectDefinitionError("REGISTRY_DEFINITIONS_NOT_IMMUTABLE_TUPLE")
        if not isinstance(self.state_tag_keys, frozenset):
            raise EffectDefinitionError("STATE_TAG_KEYS_NOT_IMMUTABLE")
        if not isinstance(self.resource_keys, frozenset):
            raise EffectDefinitionError("RESOURCE_KEYS_NOT_IMMUTABLE")
        seen: set[tuple[str, int]] = set()
        for definition in self.definitions:
            errors = validate_definition(
                definition,
                state_tag_keys=self.state_tag_keys,
                resource_keys=self.resource_keys,
            )
            if errors:
                raise EffectDefinitionError(
                    f"{definition.effect_id}@{definition.version}: {','.join(errors)}"
                )
            key = (definition.effect_id, definition.version)
            if key in seen:
                raise EffectDefinitionError(
                    f"{definition.effect_id}@{definition.version}: DUPLICATE_DEFINITION"
                )
            seen.add(key)

    @classmethod
    def from_iterable(
        cls,
        definitions: Iterable[EffectDefinition],
        *,
        state_tag_keys: frozenset[str] = DEFAULT_STATE_TAG_KEYS,
        resource_keys: frozenset[str] = DEFAULT_RESOURCE_KEYS,
    ) -> "EffectRegistry":
        return cls(
            definitions=tuple(definitions),
            state_tag_keys=state_tag_keys,
            resource_keys=resource_keys,
        )

    def get(self, effect_id: str, version: int) -> Optional[EffectDefinition]:
        for definition in self.definitions:
            if definition.effect_id == effect_id and definition.version == version:
                return definition
        return None

    def has_effect_id(self, effect_id: str) -> bool:
        return any(d.effect_id == effect_id for d in self.definitions)


# P1 intentionally ships no gameplay definition. Void Echo remains a test fixture.
DEFAULT_EFFECT_DEFINITIONS: Tuple[EffectDefinition, ...] = ()
DEFAULT_EFFECT_REGISTRY = EffectRegistry(DEFAULT_EFFECT_DEFINITIONS)


__all__ = [
    "DEFAULT_EFFECT_DEFINITIONS",
    "DEFAULT_EFFECT_REGISTRY",
    "DEFAULT_RESOURCE_KEYS",
    "DEFAULT_STATE_TAG_KEYS",
    "EFFECT_ID_MAX_BYTES",
    "EffectDefinitionError",
    "EffectRegistry",
    "IDENTIFIER_MAX_BYTES",
    "I18N_KEY_MAX_BYTES",
    "MAX_ABS_MAGNITUDE",
    "MAX_DEFINITION_TAGS",
    "MAX_STACK_CAP",
    "MAX_USE_COUNT",
    "RUNTIME_STAT_KEYS",
    "TAG_MAX_BYTES",
    "validate_definition",
]
