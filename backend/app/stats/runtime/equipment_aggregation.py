"""RT2-A · Pure equipment-stat aggregation.

Aggrega i flat-stat contributi dagli equipaggiamenti in un dict runtime.
Funzione pura, side-effect free. Nessun proc, nessun effetto item, nessun hook.

Input: iterable di dict-item con potenziali chiavi `<stat>_bonus` per ognuna
delle 5 stat runtime + campo `power_score` (non aggregato qui — power_score
resta contribuzione diretta al potere, gestito dal chiamante).

None-safe: valori assenti o `None` sono trattati come 0. Chiavi non-runtime
vengono ignorate (nessun errore).

Regola RT1-invariant: **il proc/effetto item NON è mai valutato qui**. Solo
somma dei flat bonus. Gli item legacy senza `effect_metadata` sono validi.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.stats.runtime.stat_bridge import RUNTIME_STATS


def aggregate_equipment_flat_stats(
    items: Iterable[dict[str, Any]] | None,
) -> dict[str, int]:
    """Somma i flat-stat bonus di tutti gli item forniti.

    Restituisce un dict {runtime_stat: int} con le 5 chiavi RUNTIME_STATS
    sempre presenti (default 0). Puro.
    """
    result: dict[str, int] = {s: 0 for s in RUNTIME_STATS}
    if items is None:
        return result
    for item in items:
        if not isinstance(item, dict):
            continue
        for stat in RUNTIME_STATS:
            raw = item.get(f"{stat}_bonus")
            if raw is None:
                continue
            try:
                result[stat] += int(raw)
            except (TypeError, ValueError):
                # missing optional stat with malformed value → treat as zero
                continue
    return result


def total_power_score_contribution(
    items: Iterable[dict[str, Any]] | None,
) -> int:
    """Somma le contribuzioni `power_score` degli item (int-safe).

    Ritorna la somma dei `power_score` di ogni item. Trattamento None-safe:
    valori assenti/None/malformati → 0.
    """
    if items is None:
        return 0
    total = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        raw = item.get("power_score")
        if raw is None:
            continue
        try:
            total += int(raw)
        except (TypeError, ValueError):
            continue
    return total


__all__ = [
    "aggregate_equipment_flat_stats",
    "total_power_score_contribution",
]
