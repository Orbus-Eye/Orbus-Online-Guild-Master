"""RT2-A · Audit event emitters (soft-cap / shadow / invalid stat metadata).

Emissione strutturata di 3 event_type ammessi in RT2-A:
- SOFT_CAP_EVALUATION
- SHADOW_COMPARISON
- INVALID_STAT_METADATA

Regole:
- Livelli: DEBUG (dev/test 100%; prod 0% salvo diagnostica autorizzata);
  INFO (staging 100%, prod futura 10%); WARNING/ERROR 100%.
- Reason code osservabile obbligatorio.
- Non registrare: seed RNG, loadout completo, dati sensibili, metadata boss.
- Sampling casuale non deterministico → PROIBITO.

In RT2-A NON scriviamo su `audit_log` collection (no DB writes). Emettiamo solo
log strutturati JSON su logger dedicato `orbus.rt2_a.events`. L'integrazione con
`audit/log.py::write_audit` è deferita al futuro gate RT2-D (audit runtime).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Mapping

logger = logging.getLogger("orbus.rt2_a.events")

# Environment-driven sampling. Default: DEBUG 100% test/dev, 0% prod.
_APP_ENV = os.environ.get("APP_ENV", "development").lower()


def _sampling_percent(level: str) -> int:
    """Ritorna la percentuale di sampling deterministic per (env, level)."""
    if level in ("WARNING", "ERROR"):
        return 100
    if level == "DEBUG":
        return 100 if _APP_ENV in ("development", "test") else 0
    if level == "INFO":
        if _APP_ENV == "staging":
            return 100
        if _APP_ENV == "production":
            return 10  # future policy per P0Q09
        return 100
    return 100


def _should_emit(event_id: str, level: str) -> bool:
    """Sampling deterministic basato su hash(event_id) mod 100.

    NON usa RNG. Ogni event_id ha destino unico → riproducibile.
    """
    pct = _sampling_percent(level)
    if pct >= 100:
        return True
    if pct <= 0:
        return False
    # Deterministic hash bucket
    bucket = hash(event_id) % 100
    return bucket < pct


def _emit(
    *,
    event_type: str,
    level: str,
    reason_code: str,
    payload: Mapping[str, Any],
) -> None:
    """Emit strutturato. Puro rispetto a I/O di logging."""
    event_id = f"{event_type}:{payload.get('expedition_id', '-')}:{payload.get('adventurer_id', '-')}"
    if not _should_emit(event_id, level):
        return
    record = {
        "event_type": event_type,
        "reason_code": reason_code,
        "level": level,
        **{k: v for k, v in payload.items()},
    }
    logger.log(getattr(logging, level, logging.INFO), json.dumps(record, default=str))


def emit_soft_cap_evaluation(
    *,
    expedition_id: str,
    adventurer_id: str,
    nominal_intelligence: int,
    effective_intelligence: float,
    soft_cap_applied: bool,
    reason_code: str = "RT2A_STAT_EVAL_OK",
) -> None:
    """Event: SOFT_CAP_EVALUATION."""
    _emit(
        event_type="SOFT_CAP_EVALUATION",
        level="DEBUG",
        reason_code=reason_code,
        payload={
            "expedition_id": expedition_id,
            "adventurer_id": adventurer_id,
            "nominal_intelligence": nominal_intelligence,
            "effective_intelligence": effective_intelligence,
            "soft_cap_applied": soft_cap_applied,
        },
    )


def emit_shadow_comparison(
    *,
    expedition_id: str,
    adventurer_id: str,
    nominal_intelligence: int,
    effective_intelligence: float,
    current_base_power: int,
    candidate_base_power: int,
    power_delta: int,
    soft_cap_applied: bool,
    evaluation_duration_ms: float,
    reason_code: str,
) -> None:
    """Event: SHADOW_COMPARISON (10 diagnostic fields P0Q05 verbatim)."""
    _emit(
        event_type="SHADOW_COMPARISON",
        level="INFO",
        reason_code=reason_code,
        payload={
            "expedition_id": expedition_id,
            "adventurer_id": adventurer_id,
            "nominal_intelligence": nominal_intelligence,
            "effective_intelligence": effective_intelligence,
            "current_base_power": current_base_power,
            "candidate_base_power": candidate_base_power,
            "power_delta": power_delta,
            "soft_cap_applied": soft_cap_applied,
            "evaluation_duration_ms": evaluation_duration_ms,
        },
    )


def emit_invalid_stat_metadata(
    *,
    expedition_id: str,
    adventurer_id: str,
    field_name: str,
    reason_code: str,
) -> None:
    """Event: INVALID_STAT_METADATA (WARNING · always 100%)."""
    _emit(
        event_type="INVALID_STAT_METADATA",
        level="WARNING",
        reason_code=reason_code,
        payload={
            "expedition_id": expedition_id,
            "adventurer_id": adventurer_id,
            "field_name": field_name,
        },
    )


__all__ = [
    "emit_soft_cap_evaluation",
    "emit_shadow_comparison",
    "emit_invalid_stat_metadata",
]
