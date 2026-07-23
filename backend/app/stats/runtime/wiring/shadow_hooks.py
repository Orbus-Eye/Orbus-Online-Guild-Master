"""RT2-B-2A · Shadow hooks (public API per expedition service integration).

Due funzioni non-blocking chiamate dal service Expedition:
- `maybe_shadow_dispatch(db, current_user, guild, expedition_doc)`: post-validation
  hook (T1). Verifica doppio guardrail (FF + is_test_user), poi delega al
  `ExpeditionRuntimeCoordinator` per creare shell state.
- `maybe_shadow_terminalize(db, expedition_doc, success)`: post-completion hook (T2).
  Determina outcome (COMPLETED / COMPLETED_WITH_FAILURE) e delega al coordinator.

Regole invarianti (B2Q06 + B2Q07 verbatim):
- Feature flag `cdv_transient_state_enabled` server-side, evaluated once at
  lifecycle entry (frozen per operation).
- Test-user eligibility = `users.is_test_user` server-authoritative.
- Fail-closed: missing user OR missing field OR `!= true` → **NO-OP puro**.
- Never raises: caller path critico non è mai bloccato (B2Q08).
- Never mutates response contract: nessun campo aggiunto a expedition_doc / user_doc.

Public API scope:
- Nessun endpoint pubblico creato.
- Nessun campo di risposta aggiunto.
- Solo audit log server-side (B2Q05).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from app.stats.runtime import feature_flags
from app.stats.runtime.wiring.audit import emit_audit_event

logger = logging.getLogger("orbus.rt2_b_2a.wiring.shadow_hooks")


# Env variable per identificare il DB target isolato del wiring shadow.
# Default: `orbus_r16_rt2b_test` (allowlist B2Q10).
_WIRING_TARGET_DB_ENV: str = "ORBUS_RT2B_WIRING_TARGET_DB"
_WIRING_TARGET_DB_DEFAULT: str = "orbus_r16_rt2b_test"


def _get_wiring_target_db() -> str:
    """Ritorna il nome del DB target isolato per il shadow wiring."""
    return (os.environ.get(_WIRING_TARGET_DB_ENV) or _WIRING_TARGET_DB_DEFAULT).strip()


async def _guardrail_check(
    db: Any,
    current_user: dict,
) -> tuple[bool, Optional[str]]:
    """Doppio guardrail: FF + is_test_user server-authoritative.

    Returns:
        (allowed, test_user_id): allowed=True solo se entrambi passano.
        test_user_id è l'id server-side dell'utente (audit) se allowed.
    """
    # 1. Feature flag (B2Q07): server-side, evaluated once, frozen per operation.
    if not feature_flags.is_enabled("cdv_transient_state_enabled"):
        return False, None

    # 2. Test-user eligibility (B2Q06): server-authoritative, fail-closed.
    user_id = (current_user or {}).get("id")
    if not user_id:
        return False, None

    try:
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "id": 1, "is_test_user": 1},
        )
    except Exception:  # noqa: BLE001
        # Fail-closed (B2Q06): DB error → no-op puro.
        return False, None

    if not user:
        return False, None
    if user.get("is_test_user") is not True:
        return False, None

    return True, user.get("id")


async def _build_coordinator(db: Any):
    """Costruisce un ExpeditionRuntimeCoordinator request-scoped (B2Q03).

    Application-scoped adapter (B2Q11) riutilizza il client Mongo esistente.
    Il coordinator è request-scoped.

    Never raises: on failure returns None (fallback isolation B2Q08).
    """
    try:
        from app.stats.runtime.state_store import MongoExpeditionRuntimeStateStore
        from app.stats.runtime.wiring.coordinator import ExpeditionRuntimeCoordinator

        target_db_name = _get_wiring_target_db()
        # Application-scoped: riutilizza il client Mongo del db handle.
        client = db.client  # AsyncIOMotorDatabase.client → AsyncIOMotorClient
        target_db = client[target_db_name]
        collection = target_db["expedition_runtime_states"]

        store = MongoExpeditionRuntimeStateStore(collection=collection)
        return ExpeditionRuntimeCoordinator(
            store=store,
            target_db_name=target_db_name,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "orbus.rt2_b_2a.wiring coordinator_build_failed err=%s", exc,
        )
        return None


async def maybe_shadow_dispatch(
    db: Any,
    current_user: dict,
    guild: dict,
    expedition_doc: dict,
    team_snapshot: Optional[dict] = None,
) -> None:
    """Hook T1: post-validation, pre-resolution (B2Q02 verbatim).

    Guardrail: FF + is_test_user. Se passa, crea shell state via coordinator.
    Never raises. No return value: fire-and-forget-like, ma awaited per
    determinismo dei test (B2Q04 async await inline).

    Args:
        db: motor db handle.
        current_user: dict con `id` (JWT-authenticated).
        guild: guild doc.
        expedition_doc: expedition doc appena inserito.
        team_snapshot: opzionale, per computare `evaluation_hash`.
    """
    try:
        allowed, test_user_id = await _guardrail_check(db, current_user)
        if not allowed:
            return
        coordinator = await _build_coordinator(db)
        if coordinator is None:
            return

        expedition_id = expedition_doc.get("id")
        if not expedition_id:
            return

        # Emette runtime_stat_shadow_evaluated PRIMA della create_state.
        eval_payload = {
            "expedition_id": expedition_id,
            "test_user_id": test_user_id,
            "current_power": int(expedition_doc.get("team_power", 0) or 0),
            "candidate_power": int(expedition_doc.get("final_team_power", 0) or 0),
            "delta": int(expedition_doc.get("equipment_power_bonus", 0) or 0),
            "soft_cap_applied": False,  # RT2-B-2A: soft cap NON autoritativo (B2Q07)
        }
        emit_audit_event(
            "runtime_stat_shadow_evaluated",
            {**eval_payload, "test_user_eligibility": True},
        )

        await coordinator.create_shell_state(
            expedition_id=expedition_id,
            test_user_id=test_user_id or "",
            evaluation_payload=eval_payload,
        )
    except Exception as exc:  # noqa: BLE001
        # Fallback isolation (B2Q08): gameplay preserved, audit warn.
        logger.warning(
            "orbus.rt2_b_2a.wiring maybe_shadow_dispatch_failed err=%s", exc,
        )


async def maybe_shadow_terminalize(
    db: Any,
    current_user: dict,
    expedition_doc: dict,
    success: bool,
) -> None:
    """Hook T2: post-completion (B2Q04 verbatim).

    Guardrail: FF + is_test_user. Se passa, terminalizza state via coordinator.
    Outcome: `COMPLETED` (success=True) OR `COMPLETED_WITH_FAILURE` (success=False).
    `CANCELLED` è riservato a code path futuro (cancellation esplicita).

    Never raises.
    """
    try:
        allowed, test_user_id = await _guardrail_check(db, current_user)
        if not allowed:
            return
        coordinator = await _build_coordinator(db)
        if coordinator is None:
            return

        expedition_id = expedition_doc.get("id")
        if not expedition_id:
            return

        from app.stats.runtime.wiring.coordinator import TerminalOutcome
        outcome = TerminalOutcome.COMPLETED if success else TerminalOutcome.COMPLETED_WITH_FAILURE
        await coordinator.terminalize(expedition_id=expedition_id, outcome=outcome)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "orbus.rt2_b_2a.wiring maybe_shadow_terminalize_failed err=%s", exc,
        )


__all__ = [
    "maybe_shadow_dispatch",
    "maybe_shadow_terminalize",
]
