"""ROUND 16.3 Phase 5B — Arfus Forge (guild passive technologies).

Compact single-file module (mirroring app/legendary_forge/ pattern):
- 10 technologies (one per category) — no stack same-category
- Research orders with CAS + on-visit resolve (no scheduler)
- Max 5 active technologies per guild (enforced server-side)
- Category caps clamp (safety net) — enforced at seed time + runtime
- Applier: `get_active_bonuses_for_guild(guild_id) -> {category: pct}`
- Chronicle enhancement helper: emits lowercase `legendary_perfezionato`
  audit event (reused by chronicle service for public feed)
- Admin: toggle tech, stats, dev-force-complete (gated APP_ENV)
- Backward-compat: if a guild has no active tech, all bonuses = 0
  and downstream calculations are numerically IDENTICAL to pre-5B.

Guild level gate: research visible only to guild.level >= 6.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.arfus_forge")

router = APIRouter(prefix="/api/arfus-forge", tags=["arfus-forge"])
admin_router = APIRouter(prefix="/api/admin/arfus-forge",
                          tags=["admin", "arfus-forge"])

# ── Constants ────────────────────────────────────────────────────────
MIN_GUILD_LEVEL = 6
MAX_ACTIVE_TECHS = 5
RESEARCH_DURATION_SECONDS = 180  # 3 min V1 (fast for tests + validation)

# Category caps — safety net against future stacked configs. With
# `no-stack-same-category + max_5_active` this is unreachable in V1
# (single tech per category), but we clamp at runtime anyway.
CATEGORY_CAPS = {
    "combat_damage":         30,
    "combat_healing":        30,
    "combat_defense":        30,
    "counter_effectiveness": 30,
    "exploration_luck":      15,   # conservative: impacts drop-rate
    "team_morale":           30,
    "leader_experience":     20,   # gentler on XP curve
    "arcane_knowledge":      30,
    "iron_will":             30,
    "forge_efficiency":      10,   # anti-drift on legendary balance
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _is_production() -> bool:
    return (os.environ.get("APP_ENV") or "development").lower() == "production"


# ── Technology catalog (10 techs, one per category) ─────────────────
TECHNOLOGIES = [
    {
        "slug": "via_del_ferro",
        "name_it": "Via del Ferro", "name_en": "Path of Iron",
        "category": "combat_damage",
        "description_it": ("Le tecniche di combattimento tramandate da Arfus "
                            "aumentano il danno inflitto dai team nelle missioni."),
        "description_en": ("Combat techniques passed down by Arfus increase "
                            "team damage in missions."),
        "effect_type": "combat_damage_pct", "effect_value": 5,
        "applies_to": ["expedition", "raid", "world_boss"],
        "input_resources": [
            {"slug": "cristallo_di_ambash", "qty": 1},
            {"slug": "osso_di_irthe", "qty": 1},
        ],
        "input_materials": [],
        "input_gold": 15000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 6, "prerequisite_technologies": [],
        "sort_order": 1,
    },
    {
        "slug": "mano_del_guaritore",
        "name_it": "Mano del Guaritore", "name_en": "Healer's Hand",
        "category": "combat_healing",
        "description_it": ("Aumenta l'efficacia di cure e recupero morale "
                            "dei team durante le spedizioni."),
        "description_en": ("Increases healing and morale recovery effectiveness."),
        "effect_type": "combat_healing_pct", "effect_value": 5,
        "applies_to": ["expedition", "raid"],
        "input_resources": [
            {"slug": "seme_di_nathos", "qty": 2},
            {"slug": "linfa_di_soe", "qty": 1},
        ],
        "input_materials": [],
        "input_gold": 15000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 6, "prerequisite_technologies": [],
        "sort_order": 2,
    },
    {
        "slug": "pelle_di_pietra",
        "name_it": "Pelle di Pietra", "name_en": "Stone Skin",
        "category": "combat_defense",
        "description_it": ("Rafforza la resistenza fisica e la stamina "
                            "degli avventurieri in battaglia."),
        "description_en": ("Boosts physical resistance and stamina."),
        "effect_type": "combat_defense_pct", "effect_value": 6,
        "applies_to": ["expedition", "raid", "world_boss"],
        "input_resources": [
            {"slug": "frammento_di_ergolat", "qty": 1},
            {"slug": "sigillo_di_aveol", "qty": 1},
        ],
        "input_materials": [],
        "input_gold": 20000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 7, "prerequisite_technologies": [],
        "sort_order": 3,
    },
    {
        "slug": "arte_del_contrasto",
        "name_it": "Arte del Contrasto", "name_en": "Art of Counter",
        "category": "counter_effectiveness",
        "description_it": ("Migliora l'efficacia dei counter-tag contro "
                            "minacce ed elementi nemici."),
        "description_en": ("Improves counter-tag effectiveness."),
        "effect_type": "counter_effectiveness_pct", "effect_value": 6,
        "applies_to": ["expedition", "raid", "world_boss"],
        "input_resources": [
            {"slug": "cristallo_di_ambash", "qty": 1},
            {"slug": "cenere_di_velur", "qty": 1},
        ],
        "input_materials": [],
        "input_gold": 20000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 7, "prerequisite_technologies": [],
        "sort_order": 4,
    },
    {
        "slug": "occhio_del_cacciatore",
        "name_it": "Occhio del Cacciatore", "name_en": "Hunter's Eye",
        "category": "exploration_luck",
        "description_it": ("Aumenta la probabilità di ottenere risorse "
                            "continentali dalle spedizioni di raccolta."),
        "description_en": ("Increases continental resource drop rate."),
        "effect_type": "exploration_luck_pct", "effect_value": 3,
        "applies_to": ["resource_gathering"],
        "input_resources": [
            {"slug": "nucleo_di_efreto", "qty": 1},
            {"slug": "seme_di_nathos", "qty": 1},
        ],
        "input_materials": [],
        "input_gold": 25000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 7, "prerequisite_technologies": [],
        "sort_order": 5,
    },
    {
        "slug": "spirito_del_guerriero",
        "name_it": "Spirito del Guerriero", "name_en": "Warrior's Spirit",
        "category": "team_morale",
        "description_it": ("Innalza il morale iniziale dei team in missione, "
                            "riducendo il rischio di panico."),
        "description_en": ("Raises initial team morale in missions."),
        "effect_type": "team_morale_pct", "effect_value": 8,
        "applies_to": ["expedition", "raid"],
        "input_resources": [
            {"slug": "osso_di_irthe", "qty": 1},
            {"slug": "cenere_di_velur", "qty": 2},
        ],
        "input_materials": [],
        "input_gold": 20000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 7, "prerequisite_technologies": [],
        "sort_order": 6,
    },
    {
        "slug": "saggezza_del_mentore",
        "name_it": "Saggezza del Mentore", "name_en": "Mentor's Wisdom",
        "category": "leader_experience",
        "description_it": ("Gli avventurieri guadagnano più esperienza "
                            "da spedizioni, raid e boss."),
        "description_en": ("Adventurers gain more XP from missions."),
        "effect_type": "leader_experience_pct", "effect_value": 4,
        "applies_to": ["expedition", "raid", "world_boss"],
        "input_resources": [
            {"slug": "seme_di_nathos", "qty": 1},
            {"slug": "sigillo_di_aveol", "qty": 1},
        ],
        "input_materials": [],
        "input_gold": 25000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 8, "prerequisite_technologies": [],
        "sort_order": 7,
    },
    {
        "slug": "conoscenza_arcana",
        "name_it": "Conoscenza Arcana", "name_en": "Arcane Knowledge",
        "category": "arcane_knowledge",
        "description_it": ("Aumenta la probabilità di successo delle "
                            "forgiature leggendarie."),
        "description_en": ("Increases legendary crafting success chance."),
        "effect_type": "arcane_knowledge_pct", "effect_value": 5,
        "applies_to": ["legendary_forge"],
        "input_resources": [
            {"slug": "cristallo_di_ambash", "qty": 2},
        ],
        "input_materials": [
            {"slug": "greater_arcane_dust", "qty": 5},
        ],
        "input_gold": 30000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 8, "prerequisite_technologies": [],
        "sort_order": 8,
    },
    {
        "slug": "perseveranza",
        "name_it": "Perseveranza", "name_en": "Iron Will",
        "category": "iron_will",
        "description_it": ("Il team resiste meglio ai fallimenti e "
                            "recupera morale più rapidamente."),
        "description_en": ("Team resists failures and recovers morale faster."),
        "effect_type": "iron_will_pct", "effect_value": 7,
        "applies_to": ["expedition", "raid"],
        "input_resources": [
            {"slug": "frammento_di_ergolat", "qty": 1},
        ],
        "input_materials": [
            {"slug": "iron_shard", "qty": 5},
        ],
        "input_gold": 20000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 7, "prerequisite_technologies": [],
        "sort_order": 9,
    },
    {
        "slug": "via_del_forgiatore",
        "name_it": "Via del Forgiatore", "name_en": "Forger's Path",
        "category": "forge_efficiency",
        "description_it": ("Aumenta la probabilità di ottenere un item "
                            "leggendario perfezionato."),
        "description_en": ("Increases legendary perfezionato chance."),
        "effect_type": "forge_efficiency_pct", "effect_value": 3,
        "applies_to": ["legendary_forge"],
        "input_resources": [
            {"slug": "sigillo_di_aveol", "qty": 1},
        ],
        "input_materials": [
            {"slug": "dragon_essence", "qty": 3},
        ],
        "input_gold": 40000, "research_duration_seconds": RESEARCH_DURATION_SECONDS,
        "guild_level_required": 9, "prerequisite_technologies": [],
        "sort_order": 10,
    },
]


# ── Seed ─────────────────────────────────────────────────────────────
def _validate_seed_cap():
    """Raise ValueError if any tech.effect_value > CATEGORY_CAPS[category].
    Forces explicit cap update if someone bumps effect_value."""
    for t in TECHNOLOGIES:
        cat = t["category"]
        if cat not in CATEGORY_CAPS:
            raise ValueError(f"arfus.seed_bad_category:{cat}")
        if t["effect_value"] > CATEGORY_CAPS[cat]:
            raise ValueError(
                f"arfus.seed_effect_exceeds_cap:{t['slug']}:"
                f"{t['effect_value']}>{CATEGORY_CAPS[cat]}")


async def seed_arfus_forge_catalog() -> dict:
    """Idempotent seed of 10 technologies. Validates cap guardrail."""
    _validate_seed_cap()
    inserted = 0
    updated = 0
    for tech in TECHNOLOGIES:
        doc = {**tech, "is_active": True, "updated_at": _iso(_now())}
        res = await db.arfus_technology_catalog.update_one(
            {"slug": tech["slug"]},
            {"$set": doc,
             "$setOnInsert": {"id": str(uuid.uuid4()),
                              "created_at": _iso(_now())}},
            upsert=True,
        )
        if res.upserted_id:
            inserted += 1
        elif res.modified_count:
            updated += 1
    return {"inserted": inserted, "updated": updated,
            "total": len(TECHNOLOGIES)}


async def ensure_indexes():
    try:
        await db.arfus_technology_catalog.create_index("slug", unique=True)
    except Exception as exc:
        logger.debug("arfus catalog slug idx: %s", exc)
    try:
        await db.guild_arfus_research_orders.create_index([
            ("guild_id", 1), ("status", 1)])
    except Exception as exc:
        logger.debug("arfus orders idx: %s", exc)
    try:
        await db.guild_arfus_technologies.create_index(
            [("guild_id", 1), ("technology_slug", 1)], unique=True)
    except Exception as exc:
        logger.debug("arfus techs idx: %s", exc)


# ── Audit ────────────────────────────────────────────────────────────
async def _emit_audit(event_type: str, actor_id: Optional[str],
                       guild_id: Optional[str], target_id: Optional[str],
                       metadata: dict) -> None:
    doc = {"id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_guild_id": guild_id,
            "target_id": target_id,
            "metadata": metadata,
            "created_at": _iso(_now())}
    try:
        await db.audit_log.insert_one(doc)
    except Exception as exc:
        logger.warning("audit insert %s: %s", event_type, exc)


# ── Applier (public API used by other services) ─────────────────────
async def get_active_bonuses_for_guild(guild_id: str) -> dict:
    """Return {category: bonus_pct} for all active technologies of a guild.
    Applies CATEGORY_CAPS as clamp. Returns empty dict if no tech active
    (backward-compat: downstream calculations unchanged if empty).
    """
    if not guild_id:
        return {}
    active = await db.guild_arfus_technologies.find(
        {"guild_id": guild_id, "is_active": True}, {"_id": 0}).to_list(50)
    if not active:
        return {}
    slugs = [t["technology_slug"] for t in active]
    catalog = await db.arfus_technology_catalog.find(
        {"slug": {"$in": slugs}, "is_active": True}, {"_id": 0}).to_list(50)
    by_slug = {c["slug"]: c for c in catalog}
    totals: dict[str, int] = {}
    for t in active:
        cat_doc = by_slug.get(t["technology_slug"])
        if not cat_doc:
            continue
        cat = cat_doc["category"]
        val = int(cat_doc["effect_value"])
        totals[cat] = totals.get(cat, 0) + val
    # Clamp per category cap
    return {cat: min(val, CATEGORY_CAPS.get(cat, val))
            for cat, val in totals.items()}


async def bonus_pct(guild_id: str, category: str) -> int:
    """Convenience helper: return single category bonus_pct (0 if none)."""
    b = await get_active_bonuses_for_guild(guild_id)
    return int(b.get(category, 0))


# ── Public routes ────────────────────────────────────────────────────
def _pub_tech(tech: dict, active_state: Optional[dict] = None,
               unlocked_state: Optional[dict] = None) -> dict:
    d = {k: tech.get(k) for k in
          ("slug", "name_it", "name_en", "category", "description_it",
           "description_en", "effect_type", "effect_value", "applies_to",
           "input_resources", "input_materials", "input_gold",
           "research_duration_seconds", "guild_level_required",
           "prerequisite_technologies", "is_active", "sort_order")}
    d["category_cap"] = CATEGORY_CAPS.get(tech.get("category"), 0)
    if unlocked_state is not None:
        d["is_unlocked"] = True
        d["is_active_for_guild"] = bool(unlocked_state.get("is_active"))
        d["unlocked_at"] = unlocked_state.get("unlocked_at")
    else:
        d["is_unlocked"] = False
        d["is_active_for_guild"] = False
    return d


async def _guild_unlocked_map(guild_id: str) -> dict:
    docs = await db.guild_arfus_technologies.find(
        {"guild_id": guild_id}, {"_id": 0}).to_list(50)
    return {d["technology_slug"]: d for d in docs}


@router.get("/catalog")
async def list_catalog(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    guild_level = int(guild.get("level", 1))
    if guild_level < MIN_GUILD_LEVEL:
        return {"access": False,
                "requirement": f"guild_level_{MIN_GUILD_LEVEL}",
                "technologies": []}
    docs = await db.arfus_technology_catalog.find(
        {"is_active": True}, {"_id": 0}).sort("sort_order", 1).to_list(20)
    unlocked = await _guild_unlocked_map(guild["id"])
    active_count = sum(1 for u in unlocked.values() if u.get("is_active"))
    return {"access": True,
            "guild_level": guild_level,
            "max_active_techs": MAX_ACTIVE_TECHS,
            "active_count": active_count,
            "technologies": [_pub_tech(t, None, unlocked.get(t["slug"]))
                             for t in docs]}


@router.get("/catalog/{slug}")
async def tech_detail(slug: str, user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    tech = await db.arfus_technology_catalog.find_one(
        {"slug": slug, "is_active": True}, {"_id": 0})
    if not tech:
        raise HTTPException(404, "technology_not_found")
    unlocked = await _guild_unlocked_map(guild["id"])
    my_state = unlocked.get(slug)
    # Availability check for research
    missing: list[dict] = []
    for res in tech["input_resources"]:
        have = await _inventory_qty(guild["id"], res["slug"])
        if have < res["qty"]:
            missing.append({"type": "resource", "slug": res["slug"],
                             "required": res["qty"], "owned": have})
    for mat in tech["input_materials"]:
        have = await _inventory_qty(guild["id"], mat["slug"])
        if have < mat["qty"]:
            missing.append({"type": "material", "slug": mat["slug"],
                             "required": mat["qty"], "owned": have})
    gold_have = int(guild.get("gold", 0))
    if gold_have < tech["input_gold"]:
        missing.append({"type": "gold", "required": tech["input_gold"],
                         "owned": gold_have})
    guild_level = int(guild.get("level", 1))
    if guild_level < tech["guild_level_required"]:
        missing.append({"type": "guild_level",
                         "required": tech["guild_level_required"],
                         "owned": guild_level})
    computed_effect = min(int(tech["effect_value"]),
                          CATEGORY_CAPS.get(tech["category"], 0))
    return {**_pub_tech(tech, None, my_state),
            "missing_requirements": missing,
            "can_research": len(missing) == 0 and my_state is None,
            "computed_effect_for_guild": computed_effect,
            "gold_status": {"required": tech["input_gold"],
                             "owned": gold_have}}


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


@router.post("/research/{slug}")
async def start_research(slug: str,
                         user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    tech = await db.arfus_technology_catalog.find_one(
        {"slug": slug, "is_active": True}, {"_id": 0})
    if not tech:
        raise HTTPException(404, "technology_not_found")
    guild_level = int(guild.get("level", 1))
    if guild_level < tech["guild_level_required"]:
        raise HTTPException(403,
                            f"guild_level_below_required:"
                            f"{tech['guild_level_required']}")
    # Already unlocked?
    already = await db.guild_arfus_technologies.find_one(
        {"guild_id": guild["id"], "technology_slug": slug}, {"_id": 0})
    if already:
        raise HTTPException(409, "already_unlocked")
    # Already researching?
    in_prog = await db.guild_arfus_research_orders.find_one(
        {"guild_id": guild["id"], "technology_slug": slug,
         "status": "in_progress"}, {"_id": 0})
    if in_prog:
        raise HTTPException(409, "research_already_in_progress")
    # Verify resources+materials+gold
    for res in tech["input_resources"]:
        have = await _inventory_qty(guild["id"], res["slug"])
        if have < res["qty"]:
            raise HTTPException(400,
                                f"insufficient_resource:{res['slug']}:"
                                f"required={res['qty']}:owned={have}")
    for mat in tech["input_materials"]:
        have = await _inventory_qty(guild["id"], mat["slug"])
        if have < mat["qty"]:
            raise HTTPException(400,
                                f"insufficient_material:{mat['slug']}:"
                                f"required={mat['qty']}:owned={have}")
    if int(guild.get("gold", 0)) < tech["input_gold"]:
        raise HTTPException(400,
                            f"insufficient_gold:required={tech['input_gold']}")
    # CAS-decrement gold
    gr = await db.guilds.update_one(
        {"id": guild["id"], "gold": {"$gte": tech["input_gold"]}},
        {"$inc": {"gold": -tech["input_gold"]}})
    if not gr.modified_count:
        raise HTTPException(400, "gold_race_condition")
    # Consume resources + materials
    for res in tech["input_resources"]:
        await _consume_from_inventory(guild["id"], res["slug"], res["qty"])
    for mat in tech["input_materials"]:
        await _consume_from_inventory(guild["id"], mat["slug"], mat["qty"])
    # Create order
    now = _now()
    duration = int(tech["research_duration_seconds"])
    order = {"id": str(uuid.uuid4()),
             "guild_id": guild["id"],
             "technology_slug": slug,
             "status": "in_progress",
             "started_at": _iso(now),
             "completes_at": _iso(now + timedelta(seconds=duration)),
             "duration_seconds": duration,
             "resources_consumed": tech["input_resources"],
             "materials_consumed": tech["input_materials"],
             "gold_consumed": tech["input_gold"],
             "resolution_started_at": None,
             "resolved_at": None,
             "created_at": _iso(now),
             "updated_at": _iso(now)}
    await db.guild_arfus_research_orders.insert_one(order)
    await _emit_audit("ARFUS_RESEARCH_STARTED", user["id"], guild["id"],
                       order["id"],
                       {"technology_slug": slug,
                        "gold_consumed": tech["input_gold"]})
    order.pop("_id", None)
    return {"status": "ok", "order": order}


async def _resolve_research_order(order: dict) -> dict:
    """CAS-guarded resolver: complete order + unlock technology."""
    now_iso = _iso(_now())
    r = await db.guild_arfus_research_orders.find_one_and_update(
        {"id": order["id"], "status": "in_progress",
         "resolution_started_at": None},
        {"$set": {"resolution_started_at": now_iso}},
        return_document=True)
    if not r:
        cur = await db.guild_arfus_research_orders.find_one(
            {"id": order["id"]}, {"_id": 0})
        return cur or order
    order = r
    slug = order["technology_slug"]
    # Unlock technology (is_active=False by default, player toggles)
    tech_doc = {"id": str(uuid.uuid4()),
                "guild_id": order["guild_id"],
                "technology_slug": slug,
                "unlocked_at": now_iso,
                "is_active": False,
                "activated_at": None,
                "last_toggled_at": None,
                "created_at": now_iso,
                "updated_at": now_iso}
    try:
        await db.guild_arfus_technologies.insert_one(tech_doc)
    except Exception:
        pass  # already exists (idempotent)
    await db.guild_arfus_research_orders.update_one(
        {"id": order["id"]},
        {"$set": {"status": "completed", "resolved_at": now_iso,
                  "updated_at": now_iso}})
    await _emit_audit("ARFUS_RESEARCH_COMPLETED", None, order["guild_id"],
                       order["id"], {"technology_slug": slug})
    await _emit_audit("ARFUS_TECHNOLOGY_UNLOCKED", None, order["guild_id"],
                       slug, {"technology_slug": slug})
    return await db.guild_arfus_research_orders.find_one(
        {"id": order["id"]}, {"_id": 0})


from app.core.job_freeze import frozen_when_active as _frozen_when_active


@_frozen_when_active(
    "orbus.arfus_forge._resolve_expired_for_guild", freeze_return_value=0,
)
async def _resolve_expired_for_guild(guild_id: str) -> int:
    now = _now()
    cur = db.guild_arfus_research_orders.find(
        {"guild_id": guild_id, "status": "in_progress",
         "completes_at": {"$lte": _iso(now)}}, {"_id": 0})
    resolved = 0
    async for o in cur:
        try:
            await _resolve_research_order(o)
            resolved += 1
        except Exception as exc:
            logger.warning("resolve %s: %s", o.get("id"), exc)
    return resolved


@router.get("/research/mine")
async def research_mine(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    await _resolve_expired_for_guild(guild["id"])
    in_progress = await db.guild_arfus_research_orders.find(
        {"guild_id": guild["id"], "status": "in_progress"},
        {"_id": 0}).sort("started_at", -1).to_list(20)
    recent = await db.guild_arfus_research_orders.find(
        {"guild_id": guild["id"], "status": "completed"},
        {"_id": 0}).sort("resolved_at", -1).to_list(20)
    return {"in_progress": in_progress, "recent": recent}


@router.post("/technologies/{slug}/toggle")
async def toggle_technology(slug: str,
                             user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    tech_row = await db.guild_arfus_technologies.find_one(
        {"guild_id": guild["id"], "technology_slug": slug}, {"_id": 0})
    if not tech_row:
        raise HTTPException(404, "technology_not_unlocked")
    cat_doc = await db.arfus_technology_catalog.find_one(
        {"slug": slug}, {"_id": 0, "category": 1})
    if not cat_doc:
        raise HTTPException(500, "catalog_missing")
    category = cat_doc["category"]
    new_active = not bool(tech_row.get("is_active"))
    if new_active:
        # Enforce max_5
        active_count = await db.guild_arfus_technologies.count_documents(
            {"guild_id": guild["id"], "is_active": True})
        if active_count >= MAX_ACTIVE_TECHS:
            raise HTTPException(409, "max_active_reached")
        # Enforce no-stack-same-category
        other_slugs = [t["slug"] for t in await
                        db.arfus_technology_catalog.find(
                            {"category": category, "slug": {"$ne": slug}},
                            {"_id": 0, "slug": 1}).to_list(50)]
        if other_slugs:
            same_cat_active = await db.guild_arfus_technologies.find_one(
                {"guild_id": guild["id"], "is_active": True,
                 "technology_slug": {"$in": other_slugs}})
            if same_cat_active:
                raise HTTPException(409, "stack_same_category")
    now_iso = _iso(_now())
    await db.guild_arfus_technologies.update_one(
        {"guild_id": guild["id"], "technology_slug": slug},
        {"$set": {"is_active": new_active,
                  "activated_at": now_iso if new_active
                                   else tech_row.get("activated_at"),
                  "last_toggled_at": now_iso,
                  "updated_at": now_iso}})
    ev = ("ARFUS_TECHNOLOGY_ACTIVATED" if new_active
           else "ARFUS_TECHNOLOGY_DEACTIVATED")
    await _emit_audit(ev, user["id"], guild["id"], slug,
                       {"technology_slug": slug,
                        "category": category})
    return {"status": "ok", "slug": slug, "is_active": new_active}


@router.get("/technologies/mine")
async def technologies_mine(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    docs = await db.guild_arfus_technologies.find(
        {"guild_id": guild["id"]}, {"_id": 0}).to_list(50)
    active_count = sum(1 for d in docs if d.get("is_active"))
    bonuses = await get_active_bonuses_for_guild(guild["id"])
    return {"technologies": docs,
            "active_count": active_count,
            "max_active_techs": MAX_ACTIVE_TECHS,
            "active_bonuses_by_category": bonuses}


# ── Admin routes ─────────────────────────────────────────────────────
@admin_router.patch("/technologies/{slug}")
async def admin_toggle_catalog(slug: str, is_active: bool = True,
                                 admin: dict = Depends(get_admin_user)):
    doc = await db.arfus_technology_catalog.find_one({"slug": slug},
                                                       {"_id": 0, "slug": 1})
    if not doc:
        raise HTTPException(404, "technology_not_found")
    await db.arfus_technology_catalog.update_one(
        {"slug": slug},
        {"$set": {"is_active": bool(is_active),
                  "updated_at": _iso(_now())}})
    return {"status": "ok", "slug": slug, "is_active": bool(is_active)}


@admin_router.get("/stats")
async def admin_stats(window_days: int = 7,
                       admin: dict = Depends(get_admin_user)):
    window_days = max(1, min(int(window_days), 30))
    since_iso = _iso(_now() - timedelta(days=window_days))
    orders_pipe = [
        {"$match": {"created_at": {"$gte": since_iso}}},
        {"$group": {"_id": {"tech": "$technology_slug",
                              "status": "$status"},
                     "count": {"$sum": 1}}},
    ]
    order_groups = await db.guild_arfus_research_orders.aggregate(
        orders_pipe).to_list(500)
    tech_pipe = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$technology_slug", "guilds": {"$sum": 1}}},
    ]
    active_dist = await db.guild_arfus_technologies.aggregate(
        tech_pipe).to_list(500)
    return {"window_days": window_days,
            "order_groups": order_groups,
            "active_technology_distribution": active_dist}


@admin_router.post("/dev/complete/{order_id}")
async def admin_dev_force_complete(order_id: str,
                                     admin: dict = Depends(get_admin_user)):
    if _is_production():
        raise HTTPException(403, "disabled_in_production")
    o = await db.guild_arfus_research_orders.find_one(
        {"id": order_id}, {"_id": 0})
    if not o:
        raise HTTPException(404, "order_not_found")
    if o["status"] != "in_progress":
        return {"status": "already_resolved", "order": o}
    past = _iso(_now() - timedelta(seconds=1))
    await db.guild_arfus_research_orders.update_one(
        {"id": order_id, "status": "in_progress"},
        {"$set": {"completes_at": past, "updated_at": past}})
    o["completes_at"] = past
    resolved = await _resolve_research_order(o)
    return {"status": "resolved", "order": resolved}


__all__ = [
    "router", "admin_router",
    "seed_arfus_forge_catalog", "ensure_indexes",
    "get_active_bonuses_for_guild", "bonus_pct",
    "TECHNOLOGIES", "CATEGORY_CAPS", "MAX_ACTIVE_TECHS",
    "MIN_GUILD_LEVEL", "_resolve_research_order",
    "_resolve_expired_for_guild",
]
