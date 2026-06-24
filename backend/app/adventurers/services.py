"""Adventurers + classes + traits services (Phase 5.5d)."""
from fastapi import HTTPException

from app.expeditions.formulas import (
    TRAIT_AFFECTABLE_STATS,
    TRAIT_XP_STAT,
    adventurer_base_power as _adventurer_unit_power,
    adventurer_effective_power as _adventurer_effective_power,
    apply_trait_modifiers,
    sum_xp_percent,
)


def class_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "slug": doc["slug"],
        "role": doc["role"],
        "description": doc.get("description", ""),
        "base_strength": doc["base_strength"],
        "base_agility": doc["base_agility"],
        "base_intellect": doc["base_intellect"],
        "base_endurance": doc["base_endurance"],
        "base_faith": doc["base_faith"],
        "is_active": doc.get("is_active", True),
    }


def trait_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "description": doc.get("description", ""),
        "modifier_type": doc["modifier_type"],
        "affected_stat": doc["affected_stat"],
        "modifier_value": doc["modifier_value"],
        "is_positive": doc["is_positive"],
        "is_active": doc.get("is_active", True),
    }


def adventurer_public(doc: dict) -> dict:
    """Public projection. Caller must inject `_equipment_slots` + `_equipment_power`
    via `_load_equipment_for_*` (Phase 6) when including equipment info; otherwise
    defaults to empty slots + zero equipment power."""
    # Lazy import to avoid a circular dep between adventurers ↔ equipment domains.
    from app.equipment.services import _empty_slot_map

    eq_slots = doc.get("_equipment_slots") or _empty_slot_map()
    eq_power = int(doc.get("_equipment_power", 0))
    base_power = _adventurer_unit_power(doc)
    return {
        "id": doc["id"],
        "guild_id": doc["guild_id"],
        "name": doc["name"],
        "adventurer_class_id": doc["adventurer_class_id"],
        "class_name": doc.get("class_name"),
        "class_role": doc.get("class_role"),
        "rarity": doc.get("rarity", "Common"),
        "level": doc.get("level", 1),
        "experience": doc.get("experience", 0),
        "strength": doc["strength"],
        "agility": doc["agility"],
        "intellect": doc["intellect"],
        "endurance": doc["endurance"],
        "faith": doc["faith"],
        "stamina": doc.get("stamina", 100),
        "morale": doc.get("morale", 100),
        "is_available": doc.get("is_available", True),
        "traits": doc.get("traits", []),
        "equipment": eq_slots,
        "base_power": base_power,
        "equipment_power": eq_power,
        "total_power": base_power + eq_power,
        "created_at": doc["created_at"],
        "updated_at": doc.get("updated_at", doc["created_at"]),
    }


async def list_adventurers_for_guild(db, guild_id: str) -> list[dict]:
    """Return all adventurers of a guild + equipment join, public-projected."""
    from app.equipment.services import _empty_slot_map, _load_equipment_for_guild

    rows = (
        await db.adventurers.find({"guild_id": guild_id}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(500)
    )
    equip_map = await _load_equipment_for_guild(db, guild_id)
    out = []
    for r in rows:
        slots, power = equip_map.get(r["id"], (_empty_slot_map(), 0))
        r["_equipment_slots"] = slots
        r["_equipment_power"] = power
        out.append(adventurer_public(r))
    return out


async def trait_preview_for_adventurer(db, guild_id: str, adventurer_id: str) -> dict:
    """Phase 13 — read-only preview of trait effects on stats / power.

    Returns base (no-trait) and effective (trait-applied) stats and power,
    plus a per-trait delta summary. Ownership is enforced; adventurers
    that don't belong to the caller's guild yield 404 (no leak).
    """
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    traits = adv.get("traits") or []
    base_stats = {s: int(adv.get(s, 0)) for s in TRAIT_AFFECTABLE_STATS}
    effective_stats = apply_trait_modifiers(base_stats, traits) if traits else dict(base_stats)
    base_power = _adventurer_unit_power(adv)
    effective_power = _adventurer_effective_power(adv)
    xp_pct = sum_xp_percent(traits)
    applied = []
    for t in traits:
        affected = t.get("affected_stat")
        mtype = t.get("modifier_type")
        val = t.get("modifier_value", 0) or 0
        if affected in TRAIT_AFFECTABLE_STATS and mtype == "flat":
            sign = "+" if val >= 0 else ""
            delta = f"{sign}{int(val)} {affected}"
        elif affected in TRAIT_AFFECTABLE_STATS and mtype == "percent":
            sign = "+" if val >= 0 else ""
            delta = f"{sign}{val}% {affected}"
        elif affected == TRAIT_XP_STAT and mtype == "percent":
            sign = "+" if val >= 0 else ""
            delta = f"{sign}{val}% xp_gain"
        else:
            delta = "no effect"
        applied.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "modifier_type": mtype,
            "affected_stat": affected,
            "modifier_value": val,
            "is_positive": t.get("is_positive", True),
            "delta_summary": delta,
        })
    return {
        "adventurer_id": adv["id"],
        "base_stats": base_stats,
        "effective_stats": effective_stats,
        "applied_traits": applied,
        "base_power": base_power,
        "effective_power": effective_power,
        "power_delta": effective_power - base_power,
        "xp_gain_percent": xp_pct,
    }


__all__ = [
    "class_public",
    "trait_public",
    "adventurer_public",
    "list_adventurers_for_guild",
    "trait_preview_for_adventurer",
]
