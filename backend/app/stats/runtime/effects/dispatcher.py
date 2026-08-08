"""RT2-C-P2 guarded state-store integration for generic effects.

The dispatcher is dependency-injected and not wired into public application
routes.  It enforces the server-side effect gate before the first store call,
uses the existing lease/fencing/CAS contract, and persists only the canonical
top-level active-effect tuple plus the unchanged EventReceipt ring.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Optional, Sequence

from app.stats.runtime.effects.models import (
    EffectAuditIntent,
    EffectDuration,
    EffectInstance,
    EffectLifecycleEvent,
    EffectPrimitive,
    EffectReceiptPayload,
    EffectRequest,
    EffectResolution,
    EffectResultCode,
)
from app.stats.runtime.effects.registry import EffectRegistry
from app.stats.runtime.effects.resolver import (
    instance_order_key,
    resolve_effect,
    resolve_lifecycle_event,
    validate_lifecycle_event,
)
from app.stats.runtime.effects.serialization import measure_bson_feasibility
from app.stats.runtime.state_store.errors import StoreInfraError
from app.stats.runtime.state_store.interface import ExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import ExpeditionRuntimeState
from app.stats.runtime.state_store.results import CasResultCode
from app.stats.runtime.wiring.feature_flags import (
    EffectGateContext,
    is_effect_gate_open,
)


MAX_EFFECT_DISPATCH_RETRIES = 3


@dataclass(frozen=True)
class EffectDispatchOutcome:
    resolution: EffectResolution
    cas_result_code: Optional[CasResultCode] = None
    assigned_event_sequence: Optional[int] = None
    state_version_after: Optional[int] = None
    gate_reason: Optional[str] = None
    retry_attempts: int = 0


def _payload_hash(request: EffectRequest) -> str:
    payload = {
        "application_id": request.application_id,
        "effect_id": request.effect_id,
        "effect_version": request.effect_version,
        "expedition_id": request.expedition_id,
        "idempotency_key": request.idempotency_key,
        "source_adventurer_id": request.source_adventurer_id,
        "target_id": request.target_id,
        "trigger": (
            request.trigger.value
            if hasattr(request.trigger, "value")
            else str(request.trigger)
        ),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _lifecycle_payload_hash(event: EffectLifecycleEvent) -> str:
    payload = {
        "consumed_instance_ids": list(event.consumed_instance_ids),
        "expedition_id": event.expedition_id,
        "trigger": (
            event.trigger.value
            if hasattr(event.trigger, "value")
            else str(event.trigger)
        ),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _resolution(
    *,
    event_id: str,
    effect_id: str,
    accepted: bool,
    code: EffectResultCode,
    reason: str,
) -> EffectResolution:
    return EffectResolution(
        accepted=accepted,
        result_code=code,
        audit_intents=(
            EffectAuditIntent(
                event_id=event_id,
                effect_id=effect_id,
                audit_class="effect_dispatch",
                result_code=code,
                reason_codes=(reason,),
            ),
        ),
        receipt_payload=EffectReceiptPayload(
            event_id=event_id,
            effect_id=effect_id,
            result_code=code,
        ),
    )


def _failure_outcome(
    *,
    event_id: str,
    effect_id: str,
    code: EffectResultCode,
    reason: str,
    cas_code: Optional[CasResultCode] = None,
    gate_reason: Optional[str] = None,
    retry_attempts: int = 0,
) -> EffectDispatchOutcome:
    return EffectDispatchOutcome(
        resolution=_resolution(
            event_id=event_id,
            effect_id=effect_id,
            accepted=False,
            code=code,
            reason=reason,
        ),
        cas_result_code=cas_code,
        gate_reason=gate_reason,
        retry_attempts=retry_attempts,
    )


def _deduplicated_outcome(
    *,
    event_id: str,
    effect_id: str,
    sequence: int,
    state_version: int,
) -> EffectDispatchOutcome:
    return EffectDispatchOutcome(
        resolution=_resolution(
            event_id=event_id,
            effect_id=effect_id,
            accepted=True,
            code=EffectResultCode.EFFECT_RESOLVED,
            reason="STORE_RECEIPT_DEDUPLICATED_NO_OP",
        ),
        cas_result_code=CasResultCode.DEDUPLICATED_NO_OP,
        assigned_event_sequence=sequence,
        state_version_after=state_version,
    )


def _apply_resolution(
    active: Sequence[EffectInstance],
    resolution: EffectResolution,
) -> tuple[EffectInstance, ...]:
    removed_ids = {
        instance.effect_instance_id for instance in resolution.removed_instances
    }
    updated = {
        instance.effect_instance_id: instance
        for instance in resolution.updated_instances
    }
    next_instances = [
        updated.get(instance.effect_instance_id, instance)
        for instance in active
        if instance.effect_instance_id not in removed_ids
    ]
    next_instances.extend(resolution.created_instances)
    return tuple(sorted(next_instances, key=instance_order_key))


def _p2_definition_supported(
    primitive: EffectPrimitive,
    duration: EffectDuration,
) -> bool:
    if primitive is EffectPrimitive.FEEDBACK_ONLY:
        return duration is EffectDuration.INSTANT
    return (
        primitive
        in (
            EffectPrimitive.STAT_FLAT_TEMPORARY,
            EffectPrimitive.STATE_TAG_APPLY,
        )
        and duration is not EffectDuration.INSTANT
    )


class EffectDispatcher:
    """Five-condition gated dispatcher for P2 state persistence."""

    def __init__(
        self,
        *,
        store: ExpeditionRuntimeStateStore,
        registry: EffectRegistry,
        gate_context: EffectGateContext,
        worker_id: str = "rt2-c-effect-dispatcher",
    ) -> None:
        self._store = store
        self._registry = registry
        self._gate_context = gate_context
        self._worker_id = worker_id

    async def dispatch(self, request: EffectRequest) -> EffectDispatchOutcome:
        gate_open, gate_reason = is_effect_gate_open(self._gate_context)
        if not gate_open:
            return _failure_outcome(
                event_id=request.event_id,
                effect_id=request.effect_id,
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason=gate_reason,
                gate_reason=gate_reason,
            )

        preflight = resolve_effect(request, self._registry, ())
        if not preflight.accepted:
            return EffectDispatchOutcome(resolution=preflight)
        definition = self._registry.get(request.effect_id, request.effect_version)
        if definition is None:  # defensive; preflight already fails closed
            return EffectDispatchOutcome(resolution=preflight)
        if not _p2_definition_supported(
            definition.primitive,
            definition.duration,
        ):
            return _failure_outcome(
                event_id=request.event_id,
                effect_id=request.effect_id,
                code=EffectResultCode.EFFECT_PRIMITIVE_UNSUPPORTED,
                reason="P2_PERSISTENCE_PRIMITIVE_NOT_INTEGRATED",
            )

        return await self._dispatch_request_with_store(request)

    async def _dispatch_request_with_store(
        self,
        request: EffectRequest,
    ) -> EffectDispatchOutcome:
        payload_hash = _payload_hash(request)
        lease = None
        try:
            lease = await self._store.reserve_writer(
                request.expedition_id,
                self._worker_id,
            )
            if lease.code is not CasResultCode.SUCCESS:
                return _failure_outcome(
                    event_id=request.event_id,
                    effect_id=request.effect_id,
                    code=EffectResultCode.EFFECT_REQUEST_INVALID,
                    reason=lease.code.value,
                    cas_code=lease.code,
                )
            for retry in range(MAX_EFFECT_DISPATCH_RETRIES):
                read = await self._store.get_state(request.expedition_id)
                if read.code is not CasResultCode.SUCCESS or not isinstance(
                    read.state, ExpeditionRuntimeState
                ):
                    return _failure_outcome(
                        event_id=request.event_id,
                        effect_id=request.effect_id,
                        code=EffectResultCode.EFFECT_REQUEST_INVALID,
                        reason=read.code.value,
                        cas_code=read.code,
                        retry_attempts=retry,
                    )
                state = read.state
                prior = state.receipt_for(request.event_id)
                if prior is not None:
                    if prior.payload_hash != payload_hash:
                        return _failure_outcome(
                            event_id=request.event_id,
                            effect_id=request.effect_id,
                            code=EffectResultCode.EFFECT_REQUEST_INVALID,
                            reason="EVENT_ID_PAYLOAD_MISMATCH",
                            cas_code=CasResultCode.EVENT_ID_PAYLOAD_MISMATCH,
                            retry_attempts=retry,
                        )
                    return _deduplicated_outcome(
                        event_id=request.event_id,
                        effect_id=request.effect_id,
                        sequence=prior.assigned_event_sequence,
                        state_version=state.state_version,
                    )

                authoritative = replace(
                    request,
                    root_event_sequence=state.last_event_sequence + 1,
                    expected_state_version=state.state_version,
                )
                resolution = resolve_effect(
                    authoritative,
                    self._registry,
                    state.active_effect_instances,
                )
                if not resolution.accepted:
                    return EffectDispatchOutcome(
                        resolution=resolution,
                        retry_attempts=retry,
                    )
                next_instances = _apply_resolution(
                    state.active_effect_instances,
                    resolution,
                )
                feasibility = measure_bson_feasibility(
                    next_instances,
                    layout="B",
                )
                if not feasibility.passed:
                    return _failure_outcome(
                        event_id=request.event_id,
                        effect_id=request.effect_id,
                        code=EffectResultCode.EFFECT_CAP_EXCEEDED,
                        reason="ACTIVE_EFFECT_BSON_BUDGET_EXCEEDED",
                        retry_attempts=retry,
                    )
                cas = await self._store.apply_event_once(
                    expedition_id=request.expedition_id,
                    event_id=request.event_id,
                    event_type="EFFECT_APPLY",
                    source_adventurer_id=request.source_adventurer_id,
                    payload_hash=payload_hash,
                    expected_state_version=state.state_version,
                    expected_fencing_token=lease.fencing_token or 0,
                    mutation={"active_effect_instances": next_instances},
                )
                if cas.code is CasResultCode.SUCCESS:
                    return EffectDispatchOutcome(
                        resolution=resolution,
                        cas_result_code=cas.code,
                        assigned_event_sequence=cas.assigned_event_sequence,
                        state_version_after=cas.new_state_version,
                        retry_attempts=retry,
                    )
                if cas.code is CasResultCode.DEDUPLICATED_NO_OP:
                    return _deduplicated_outcome(
                        event_id=request.event_id,
                        effect_id=request.effect_id,
                        sequence=cas.assigned_event_sequence or 0,
                        state_version=cas.new_state_version or state.state_version,
                    )
                if cas.code is not CasResultCode.STATE_VERSION_CONFLICT:
                    code = (
                        EffectResultCode.EFFECT_CAP_EXCEEDED
                        if cas.code is CasResultCode.CAP_EXCEEDED
                        else EffectResultCode.EFFECT_REQUEST_INVALID
                    )
                    return _failure_outcome(
                        event_id=request.event_id,
                        effect_id=request.effect_id,
                        code=code,
                        reason=cas.code.value,
                        cas_code=cas.code,
                        retry_attempts=retry,
                    )
            return _failure_outcome(
                event_id=request.event_id,
                effect_id=request.effect_id,
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason="STATE_VERSION_RETRY_CEILING_EXCEEDED",
                cas_code=CasResultCode.STATE_VERSION_CONFLICT,
                retry_attempts=MAX_EFFECT_DISPATCH_RETRIES,
            )
        except StoreInfraError:
            return _failure_outcome(
                event_id=request.event_id,
                effect_id=request.effect_id,
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason="STATE_INFRA_UNAVAILABLE",
            )
        finally:
            if (
                lease is not None
                and lease.code is CasResultCode.SUCCESS
                and lease.lease_id
                and lease.fencing_token is not None
            ):
                try:
                    await self._store.release_writer(
                        request.expedition_id,
                        lease.lease_id,
                        lease.fencing_token,
                    )
                except StoreInfraError:
                    # The committed event remains authoritative; lease TTL is
                    # the fail-safe for an unavailable release operation.
                    pass

    async def dispatch_lifecycle(
        self,
        event: EffectLifecycleEvent,
    ) -> EffectDispatchOutcome:
        gate_open, gate_reason = is_effect_gate_open(self._gate_context)
        if not gate_open:
            return _failure_outcome(
                event_id=event.event_id,
                effect_id="effect_lifecycle",
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason=gate_reason,
                gate_reason=gate_reason,
            )
        validation_errors = validate_lifecycle_event(event)
        if validation_errors:
            return _failure_outcome(
                event_id=event.event_id,
                effect_id="effect_lifecycle",
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason=validation_errors[0],
            )
        payload_hash = _lifecycle_payload_hash(event)
        lease = None
        try:
            lease = await self._store.reserve_writer(
                event.expedition_id,
                self._worker_id,
            )
            if lease.code is not CasResultCode.SUCCESS:
                return _failure_outcome(
                    event_id=event.event_id,
                    effect_id="effect_lifecycle",
                    code=EffectResultCode.EFFECT_REQUEST_INVALID,
                    reason=lease.code.value,
                    cas_code=lease.code,
                )
            for retry in range(MAX_EFFECT_DISPATCH_RETRIES):
                read = await self._store.get_state(event.expedition_id)
                if read.code is not CasResultCode.SUCCESS or not isinstance(
                    read.state, ExpeditionRuntimeState
                ):
                    return _failure_outcome(
                        event_id=event.event_id,
                        effect_id="effect_lifecycle",
                        code=EffectResultCode.EFFECT_REQUEST_INVALID,
                        reason=read.code.value,
                        cas_code=read.code,
                        retry_attempts=retry,
                    )
                state = read.state
                prior = state.receipt_for(event.event_id)
                if prior is not None:
                    if prior.payload_hash != payload_hash:
                        return _failure_outcome(
                            event_id=event.event_id,
                            effect_id="effect_lifecycle",
                            code=EffectResultCode.EFFECT_REQUEST_INVALID,
                            reason="EVENT_ID_PAYLOAD_MISMATCH",
                            cas_code=CasResultCode.EVENT_ID_PAYLOAD_MISMATCH,
                            retry_attempts=retry,
                        )
                    return _deduplicated_outcome(
                        event_id=event.event_id,
                        effect_id="effect_lifecycle",
                        sequence=prior.assigned_event_sequence,
                        state_version=state.state_version,
                    )
                authoritative = replace(
                    event,
                    root_event_sequence=state.last_event_sequence + 1,
                )
                resolution = resolve_lifecycle_event(
                    authoritative,
                    self._registry,
                    state.active_effect_instances,
                )
                if not resolution.accepted:
                    return EffectDispatchOutcome(
                        resolution=resolution,
                        retry_attempts=retry,
                    )
                next_instances = _apply_resolution(
                    state.active_effect_instances,
                    resolution,
                )
                cas = await self._store.apply_event_once(
                    expedition_id=event.expedition_id,
                    event_id=event.event_id,
                    event_type=f"EFFECT_LIFECYCLE_{event.trigger.value}",
                    source_adventurer_id="system",
                    payload_hash=payload_hash,
                    expected_state_version=state.state_version,
                    expected_fencing_token=lease.fencing_token or 0,
                    mutation={"active_effect_instances": next_instances},
                )
                if cas.code is CasResultCode.SUCCESS:
                    return EffectDispatchOutcome(
                        resolution=resolution,
                        cas_result_code=cas.code,
                        assigned_event_sequence=cas.assigned_event_sequence,
                        state_version_after=cas.new_state_version,
                        retry_attempts=retry,
                    )
                if cas.code is CasResultCode.DEDUPLICATED_NO_OP:
                    return _deduplicated_outcome(
                        event_id=event.event_id,
                        effect_id="effect_lifecycle",
                        sequence=cas.assigned_event_sequence or 0,
                        state_version=cas.new_state_version or state.state_version,
                    )
                if cas.code is not CasResultCode.STATE_VERSION_CONFLICT:
                    return _failure_outcome(
                        event_id=event.event_id,
                        effect_id="effect_lifecycle",
                        code=EffectResultCode.EFFECT_REQUEST_INVALID,
                        reason=cas.code.value,
                        cas_code=cas.code,
                        retry_attempts=retry,
                    )
            return _failure_outcome(
                event_id=event.event_id,
                effect_id="effect_lifecycle",
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason="STATE_VERSION_RETRY_CEILING_EXCEEDED",
                cas_code=CasResultCode.STATE_VERSION_CONFLICT,
                retry_attempts=MAX_EFFECT_DISPATCH_RETRIES,
            )
        except StoreInfraError:
            return _failure_outcome(
                event_id=event.event_id,
                effect_id="effect_lifecycle",
                code=EffectResultCode.EFFECT_REQUEST_INVALID,
                reason="STATE_INFRA_UNAVAILABLE",
            )
        finally:
            if (
                lease is not None
                and lease.code is CasResultCode.SUCCESS
                and lease.lease_id
                and lease.fencing_token is not None
            ):
                try:
                    await self._store.release_writer(
                        event.expedition_id,
                        lease.lease_id,
                        lease.fencing_token,
                    )
                except StoreInfraError:
                    pass


__all__ = [
    "EffectDispatchOutcome",
    "EffectDispatcher",
    "MAX_EFFECT_DISPATCH_RETRIES",
]
