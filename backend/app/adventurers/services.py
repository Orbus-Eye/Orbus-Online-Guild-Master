"""Adventurers + classes + traits services (Phase 5.5d)."""
from app.expeditions.formulas import adventurer_base_power as _adventurer_unit_power


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


__all__ = [
    "class_public",
    "trait_public",
    "adventurer_public",
    "list_adventurers_for_guild",
]
