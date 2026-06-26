"""Items domain services (Phase 5.5c.2)."""


def item_public(it: dict) -> dict:
    """Project a Mongo item document to its public JSON shape.

    Includes the full monetization flag set required by the cross-cutting
    monetization invariant (combat/economy/ranking items MUST NOT be
    `can_be_sold_for_real_money`).
    """
    return {
        "id": it["id"],
        "slug": it["slug"],
        "name": it["name"],
        "display_name_it": it.get("display_name_it") or it["name"],
        "display_name_en": it.get("display_name_en") or it["name"],
        "description": it.get("description", ""),
        "item_type": it["item_type"],
        "rarity": it["rarity"],
        "level_required": it.get("level_required", 1),
        "power_score": it["power_score"],
        "strength_bonus": it.get("strength_bonus", 0),
        "agility_bonus": it.get("agility_bonus", 0),
        "intellect_bonus": it.get("intellect_bonus", 0),
        "endurance_bonus": it.get("endurance_bonus", 0),
        "faith_bonus": it.get("faith_bonus", 0),
        "is_tradeable": it.get("is_tradeable", True),
        "is_cosmetic": it.get("is_cosmetic", False),
        "affects_combat": it.get("affects_combat", False),
        "affects_economy": it.get("affects_economy", False),
        "affects_ranking": it.get("affects_ranking", False),
        "can_be_sold_for_gold": it.get("can_be_sold_for_gold", True),
        "can_be_sold_for_real_money": it.get("can_be_sold_for_real_money", False),
        "is_active": it.get("is_active", True),
    }


async def list_active_items(db) -> list[dict]:
    """Return all active, non-test items sorted by name. Used by `GET /api/items`.

    Phase 14.6 ROUND 3.A: filters `is_test=True` so admin/dev test items
    never leak to the public catalog. Mirrors the trait anti-leak filter
    used in adventurers/services.py.
    """
    rows = (
        await db.items.find(
            {"is_active": True, "is_test": {"$ne": True}},
            {"_id": 0},
        )
        .sort("name", 1)
        .to_list(500)
    )
    return [item_public(r) for r in rows]


__all__ = ["item_public", "list_active_items"]
