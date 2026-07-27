"""RT2-B-2B-1 · ClassTransitionDispatcher (lease+CAS event batch orchestrator).

Orchestrazione del ciclo (PM Message 151 §8 verbatim):
  1. acquire short request-scoped lease
  2. obtain and validate fencing token
  3. read expected state_version
  4. validate complete event
  5. apply state changes atomically
  6. increment state_version exactly once
  7. persist event receipt
  8. release lease or allow short expiry

Regole:
- CAS **INSIDE** lease = MANDATORY
- CAS-only mutation senza lease = FORBIDDEN (→ `CAS_WITHOUT_VALID_LEASE`)
- Retry max 3 · ogni retry rilegge stato + rivalida lease/fencing/receipt
- No background renewer

Boundary (PM §11):
- Composizione atomica event batch
- Iniezione state store (nessuna istanziazione diretta)
- Iniezione trusted context (identità + phase + policy config)
- NO conoscenza HTTP/frontend/env vars
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from app.stats.runtime.state_store.interface import ExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    EventReceipt,
    ExpeditionRuntimeState,
    RuntimeStatus,
)
from app.stats.runtime.state_store.results import CasResult, CasResultCode
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    ReceiptCategory,
    TransitionResult,
    TransitionResultCode,
    categorize_event,
)
from app.stats.runtime.transitions.phase import (
    build_phase_id,
    is_transition_allowed_in_phase,
)
from app.stats.runtime.transitions.state_machine import (
    apply_mark,
    close_resource_segment,
    gain_fragment,
    lazy_expire_marks,
    refresh_mark,
    reset_fragments,
    spend_fragment,
    would_receipt_be_accepted,
)
from app.stats.runtime.transitions.drain import (
    DRAIN_EVENT_TYPES,
    DRAIN_FOLD_COMMIT_CODES,
    DRAIN_SUCCESS_CODES,
    LIFECYCLE_CANCELLED_IDS_BOUND,
    cancel_drain,
    cancel_started_drains_for_lifecycle,
    complete_drain,
    find_drain_by_start_event,
    start_drain,
)

# PM Message 151 §8: retry max 3.
RETRY_MAX: int = 3


@dataclass(frozen=True)
class DispatchOutcome:
    """Outcome del dispatch di un event class-state.

    Contiene sia il TransitionResult (audit-only) sia info di orchestrazione
    (lease acquisition, retry count).
    """

    result: TransitionResult
    lease_acquired: bool = False
    lease_id: Optional[str] = None
    fencing_token: Optional[int] = None
    retry_attempts: int = 0
    total_duration_ms: float = 0.0


class ClassTransitionDispatcher:
    """Dispatcher server-authoritative per class-state events.

    Costruito dal wiring layer con state store iniettato. Non conosce Mongo
    direttamente.
    """

    def __init__(
        self,
        store: ExpeditionRuntimeStateStore,
        *,
        worker_id: str = "e1-dispatcher",
        lease_ttl_seconds: int = 5,
        now_fn: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._store = store
        self._worker_id = worker_id
        self._lease_ttl = lease_ttl_seconds
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def _now(self) -> datetime:
        return self._now_fn()

    async def dispatch(
        self,
        event: ClassStateEvent,
        *,
        trusted_context: Dict[str, Any],
    ) -> DispatchOutcome:
        """Dispatcha un event class-state seguendo il ciclo 8-step del PM §8.

        Args:
            event: ClassStateEvent (client fields + server derived assignment)
            trusted_context: dict con `test_user_id`, `phase_id`, `db_allowlisted`,
                `feature_enabled`, `expected_state_version_override` (opzionale)

        Returns:
            DispatchOutcome with TransitionResult (never raises).
        """
        t0 = time.monotonic()

        # Feature/test-user/db gates (composite quadruple gate)
        if not trusted_context.get("feature_enabled", False):
            return _skip_outcome(event, TransitionResultCode.FEATURE_DISABLED, t0)
        if not trusted_context.get("test_user_verified", False):
            return _skip_outcome(event, TransitionResultCode.TEST_USER_BOUNDARY_VIOLATION, t0)
        if not trusted_context.get("db_allowlisted", False):
            return _skip_outcome(event, TransitionResultCode.DB_NOT_ALLOWLISTED, t0)

        # Lease acquire (short request-scoped)
        lease_res = await self._store.reserve_writer(
            expedition_id=event.expedition_id,
            writer_worker_id=self._worker_id,
            lease_ttl_seconds=self._lease_ttl,
        )
        if lease_res.code is not CasResultCode.SUCCESS:
            # Mappa lease failure → transition result code
            code_map = {
                CasResultCode.NOT_FOUND: TransitionResultCode.NOT_FOUND,
                CasResultCode.STATE_VERSION_CONFLICT: TransitionResultCode.STATE_VERSION_CONFLICT,
                CasResultCode.OWNERSHIP_INVALID: TransitionResultCode.OWNERSHIP_INVALID,
            }
            # RT2-B-2B-2-1 · B2B2Q09: canonical code per Drain events —
            # qualunque lease failure (tranne NOT_FOUND) → LEASE_ACQUISITION_FAILED.
            if event.event_type in DRAIN_EVENT_TYPES:
                _lease_code = (
                    TransitionResultCode.NOT_FOUND
                    if lease_res.code is CasResultCode.NOT_FOUND
                    else TransitionResultCode.LEASE_ACQUISITION_FAILED
                )
            else:
                _lease_code = code_map.get(
                    lease_res.code, TransitionResultCode.CAS_WITHOUT_VALID_LEASE,
                )
            return DispatchOutcome(
                result=TransitionResult(
                    code=_lease_code,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    expedition_id=event.expedition_id,
                    source_adventurer_id=event.source_adventurer_id,
                    reason_code=lease_res.reason or "LEASE_NOT_ACQUIRED",
                    duration_ms=(time.monotonic() - t0) * 1000.0,
                ),
                lease_acquired=False,
                total_duration_ms=(time.monotonic() - t0) * 1000.0,
            )

        lease_id = lease_res.lease_id or ""
        fencing = lease_res.fencing_token or 0

        try:
            # Retry loop (max 3, PM §8)
            attempt = 0
            last_res: Optional[TransitionResult] = None
            while attempt < RETRY_MAX:
                attempt += 1
                read = await self._store.get_state(event.expedition_id)
                if read.code is not CasResultCode.SUCCESS or read.state is None:
                    last_res = TransitionResult(
                        code=TransitionResultCode.NOT_FOUND,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        retry_attempts=attempt,
                    )
                    break

                state: ExpeditionRuntimeState = read.state

                # PRE-CHECK dedup: se event_id+payload_hash già presente → DEDUPLICATED_NO_OP.
                # Questo previene di eseguire state-machine (che rigetterebbe con altro codice)
                # su replay legittimi. Delegato dal store via apply_event_once, ma serve check
                # esplicito perché il pure state-machine potrebbe rigettare per invarianti
                # (es. MARK_ALREADY_ACTIVE_FOR_PAIR) prima di raggiungere il CAS.
                dedup_hit = None
                for r in state.processed_event_keys:
                    if r.event_id == event.event_id:
                        dedup_hit = r
                        break
                if dedup_hit is not None:
                    if dedup_hit.payload_hash == event.payload_hash:
                        # RT2-B-2B-2-1 · B2B2Q01: replay dello stesso START
                        # accettato → ritorna il prior drain_execution_id
                        # (nessun nuovo Drain · nessuna mutation).
                        prior_drain_id = None
                        if event.event_type in DRAIN_EVENT_TYPES:
                            cs_dedup = state.class_state_for(event.source_adventurer_id)
                            if cs_dedup is not None:
                                if event.event_type == ClassEventType.START_DRAIN.value:
                                    prior = find_drain_by_start_event(cs_dedup, event.event_id)
                                    if prior is not None:
                                        prior_drain_id = prior.drain_execution_id
                                else:
                                    prior_drain_id = event.drain_execution_id
                        last_res = TransitionResult(
                            code=TransitionResultCode.DEDUPLICATED_NO_OP,
                            event_id=event.event_id,
                            event_type=event.event_type,
                            expedition_id=event.expedition_id,
                            source_adventurer_id=event.source_adventurer_id,
                            assigned_event_sequence=dedup_hit.assigned_event_sequence,
                            state_version_before=state.state_version,
                            state_version_after=dedup_hit.state_version_after,
                            dedup_reference=str(dedup_hit.assigned_event_sequence),
                            retry_attempts=attempt,
                            drain_execution_id=prior_drain_id,
                        )
                        break
                    else:
                        last_res = TransitionResult(
                            code=TransitionResultCode.EVENT_ID_PAYLOAD_MISMATCH,
                            event_id=event.event_id,
                            event_type=event.event_type,
                            expedition_id=event.expedition_id,
                            source_adventurer_id=event.source_adventurer_id,
                            reason_code="PAYLOAD_HASH_DIFFERS",
                            dedup_reference=str(dedup_hit.assigned_event_sequence),
                            retry_attempts=attempt,
                        )
                        break

                # Phase / terminal boundary
                phase_ended = trusted_context.get("phase_ended", False)
                expedition_terminal = state.runtime_status in (
                    RuntimeStatus.COMPLETED, RuntimeStatus.CANCELLED, RuntimeStatus.EXPIRED,
                )
                allowed, boundary_reason = is_transition_allowed_in_phase(
                    phase_ended=phase_ended,
                    expedition_terminal=expedition_terminal,
                    event_type=event.event_type,
                )
                if not allowed:
                    # RT2-B-2B-2-1 · B2B2Q09: canonical rejection codes per Drain.
                    if event.event_type in DRAIN_EVENT_TYPES:
                        _boundary_code = (
                            TransitionResultCode.EXPEDITION_TERMINAL_REJECTED
                            if expedition_terminal
                            else TransitionResultCode.PHASE_INACTIVE
                        )
                    else:
                        _boundary_code = (
                            TransitionResultCode.EVENT_POST_TERMINAL_REJECTED
                            if expedition_terminal
                            else TransitionResultCode.PHASE_ENDED
                        )
                    last_res = TransitionResult(
                        code=_boundary_code,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        reason_code=boundary_reason,
                        state_version_before=state.state_version,
                        retry_attempts=attempt,
                    )
                    break

                # Receipt cap check (B2BQ14) — pre-commit
                receipt_ok, receipt_code = would_receipt_be_accepted(
                    state.processed_event_keys, event.event_type,
                )
                if not receipt_ok:
                    last_res = TransitionResult(
                        code=receipt_code,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        reason_code="RECEIPT_CAP_REACHED",
                        state_version_before=state.state_version,
                        retry_attempts=attempt,
                    )
                    break

                # Compute new class state + intermediate result
                cs = state.class_state_for(event.source_adventurer_id) or AdventurerClassState(
                    adventurer_id=event.source_adventurer_id,
                )
                new_cs, tr = _apply_event_pure(
                    cs, event, self._now(),
                    next_event_sequence=state.last_event_sequence + 1,
                    state_version_after=state.state_version + 1,
                )

                # Commit decision (RT2-B-2B-2-1):
                # - SUCCESS legacy → commit
                # - Drain success codes (DRAIN_STARTED/COMPLETED/CANCELLED) → commit
                # - Drain fold-cancellation codes (B2B2Q14) → commit SOLO se la
                #   mutation esiste (auto-cancel foldato nella receipt del
                #   triggering event · MAI una seconda receipt)
                _is_drain_event = event.event_type in DRAIN_EVENT_TYPES
                _committable = (
                    tr.code is TransitionResultCode.SUCCESS
                    or (_is_drain_event and tr.code in DRAIN_SUCCESS_CODES)
                    or (
                        _is_drain_event
                        and tr.code in DRAIN_FOLD_COMMIT_CODES
                        and new_cs is not cs
                    )
                )
                if not _committable:
                    last_res = replace(
                        tr,
                        state_version_before=state.state_version,
                        retry_attempts=attempt,
                    )
                    break

                # Build updated adventurer_class_states tuple
                updated_map = []
                found = False
                for aid, existing_cs in state.adventurer_class_states:
                    if aid == event.source_adventurer_id:
                        updated_map.append((aid, new_cs))
                        found = True
                    else:
                        updated_map.append((aid, existing_cs))
                if not found:
                    updated_map.append((event.source_adventurer_id, new_cs))

                mutation = {
                    "adventurer_class_states": tuple(updated_map),
                }

                # CAS write via apply_event_once (dedup guarantee)
                cas = await self._store.apply_event_once(
                    expedition_id=event.expedition_id,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    source_adventurer_id=event.source_adventurer_id,
                    payload_hash=event.payload_hash,
                    expected_state_version=state.state_version,
                    expected_fencing_token=fencing,
                    mutation=mutation,
                )

                if cas.code is CasResultCode.SUCCESS:
                    # Preserva tr.code: SUCCESS legacy · DRAIN_* success ·
                    # fold-cancellation code (committato, B2B2Q14).
                    last_res = replace(
                        tr,
                        assigned_event_sequence=cas.assigned_event_sequence,
                        state_version_before=state.state_version,
                        state_version_after=cas.new_state_version,
                        retry_attempts=attempt,
                    )
                    break
                elif cas.code is CasResultCode.DEDUPLICATED_NO_OP:
                    last_res = TransitionResult(
                        code=TransitionResultCode.DEDUPLICATED_NO_OP,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        assigned_event_sequence=cas.assigned_event_sequence,
                        state_version_before=state.state_version,
                        state_version_after=cas.new_state_version,
                        dedup_reference=cas.prior_result_reference,
                        retry_attempts=attempt,
                    )
                    break
                elif cas.code is CasResultCode.EVENT_ID_PAYLOAD_MISMATCH:
                    last_res = TransitionResult(
                        code=TransitionResultCode.EVENT_ID_PAYLOAD_MISMATCH,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        dedup_reference=cas.prior_result_reference,
                        retry_attempts=attempt,
                    )
                    break
                elif cas.code is CasResultCode.STATE_VERSION_CONFLICT:
                    # Retry con fresh read + rivalidazione
                    last_res = TransitionResult(
                        code=TransitionResultCode.STATE_VERSION_CONFLICT,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        retry_attempts=attempt,
                    )
                    continue
                elif cas.code is CasResultCode.STALE_WRITER_REJECTED:
                    last_res = TransitionResult(
                        code=TransitionResultCode.STALE_WRITER_REJECTED,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        retry_attempts=attempt,
                    )
                    break
                elif cas.code is CasResultCode.CAP_EXCEEDED:
                    last_res = TransitionResult(
                        code=TransitionResultCode.RECEIPT_CAP_REACHED,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        retry_attempts=attempt,
                    )
                    break
                else:
                    last_res = TransitionResult(
                        code=TransitionResultCode.NOT_FOUND,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        expedition_id=event.expedition_id,
                        source_adventurer_id=event.source_adventurer_id,
                        retry_attempts=attempt,
                    )
                    break

            # Retry ceiling exhausted
            if last_res is None or (
                last_res.code is TransitionResultCode.STATE_VERSION_CONFLICT
                and attempt >= RETRY_MAX
            ):
                last_res = TransitionResult(
                    code=(
                        TransitionResultCode.RETRY_LIMIT_REACHED
                        if event.event_type in DRAIN_EVENT_TYPES
                        else TransitionResultCode.RETRY_CEILING_EXCEEDED
                    ),
                    event_id=event.event_id,
                    event_type=event.event_type,
                    expedition_id=event.expedition_id,
                    source_adventurer_id=event.source_adventurer_id,
                    reason_code="STATE_VERSION_CONFLICT_MAX_RETRIES",
                    retry_attempts=attempt,
                )

            total_ms = (time.monotonic() - t0) * 1000.0
            enriched = replace(last_res, duration_ms=total_ms)
            return DispatchOutcome(
                result=enriched,
                lease_acquired=True,
                lease_id=lease_id,
                fencing_token=fencing,
                retry_attempts=enriched.retry_attempts,
                total_duration_ms=total_ms,
            )
        finally:
            # Release lease (never raises)
            try:
                await self._store.release_writer(
                    expedition_id=event.expedition_id,
                    lease_id=lease_id,
                    fencing_token=fencing,
                )
            except Exception:  # noqa: BLE001
                pass


# ═══════════════════════ Pure event application ═══════════════════════
def _apply_event_pure(
    cs: AdventurerClassState,
    event: ClassStateEvent,
    now: datetime,
    *,
    next_event_sequence: int = 0,
    state_version_after: int = 0,
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Applica un evento class-state a un `AdventurerClassState`, pure/deterministic.

    Non tocca lo store. Ritorna (new_cs, intermediate TransitionResult) senza
    campi di orchestrazione (verranno riempiti dal dispatcher).

    `next_event_sequence` / `state_version_after` sono i valori deterministici
    post-commit (garantiti dal CAS filter se il commit riesce) — usati per il
    completion payload EMBEDDED del Drain (B2B2Q07).
    """
    et = event.event_type
    # ── RT2-B-2B-2-1 · Drain lifecycle ──
    if et == ClassEventType.START_DRAIN.value:
        return start_drain(
            cs,
            target_id=event.target_id or "",
            now=now,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et == ClassEventType.COMPLETE_DRAIN.value:
        return complete_drain(
            cs,
            drain_execution_id=event.drain_execution_id,
            now=now,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
            next_event_sequence=next_event_sequence,
            state_version_after=state_version_after,
        )
    if et == ClassEventType.CANCEL_DRAIN.value:
        return cancel_drain(
            cs,
            drain_execution_id=event.drain_execution_id,
            now=now,
            reason_code=event.reason_code,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et == ClassEventType.APPLY_MARK.value:
        return apply_mark(
            cs,
            target_id=event.target_id or "",
            now=now,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et == ClassEventType.REFRESH_MARK.value:
        return refresh_mark(
            cs,
            target_id=event.target_id or "",
            now=now,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et == ClassEventType.LAZY_MARK_EXPIRATION.value:
        new_cs, expired = lazy_expire_marks(cs, now)
        return new_cs, TransitionResult(
            code=TransitionResultCode.SUCCESS,
            event_id=event.event_id,
            event_type=et,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
            active_marks_count_after=len(new_cs.active_marks),
            reason_code=f"EXPIRED_COUNT_{expired}",
        )
    if et == ClassEventType.OPPORTUNISTIC_MARK_CLEANUP.value:
        new_cs, expired = lazy_expire_marks(cs, now)
        return new_cs, TransitionResult(
            code=TransitionResultCode.SUCCESS,
            event_id=event.event_id,
            event_type=et,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
            active_marks_count_after=len(new_cs.active_marks),
            reason_code=f"CLEANED_{expired}",
        )
    if et == ClassEventType.GAIN_FRAGMENT.value:
        return gain_fragment(
            cs,
            trusted_receipt=event.trusted_drain_receipt,
            now=now,
            amount=event.amount if event.amount > 0 else 1,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et == ClassEventType.SPEND_FRAGMENT.value:
        return spend_fragment(
            cs,
            amount=event.amount,
            uses_focus_bonus=(event.reason_code == "USES_FOCUS_BONUS"),
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et == ClassEventType.RESET_FRAGMENTS.value:
        return reset_fragments(
            cs,
            reason=event.reason_code or "EXPLICIT_RESET",
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et in (
        ClassEventType.CLOSE_RESOURCE_SEGMENT.value,
        ClassEventType.AUTO_CLOSE_ON_ZERO.value,
        ClassEventType.AUTO_CLOSE_ON_PHASE_END.value,
        ClassEventType.AUTO_CLOSE_ON_EXPEDITION_TERMINAL.value,
    ):
        return close_resource_segment(
            cs,
            trigger=et,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
    if et in (
        ClassEventType.PHASE_END.value,
        ClassEventType.EXPEDITION_TERMINAL.value,
        ClassEventType.CLEANUP_CRITICAL.value,
    ):
        # Reserved lifecycle: reset fragments + close segment + bulk Drain
        # cancellation (B2B2Q11: ONE reserved lifecycle receipt per l'INTERO
        # atomic batch — MAI una receipt per singolo Drain cancellato).
        new_cs, _ = reset_fragments(
            cs,
            reason=et,
            event_id=event.event_id,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
        )
        _lifecycle_reason_map = {
            ClassEventType.PHASE_END.value: "PHASE_ENDED",
            ClassEventType.EXPEDITION_TERMINAL.value: "EXPEDITION_TERMINAL",
            ClassEventType.CLEANUP_CRITICAL.value: "EXPLICIT_SERVER_CANCEL",
        }
        new_cs, cancelled_ids = cancel_started_drains_for_lifecycle(
            new_cs,
            reason=_lifecycle_reason_map[et],
            now=now,
        )
        return new_cs, TransitionResult(
            code=TransitionResultCode.SUCCESS,
            event_id=event.event_id,
            event_type=et,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
            fragment_count_after=0,
            resource_segment_id=None,
            reason_code=et,
            drains_cancelled_count=len(cancelled_ids),
            cancelled_drain_execution_ids=cancelled_ids[:LIFECYCLE_CANCELLED_IDS_BOUND],
            cancellation_reason=(
                _lifecycle_reason_map[et] if cancelled_ids else None
            ),
        )
    if et == ClassEventType.OPEN_RESOURCE_SEGMENT.value:
        # Standalone open (rare — normally auto-opens on first gain).
        if cs.resource_segment_id is not None:
            return cs, TransitionResult(
                code=TransitionResultCode.DEDUPLICATED_NO_OP,
                event_id=event.event_id,
                event_type=et,
                expedition_id=event.expedition_id,
                source_adventurer_id=event.source_adventurer_id,
                resource_segment_id=cs.resource_segment_id,
            )
        new_seg_id = f"seg-{uuid.uuid4().hex[:16]}"
        new_cs = AdventurerClassState(
            adventurer_id=cs.adventurer_id,
            active_marks=cs.active_marks,
            active_drain_executions=cs.active_drain_executions,
            fragment_count=cs.fragment_count,
            resource_segment_id=new_seg_id,
            focus_bonus_usage=cs.focus_bonus_usage,
            class_state_version=cs.class_state_version + 1,
        )
        return new_cs, TransitionResult(
            code=TransitionResultCode.SUCCESS,
            event_id=event.event_id,
            event_type=et,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
            resource_segment_id=new_seg_id,
        )
    # Unknown event type: no-op reject.
    return cs, TransitionResult(
        code=TransitionResultCode.SOURCE_INVALID,
        event_id=event.event_id,
        event_type=et,
        expedition_id=event.expedition_id,
        source_adventurer_id=event.source_adventurer_id,
        reason_code="UNKNOWN_EVENT_TYPE",
    )


def _skip_outcome(
    event: ClassStateEvent,
    code: TransitionResultCode,
    t0: float,
) -> DispatchOutcome:
    """Costruisce un outcome no-op (feature disabled / test-user / db-not-allowlisted)."""
    duration = (time.monotonic() - t0) * 1000.0
    return DispatchOutcome(
        result=TransitionResult(
            code=code,
            event_id=event.event_id,
            event_type=event.event_type,
            expedition_id=event.expedition_id,
            source_adventurer_id=event.source_adventurer_id,
            duration_ms=duration,
        ),
        lease_acquired=False,
        total_duration_ms=duration,
    )


__all__ = [
    "RETRY_MAX",
    "ClassTransitionDispatcher",
    "DispatchOutcome",
]
