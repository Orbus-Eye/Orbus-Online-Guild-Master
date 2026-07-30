"""RT2-A · Loadout snapshot constructor (immutable · expedition-start).

Costruisce un `LoadoutSnapshot` immutabile a partire dallo stato adventurer
+ equipment. Puro, side-effect free. Nessuna persistenza DB.

Regole (P0Q02 §20.3 verbatim):
- Immutabile all'avvio spedizione (dataclass frozen)
- NON salvato come stato persistente del personaggio
- NON aggiornato da equip/unequip successivi
- Può esistere nel contesto runtime già usato dalla spedizione
- Nuova persistenza cross-request → STOP `PERSISTENCE_BASELINE_CONFLICT`
"""

from __future__ import annotations

from typing import Any, Mapping

from app.stats.runtime.equipment_aggregation import aggregate_equipment_flat_stats
from app.stats.runtime.models import LoadoutSnapshot
from app.stats.runtime.modifier_order import evaluate_runtime_stats


def build_loadout_snapshot(
    *,
    adventurer_id: str,
    expedition_id: str,
    base_stats: Mapping[str, Any],
    equipment_items: list[dict[str, Any]] | None = None,
    permanent_modifiers: Mapping[str, Any] | None = None,
    temporary_modifiers_at_start: Mapping[str, Any] | None = None,
    percent_modifiers: Mapping[str, Any] | None = None,
) -> LoadoutSnapshot:
    """Costruisce lo snapshot immutabile all'avvio spedizione.

    Puro. Nessuna scrittura DB. Il chiamante è responsabile di trasportare
    lo snapshot nel contesto runtime dell'expedition_id — mai persistere come
    stato del personaggio.
    """
    if not adventurer_id:
        raise ValueError("adventurer_id required")
    if not expedition_id:
        raise ValueError("expedition_id required")

    result = evaluate_runtime_stats(
        base_stats=base_stats,
        equipment_items=equipment_items,
        permanent_modifiers=permanent_modifiers,
        temporary_modifiers_at_start=temporary_modifiers_at_start,
        percent_modifiers=percent_modifiers,
    )

    equipment_flat = aggregate_equipment_flat_stats(equipment_items)
    blueprint_list: tuple[str, ...] = tuple(
        # Prefer the stable catalog slug over the legacy per-row UUID.  This
        # keeps item-effect identity deterministic across databases/seeds.
        str(item.get("blueprint_id") or item.get("slug") or item.get("id") or "")
        for item in (equipment_items or [])
        if isinstance(item, dict)
    )
    from app.stats.runtime.stat_bridge import RUNTIME_STATS

    base_dict: dict[str, int] = {}
    for s in RUNTIME_STATS:
        raw = base_stats.get(s) if isinstance(base_stats, Mapping) else None
        try:
            base_dict[s] = int(raw) if raw is not None else 0
        except (TypeError, ValueError):
            base_dict[s] = 0
    perm_dict = _dict_from(permanent_modifiers)
    temp_dict = _dict_from(temporary_modifiers_at_start)

    return LoadoutSnapshot(
        adventurer_id=str(adventurer_id),
        expedition_id=str(expedition_id),
        base_stats=base_dict,
        equipment_derived_flat_stats=equipment_flat,
        permanent_modifiers=perm_dict,
        temporary_modifiers_at_start=temp_dict,
        nominal_stats=result.nominal_stats,
        effective_stats=result.effective_stats,
        soft_cap_result=result.soft_cap_applied,
        source_item_blueprint_list=blueprint_list,
    )


def _dict_from(m: Mapping[str, Any] | None) -> dict[str, int]:
    from app.stats.runtime.stat_bridge import RUNTIME_STATS

    out = {s: 0 for s in RUNTIME_STATS}
    if not isinstance(m, Mapping):
        return out
    for s in RUNTIME_STATS:
        raw = m.get(s)
        if raw is None:
            continue
        try:
            out[s] = int(raw)
        except (TypeError, ValueError):
            continue
    return out


__all__ = ["build_loadout_snapshot"]
