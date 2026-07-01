"""ROUND 16.3 Phase 6 — Guild Specialization V0 (flavor + narrative).

V0 = purely flavor + narrative + hook categories for future Phase 6.5+.
Zero numerical bonuses in V0. Frontend uses `badge_color` + `icon_slug`
+ `description` to render.

Rules:
- 1 active choice per guild (previous becomes `archived` on reset)
- Guild level gate ≥ 8
- First choice is free
- Reset cost: 200_000 gold + 3× frammento_di_ergolat
- Reset cooldown: 30 days
- No hard delete: archived rows preserved for audit trail
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.guild_specialization")

router = APIRouter(prefix="/api/guild-specialization",
                    tags=["guild-specialization"])
admin_router = APIRouter(prefix="/api/admin/guild-specialization",
                          tags=["admin", "guild-specialization"])

MIN_GUILD_LEVEL = 8
RESET_COOLDOWN_DAYS = 30
RESET_GOLD_COST = 200_000
RESET_MATERIAL_SLUG = "frammento_di_ergolat"
RESET_MATERIAL_QTY = 3


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ── Seed catalog — 6 specializations ────────────────────────────────
SPECIALIZATIONS = [
    {"slug": "incursion", "name_it": "Gilda di Incursioni",
      "name_en": "Incursion Guild",
      "description_it": ("Specializzata in raid e world boss. I team di questa "
                          "gilda eccellono in scontri prolungati e coordinati."),
      "description_en": "Specialized in raids and world boss encounters.",
      "hook_categories": ["world_boss", "raid"],
      "badge_color": "amber", "icon_slug": "crossed_swords", "sort_order": 1},
    {"slug": "production", "name_it": "Gilda di Produzione",
      "name_en": "Production Guild",
      "description_it": ("Maestria nel crafting e nella forgia leggendaria. "
                          "Le opere di questa gilda sono rinomate."),
      "description_en": "Crafting and legendary forging mastery.",
      "hook_categories": ["legendary_forge", "crafting"],
      "badge_color": "orange", "icon_slug": "anvil", "sort_order": 2},
    {"slug": "merchant", "name_it": "Gilda Mercantile",
      "name_en": "Merchant Guild",
      "description_it": ("Ottimizzata per mercato e commercio. La reputazione "
                          "commerciale è impareggiabile."),
      "description_en": "Optimized for market and trade.",
      "hook_categories": ["market", "auction"],
      "badge_color": "emerald", "icon_slug": "scales", "sort_order": 3},
    {"slug": "exploration", "name_it": "Gilda di Esplorazione",
      "name_en": "Exploration Guild",
      "description_it": ("Focalizzata su risorse continentali e scoperta. "
                          "I suoi cartografi mappano l'ignoto."),
      "description_en": "Focused on continental resources and discovery.",
      "hook_categories": ["resource_gathering", "continent"],
      "badge_color": "sky", "icon_slug": "compass", "sort_order": 4},
    {"slug": "military", "name_it": "Gilda Militare",
      "name_en": "Military Guild",
      "description_it": ("Esperta in PvP e difesa. Le sue tattiche sono "
                          "temute sull'intero continente."),
      "description_en": "PvP and defense experts.",
      "hook_categories": ["pvp", "defense"],
      "badge_color": "red", "icon_slug": "shield", "sort_order": 5},
    {"slug": "arcane_research", "name_it": "Gilda di Ricerca Arcana",
      "name_en": "Arcane Research Guild",
      "description_it": ("Dedicata a magia, tecnologia di Arfus e artefatti. "
                          "I loro segreti riscrivono la realtà."),
      "description_en": "Dedicated to magic, Arfus tech and artifacts.",
      "hook_categories": ["arfus_forge", "arcane"],
      "badge_color": "violet", "icon_slug": "book", "sort_order": 6},
]


async def seed_guild_specialization_catalog() -> dict:
    inserted = 0
    updated = 0
    for spec in SPECIALIZATIONS:
        doc = {**spec, "is_active": True, "updated_at": _iso(_now())}
        r = await db.guild_specialization_catalog.update_one(
            {"slug": spec["slug"]},
            {"$set": doc,
             "$setOnInsert": {"id": str(uuid.uuid4()),
                              "created_at": _iso(_now())}},
            upsert=True)
        if r.upserted_id:
            inserted += 1
        elif r.modified_count:
            updated += 1
    return {"inserted": inserted, "updated": updated,
            "total": len(SPECIALIZATIONS)}


async def ensure_indexes():
    try:
        await db.guild_specialization_catalog.create_index("slug", unique=True)
    except Exception as exc:
        logger.debug("spec catalog idx: %s", exc)
    try:
        # 1 active per guild — enforced at query time (partial-unique semantic)
        await db.guild_specialization_choice.create_index(
            [("guild_id", 1), ("status", 1)])
    except Exception as exc:
        logger.debug("spec choice idx: %s", exc)


async def _emit_audit(event_type: str, actor_id: Optional[str],
                       guild_id: Optional[str], target_id: Optional[str],
                       metadata: dict) -> None:
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_guild_id": guild_id,
            "target_id": target_id,
            "metadata": metadata,
            "created_at": _iso(_now()),
        })
    except Exception as exc:
        logger.warning("audit %s: %s", event_type, exc)


async def _get_active_choice(guild_id: str) -> Optional[dict]:
    return await db.guild_specialization_choice.find_one(
        {"guild_id": guild_id, "status": "active"}, {"_id": 0})


async def _inventory_qty(guild_id: str, item_slug: str) -> int:
    it = await db.items.find_one({"slug": item_slug}, {"_id": 0, "id": 1})
    if not it:
        return 0
    docs = await db.inventory_items.find(
        {"guild_id": guild_id, "item_id": it["id"]},
        {"_id": 0, "quantity": 1}).to_list(1000)
    return sum(int(d.get("quantity") or 0) for d in docs)


async def _consume_from_inventory(guild_id: str, item_slug: str,
                                    qty: int) -> None:
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
            raise HTTPException(400, f"insufficient_material:{item_slug}")
        take = min(int(row["quantity"]), remaining)
        r = await db.inventory_items.update_one(
            {"id": row["id"], "quantity": row["quantity"]},
            {"$inc": {"quantity": -take}})
        if r.modified_count:
            remaining -= take


def _spec_public(spec: dict) -> dict:
    return {k: spec.get(k) for k in (
        "slug", "name_it", "name_en", "description_it", "description_en",
        "hook_categories", "badge_color", "icon_slug", "sort_order",
        "is_active",
    )}


# ── Public routes ────────────────────────────────────────────────────
@router.get("/catalog")
async def list_catalog(user: dict = Depends(get_current_user)):
    docs = await db.guild_specialization_catalog.find(
        {"is_active": True}, {"_id": 0}).sort("sort_order", 1).to_list(20)
    return {"specializations": [_spec_public(d) for d in docs]}


@router.get("/mine")
async def mine_specialization(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    choice = await _get_active_choice(guild["id"])
    if not choice:
        return {"active_choice": None,
                "can_choose": int(guild.get("level", 1)) >= MIN_GUILD_LEVEL,
                "guild_level": guild.get("level", 1),
                "min_guild_level": MIN_GUILD_LEVEL}
    spec = await db.guild_specialization_catalog.find_one(
        {"slug": choice["specialization_slug"]}, {"_id": 0})
    return {"active_choice": choice,
            "specialization": _spec_public(spec) if spec else None,
            "guild_level": guild.get("level", 1),
            "min_guild_level": MIN_GUILD_LEVEL,
            "reset_cost_gold": RESET_GOLD_COST,
            "reset_cost_material":
                {"slug": RESET_MATERIAL_SLUG, "qty": RESET_MATERIAL_QTY}}


async def _validate_and_lookup_spec(slug: str) -> dict:
    spec = await db.guild_specialization_catalog.find_one(
        {"slug": slug, "is_active": True}, {"_id": 0})
    if not spec:
        raise HTTPException(404, "specialization_not_found")
    return spec


@router.post("/choose/{slug}")
async def choose_specialization(slug: str,
                                  user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    if int(guild.get("level", 1)) < MIN_GUILD_LEVEL:
        raise HTTPException(403,
                            f"guild_level_below_required:{MIN_GUILD_LEVEL}")
    if await _get_active_choice(guild["id"]):
        raise HTTPException(409, "already_has_active_choice")
    await _validate_and_lookup_spec(slug)
    now = _now()
    choice = {"id": str(uuid.uuid4()),
                "guild_id": guild["id"],
                "specialization_slug": slug,
                "chosen_at": _iso(now),
                "last_reset_at": None,
                "next_reset_available_at":
                    _iso(now + timedelta(days=RESET_COOLDOWN_DAYS)),
                "reset_count": 0,
                "status": "active",
                "created_at": _iso(now),
                "updated_at": _iso(now)}
    await db.guild_specialization_choice.insert_one(choice)
    await _emit_audit("GUILD_SPECIALIZATION_CHOSEN", user["id"], guild["id"],
                       choice["id"],
                       {"specialization_slug": slug, "is_first_choice": True})
    choice.pop("_id", None)
    return {"status": "ok", "choice": choice}


@router.post("/reset/{new_slug}")
async def reset_specialization(new_slug: str,
                                 user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    if int(guild.get("level", 1)) < MIN_GUILD_LEVEL:
        raise HTTPException(403,
                            f"guild_level_below_required:{MIN_GUILD_LEVEL}")
    active = await _get_active_choice(guild["id"])
    if not active:
        raise HTTPException(404, "no_active_choice_to_reset")
    now = _now()
    if active.get("next_reset_available_at") and \
        _iso(now) < active["next_reset_available_at"]:
        raise HTTPException(409,
                            f"reset_cooldown_active:until="
                            f"{active['next_reset_available_at']}")
    await _validate_and_lookup_spec(new_slug)
    # Check funds
    if int(guild.get("gold", 0)) < RESET_GOLD_COST:
        raise HTTPException(402,
                            f"insufficient_gold:required={RESET_GOLD_COST}")
    mat_have = await _inventory_qty(guild["id"], RESET_MATERIAL_SLUG)
    if mat_have < RESET_MATERIAL_QTY:
        raise HTTPException(402,
                            f"insufficient_material:{RESET_MATERIAL_SLUG}:"
                            f"required={RESET_MATERIAL_QTY}:owned={mat_have}")
    # CAS gold debit
    gr = await db.guilds.update_one(
        {"id": guild["id"], "gold": {"$gte": RESET_GOLD_COST}},
        {"$inc": {"gold": -RESET_GOLD_COST}})
    if not gr.modified_count:
        raise HTTPException(400, "gold_race_condition")
    # Consume material
    await _consume_from_inventory(guild["id"], RESET_MATERIAL_SLUG,
                                    RESET_MATERIAL_QTY)
    # Archive old choice
    await db.guild_specialization_choice.update_one(
        {"id": active["id"]},
        {"$set": {"status": "archived",
                    "last_reset_at": _iso(now),
                    "updated_at": _iso(now)}})
    # Insert new active choice
    new_choice = {"id": str(uuid.uuid4()),
                    "guild_id": guild["id"],
                    "specialization_slug": new_slug,
                    "chosen_at": _iso(now),
                    "last_reset_at": _iso(now),
                    "next_reset_available_at":
                        _iso(now + timedelta(days=RESET_COOLDOWN_DAYS)),
                    "reset_count": int(active.get("reset_count") or 0) + 1,
                    "status": "active",
                    "created_at": _iso(now),
                    "updated_at": _iso(now)}
    await db.guild_specialization_choice.insert_one(new_choice)
    await _emit_audit("GUILD_SPECIALIZATION_RESET", user["id"], guild["id"],
                       new_choice["id"],
                       {"old_slug": active["specialization_slug"],
                        "new_slug": new_slug,
                        "gold_paid": RESET_GOLD_COST,
                        "material_paid":
                            {"slug": RESET_MATERIAL_SLUG,
                                "qty": RESET_MATERIAL_QTY},
                        "reset_count": new_choice["reset_count"]})
    new_choice.pop("_id", None)
    return {"status": "ok", "choice": new_choice,
            "archived_choice_id": active["id"]}


# ── Admin routes ─────────────────────────────────────────────────────
@admin_router.patch("/catalog/{slug}")
async def admin_toggle_catalog(slug: str, is_active: bool = Query(True),
                                 admin: dict = Depends(get_admin_user)):
    doc = await db.guild_specialization_catalog.find_one({"slug": slug},
                                                            {"_id": 0})
    if not doc:
        raise HTTPException(404, "specialization_not_found")
    await db.guild_specialization_catalog.update_one(
        {"slug": slug},
        {"$set": {"is_active": bool(is_active),
                    "updated_at": _iso(_now())}})
    await _emit_audit("GUILD_SPECIALIZATION_CATALOG_TOGGLED", admin["id"],
                       None, slug, {"is_active": bool(is_active)})
    return {"status": "ok", "slug": slug, "is_active": bool(is_active)}


@admin_router.get("/stats")
async def admin_stats(admin: dict = Depends(get_admin_user)):
    pipe = [{"$match": {"status": "active"}},
             {"$group": {"_id": "$specialization_slug",
                          "count": {"$sum": 1}}}]
    dist = await db.guild_specialization_choice.aggregate(pipe).to_list(20)
    total_active = await db.guild_specialization_choice.count_documents(
        {"status": "active"})
    total_archived = await db.guild_specialization_choice.count_documents(
        {"status": "archived"})
    return {"distribution": dist,
            "total_active": total_active,
            "total_archived": total_archived}


__all__ = ["router", "admin_router",
             "seed_guild_specialization_catalog", "ensure_indexes",
             "SPECIALIZATIONS", "MIN_GUILD_LEVEL",
             "RESET_COOLDOWN_DAYS", "RESET_GOLD_COST",
             "RESET_MATERIAL_SLUG", "RESET_MATERIAL_QTY"]
