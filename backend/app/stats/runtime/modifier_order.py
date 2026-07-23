"""RT2-A · Modifier-order implementation + runtime stat evaluator.

Ordine deterministico (9-step) come da P0Q10 verbatim:
    1. base character stat
    2. equipment flat stat
    3. permanent flat modifiers
    4. temporary flat buffs/debuffs (present at start)
    5. percentage stat modifiers
    6. clamp nominal stat ≥ 0
    7. soft-cap transformation (Intelligence)
    8. derived-power calculation
    9. direct power modifiers

Puro, deterministic, side-effect free.

Compatibility contract:
- Se il chiamante non fornisce modifiers per una stat → treat as zero.
- Se una stat è assente dal base_stats → treat as zero.
- Unknown stat field in input → validation error (raise `ModifierOrderError`).
- Calculation exception → propagate come `ModifierOrderError`; il chiamante
  (shadow path) è responsabile del graceful degrade a "no gameplay impact".

Rounding:
- Intermediate: NONE (nessun rounding fra step 1-7).
- Nominal stat = int (dopo somma flat + percent).
- Effective Intelligence: Decimal precision 4 (via soft_caps).
- Derived power: Decimal precision 4 intermedia; ROUND_HALF_UP finale (fatto
  al momento della somma nel derived-power path).
"""
from __future__ import annotations

import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping

from app.stats.runtime.equipment_aggregation import (
    aggregate_equipment_flat_stats,
    total_power_score_contribution,
)
from app.stats.runtime.models import EffectiveStatResult
from app.stats.runtime.soft_caps import (
    effective_intelligence,
    soft_cap_applied,
    soft_cap_delta,
    INTELLIGENCE_SOFT_CAP,
)
from app.stats.runtime.stat_bridge import RUNTIME_STATS, StatBridgeError, _normalize


class ModifierOrderError(ValueError):
    """Sollevato su input malformato durante evaluate_runtime_stats."""


def _sanitize_stat_dict(
    raw: Mapping[str, Any] | None,
    *,
    strict_unknown: bool,
    field_label: str,
) -> dict[str, int]:
    """Filtra a chiavi runtime + coerce int None-safe.

    - `strict_unknown=True` → una chiave sconosciuta solleva ModifierOrderError
      (validation policy per `base_stats`).
    - `strict_unknown=False` → chiavi sconosciute vengono ignorate silenziosamente
      (per modifier dicts opzionali forniti dal chiamante).
    """
    out = {s: 0 for s in RUNTIME_STATS}
    if raw is None:
        return out
    if not isinstance(raw, Mapping):
        raise ModifierOrderError(
            f"{field_label} must be a mapping, got {type(raw).__name__}"
        )
    for key, val in raw.items():
        norm = _normalize(str(key))
        if norm not in RUNTIME_STATS:
            if strict_unknown:
                raise ModifierOrderError(
                    f"unknown stat field in {field_label}: {key!r}"
                )
            continue
        if val is None:
            continue
        try:
            out[norm] += int(val)
        except (TypeError, ValueError):
            # missing optional stat with malformed value → treat as zero
            continue
    return out


def _apply_percent(nominal: dict[str, int], pct: Mapping[str, Any] | None) -> dict[str, int]:
    """Applica i percent modifiers additivamente (RT1 verbatim: additive stacking).

    Esempio: pct = {"strength": 20, "agility": -10} + nominal = {"strength": 50}
    → strength: 50 * (1 + 0.20) = 60 (int troncato).
    Puro. Nominal stat NON è modificato in-place (nuovo dict).
    """
    if pct is None:
        return dict(nominal)
    pct_sanitized = _sanitize_stat_dict(pct, strict_unknown=False, field_label="percent_modifiers")
    result: dict[str, int] = {}
    for stat, base in nominal.items():
        factor = Decimal(100 + pct_sanitized.get(stat, 0)) / Decimal(100)
        raw = Decimal(base) * factor
        # No intermediate rounding; final coerce to int (truncate on quantize)
        result[stat] = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return result


def evaluate_runtime_stats(
    *,
    base_stats: Mapping[str, Any],
    equipment_items: list[dict[str, Any]] | None = None,
    permanent_modifiers: Mapping[str, Any] | None = None,
    temporary_modifiers_at_start: Mapping[str, Any] | None = None,
    percent_modifiers: Mapping[str, Any] | None = None,
) -> EffectiveStatResult:
    """Valuta le stat runtime applicando l'ordine 9-step.

    Ritorna un `EffectiveStatResult` con nominal, effective (soft-capped),
    diagnostica e durata (ns). Puro.

    :raises ModifierOrderError: su unknown stat field in `base_stats`.
    """
    start_ns = time.perf_counter_ns()
    try:
        # Step 1: base character stat (strict — unknown key = validation error)
        base = _sanitize_stat_dict(base_stats, strict_unknown=True, field_label="base_stats")
        # Step 2: equipment flat stat
        eq_flat = aggregate_equipment_flat_stats(equipment_items)
        # Step 3: permanent flat modifiers
        perm = _sanitize_stat_dict(
            permanent_modifiers, strict_unknown=False, field_label="permanent_modifiers"
        )
        # Step 4: temporary flat buffs/debuffs (present at start)
        temp = _sanitize_stat_dict(
            temporary_modifiers_at_start,
            strict_unknown=False,
            field_label="temporary_modifiers_at_start",
        )
        # Sum flat contributions
        flat_sum = {
            s: base[s] + eq_flat[s] + perm[s] + temp[s] for s in RUNTIME_STATS
        }
        # Step 5: percentage stat modifiers
        nominal = _apply_percent(flat_sum, percent_modifiers)
        # Step 6: clamp nominal stat ≥ 0
        nominal = {s: max(0, v) for s, v in nominal.items()}
        # Step 7: soft-cap transformation (Intelligence only)
        nominal_int = int(nominal.get("intellect", 0))
        eff_int_dec = effective_intelligence(nominal_int)
        effective = {s: Decimal(nominal[s]) for s in RUNTIME_STATS}
        effective["intellect"] = eff_int_dec
        cap_applied = soft_cap_applied(nominal_int)
        cap_delta = soft_cap_delta(nominal_int)
        # Reason code
        reason = "RT2A_STAT_EVAL_OK" if cap_applied else "RT2A_STAT_EVAL_NO_CAP"
        duration_ns = time.perf_counter_ns() - start_ns
        return EffectiveStatResult(
            nominal_stats=nominal,
            effective_stats=effective,
            soft_cap_applied=cap_applied,
            soft_cap_delta=cap_delta,
            evaluation_duration_ns=duration_ns,
            reason_code=reason,
        )
    except ModifierOrderError:
        raise
    except (StatBridgeError, TypeError, ValueError) as exc:
        raise ModifierOrderError(f"calculation exception: {exc}") from exc


def derived_base_power(result: EffectiveStatResult, level: int = 1) -> int:
    """Step 8: derived-power calculation.

    Deriva il base_power da un `EffectiveStatResult`. Formula deterministica
    coerente con `expeditions.formulas.adventurer_base_power` (parità con
    legacy quando i flag RT2-A sono OFF): somma effective stats + level*2.

    ROUND_HALF_UP finale (Step 9 richiede direct power modifiers, applicati
    dal chiamante se necessari; qui restituiamo la base pura int).
    """
    total = Decimal(0)
    for stat in RUNTIME_STATS:
        total += result.effective_stats.get(stat, Decimal(0))
    total += Decimal(int(level)) * Decimal(2)
    return int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


__all__ = [
    "INTELLIGENCE_SOFT_CAP",
    "ModifierOrderError",
    "evaluate_runtime_stats",
    "derived_base_power",
]
