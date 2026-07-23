"""RT2-A · Shadow comparison path.

Se `runtime_stat_shadow_enabled = true`, il motore RT2-A calcola in parallelo
al risultato legacy e produce un `ShadowComparisonResult`. Il risultato NON è
autoritativo: non modifica power reale, non modifica success spedizione, non
modifica statistiche salvate, non modifica API pubblica.

Campi diagnostici (P0Q05 verbatim, 10):
    expedition_id, adventurer_id, nominal_intelligence, effective_intelligence,
    current_base_power, candidate_base_power, power_delta, soft_cap_applied,
    evaluation_duration_ms, reason_code

Prohibitions:
- Non registrare loadout intero
- Non registrare dati sensibili (email, token, JWT, RNG seed, boss metadata)
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Optional

from app.stats.runtime.feature_flags import is_enabled
from app.stats.runtime.modifier_order import (
    derived_base_power,
    evaluate_runtime_stats,
    ModifierOrderError,
)


@dataclass(frozen=True)
class ShadowComparisonResult:
    """Diagnostica shadow-mode. Read-only. Non esposto al client."""

    expedition_id: str
    adventurer_id: str
    nominal_intelligence: int
    effective_intelligence: float
    current_base_power: int
    candidate_base_power: int
    power_delta: int
    soft_cap_applied: bool
    evaluation_duration_ms: float
    reason_code: str


def _empty_result(
    expedition_id: str,
    adventurer_id: str,
    reason_code: str,
) -> ShadowComparisonResult:
    return ShadowComparisonResult(
        expedition_id=expedition_id,
        adventurer_id=adventurer_id,
        nominal_intelligence=0,
        effective_intelligence=0.0,
        current_base_power=0,
        candidate_base_power=0,
        power_delta=0,
        soft_cap_applied=False,
        evaluation_duration_ms=0.0,
        reason_code=reason_code,
    )


def compare_shadow(
    *,
    expedition_id: str,
    adventurer_id: str,
    current_base_power: int,
    base_stats: Mapping[str, Any],
    equipment_items: list[dict[str, Any]] | None = None,
    permanent_modifiers: Mapping[str, Any] | None = None,
    temporary_modifiers_at_start: Mapping[str, Any] | None = None,
    percent_modifiers: Mapping[str, Any] | None = None,
    level: int = 1,
) -> Optional[ShadowComparisonResult]:
    """Esegue shadow comparison SE il flag è ON. Altrimenti ritorna None.

    Nessun impatto su gameplay. Failure candidate → return diagnostic
    result con `reason_code="RT2A_SHADOW_CANDIDATE_FAILURE"`.

    Contract:
    - Se `runtime_stat_shadow_enabled=False` → ritorna `None` (nessun calcolo).
    - Se il flag è ON e il calcolo riesce → ritorna `ShadowComparisonResult` popolato.
    - Se il flag è ON e il calcolo fallisce → ritorna diagnostica con reason
      code di failure (no exception propagation; gameplay MUST NOT be affected).
    """
    if not is_enabled("runtime_stat_shadow_enabled"):
        return None
    start = time.perf_counter()
    try:
        result = evaluate_runtime_stats(
            base_stats=base_stats,
            equipment_items=equipment_items,
            permanent_modifiers=permanent_modifiers,
            temporary_modifiers_at_start=temporary_modifiers_at_start,
            percent_modifiers=percent_modifiers,
        )
        candidate_power = derived_base_power(result, level=level)
        duration_ms = (time.perf_counter() - start) * 1000.0
        nominal_int = int(result.nominal_stats.get("intellect", 0))
        effective_int = float(result.effective_stats.get("intellect", Decimal(0)))
        return ShadowComparisonResult(
            expedition_id=expedition_id,
            adventurer_id=adventurer_id,
            nominal_intelligence=nominal_int,
            effective_intelligence=effective_int,
            current_base_power=int(current_base_power),
            candidate_base_power=int(candidate_power),
            power_delta=int(candidate_power) - int(current_base_power),
            soft_cap_applied=result.soft_cap_applied,
            evaluation_duration_ms=duration_ms,
            reason_code=result.reason_code,
        )
    except ModifierOrderError:
        return _empty_result(
            expedition_id, adventurer_id, "RT2A_SHADOW_CANDIDATE_FAILURE"
        )
    except Exception:  # noqa: BLE001 (gameplay MUST NOT be affected)
        return _empty_result(
            expedition_id, adventurer_id, "RT2A_SHADOW_CANDIDATE_UNEXPECTED_ERROR"
        )


__all__ = [
    "ShadowComparisonResult",
    "compare_shadow",
]
