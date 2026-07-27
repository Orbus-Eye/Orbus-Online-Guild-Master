"""RT2-B-2B-2-1 · Drain pure state machine (START · COMPLETE · CANCEL).

PM Message 170 verbatim design (Drain readiness gate `RT2-B-2B-2-P0` §9-§45).

Ogni funzione:
- Riceve: current `AdventurerClassState` · trusted command · authoritative time · policy config
- Ritorna: (new_class_state, TransitionResult, Optional[DrainCompletionReceipt])
- NON tocca I/O · NON istanzia client Mongo · NON conosce HTTP/frontend
- È idempotente rispetto a inputs identici (dedup layer in dispatcher)

Hard-locks (PM Message 170 §18 verbatim):
- max active Drain per (source_adventurer_id, target_id) pair = 1
- max active Drain per Mark application (mark_id, required_mark_application_id) = 1
- Drain terminali (COMPLETED / CANCELLED / EXPIRED) bounded storicamente · NON bloccano nuovo Drain

Invarianti preservate (PM §4 verbatim):
- Drain consumes Mark = FALSE
- Fragment gain per accepted completion = 1 (fixed · PM B2B2Q05)
- Drain completion at Fragment cap = ACCEPTED WITH OVERFLOW DISCARDED
- Zero dipendenza da `TrustedDrainReceipt` (DEPRECATED_COMPATIBILITY_ONLY)

Identifier bounds (PM §3 verbatim · zero mutation on invalid · no silent truncation):
- event_id ≤ 96 byte UTF-8 → EVENT_ID_INVALID
- source_adventurer_id ≤ 64 byte UTF-8 → SOURCE_INVALID
- target_id ≤ 64 byte UTF-8 → TARGET_INVALID

Cancellation reason codes (PM Message 170 §18 verbatim · 8 canonical · NO extensions).
Completion receipt (PM Message 170 §25): 15-field EMBEDDED in processed event receipt.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainDoc,
    DrainStatus,
    MarkDoc,
)
from app.stats.runtime.transitions.models import (
    DRAIN_CANCEL_REASONS,
    DrainCommand,
    DrainCompletionReceipt,
    ReasonCode,
    TransitionResult,
    TransitionResultCode,
    validate_identifier_bounds,
)


# ═══════════════════════ Constants (PM Message 170 verbatim) ═══════════════════════
FRAGMENT_CAP: int = 5
FRAGMENT_GAIN_PER_DRAIN: int = 1  # PM B2B2Q05 verbatim (fixed=1)
DRAIN_EXECUTION_ID_PREFIX: str = "drn-"


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _is_mark_active(m: MarkDoc, now: datetime) -> bool:
    exp = _parse_iso(m.expires_at)
    if exp is None:
        return False
    return exp > now


def _find_mark(cs: AdventurerClassState, target_id: str, now: datetime) -> Optional[MarkDoc]:
    """Find own active Mark for (source=cs.adventurer_id, target=target_id)."""
    for m in cs.active_marks:
        if m.target_id == target_id and _is_mark_active(m, now):
            return m
    return None


def _find_active_drain_for_pair(
    cs: AdventurerClassState, target_id: str
) -> Optional[DrainDoc]:
    """Find any Drain with runtime_status=IN_PROGRESS for (source, target).

    Only IN_PROGRESS blocks new starts (§18 verbatim: terminal drains are bounded
    historical, do NOT block new valid drain on new application).
    """
    for d in cs.active_drain_executions:
        if (
            d.target_id == target_id
            and d.source_adventurer_id == cs.adventurer_id
            and d.runtime_status is DrainStatus.IN_PROGRESS
        ):
            return d
    return None


def _find_active_drain_for_application(
    cs: AdventurerClassState, mark_id: str, application_id: str
) -> Optional[DrainDoc]:
    """Find any Drain with runtime_status=IN_PROGRESS for (mark_id, application_id)."""
    for d in cs.active_drain_executions:
        if (
            d.mark_id == mark_id
            and d.required_mark_application_id == application_id
            and d.runtime_status is DrainStatus.IN_PROGRESS
        ):
            return d
    return None


def _find_drain_by_id(cs: AdventurerClassState, drain_execution_id: str) -> Optional[DrainDoc]:
    for d in cs.active_drain_executions:
        if d.drain_execution_id == drain_execution_id:
            return d
    return None


def _replace_drain(
    drains: Tuple[DrainDoc, ...], drain_execution_id: str, updated: DrainDoc
) -> Tuple[DrainDoc, ...]:
    return tuple(updated if d.drain_execution_id == drain_execution_id else d for d in drains)


def _reject(
    command: DrainCommand,
    code: TransitionResultCode,
    reason_code: Optional[str] = None,
    state_version_before: Optional[int] = None,
) -> TransitionResult:
    """Build a rejection TransitionResult (zero mutation guarantee for caller)."""
    return TransitionResult(
        code=code,
        event_id=command.event_id,
        event_type=command.command_type,
        expedition_id=command.expedition_id,
        source_adventurer_id=command.source_adventurer_id,
        reason_code=reason_code,
        state_version_before=state_version_before,
    )


# ═══════════════════════ START_DRAIN ═══════════════════════
def start_drain(
    cs: AdventurerClassState,
    *,
    command: DrainCommand,
    now: datetime,
    expedition_terminal: bool = False,
    phase_ended: bool = False,
    receipt_ordinary_available: bool = True,
) -> Tuple[AdventurerClassState, TransitionResult]:
    """START_DRAIN transition (NOT_STARTED → STARTED).

    PM Message 170 §13 verbatim (8-step atomic sequence): identifier validation ·
    expedition/phase precondition · Mark presence + ownership + application binding ·
    hard-locks max=1 per pair AND max=1 per Mark application · receipt capacity ·
    server-authoritative UUIDv4 · DrainDoc append · state_version increment (dispatcher).

    Args:
        cs: current AdventurerClassState (single writer expected)
        command: DrainCommand (command_type=START_DRAIN)
        now: authoritative server clock
        expedition_terminal: True if expedition runtime_status ∈ {COMPLETED, CANCELLED, EXPIRED}
        phase_ended: True if phase_ended in trusted_context
        receipt_ordinary_available: False if ordinary cap 504 exhausted

    Returns:
        (new_cs, TransitionResult). On rejection: new_cs == cs (zero mutation).
    """
    # Identifier bounds enforcement (§3 verbatim · zero mutation on invalid).
    bounds_reject = validate_identifier_bounds(
        command.event_id, command.source_adventurer_id, command.target_id
    )
    if bounds_reject is not None:
        return cs, _reject(command, bounds_reject, reason_code="IDENTIFIER_BOUNDS")

    # Expedition/phase precondition
    if expedition_terminal:
        return cs, _reject(
            command,
            TransitionResultCode.EXPEDITION_TERMINAL_REJECTED,
            reason_code=ReasonCode.EXPEDITION_TERMINAL.value,
        )
    if phase_ended:
        return cs, _reject(
            command,
            TransitionResultCode.PHASE_INACTIVE,
            reason_code=ReasonCode.PHASE_ENDED.value,
        )

    # Ownership: source_adventurer_id must equal caller's class state adventurer_id
    if command.source_adventurer_id != cs.adventurer_id:
        return cs, _reject(
            command,
            TransitionResultCode.OWNERSHIP_INVALID,
            reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
        )

    # Mark presence + not expired (own active Mark)
    mark = _find_mark(cs, command.target_id, now)
    if mark is None:
        # Distinguish MARK_NOT_FOUND vs MARK_EXPIRED
        for m in cs.active_marks:
            if m.target_id == command.target_id:
                # Present but expired
                return cs, _reject(
                    command,
                    TransitionResultCode.MARK_EXPIRED,
                    reason_code=ReasonCode.MARK_EXPIRED.value,
                )
        return cs, _reject(
            command, TransitionResultCode.MARK_NOT_FOUND, reason_code="MARK_NOT_FOUND"
        )

    # Mark ownership check (defensive — should always match since we scanned cs.active_marks)
    if mark.source_adventurer_id != cs.adventurer_id:
        return cs, _reject(
            command,
            TransitionResultCode.OWNERSHIP_INVALID,
            reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
        )

    # Mark ID + application ID binding (strict invariance PM B2B2Q03)
    if command.mark_id and command.mark_id != mark.mark_id:
        return cs, _reject(
            command,
            TransitionResultCode.MARK_APPLICATION_CHANGED,
            reason_code=ReasonCode.MARK_APPLICATION_CHANGED.value,
        )
    if command.application_id and command.application_id != mark.application_id:
        return cs, _reject(
            command,
            TransitionResultCode.MARK_APPLICATION_CHANGED,
            reason_code=ReasonCode.MARK_APPLICATION_CHANGED.value,
        )

    # Hard-lock 1: max=1 active Drain per (source, target)
    if _find_active_drain_for_pair(cs, command.target_id) is not None:
        return cs, _reject(
            command,
            TransitionResultCode.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR,
            reason_code="DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR",
        )

    # Hard-lock 2: max=1 active Drain per Mark application
    if _find_active_drain_for_application(cs, mark.mark_id, mark.application_id) is not None:
        return cs, _reject(
            command,
            TransitionResultCode.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR,
            reason_code="DRAIN_ALREADY_IN_PROGRESS_FOR_APPLICATION",
        )

    # Receipt capacity (ordinary slot required for START_DRAIN)
    if not receipt_ordinary_available:
        return cs, _reject(
            command,
            TransitionResultCode.RECEIPT_CAP_REACHED,
            reason_code="RECEIPT_CAP_REACHED",
        )

    # Server-authoritative UUIDv4 (PM B2B2Q01 verbatim: full UUIDv4, NOT truncated)
    drain_execution_id = f"{DRAIN_EXECUTION_ID_PREFIX}{uuid.uuid4()}"

    new_drain = DrainDoc(
        drain_execution_id=drain_execution_id,
        source_adventurer_id=cs.adventurer_id,
        target_id=command.target_id,
        mark_id=mark.mark_id,
        required_mark_application_id=mark.application_id,
        started_at=_iso(now),
        completed_at=None,
        cancelled_at=None,
        cancellation_reason=None,
        runtime_status=DrainStatus.IN_PROGRESS,
        resolution_version=1,
        drain_version=1,
        reward_resolved=False,
    )
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=cs.active_drain_executions + (new_drain,),
        fragment_count=cs.fragment_count,
        resource_segment_id=cs.resource_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.DRAIN_STARTED,
        event_id=command.event_id,
        event_type=command.command_type,
        expedition_id=command.expedition_id,
        source_adventurer_id=command.source_adventurer_id,
        mark_id=mark.mark_id,
        mark_application_id=mark.application_id,
        reason_code=drain_execution_id,  # exposed as reason_code for dispatcher pickup
    )


# ═══════════════════════ COMPLETE_DRAIN ═══════════════════════
def complete_drain(
    cs: AdventurerClassState,
    *,
    command: DrainCommand,
    now: datetime,
    expedition_terminal: bool = False,
    phase_ended: bool = False,
    receipt_ordinary_available: bool = True,
) -> Tuple[AdventurerClassState, TransitionResult, Optional[DrainCompletionReceipt]]:
    """COMPLETE_DRAIN transition (STARTED → COMPLETED) with atomic Fragment gain.

    PM Message 170 §15-§16 verbatim: 15 mandatory revalidations · single CAS batch ·
    completion payload EMBEDDED in the single ORDINARY receipt (§25) · Fragment gain
    fixed=1 (B2B2Q05) · overflow at cap = COMPLETED+discarded (B2B2Q06) · resource
    segment opening on 0→positive.

    Returns:
        (new_cs, TransitionResult, DrainCompletionReceipt or None on rejection).
    """
    # ── Identifier bounds (§3 verbatim) ──
    bounds_reject = validate_identifier_bounds(
        command.event_id, command.source_adventurer_id, command.target_id
    )
    if bounds_reject is not None:
        return cs, _reject(command, bounds_reject, reason_code="IDENTIFIER_BOUNDS"), None

    # ── 15 mandatory revalidations (PM B2B2Q04 verbatim) ──
    # (11) expedition not terminal
    if expedition_terminal:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.EXPEDITION_TERMINAL_REJECTED,
                reason_code=ReasonCode.EXPEDITION_TERMINAL.value,
            ),
            None,
        )
    # (10) phase active
    if phase_ended:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.PHASE_INACTIVE,
                reason_code=ReasonCode.PHASE_ENDED.value,
            ),
            None,
        )
    # (1) source ownership
    if command.source_adventurer_id != cs.adventurer_id:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.OWNERSHIP_INVALID,
                reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
            ),
            None,
        )
    # (8-10) Drain lookup by drain_execution_id + status checks
    drain = _find_drain_by_id(cs, command.drain_execution_id)
    if drain is None:
        return (
            cs,
            _reject(command, TransitionResultCode.DRAIN_NOT_STARTED, reason_code="DRAIN_NOT_FOUND"),
            None,
        )
    if drain.runtime_status is DrainStatus.RESOLVED:
        return (
            cs,
            _reject(
                command, TransitionResultCode.DRAIN_ALREADY_COMPLETED, reason_code="ALREADY_COMPLETED"
            ),
            None,
        )
    if drain.runtime_status is DrainStatus.CANCELLED:
        return (
            cs,
            _reject(
                command, TransitionResultCode.DRAIN_ALREADY_CANCELLED, reason_code="ALREADY_CANCELLED"
            ),
            None,
        )
    if drain.runtime_status is not DrainStatus.IN_PROGRESS:
        return (
            cs,
            _reject(command, TransitionResultCode.DRAIN_NOT_STARTED, reason_code="STATE_INVALID"),
            None,
        )
    # (2) target match
    if drain.target_id != command.target_id:
        return (
            cs,
            _reject(command, TransitionResultCode.TARGET_INVALID, reason_code="TARGET_MISMATCH"),
            None,
        )
    # (3-4) mark_id + application_id match DrainDoc
    if command.mark_id and command.mark_id != drain.mark_id:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.MARK_APPLICATION_CHANGED,
                reason_code=ReasonCode.MARK_APPLICATION_CHANGED.value,
            ),
            None,
        )
    if command.application_id and command.application_id != drain.required_mark_application_id:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.MARK_APPLICATION_CHANGED,
                reason_code=ReasonCode.MARK_APPLICATION_CHANGED.value,
            ),
            None,
        )
    # (5-7) Mark active + not expired + ownership
    mark = _find_mark(cs, drain.target_id, now)
    if mark is None:
        # Present but expired vs entirely missing
        for m in cs.active_marks:
            if m.target_id == drain.target_id:
                return (
                    cs,
                    _reject(
                        command,
                        TransitionResultCode.MARK_EXPIRED,
                        reason_code=ReasonCode.MARK_EXPIRED.value,
                    ),
                    None,
                )
        return (
            cs,
            _reject(command, TransitionResultCode.MARK_NOT_FOUND, reason_code="MARK_NOT_FOUND"),
            None,
        )
    if mark.source_adventurer_id != cs.adventurer_id:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.OWNERSHIP_INVALID,
                reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
            ),
            None,
        )
    # (4bis) Mark application not changed since START_DRAIN
    if mark.application_id != drain.required_mark_application_id:
        return (
            cs,
            _reject(
                command,
                TransitionResultCode.MARK_APPLICATION_CHANGED,
                reason_code=ReasonCode.MARK_APPLICATION_CHANGED.value,
            ),
            None,
        )
    # (12-15) lease / fencing / state_version / receipt_capacity — enforced by dispatcher/store
    if not receipt_ordinary_available:
        return (
            cs,
            _reject(command, TransitionResultCode.RECEIPT_CAP_REACHED, reason_code="RECEIPT_CAP_REACHED"),
            None,
        )

    # ── Atomic completion-to-Fragment batch (§26 verbatim) ──
    # Fragment gain fixed=1 (B2B2Q05). Cap=5 (B2B2Q06). Overflow → discarded.
    fragment_gain_requested = FRAGMENT_GAIN_PER_DRAIN
    if cs.fragment_count >= FRAGMENT_CAP:
        fragment_gain_applied = 0
        fragment_overflow_discarded = 1
        new_fragment_count = cs.fragment_count
        new_segment_id = cs.resource_segment_id
    else:
        fragment_gain_applied = 1
        fragment_overflow_discarded = 0
        new_fragment_count = cs.fragment_count + 1
        # Segment opening on 0 → positive
        if cs.fragment_count == 0 and cs.resource_segment_id is None:
            new_segment_id = f"sg-{uuid.uuid4().hex[:16]}"
        else:
            new_segment_id = cs.resource_segment_id

    resolved_drain = DrainDoc(
        drain_execution_id=drain.drain_execution_id,
        source_adventurer_id=drain.source_adventurer_id,
        target_id=drain.target_id,
        mark_id=drain.mark_id,
        required_mark_application_id=drain.required_mark_application_id,
        started_at=drain.started_at,
        completed_at=_iso(now),
        cancelled_at=None,
        cancellation_reason=None,
        runtime_status=DrainStatus.RESOLVED,
        resolution_version=drain.resolution_version + 1,
        drain_version=drain.drain_version + 1,
        reward_resolved=True,
    )
    new_drains = _replace_drain(cs.active_drain_executions, drain.drain_execution_id, resolved_drain)
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=new_drains,
        fragment_count=new_fragment_count,
        resource_segment_id=new_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )

    # 15-field completion receipt (EMBEDDED payload · §25 verbatim)
    completion_receipt = DrainCompletionReceipt(
        drain_execution_id=drain.drain_execution_id,
        completion_event_id=command.event_id,
        source_adventurer_id=cs.adventurer_id,
        target_id=drain.target_id,
        mark_id=drain.mark_id,
        application_id=drain.required_mark_application_id,
        result_code=TransitionResultCode.DRAIN_COMPLETED.value,
        mark_valid_at_completion=True,
        fragment_gain_requested=fragment_gain_requested,
        fragment_gain_applied=fragment_gain_applied,
        fragment_overflow_discarded=fragment_overflow_discarded,
        resource_segment_id=new_segment_id,
        assigned_event_sequence=0,  # populated by dispatcher post CAS
        state_version_after=0,  # populated by dispatcher post CAS
        processed_at=_iso(now),
    )

    return new_cs, TransitionResult(
        code=TransitionResultCode.DRAIN_COMPLETED,
        event_id=command.event_id,
        event_type=command.command_type,
        expedition_id=command.expedition_id,
        source_adventurer_id=command.source_adventurer_id,
        mark_id=drain.mark_id,
        mark_application_id=drain.required_mark_application_id,
        resource_segment_id=new_segment_id,
        fragment_count_after=new_fragment_count,
        overflow_discarded=fragment_overflow_discarded,
        reason_code=drain.drain_execution_id,
    ), completion_receipt


# ═══════════════════════ CANCEL_DRAIN ═══════════════════════
def cancel_drain(
    cs: AdventurerClassState,
    *,
    command: DrainCommand,
    now: datetime,
) -> Tuple[AdventurerClassState, TransitionResult]:
    """CANCEL_DRAIN transition (STARTED → CANCELLED).

    PM Message 170 §17 verbatim: 4 triggers (EXPLICIT · PHASE_END · EXPEDITION_TERMINAL ·
    lazy Mark-expiration cascade) → 8 canonical reason codes (§18 · NO extensions).

    Idempotency: cancel su Drain già cancelled → DRAIN_ALREADY_CANCELLED (no mutation).
                 cancel su Drain già completed → DRAIN_ALREADY_COMPLETED (no mutation).
    """
    # Identifier bounds
    bounds_reject = validate_identifier_bounds(
        command.event_id, command.source_adventurer_id, command.target_id or "cancel-cascade"
    )
    if bounds_reject is TransitionResultCode.EVENT_ID_INVALID or bounds_reject is TransitionResultCode.SOURCE_INVALID:
        return cs, _reject(command, bounds_reject, reason_code="IDENTIFIER_BOUNDS")
    # target_id may be empty for lifecycle cancel; only enforce if provided
    if command.target_id and bounds_reject is TransitionResultCode.TARGET_INVALID:
        return cs, _reject(command, bounds_reject, reason_code="IDENTIFIER_BOUNDS")

    # Cancellation reason must be one of 8 canonical (§18 verbatim)
    if command.cancellation_reason not in DRAIN_CANCEL_REASONS:
        return cs, _reject(
            command,
            TransitionResultCode.SOURCE_INVALID,
            reason_code="UNKNOWN_CANCELLATION_REASON",
        )

    # Ownership (skip for lifecycle EXPEDITION_TERMINAL / PHASE_ENDED which target all drains)
    if command.cancellation_reason not in ("PHASE_ENDED", "EXPEDITION_TERMINAL"):
        if command.source_adventurer_id != cs.adventurer_id:
            return cs, _reject(
                command,
                TransitionResultCode.OWNERSHIP_INVALID,
                reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
            )

    drain = _find_drain_by_id(cs, command.drain_execution_id)
    if drain is None:
        return cs, _reject(
            command, TransitionResultCode.DRAIN_NOT_STARTED, reason_code="DRAIN_NOT_FOUND"
        )
    if drain.runtime_status is DrainStatus.CANCELLED:
        return cs, _reject(
            command, TransitionResultCode.DRAIN_ALREADY_CANCELLED, reason_code="ALREADY_CANCELLED"
        )
    if drain.runtime_status is DrainStatus.RESOLVED:
        return cs, _reject(
            command, TransitionResultCode.DRAIN_ALREADY_COMPLETED, reason_code="ALREADY_COMPLETED"
        )
    if drain.runtime_status is not DrainStatus.IN_PROGRESS:
        return cs, _reject(
            command, TransitionResultCode.DRAIN_NOT_STARTED, reason_code="STATE_INVALID"
        )

    cancelled_drain = DrainDoc(
        drain_execution_id=drain.drain_execution_id,
        source_adventurer_id=drain.source_adventurer_id,
        target_id=drain.target_id,
        mark_id=drain.mark_id,
        required_mark_application_id=drain.required_mark_application_id,
        started_at=drain.started_at,
        completed_at=None,
        cancelled_at=_iso(now),
        cancellation_reason=command.cancellation_reason,
        runtime_status=DrainStatus.CANCELLED,
        resolution_version=drain.resolution_version + 1,
        drain_version=drain.drain_version + 1,
        reward_resolved=False,
    )
    new_drains = _replace_drain(cs.active_drain_executions, drain.drain_execution_id, cancelled_drain)
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=new_drains,
        fragment_count=cs.fragment_count,
        resource_segment_id=cs.resource_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.DRAIN_CANCELLED,
        event_id=command.event_id,
        event_type=command.command_type,
        expedition_id=command.expedition_id,
        source_adventurer_id=command.source_adventurer_id,
        mark_id=drain.mark_id,
        mark_application_id=drain.required_mark_application_id,
        reason_code=command.cancellation_reason,
    )


__all__ = [
    "FRAGMENT_CAP",
    "FRAGMENT_GAIN_PER_DRAIN",
    "DRAIN_EXECUTION_ID_PREFIX",
    "start_drain",
    "complete_drain",
    "cancel_drain",
]
