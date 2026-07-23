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


__all__ = [
    "ExpeditionRuntimeCoordinator",
    "TerminalOutcome",
    "utc_now_iso",
]
