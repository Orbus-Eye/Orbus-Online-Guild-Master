"""RT2-B-2A · Audit event emission (existing server-side substrate).

PM verdict B2Q05 verbatim: audit destination = existing server-side structured
audit/logging substrate. **No new audit collection · no public endpoint · no
response field · no player-facing log**.

5 event id emessi (B2Q05 verbatim):
- `runtime_stat_shadow_evaluated`
- `runtime_state_created`
- `runtime_state_terminalized`
- `runtime_state_shadow_failure`
- `runtime_state_cleanup_deferred`

Campi ammessi (whitelist verbatim B2Q05):
    expedition_id · adventurer_id · test-user eligibility · current/candidate power ·
    delta · soft-cap applied · state version · result code · duration_ms

Campi VIETATI (blacklist verbatim B2Q05):
    seed RNG · intero loadout · credenziali · payload Mongo completo
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("orbus.rt2_b_2a.wiring")


# Whitelist campi consentiti nel payload audit (verbatim B2Q05 + RT2-B-2B-1 extension).
_ALLOWED_FIELDS: frozenset[str] = frozenset({
    "expedition_id",
    "adventurer_id",
    "source_adventurer_id",
    "target_id",
    "test_user_eligibility",
    "current_power",
    "candidate_power",
    "delta",
    "soft_cap_applied",
    "state_version",
    "state_version_before",
    "state_version_after",
    "fencing_token",
    "result_code",
    "duration_ms",
    "evaluation_hash",
    "test_user_id",
    "outcome",
    # RT2-B-2B-1 class-transition additions (PM Message 151 §13)
    "event_id",
    "event_type",
    "event_sequence",
    "reason_code",
    "mark_id",
    "mark_application_id",
    "resource_segment_id",
    "fragment_count_after",
    "active_marks_count_after",
    "focus_bonus_used_after",
    "overflow_discarded",
    "retry_attempts",
    "dedup_reference",
    "phase_id",
    # RT2-B-2B-2-1 Drain additions (PM Message 170 B2B2Q15 campi minimi)
    "drain_execution_id",
    "cancellation_reason",
    "fragment_gain_requested",
    "fragment_gain_applied",
    "fragment_overflow_discarded",
    "mark_valid_at_completion",
    "drains_cancelled_count",
    "cancelled_drain_execution_ids",
})

# Blacklist esplicita — se rilevata, il record NON viene emesso (fail-closed).
_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "seed",
    "seed_rng",
    "rng_seed",
    "loadout",
    "password",
    "token",
    "credentials",
    "email",
    "mongo_payload",
})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_evaluation_hash(payload: dict[str, Any]) -> str:
    """SHA256 stabile del payload di valutazione shadow (subset whitelist).

    Usato come `evaluation_hash` per correlare shadow evaluations e state document
    senza esporre l'intero contenuto della valutazione.
    """
    sanitized = {k: v for k, v in sorted(payload.items()) if k in _ALLOWED_FIELDS}
    raw = json.dumps(sanitized, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _sanitize(record: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Applica whitelist + blacklist. Ritorna None se blacklist rilevata."""
    for k in record.keys():
        if k in _FORBIDDEN_FIELDS:
            logger.error(
                "orbus.rt2_b_2a.wiring audit_forbidden_field field=%s dropped",
                k,
            )
            return None
    return {k: v for k, v in record.items() if k in _ALLOWED_FIELDS}


def emit_audit_event(event_id: str, record: dict[str, Any]) -> bool:
    """Emette un audit event via structured logger (JSON line).

    Ritorna True se emesso, False se blacklist ha rifiutato il record.
    NEVER raises: fail-safe by design.
    """
    sanitized = _sanitize(record)
    if sanitized is None:
        return False
    payload = {
        "event_id": event_id,
        "timestamp": utc_now_iso(),
        **sanitized,
    }
    # Structured logging: JSON line su substrate esistente.
    try:
        logger.info("audit_event %s", json.dumps(payload, sort_keys=True, default=str))
    except Exception as exc:  # noqa: BLE001
        logger.error("orbus.rt2_b_2a.wiring audit_emission_failed err=%s", exc)
        return False
    return True


__all__ = [
    "emit_audit_event",
    "compute_evaluation_hash",
    "utc_now_iso",
]
