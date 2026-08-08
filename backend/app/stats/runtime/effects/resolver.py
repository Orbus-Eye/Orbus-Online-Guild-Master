"""Pure deterministic effect resolution for RT2-C-P1."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from typing import Iterable, Optional, Sequence, Tuple

from .models import (
    EffectAuditIntent,
    EffectDefinition,
    EffectDuration,
    EffectFeedbackEvent,
    EffectFeedbackKind,
    EffectInstance,
    EffectLifecycleEvent,
    EffectLifecycleStatus,
    EffectMutationAction,
    EffectMutationIntent,
    EffectPrimitive,
    EffectReceiptPayload,
    EffectRequest,
    EffectResolution,
    EffectResultCode,
    EffectStacking,
    EffectTargetScope,
    EffectTrigger,
)
from .registry import (
    EFFECT_ID_MAX_BYTES,
    IDENTIFIER_MAX_BYTES,
    EffectRegistry,
)


MAX_ACTIVE_INSTANCES = 16
MAX_EFFECTS_PER_ROOT_EVENT = 8
MAX_FEEDBACK_PER_RESOLUTION = 8
MAX_TRIGGER_DEPTH = 1
EVENT_ID_MAX_BYTES = 96
IDEMPOTENCY_KEY_MAX_BYTES = 96
APPLICATION_ID_MAX_BYTES = 32
EFFECT_INSTANCE_ID_MAX_BYTES = 40


def _byte_len(value: str) -> int:
    return len(value.encode("utf-8"))


def _request_errors(request: EffectRequest) -> Tuple[str, ...]:
    errors: list[str] = []
    for value, name, max_bytes in (
        (request.expedition_id, "EXPEDITION_ID", IDENTIFIER_MAX_BYTES),
        (request.event_id, "EVENT_ID", EVENT_ID_MAX_BYTES),
        (request.effect_id, "EFFECT_ID", EFFECT_ID_MAX_BYTES),
        (request.source_adventurer_id, "SOURCE_ID", IDENTIFIER_MAX_BYTES),
        (request.target_id, "TARGET_ID", IDENTIFIER_MAX_BYTES),
        (request.application_id, "APPLICATION_ID", APPLICATION_ID_MAX_BYTES),
        (request.idempotency_key, "IDEMPOTENCY_KEY", IDEMPOTENCY_KEY_MAX_BYTES),
    ):
        if not isinstance(value, str) or not value:
            errors.append(f"{name}_EMPTY")
        elif _byte_len(value) > max_bytes:
            errors.append(f"{name}_TOO_LONG")
    if type(request.effect_version) is not int or request.effect_version < 1:
        errors.append("EFFECT_VERSION_INVALID")
    if type(request.root_event_sequence) is not int or request.root_event_sequence < 1:
        errors.append("ROOT_EVENT_SEQUENCE_INVALID")
    if request.expected_state_version is not None and (
        type(request.expected_state_version) is not int
        or request.expected_state_version < 1
    ):
        errors.append("EXPECTED_STATE_VERSION_INVALID")
    if type(request.trigger_depth) is not int or request.trigger_depth < 0:
        errors.append("TRIGGER_DEPTH_INVALID")
    if not isinstance(request.trigger, EffectTrigger):
        errors.append("TRIGGER_INVALID")
    return tuple(errors)


def _lifecycle_errors(event: EffectLifecycleEvent) -> Tuple[str, ...]:
    errors: list[str] = []
    for value, name, max_bytes in (
        (event.expedition_id, "EXPEDITION_ID", IDENTIFIER_MAX_BYTES),
        (event.event_id, "EVENT_ID", EVENT_ID_MAX_BYTES),
    ):
        if not isinstance(value, str) or not value:
            errors.append(f"{name}_EMPTY")
        elif _byte_len(value) > max_bytes:
            errors.append(f"{name}_TOO_LONG")
    if type(event.root_event_sequence) is not int or event.root_event_sequence < 1:
        errors.append("ROOT_EVENT_SEQUENCE_INVALID")
    if type(event.trigger_depth) is not int or event.trigger_depth < 0:
        errors.append("TRIGGER_DEPTH_INVALID")
    if not isinstance(event.trigger, EffectTrigger):
        errors.append("TRIGGER_INVALID")
    if not isinstance(event.consumed_instance_ids, tuple):
        errors.append("CONSUMED_INSTANCE_IDS_NOT_IMMUTABLE_TUPLE")
        consumed_ids = ()
    else:
        consumed_ids = event.consumed_instance_ids
    if len(set(consumed_ids)) != len(consumed_ids):
        errors.append("CONSUMED_INSTANCE_IDS_DUPLICATED")
    for instance_id in consumed_ids:
        if (
            not isinstance(instance_id, str)
            or not instance_id
            or _byte_len(instance_id) > EFFECT_INSTANCE_ID_MAX_BYTES
        ):
            errors.append("EFFECT_INSTANCE_ID_INVALID")
    return tuple(errors)


def validate_effect_request(request: EffectRequest) -> Tuple[str, ...]:
    """Public, pure syntax validation for integration boundaries."""

    return _request_errors(request)


def validate_lifecycle_event(event: EffectLifecycleEvent) -> Tuple[str, ...]:
    """Public, pure syntax validation before any store access."""

    return _lifecycle_errors(event)


def deterministic_instance_id(request: EffectRequest) -> str:
    """Derive a stable bounded identity from authoritative request fields."""

    material = "\x1f".join(
        (
            request.expedition_id,
            request.event_id,
            str(request.root_event_sequence),
            request.effect_id,
            str(request.effect_version),
            request.source_adventurer_id,
            request.target_id,
            request.application_id,
            request.idempotency_key,
        )
    ).encode("utf-8")
    return "fx_" + sha256(material).hexdigest()[:32]


def effect_order_key(
    definition: EffectDefinition,
    request: EffectRequest,
) -> tuple[int, int, str]:
    return (
        definition.priority,
        request.root_event_sequence,
        deterministic_instance_id(request),
    )


def instance_order_key(instance: EffectInstance) -> tuple[int, int, str]:
    return (
        instance.definition_priority,
        instance.root_event_sequence,
        instance.effect_instance_id,
    )


def _audit(
    *,
    event_id: str,
    effect_id: str,
    audit_class: str,
    code: EffectResultCode,
    reasons: Tuple[str, ...] = (),
    instance_ids: Tuple[str, ...] = (),
) -> EffectAuditIntent:
    return EffectAuditIntent(
        event_id=event_id,
        effect_id=effect_id,
        audit_class=audit_class,
        result_code=code,
        reason_codes=reasons,
        effect_instance_ids=instance_ids,
    )


def _receipt(
    *,
    event_id: str,
    effect_id: str,
    code: EffectResultCode,
    created: Sequence[EffectInstance] = (),
    updated: Sequence[EffectInstance] = (),
    removed: Sequence[EffectInstance] = (),
) -> EffectReceiptPayload:
    ids = tuple(
        i.effect_instance_id for i in tuple(created) + tuple(updated) + tuple(removed)
    )
    return EffectReceiptPayload(
        event_id=event_id,
        effect_id=effect_id,
        result_code=code,
        effect_instance_ids=ids,
        created_count=len(created),
        updated_count=len(updated),
        removed_count=len(removed),
    )


def _reject(
    request: EffectRequest,
    code: EffectResultCode,
    reasons: Tuple[str, ...],
    *,
    audit_class: str = "effect_resolution",
) -> EffectResolution:
    return EffectResolution(
        accepted=False,
        result_code=code,
        audit_intents=(
            _audit(
                event_id=request.event_id,
                effect_id=request.effect_id,
                audit_class=audit_class,
                code=code,
                reasons=reasons,
            ),
        ),
        receipt_payload=_receipt(
            event_id=request.event_id,
            effect_id=request.effect_id,
            code=code,
        ),
    )


def _mutation(
    definition: EffectDefinition,
    instance: Optional[EffectInstance],
    *,
    action: EffectMutationAction,
    amount: Optional[int] = None,
) -> Optional[EffectMutationIntent]:
    if definition.primitive is EffectPrimitive.FEEDBACK_ONLY:
        return None
    resolved = definition.magnitude if amount is None else amount
    if definition.primitive is EffectPrimitive.RESOURCE_CONSUME:
        resolved = -abs(resolved)
    if action is EffectMutationAction.REMOVE:
        if definition.primitive is EffectPrimitive.STAT_FLAT_TEMPORARY:
            resolved = -resolved
        elif definition.primitive is EffectPrimitive.STATE_TAG_APPLY:
            resolved = 0
        else:
            return None
    return EffectMutationIntent(
        primitive=definition.primitive,
        action=action,
        target_id=instance.target_id if instance else "",
        target_key=definition.target_key,
        amount=resolved,
        effect_instance_id=instance.effect_instance_id if instance else None,
    )


def _feedback(
    request: EffectRequest,
    definition: EffectDefinition,
    *,
    instance_id: Optional[str],
    kind: EffectFeedbackKind,
    stack_count: int,
    ordering_hint: int = 0,
) -> EffectFeedbackEvent:
    return EffectFeedbackEvent(
        event_id=request.event_id,
        effect_instance_id=instance_id,
        kind=kind,
        source_adventurer_id=request.source_adventurer_id,
        target_id=request.target_id,
        i18n_key=definition.i18n_key,
        magnitude=definition.magnitude,
        stack_count_after=stack_count,
        visibility=definition.visibility,
        ordering_hint=ordering_hint,
    )


def _new_instance(
    request: EffectRequest,
    definition: EffectDefinition,
) -> EffectInstance:
    return EffectInstance(
        effect_instance_id=deterministic_instance_id(request),
        effect_id=definition.effect_id,
        effect_version=definition.version,
        source_adventurer_id=request.source_adventurer_id,
        target_id=request.target_id,
        application_id=request.application_id,
        root_event_sequence=request.root_event_sequence,
        primitive=definition.primitive,
        target_key=definition.target_key,
        resolved_magnitude=definition.magnitude,
        duration=definition.duration,
        remaining_uses=definition.use_count,
        stack_count=1,
        definition_priority=definition.priority,
    )


def resolve_effect(
    request: EffectRequest,
    registry: EffectRegistry,
    active_instances: Sequence[EffectInstance] = (),
) -> EffectResolution:
    """Resolve one request without mutating the supplied registry or state."""

    errors = _request_errors(request)
    if errors:
        return _reject(request, EffectResultCode.EFFECT_REQUEST_INVALID, errors)
    if request.trigger_depth > MAX_TRIGGER_DEPTH:
        return _reject(
            request,
            EffectResultCode.EFFECT_TRIGGER_DEPTH_EXCEEDED,
            ("TRIGGER_DEPTH_EXCEEDED",),
        )
    if len(active_instances) > MAX_ACTIVE_INSTANCES:
        return _reject(
            request,
            EffectResultCode.EFFECT_CAP_EXCEEDED,
            ("ACTIVE_INSTANCE_CAP_EXCEEDED",),
        )

    definition = registry.get(request.effect_id, request.effect_version)
    if definition is None:
        code = (
            EffectResultCode.EFFECT_VERSION_MISMATCH
            if registry.has_effect_id(request.effect_id)
            else EffectResultCode.EFFECT_DEFINITION_UNKNOWN
        )
        return _reject(request, code, (code.value,))
    if request.trigger is not definition.trigger:
        return _reject(
            request,
            EffectResultCode.EFFECT_REQUEST_INVALID,
            ("TRIGGER_MISMATCH",),
            audit_class=definition.audit_class,
        )
    if (
        definition.target_scope is EffectTargetScope.SELF
        and request.target_id != request.source_adventurer_id
    ):
        return _reject(
            request,
            EffectResultCode.EFFECT_REQUEST_INVALID,
            ("SELF_TARGET_MISMATCH",),
            audit_class=definition.audit_class,
        )

    instance_id = deterministic_instance_id(request)
    for existing in active_instances:
        if existing.effect_instance_id == instance_id:
            feedback = _feedback(
                request,
                definition,
                instance_id=instance_id,
                kind=EffectFeedbackKind.DEDUPLICATED,
                stack_count=existing.stack_count,
            )
            return EffectResolution(
                accepted=True,
                result_code=EffectResultCode.EFFECT_RESOLVED,
                feedback_events=(feedback,),
                audit_intents=(
                    _audit(
                        event_id=request.event_id,
                        effect_id=request.effect_id,
                        audit_class=definition.audit_class,
                        code=EffectResultCode.EFFECT_RESOLVED,
                        reasons=("DETERMINISTIC_REPLAY_NO_OP",),
                        instance_ids=(instance_id,),
                    ),
                ),
                receipt_payload=_receipt(
                    event_id=request.event_id,
                    effect_id=request.effect_id,
                    code=EffectResultCode.EFFECT_RESOLVED,
                ),
            )

    if definition.duration is EffectDuration.INSTANT:
        feedback = _feedback(
            request,
            definition,
            instance_id=None,
            kind=EffectFeedbackKind.FEEDBACK,
            stack_count=0,
        )
        intent = _mutation(
            definition,
            replace(
                _new_instance(request, definition),
                lifecycle_status=EffectLifecycleStatus.RESOLVED,
            ),
            action=EffectMutationAction.APPLY,
        )
        intents = () if intent is None else (intent,)
        return EffectResolution(
            accepted=True,
            result_code=EffectResultCode.EFFECT_RESOLVED,
            mutation_intents=intents,
            feedback_events=(feedback,),
            audit_intents=(
                _audit(
                    event_id=request.event_id,
                    effect_id=request.effect_id,
                    audit_class=definition.audit_class,
                    code=EffectResultCode.EFFECT_RESOLVED,
                ),
            ),
            receipt_payload=_receipt(
                event_id=request.event_id,
                effect_id=request.effect_id,
                code=EffectResultCode.EFFECT_RESOLVED,
            ),
        )

    matching = tuple(
        sorted(
            (
                item
                for item in active_instances
                if item.lifecycle_status is EffectLifecycleStatus.ACTIVE
                and item.effect_id == definition.effect_id
                and item.effect_version == definition.version
                and item.target_id == request.target_id
                and item.target_key == definition.target_key
            ),
            key=instance_order_key,
        )
    )
    if matching and definition.stacking is EffectStacking.NONE:
        return _reject(
            request,
            EffectResultCode.EFFECT_STACKING_REJECTED,
            ("STACKING_NONE_ALREADY_ACTIVE",),
            audit_class=definition.audit_class,
        )

    if matching and definition.stacking is EffectStacking.REFRESH:
        current = matching[0]
        updated = replace(
            current,
            application_id=request.application_id,
            root_event_sequence=request.root_event_sequence,
            remaining_uses=definition.use_count,
        )
        feedback = _feedback(
            request,
            definition,
            instance_id=current.effect_instance_id,
            kind=EffectFeedbackKind.REFRESHED,
            stack_count=current.stack_count,
        )
        return _success(request, definition, updated=(updated,), feedback=(feedback,))

    if matching and definition.stacking is EffectStacking.REPLACE:
        removed = matching
        created = _new_instance(request, definition)
        intents: list[EffectMutationIntent] = []
        for old in removed:
            old_definition = registry.get(old.effect_id, old.effect_version)
            if old_definition:
                intent = _mutation(
                    old_definition,
                    old,
                    action=EffectMutationAction.REMOVE,
                    amount=old.resolved_magnitude * old.stack_count,
                )
                if intent:
                    intents.append(intent)
        applied = _mutation(
            definition,
            created,
            action=EffectMutationAction.APPLY,
        )
        if applied:
            intents.append(applied)
        feedback = _feedback(
            request,
            definition,
            instance_id=created.effect_instance_id,
            kind=EffectFeedbackKind.REPLACED,
            stack_count=1,
        )
        return _success(
            request,
            definition,
            created=(created,),
            removed=removed,
            intents=tuple(intents),
            feedback=(feedback,),
        )

    if matching and definition.stacking is EffectStacking.ADDITIVE_CAPPED:
        current = matching[0]
        if current.stack_count >= definition.stack_cap:
            return _reject(
                request,
                EffectResultCode.EFFECT_STACKING_REJECTED,
                ("ADDITIVE_STACK_CAP_REACHED",),
                audit_class=definition.audit_class,
            )
        updated = replace(
            current,
            application_id=request.application_id,
            root_event_sequence=request.root_event_sequence,
            remaining_uses=definition.use_count,
            stack_count=current.stack_count + 1,
        )
        intent = _mutation(
            definition,
            updated,
            action=EffectMutationAction.APPLY,
            amount=definition.magnitude,
        )
        feedback = _feedback(
            request,
            definition,
            instance_id=current.effect_instance_id,
            kind=EffectFeedbackKind.STACKED,
            stack_count=updated.stack_count,
        )
        return _success(
            request,
            definition,
            updated=(updated,),
            intents=() if intent is None else (intent,),
            feedback=(feedback,),
        )

    if len(active_instances) >= MAX_ACTIVE_INSTANCES:
        return _reject(
            request,
            EffectResultCode.EFFECT_CAP_EXCEEDED,
            ("ACTIVE_INSTANCE_CAP_REACHED",),
            audit_class=definition.audit_class,
        )
    created = _new_instance(request, definition)
    intent = _mutation(definition, created, action=EffectMutationAction.APPLY)
    feedback = _feedback(
        request,
        definition,
        instance_id=created.effect_instance_id,
        kind=EffectFeedbackKind.APPLIED,
        stack_count=1,
    )
    return _success(
        request,
        definition,
        created=(created,),
        intents=() if intent is None else (intent,),
        feedback=(feedback,),
    )


def _success(
    request: EffectRequest,
    definition: EffectDefinition,
    *,
    created: Tuple[EffectInstance, ...] = (),
    updated: Tuple[EffectInstance, ...] = (),
    removed: Tuple[EffectInstance, ...] = (),
    intents: Tuple[EffectMutationIntent, ...] = (),
    feedback: Tuple[EffectFeedbackEvent, ...] = (),
) -> EffectResolution:
    ids = tuple(instance.effect_instance_id for instance in created + updated + removed)
    return EffectResolution(
        accepted=True,
        result_code=EffectResultCode.EFFECT_RESOLVED,
        created_instances=created,
        updated_instances=updated,
        removed_instances=removed,
        mutation_intents=intents,
        feedback_events=feedback[:MAX_FEEDBACK_PER_RESOLUTION],
        audit_intents=(
            _audit(
                event_id=request.event_id,
                effect_id=request.effect_id,
                audit_class=definition.audit_class,
                code=EffectResultCode.EFFECT_RESOLVED,
                instance_ids=ids,
            ),
        ),
        receipt_payload=_receipt(
            event_id=request.event_id,
            effect_id=request.effect_id,
            code=EffectResultCode.EFFECT_RESOLVED,
            created=created,
            updated=updated,
            removed=removed,
        ),
    )


def resolve_effects(
    requests: Iterable[EffectRequest],
    registry: EffectRegistry,
    active_instances: Sequence[EffectInstance] = (),
) -> Tuple[EffectResolution, ...]:
    """Resolve a bounded batch using the canonical deterministic tie-break."""

    batch = tuple(requests)
    if len(batch) > MAX_EFFECTS_PER_ROOT_EVENT:
        return tuple(
            _reject(
                request,
                EffectResultCode.EFFECT_CAP_EXCEEDED,
                ("EFFECTS_PER_ROOT_EVENT_CAP_EXCEEDED",),
            )
            for request in batch
        )

    def key(request: EffectRequest) -> tuple[int, int, str]:
        definition = registry.get(request.effect_id, request.effect_version)
        priority = definition.priority if definition else 10_001
        errors = _request_errors(request)
        if errors:
            sequence = (
                request.root_event_sequence
                if type(request.root_event_sequence) is int
                else 0
            )
            identity = sha256(repr(request).encode("utf-8")).hexdigest()[:32]
            return priority, sequence, identity
        return priority, request.root_event_sequence, deterministic_instance_id(request)

    state = list(active_instances)
    resolutions: list[EffectResolution] = []
    for request in sorted(batch, key=key):
        resolution = resolve_effect(request, registry, tuple(state))
        resolutions.append(resolution)
        if resolution.accepted:
            removed_ids = {
                item.effect_instance_id for item in resolution.removed_instances
            }
            updated_by_id = {
                item.effect_instance_id: item for item in resolution.updated_instances
            }
            state = [
                updated_by_id.get(item.effect_instance_id, item)
                for item in state
                if item.effect_instance_id not in removed_ids
            ]
            state.extend(resolution.created_instances)
    return tuple(resolutions)


def resolve_lifecycle_event(
    event: EffectLifecycleEvent,
    registry: EffectRegistry,
    active_instances: Sequence[EffectInstance],
) -> EffectResolution:
    """Resolve phase/expedition boundaries and explicit USE_COUNT consumption."""

    errors = _lifecycle_errors(event)
    pseudo_request = EffectRequest(
        expedition_id=event.expedition_id,
        event_id=event.event_id,
        root_event_sequence=event.root_event_sequence,
        effect_id="effect_lifecycle",
        effect_version=1,
        trigger=event.trigger,
        source_adventurer_id="system",
        target_id="system",
        application_id="lifecycle",
        idempotency_key=event.event_id,
        trigger_depth=event.trigger_depth,
    )
    if errors:
        return _reject(pseudo_request, EffectResultCode.EFFECT_REQUEST_INVALID, errors)
    if event.trigger_depth > MAX_TRIGGER_DEPTH:
        return _reject(
            pseudo_request,
            EffectResultCode.EFFECT_TRIGGER_DEPTH_EXCEEDED,
            ("TRIGGER_DEPTH_EXCEEDED",),
        )
    if len(active_instances) > MAX_ACTIVE_INSTANCES:
        return _reject(
            pseudo_request,
            EffectResultCode.EFFECT_CAP_EXCEEDED,
            ("ACTIVE_INSTANCE_CAP_EXCEEDED",),
        )

    consumed = set(event.consumed_instance_ids)
    if event.trigger is not EffectTrigger.ON_EVENT_COMPLETION and consumed:
        return _reject(
            pseudo_request,
            EffectResultCode.EFFECT_REQUEST_INVALID,
            ("CONSUMED_IDS_ONLY_ALLOWED_ON_EVENT_COMPLETION",),
        )
    known_ids = {instance.effect_instance_id for instance in active_instances}
    if consumed - known_ids:
        return _reject(
            pseudo_request,
            EffectResultCode.EFFECT_INSTANCE_NOT_FOUND,
            tuple(sorted(consumed - known_ids)),
        )

    candidates: list[EffectInstance] = []
    for instance in sorted(active_instances, key=instance_order_key):
        should_process = (
            event.trigger is EffectTrigger.ON_EXPEDITION_END
            or (
                event.trigger is EffectTrigger.ON_PHASE_END
                and instance.duration is EffectDuration.UNTIL_PHASE_END
            )
            or (
                event.trigger is EffectTrigger.ON_EVENT_COMPLETION
                and instance.effect_instance_id in consumed
            )
        )
        if should_process:
            candidates.append(instance)
    if len(candidates) > MAX_EFFECTS_PER_ROOT_EVENT:
        return _reject(
            pseudo_request,
            EffectResultCode.EFFECT_CAP_EXCEEDED,
            ("LIFECYCLE_EFFECT_CAP_EXCEEDED",),
        )

    updated: list[EffectInstance] = []
    removed: list[EffectInstance] = []
    intents: list[EffectMutationIntent] = []
    feedback: list[EffectFeedbackEvent] = []
    audits: list[EffectAuditIntent] = []
    for order, instance in enumerate(candidates):
        definition = registry.get(instance.effect_id, instance.effect_version)
        if definition is None:
            return _reject(
                pseudo_request,
                (
                    EffectResultCode.EFFECT_VERSION_MISMATCH
                    if registry.has_effect_id(instance.effect_id)
                    else EffectResultCode.EFFECT_DEFINITION_UNKNOWN
                ),
                (instance.effect_instance_id,),
            )
        if (
            event.trigger is EffectTrigger.ON_EVENT_COMPLETION
            and instance.duration is not EffectDuration.USE_COUNT
        ):
            return _reject(
                pseudo_request,
                EffectResultCode.EFFECT_REQUEST_INVALID,
                ("CONSUMED_INSTANCE_NOT_USE_COUNT", instance.effect_instance_id),
            )
        if (
            instance.duration is EffectDuration.USE_COUNT
            and event.trigger is EffectTrigger.ON_EVENT_COMPLETION
            and (instance.remaining_uses or 0) > 1
        ):
            next_instance = replace(
                instance,
                remaining_uses=(instance.remaining_uses or 0) - 1,
            )
            updated.append(next_instance)
            continue

        terminal = replace(instance, lifecycle_status=EffectLifecycleStatus.REMOVED)
        removed.append(terminal)
        intent = _mutation(
            definition,
            instance,
            action=EffectMutationAction.REMOVE,
            amount=instance.resolved_magnitude * instance.stack_count,
        )
        if intent:
            intents.append(intent)
        feedback.append(
            EffectFeedbackEvent(
                event_id=event.event_id,
                effect_instance_id=instance.effect_instance_id,
                kind=EffectFeedbackKind.REMOVED,
                source_adventurer_id=instance.source_adventurer_id,
                target_id=instance.target_id,
                i18n_key=definition.i18n_key,
                magnitude=instance.resolved_magnitude,
                stack_count_after=0,
                visibility=definition.visibility,
                ordering_hint=order,
            )
        )
        audits.append(
            _audit(
                event_id=event.event_id,
                effect_id=instance.effect_id,
                audit_class=definition.audit_class,
                code=EffectResultCode.EFFECT_RESOLVED,
                reasons=("LIFECYCLE_REMOVED",),
                instance_ids=(instance.effect_instance_id,),
            )
        )

    receipt = _receipt(
        event_id=event.event_id,
        effect_id="effect_lifecycle",
        code=EffectResultCode.EFFECT_RESOLVED,
        updated=tuple(updated),
        removed=tuple(removed),
    )
    return EffectResolution(
        accepted=True,
        result_code=EffectResultCode.EFFECT_RESOLVED,
        updated_instances=tuple(updated),
        removed_instances=tuple(removed),
        mutation_intents=tuple(intents),
        feedback_events=tuple(feedback),
        audit_intents=tuple(audits),
        receipt_payload=receipt,
    )


__all__ = [
    "APPLICATION_ID_MAX_BYTES",
    "EFFECT_INSTANCE_ID_MAX_BYTES",
    "EVENT_ID_MAX_BYTES",
    "IDEMPOTENCY_KEY_MAX_BYTES",
    "MAX_ACTIVE_INSTANCES",
    "MAX_EFFECTS_PER_ROOT_EVENT",
    "MAX_FEEDBACK_PER_RESOLUTION",
    "MAX_TRIGGER_DEPTH",
    "deterministic_instance_id",
    "effect_order_key",
    "instance_order_key",
    "resolve_effect",
    "resolve_effects",
    "resolve_lifecycle_event",
    "validate_effect_request",
    "validate_lifecycle_event",
]
