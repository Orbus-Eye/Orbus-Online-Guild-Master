"""ROUND 16.0 — Phase 3 — Auto-Equip service.

Given an adventurer, scans guild inventory and equips the best
compatible item per slot, honouring the R15/R16 compatibility validator
(`check_equip_compatibility`). Never downgrades, never equips
incompatible items, and is fully idempotent: a second invocation with
the same inventory state yields zero swaps.

Fitness scoring (simple, deterministic):
    fitness = power_score
            + 2 * sum(stats[primary_stat])
            + 1 * sum(stats[s] for s in secondary_stats)
            + level_bonus (small)

Hard rules:
    * severity == "block"  → item excluded.
    * severity == "warning" → item considered but only as last resort
      (fitness penalised −50%).
    * `required_level` > adventurer.level → excluded.
    * Equipment slot mapping uses `SLOT_TO_ITEM_TYPE`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.audit.log import write_audit
from app.equipment.compatibility import check_equip_compatibility
from app.equipment.services import equip_item_service, unequip_item_service
from app.shared.constants import EQUIPMENT_SLOTS, SLOT_TO_ITEM_TYPE


def item_equip_power(item: dict) -> int:
    """Local copy of `app.equipment.power.item_equip_power` semantics.

    Falls back to `power_score` when available, otherwise sums up the
    integer stat values present on the item.
    """
    if not item:
        return 0
    if "power_score" in item:
        try:
            return int(item.get("power_score") or 0)
        except (TypeError, ValueError):
            pass
    stats = item.get("stats") or {}
    return sum(int(v) for v in stats.values()
               if isinstance(v, (int, float)))


PRIMARY_STAT_WEIGHT = 2
SECONDARY_STAT_WEIGHT = 1
WARNING_PENALTY = 0.5


def _compute_fitness(item: dict, primary: str, secondaries: list[str]) -> float:
    stats = item.get("stats") or {}
    base = float(item_equip_power(item))
    primary_boost = float(stats.get(primary, 0)) * PRIMARY_STAT_WEIGHT
    secondary_boost = sum(
        float(stats.get(s, 0)) for s in (secondaries or [])
    ) * SECONDARY_STAT_WEIGHT
    return base + primary_boost + secondary_boost


async def _load_class_meta(db, class_slug: Optional[str]) -> dict:
    if not class_slug:
        return {"primary_stat": "strength", "secondary_stats": []}
    doc = await db.adventurer_classes.find_one(
        {"slug": class_slug},
        {"_id": 0, "primary_stat": 1, "secondary_stats": 1},
    )
    return doc or {"primary_stat": "strength", "secondary_stats": []}


async def auto_equip_adventurer(
    db, *, guild: dict, adventurer_id: str, actor_user_id: Optional[str],
) -> dict[str, Any]:
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"]},
        {"_id": 0, "id": 1, "name": 1, "level": 1, "class_slug": 1,
         "class_name": 1, "specialization_slug": 1},
    )
    if not adv:
        from fastapi import HTTPException
        raise HTTPException(404, {
            "code": "auto_equip.adventurer_not_found",
            "user_message": "Avventuriero non trovato in questa gilda.",
        })

    cls_meta = await _load_class_meta(db, adv.get("class_slug"))
    primary = cls_meta.get("primary_stat") or "strength"
    secondaries = cls_meta.get("secondary_stats") or []
    adv_level = int(adv.get("level") or 1)

    # Current equipment snapshot per slot.
    eq_docs = await db.equipped_items.find(
        {"guild_id": guild["id"], "adventurer_id": adv["id"]},
        {"_id": 0, "slot": 1, "item_id": 1},
    ).to_list(20)
    current_by_slot: dict[str, dict] = {}
    for e in eq_docs:
        item = await db.items.find_one({"id": e["item_id"]},
                                       {"_id": 0})
        if item:
            current_by_slot[e["slot"]] = item

    # Inventory pool (NOT bound to other adventurers).
    inv_rows = await db.inventory_items.find(
        {"guild_id": guild["id"], "is_active": {"$ne": False}},
        {"_id": 0, "item_id": 1, "is_bound": 1,
         "bound_to_adventurer_id": 1},
    ).to_list(2000)
    item_ids = list({r["item_id"] for r in inv_rows
                     if not r.get("is_bound") or
                     r.get("bound_to_adventurer_id") == adv["id"]})
    if not item_ids:
        items_pool: list[dict] = []
    else:
        items_pool = await db.items.find(
            {"id": {"$in": item_ids}, "is_active": {"$ne": False}},
            {"_id": 0},
        ).to_list(len(item_ids))

    equipped_summary: list[dict] = []
    replaced_summary: list[dict] = []
    unchanged: list[str] = []
    warnings: list[str] = []
    score_before = sum(item_equip_power(i) for i in current_by_slot.values())

    for slot in EQUIPMENT_SLOTS:
        expected_type = SLOT_TO_ITEM_TYPE[slot]
        # Candidates: matching item_type + level + compat severity ≠ block.
        candidates: list[tuple[float, dict]] = []
        for it in items_pool:
            if it.get("item_type") != expected_type:
                continue
            req_lv = int(it.get("required_level") or it.get("level_requirement") or 1)
            if req_lv > adv_level:
                continue
            verdict = check_equip_compatibility(adv, it)
            if verdict["severity"] == "block":
                continue
            fit = _compute_fitness(it, primary, secondaries)
            if verdict["severity"] == "warning":
                fit *= WARNING_PENALTY
            candidates.append((fit, it))
        if not candidates:
            warnings.append(f"{slot}: nessun item compatibile disponibile")
            unchanged.append(slot)
            continue
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_fit, best_item = candidates[0]
        current = current_by_slot.get(slot)
        current_fit = (_compute_fitness(current, primary, secondaries)
                       if current else -1.0)
        if current and best_item.get("id") == current.get("id"):
            unchanged.append(slot)
            continue
        if best_fit <= current_fit:
            unchanged.append(slot)
            continue
        # Swap: unequip current then equip new.
        if current:
            try:
                await unequip_item_service(db, guild, adv["id"], slot)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{slot}: unequip fallito ({type(exc).__name__})")
                continue
        try:
            await equip_item_service(db, guild, adv["id"],
                                     best_item["id"], slot)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{slot}: equip fallito ({type(exc).__name__})")
            continue
        if current:
            replaced_summary.append({
                "slot": slot,
                "old_item_slug": current.get("slug"),
                "new_item_slug": best_item.get("slug"),
                "fitness_delta": round(best_fit - current_fit, 2),
            })
        else:
            equipped_summary.append({
                "slot": slot,
                "item_slug": best_item.get("slug"),
                "fitness": round(best_fit, 2),
            })

    score_after_rows = await db.equipped_items.find(
        {"guild_id": guild["id"], "adventurer_id": adv["id"]},
        {"_id": 0, "item_id": 1},
    ).to_list(20)
    after_items = await db.items.find(
        {"id": {"$in": [r["item_id"] for r in score_after_rows]}},
        {"_id": 0},
    ).to_list(20)
    score_after = sum(item_equip_power(i) for i in after_items)

    swaps_count = len(equipped_summary) + len(replaced_summary)
    await write_audit(
        db, event_type="adventurer_auto_equipped",
        actor_user_id=actor_user_id, actor_guild_id=guild["id"],
        source="equipment.auto_equip",
        metadata={
            "adventurer_id": adv["id"],
            "swaps_count": swaps_count,
            "score_delta": score_after - score_before,
        },
    )

    return {
        "adventurer_id": adv["id"],
        "adventurer_name": adv.get("name"),
        "equipped": equipped_summary,
        "replaced": replaced_summary,
        "unchanged_slots": unchanged,
        "warnings": warnings,
        "score_before": int(score_before),
        "score_after": int(score_after),
        "swaps_count": swaps_count,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["auto_equip_adventurer"]
