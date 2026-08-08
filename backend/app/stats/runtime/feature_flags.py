"""RT2-A · Server-side default-OFF feature flags (P0Q04 verbatim).

Meccanismo:
- Environment / centralized application settings
- Letti a startup (memoizzati)
- Server controlled (nessun canale client / query param / DB dinamico / API pubblica)
- Default `false` per tutti gli 8 flag canonici
- Fail-safe:
    * `missing flag → false`
    * `invalid flag → startup validation failure OR false with explicit ERROR log`
- Nessun flag auto-abilitato in produzione

Registry evolutivo (8 identificatori totali, nessun nono flag in P2):
    runtime_stat_soft_cap_enabled       (attivabile solo in ambiente autorizzato PM)
    runtime_stat_shadow_enabled         (attivabile per diagnostica shadow)
    cdv_transient_state_enabled         (costante-non-attivabile in RT2-A · RT2-B target)
    item_effect_engine_enabled          (attivabile local/test da RT2-C-P2)
    cdv_item_hooks_enabled              (costante-non-attivabile in RT2-A · RT2-E target)
    effect_observability_enabled        (costante-non-attivabile in RT2-A · RT2-D target)

Environment variable naming: `ORBUS_FLAG_<UPPERCASE_FLAG_ID>`.
Valid truthy values (case-insensitive): "1", "true", "yes", "on".
Valid falsy values (case-insensitive): "0", "false", "no", "off", "" (empty).
Any other value → `_invalid_flag_action` (default: log ERROR + return False).

RT2-B ha promosso i tre flag transient/class/drain. RT2-C-P2 promuove
`item_effect_engine_enabled` soltanto per il gate local/test isolato. I due
identificatori consumer/observability restano hard-forced False.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Final

logger = logging.getLogger("orbus.rt2_a.feature_flags")

# ─── Flag registry ─────────────────────────────────────────────────────
RT2_A_RUNTIME_ATTIVABILE: Final[frozenset[str]] = frozenset(
    {
        "runtime_stat_soft_cap_enabled",
        "runtime_stat_shadow_enabled",
    }
)

# RT2-B-2A · PM verdict B2Q07 verbatim (2026-02):
# `cdv_transient_state_enabled` è ora attivabile via env variable **solo in
# test/local env**. Default OFF. In produzione shared l'env variable NON viene
# settata → il flag resta OFF (fail-safe by default). Nessuna auto-attivazione
# in produzione: la ratifica del PM autorizza esclusivamente activation locale
# isolata per shadow wiring RT2-B-2A.
RT2_B_RUNTIME_ATTIVABILE: Final[frozenset[str]] = frozenset({
    "cdv_transient_state_enabled",
    # RT2-B-2B-1 · PM Message 151 B2BQ10 verbatim: nuovo flag dedicato per
    # class-state transitions (Mark, Fragment, Resource Segment). Default OFF.
    # Attivabile solo con quadruple-gate: transient=true AND class=true AND
    # is_test_user=true AND environment=localhost isolated AND Mongo target
    # allowlisted. In produzione l'env var non è settata → resta OFF.
    "cdv_class_transitions_enabled",
    # RT2-B-2B-2-1 · PM Message 170 B2B2Q13 verbatim: kill-switch DEDICATO
    # Drain. Default OFF. 6-conditions gate composito (normalizzazione PM §13
    # — "quintuple-gate" DEPRECATO): transient AND class AND drain AND
    # is_test_user AND localhost isolated AND Mongo allowlisted.
    # Kill-switch surgical: il flag Drain OFF NON disabilita Mark/Fragment
    # già implementati. Drain OFF ⇒ 0 DB calls · 0 audit events · 0 mutations.
    "cdv_drain_transitions_enabled",
})

RT2_FUTURE_CONSTANTS: Final[frozenset[str]] = frozenset({
    "item_effect_engine_enabled",
    "cdv_item_hooks_enabled",
    "effect_observability_enabled",
})

ALL_FLAGS: Final[frozenset[str]] = (
    RT2_A_RUNTIME_ATTIVABILE
    | RT2_B_RUNTIME_ATTIVABILE
    | RT2_C_RUNTIME_ATTIVABILE
    | RT2_FUTURE_CONSTANTS
)
assert len(ALL_FLAGS) == 8, "RT2-A/B/future must expose exactly 8 flags total"

DEFAULT_VALUE: Final[bool] = False

_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSY: Final[frozenset[str]] = frozenset({"0", "false", "no", "off", ""})


def _env_var_name(flag_id: str) -> str:
    return f"ORBUS_FLAG_{flag_id.upper()}"


def _parse_value(raw: str | None, flag_id: str) -> bool:
    if raw is None:
        return DEFAULT_VALUE
    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    # Invalid value → log ERROR + fail-safe False
    logger.error(
        "orbus.rt2_a.feature_flags invalid_value flag=%s raw=%r fallback=false",
        flag_id,
        raw,
    )
    return False


@lru_cache(maxsize=None)
def _read_raw_env_snapshot() -> dict[str, bool]:
    """Legge tutti gli 8 flag da environment ONE SHOT (memoized).

    Chiamato lazy al primo `is_enabled`. Idempotente.
    """
    snapshot: dict[str, bool] = {}
    for flag in ALL_FLAGS:
        raw = os.environ.get(_env_var_name(flag))
        snapshot[flag] = _parse_value(raw, flag)
    return snapshot


def is_enabled(flag_id: str) -> bool:
    """Ritorna True se il flag è attivo. Fail-safe on unknown → False.

    Enforcement:
    - flag ∉ ALL_FLAGS → log ERROR + return False
    - flag ∈ RT2_FUTURE_CONSTANTS → hard-force False (indipendente da env)
    - flag ∈ RT2_A_RUNTIME_ATTIVABILE | RT2_B_RUNTIME_ATTIVABILE |
      RT2_C_RUNTIME_ATTIVABILE →
      ritorna valore letto da env (default False)

    RT2-B-2A · PM verdict B2Q07 verbatim (2026-02):
    - `cdv_transient_state_enabled` è attivabile solo in test/local env via
      env var `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED=true`. Default OFF.
      In produzione shared l'env var non è settata → resta OFF (fail-safe).
    """
    if flag_id not in ALL_FLAGS:
        logger.error(
            "orbus.rt2_a.feature_flags unknown_flag flag=%s fallback=false",
            flag_id,
        )
        return False
    if flag_id in RT2_FUTURE_CONSTANTS:
        # Hard-force False (RT2-A enforcement — nessun override in questa fase)
        return False
    snapshot = _read_raw_env_snapshot()
    return snapshot.get(flag_id, DEFAULT_VALUE)


def reset_cache() -> None:
    """Reset del cache env snapshot. USO TEST ONLY (mai in runtime prod)."""
    _read_raw_env_snapshot.cache_clear()


def all_flags_status() -> dict[str, bool]:
    """Diagnostica: ritorna lo stato di tutti i 6 flag. Read-only."""
    return {flag: is_enabled(flag) for flag in sorted(ALL_FLAGS)}


__all__ = [
    "ALL_FLAGS",
    "RT2_A_RUNTIME_ATTIVABILE",
    "RT2_B_RUNTIME_ATTIVABILE",
    "RT2_C_RUNTIME_ATTIVABILE",
    "RT2_FUTURE_CONSTANTS",
    "DEFAULT_VALUE",
    "is_enabled",
    "reset_cache",
    "all_flags_status",
]
