"""Equipment services (Phase 5.5d).

Equipment slot map, load helpers, snapshot serializer, and the three service
operations (get/equip/unequip). Pure functions (`_empty_slot_map`,
`_equipped_slot_entry`, `_item_summary_for_snapshot`) carry no DB access and
can be imported eagerly. Async helpers accept the Motor `db` handle.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.expeditions.formulas import (
    adventurer_base_power as _adventurer_unit_power,
    item_equip_power as _item_equip_power,
)
from app.items.services import item_public
from app.shared.constants import EQUIPMENT_SLOTS, SLOT_TO_ITEM_TYPE

LEGACY_SLOT_ALIASES = {"armor": "chest"}


def normalize_equipment_slot(slot: str) -> str:
    value = (slot or "").strip().lower()
    return LEGACY_SLOT_ALIASES.get(value, value)


def _storage_slots_for(slot: str) -> list[str]:
    canonical = normalize_equipment_slot(slot)
    legacy = [old for old, new in LEGACY_SLOT_ALIASES.items() if new == canonical]
    return [canonical, *legacy]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _empty_slot_map() -> dict:
    return {slot: None for slot in EQUIPMENT_SLOTS}


def _equipped_slot_entry(equipped_row: dict, item: dict) -> dict:
    """Shape returned to clients for a single occupied slot."""
    slot = normalize_equipment_slot(equipped_row["slot"])
    return {
        "equipped_item_id": equipped_row["id"],
        "item": item_public(item),
        "slot": slot,
    }


def _item_summary_for_snapshot(equipped_row: dict, item: dict) -> dict:
    """Frozen, minimal shape persisted on expedition_members.equipment_snapshot."""
    return {
        "slot": equipped_row["slot"],
        "item_id": item["id"],
        "item_name": item["name"],
        "rarity": item.get("rarity", "Common"),
        "strength_bonus": int(item.get("strength_bonus", 0)),
        "agility_bonus": int(item.get("agility_bonus", 0)),
        "intellect_bonus": int(item.get("intellect_bonus", 0)),
        "endurance_bonus": int(item.get("endurance_bonus", 0)),
        "faith_bonus": int(item.get("faith_bonus", 0)),
        "power_score": int(item.get("power_score", 0)),
    }


async def _load_equipment_for_adventurer(
    db, adventurer_id: str
) -> tuple[dict, int, list[dict]]:
    """Return (slot_map_for_public_response, equipment_power, raw_equipped_rows_with_item).

    `raw_equipped_rows_with_item` is a list of {row, item} dicts (used for snapshots).
    """
    rows = await db.equipped_items.find(
        {"adventurer_id": adventurer_id}, {"_id": 0}
    ).to_list(20)
    slots = _empty_slot_map()
    eq_power = 0
    raw: list[dict] = []
    if not rows:
        return slots, 0, raw
    item_ids = list({r["item_id"] for r in rows})
    items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(50)
    items_by_id = {i["id"]: i for i in items}
    for r in rows:
        item = items_by_id.get(r["item_id"])
        if not item:
            continue
        canonical_slot = normalize_equipment_slot(r["slot"])
        if canonical_slot in slots:
            slots[canonical_slot] = _equipped_slot_entry(r, item)
        eq_power += _item_equip_power(item)
        raw.append({"row": r, "item": item})
    return slots, eq_power, raw


async def _load_equipment_for_guild(
    db, guild_id: str
) -> dict[str, tuple[dict, int]]:
    """Batch-load equipment for all adventurers in a guild.

    Returns {adventurer_id: (slot_map, equipment_power)}.
    """
    rows = await db.equipped_items.find(
        {"guild_id": guild_id}, {"_id": 0}
    ).to_list(2000)
    if not rows:
        return {}
    item_ids = list({r["item_id"] for r in rows})
    items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(500)
    items_by_id = {i["id"]: i for i in items}
    by_adv: dict[str, tuple[dict, int]] = {}
    for r in rows:
        item = items_by_id.get(r["item_id"])
        if not item:
            continue
        slots, power = by_adv.get(r["adventurer_id"], (_empty_slot_map(), 0))
        canonical_slot = normalize_equipment_slot(r["slot"])
        if canonical_slot not in slots:
            continue
        slots[canonical_slot] = _equipped_slot_entry(r, item)
        by_adv[r["adventurer_id"]] = (slots, power + _item_equip_power(item))
    return by_adv


def _build_equipment_response(adventurer: dict, slots: dict, eq_power: int) -> dict:
    base_power = _adventurer_unit_power(adventurer)
    return {
        "adventurer_id": adventurer["id"],
        "slots": slots,
        "base_power": base_power,
        "equipment_power": int(eq_power),
        "total_power": base_power + int(eq_power),
    }


async def _adventurer_owned_or_404(db, adventurer_id: str, guild_id: str) -> dict:
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        # FASE 3.5 — messaggi player-facing in italiano.
        raise HTTPException(status_code=404, detail="Avventuriero non trovato")
    return adv


async def get_equipment_for_adventurer(
    db, guild: dict, adventurer_id: str
) -> dict:
    adv = await _adventurer_owned_or_404(db, adventurer_id, guild["id"])
    slots, eq_power, _raw = await _load_equipment_for_adventurer(db, adv["id"])
    return _build_equipment_response(adv, slots, eq_power)


async def equip_item_service(
    db, guild: dict, adventurer_id: str, item_id: str, slot: str
) -> dict:
    adv = await _adventurer_owned_or_404(db, adventurer_id, guild["id"])
    # ROUND 6B.3 Wave 1.5 — block equip on retired adventurers BEFORE the
    # generic `is_available` check so the FE gets a structured 423 instead
    # of a string 400.
    if adv.get("is_retired") is True:
        raise HTTPException(
            status_code=423,
            detail={
                "code": "equip.target_retired",
                "source": "equipment.equip",
                "adventurer_id": adventurer_id,
                "user_message": (
                    "Non puoi equipaggiare un avventuriero congedato. "
                    "Reintegralo dal supporto oppure scegli un altro avventuriero."
                ),
            },
        )
    if not adv.get("is_available", True):
        raise HTTPException(
            status_code=400,
            detail="Non puoi modificare l'equipaggiamento di un avventuriero in spedizione",
        )

    slot = normalize_equipment_slot(slot)
    if slot not in EQUIPMENT_SLOTS:
        raise HTTPException(
            status_code=400,
            detail=f"Slot '{slot}' non valido. Slot ammessi: {', '.join(EQUIPMENT_SLOTS)}",
        )

    item = await db.items.find_one({"id": item_id, "is_active": True}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Oggetto non trovato")

    expected_type = SLOT_TO_ITEM_TYPE[slot]
    if item.get("item_type") != expected_type:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Item type '{item.get('item_type')}' cannot be equipped in slot '{slot}'"
            ),
        )
    declared_slot = normalize_equipment_slot(item.get("slot_type") or "")
    slot_family = slot.split("_", 1)[0] if slot.startswith(("ring_", "trinket_")) else slot
    if declared_slot:
        declared_family = (
            declared_slot.split("_", 1)[0]
            if declared_slot.startswith(("ring_", "trinket_"))
            else declared_slot
        )
        if declared_family != slot_family:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Item slot '{item.get('slot_type')}' cannot be equipped "
                    f"in physical slot '{slot}'"
                ),
            )

    # ROUND 11.3 TASK B — adventurer-level gate on equip. MUST run before
    # the atomic reservation so we don't have to refund a reserved_qty on
    # the rejection path. PWR alone does NOT bypass.
    from app.equipment.level_gate import enforce_item_level_requirement
    enforce_item_level_requirement(item, adv, source="equipment.equip")

    # ROUND 15 FASE 2 — class-compatibility validator. Hard blocks (heavy
    # armour on caster, arcane staff on melee, signature class lock) → 400.
    # Soft warnings (non-recommended class) are appended to the response.
    from app.equipment.compatibility import check_equip_compatibility
    compat = check_equip_compatibility(adv, item)
    if compat["severity"] == "block":
        raise HTTPException(
            status_code=400,
            detail={
                "code": f"equip.incompatible.{compat['reason_code']}",
                "source": "equipment.equip",
                "reason_it": compat["reason_it"],
                "severity": "block",
                "adventurer_id": adventurer_id,
                "item_id": item_id,
            },
        )
    _equip_warning = (
        compat if compat["severity"] == "warning" else None
    )

    inv_row = await db.inventory_items.find_one(
        {"guild_id": guild["id"], "item_id": item_id}, {"_id": 0}
    )
    if not inv_row:
        raise HTTPException(
            status_code=404,
            detail="Oggetto non presente nel deposito della gilda",
        )

    # ROUND 6B.4 Task 2 — adventurer-bound guard.
    # If the inventory row is bound to another adventurer, reject the equip
    # with a 422 + structured `code` so the FE renders the proper toast.
    from app.inventory.bound import is_bound_to_other_adventurer
    if is_bound_to_other_adventurer(inv_row, adv["id"]):
        from app.core.bound_errors import raise_equipment_not_transferable
        raise_equipment_not_transferable(
            source="equipment.equip",
            bound_to_adventurer_id=inv_row.get("bound_to_adventurer_id"),
            target_adventurer_id=adv["id"],
        )

    # Phase 9.3.1 — atomic reservation. Replaces the previous non-atomic
    # (`total - count`) check that could allow concurrent equips on different
    # adventurers to duplicate a single-quantity item. We $inc reserved_qty
    # gated by `reserved_qty < quantity` server-side via `$expr`. `$ifNull`
    # covers legacy docs predating Phase 9.3.1 where the field is missing.
    reserved = await db.inventory_items.find_one_and_update(
        {
            "guild_id": guild["id"],
            "item_id": item_id,
            "$expr": {
                "$lt": [
                    {"$ifNull": ["$reserved_qty", 0]},
                    {"$ifNull": ["$quantity", 0]},
                ]
            },
        },
        {"$inc": {"reserved_qty": 1}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    if not reserved:
        raise HTTPException(
            status_code=409,
            detail="Oggetto non disponibile (già equipaggiato da un altro avventuriero)",
        )

    now = utc_now()
    occupied = await db.equipped_items.find_one(
        {
            "guild_id": guild["id"],
            "adventurer_id": adv["id"],
            "slot": {"$in": _storage_slots_for(slot)},
        },
        {"_id": 0, "id": 1},
    )
    if occupied:
        await db.inventory_items.update_one(
            {
                "guild_id": guild["id"],
                "item_id": item_id,
                "reserved_qty": {"$gt": 0},
            },
            {"$inc": {"reserved_qty": -1}},
        )
        raise HTTPException(
            status_code=400,
            detail="Slot già occupato: rimuovi prima l'oggetto attuale",
        )
    new_row = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "adventurer_id": adv["id"],
        "item_id": item_id,
        "slot": slot,
        "equipped_at": now.isoformat(),
    }
    try:
        await db.equipped_items.insert_one(new_row)
    except DuplicateKeyError:
        # Slot was taken between the reservation and the insert. Refund the
        # atomic reservation so the inventory invariant `reserved <= quantity`
        # stays exact.
        await db.inventory_items.update_one(
            {
                "guild_id": guild["id"],
                "item_id": item_id,
                "reserved_qty": {"$gt": 0},
            },
            {"$inc": {"reserved_qty": -1}},
        )
        raise HTTPException(
            status_code=400,
            detail="Slot già occupato: rimuovi prima l'oggetto attuale",
        )

    slots, eq_power, _raw = await _load_equipment_for_adventurer(db, adv["id"])
    # Phase 14 — daily quest progress (best-effort)
    try:
        from app.quests.services import increment_quest_progress
        await increment_quest_progress(db, guild["id"], "equip")
    except Exception:
        pass
    # Phase 14.1 — weekly quest progress (best-effort)
    try:
        from app.quests.services import increment_weekly_progress
        await increment_weekly_progress(db, guild["id"], "items_equipped", 1)
    except Exception:
        pass
    # Phase 14.7 — audit log (best-effort)
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="equip_item",
            actor_guild_id=guild["id"],
            item_slug=item.get("slug"), item_template_id=item.get("id"),
            quantity=1, source="equip",
            related_entity_id=adv["id"],
            metadata={"slot": slot},
        )
    except Exception:
        pass
    response = _build_equipment_response(adv, slots, eq_power)
    # ROUND 15 FASE 2 — surface soft compatibility warning to FE.
    if _equip_warning:
        response["warning_it"] = _equip_warning["reason_it"]
        response["warning_code"] = _equip_warning["reason_code"]
    # ROUND 15 Phase 3 — achievement trigger (best-effort).
    try:
        from app.achievements.engine import evaluate_achievements
        await evaluate_achievements(
            guild["id"], "item_equipped",
            {"item_slug": item.get("slug"), "slot": slot,
             "adventurer_id": adv["id"], "class_slug": adv.get("class_slug")},
            db=db,
        )
    except Exception:
        pass
    return response


async def unequip_item_service(
    db, guild: dict, adventurer_id: str, slot: str
) -> dict:
    adv = await _adventurer_owned_or_404(db, adventurer_id, guild["id"])
    if not adv.get("is_available", True):
        raise HTTPException(
            status_code=400,
            detail="Non puoi modificare l'equipaggiamento di un avventuriero in spedizione",
        )

    slot = normalize_equipment_slot(slot)
    if slot not in EQUIPMENT_SLOTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid slot '{slot}'. Must be one of: {', '.join(EQUIPMENT_SLOTS)}",
        )

    # Phase 9.3.1 — atomic delete that also returns the freed item_id so we
    # can release the reservation. We use find_one_and_delete to capture the
    # row in one round-trip.
    freed = await db.equipped_items.find_one_and_delete(
        {
            "adventurer_id": adv["id"],
            "slot": {"$in": _storage_slots_for(slot)},
            "guild_id": guild["id"],
        },
        projection={"_id": 0, "item_id": 1},
    )
    if not freed:
        raise HTTPException(status_code=404, detail=f"No item equipped in slot '{slot}'")

    # Release the inventory reservation. Guard `reserved_qty > 0` keeps the
    # counter from going negative even if the row is somehow stale.
    await db.inventory_items.update_one(
        {
            "guild_id": guild["id"],
            "item_id": freed["item_id"],
            "reserved_qty": {"$gt": 0},
        },
        {"$inc": {"reserved_qty": -1}},
    )

    slots, eq_power, _raw = await _load_equipment_for_adventurer(db, adv["id"])
    # Phase 14.7 — audit log (best-effort)
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="unequip_item",
            actor_guild_id=guild["id"],
            item_template_id=freed["item_id"],
            quantity=1, source="equip",
            related_entity_id=adv["id"],
            metadata={"slot": slot},
        )
    except Exception:
        pass
    return _build_equipment_response(adv, slots, eq_power)


__all__ = [
    "_empty_slot_map",
    "normalize_equipment_slot",
    "_equipped_slot_entry",
    "_item_summary_for_snapshot",
    "_load_equipment_for_adventurer",
    "_load_equipment_for_guild",
    "_build_equipment_response",
    "_adventurer_owned_or_404",
    "get_equipment_for_adventurer",
    "equip_item_service",
    "unequip_item_service",
]
