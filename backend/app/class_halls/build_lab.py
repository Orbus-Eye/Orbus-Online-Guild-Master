"""Read-only loadout guidance for testing the three item-driven Hall builds."""

from __future__ import annotations

from fastapi import HTTPException

from app.class_halls.catalog import get_class_hall_profile
from app.class_halls.mechanics import (
    CLASS_MECHANICS,
    resolve_class_mechanic,
)
from app.items.services import item_public


def _error(status: int, code: str, message: str, **extra) -> HTTPException:
    return HTTPException(
        status_code=status,
        detail={"code": code, "user_message": message, **extra},
    )


def compile_class_hall_build_lab(
    *,
    profile,
    adventurer: dict,
    path_items: list[dict],
    inventory_rows: list[dict],
    equipped_rows: list[dict],
    equipped_items: list[dict],
) -> dict:
    mechanic = CLASS_MECHANICS[profile.canonical_class_slug]
    item_by_id = {
        item.get("id"): item for item in equipped_items if item.get("id")
    }
    equipped_item_ids = {
        row.get("item_id") for row in equipped_rows if row.get("item_id")
    }
    current_items = [
        item_by_id[item_id]
        for item_id in equipped_item_ids
        if item_id in item_by_id
    ]
    current = resolve_class_mechanic(
        adventurer=adventurer,
        equipment_items=current_items,
    )
    current_build = current.get("active_build") or {}
    inventory_by_item = {
        row.get("item_id"): row
        for row in inventory_rows
        if row.get("item_id")
    }
    path_item_by_build = {
        item.get("build_path_id"): item
        for item in path_items
        if item.get("build_path_id")
    }
    expected_build_ids = {
        build.build_id for build in mechanic.builds
    }
    if set(path_item_by_build) != expected_build_ids:
        raise _error(
            503,
            "class_hall.build_lab_incomplete",
            "Il Laboratorio non dispone ancora di tutti e tre i sentieri.",
            expected=sorted(expected_build_ids),
            actual=sorted(path_item_by_build),
        )

    paths = []
    for build in mechanic.builds:
        target_item = path_item_by_build[build.build_id]
        inventory = inventory_by_item.get(target_item["id"])
        owned = bool(inventory and int(inventory.get("quantity") or 0) > 0)
        equipped = target_item["id"] in equipped_item_ids
        competing_items = []
        for item in current_items:
            if item.get("id") == target_item.get("id"):
                continue
            resolved = resolve_class_mechanic(
                adventurer=adventurer,
                equipment_items=[item],
            )
            active = resolved.get("active_build") or {}
            if (
                active.get("resonance_active") is True
                and active.get("build_id") != build.build_id
            ):
                competing_items.append(
                    {
                        "item_id": item.get("id"),
                        "item_name_it": (
                            item.get("display_name_it") or item.get("name")
                        ),
                        "activates_build_id": active.get("build_id"),
                        "slot": next(
                            (
                                row.get("slot")
                                for row in equipped_rows
                                if row.get("item_id") == item.get("id")
                            ),
                            None,
                        ),
                    }
                )
        active_now = bool(
            current_build.get("resonance_active") is True
            and current_build.get("build_id") == build.build_id
        )
        isolated_ready = bool(
            equipped and active_now and not competing_items
        )
        if not owned:
            next_action = "Ottieni questo item dal Sentiero degli Oggetti."
            action_code = "acquire_path_item"
        elif not equipped:
            next_action = "Equipaggia l'item indicato."
            action_code = "equip_path_item"
        elif competing_items:
            next_action = (
                "Rimuovi gli item concorrenti prima della prova, così il "
                "risultato appartiene a una sola build."
            )
            action_code = "unequip_competing_items"
        elif not active_now:
            next_action = (
                "Aggiorna l'equipaggiamento: il sentiero dichiarato non "
                "risulta ancora attivo."
            )
            action_code = "refresh_loadout"
        else:
            next_action = (
                "Build isolata: completa un dungeon o un raid per "
                "registrare il campione."
            )
            action_code = "run_activity"
        paths.append(
            {
                "build_id": build.build_id,
                "build_name_it": build.name_it,
                "description_it": build.description_it,
                "item_tags": list(build.item_tags),
                "path_item": item_public(target_item),
                "owned": owned,
                "owned_quantity": (
                    int(inventory.get("quantity") or 0) if inventory else 0
                ),
                "equipped": equipped,
                "active_now": active_now,
                "isolated_ready": isolated_ready,
                "competing_equipped_items": competing_items,
                "action_code": action_code,
                "next_action_it": next_action,
            }
        )

    return {
        "hall": {
            "hall_id": profile.hall_id,
            "hall_name_it": profile.hall_name_it,
            "class_slug": profile.canonical_class_slug,
            "class_name_it": profile.class_name_it,
            "wave": profile.wave,
        },
        "adventurer": {
            "id": adventurer.get("id"),
            "name": adventurer.get("name"),
            "level": int(adventurer.get("level") or 1),
        },
        "current_build": (
            {
                "build_id": current_build.get("build_id"),
                "name_it": current_build.get("name_it"),
                "resonance_active": bool(
                    current_build.get("resonance_active")
                ),
            }
            if current.get("active")
            else None
        ),
        "isolated_ready_count": sum(
            path["isolated_ready"] for path in paths
        ),
        "total_builds": len(paths),
        "equipment_url": (
            f"/adventurers/{adventurer.get('id')}/equipment"
        ),
        "paths": paths,
    }


async def get_class_hall_build_lab(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
) -> dict:
    profile = get_class_hall_profile(hall_id)
    if not profile:
        raise _error(
            404,
            "class_hall.unknown_hall",
            "Sala di Classe non riconosciuta.",
        )
    adventurer = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id},
        {"_id": 0},
    )
    if not adventurer:
        raise _error(
            404,
            "class_hall.adventurer_not_found",
            "Avventuriero non trovato.",
        )
    if (
        adventurer.get("class_hall_id") != hall_id
        or adventurer.get("canonical_class_slug")
        != profile.canonical_class_slug
    ):
        raise _error(
            409,
            "class_hall.build_lab_wrong_hall",
            "Il Laboratorio deve usare la Sala scelta dall'avventuriero.",
        )
    path_items = await db.items.find(
        {
            "source": f"class_hall:{hall_id}",
            "build_path_id": {"$ne": None},
            "is_active": {"$ne": False},
        },
        {"_id": 0},
    ).to_list(10)
    item_ids = [item["id"] for item in path_items]
    inventory_rows = await db.inventory_items.find(
        {
            "guild_id": guild_id,
            "item_id": {"$in": item_ids},
            "quantity": {"$gt": 0},
        },
        {"_id": 0, "item_id": 1, "quantity": 1},
    ).to_list(10)
    equipped_rows = await db.equipped_items.find(
        {
            "guild_id": guild_id,
            "adventurer_id": adventurer_id,
        },
        {"_id": 0, "item_id": 1, "slot": 1},
    ).to_list(20)
    all_equipped_ids = [
        row.get("item_id") for row in equipped_rows if row.get("item_id")
    ]
    equipped_items = await db.items.find(
        {"id": {"$in": all_equipped_ids}},
        {"_id": 0},
    ).to_list(20)
    return compile_class_hall_build_lab(
        profile=profile,
        adventurer=adventurer,
        path_items=path_items,
        inventory_rows=inventory_rows,
        equipped_rows=equipped_rows,
        equipped_items=equipped_items,
    )


__all__ = [
    "compile_class_hall_build_lab",
    "get_class_hall_build_lab",
]
