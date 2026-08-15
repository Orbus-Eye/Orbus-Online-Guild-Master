"""ROUND 16.3 Phase 4 — Continent Resources + Continent Leaderboards V0.

Compact single-file module:
- Seed 8 continent resources (5 epic + 3 rare) idempotent as items with
  item_type="material_continental"
- Gathering missions with CAS lifecycle + adventurer team lock/unlock
- On-visit resolution fallback (no scheduler)
- Continent leaderboards V0 snapshots (24h freshness), on-visit recompute
- Admin CRUD + dev grant utility gated APP_ENV != "production"

Drop rates conservative: base 3% (epic) / 5% (rare), +2% per active
site_income_pct event on continent, max +10% total. Cost 20 gold/mission.
"""
from __future__ import annotations

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
from app.world import has_world_access
from app.adventurers.classless import require_class_hall_assignment

logger = logging.getLogger("orbus.resources")

router = APIRouter(prefix="/api/resources", tags=["resources"])
leaderboard_router = APIRouter(
    prefix="/api/continent-leaderboards", tags=["continent-leaderboards"],
)
admin_router = APIRouter(prefix="/api/admin/resources",
                         tags=["admin", "resources"])
admin_lb_router = APIRouter(prefix="/api/admin/continent-leaderboards",
                             tags=["admin", "continent-leaderboards"])

# ═════════════════════════════════════════════════════════════════════
# CATALOG — 8 continental resources
# 5 epic (cosmically important continents) + 3 rare
# ═════════════════════════════════════════════════════════════════════
CATALOG_SEED = [
    {"slug": "cristallo_di_ambash", "continent_slug": "ambash", "rarity": "epic",
     "name_it": "Cristallo di Ambash", "name_en": "Ambash Crystal",
     "description_it": "Cristallo grezzo pulsante di energia arcana. Solo ad Ambash cresce così puro.",
     "description_en": "Raw crystal pulsing with arcane energy. Grows this pure only in Ambash."},
    {"slug": "cenere_di_velur", "continent_slug": "velur", "rarity": "epic",
     "name_it": "Cenere di Velur", "name_en": "Velur Ash",
     "description_it": "Polvere sacra ottenuta dai rituali di reincarnazione. Ogni granello ricorda una vita.",
     "description_en": "Sacred dust from reincarnation rituals. Every grain remembers a life."},
    {"slug": "linfa_di_soe", "continent_slug": "soe", "rarity": "rare",
     "name_it": "Linfa di Soe", "name_en": "Soe Sap",
     "description_it": "Linfa dorata dalle foreste primordiali. Profuma di natura antica.",
     "description_en": "Golden sap from primordial forests. Smells of ancient nature."},
    {"slug": "nucleo_di_efreto", "continent_slug": "efreto", "rarity": "epic",
     "name_it": "Nucleo di Efreto", "name_en": "Efreto Core",
     "description_it": "Frammento denso di un elemento puro. Cambia colore al tocco.",
     "description_en": "Dense fragment of pure elemental matter. Changes color at touch."},
    {"slug": "osso_di_irthe", "continent_slug": "irthe", "rarity": "rare",
     "name_it": "Osso di Irthe", "name_en": "Irthe Bone",
     "description_it": "Osso di guardiano necromantico rinato. Ossa che non decadono.",
     "description_en": "Bone of a reborn necromantic guardian. Bone that never decays."},
    {"slug": "seme_di_nathos", "continent_slug": "nathos", "rarity": "rare",
     "name_it": "Seme di Nathos", "name_en": "Nathos Seed",
     "description_it": "Seme incorruttibile che germoglia solo nel Continente della Vita.",
     "description_en": "Incorruptible seed that sprouts only in the Continent of Life."},
    {"slug": "frammento_di_ergolat", "continent_slug": "ergolat", "rarity": "epic",
     "name_it": "Frammento di Ergolat", "name_en": "Ergolat Shard",
     "description_it": "Scheggia di Obelisco del Vuoto. Legata alla presenza di Alveora.",
     "description_en": "Void Obelisk shard. Linked to Alveora's presence."},
    {"slug": "sigillo_di_aveol", "continent_slug": "aveol", "rarity": "epic",
     "name_it": "Sigillo di Aveol", "name_en": "Aveol Seal",
     "description_it": "Sigillo runico dei Guardiani dell'Ordine. Vibra vicino al caos.",
     "description_en": "Runic seal of the Order Guardians. Hums near chaos."},
]

MISSION_DURATION_SECONDS = 780  # 13 min (ROUND 17.2 P0.3 — was 1800)
MISSION_COST_GOLD = 20
TEAM_SIZE = 3
DROP_RATE_RARE = 5
DROP_RATE_EPIC = 3
EVENT_DROP_BOOST_MAX = 10  # cap
LEADERBOARD_FRESHNESS_HOURS = 24
LEADERBOARD_TOP_N = 20

# ROUND 17.2 P0.3 — Gating & pacing
MIN_GUILD_LEVEL = 2                # Prestigio di Gilda Lv 2 required
DAILY_MISSION_CAP = 6              # max started per guild per UTC day
CONTINENT_DAILY_LIMIT = 1          # max per continent per guild per UTC day

RESOURCE_ITEM_TYPE = "material_continental"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _is_production() -> bool:
    return os.environ.get("APP_ENV") == "production"


async def _emit_audit(event_type: str, actor_user_id: Optional[str],
                      actor_guild_id: Optional[str], related_entity_id: Optional[str],
                      metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type=event_type, actor_user_id=actor_user_id,
            actor_guild_id=actor_guild_id, source="resources",
            related_entity_id=related_entity_id or "-", metadata=metadata,
        )
    except Exception as exc:
        logger.debug("resources.audit_emit skipped %s: %s", event_type, exc)


def _drop_rate_for(rarity: str) -> int:
    return DROP_RATE_EPIC if rarity == "epic" else DROP_RATE_RARE


async def _event_drop_bonus(continent_slug: str) -> int:
    """Return small bonus % from active site_income_pct events (max 10)."""
    from app.world_events import _get_active_event_for_continent
    data = await _get_active_event_for_continent(continent_slug)
    if not data:
        return 0
    cat = (data.get("catalog") or {})
    if cat.get("modifier_type") != "site_income_pct":
        return 0
    v = int(cat.get("modifier_value") or 0)
    # +2% per positive-income event, no bonus for negative
    return min(EVENT_DROP_BOOST_MAX, max(0, 2 if v > 0 else 0))


def _pub(doc: dict) -> dict:
    if not doc:
        return {}
    out = {k: v for k, v in doc.items() if not k.startswith("_")}
    out.pop("_id", None)
    return out


# ═════════════════════════════════════════════════════════════════════
# SEED
# ═════════════════════════════════════════════════════════════════════
async def seed_resource_catalog() -> dict:
    now_iso = _iso(_now())
    inserted_cat = 0
    inserted_items = 0
    for c in CATALOG_SEED:
        r = await db.continent_resource_catalog.update_one(
            {"slug": c["slug"]},
            {"$setOnInsert": {
                **c,
                "is_active": True,
                "is_tradeable": True,
                "is_cosmetic": False,
                "affects_combat": False,
                "affects_economy": False,
                "market_cap_daily_per_guild": 3,
                "created_at": now_iso,
            }},
            upsert=True,
        )
        if r.upserted_id:
            inserted_cat += 1
        # Mirror as an entry in `items` collection so existing inventory
        # infrastructure (GET /api/inventory) can join it.
        item_doc = {
            "id": str(uuid.uuid4()),
            "slug": c["slug"],
            "name": c["name_it"],
            "display_name_it": c["name_it"],
            "display_name_en": c["name_en"],
            "description": c["description_it"],
            "item_type": RESOURCE_ITEM_TYPE,
            "rarity": c["rarity"],
            "level_required": 1,
            "power_score": 0,
            "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 0,
            "endurance_bonus": 0, "faith_bonus": 0,
            "is_tradeable": True,
            "is_cosmetic": False,
            "affects_combat": False,
            "affects_economy": False,
            "affects_ranking": False,
            "can_be_sold_for_gold": True,
            "can_be_sold_for_real_money": False,
            "is_active": True,
            "continent_slug": c["continent_slug"],
            "created_at": now_iso,
        }
        ir = await db.items.update_one(
            {"slug": c["slug"]},
            {"$setOnInsert": item_doc},
            upsert=True,
        )
        if ir.upserted_id:
            inserted_items += 1
    return {"total": len(CATALOG_SEED),
            "inserted_catalog": inserted_cat,
            "inserted_items": inserted_items}


async def ensure_indexes() -> None:
    try:
        await db.resource_gathering_missions.create_index(
            [("guild_id", 1), ("status", 1)], name="idx_guild_status",
        )
        await db.continent_leaderboard_snapshots.create_index(
            [("continent_slug", 1), ("leaderboard_type", 1), ("computed_at", -1)],
            name="idx_lb_freshness",
        )
    except Exception as exc:
        logger.debug("resource indexes skipped: %s", exc)


# ═════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════
async def _get_current_continent_slug(guild_id: str) -> Optional[str]:
    p = await db.guild_world_presence.find_one(
        {"guild_id": guild_id, "status": "active"},
        {"_id": 0, "continent_slug": 1},
    )
    return p.get("continent_slug") if p else None


async def _validate_adventurers(guild_id: str, adventurer_ids: list[str]) -> list[dict]:
    if len(adventurer_ids) != TEAM_SIZE:
        raise HTTPException(400, f"team_must_have_{TEAM_SIZE}_adventurers")
    if len(set(adventurer_ids)) != TEAM_SIZE:
        raise HTTPException(400, "team_has_duplicate_adventurers")
    docs = await db.adventurers.find(
        {"id": {"$in": adventurer_ids}, "guild_id": guild_id},
        {"_id": 0},
    ).to_list(TEAM_SIZE)
    if len(docs) != TEAM_SIZE:
        raise HTTPException(400, "adventurers_not_found_in_guild")
    require_class_hall_assignment(docs, source="resource_mission.start")
    for d in docs:
        # Server-side double-book protection (Phase 4 post-verify):
        # respect both `is_available` and `status` and per-flow locks.
        if d.get("is_available") is False:
            raise HTTPException(409, f"adventurer_busy:{d['id']}:not_available")
        if d.get("status") not in (None, "idle", "available"):
            raise HTTPException(409, f"adventurer_busy:{d['id']}:{d.get('status')}")
        if d.get("expedition_in_progress"):
            raise HTTPException(409, f"adventurer_busy:{d['id']}:expedition")
        if d.get("current_mission_id"):
            raise HTTPException(409, f"adventurer_busy:{d['id']}:mission_locked")
    return docs


def _compute_team_power(adventurers: list[dict]) -> int:
    from app.expeditions.formulas import adventurer_effective_power
    return sum(adventurer_effective_power(a) for a in adventurers)


def _success_chance(team_power: int) -> int:
    return max(20, min(90, int(50 + (team_power - 60) * 0.5)))


async def _lock_adventurers(ids: list[str], mission_id: str) -> None:
    """Post-verify Phase 4 fix: flip is_available=False + stamp
    current_mission_type so cross-flow gates block this team."""
    now_iso = _iso(_now())
    await db.adventurers.update_many(
        {"id": {"$in": ids}},
        {"$set": {"status": "resource_gathering",
                  "is_available": False,
                  "current_mission_id": mission_id,
                  "current_mission_type": "resource_gathering",
                  "updated_at": now_iso}},
    )


async def _release_adventurers(ids: list[str]) -> None:
    now_iso = _iso(_now())
    await db.adventurers.update_many(
        {"id": {"$in": ids}},
        {"$set": {"status": "idle",
                  "is_available": True,
                  "current_mission_id": None,
                  "current_mission_type": None,
                  "updated_at": now_iso}},
    )


async def _grant_resource(guild_id: str, resource_slug: str, qty: int) -> str:
    """Add qty to guild inventory of the given resource. Returns item_id."""
    item = await db.items.find_one({"slug": resource_slug}, {"_id": 0})
    if not item:
        raise HTTPException(500, f"item_not_found_for_resource:{resource_slug}")
    now_iso = _iso(_now())
    # Idempotent upsert: inventory_items row per (guild_id, item_id)
    existing = await db.inventory_items.find_one(
        {"guild_id": guild_id, "item_id": item["id"]}, {"_id": 0, "id": 1},
    )
    if existing:
        await db.inventory_items.update_one(
            {"id": existing["id"]},
            {"$inc": {"quantity": qty},
             "$set": {"updated_at": now_iso}},
        )
    else:
        await db.inventory_items.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": guild_id,
            "item_id": item["id"],
            "quantity": int(qty),
            "acquired_at": now_iso,
            "created_at": now_iso,
            "updated_at": now_iso,
        })
    return item["id"]


async def _resolve_mission(mission: dict, rng: Optional[_random.Random] = None) -> dict:
    """Idempotent resolve via CAS on resolution_started_at."""
    r = await db.resource_gathering_missions.find_one_and_update(
        {"id": mission["id"], "status": "in_progress",
         "resolution_started_at": None},
        {"$set": {"resolution_started_at": _iso(_now())}},
        projection={"_id": 0},
    )
    if not r:
        # Another resolver already handling; return current state
        return await db.resource_gathering_missions.find_one(
            {"id": mission["id"]}, {"_id": 0},
        ) or mission
    rng = rng or _random
    # ROUND 16.3 Phase 5B — Arfus exploration_luck bonus (0 if none active).
    from app.arfus_forge import bonus_pct as _arfus_bonus
    _luck_bonus = await _arfus_bonus(r["guild_id"], "exploration_luck")
    success = rng.randint(1, 100) <= int(r.get("success_chance", 50))
    resources_obtained = 0
    outcome = "failed"
    if success:
        drop_roll = rng.randint(1, 100)
        effective_drop = min(100, int(r.get("drop_rate", DROP_RATE_RARE))
                               + int(_luck_bonus))
        if drop_roll <= effective_drop:
            resources_obtained = 1
            outcome = "completed_with_drop"
        else:
            outcome = "completed_no_drop"
    now_iso = _iso(_now())
    new_status = "completed" if success else "failed"
    updates = {"status": new_status, "outcome": outcome,
               "resources_obtained": resources_obtained,
               "resolved_at": now_iso, "updated_at": now_iso}
    await db.resource_gathering_missions.update_one(
        {"id": r["id"]}, {"$set": updates},
    )
    r.update(updates)
    # Release adventurers
    await _release_adventurers(r.get("adventurers", []))
    # Grant resource if drop
    if resources_obtained > 0:
        item_id = await _grant_resource(r["guild_id"], r["resource_slug"],
                                        resources_obtained)
        await _emit_audit(
            "RESOURCE_GRANTED", None, r["guild_id"], r["id"],
            {"resource_slug": r["resource_slug"],
             "qty": resources_obtained, "item_id": item_id,
             "continent_slug": r["continent_slug"]},
        )
    # Audit final
    audit_event = "RESOURCE_MISSION_COMPLETED" if success else "RESOURCE_MISSION_FAILED"
    await _emit_audit(
        audit_event, None, r["guild_id"], r["id"],
        {"outcome": outcome, "resources_obtained": resources_obtained,
         "resource_slug": r["resource_slug"],
         "continent_slug": r["continent_slug"]},
    )
    # FASE 10E — +10 Beni di Gilda per missione risorse completata con
    # successo (le "missioni" canoniche del gioco con completion event
    # sono le resource_gathering_missions). Idempotente per mission_id:
    # marker CAS sul doc missione, un solo reward per completamento.
    if success:
        try:
            claim = await db.resource_gathering_missions.update_one(
                {"id": r["id"],
                 "supplies_reward_granted": {"$ne": True}},
                {"$set": {"supplies_reward_granted": True}},
            )
            if getattr(claim, "modified_count", 0):
                from app.guild_supplies import (
                    MISSION_REWARD, grant_supplies,
                )
                await grant_supplies(
                    db, r["guild_id"], MISSION_REWARD,
                    reason="mission_reward",
                    event_type="guild_supplies_mission_reward",
                    metadata={"mission_id": r["id"],
                              "resource_slug": r.get("resource_slug")},
                )
        except Exception:
            pass

    # ROUND 16.5.3 P1 — Guild XP drip (Prestigio di Gilda). Best-effort,
    # idempotente su mission_id, cap 6/giorno. Solo su success.
    # ROUND 17.2 P0.3 — XP tier per rarity (rare=+8, epic=+10).
    try:
        from app.achievements.xp_hooks import on_resource_mission_completed
        await on_resource_mission_completed(
            db, r["guild_id"], mission_id=r["id"], success=success,
            rarity=r.get("resource_rarity"),
        )
    except Exception:
        pass
    return r


from app.core.job_freeze import frozen_when_active as _frozen_when_active


@_frozen_when_active(
    "orbus.resources._resolve_expired_missions_for_guild", freeze_return_value=0,
)
async def _resolve_expired_missions_for_guild(guild_id: str) -> int:
    now_iso = _iso(_now())
    stuck = await db.resource_gathering_missions.find(
        {"guild_id": guild_id, "status": "in_progress",
         "completes_at": {"$lte": now_iso}},
        {"_id": 0},
    ).to_list(20)
    for m in stuck:
        await _resolve_mission(m)
    return len(stuck)


# ═════════════════════════════════════════════════════════════════════
# PUBLIC — resources
# ═════════════════════════════════════════════════════════════════════
@router.get("/catalog")
async def resource_catalog():
    docs = await db.continent_resource_catalog.find(
        {"is_active": True}, {"_id": 0},
    ).sort("continent_slug", 1).to_list(20)
    return {"resources": [_pub(d) for d in docs]}


@router.get("/mine")
async def my_resources(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, _ = await has_world_access(guild["id"])
    if not has_acc:
        raise HTTPException(403, "world_access_denied")
    slug = await _get_current_continent_slug(guild["id"])
    # Items of type material_continental in inventory
    items = await db.items.find(
        {"item_type": RESOURCE_ITEM_TYPE}, {"_id": 0},
    ).to_list(20)
    items_by_id = {it["id"]: it for it in items}
    rows = await db.inventory_items.find(
        {"guild_id": guild["id"], "item_id": {"$in": list(items_by_id.keys())}},
        {"_id": 0},
    ).to_list(50)
    inventory = [
        {"item_id": r["item_id"],
         "slug": items_by_id[r["item_id"]]["slug"],
         "continent_slug": items_by_id[r["item_id"]].get("continent_slug"),
         "quantity": int(r.get("quantity", 0)),
         "rarity": items_by_id[r["item_id"]].get("rarity")}
        for r in rows if r["item_id"] in items_by_id
    ]
    return {"current_continent": slug, "inventory": inventory}


class GatherBody(BaseModel):
    resource_slug: str
    adventurer_ids: list[str] = Field(min_length=TEAM_SIZE, max_length=TEAM_SIZE)


@router.post("/gather")
async def gather(body: GatherBody, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, _ = await has_world_access(guild["id"])
    if not has_acc:
        raise HTTPException(403, "world_access_denied")
    # ROUND 17.2 P0.3 — Gate Prestigio di Gilda Lv 2 (schema field: `guild_level`).
    # Legacy `guild.level` NOT used (R16.5.4d separation preserved).
    prestige_level = int(guild.get("guild_level", 1) or 1)
    if prestige_level < MIN_GUILD_LEVEL:
        raise HTTPException(
            403,
            {
                "code": "prestige_level_gate",
                "message": f"Richiede Livello di Gilda {MIN_GUILD_LEVEL} per raccogliere risorse.",
                "current_level": prestige_level,
                "required_level": MIN_GUILD_LEVEL,
            },
        )
    # Resolve any expired missions before starting a new one
    await _resolve_expired_missions_for_guild(guild["id"])
    slug = await _get_current_continent_slug(guild["id"])
    if not slug:
        raise HTTPException(409, "no_continent_active")
    resource = await db.continent_resource_catalog.find_one(
        {"slug": body.resource_slug, "is_active": True}, {"_id": 0},
    )
    if not resource:
        raise HTTPException(404, "resource_not_found")
    if resource["continent_slug"] != slug:
        raise HTTPException(400, "resource_not_in_current_continent")

    # ROUND 17.2 P0.3 — Daily cap 6/guild + cooldown 1/continent/day.
    # Count all statuses (in_progress + completed + failed) for the current UTC day.
    today_iso_date = _now().strftime("%Y-%m-%d")
    today_prefix = today_iso_date  # ISO dates start with YYYY-MM-DD
    started_today_total = await db.resource_gathering_missions.count_documents({
        "guild_id": guild["id"],
        "created_at": {"$regex": f"^{today_prefix}"},
    })
    if started_today_total >= DAILY_MISSION_CAP:
        raise HTTPException(
            429,
            {
                "code": "daily_cap_reached",
                "message": (
                    f"Hai già completato o avviato il massimo di {DAILY_MISSION_CAP} "
                    "missioni risorse oggi. Torna domani per raccogliere altre risorse."
                ),
                "cap": DAILY_MISSION_CAP,
                "count_today": started_today_total,
            },
        )
    started_today_continent = await db.resource_gathering_missions.count_documents({
        "guild_id": guild["id"],
        "continent_slug": slug,
        "created_at": {"$regex": f"^{today_prefix}"},
    })
    if started_today_continent >= CONTINENT_DAILY_LIMIT:
        continent_doc = await db.world_continents.find_one(
            {"slug": slug}, {"_id": 0, "name_it": 1, "name": 1},
        ) or {}
        continent_name = continent_doc.get("name_it") or continent_doc.get("name") or slug.title()
        raise HTTPException(
            429,
            {
                "code": "continent_daily_limit",
                "message": (
                    f"Hai già raccolto risorse a {continent_name} oggi. "
                    "Scegli un altro continente o torna domani."
                ),
                "continent_slug": slug,
                "continent_name": continent_name,
            },
        )

    if int(guild.get("gold", 0)) < MISSION_COST_GOLD:
        raise HTTPException(400, f"insufficient_gold:{MISSION_COST_GOLD}")
    advs = await _validate_adventurers(guild["id"], body.adventurer_ids)
    team_power = _compute_team_power(advs)
    success_chance = _success_chance(team_power)
    event_bonus = await _event_drop_bonus(slug)
    drop_rate = _drop_rate_for(resource["rarity"]) + event_bonus
    now = _now()
    now_iso = _iso(now)
    completes_at = _iso(now + timedelta(seconds=MISSION_DURATION_SECONDS))
    mission_id = str(uuid.uuid4())
    mission = {
        "id": mission_id,
        "guild_id": guild["id"],
        "continent_slug": slug,
        "resource_slug": body.resource_slug,
        "resource_rarity": resource.get("rarity"),  # R17.2 P0.3 — tier XP reward
        "adventurers": body.adventurer_ids,
        "team_snapshot": [
            {"id": a["id"], "name": a.get("name"), "level": a.get("level", 1)}
            for a in advs
        ],
        "status": "in_progress",
        "started_at": now_iso,
        "completes_at": completes_at,
        "duration_seconds": MISSION_DURATION_SECONDS,
        "team_power": team_power,
        "success_chance": success_chance,
        "drop_rate": drop_rate,
        "event_drop_bonus": event_bonus,
        "outcome": None,
        "resources_obtained": 0,
        "resolution_started_at": None,
        "recovered": False,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    # Deduct cost + lock adventurers
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$inc": {"gold": -MISSION_COST_GOLD},
         "$set": {"updated_at": now_iso}},
    )
    await db.resource_gathering_missions.insert_one(mission)
    await _lock_adventurers(body.adventurer_ids, mission_id)
    await _emit_audit(
        "RESOURCE_MISSION_STARTED", current_user.get("id"), guild["id"], mission_id,
        {"resource_slug": body.resource_slug, "continent_slug": slug,
         "cost_gold": MISSION_COST_GOLD, "team_power": team_power,
         "success_chance": success_chance, "drop_rate": drop_rate},
    )
    return {"mission": _pub(mission)}


@router.get("/missions/mine")
async def my_missions(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    await _resolve_expired_missions_for_guild(guild["id"])
    in_prog = await db.resource_gathering_missions.find(
        {"guild_id": guild["id"], "status": "in_progress"}, {"_id": 0},
    ).sort("started_at", -1).to_list(10)
    recent = await db.resource_gathering_missions.find(
        {"guild_id": guild["id"], "status": {"$in": ["completed", "failed"]}},
        {"_id": 0},
    ).sort("resolved_at", -1).limit(10).to_list(10)
    return {"in_progress": [_pub(m) for m in in_prog],
            "recent": [_pub(m) for m in recent]}


# ROUND 17.2 P0.3 — Frontend-facing daily usage stats + gating info.
@router.get("/missions/stats")
async def my_missions_stats(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    today_prefix = _now().strftime("%Y-%m-%d")
    total_today = await db.resource_gathering_missions.count_documents({
        "guild_id": guild["id"],
        "created_at": {"$regex": f"^{today_prefix}"},
    })
    # Continents already used today (list of slugs).
    cursor = db.resource_gathering_missions.aggregate([
        {"$match": {
            "guild_id": guild["id"],
            "created_at": {"$regex": f"^{today_prefix}"},
        }},
        {"$group": {"_id": "$continent_slug"}},
    ])
    continents_today = [d["_id"] for d in await cursor.to_list(20) if d.get("_id")]
    prestige_level = int(guild.get("guild_level", 1) or 1)
    return {
        "daily_used": total_today,
        "daily_cap": DAILY_MISSION_CAP,
        "continents_used_today": continents_today,
        "min_guild_level": MIN_GUILD_LEVEL,
        "current_guild_level": prestige_level,
        "gate_passed": prestige_level >= MIN_GUILD_LEVEL,
        "mission_duration_seconds": MISSION_DURATION_SECONDS,
        "prestige_reward_rare": 8,
        "prestige_reward_epic": 10,
    }


@router.get("/missions/{mission_id}")
async def mission_detail(mission_id: str,
                          current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    m = await db.resource_gathering_missions.find_one(
        {"id": mission_id, "guild_id": guild["id"]}, {"_id": 0},
    )
    if not m:
        raise HTTPException(404, "mission_not_found")
    # Trigger resolve if expired
    if m["status"] == "in_progress" and m.get("completes_at", "") <= _iso(_now()):
        m = await _resolve_mission(m) or m
    return {"mission": _pub(m)}


# ═════════════════════════════════════════════════════════════════════
# CONTINENT LEADERBOARDS V0
# ═════════════════════════════════════════════════════════════════════
LEADERBOARD_TYPES = ("resource_gathering_count", "site_income_total")


async def _compute_leaderboard(continent_slug: str, ltype: str) -> dict:
    """Recompute a top-20 snapshot from source-of-truth collections."""
    if ltype not in LEADERBOARD_TYPES:
        raise HTTPException(400, f"unknown_leaderboard_type:{ltype}")
    now = _now()
    now_iso = _iso(now)
    period_start_iso = _iso(now - timedelta(days=7))
    # Only guilds anchored to this continent (active presence)
    presences = await db.guild_world_presence.find(
        {"continent_slug": continent_slug, "status": "active"},
        {"_id": 0, "guild_id": 1},
    ).to_list(1000)
    guild_ids = [p["guild_id"] for p in presences]
    if not guild_ids:
        entries = []
    elif ltype == "resource_gathering_count":
        cur = db.resource_gathering_missions.aggregate([
            {"$match": {"guild_id": {"$in": guild_ids},
                        "status": "completed",
                        "resolved_at": {"$gte": period_start_iso}}},
            {"$group": {"_id": "$guild_id",
                        "score": {"$sum": "$resources_obtained"}}},
            {"$sort": {"score": -1}},
            {"$limit": LEADERBOARD_TOP_N},
        ])
        rows = await cur.to_list(LEADERBOARD_TOP_N)
        entries = rows
    else:  # site_income_total
        cur = db.guild_site_income_ledger.aggregate([
            {"$match": {"guild_id": {"$in": guild_ids},
                        "claimed_at": {"$ne": None},
                        "day_bucket": {"$gte": (now - timedelta(days=7)).strftime("%Y-%m-%d")}}},
            {"$group": {"_id": "$guild_id",
                        "score": {"$sum": "$total_amount"}}},
            {"$sort": {"score": -1}},
            {"$limit": LEADERBOARD_TOP_N},
        ])
        entries = await cur.to_list(LEADERBOARD_TOP_N)
    # Attach guild names + rank
    if entries:
        g_ids = [e["_id"] for e in entries]
        gs = await db.guilds.find({"id": {"$in": g_ids}},
                                   {"_id": 0, "id": 1, "name": 1}).to_list(50)
        names = {g["id"]: g.get("name", "?") for g in gs}
        ranked = [
            {"guild_id": e["_id"], "guild_name": names.get(e["_id"], "?"),
             "score": int(e["score"]), "rank": i + 1}
            for i, e in enumerate(entries)
        ]
    else:
        ranked = []
    snap = {
        "id": str(uuid.uuid4()),
        "continent_slug": continent_slug,
        "leaderboard_type": ltype,
        "period_start": period_start_iso,
        "period_end": now_iso,
        "computed_at": now_iso,
        "entries": ranked,
    }
    await db.continent_leaderboard_snapshots.insert_one(dict(snap))
    await _emit_audit(
        "LEADERBOARD_SNAPSHOT_COMPUTED", None, None, snap["id"],
        {"continent_slug": continent_slug, "leaderboard_type": ltype,
         "entries_count": len(ranked)},
    )
    return snap


async def _get_or_recompute_leaderboard(continent_slug: str, ltype: str) -> dict:
    now = _now()
    fresh_cutoff = _iso(now - timedelta(hours=LEADERBOARD_FRESHNESS_HOURS))
    doc = await db.continent_leaderboard_snapshots.find_one(
        {"continent_slug": continent_slug, "leaderboard_type": ltype,
         "computed_at": {"$gt": fresh_cutoff}},
        {"_id": 0}, sort=[("computed_at", -1)],
    )
    if doc:
        return _pub(doc)
    snap = await _compute_leaderboard(continent_slug, ltype)
    return _pub(snap)


@leaderboard_router.get("/{continent_slug}/summary")
async def lb_summary(continent_slug: str):
    out = {}
    for ltype in LEADERBOARD_TYPES:
        snap = await _get_or_recompute_leaderboard(continent_slug, ltype)
        out[ltype] = {
            "computed_at": snap.get("computed_at"),
            "top3": (snap.get("entries") or [])[:3],
            "entries_count": len(snap.get("entries") or []),
        }
    return {"continent_slug": continent_slug, "leaderboards": out}


@leaderboard_router.get("/{continent_slug}/{ltype}")
async def lb_detail(continent_slug: str, ltype: str):
    if ltype not in LEADERBOARD_TYPES:
        raise HTTPException(400, f"unknown_leaderboard_type:{ltype}")
    snap = await _get_or_recompute_leaderboard(continent_slug, ltype)
    return {"snapshot": snap}


# ═════════════════════════════════════════════════════════════════════
# ADMIN
# ═════════════════════════════════════════════════════════════════════
class ResourceTogglePayload(BaseModel):
    is_active: bool


@admin_router.patch("/catalog/{slug}")
async def admin_toggle_resource(slug: str, body: ResourceTogglePayload,
                                 admin: dict = Depends(get_admin_user)):
    r = await db.continent_resource_catalog.find_one_and_update(
        {"slug": slug},
        {"$set": {"is_active": bool(body.is_active),
                   "updated_at": _iso(_now())}},
        projection={"_id": 0},
    )
    if not r:
        raise HTTPException(404, "resource_not_found")
    r["is_active"] = bool(body.is_active)
    # Mirror on items collection
    await db.items.update_one(
        {"slug": slug}, {"$set": {"is_active": bool(body.is_active)}},
    )
    return {"resource": _pub(r)}


@admin_router.get("/gathering-stats")
async def admin_stats(window_days: int = 7,
                       admin: dict = Depends(get_admin_user)):
    window_days = max(1, min(int(window_days), 30))
    since = _iso(_now() - timedelta(days=window_days))
    cur = db.resource_gathering_missions.aggregate([
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": {"resource_slug": "$resource_slug",
                              "status": "$status"},
                    "count": {"$sum": 1},
                    "drops": {"$sum": "$resources_obtained"}}},
        {"$sort": {"count": -1}},
    ])
    rows = await cur.to_list(200)
    return {"window_days": window_days,
            "groups": [{"resource_slug": r["_id"]["resource_slug"],
                        "status": r["_id"]["status"],
                        "count": r["count"], "drops": r["drops"]}
                       for r in rows]}


@admin_router.post("/dev/grant/{guild_id}/{resource_slug}")
async def admin_dev_grant(guild_id: str, resource_slug: str, qty: int = 1,
                            admin: dict = Depends(get_admin_user)):
    if _is_production():
        raise HTTPException(403, "disabled_in_production")
    qty = max(1, min(int(qty), 20))
    r = await db.continent_resource_catalog.find_one(
        {"slug": resource_slug}, {"_id": 0, "slug": 1},
    )
    if not r:
        raise HTTPException(404, "resource_not_found")
    item_id = await _grant_resource(guild_id, resource_slug, qty)
    await _emit_audit(
        "RESOURCE_GRANTED", admin.get("id"), guild_id, item_id,
        {"resource_slug": resource_slug, "qty": qty, "utility": "dev_grant"},
    )
    return {"status": "ok", "guild_id": guild_id,
            "resource_slug": resource_slug, "qty": qty, "item_id": item_id}


@admin_router.post("/dev/complete/{mission_id}")
async def admin_dev_complete(mission_id: str,
                              admin: dict = Depends(get_admin_user)):
    """Force-resolve an in-progress mission NOW (dev/QA only).

    Post-verify Phase 4 utility: bypasses the 30-min wait by setting
    `completes_at` to the past and triggering `_resolve_mission`
    immediately. Fully gated on `APP_ENV != production`. Idempotent
    via the same CAS lock used by the natural resolver.
    """
    if _is_production():
        raise HTTPException(403, "disabled_in_production")
    m = await db.resource_gathering_missions.find_one(
        {"id": mission_id}, {"_id": 0},
    )
    if not m:
        raise HTTPException(404, "mission_not_found")
    if m.get("status") != "in_progress":
        return {"status": "already_resolved", "mission": _pub(m)}
    past = _iso(_now() - timedelta(seconds=1))
    await db.resource_gathering_missions.update_one(
        {"id": mission_id, "status": "in_progress"},
        {"$set": {"completes_at": past, "updated_at": past}},
    )
    m["completes_at"] = past
    resolved = await _resolve_mission(m)
    return {"status": "resolved", "mission": _pub(resolved)}


@admin_lb_router.post("/{continent_slug}/{ltype}/recompute")
async def admin_recompute_lb(continent_slug: str, ltype: str,
                             admin: dict = Depends(get_admin_user)):
    if ltype not in LEADERBOARD_TYPES:
        raise HTTPException(400, f"unknown_leaderboard_type:{ltype}")
    snap = await _compute_leaderboard(continent_slug, ltype)
    return {"snapshot": _pub(snap)}


__all__ = [
    "router", "leaderboard_router", "admin_router", "admin_lb_router",
    "seed_resource_catalog", "ensure_indexes",
    "_resolve_mission", "_resolve_expired_missions_for_guild",
    "_compute_leaderboard", "_get_or_recompute_leaderboard",
    "MISSION_COST_GOLD", "TEAM_SIZE",
]
