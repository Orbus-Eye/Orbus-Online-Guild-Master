"""Guild collection book for the 27 Class Hall item paths."""

from __future__ import annotations

from fastapi import HTTPException

from app.class_halls.catalog import CLASS_HALLS
from app.items.services import item_public


async def get_class_hall_collection_book(db, *, guild_id: str) -> dict:
    """Return ownership/equipment progress for all 135 canonical Hall items."""
    items = await db.items.find(
        {
            "source": {"$regex": "^class_hall:"},
            "is_active": {"$ne": False},
            "is_test": {"$ne": True},
        },
        {"_id": 0},
    ).to_list(200)
    if len(items) != 135:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "class_hall.collection_catalog_incomplete",
                "user_message": (
                    "Il Libro della Collezione non è ancora completo."
                ),
                "expected": 135,
                "actual": len(items),
            },
        )
    item_ids = [item["id"] for item in items]
    if (
        len(set(item_ids)) != 135
        or len({item["slug"].casefold() for item in items}) != 135
        or len(
            {
                (item.get("display_name_it") or item["name"]).casefold()
                for item in items
            }
        )
        != 135
    ):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "class_hall.collection_catalog_not_singular",
                "user_message": (
                    "Il catalogo contiene identità duplicate e non può "
                    "essere mostrato come collezione."
                ),
            },
        )

    inventory_rows = await db.inventory_items.find(
        {
            "guild_id": guild_id,
            "item_id": {"$in": item_ids},
            "quantity": {"$gt": 0},
        },
        {"_id": 0, "item_id": 1, "quantity": 1, "reserved_qty": 1},
    ).to_list(200)
    inventory_by_item = {
        row["item_id"]: row for row in inventory_rows
    }
    equipped_rows = await db.equipped_items.find(
        {
            "guild_id": guild_id,
            "item_id": {"$in": item_ids},
        },
        {"_id": 0, "item_id": 1, "adventurer_id": 1},
    ).to_list(500)
    equipped_by_item: dict[str, list[str]] = {}
    for row in equipped_rows:
        equipped_by_item.setdefault(row["item_id"], []).append(
            row["adventurer_id"]
        )

    assignments = await db.adventurers.find(
        {
            "guild_id": guild_id,
            "is_retired": {"$ne": True},
            "retired": {"$ne": True},
            "archived": {"$ne": True},
            "class_hall_id": {"$in": list(CLASS_HALLS)},
        },
        {"_id": 0, "class_hall_id": 1},
    ).to_list(500)
    assigned_counts: dict[str, int] = {}
    for adventurer in assignments:
        hall_id = adventurer["class_hall_id"]
        assigned_counts[hall_id] = assigned_counts.get(hall_id, 0) + 1

    items_by_hall: dict[str, list[dict]] = {}
    for item in items:
        hall_id = item["source"].split(":", 1)[1]
        items_by_hall.setdefault(hall_id, []).append(item)

    halls = []
    for profile in sorted(
        CLASS_HALLS.values(),
        key=lambda value: (value.wave, value.class_name_it),
    ):
        track_items = sorted(
            items_by_hall.get(profile.hall_id, []),
            key=lambda item: int(item.get("acquisition_track_order") or 0),
        )
        if (
            len(track_items) != 5
            or [
                int(item.get("acquisition_track_order") or 0)
                for item in track_items
            ]
            != [0, 1, 2, 3, 4]
        ):
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "class_hall.collection_track_incomplete",
                    "hall_id": profile.hall_id,
                    "expected": 5,
                    "actual": len(track_items),
                    "user_message": (
                        "Un sentiero del Libro della Collezione è incompleto."
                    ),
                },
            )

        public_items = []
        owned_count = 0
        equipped_count = 0
        for item in track_items:
            inventory = inventory_by_item.get(item["id"])
            equipped_adventurers = equipped_by_item.get(item["id"], [])
            owned = bool(inventory)
            equipped = bool(equipped_adventurers)
            owned_count += int(owned)
            equipped_count += int(equipped)
            public_items.append(
                {
                    "order": int(item.get("acquisition_track_order") or 0),
                    "is_signature": (
                        int(item.get("acquisition_track_order") or 0) == 0
                    ),
                    "status": (
                        "equipped"
                        if equipped
                        else ("owned" if owned else "undiscovered")
                    ),
                    "owned_quantity": (
                        int(inventory.get("quantity") or 0)
                        if inventory
                        else 0
                    ),
                    "reserved_quantity": (
                        int(inventory.get("reserved_qty") or 0)
                        if inventory
                        else 0
                    ),
                    "equipped_adventurer_ids": equipped_adventurers,
                    "item": item_public(item),
                }
            )
        halls.append(
            {
                "hall_id": profile.hall_id,
                "hall_name_it": profile.hall_name_it,
                "class_slug": profile.canonical_class_slug,
                "class_name_it": profile.class_name_it,
                "wave": profile.wave,
                "lore_hook_it": profile.lore_hook_it,
                "hall_master_witness_npc": profile.hall_master_witness_npc,
                "assigned_adventurers": assigned_counts.get(
                    profile.hall_id,
                    0,
                ),
                "owned_count": owned_count,
                "equipped_count": equipped_count,
                "total_count": 5,
                "is_complete": owned_count == 5,
                "items": public_items,
            }
        )

    owned_total = sum(hall["owned_count"] for hall in halls)
    completed_halls = sum(hall["is_complete"] for hall in halls)
    return {
        "guild_id": guild_id,
        "owned_count": owned_total,
        "total_count": 135,
        "completion_percent": round(owned_total / 135 * 100, 1),
        "completed_halls": completed_halls,
        "total_halls": 27,
        "halls": halls,
    }


__all__ = ["get_class_hall_collection_book"]
