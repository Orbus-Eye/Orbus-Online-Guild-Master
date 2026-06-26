"""Phase 14.6 (ROUND 3.B) — Crafting domain.

Two endpoints:
  - GET  /api/recipes            → list recipes + per-guild eligibility
  - POST /api/recipes/{slug}/craft → craft action (atomic)

Atomicity strategy
------------------
The Mongo deployment (`mongodb://localhost`) is a stand-alone server, so we
can't rely on multi-document transactions. We use a pre-flight validation +
conditional `$inc` pattern:

  1. Re-read recipe + guild + relevant inventory rows under one read pass.
  2. Validate guild_level / gold / materials + non-equipped quantity.
  3. Decrement each input row with a conditional update that asserts the
     current `quantity >= required + reserved`. If any single decrement
     fails (concurrent equip / craft), revert prior decrements by `$inc`.
  4. Decrement gold under a conditional update `gold >= cost`. Revert on
     failure.
  5. Upsert the output item into inventory (`$inc` quantity).

The reverts (`$inc` positive) are themselves idempotent and never lose
material — at worst we end up where we started.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

logger = logging.getLogger("orbus.crafting")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _localized_name(item_or_recipe: dict, lang: str = "it") -> str:
    if lang == "en":
        return item_or_recipe.get("display_name_en") or item_or_recipe.get("name") or item_or_recipe.get("slug", "")
    return item_or_recipe.get("display_name_it") or item_or_recipe.get("name") or item_or_recipe.get("slug", "")


async def _load_item_map_by_slug(db, slugs: list[str]) -> dict[str, dict]:
    items = await db.items.find(
        {"slug": {"$in": slugs}, "is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    ).to_list(200)
    return {it["slug"]: it for it in items}


async def _load_inventory_by_item_ids(db, guild_id: str, item_ids: list[str]) -> dict[str, dict]:
    rows = await db.inventory_items.find(
        {"guild_id": guild_id, "item_id": {"$in": item_ids}},
        {"_id": 0},
    ).to_list(200)
    return {r["item_id"]: r for r in rows}


async def _equipped_count(db, guild_id: str, item_id: str) -> int:
    return await db.equipped_items.count_documents({"guild_id": guild_id, "item_id": item_id})


def _recipe_public(recipe: dict, items_by_slug: dict[str, dict], lang: str = "it") -> dict:
    """Project a recipe to its public list shape."""
    out_item = items_by_slug.get(recipe["output_item_slug"], {})
    return {
        "slug": recipe["slug"],
        "display_name": _localized_name(recipe, lang),
        "description": recipe.get("description_it") if lang == "it" else recipe.get("description_en"),
        "inputs": [
            {
                "item_slug": i["item_slug"],
                "quantity": int(i["quantity"]),
                "item_name": _localized_name(items_by_slug.get(i["item_slug"], {}), lang),
                "item_rarity": items_by_slug.get(i["item_slug"], {}).get("rarity"),
            }
            for i in recipe.get("inputs", [])
        ],
        "gold_cost": int(recipe.get("gold_cost", 0)),
        "output": {
            "item_slug": recipe["output_item_slug"],
            "quantity": int(recipe.get("output_quantity", 1)),
            "name": _localized_name(out_item, lang),
            "rarity": out_item.get("rarity"),
            "item_type": out_item.get("item_type"),
        },
        "required_guild_level": int(recipe.get("required_guild_level", 1)),
    }


async def list_recipes_with_eligibility(db, guild: dict, lang: str = "it") -> dict:
    recipes = await db.recipes.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    ).sort("required_guild_level", 1).to_list(200)

    # Gather all item slugs we need (inputs + outputs)
    all_slugs: set[str] = set()
    for r in recipes:
        for i in r.get("inputs", []):
            all_slugs.add(i["item_slug"])
        all_slugs.add(r["output_item_slug"])
    items_by_slug = await _load_item_map_by_slug(db, list(all_slugs))
    # Map item_id → row for the guild's inventory (only for inputs)
    input_item_ids = [it["id"] for slug, it in items_by_slug.items() if slug in {i["item_slug"] for r in recipes for i in r["inputs"]}]
    inv_by_id = await _load_inventory_by_item_ids(db, guild["id"], input_item_ids)
    # Available qty (= quantity - equipped) per item_id
    available_by_id: dict[str, int] = {}
    for item_id, row in inv_by_id.items():
        eq = await _equipped_count(db, guild["id"], item_id)
        available_by_id[item_id] = max(0, int(row.get("quantity", 0)) - eq)

    guild_gold = int(guild.get("gold", 0))
    guild_level = int(guild.get("level", 1))

    enriched = []
    for r in recipes:
        pub = _recipe_public(r, items_by_slug, lang)
        missing: dict[str, int] = {}
        gold_short = max(0, pub["gold_cost"] - guild_gold)
        if guild_level < pub["required_guild_level"]:
            status = "requires_level"
        else:
            for i in r.get("inputs", []):
                it = items_by_slug.get(i["item_slug"])
                if not it:
                    missing[i["item_slug"]] = int(i["quantity"])
                    continue
                have = available_by_id.get(it["id"], 0)
                need = int(i["quantity"])
                if have < need:
                    missing[i["item_slug"]] = need - have
            if missing:
                status = "missing_materials"
            elif gold_short > 0:
                status = "insufficient_gold"
            else:
                status = "craftable"
        pub.update({
            "status": status,
            "missing": missing,
            "gold_short": gold_short,
        })
        enriched.append(pub)
    return {"recipes": enriched}


async def craft_recipe(db, guild: dict, recipe_slug: str, lang: str = "it") -> dict:
    """Atomic craft. Raises 400/404/409 on failure."""
    recipe = await db.recipes.find_one(
        {"slug": recipe_slug, "is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 1) Guild level gate
    if int(guild.get("level", 1)) < int(recipe.get("required_guild_level", 1)):
        raise HTTPException(
            status_code=400,
            detail=f"Requires guild level {recipe.get('required_guild_level', 1)}",
        )

    # 2) Resolve all input items + output item
    input_slugs = [i["item_slug"] for i in recipe.get("inputs", [])]
    needed_slugs = list(set(input_slugs + [recipe["output_item_slug"]]))
    items_by_slug = await _load_item_map_by_slug(db, needed_slugs)
    for slug in needed_slugs:
        if slug not in items_by_slug:
            raise HTTPException(status_code=409, detail=f"Item '{slug}' is not available")

    # 3) Pre-flight: gold + materials with equipped exclusion
    gold_cost = int(recipe.get("gold_cost", 0))
    if int(guild.get("gold", 0)) < gold_cost:
        raise HTTPException(status_code=400, detail="Not enough gold")
    inv_by_id = await _load_inventory_by_item_ids(
        db, guild["id"], [items_by_slug[s]["id"] for s in input_slugs]
    )
    for i in recipe["inputs"]:
        it = items_by_slug[i["item_slug"]]
        row = inv_by_id.get(it["id"])
        have = int((row or {}).get("quantity", 0))
        eq = await _equipped_count(db, guild["id"], it["id"])
        if have - eq < int(i["quantity"]):
            raise HTTPException(
                status_code=400,
                detail=f"Not enough materials: need {i['quantity']} of {it.get('name')}",
            )

    # 4) Atomic decrement loop with rollback on conflict
    decremented: list[tuple[str, int]] = []  # (item_id, qty) for revert
    for i in recipe["inputs"]:
        it = items_by_slug[i["item_slug"]]
        eq = await _equipped_count(db, guild["id"], it["id"])
        min_required_total = eq + int(i["quantity"])
        res = await db.inventory_items.update_one(
            {
                "guild_id": guild["id"],
                "item_id": it["id"],
                "quantity": {"$gte": min_required_total},
            },
            {"$inc": {"quantity": -int(i["quantity"])}},
        )
        if res.modified_count != 1:
            # Revert everything decremented so far.
            for revert_id, revert_qty in decremented:
                await db.inventory_items.update_one(
                    {"guild_id": guild["id"], "item_id": revert_id},
                    {"$inc": {"quantity": revert_qty}},
                )
            raise HTTPException(
                status_code=409,
                detail="Inventory changed during craft — try again",
            )
        decremented.append((it["id"], int(i["quantity"])))

    # 5) Conditional gold decrement (rollback inventory on conflict)
    gold_res = await db.guilds.update_one(
        {"id": guild["id"], "gold": {"$gte": gold_cost}},
        {"$inc": {"gold": -gold_cost}, "$set": {"updated_at": _utc_now_iso()}},
    )
    if gold_res.modified_count != 1:
        for revert_id, revert_qty in decremented:
            await db.inventory_items.update_one(
                {"guild_id": guild["id"], "item_id": revert_id},
                {"$inc": {"quantity": revert_qty}},
            )
        raise HTTPException(status_code=409, detail="Gold changed during craft — try again")

    # 6) Upsert output (quantity += output_quantity)
    out_item = items_by_slug[recipe["output_item_slug"]]
    out_qty = int(recipe.get("output_quantity", 1))
    now = _utc_now_iso()
    await db.inventory_items.update_one(
        {"guild_id": guild["id"], "item_id": out_item["id"]},
        {
            "$inc": {"quantity": out_qty},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "guild_id": guild["id"],
                "item_id": out_item["id"],
                "acquired_at": now,
                "source": "crafting",
                "bind_state": "unbound",
            },
        },
        upsert=True,
    )

    # 7) Best-effort audit log (persistent audit log is ROUND 3.D)
    logger.info(
        "craft ok guild=%s recipe=%s gold=-%d out=%s x%d",
        guild["id"], recipe_slug, gold_cost, out_item["slug"], out_qty,
    )
    # Phase 14.7 — persistent audit log
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="gold_debited",
            actor_guild_id=guild["id"], gold_delta=-gold_cost,
            source="crafting", related_entity_id=recipe_slug,
        )
        for i in recipe["inputs"]:
            inp_item = items_by_slug[i["item_slug"]]
            await write_audit(
                db, event_type="crafting_inputs_consumed",
                actor_guild_id=guild["id"],
                item_slug=inp_item["slug"], item_template_id=inp_item["id"],
                quantity=-int(i["quantity"]),
                source="crafting", related_entity_id=recipe_slug,
            )
        await write_audit(
            db, event_type="item_crafted",
            actor_guild_id=guild["id"],
            item_slug=out_item["slug"], item_template_id=out_item["id"],
            quantity=out_qty,
            source="crafting", related_entity_id=recipe_slug,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit write failed in craft_recipe: %s", exc)

    # Phase 14.1 — weekly quest progress (best-effort, non-critical)
    try:
        from app.quests.services import increment_weekly_progress
        await increment_weekly_progress(
            db, guild["id"], "items_crafted", out_qty
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("weekly quest hook failed in craft_recipe: %s", exc)

    remaining_gold = int(guild.get("gold", 0)) - gold_cost
    return {
        "success": True,
        "output_item": {
            "slug": out_item["slug"],
            "name": _localized_name(out_item, lang),
            "rarity": out_item.get("rarity"),
            "quantity": out_qty,
        },
        "remaining_gold": remaining_gold,
    }


__all__ = ["list_recipes_with_eligibility", "craft_recipe"]
