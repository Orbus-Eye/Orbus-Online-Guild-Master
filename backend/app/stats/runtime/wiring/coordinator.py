"""RT2-B-2A · ExpeditionRuntimeCoordinator (request-scoped).

PM verdict B2Q03 verbatim: lease owner = **request-scoped ExpeditionRuntimeCoordinator**.
Gestisce lease solo per create/terminalize/cancel/cleanup. **No background renewer**.
Marchi/Drain/Frammenti → gate successivo (RT2-B-2B).

Regole di lifecycle (B2Q04 + B2Q09):
- CREATE (shell vuoto, no gameplay transition).
- TERMINALIZE con outcome ∈ {COMPLETED, CANCELLED, COMPLETED_WITH_FAILURE}.

Regole di failure isolation (B2Q08 verbatim):
- shadow failure → gameplay preserved · audit warn.
- state creation failure → gameplay preserved · no class-state execution · no reward linked.
- lease/CAS failure → no partial mutation · no automatic fallback.
- terminalization failure → gameplay preserved · state TTL orphan · warning.
- FORBIDDEN: duplicate reward · partial new-runtime reward · silent granting fallback.

Environment allowlist (B2Q10 verbatim):
- Solo `orbus_r16_rt2b_test` OR `orbus_r16_rt2b_it_<unique_run_id>`.
- VIETATI: `orbus_r16` · `orbus_r16_test` · preview · staging · production.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from app.stats.runtime.state_store import (
    CasResultCode,
    ExpeditionRuntimeState,
    ExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import RuntimeStatus
from app.stats.runtime.transitions.dispatcher import (
    ClassTransitionDispatcher,
    DispatchOutcome,
)
from app.stats.runtime.transitions.models import (
    ClassStateEvent,
    TransitionResult,
    TransitionResultCode,
)
from app.stats.runtime.transitions.drain import DRAIN_EVENT_TYPES
from app.stats.runtime import feature_flags as _feature_flags
from app.stats.runtime.wiring.audit import (
    compute_evaluation_hash,
    emit_audit_event,
    utc_now_iso,
)


# ═══════════════════════ Terminal outcomes (B2Q04 verbatim) ═══════════════════════
class TerminalOutcome(str, Enum):
    """Outcomes di terminalization ratificati B2Q04 verbatim."""

    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    COMPLETED_WITH_FAILURE = "COMPLETED_WITH_FAILURE"


# ═══════════════════════ DB allowlist (B2Q10 verbatim) ═══════════════════════
# Consentiti: `orbus_r16_rt2b_test` + `orbus_r16_rt2b_it_<unique_run_id>`.
# VIETATI: `orbus_r16`, `orbus_r16_test`, preview, staging, production.
_ALLOWED_DB_EXACT: frozenset[str] = frozenset({
    "orbus_r16_rt2b_test",
})
_ALLOWED_DB_PATTERN = re.compile(r"^orbus_r16_rt2b_it_[a-zA-Z0-9_]+$")

_FORBIDDEN_DB: frozenset[str] = frozenset({
    "orbus_r16",
    "orbus_r16_test",
})


def _is_db_allowlisted(db_name: str) -> bool:
    """Fail-closed check contro allowlist DB (B2Q10)."""
    if not db_name or db_name in _FORBIDDEN_DB:
        return False
    if db_name in _ALLOWED_DB_EXACT:
        return True
    return bool(_ALLOWED_DB_PATTERN.match(db_name))


# ═══════════════════════ Coordinator ═══════════════════════
class ExpeditionRuntimeCoordinator:
    """Request-scoped coordinator per lifecycle shadow del runtime state.

    Costruito on-demand da `maybe_shadow_dispatch` / `maybe_shadow_terminalize`.
    Non è un singleton: nuova istanza per ogni operazione hook.

    Args:
        store: implementazione `ExpeditionRuntimeStateStore` (application-scoped
            singleton iniettato dal caller). In test può essere fake.
        target_db_name: nome del DB target per l'allowlist enforcement (B2Q10).
            Se non allowlisted → il coordinator no-op silenziosamente.
    """

    def __init__(
        self,
        store: ExpeditionRuntimeStateStore,
        target_db_name: str,
    ) -> None:
        self._store = store
        self._target_db = target_db_name
        self._db_allowlisted = _is_db_allowlisted(target_db_name)

    @property
    def is_target_db_allowlisted(self) -> bool:
        """Espone lo stato dell'allowlist per test/introspection."""
        return self._db_allowlisted

    # ─── shell state creation (B2Q02 + B2Q09 verbatim) ───────────────────
    async def create_shell_state(
        self,
        expedition_id: str,
        test_user_id: str,
        evaluation_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Crea shell state vuoto (nessuna transizione gameplay · B2Q09).

        Args:
            expedition_id: id spedizione owner del state document.
            test_user_id: id dell'utente test-user server-authoritative (audit only).
            evaluation_payload: payload opzionale per computare `evaluation_hash`
                (subset whitelist B2Q05).

        Returns:
            Dict con `result_code`, `state_version`, `fencing_token`, `evaluation_hash`,
            `duration_ms`. Never raises: fallback isolation (B2Q08).
        """
        t0 = time.monotonic()
        result: dict[str, Any] = {
            "expedition_id": expedition_id,
            "test_user_id": test_user_id,
            "result_code": "SHADOW_SKIPPED",
            "state_version": 0,
            "fencing_token": 0,
            "duration_ms": 0.0,
        }

        # B2Q10: allowlist DB fail-closed.
        if not self._db_allowlisted:
            result["result_code"] = "DB_NOT_ALLOWLISTED"
            result["duration_ms"] = (time.monotonic() - t0) * 1000.0
            emit_audit_event("runtime_state_shadow_failure", result)
            return result

        # Compute evaluation_hash (whitelist-only subset).
        eval_hash = ""
        if evaluation_payload:
            try:
                eval_hash = compute_evaluation_hash(evaluation_payload)
            except Exception:  # noqa: BLE001
                eval_hash = ""
        result["evaluation_hash"] = eval_hash

        # Shell state creation (B2Q02 + B2Q09): nessuna class transition.
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=6)  # B0Q07 verdict upstream (6h inactivity)
        shell = ExpeditionRuntimeState(
            expedition_id=expedition_id,
            state_version=1,
            fencing_token=0,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            expires_at=expires.isoformat(),
            runtime_status=RuntimeStatus.ACTIVE,
            adventurer_class_states=(),  # SHELL — B2Q09 no transitions
            processed_event_keys=(),
            last_event_sequence=0,
            owner_worker_or_lease_id=None,
            lease=None,
        )

        try:
            cas = await self._store.create_state(expedition_id, shell)
            result["result_code"] = cas.code.value if hasattr(cas.code, "value") else str(cas.code)
            result["state_version"] = 1
            result["fencing_token"] = 0
            result["duration_ms"] = (time.monotonic() - t0) * 1000.0

            if cas.code == CasResultCode.SUCCESS:
                emit_audit_event("runtime_state_created", result)
            elif cas.code == CasResultCode.ALREADY_EXISTS:
                # Idempotent no-op (B2Q08).
                emit_audit_event("runtime_state_created", {**result, "result_code": "ALREADY_EXISTS_NOOP"})
            else:
                emit_audit_event("runtime_state_shadow_failure", result)
        except Exception as exc:  # noqa: BLE001
            result["result_code"] = "STORE_INFRA_ERROR"
            result["duration_ms"] = (time.monotonic() - t0) * 1000.0
            result["error_class"] = type(exc).__name__
            # Sanitize: emit only whitelist fields
            emit_audit_event(
                "runtime_state_shadow_failure",
                {k: v for k, v in result.items() if k != "error_class"},
            )
        return result

    # ─── terminalization (B2Q04 verbatim) ────────────────────────────────
    async def terminalize(
        self,
        expedition_id: str,
        outcome: TerminalOutcome,
    ) -> dict[str, Any]:
        """Terminalizza lo state document con outcome verbatim B2Q04.

        Never raises. Failure → audit warn + orphan a TTL (B2Q08).
        """
        t0 = time.monotonic()
        result: dict[str, Any] = {
            "expedition_id": expedition_id,
            "outcome": outcome.value,
            "result_code": "SHADOW_SKIPPED",
            "duration_ms": 0.0,
        }

        if not self._db_allowlisted:
            result["result_code"] = "DB_NOT_ALLOWLISTED"
            result["duration_ms"] = (time.monotonic() - t0) * 1000.0
            emit_audit_event("runtime_state_cleanup_deferred", result)
            return result

        try:
            cas = await self._store.expire_state(expedition_id)
            result["result_code"] = cas.code.value if hasattr(cas.code, "value") else str(cas.code)
            result["duration_ms"] = (time.monotonic() - t0) * 1000.0
            if cas.code in (CasResultCode.SUCCESS, CasResultCode.DEDUPLICATED_NO_OP):
                emit_audit_event("runtime_state_terminalized", result)
            elif cas.code == CasResultCode.NOT_FOUND:
                # No state to terminalize → cleanup deferred to TTL sweep.
                emit_audit_event("runtime_state_cleanup_deferred", result)
            else:
                emit_audit_event("runtime_state_shadow_failure", result)
        except Exception as exc:  # noqa: BLE001
            result["result_code"] = "STORE_INFRA_ERROR"
            result["duration_ms"] = (time.monotonic() - t0) * 1000.0
            emit_audit_event("runtime_state_cleanup_deferred", result)
        return result

    # ─── class-state event dispatch (RT2-B-2B-1 · PM §6-§13) ─────────────
    async def dispatch_class_state_event(
        self,
        event: ClassStateEvent,
        trusted_context: dict[str, Any],
    ) -> DispatchOutcome:
        """Dispatch di un class-state event (Mark / Fragment / Segment).

        PM Message 151 verbatim (B2BQ02):
        - Entry point interno backend, non esposto tramite route pubblica
        - server-authoritative, gated PRIMA di qualsiasi DB access
        - flag composite: cdv_transient_state_enabled AND cdv_class_transitions_enabled
          AND user.is_test_user AND environment=localhost isolated AND
          Mongo target allowlisted (`orbus_r16_rt2b_test` o `orbus_r16_rt2b_it_*`)

        Args:
            event: ClassStateEvent (client fields + payload_hash)
            trusted_context: dict con `test_user_id`, `test_user_verified`,
                `feature_enabled`, `phase_id`, `phase_ended`. Il flag
                `db_allowlisted` viene forzato in base allo stato del coordinator.

        Returns:
            DispatchOutcome (never raises; failure isolation preservata).
        """
        t0 = time.monotonic()
        outcome: DispatchOutcome
        try:
            # Enforce composite gate: db allowlist forzato server-side
            ctx = dict(trusted_context)
            ctx["db_allowlisted"] = self._db_allowlisted

            # ── RT2-B-2B-2-1 · B2B2Q13: 6-conditions gate DEDICATO Drain ──
            # transient AND class (già rappresentati da `feature_enabled`)
            # AND cdv_drain_transitions_enabled AND is_test_user AND
            # localhost isolated AND Mongo allowlisted.
            # Kill-switch surgical: Drain OFF ⇒ 0 DB calls · 0 audit events ·
            # 0 mutations (return PRIMA del dispatcher e PRIMA di ogni emit).
            # Mark/Fragment legacy NON sono toccati da questo gate.
            if event.event_type in DRAIN_EVENT_TYPES:
                drain_flag = ctx.get("drain_feature_enabled")
                if drain_flag is None:
                    drain_flag = _feature_flags.is_enabled(
                        "cdv_drain_transitions_enabled"
                    )
                if not drain_flag:
                    return DispatchOutcome(
                        result=TransitionResult(
                            code=TransitionResultCode.FEATURE_DISABLED,
                            event_id=event.event_id,
                            event_type=event.event_type,
                            expedition_id=event.expedition_id,
                            source_adventurer_id=event.source_adventurer_id,
                            duration_ms=(time.monotonic() - t0) * 1000.0,
                        ),
                        lease_acquired=False,
                        total_duration_ms=(time.monotonic() - t0) * 1000.0,
                    )

            dispatcher = ClassTransitionDispatcher(store=self._store)
            outcome = await dispatcher.dispatch(event, trusted_context=ctx)

            # Audit emission — mapping event_type → audit event id
            if event.event_type in DRAIN_EVENT_TYPES:
                audit_id = _drain_event_audit_id(
                    event.event_type, outcome.result.code,
                )
            else:
                audit_id = _class_event_audit_id(event.event_type, outcome.result.code)
            emit_audit_event(
                audit_id,
                {
                    "expedition_id": outcome.result.expedition_id,
                    "source_adventurer_id": outcome.result.source_adventurer_id,
                    "target_id": event.target_id,
                    "event_id": outcome.result.event_id,
                    "event_type": outcome.result.event_type,
                    "event_sequence": outcome.result.assigned_event_sequence,
                    "result_code": outcome.result.code.value,
                    "state_version_before": outcome.result.state_version_before,
                    "state_version_after": outcome.result.state_version_after,
                    "duration_ms": outcome.result.duration_ms,
                    "reason_code": outcome.result.reason_code,
                    "mark_id": outcome.result.mark_id,
                    "mark_application_id": outcome.result.mark_application_id,
                    "resource_segment_id": outcome.result.resource_segment_id,
                    "fragment_count_after": outcome.result.fragment_count_after,
                    "active_marks_count_after": outcome.result.active_marks_count_after,
                    "focus_bonus_used_after": outcome.result.focus_bonus_used_after,
                    "overflow_discarded": outcome.result.overflow_discarded,
                    "retry_attempts": outcome.result.retry_attempts,
                    "dedup_reference": outcome.result.dedup_reference,
                    "drain_execution_id": outcome.result.drain_execution_id,
                    "cancellation_reason": outcome.result.cancellation_reason,
                    "fragment_gain_requested": outcome.result.fragment_gain_requested,
                    "fragment_gain_applied": outcome.result.fragment_gain_applied,
                    "fragment_overflow_discarded": outcome.result.fragment_overflow_discarded,
                    "mark_valid_at_completion": outcome.result.mark_valid_at_completion,
                    "drains_cancelled_count": outcome.result.drains_cancelled_count,
                },
            )
            # Supplementary Drain audit (B2B2Q15 · batch outcome events).
            if (
                event.event_type in DRAIN_EVENT_TYPES
                and outcome.result.code is TransitionResultCode.DRAIN_COMPLETED
            ):
                _batch_payload = {
                    "expedition_id": outcome.result.expedition_id,
                    "source_adventurer_id": outcome.result.source_adventurer_id,
                    "drain_execution_id": outcome.result.drain_execution_id,
                    "event_id": outcome.result.event_id,
                    "result_code": outcome.result.code.value,
                    "fragment_gain_requested": outcome.result.fragment_gain_requested,
                    "fragment_gain_applied": outcome.result.fragment_gain_applied,
                    "fragment_overflow_discarded": outcome.result.fragment_overflow_discarded,
                    "fragment_count_after": outcome.result.fragment_count_after,
                    "state_version_after": outcome.result.state_version_after,
                }
                if outcome.result.fragment_gain_applied > 0:
                    emit_audit_event("cdv_drain_fragment_batch_applied", _batch_payload)
                if outcome.result.fragment_overflow_discarded > 0:
                    emit_audit_event(
                        "cdv_drain_fragment_overflow_discarded", _batch_payload,
                    )
            return outcome
        except Exception as exc:  # noqa: BLE001
            duration = (time.monotonic() - t0) * 1000.0
            fallback = TransitionResult(
                code=TransitionResultCode.NOT_FOUND,
                event_id=event.event_id,
                event_type=event.event_type,
                expedition_id=event.expedition_id,
                source_adventurer_id=event.source_adventurer_id,
                duration_ms=duration,
                reason_code="STORE_INFRA_ERROR",
            )
            emit_audit_event(
                "cdv_state_transition_conflict",
                {
                    "expedition_id": event.expedition_id,
                    "source_adventurer_id": event.source_adventurer_id,
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "result_code": "STORE_INFRA_ERROR",
                    "duration_ms": duration,
                },
            )
            return DispatchOutcome(
                result=fallback,
                lease_acquired=False,
                total_duration_ms=duration,
            )


# ═══════════════════════ Drain audit event id mapping (10 ids · B2B2Q15) ═══════════════════════
# 1 cdv_drain_started · 2 cdv_drain_start_rejected · 3 cdv_drain_completed ·
# 4 cdv_drain_completion_rejected · 5 cdv_drain_cancelled ·
# 6 cdv_drain_cancellation_rejected · 7 cdv_drain_duplicate_completion ·
# 8 cdv_drain_fragment_batch_applied (supplementare · emesso dal coordinator) ·
# 9 cdv_drain_fragment_overflow_discarded (supplementare) ·
# 10 cdv_drain_transition_conflict
_DRAIN_CONFLICT_CODES: frozenset[str] = frozenset({
    "STATE_VERSION_CONFLICT",
    "STALE_WRITER_REJECTED",
    "EVENT_ID_PAYLOAD_MISMATCH",
    "LEASE_ACQUISITION_FAILED",
    "RETRY_LIMIT_REACHED",
    "CAS_WITHOUT_VALID_LEASE",
    "RECEIPT_CAP_REACHED",
    "RESERVED_CAPACITY_EXHAUSTED",
})


def _drain_event_audit_id(event_type: str, result_code) -> str:
    """Mappa (drain event_type, result_code) → audit event id (B2B2Q15)."""
    code = getattr(result_code, "value", str(result_code))
    if code in _DRAIN_CONFLICT_CODES:
        return "cdv_drain_transition_conflict"
    if event_type == "START_DRAIN":
        if code in ("DRAIN_STARTED", "DEDUPLICATED_NO_OP"):
            return "cdv_drain_started"
        return "cdv_drain_start_rejected"
    if event_type == "COMPLETE_DRAIN":
        if code == "DRAIN_COMPLETED":
            return "cdv_drain_completed"
        if code in ("DRAIN_ALREADY_COMPLETED", "DEDUPLICATED_NO_OP"):
            return "cdv_drain_duplicate_completion"
        return "cdv_drain_completion_rejected"
    if event_type == "CANCEL_DRAIN":
        if code in ("DRAIN_CANCELLED", "DEDUPLICATED_NO_OP"):
            return "cdv_drain_cancelled"
        return "cdv_drain_cancellation_rejected"
    return "cdv_drain_transition_conflict"


# ═══════════════════════ Audit event id mapping (11 event ids, PM §13) ═══════════════════════
def _class_event_audit_id(event_type: str, result_code) -> str:
    """Mappa (event_type, result_code) → audit event id (11 canonici + conflict).

    PM Message 151 §13 verbatim.
    """
    code = getattr(result_code, "value", str(result_code))

    # Conflict/rejection audit id
    conflict_codes = {
        "STATE_VERSION_CONFLICT",
        "STALE_WRITER_REJECTED",
        "EVENT_ID_PAYLOAD_MISMATCH",
        "CAS_WITHOUT_VALID_LEASE",
        "RETRY_CEILING_EXCEEDED",
        "RECEIPT_CAP_REACHED",
        "RESERVED_CAPACITY_EXHAUSTED",
        "STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED",
        "EVENT_POST_TERMINAL_REJECTED",
    }
    if code in conflict_codes:
        return "cdv_state_transition_conflict"

    rejected_codes = {
        "MARK_ALREADY_ACTIVE_FOR_PAIR",
        "MARK_CAP_EXCEEDED",
        "MARK_EXPIRED",
        "MARK_NOT_FOUND",
        "FRAGMENT_CAP_REACHED",
        "FRAGMENT_INSUFFICIENT",
        "FRAGMENT_INVALID_AMOUNT",
        "FRAGMENT_GAIN_UNAUTHORIZED",
        "OWNERSHIP_INVALID",
        "TARGET_INVALID",
        "SOURCE_INVALID",
        "SEGMENT_NOT_OPEN",
        "FOCUS_BONUS_CAP_EXCEEDED",
        "PHASE_ENDED",
    }
    if code == "FRAGMENT_OVERFLOW_DISCARDED":
        return "cdv_fragment_overflow_discarded"
    if code in rejected_codes:
        return "cdv_mark_rejected"

    if event_type == "APPLY_MARK":
        return "cdv_mark_applied"
    if event_type == "REFRESH_MARK":
        return "cdv_mark_refreshed"
    if event_type in ("LAZY_MARK_EXPIRATION", "OPPORTUNISTIC_MARK_CLEANUP"):
        return "cdv_mark_expired"
    if event_type == "GAIN_FRAGMENT":
        return "cdv_fragment_gained"
    if event_type == "SPEND_FRAGMENT":
        return "cdv_fragment_spent"
    if event_type == "RESET_FRAGMENTS":
        return "cdv_fragment_reset"
    if event_type == "DISCARD_FRAGMENT_OVERFLOW":
        return "cdv_fragment_overflow_discarded"
    if event_type in ("OPEN_RESOURCE_SEGMENT",):
        return "cdv_resource_segment_opened"
    if event_type in (
        "CLOSE_RESOURCE_SEGMENT",
        "AUTO_CLOSE_ON_ZERO",
        "AUTO_CLOSE_ON_PHASE_END",
        "AUTO_CLOSE_ON_EXPEDITION_TERMINAL",
    ):
        return "cdv_resource_segment_closed"
    # ═══ RT2-B-2B-2-1 Drain audit mapping (PM Message 170 §38 · 10 event ids) ═══
    # Drain-specific rejection codes → cdv_drain_*_rejected
    drain_start_reject = {
        "DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR",
        "MARK_APPLICATION_CHANGED",
        "EXPEDITION_TERMINAL_REJECTED",
        "PHASE_INACTIVE",
        "EVENT_ID_INVALID",
    }
    drain_state_reject = {
        "DRAIN_NOT_STARTED",
        "DRAIN_ALREADY_COMPLETED",
        "DRAIN_ALREADY_CANCELLED",
    }
    if event_type == "START_DRAIN":
        if code == "DRAIN_STARTED":
            return "cdv_drain_started"
        if code in drain_start_reject or code in drain_state_reject:
            return "cdv_drain_start_rejected"
        return "cdv_drain_start_rejected"
    if event_type == "COMPLETE_DRAIN":
        if code == "DRAIN_COMPLETED":
            return "cdv_drain_completed"
        if code == "DRAIN_ALREADY_COMPLETED":
            return "cdv_drain_duplicate_completion"
        return "cdv_drain_completion_rejected"
    if event_type == "CANCEL_DRAIN":
        if code == "DRAIN_CANCELLED":
            return "cdv_drain_cancelled"
        return "cdv_drain_cancellation_rejected"
    return "cdv_state_transition_conflict"


__all__ = [
    "ExpeditionRuntimeCoordinator",
    "TerminalOutcome",
    "utc_now_iso",
]
