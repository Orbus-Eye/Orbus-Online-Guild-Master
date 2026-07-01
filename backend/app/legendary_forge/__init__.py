"""ROUND 16.3 Phase 5A — Legendary Forge.

Compact single-file module:
- 6 recipe seed (idempotent) mapped to REAL existing materials
- 6 legendary items seed with hard-cap stat guardrail (+50% vs epic baseline)
- Craft orders with CAS lifecycle + on-visit resolve (no scheduler)
- Deterministic RNG seeded by (guild_id, order_id) for idempotent resolution
- Pity system: after 5 crafts without "perfezionato", the 6th imperfetto is
  clamped to "normale" (no downgrade)
- BOP legendary items: is_bound=true, no market/auction/gold-sell
- Admin: toggle recipe, stats, dev-force-complete (gated APP_ENV)
- Recovery CLI script + admin audit whitelist (23 -> 28 events)

Guild level gate: recipes visible only to guild.level >= recipe.guild_level_required.
"""
from __future__ import annotations

import hashlib
import logging
import os
import random as _random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.legendary_forge")

router = APIRouter(prefix="/api/legendary-forge",
                    tags=["legendary-forge"])
admin_router = APIRouter(prefix="/api/admin/legendary-forge",
                          tags=["admin", "legendary-forge"])

# ── Constants ────────────────────────────────────────────────────────
# Epic baseline snapshot (2026-Q2) — see report "Epic Baseline Snapshot
# & Rebalance Policy". If epic tier is rebalanced, this must be updated
# explicitly (grep-friendly key EPIC_STAT_BASELINE).
EPIC_STAT_BASELINE = {
    "weapon":    {"primary": 5, "secondary": 2, "power_score": 7},
    "armor":     {"primary": 5, "secondary": 2, "power_score": 7},
    "accessory": {"primary": 2, "secondary": 2, "power_score": 7},
}
# Cap = baseline * 1.5, rounded down to integer.
LEGENDARY_CAP = {
    "weapon":    {"primary": 7, "secondary": 3, "power_score": 10},
    "armor":     {"primary": 7, "secondary": 3, "power_score": 10},
    "accessory": {"primary": 3, "secondary": 3, "power_score": 10},
}
PITY_THRESHOLD = 5           # after 5 crafts without perfezionato
CRAFT_DURATION_SECONDS = 180  # 3 min V1 (fast for validation)
MIN_GUILD_LEVEL = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _is_production() -> bool:
    return (os.environ.get("APP_ENV") or "development").lower() == "production"


def _rng_for(guild_id: str, order_id: str) -> _random.Random:
    """Deterministic RNG: same (guild, order) → same rolls (idempotency
    for on-visit fallback + recovery CLI)."""
    seed = int(hashlib.sha256(
        f"{guild_id}:{order_id}".encode("utf-8")).hexdigest()[:16], 16)
    return _random.Random(seed)


# ── Recipes seed (6) — using REAL materials only ─────────────────────
RECIPES = [
    {"slug": "spada_di_alveora", "name_it": "Spada di Alveora",
     "name_en": "Sword of Alveora", "output_slug": "legendary_sword_alveora",
     "resources": [{"slug": "frammento_di_ergolat", "qty": 2},
                    {"slug": "osso_di_irthe", "qty": 1}],
     "materials": [{"slug": "iron_shard", "qty": 5},
                    {"slug": "dragon_essence", "qty": 3}],
     "gold": 35000, "guild_level_required": 7, "base_success_chance": 75},
    {"slug": "armatura_ambash", "name_it": "Armatura di Ambash",
     "name_en": "Armor of Ambash", "output_slug": "legendary_armor_ambash",
     "resources": [{"slug": "cristallo_di_ambash", "qty": 2},
                    {"slug": "linfa_di_soe", "qty": 1}],
     "materials": [{"slug": "raw_leather", "qty": 5},
                    {"slug": "greater_arcane_dust", "qty": 3}],
     "gold": 30000, "guild_level_required": 6, "base_success_chance": 78},
    {"slug": "anello_di_velur", "name_it": "Anello di Velur",
     "name_en": "Ring of Velur", "output_slug": "legendary_ring_velur",
     "resources": [{"slug": "cenere_di_velur", "qty": 3}],
     "materials": [{"slug": "greater_arcane_dust", "qty": 4}],
     "gold": 15000, "guild_level_required": 5, "base_success_chance": 82},
    {"slug": "bastone_di_efreto", "name_it": "Bastone di Efreto",
     "name_en": "Staff of Efreto", "output_slug": "legendary_staff_efreto",
     "resources": [{"slug": "nucleo_di_efreto", "qty": 2},
                    {"slug": "cristallo_di_ambash", "qty": 1}],
     "materials": [{"slug": "arcane_dust", "qty": 5},
                    {"slug": "dragon_essence", "qty": 3}],
     "gold": 40000, "guild_level_required": 8, "base_success_chance": 72},
    {"slug": "amuleto_di_nathos", "name_it": "Amuleto di Nathos",
     "name_en": "Amulet of Nathos", "output_slug": "legendary_amulet_nathos",
     "resources": [{"slug": "seme_di_nathos", "qty": 2}],
     "materials": [{"slug": "greater_arcane_dust", "qty": 4},
                    {"slug": "arcane_dust", "qty": 2}],
     "gold": 20000, "guild_level_required": 5, "base_success_chance": 80},
    {"slug": "mantello_di_aveol", "name_it": "Mantello di Aveol",
     "name_en": "Cloak of Aveol", "output_slug": "legendary_cape_aveol",
     "resources": [{"slug": "sigillo_di_aveol", "qty": 2},
                    {"slug": "linfa_di_soe", "qty": 1}],
     "materials": [{"slug": "raw_leather", "qty": 4},
                    {"slug": "greater_arcane_dust", "qty": 3}],
     "gold": 45000, "guild_level_required": 9, "base_success_chance": 70},
]

# Quality chances (same for all recipes V1)
PERFEZIONATO_CHANCE = 18
IMPERFETTO_CHANCE = 7  # rest = "normale"
QUALITY_MULTIPLIERS = {"perfezionato": 1.15, "normale": 1.0, "imperfetto": 0.9}

# ── Legendary items seed (6) — stats within epic*1.5 cap ─────────────
LEGENDARY_ITEMS = [
    {"slug": "legendary_sword_alveora", "name_it": "Spada di Alveora",
     "item_type": "weapon", "base_stats": {"strength": 7, "endurance": 3,
                                             "power_score": 10}},
    {"slug": "legendary_armor_ambash", "name_it": "Armatura di Ambash",
     "item_type": "armor", "base_stats": {"endurance": 7, "agility": 2,
                                            "power_score": 10}},
    {"slug": "legendary_ring_velur", "name_it": "Anello di Velur",
     "item_type": "accessory", "base_stats": {"strength": 3, "faith": 3,
                                                 "power_score": 10}},
    {"slug": "legendary_staff_efreto", "name_it": "Bastone di Efreto",
     "item_type": "weapon", "base_stats": {"intellect": 7, "faith": 3,
                                             "power_score": 10}},
    {"slug": "legendary_amulet_nathos", "name_it": "Amuleto di Nathos",
     "item_type": "accessory", "base_stats": {"intellect": 3, "endurance": 3,
                                                "power_score": 10}},
    {"slug": "legendary_cape_aveol", "name_it": "Mantello di Aveol",
     "item_type": "armor", "base_stats": {"agility": 7, "faith": 3,
                                            "power_score": 10}},
]


def _validate_base_stats_within_cap() -> None:
    """Seed-time guardrail: panic if any recipe's base_stats already
    exceed LEGENDARY_CAP BEFORE quality multipliers apply. Forces
    explicit review when epic baseline is rebalanced."""
    for it in LEGENDARY_ITEMS:
        cap = LEGENDARY_CAP.get(it["item_type"])
        if not cap:
            raise ValueError(
                f"legendary_forge: unknown item_type {it['item_type']}")
        s = it["base_stats"]
        for stat_key in ("strength", "agility", "intellect",
                          "endurance", "faith"):
            v = s.get(stat_key, 0)
            # primary/secondary determination: any stat != 0 is either
            # primary (highest) or secondary. Use max as bound.
            if v > cap["primary"]:
                raise ValueError(
                    f"legendary_forge SEED VIOLATION: "
                    f"{it['slug']}.{stat_key}={v} exceeds cap "
                    f"{cap['primary']} for {it['item_type']}. "
                    f"Update EPIC_STAT_BASELINE or reduce base_stats.")
        if s.get("power_score", 0) > cap["power_score"]:
            raise ValueError(
                f"legendary_forge SEED VIOLATION: {it['slug']}.power_score="
                f"{s.get('power_score')} exceeds cap {cap['power_score']}")


async def seed_legendary_forge_catalog() -> dict:
    """Idempotent seed of 6 recipes + 6 legendary items."""
    _validate_base_stats_within_cap()
    now_iso = _iso(_now())
    inserted_recipes = 0
    for r in RECIPES:
        doc = dict(r)
        doc.update({"perfezionato_chance": PERFEZIONATO_CHANCE,
                     "imperfetto_chance": IMPERFETTO_CHANCE,
                     "crafting_duration_seconds": CRAFT_DURATION_SECONDS,
                     "is_active": True,
                     "created_at": now_iso, "updated_at": now_iso})
        res = await db.legendary_recipe_catalog.update_one(
            {"slug": r["slug"]},
            {"$setOnInsert": doc}, upsert=True)
        if res.upserted_id:
            inserted_recipes += 1
    inserted_items = 0
    for it in LEGENDARY_ITEMS:
        doc = {
            "slug": it["slug"], "name_it": it["name_it"],
            "name_en": it["name_it"],
            "item_type": it["item_type"], "rarity": "legendary",
            "is_tradeable": False, "is_bound": True,
            "bind_type": "on_pickup", "is_cosmetic": False,
            "affects_combat": True, "affects_economy": False,
            "can_be_sold_for_gold": False,
            "can_be_sold_for_real_money": False,
            "base_stats": it["base_stats"],
            "quality_multipliers": QUALITY_MULTIPLIERS,
            "created_at": now_iso, "updated_at": now_iso,
        }
        res = await db.legendary_items_catalog.update_one(
            {"slug": it["slug"]},
            {"$setOnInsert": doc}, upsert=True)
        if res.upserted_id:
            inserted_items += 1
    return {"recipes_total": len(RECIPES),
            "items_total": len(LEGENDARY_ITEMS),
            "inserted_recipes": inserted_recipes,
            "inserted_items": inserted_items}


async def ensure_indexes() -> None:
    try:
        await db.legendary_recipe_catalog.create_index("slug", unique=True)
        await db.legendary_items_catalog.create_index("slug", unique=True)
        await db.legendary_forge_crafting_orders.create_index("id", unique=True)
        await db.legendary_forge_crafting_orders.create_index(
            [("guild_id", 1), ("status", 1)])
        await db.legendary_forge_crafting_orders.create_index(
            [("status", 1), ("completes_at", 1)])
        await db.legendary_forge_pity_counters.create_index(
            "guild_id", unique=True)
        await db.legendary_item_instances.create_index("id", unique=True)
        await db.legendary_item_instances.create_index(
            [("guild_id", 1), ("created_at", -1)])
    except Exception as exc:
        logger.debug("legendary_forge index create: %s", exc)


# ── Helpers ──────────────────────────────────────────────────────────
async def _get_pity(guild_id: str) -> dict:
    doc = await db.legendary_forge_pity_counters.find_one(
        {"guild_id": guild_id}, {"_id": 0})
    if not doc:
        return {"guild_id": guild_id,
                "pity_counter_since_perfezionato": 0,
                "last_perfezionato_at": None,
                "total_craft_count": 0,
                "total_perfezionato_count": 0,
                "updated_at": _iso(_now())}
    return doc


async def _bump_pity(guild_id: str, quality: Optional[str]) -> None:
    now_iso = _iso(_now())
    pity = await _get_pity(guild_id)
    upd = {"$set": {"updated_at": now_iso},
            "$inc": {"total_craft_count": 1}}
    if quality == "perfezionato":
        upd["$set"]["pity_counter_since_perfezionato"] = 0
        upd["$set"]["last_perfezionato_at"] = now_iso
        upd["$inc"]["total_perfezionato_count"] = 1
    else:
        upd["$inc"]["pity_counter_since_perfezionato"] = 1
    await db.legendary_forge_pity_counters.update_one(
        {"guild_id": guild_id}, upd, upsert=True)


def _compute_success_chance(recipe: dict, guild_level: int) -> int:
    base = int(recipe.get("base_success_chance", 75))
    lvl_bonus = min(
        max(guild_level - int(recipe.get("guild_level_required", 5)), 0) * 2,
        15)
    return min(base + lvl_bonus, 95)


def _clamp_stats(base_stats: dict, item_type: str,
                  quality: str) -> tuple[dict, list[dict]]:
    """Apply quality multiplier, then clamp against LEGENDARY_CAP.

    Returns (final_stats, clamp_audit_entries).
    Each clamp entry: {stat, original, clamped, cap}.
    """
    mult = QUALITY_MULTIPLIERS.get(quality, 1.0)
    cap = LEGENDARY_CAP.get(item_type, {"primary": 999, "secondary": 999,
                                          "power_score": 999})
    clamp_audit: list[dict] = []
    final: dict = {}
    for k, v in (base_stats or {}).items():
        raw = int(round(v * mult))
        # Determine cap key
        if k == "power_score":
            cap_val = cap["power_score"]
        else:
            # Primary if any stat = base_stats max ignoring power_score
            base_max = max([base_stats.get(s, 0) for s in
                             ("strength", "agility", "intellect",
                              "endurance", "faith")] or [0])
            cap_val = cap["primary"] if v == base_max else cap["secondary"]
        if raw > cap_val:
            clamp_audit.append({"stat": k, "original": raw,
                                 "clamped": cap_val, "cap": cap_val})
            raw = cap_val
        final[k] = raw
    return final, clamp_audit


async def _emit_audit(event_type: str, actor_id: Optional[str],
                       guild_id: Optional[str], target_id: Optional[str],
                       metadata: dict) -> None:
    doc = {"id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_id": actor_id,
            "guild_id": guild_id,
            "target_id": target_id,
            "metadata": metadata,
            "created_at": _iso(_now())}
    try:
        await db.audit_log.insert_one(doc)
    except Exception as exc:
        logger.warning("audit insert %s: %s", event_type, exc)


async def _inventory_qty(guild_id: str, item_slug: str) -> int:
    """Return total quantity of a material/resource in guild inventory."""
    it = await db.items.find_one({"slug": item_slug}, {"_id": 0, "id": 1})
    if not it:
        return 0
    docs = await db.inventory_items.find(
        {"guild_id": guild_id, "item_id": it["id"]},
        {"_id": 0, "quantity": 1}).to_list(1000)
    return sum(int(d.get("quantity") or 0) for d in docs)


async def _consume_from_inventory(guild_id: str, item_slug: str,
                                    qty: int) -> None:
    """Consume qty units of a material/resource. Assumes availability
    was pre-validated by the caller; uses CAS decrement loop."""
    it = await db.items.find_one({"slug": item_slug}, {"_id": 0, "id": 1})
    if not it:
        raise HTTPException(400, f"item_slug_not_found:{item_slug}")
    remaining = qty
    while remaining > 0:
        row = await db.inventory_items.find_one(
            {"guild_id": guild_id, "item_id": it["id"],
             "quantity": {"$gt": 0}},
            sort=[("quantity", -1)])
        if not row:
            raise HTTPException(400,
                                f"insufficient_material:{item_slug}")
        take = min(int(row["quantity"]), remaining)
        r = await db.inventory_items.update_one(
            {"id": row["id"], "quantity": row["quantity"]},
            {"$inc": {"quantity": -take}})
        if r.modified_count:
            remaining -= take


async def _grant_legendary(guild_id: str, item_slug: str,
                             final_stats: dict, quality: str,
                             order_id: str) -> str:
    """Create a bound legendary instance in inventory (qty=1)."""
    it = await db.legendary_items_catalog.find_one(
        {"slug": item_slug}, {"_id": 0})
    if not it:
        raise HTTPException(500, f"legendary_catalog_missing:{item_slug}")
    # Ensure a mirror row exists in `items` collection (for equip/loot
    # compatibility) — insert-or-get pattern
    item_row = await db.items.find_one({"slug": item_slug},
                                         {"_id": 0, "id": 1})
    if not item_row:
        base_stats = it.get("base_stats", {})
        item_row_doc = {
            "id": str(uuid.uuid4()),
            "slug": item_slug,
            "name": it.get("name_it", item_slug),
            "item_type": it["item_type"],
            "rarity": "legendary",
            "is_tradeable": False,
            "is_bound": True,
            "bind_type": "on_pickup",
            "is_cosmetic": False,
            "affects_combat": True,
            "affects_economy": False,
            "can_be_sold_for_gold": False,
            "can_be_sold_for_real_money": False,
            "strength_bonus": int(base_stats.get("strength", 0)),
            "agility_bonus": int(base_stats.get("agility", 0)),
            "intellect_bonus": int(base_stats.get("intellect", 0)),
            "endurance_bonus": int(base_stats.get("endurance", 0)),
            "faith_bonus": int(base_stats.get("faith", 0)),
            "power_score": int(base_stats.get("power_score", 0)),
            "created_at": _iso(_now()),
        }
        try:
            await db.items.insert_one(item_row_doc)
        except Exception:
            pass
        item_row = await db.items.find_one({"slug": item_slug},
                                             {"_id": 0, "id": 1})
    inst_id = str(uuid.uuid4())
    inst = {
        "id": inst_id,
        "guild_id": guild_id,
        "item_id": item_row["id"],
        "item_slug": item_slug,
        "quantity": 1,
        "is_bound": True,
        "bound_to_guild_id": guild_id,
        "bound_at": _iso(_now()),
        "is_tradeable": False,
        "can_be_sold_for_gold": False,
        "legendary_quality": quality,
        "legendary_stats": final_stats,
        "source_craft_order_id": order_id,
        "created_at": _iso(_now()),
    }
    # Legendary instances live in their own collection (unique per craft)
    # to avoid clashing with `inventory_items` unique (guild_id, item_id)
    # index used for stackable materials. Frontend/equip layers can read
    # both collections in a UNION view.
    await db.legendary_item_instances.insert_one(inst)
    return inst_id


# ── Craft resolve (deterministic) ────────────────────────────────────
async def _resolve_order(order: dict) -> dict:
    """CAS-guarded resolver. Deterministic RNG on (guild_id, order_id).
    Emits audit + creates legendary instance if quality != None.
    Bumps pity counter."""
    now_iso = _iso(_now())
    # CAS: transition to resolving
    r = await db.legendary_forge_crafting_orders.find_one_and_update(
        {"id": order["id"], "status": "in_progress",
         "resolution_started_at": None},
        {"$set": {"resolution_started_at": now_iso}},
        return_document=True)
    if not r:
        # Another resolver already handled it
        cur = await db.legendary_forge_crafting_orders.find_one(
            {"id": order["id"]}, {"_id": 0})
        return cur or order
    order = r
    recipe = await db.legendary_recipe_catalog.find_one(
        {"slug": order["recipe_slug"]}, {"_id": 0})
    if not recipe:
        raise HTTPException(500, "recipe_missing_on_resolve")
    guild = await db.guilds.find_one({"id": order["guild_id"]},
                                       {"_id": 0, "level": 1})
    guild_level = int(guild.get("level", 1)) if guild else 1
    success_chance = _compute_success_chance(recipe, guild_level)
    rng = _rng_for(order["guild_id"], order["id"])
    success_roll = rng.randint(1, 100)
    success = success_roll <= success_chance
    quality: Optional[str] = None
    quality_roll: Optional[int] = None
    pity_applied = False
    inst_id: Optional[str] = None
    clamp_audit: list[dict] = []
    if success:
        quality_roll = rng.randint(1, 100)
        if quality_roll <= PERFEZIONATO_CHANCE:
            quality = "perfezionato"
        elif quality_roll <= PERFEZIONATO_CHANCE + IMPERFETTO_CHANCE:
            quality = "imperfetto"
        else:
            quality = "normale"
        # Pity: convert imperfetto -> normale if streak reached
        pity = await _get_pity(order["guild_id"])
        if (pity.get("pity_counter_since_perfezionato", 0) >= PITY_THRESHOLD
                and quality == "imperfetto"):
            quality = "normale"
            pity_applied = True
        # Create legendary instance with clamped stats
        lg = await db.legendary_items_catalog.find_one(
            {"slug": recipe["output_slug"]},
            {"_id": 0, "base_stats": 1, "item_type": 1})
        final_stats, clamp_audit = _clamp_stats(
            lg["base_stats"], lg["item_type"], quality)
        inst_id = await _grant_legendary(
            order["guild_id"], recipe["output_slug"],
            final_stats, quality, order["id"])
        await _bump_pity(order["guild_id"], quality)
        if clamp_audit:
            await _emit_audit("LEGENDARY_STAT_CLAMPED",
                               None, order["guild_id"], inst_id,
                               {"recipe_slug": recipe["slug"],
                                "quality": quality,
                                "clamps": clamp_audit})
    else:
        # Failed: still counts towards pity streak
        await _bump_pity(order["guild_id"], None)
    # Finalize order
    final_status = "completed" if success else "failed"
    await db.legendary_forge_crafting_orders.update_one(
        {"id": order["id"]},
        {"$set": {"status": final_status,
                  "result_item_instance_id": inst_id,
                  "result_quality": quality,
                  "success_roll": success_roll,
                  "quality_roll": quality_roll,
                  "pity_applied": pity_applied,
                  "resolved_at": now_iso,
                  "updated_at": now_iso}})
    await _emit_audit(
        "LEGENDARY_CRAFT_COMPLETED" if success else "LEGENDARY_CRAFT_FAILED",
        None, order["guild_id"], order["id"],
        {"recipe_slug": recipe["slug"], "quality": quality,
         "success_roll": success_roll, "quality_roll": quality_roll,
         "pity_applied": pity_applied,
         "result_item_instance_id": inst_id})
    return await db.legendary_forge_crafting_orders.find_one(
        {"id": order["id"]}, {"_id": 0})


async def _resolve_expired_for_guild(guild_id: str) -> int:
    now = _now()
    cur = db.legendary_forge_crafting_orders.find(
        {"guild_id": guild_id, "status": "in_progress",
         "completes_at": {"$lte": _iso(now)}}, {"_id": 0})
    resolved = 0
    async for o in cur:
        try:
            await _resolve_order(o)
            resolved += 1
        except Exception as exc:
            logger.warning("resolve_order %s: %s", o.get("id"), exc)
    return resolved


# ── Schemas ──────────────────────────────────────────────────────────
class _CraftReq(BaseModel):
    pass  # empty body; recipe_slug from path


# ── Public endpoints ─────────────────────────────────────────────────
def _pub_recipe(r: dict, computed_success: Optional[int] = None) -> dict:
    d = {k: r.get(k) for k in
          ("slug", "name_it", "name_en", "output_slug", "resources",
           "materials", "gold", "guild_level_required",
           "base_success_chance", "perfezionato_chance",
           "imperfetto_chance", "crafting_duration_seconds",
           "is_active")}
    d["normale_chance"] = 100 - PERFEZIONATO_CHANCE - IMPERFETTO_CHANCE
    if computed_success is not None:
        d["computed_success_chance"] = computed_success
    return d


@router.get("/catalog")
async def list_catalog(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    guild_level = int(guild.get("level", 1))
    if guild_level < MIN_GUILD_LEVEL:
        return {"access": False, "requirement": f"guild_level_{MIN_GUILD_LEVEL}",
                "recipes": []}
    docs = await db.legendary_recipe_catalog.find(
        {"is_active": True}, {"_id": 0}).sort("guild_level_required", 1).to_list(20)
    return {"access": True, "guild_level": guild_level,
            "recipes": [_pub_recipe(r, _compute_success_chance(r, guild_level))
                        for r in docs]}


@router.get("/catalog/{slug}")
async def recipe_detail(slug: str, user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    guild_level = int(guild.get("level", 1))
    r = await db.legendary_recipe_catalog.find_one(
        {"slug": slug, "is_active": True}, {"_id": 0})
    if not r:
        raise HTTPException(404, "recipe_not_found")
    computed_success = _compute_success_chance(r, guild_level)
    # Resource + material availability
    missing: list[dict] = []
    resources_status: list[dict] = []
    for res in r["resources"]:
        have = await _inventory_qty(guild["id"], res["slug"])
        resources_status.append({"slug": res["slug"],
                                   "required": res["qty"], "owned": have})
        if have < res["qty"]:
            missing.append({"type": "resource", "slug": res["slug"],
                             "required": res["qty"], "owned": have})
    materials_status: list[dict] = []
    for mat in r["materials"]:
        have = await _inventory_qty(guild["id"], mat["slug"])
        materials_status.append({"slug": mat["slug"],
                                   "required": mat["qty"], "owned": have})
        if have < mat["qty"]:
            missing.append({"type": "material", "slug": mat["slug"],
                             "required": mat["qty"], "owned": have})
    gold_have = int(guild.get("gold", 0))
    if gold_have < r["gold"]:
        missing.append({"type": "gold", "required": r["gold"],
                         "owned": gold_have})
    if guild_level < r["guild_level_required"]:
        missing.append({"type": "guild_level",
                         "required": r["guild_level_required"],
                         "owned": guild_level})
    pity = await _get_pity(guild["id"])
    return {**_pub_recipe(r, computed_success),
            "resources_status": resources_status,
            "materials_status": materials_status,
            "gold_status": {"required": r["gold"], "owned": gold_have},
            "pity_status": {
                "counter": pity["pity_counter_since_perfezionato"],
                "threshold": PITY_THRESHOLD,
                "next_guaranteed_no_imperfetto":
                    pity["pity_counter_since_perfezionato"] >= PITY_THRESHOLD,
            },
            "missing_requirements": missing,
            "can_craft": len(missing) == 0}


@router.post("/craft/{recipe_slug}")
async def start_craft(recipe_slug: str,
                       user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    r = await db.legendary_recipe_catalog.find_one(
        {"slug": recipe_slug, "is_active": True}, {"_id": 0})
    if not r:
        raise HTTPException(404, "recipe_not_found")
    guild_level = int(guild.get("level", 1))
    if guild_level < r["guild_level_required"]:
        raise HTTPException(403, f"guild_level_below_required:"
                                    f"{r['guild_level_required']}")
    # Check resources
    for res in r["resources"]:
        have = await _inventory_qty(guild["id"], res["slug"])
        if have < res["qty"]:
            raise HTTPException(400,
                                f"insufficient_resource:{res['slug']}:"
                                f"required={res['qty']}:owned={have}")
    for mat in r["materials"]:
        have = await _inventory_qty(guild["id"], mat["slug"])
        if have < mat["qty"]:
            raise HTTPException(400,
                                f"insufficient_material:{mat['slug']}:"
                                f"required={mat['qty']}:owned={have}")
    if int(guild.get("gold", 0)) < r["gold"]:
        raise HTTPException(400, f"insufficient_gold:required={r['gold']}")
    # CAS-decrement gold
    gr = await db.guilds.update_one(
        {"id": guild["id"], "gold": {"$gte": r["gold"]}},
        {"$inc": {"gold": -r["gold"]}})
    if not gr.modified_count:
        raise HTTPException(400, "gold_race_condition")
    # Consume resources + materials
    for res in r["resources"]:
        await _consume_from_inventory(guild["id"], res["slug"], res["qty"])
    for mat in r["materials"]:
        await _consume_from_inventory(guild["id"], mat["slug"], mat["qty"])
    # Create order
    now = _now()
    duration = int(r.get("crafting_duration_seconds",
                           CRAFT_DURATION_SECONDS))
    order = {"id": str(uuid.uuid4()),
              "guild_id": guild["id"],
              "recipe_slug": recipe_slug,
              "status": "in_progress",
              "started_at": _iso(now),
              "completes_at": _iso(now + timedelta(seconds=duration)),
              "duration_seconds": duration,
              "resources_consumed": r["resources"],
              "materials_consumed": r["materials"],
              "gold_consumed": r["gold"],
              "result_item_instance_id": None,
              "result_quality": None,
              "success_roll": None,
              "quality_roll": None,
              "pity_applied": False,
              "resolution_started_at": None,
              "resolved_at": None,
              "created_at": _iso(now),
              "updated_at": _iso(now)}
    await db.legendary_forge_crafting_orders.insert_one(order)
    await _emit_audit("LEGENDARY_CRAFT_STARTED", user["id"],
                       guild["id"], order["id"],
                       {"recipe_slug": recipe_slug,
                        "gold_consumed": r["gold"],
                        "computed_success_chance":
                            _compute_success_chance(r, guild_level)})
    order.pop("_id", None)
    return {"status": "ok", "order": order,
            "preview_probabilities": {
                "success_chance":
                    _compute_success_chance(r, guild_level),
                "perfezionato": PERFEZIONATO_CHANCE,
                "imperfetto": IMPERFETTO_CHANCE,
                "normale": 100 - PERFEZIONATO_CHANCE - IMPERFETTO_CHANCE}}


@router.get("/orders/mine")
async def orders_mine(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    await _resolve_expired_for_guild(guild["id"])
    in_progress = await db.legendary_forge_crafting_orders.find(
        {"guild_id": guild["id"], "status": "in_progress"},
        {"_id": 0}).sort("started_at", -1).to_list(20)
    recent = await db.legendary_forge_crafting_orders.find(
        {"guild_id": guild["id"], "status": {"$in": ["completed", "failed"]}},
        {"_id": 0}).sort("resolved_at", -1).to_list(20)
    return {"in_progress": in_progress, "recent": recent}


@router.get("/orders/{order_id}")
async def order_detail(order_id: str,
                        user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    o = await db.legendary_forge_crafting_orders.find_one(
        {"id": order_id, "guild_id": guild["id"]}, {"_id": 0})
    if not o:
        raise HTTPException(404, "order_not_found")
    # On-visit resolve if expired
    if (o["status"] == "in_progress"
            and o["completes_at"] <= _iso(_now())):
        o = await _resolve_order(o)
    return {"order": o}


# ── Admin endpoints ──────────────────────────────────────────────────
@admin_router.patch("/recipes/{slug}")
async def admin_toggle_recipe(slug: str, is_active: bool = True,
                                admin: dict = Depends(get_admin_user)):
    r = await db.legendary_recipe_catalog.find_one({"slug": slug},
                                                     {"_id": 0, "slug": 1})
    if not r:
        raise HTTPException(404, "recipe_not_found")
    await db.legendary_recipe_catalog.update_one(
        {"slug": slug},
        {"$set": {"is_active": bool(is_active),
                  "updated_at": _iso(_now())}})
    await _emit_audit("LEGENDARY_RECIPE_TOGGLED", admin.get("id"),
                       None, slug, {"is_active": bool(is_active)})
    return {"status": "ok", "slug": slug, "is_active": bool(is_active)}


@admin_router.get("/stats")
async def admin_stats(window_days: int = 7,
                       admin: dict = Depends(get_admin_user)):
    window_days = max(1, min(int(window_days), 30))
    since_iso = _iso(_now() - timedelta(days=window_days))
    pipe = [
        {"$match": {"created_at": {"$gte": since_iso}}},
        {"$group": {"_id": {"recipe": "$recipe_slug",
                              "status": "$status",
                              "quality": "$result_quality"},
                     "count": {"$sum": 1},
                     "pity_hits": {"$sum": {"$cond": ["$pity_applied", 1, 0]}}}},
    ]
    groups = await db.legendary_forge_crafting_orders.aggregate(
        pipe).to_list(500)
    return {"window_days": window_days, "groups": groups}


@admin_router.post("/dev/force-complete/{order_id}")
async def admin_dev_force_complete(order_id: str,
                                     admin: dict = Depends(get_admin_user)):
    if _is_production():
        raise HTTPException(403, "disabled_in_production")
    o = await db.legendary_forge_crafting_orders.find_one(
        {"id": order_id}, {"_id": 0})
    if not o:
        raise HTTPException(404, "order_not_found")
    if o["status"] != "in_progress":
        return {"status": "already_resolved", "order": o}
    past = _iso(_now() - timedelta(seconds=1))
    await db.legendary_forge_crafting_orders.update_one(
        {"id": order_id, "status": "in_progress"},
        {"$set": {"completes_at": past, "updated_at": past}})
    o["completes_at"] = past
    resolved = await _resolve_order(o)
    return {"status": "resolved", "order": resolved}


__all__ = [
    "router", "admin_router",
    "seed_legendary_forge_catalog", "ensure_indexes",
    "_resolve_order", "_resolve_expired_for_guild",
    "_rng_for", "_compute_success_chance", "_clamp_stats",
    "EPIC_STAT_BASELINE", "LEGENDARY_CAP", "RECIPES",
    "LEGENDARY_ITEMS", "PERFEZIONATO_CHANCE", "IMPERFETTO_CHANCE",
    "PITY_THRESHOLD", "MIN_GUILD_LEVEL",
]
