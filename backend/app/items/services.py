"""Items domain services (Phase 5.5c.2)."""


def item_public(it: dict) -> dict:
    """Project a Mongo item document to its public JSON shape.

    Includes the full monetization flag set required by the cross-cutting
    monetization invariant (combat/economy/ranking items MUST NOT be
    `can_be_sold_for_real_money`).
    """
    # ROUND 11.3 TASK B — single source of truth for the required level.
    # Avoids drift between the FE display and the server-side gate.
    from app.equipment.level_gate import resolve_item_required_level

    return {
        "id": it["id"],
        "slug": it["slug"],
        "name": it["name"],
        "display_name_it": it.get("display_name_it") or it["name"],
        "display_name_en": it.get("display_name_en") or it["name"],
        "description": it.get("description", ""),
        "description_it": it.get("description_it") or it.get("description", ""),
        "description_en": it.get("description_en") or it.get("description", ""),
        "item_type": it["item_type"],
        "rarity": it["rarity"],
        "level_required": it.get("level_required", 1),
        # ROUND 11.3 TASK B — derived field: the actual gate the equip
        # service will enforce. Honours explicit `required_adventurer_level`
        # if set, else legacy `level_required` if > 1, else a rarity-based
        # default. FE uses this to grey-out under-level cards before equip.
        "required_adventurer_level": resolve_item_required_level(it),
        # ROUND 11.1 P1 (post-Slice-1 hotfix) — defensive `.get(..., 0)` for
        # all numeric fields. Some catalog materials (e.g. lesser_arcane_dust,
        # greater_arcane_dust) were seeded without an explicit `power_score`,
        # which raised KeyError on `GET /api/inventory` for any guild
        # holding them. The seed has been backfilled (see migrations), but
        # we keep the defensive default here so future seeds can't reintroduce
        # the regression silently.
        "power_score": it.get("power_score", 0),
        # FASE 3.3 — contratto effetto consumabile (None per non-consumabili).
        "consumable_effect": it.get("consumable_effect") or None,
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
        # ROUND 13a — Lore meta (additive, additivo per UI Inventory/Auction/Equip).
        "flavor_text_it": it.get("flavor_text_it"),
        "flavor_text_en": it.get("flavor_text_en"),
        "lore_tags": it.get("lore_tags") or [],
        "lore_source": it.get("lore_source"),
        "spoiler_level": it.get("spoiler_level") or "public",
        "lore_reviewed": bool(it.get("lore_reviewed", False)),
        "source": it.get("source"),
        "acquisition_sources": it.get("acquisition_sources") or [],
        "acquisition_hint_it": it.get("acquisition_hint_it"),
        "acquisition_track_order": it.get("acquisition_track_order"),
        "build_path_id": it.get("build_path_id"),
        "build_path_name_it": it.get("build_path_name_it"),
        "build_path_description_it": it.get(
            "build_path_description_it"
        ),
        "build_path_item_tags": it.get("build_path_item_tags") or [],
        # RT2-E starter vertical slice: player-facing projection only.
        # Executable details (primitive/magnitude/target/stacking) remain in
        # the static server registry and are never accepted from clients.
        "has_runtime_effect": bool(
            isinstance(it.get("effect_metadata"), dict)
            and it["effect_metadata"].get("enabled", True) is True
        ),
        "effect_summary_it": (
            it.get("effect_metadata", {}).get("effect_summary_it")
            if isinstance(it.get("effect_metadata"), dict)
            else None
        ),
        "effect_summary_en": (
            it.get("effect_metadata", {}).get("effect_summary_en")
            if isinstance(it.get("effect_metadata"), dict)
            else None
        ),
        "effect_lore_key": (
            it.get("effect_metadata", {}).get("lore_key")
            if isinstance(it.get("effect_metadata"), dict)
            else None
        ),
        # R18.4 canonical slot_type (post-B3 real apply; null se non equipable/materials)
        "slot_type": it.get("slot_type"),
        # R18.4 item binding policy raw enum ("hard"|"soft"|"universal"); default None se legacy
        "item_binding_policy": it.get("item_binding_policy"),
        # R18.4.followup UI 4-state derived signal (context-free):
        # true se item_binding_policy=="universal". recommended_for_class NON è
        # esposto qui (context-aware, solo endpoint /api/adventurers/{id}/eligible-items).
        "is_universal": (it.get("item_binding_policy") == "universal"),
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
        .to_list(2000)
    )
    return [item_public(r) for r in rows]


async def get_catalog_contract_status(db) -> dict:
    """Return canonical targets plus a read-only audit of runtime items."""
    from app.items.catalog_contract import (
        audit_catalog_items,
        public_catalog_contract,
    )

    rows = await db.items.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0, "rarity": 1, "is_active": 1, "is_test": 1},
    ).to_list(2000)
    return {
        "contract": public_catalog_contract(),
        "audit": audit_catalog_items(rows),
    }


__all__ = [
    "get_catalog_contract_status",
    "item_public",
    "list_active_items",
]
