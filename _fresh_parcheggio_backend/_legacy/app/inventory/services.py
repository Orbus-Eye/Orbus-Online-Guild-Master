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
        "acquired_at": row.get("acquired_at") or row.get("bound_at") or row.get("created_at") or "1970-01-01T00:00:00+00:00",
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
        # Phase 5A additive: legendary instance markers (default False).
        "is_legendary_instance": bool(row.get("is_legendary_instance", False)),
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

    Post-verify Phase 5A Iter1 fix (bug #2): the returned list also
    includes rows from `legendary_item_instances` (BOP legendary items
    live in a dedicated collection to avoid unique-index clash with
    stackable materials). Legendary rows are shaped like regular
    inventory rows with `is_legendary_instance=True` + `is_bound=True`
    + `quantity=1` (legendary instances are unique).
    """
    rows = (
        await db.inventory_items.find({"guild_id": guild_id}, {"_id": 0})
        .sort("acquired_at", -1)
        .to_list(500)
    )
    # Phase 5A: merge legendary instances (dedicated collection).
    leg_rows = (
        await db.legendary_item_instances.find(
            {"guild_id": guild_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(500)
    )
    item_ids = list({r["item_id"] for r in rows}
                    | {r["item_id"] for r in leg_rows if r.get("item_id")})
    items_map: dict[str, dict] = {}
    if item_ids:
        items = await db.items.find(
            {"id": {"$in": item_ids}}, {"_id": 0}
        ).to_list(500)
        items_map = {it["id"]: it for it in items}
    equipped_counts = await count_equipped_for_guild_items(db, guild_id)
    out = [
        inventory_entry_public(
            r, items_map.get(r["item_id"]), equipped_counts.get(r["item_id"], 0)
        )
        for r in rows
    ]
    # Append legendary instances mapped to public shape
    now_iso = "1970-01-01T00:00:00+00:00"
    for lr in leg_rows:
        entry = inventory_entry_public(
            {
                "id": lr["id"],
                "guild_id": lr["guild_id"],
                "item_id": lr.get("item_id") or "",
                "quantity": int(lr.get("quantity", 1)),
                "acquired_at": (lr.get("bound_at") or lr.get("created_at")
                                 or now_iso),
                "instance_id": lr["id"],
                "is_bound": True,
                "bound_to_adventurer_id": None,
                "bound_reason": "legendary_forge_craft",
                "bound_at": lr.get("bound_at"),
                "is_legendary_instance": True,
            },
            items_map.get(lr.get("item_id")),
            0,
        )
        entry["is_legendary_instance"] = True
        entry["legendary_quality"] = lr.get("legendary_quality")
        entry["legendary_stats"] = lr.get("legendary_stats") or {}
        entry["source_craft_order_id"] = lr.get("source_craft_order_id")
        out.append(entry)
    return out


__all__ = [
    "inventory_entry_public",
    "count_equipped_for_guild_items",
    "list_inventory_for_guild",
]
