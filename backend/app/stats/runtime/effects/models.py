"""RT2-C-P1 immutable contracts for the generic effect foundation.

The foundation deliberately models intent only.  It does not write state,
read a clock, use randomness, emit logs, or perform network/database I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class EffectPrimitive(str, Enum):
    STAT_FLAT_TEMPORARY = "STAT_FLAT_TEMPORARY"
    STATE_TAG_APPLY = "STATE_TAG_APPLY"
    STATE_TAG_REMOVE = "STATE_TAG_REMOVE"
    RESOURCE_GENERATE = "RESOURCE_GENERATE"
    RESOURCE_CONSUME = "RESOURCE_CONSUME"
    FEEDBACK_ONLY = "FEEDBACK_ONLY"


class EffectTrigger(str, Enum):
    ON_EVENT_COMPLETION = "ON_EVENT_COMPLETION"
    ON_PHASE_END = "ON_PHASE_END"
    ON_EXPEDITION_END = "ON_EXPEDITION_END"


class EffectDuration(str, Enum):
    INSTANT = "INSTANT"
    UNTIL_PHASE_END = "UNTIL_PHASE_END"
    UNTIL_EXPEDITION_END = "UNTIL_EXPEDITION_END"
    USE_COUNT = "USE_COUNT"


class EffectStacking(str, Enum):
    NONE = "NONE"
    REFRESH = "REFRESH"
    REPLACE = "REPLACE"
    ADDITIVE_CAPPED = "ADDITIVE_CAPPED"


class EffectTargetScope(str, Enum):
    SELF = "SELF"
    TARGET = "TARGET"


class EffectLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    REMOVED = "REMOVED"


class EffectMutationAction(str, Enum):
    APPLY = "APPLY"
    REMOVE = "REMOVE"


class EffectFeedbackKind(str, Enum):
    APPLIED = "APPLIED"
    REFRESHED = "REFRESHED"
    REPLACED = "REPLACED"
    STACKED = "STACKED"
    REMOVED = "REMOVED"
    DEDUPLICATED = "DEDUPLICATED"
    FEEDBACK = "FEEDBACK"


class EffectVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PARTY = "PARTY"
    PRIVATE = "PRIVATE"


class EffectResultCode(str, Enum):
    EFFECT_RESOLVED = "EFFECT_RESOLVED"
    EFFECT_REQUEST_INVALID = "EFFECT_REQUEST_INVALID"
    EFFECT_DEFINITION_UNKNOWN = "EFFECT_DEFINITION_UNKNOWN"
    EFFECT_DEFINITION_INVALID = "EFFECT_DEFINITION_INVALID"
    EFFECT_VERSION_MISMATCH = "EFFECT_VERSION_MISMATCH"
    EFFECT_PRIMITIVE_UNSUPPORTED = "EFFECT_PRIMITIVE_UNSUPPORTED"
    EFFECT_STACKING_REJECTED = "EFFECT_STACKING_REJECTED"
    EFFECT_INSTANCE_NOT_FOUND = "EFFECT_INSTANCE_NOT_FOUND"
    EFFECT_CAP_EXCEEDED = "EFFECT_CAP_EXCEEDED"
    EFFECT_TRIGGER_DEPTH_EXCEEDED = "EFFECT_TRIGGER_DEPTH_EXCEEDED"


@dataclass(frozen=True)
class EffectDefinition:
    effect_id: str
    version: int
    primitive: EffectPrimitive
    trigger: EffectTrigger
    duration: EffectDuration
    target_scope: EffectTargetScope
    target_key: Optional[str]
    magnitude: int
    i18n_key: str
    stacking: EffectStacking = EffectStacking.NONE
    use_count: Optional[int] = None
    stack_cap: int = 1
    priority: int = 100
    tags: Tuple[str, ...] = ()
    audit_class: str = "gameplay_effect"
    visibility: EffectVisibility = EffectVisibility.PARTY


@dataclass(frozen=True)
class EffectRequest:
    expedition_id: str
    event_id: str
    root_event_sequence: int
    effect_id: str
    effect_version: int
    trigger: EffectTrigger
    source_adventurer_id: str
    target_id: str
    application_id: str
    idempotency_key: str
    expected_state_version: Optional[int] = None
    trigger_depth: int = 0


@dataclass(frozen=True)
class EffectLifecycleEvent:
    expedition_id: str
    event_id: str
    root_event_sequence: int
    trigger: EffectTrigger
    consumed_instance_ids: Tuple[str, ...] = ()
    trigger_depth: int = 0


@dataclass(frozen=True)
class EffectInstance:
    effect_instance_id: str
    effect_id: str
    effect_version: int
    source_adventurer_id: str
    target_id: str
    application_id: str
    root_event_sequence: int
    primitive: EffectPrimitive
    target_key: Optional[str]
    resolved_magnitude: int
    duration: EffectDuration
    remaining_uses: Optional[int]
    stack_count: int
    definition_priority: int
    lifecycle_status: EffectLifecycleStatus = EffectLifecycleStatus.ACTIVE


@dataclass(frozen=True)
class EffectMutationIntent:
    primitive: EffectPrimitive
    action: EffectMutationAction
    target_id: str
    target_key: Optional[str]
    amount: int
    effect_instance_id: Optional[str]


@dataclass(frozen=True)
class EffectReceiptPayload:
    event_id: str
    effect_id: str
    result_code: EffectResultCode
    effect_instance_ids: Tuple[str, ...] = ()
    created_count: int = 0
    updated_count: int = 0
    removed_count: int = 0


@dataclass(frozen=True)
class EffectAuditIntent:
    event_id: str
    effect_id: str
    audit_class: str
    result_code: EffectResultCode
    reason_codes: Tuple[str, ...] = ()
    effect_instance_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class EffectFeedbackEvent:
    event_id: str
    effect_instance_id: Optional[str]
    kind: EffectFeedbackKind
    source_adventurer_id: str
    target_id: str
    i18n_key: str
    magnitude: int
    stack_count_after: int
    visibility: EffectVisibility
    ordering_hint: int


@dataclass(frozen=True)
class EffectResolution:
    accepted: bool
    result_code: EffectResultCode
    created_instances: Tuple[EffectInstance, ...] = ()
    updated_instances: Tuple[EffectInstance, ...] = ()
    removed_instances: Tuple[EffectInstance, ...] = ()
    mutation_intents: Tuple[EffectMutationIntent, ...] = ()
    feedback_events: Tuple[EffectFeedbackEvent, ...] = ()
    audit_intents: Tuple[EffectAuditIntent, ...] = ()
    receipt_payload: Optional[EffectReceiptPayload] = None


__all__ = [
    "EffectAuditIntent",
    "EffectDefinition",
    "EffectDuration",
    "EffectFeedbackEvent",
    "EffectFeedbackKind",
    "EffectInstance",
    "EffectLifecycleEvent",
    "EffectLifecycleStatus",
    "EffectMutationAction",
    "EffectMutationIntent",
    "EffectPrimitive",
    "EffectReceiptPayload",
    "EffectRequest",
    "EffectResolution",
    "EffectResultCode",
    "EffectStacking",
    "EffectTargetScope",
    "EffectTrigger",
    "EffectVisibility",
]
