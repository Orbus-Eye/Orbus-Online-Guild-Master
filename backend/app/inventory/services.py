"""Inventory domain services (Phase 5.5c.2)."""
from typing import Optional

from app.items.services import item_public


def inventory_entry_public(
    row: dict, item: Optional[dict], equipped_count: int = 0
) -> dict:
    """Project an inventory row + (optional) item join to its public shape."""
    total = int(row.get("quantity", 1))
    equipped = max(0, int(equipped_count))
    market_locked = max(0, int(row.get("market_locked_qty", 0)))
    available = max(0, total - equipped - market_locked)
    out = {
        "id": row["id"],
        "guild_id": row["guild_id"],
        "item_id": row["item_id"],
        # Backward-compat: `quantity` keeps the legacy semantics (total owned)
        "quantity": total,
        "total_quantity": total,
        "equipped_quantity": equipped,
        "market_locked_quantity": market_locked,
        "available_quantity": available,
        "acquired_at": row["acquired_at"],
        # ROUND 4 per-instance fields (additive, default-safe)
        "instance_id": row.get("instance_id") or row["id"],
        "is_bound": bool(row.get("is_bound", False)),
        "refinement_level": int(row.get("refinement_level", 0)),
        "enchants": row.get("enchants", []) or [],
        "affixes": row.get("affixes", []) or [],
        "reroll_count": int(row.get("reroll_count", 0)),
        "disenchanted_at": row.get("disenchanted_at"),
        # ROUND 6B.4 — adventurer-bound metadata. `None` for legacy/unbound rows.
        "bound_to_adventurer_id": row.get("bound_to_adventurer_id"),
        "bound_reason": row.get("bound_reason"),
        "bound_at": row.get("bound_at"),
    }
    if item:
        out["item"] = item_public(item)
    return out


async def count_equipped_for_guild_items(db, guild_id: str) -> dict[str, int]:
    """Return {item_id: equipped_count} for the given guild."""
    pipeline = [
        {"$match": {"guild_id": guild_id}},
        {"$group": {"_id": "$item_id", "count": {"$sum": 1}}},
    ]
    out: dict[str, int] = {}
    async for row in db.equipped_items.aggregate(pipeline):
        out[row["_id"]] = int(row["count"])
    return out


async def list_inventory_for_guild(db, guild_id: str) -> list[dict]:
    """Return the full inventory of a guild, joined with item docs + equipped counts.

    Sorted by `acquired_at` desc to match the prior implementation.
    """
    rows = (
        await db.inventory_items.find({"guild_id": guild_id}, {"_id": 0})
        .sort("acquired_at", -1)
        .to_list(500)
    )
    item_ids = list({r["item_id"] for r in rows})
    items_map: dict[str, dict] = {}
    if item_ids:
        items = await db.items.find(
            {"id": {"$in": item_ids}}, {"_id": 0}
        ).to_list(500)
        items_map = {it["id"]: it for it in items}
    equipped_counts = await count_equipped_for_guild_items(db, guild_id)
    return [
        inventory_entry_public(
            r, items_map.get(r["item_id"]), equipped_counts.get(r["item_id"], 0)
        )
        for r in rows
    ]


__all__ = [
    "inventory_entry_public",
    "count_equipped_for_guild_items",
    "list_inventory_for_guild",
]
