"""RT2-B-2B-2-1 · Pure/deterministic Drain state machine (PM Message 170).

DRAIN TRANSITION & COMPLETION-TO-FRAGMENT FOUNDATION.

Ogni funzione:
- Riceve: current `AdventurerClassState` · trusted event fields · authoritative time
- Ritorna: (new_class_state, TransitionResult)
- NON tocca I/O · NON istanzia client Mongo · NON conosce HTTP/frontend
- È deterministica rispetto a inputs identici (l'unica non-determinism è la
  generazione server-side dell'execution ID a START accettato — B2B2Q01)

Verdetti PM Message 170 (verbatim, adjudicated 16/16):
- B2B2Q01 · `drain_execution_id = "drn-" + canonical UUIDv4` (NON troncato ·
  server-authoritative · mai client-provided · mai riusato post-terminal)
- B2B2Q03 · strict application_id invariance (refresh valido NON invalida ·
  nuova application invalida il binding)
- B2B2Q04 · 15-check completion revalidation (checks 1-12 pure-level qui;
  13-15 lease/fencing/state_version enforced dispatcher/store-side)
- B2B2Q05 · fragment_gain_requested fissato = 1 (no RNG · no scaling)
- B2B2Q06 · at-cap: COMPLETED + applied=0 + overflow_discarded=1
- B2B2Q07 · completion payload 15-field EMBEDDED nell'atomic batch (DrainDoc)
  · 1 sola receipt ORDINARY · MAI un secondo slot
- B2B2Q08 · 8 cancellation reason codes verbatim · NO extensions
- B2B2Q14 · lazy Mark-expiration cancellation FOLDED nella receipt ordinaria
  del triggering event (commit-on-rejection · NO seconda receipt)
- PM §18 hard-lock · max 1 Drain attivo per (source,target) pair · max 1 per
  Mark application

Il Drain NON consuma il Mark · NON spende Fragment · NON chiude segment ·
NON muta `focus_bonus_usage` (§30 DEFERRED).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Tuple

from dataclasses import replace

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainCompletionPayload,
    DrainDoc,
    DrainStatus,
    MarkDoc,
)
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ReasonCode,
    TransitionResult,
    TransitionResultCode,
)
from app.stats.runtime.transitions.state_machine import (
    FRAGMENT_CAP,
    _is_mark_active,
    _iso,
)

# ═══════════════════════ Canonical sets ═══════════════════════
# Event types Drain (routing dispatcher).
DRAIN_EVENT_TYPES: frozenset[str] = frozenset({
    ClassEventType.START_DRAIN.value,
    ClassEventType.COMPLETE_DRAIN.value,
    ClassEventType.CANCEL_DRAIN.value,
})

# Result codes che rappresentano un commit valido (success family Drain).
DRAIN_SUCCESS_CODES: frozenset[TransitionResultCode] = frozenset({
    TransitionResultCode.DRAIN_STARTED,
    TransitionResultCode.DRAIN_COMPLETED,
    TransitionResultCode.DRAIN_CANCELLED,
})

# Rejection codes che RICHIEDONO commit della mutation (fold-cancellation
# B2B2Q14: il Drain viene auto-cancellato e il risultato è foldato nella
# receipt ordinaria del triggering event — mai una seconda receipt).
DRAIN_FOLD_COMMIT_CODES: frozenset[TransitionResultCode] = frozenset({
    TransitionResultCode.MARK_EXPIRED,
    TransitionResultCode.MARK_APPLICATION_CHANGED,
    TransitionResultCode.MARK_OWNERSHIP_MISMATCH,
})

# 8 cancellation reason codes canonici (B2B2Q08 verbatim · NO extensions).
CANONICAL_CANCELLATION_REASONS: frozenset[str] = frozenset({
    ReasonCode.MARK_EXPIRED.value,
    ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
    ReasonCode.MARK_APPLICATION_CHANGED.value,
    ReasonCode.TARGET_INVALID.value,
    ReasonCode.SOURCE_INVALID.value,
    ReasonCode.PHASE_ENDED.value,
    ReasonCode.EXPEDITION_TERMINAL.value,
    ReasonCode.EXPLICIT_SERVER_CANCEL.value,
})

# Bounded list cap per lifecycle receipt aggregation (§24 · lista bounded).
LIFECYCLE_CANCELLED_IDS_BOUND: int = 32

# Fragment gain fisso per accepted completion (B2B2Q05 verbatim).
FRAGMENT_GAIN_FIXED: int = 1


# ═══════════════════════ Execution identity (B2B2Q01) ═══════════════════════
def generate_drain_execution_id() -> str:
    """Server-authoritative execution ID: `"drn-" + canonical UUIDv4` completo.

    Vietato (B2B2Q01 verbatim): UUID troncato · client-provided · derivato da
    input · riutilizzabile post-cancel/complete.
    """
    return f"drn-{uuid.uuid4()}"


# ═══════════════════════ Coercion helpers ═══════════════════════
def _coerce_drain(obj) -> DrainDoc:
    """Normalizza un elemento di `active_drain_executions` a DrainDoc.

    Il Mongo adapter rehydrata i drains come raw dicts (fuori file-boundary
    del gate): la coercion avviene qui, application-side.
    """
    if isinstance(obj, DrainDoc):
        return obj
    if isinstance(obj, dict):
        payload = obj.get("completion_payload")
        cp: Optional[DrainCompletionPayload] = None
        if isinstance(payload, dict):
            cp = DrainCompletionPayload(
                drain_execution_id=payload.get("drain_execution_id", ""),
                completion_event_id=payload.get("completion_event_id", ""),
                source_adventurer_id=payload.get("source_adventurer_id", ""),
                target_id=payload.get("target_id", ""),
                mark_id=payload.get("mark_id", ""),
                application_id=payload.get("application_id", ""),
                result_code=payload.get("result_code", ""),
                mark_valid_at_completion=bool(payload.get("mark_valid_at_completion", False)),
                fragment_gain_requested=int(payload.get("fragment_gain_requested", 0)),
                fragment_gain_applied=int(payload.get("fragment_gain_applied", 0)),
                fragment_overflow_discarded=int(payload.get("fragment_overflow_discarded", 0)),
                resource_segment_id=payload.get("resource_segment_id"),
                assigned_event_sequence=int(payload.get("assigned_event_sequence", 0)),
                state_version_after=int(payload.get("state_version_after", 0)),
                processed_at=payload.get("processed_at", ""),
            )
        status_raw = obj.get("runtime_status", DrainStatus.IN_PROGRESS.value)
        try:
            status = DrainStatus(status_raw)
        except ValueError:
            status = DrainStatus.IN_PROGRESS
        return DrainDoc(
            drain_execution_id=obj.get("drain_execution_id", ""),
            source_adventurer_id=obj.get("source_adventurer_id", ""),
            target_id=obj.get("target_id", ""),
            required_mark_application_id=obj.get("required_mark_application_id", ""),
            started_at=obj.get("started_at", ""),
            completed_at=obj.get("completed_at"),
            runtime_status=status,
            resolution_version=int(obj.get("resolution_version", 1)),
            reward_resolved=bool(obj.get("reward_resolved", False)),
            mark_id=obj.get("mark_id", ""),
            cancelled_at=obj.get("cancelled_at"),
            cancellation_reason=obj.get("cancellation_reason"),
            drain_version=int(obj.get("drain_version", 1)),
            start_event_id=obj.get("start_event_id", ""),
            completion_payload=cp,
        )
    raise TypeError(f"unsupported drain entry type: {type(obj)!r}")


def coerce_drains(cs: AdventurerClassState) -> Tuple[DrainDoc, ...]:
    """Tuple di DrainDoc coerced da `cs.active_drain_executions`."""
    return tuple(_coerce_drain(d) for d in cs.active_drain_executions)


def find_drain_by_start_event(
    cs: AdventurerClassState, start_event_id: str,
) -> Optional[DrainDoc]:
    """Replay lookup (B2B2Q01): stesso start event → prior execution ID."""
    if not start_event_id:
        return None
    for d in coerce_drains(cs):
        if d.start_event_id == start_event_id:
            return d
    return None


def _result(
    code: TransitionResultCode,
    *,
    event_type: str,
    event_id: str,
    expedition_id: str,
    source_adventurer_id: str,
    **kwargs,
) -> TransitionResult:
    return TransitionResult(
        code=code,
        event_id=event_id,
        event_type=event_type,
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        **kwargs,
    )


def _replace_drain(
    drains: Tuple[DrainDoc, ...], updated: DrainDoc,
) -> Tuple[DrainDoc, ...]:
    return tuple(
        updated if d.drain_execution_id == updated.drain_execution_id else d
        for d in drains
    )


# ═══════════════════════ START_DRAIN (§13-§14) ═══════════════════════
def start_drain(
    cs: AdventurerClassState,
    *,
    target_id: str,
    now: datetime,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """START_DRAIN: `NOT_STARTED → STARTED` (DrainDoc IN_PROGRESS).

    Precondizioni pure-level (§14): target valido non-self · own active Mark
    su (source,target) non scaduto · ownership · hard-lock pair=1 ·
    hard-lock Mark application=1.
    """
    ctx = dict(
        event_type=ClassEventType.START_DRAIN.value,
        event_id=event_id,
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
    )
    if not source_adventurer_id or source_adventurer_id != cs.adventurer_id:
        return cs, _result(
            TransitionResultCode.SOURCE_INVALID,
            reason_code=ReasonCode.SOURCE_INVALID.value, **ctx,
        )
    if not target_id or target_id == source_adventurer_id:
        return cs, _result(
            TransitionResultCode.TARGET_INVALID,
            reason_code=ReasonCode.TARGET_INVALID.value, **ctx,
        )

    # Mark lookup su pair (lazy validation server-time authoritative).
    pair_mark: Optional[MarkDoc] = None
    pair_mark_expired = False
    for m in cs.active_marks:
        if m.target_id == target_id:
            if _is_mark_active(m, now):
                pair_mark = m
            else:
                pair_mark_expired = True
            break
    if pair_mark is None:
        return cs, _result(
            (TransitionResultCode.MARK_EXPIRED
             if pair_mark_expired else TransitionResultCode.MARK_NOT_FOUND),
            reason_code=(ReasonCode.MARK_EXPIRED.value
                         if pair_mark_expired else "NO_ACTIVE_MARK_FOR_PAIR"),
            **ctx,
        )
    if pair_mark.source_adventurer_id != cs.adventurer_id:
        return cs, _result(
            TransitionResultCode.MARK_OWNERSHIP_MISMATCH,
            reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
            mark_id=pair_mark.mark_id,
            mark_application_id=pair_mark.application_id,
            **ctx,
        )

    # Hard-lock PM §18: max 1 Drain attivo per pair · max 1 per application.
    drains = coerce_drains(cs)
    for d in drains:
        if d.runtime_status is not DrainStatus.IN_PROGRESS:
            continue
        same_pair = (
            d.source_adventurer_id == source_adventurer_id
            and d.target_id == target_id
        )
        same_application = (
            d.mark_id == pair_mark.mark_id
            and d.required_mark_application_id == pair_mark.application_id
        )
        if same_pair or same_application:
            return cs, _result(
                TransitionResultCode.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR,
                reason_code=("PAIR_HARD_LOCK" if same_pair else "APPLICATION_HARD_LOCK"),
                drain_execution_id=d.drain_execution_id,
                mark_id=pair_mark.mark_id,
                mark_application_id=pair_mark.application_id,
                **ctx,
            )

    # Server-generate execution identity (B2B2Q01 verbatim).
    execution_id = generate_drain_execution_id()
    new_drain = DrainDoc(
        drain_execution_id=execution_id,
        source_adventurer_id=source_adventurer_id,
        target_id=target_id,
        required_mark_application_id=pair_mark.application_id,
        started_at=_iso(now),
        runtime_status=DrainStatus.IN_PROGRESS,
        mark_id=pair_mark.mark_id,
        drain_version=1,
        start_event_id=event_id,
    )
    new_cs = replace(
        cs,
        active_drain_executions=drains + (new_drain,),
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, _result(
        TransitionResultCode.DRAIN_STARTED,
        drain_execution_id=execution_id,
        mark_id=pair_mark.mark_id,
        mark_application_id=pair_mark.application_id,
        **ctx,
    )


# ═══════════════════════ COMPLETE_DRAIN (§15-§16 · §26-§29) ═══════════════════════
def complete_drain(
    cs: AdventurerClassState,
    *,
    drain_execution_id: Optional[str],
    now: datetime,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
    next_event_sequence: int = 0,
    state_version_after: int = 0,
) -> Tuple[AdventurerClassState, TransitionResult]:
    """COMPLETE_DRAIN: `STARTED → COMPLETED` + completion-to-Fragment batch.

    Rivalidazioni B2B2Q04 pure-level (checks 1-12; 13-15 lease/fencing/
    state_version dispatcher/store-side). Una sola falsa → rejected o
    fold-cancelled (B2B2Q14) · no Fragment · no partial mutation.

    Atomic batch (B2B2Q07): status RESOLVED · Fragment decision (fixed=1) ·
    overflow discard · segment opening 0→positive · payload EMBEDDED ·
    tutto in un singolo CAS committato dal dispatcher.
    """
    ctx = dict(
        event_type=ClassEventType.COMPLETE_DRAIN.value,
        event_id=event_id,
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
    )
    drains = coerce_drains(cs)
    drain: Optional[DrainDoc] = None
    for d in drains:
        if d.drain_execution_id == (drain_execution_id or ""):
            drain = d
            break
    if drain is None:
        return cs, _result(
            TransitionResultCode.DRAIN_NOT_STARTED,
            reason_code="UNKNOWN_DRAIN_EXECUTION_ID",
            drain_execution_id=drain_execution_id, **ctx,
        )
    # Check 1 · source ownership (foreign complete FORBIDDEN).
    if drain.source_adventurer_id != source_adventurer_id or cs.adventurer_id != source_adventurer_id:
        return cs, _result(
            TransitionResultCode.MARK_OWNERSHIP_MISMATCH,
            reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
            drain_execution_id=drain.drain_execution_id, **ctx,
        )
    # Checks 8-10 · drain state (idempotency · no mutation).
    if drain.runtime_status is DrainStatus.RESOLVED:
        return cs, _result(
            TransitionResultCode.DRAIN_ALREADY_COMPLETED,
            reason_code="DUPLICATE_COMPLETION",
            drain_execution_id=drain.drain_execution_id, **ctx,
        )
    if drain.runtime_status in (DrainStatus.CANCELLED, DrainStatus.EXPIRED):
        return cs, _result(
            TransitionResultCode.DRAIN_ALREADY_CANCELLED,
            reason_code=drain.cancellation_reason or "ALREADY_CANCELLED",
            drain_execution_id=drain.drain_execution_id,
            cancellation_reason=drain.cancellation_reason, **ctx,
        )

    def _fold_cancel(
        code: TransitionResultCode, reason: str,
    ) -> Tuple[AdventurerClassState, TransitionResult]:
        """B2B2Q14: auto-cancel FOLDED nella receipt del triggering event."""
        cancelled = replace(
            drain,
            runtime_status=DrainStatus.CANCELLED,
            cancelled_at=_iso(now),
            cancellation_reason=reason,
            drain_version=drain.drain_version + 1,
        )
        folded_cs = replace(
            cs,
            active_drain_executions=_replace_drain(drains, cancelled),
            class_state_version=cs.class_state_version + 1,
        )
        return folded_cs, _result(
            code,
            reason_code=reason,
            drain_execution_id=drain.drain_execution_id,
            cancellation_reason=reason,
            mark_valid_at_completion=False,
            mark_id=drain.mark_id,
            mark_application_id=drain.required_mark_application_id,
            **ctx,
        )

    # Checks 2 · target binding.
    if not drain.target_id:
        return cs, _result(
            TransitionResultCode.TARGET_INVALID,
            reason_code=ReasonCode.TARGET_INVALID.value,
            drain_execution_id=drain.drain_execution_id, **ctx,
        )
    # Checks 3-7 · Mark revalidation completion-time (B2B2Q03 strict).
    bound_mark: Optional[MarkDoc] = None
    pair_mark_other_application: Optional[MarkDoc] = None
    for m in cs.active_marks:
        if m.mark_id == drain.mark_id:
            bound_mark = m
            break
        if m.target_id == drain.target_id:
            pair_mark_other_application = m
    if bound_mark is None:
        if pair_mark_other_application is not None and _is_mark_active(
            pair_mark_other_application, now,
        ):
            # Scadenza + nuova applicazione → binding invalid (B2B2Q03).
            return _fold_cancel(
                TransitionResultCode.MARK_APPLICATION_CHANGED,
                ReasonCode.MARK_APPLICATION_CHANGED.value,
            )
        return _fold_cancel(
            TransitionResultCode.MARK_EXPIRED, ReasonCode.MARK_EXPIRED.value,
        )
    if bound_mark.source_adventurer_id != source_adventurer_id:
        return _fold_cancel(
            TransitionResultCode.MARK_OWNERSHIP_MISMATCH,
            ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
        )
    if not _is_mark_active(bound_mark, now):
        return _fold_cancel(
            TransitionResultCode.MARK_EXPIRED, ReasonCode.MARK_EXPIRED.value,
        )
    if bound_mark.application_id != drain.required_mark_application_id:
        return _fold_cancel(
            TransitionResultCode.MARK_APPLICATION_CHANGED,
            ReasonCode.MARK_APPLICATION_CHANGED.value,
        )

    # ── Completion-to-Fragment atomic batch (B2B2Q05/Q06/Q07 · §26-§29) ──
    requested = FRAGMENT_GAIN_FIXED
    if cs.fragment_count >= FRAGMENT_CAP:
        applied = 0
        discarded = 1
        new_fragment_count = cs.fragment_count
    else:
        applied = 1
        discarded = 0
        new_fragment_count = cs.fragment_count + 1

    # Resource segment opening SOLO su transizione strict 0 → positive (§29).
    new_segment_id = cs.resource_segment_id
    if cs.fragment_count == 0 and applied > 0:
        new_segment_id = f"sg-{uuid.uuid4().hex[:16]}"

    payload = DrainCompletionPayload(
        drain_execution_id=drain.drain_execution_id,
        completion_event_id=event_id,
        source_adventurer_id=source_adventurer_id,
        target_id=drain.target_id,
        mark_id=drain.mark_id,
        application_id=drain.required_mark_application_id,
        result_code="SUCCESS",
        mark_valid_at_completion=True,
        fragment_gain_requested=requested,
        fragment_gain_applied=applied,
        fragment_overflow_discarded=discarded,
        resource_segment_id=new_segment_id,
        assigned_event_sequence=next_event_sequence,
        state_version_after=state_version_after,
        processed_at=_iso(now),
    )
    resolved = replace(
        drain,
        runtime_status=DrainStatus.RESOLVED,
        completed_at=_iso(now),
        drain_version=drain.drain_version + 1,
        completion_payload=payload,
    )
    new_cs = replace(
        cs,
        active_drain_executions=_replace_drain(drains, resolved),
        fragment_count=new_fragment_count,
        resource_segment_id=new_segment_id,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, _result(
        TransitionResultCode.DRAIN_COMPLETED,
        drain_execution_id=drain.drain_execution_id,
        mark_id=drain.mark_id,
        mark_application_id=drain.required_mark_application_id,
        mark_valid_at_completion=True,
        fragment_gain_requested=requested,
        fragment_gain_applied=applied,
        fragment_overflow_discarded=discarded,
        fragment_count_after=new_fragment_count,
        resource_segment_id=new_segment_id,
        overflow_discarded=discarded,
        **ctx,
    )


# ═══════════════════════ CANCEL_DRAIN (§17-§18) ═══════════════════════
def cancel_drain(
    cs: AdventurerClassState,
    *,
    drain_execution_id: Optional[str],
    now: datetime,
    reason_code: Optional[str] = None,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """CANCEL_DRAIN esplicito: `STARTED → CANCELLED` (terminale).

    Reason canonico obbligatorio (B2B2Q08 · default EXPLICIT_SERVER_CANCEL ·
    reason non canonico → rejection, MAI un nuovo codice).
    """
    ctx = dict(
        event_type=ClassEventType.CANCEL_DRAIN.value,
        event_id=event_id,
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
    )
    reason = reason_code or ReasonCode.EXPLICIT_SERVER_CANCEL.value
    if reason not in CANONICAL_CANCELLATION_REASONS:
        return cs, _result(
            TransitionResultCode.SOURCE_INVALID,
            reason_code="NON_CANONICAL_CANCELLATION_REASON_REJECTED",
            drain_execution_id=drain_execution_id, **ctx,
        )
    drains = coerce_drains(cs)
    drain: Optional[DrainDoc] = None
    for d in drains:
        if d.drain_execution_id == (drain_execution_id or ""):
            drain = d
            break
    if drain is None:
        return cs, _result(
            TransitionResultCode.DRAIN_NOT_STARTED,
            reason_code="UNKNOWN_DRAIN_EXECUTION_ID",
            drain_execution_id=drain_execution_id, **ctx,
        )
    if drain.source_adventurer_id != source_adventurer_id:
        return cs, _result(
            TransitionResultCode.MARK_OWNERSHIP_MISMATCH,
            reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
            drain_execution_id=drain.drain_execution_id, **ctx,
        )
    if drain.runtime_status is DrainStatus.RESOLVED:
        # first-committed-wins (B2B2Q10): completion prima → no mutation.
        return cs, _result(
            TransitionResultCode.DRAIN_ALREADY_COMPLETED,
            reason_code="COMPLETION_COMMITTED_FIRST",
            drain_execution_id=drain.drain_execution_id, **ctx,
        )
    if drain.runtime_status in (DrainStatus.CANCELLED, DrainStatus.EXPIRED):
        return cs, _result(
            TransitionResultCode.DRAIN_ALREADY_CANCELLED,
            reason_code=drain.cancellation_reason or "ALREADY_CANCELLED",
            drain_execution_id=drain.drain_execution_id,
            cancellation_reason=drain.cancellation_reason, **ctx,
        )
    cancelled = replace(
        drain,
        runtime_status=DrainStatus.CANCELLED,
        cancelled_at=_iso(now),
        cancellation_reason=reason,
        drain_version=drain.drain_version + 1,
    )
    new_cs = replace(
        cs,
        active_drain_executions=_replace_drain(drains, cancelled),
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, _result(
        TransitionResultCode.DRAIN_CANCELLED,
        reason_code=reason,
        cancellation_reason=reason,
        drain_execution_id=drain.drain_execution_id,
        mark_id=drain.mark_id,
        mark_application_id=drain.required_mark_application_id,
        **ctx,
    )


# ═══════════════════════ Lifecycle bulk cancellation (§24 · B2B2Q11) ═══════════════════════
def cancel_started_drains_for_lifecycle(
    cs: AdventurerClassState,
    *,
    reason: str,
    now: datetime,
) -> Tuple[AdventurerClassState, Tuple[str, ...]]:
    """Cancella TUTTI i Drain ancora STARTED in un lifecycle batch.

    B2B2Q11 verbatim: phase-end/terminal committed first → all STARTED
    Drains → CANCELLED (reason PHASE_ENDED | EXPEDITION_TERMINAL) ·
    ONE reserved lifecycle receipt per l'INTERO batch (mai per-Drain) ·
    Drain già COMPLETED restano COMPLETED (Fragment assegnato preservato).

    Returns:
        (new_cs, cancelled_execution_ids) — ids bounded a
        LIFECYCLE_CANCELLED_IDS_BOUND nella receipt; count sempre esatto
        via len(cancelled_execution_ids) pre-bound dal caller.
    """
    if reason not in CANONICAL_CANCELLATION_REASONS:
        reason = ReasonCode.EXPLICIT_SERVER_CANCEL.value
    drains = coerce_drains(cs)
    cancelled_ids: list[str] = []
    new_drains: list[DrainDoc] = []
    for d in drains:
        if d.runtime_status is DrainStatus.IN_PROGRESS:
            cancelled_ids.append(d.drain_execution_id)
            new_drains.append(replace(
                d,
                runtime_status=DrainStatus.CANCELLED,
                cancelled_at=_iso(now),
                cancellation_reason=reason,
                drain_version=d.drain_version + 1,
            ))
        else:
            new_drains.append(d)
    if not cancelled_ids:
        return cs, ()
    new_cs = replace(
        cs,
        active_drain_executions=tuple(new_drains),
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, tuple(cancelled_ids)


__all__ = [
    "CANONICAL_CANCELLATION_REASONS",
    "DRAIN_EVENT_TYPES",
    "DRAIN_FOLD_COMMIT_CODES",
    "DRAIN_SUCCESS_CODES",
    "FRAGMENT_GAIN_FIXED",
    "LIFECYCLE_CANCELLED_IDS_BOUND",
    "cancel_drain",
    "cancel_started_drains_for_lifecycle",
    "coerce_drains",
    "complete_drain",
    "find_drain_by_start_event",
    "generate_drain_execution_id",
    "start_drain",
]
