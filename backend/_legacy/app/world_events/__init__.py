"""ROUND 16.3 Phase 3 — Continent events V1.

Compact single-file module:
- Seed 12 continent event catalog (idempotent)
- Instances CAS-protected (max 1 active per continent)
- Public GET endpoints + admin CRUD
- On-visit expiry fallback (no scheduler)
- Modifier types: `site_income_pct` applied to guild_site_income; other
  categories flavor-only in Phase 3.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404
from app.world import has_world_access

logger = logging.getLogger("orbus.world_events")

router = APIRouter(prefix="/api/world-events", tags=["world-events"])
admin_router = APIRouter(prefix="/api/admin/world-events",
                         tags=["admin", "world-events"])

CATALOG_SEED = [
    {"slug": "clima_mite", "sort_order": 1, "category": "clima",
     "name_it": "Clima Mite", "name_en": "Mild Climate",
     "description_it": "Il tempo è clemente. Piccolo aiuto alle attività di sede.",
     "description_en": "Weather is kind. Small boost to site activities.",
     "flavor_tags": ["clima", "sereno"],
     "modifier_type": "site_income_pct", "modifier_value": 5},
    {"slug": "carestia", "sort_order": 2, "category": "economia",
     "name_it": "Carestia", "name_en": "Famine",
     "description_it": "Le riserve calano. Le entrate delle sedi si riducono.",
     "description_en": "Reserves fall. Site incomes are reduced.",
     "flavor_tags": ["carestia", "scarsità"],
     "modifier_type": "site_income_pct", "modifier_value": -10},
    {"slug": "boom_commerciale", "sort_order": 3, "category": "economia",
     "name_it": "Boom Commerciale", "name_en": "Trade Boom",
     "description_it": "Le rotte commerciali fioriscono. Le sedi ricevono più ordini.",
     "description_en": "Trade routes flourish. Sites receive more orders.",
     "flavor_tags": ["commercio", "abbondanza"],
     "modifier_type": "site_income_pct", "modifier_value": 15},
    {"slug": "instabilita_magica", "sort_order": 4, "category": "magia",
     "name_it": "Instabilità Magica", "name_en": "Arcane Instability",
     "description_it": "Le trame magiche vibrano. Missioni più rischiose (in arrivo, non ancora applicato).",
     "description_en": "Magic weave shakes. Missions riskier (upcoming, not applied yet).",
     "flavor_tags": ["magia", "rischio"],
     "modifier_type": "mission_risk_pct", "modifier_value": 10},
    {"slug": "benedizione_divina", "sort_order": 5, "category": "divino",
     "name_it": "Benedizione Divina", "name_en": "Divine Blessing",
     "description_it": "I fedeli ricevono grazia. Le sedi prosperano.",
     "description_en": "The faithful receive grace. Sites prosper.",
     "flavor_tags": ["divino", "grazia"],
     "modifier_type": "site_income_pct", "modifier_value": 10},
    {"slug": "maledizione", "sort_order": 6, "category": "divino",
     "name_it": "Maledizione", "name_en": "Curse",
     "description_it": "Un'ombra pesa sul continente. Ricchezza incerta.",
     "description_en": "A shadow weighs on the continent. Wealth uncertain.",
     "flavor_tags": ["divino", "ombra"],
     "modifier_type": "site_income_pct", "modifier_value": -15},
    {"slug": "invasione_locale", "sort_order": 7, "category": "guerra",
     "name_it": "Invasione Locale", "name_en": "Local Invasion",
     "description_it": "Bande predatrici disturbano i confini. Sfida narrativa.",
     "description_en": "Raiders trouble the borders. Narrative challenge.",
     "flavor_tags": ["guerra", "confine"],
     "modifier_type": None, "modifier_value": 0},
    {"slug": "stagione_fertile", "sort_order": 8, "category": "natura",
     "name_it": "Stagione Fertile", "name_en": "Fertile Season",
     "description_it": "I raccolti sono generosi. Le sedi vendono di più.",
     "description_en": "Harvests are generous. Sites sell more.",
     "flavor_tags": ["natura", "raccolto"],
     "modifier_type": "site_income_pct", "modifier_value": 8},
    {"slug": "tempesta_elementale", "sort_order": 9, "category": "elementi",
     "name_it": "Tempesta Elementale", "name_en": "Elemental Storm",
     "description_it": "Gli elementi ruggiscono. Spettacolo narrativo.",
     "description_en": "The elements roar. Narrative spectacle.",
     "flavor_tags": ["elementi", "tempesta"],
     "modifier_type": None, "modifier_value": 0},
    {"slug": "frattura_del_vuoto", "sort_order": 10, "category": "vuoto",
     "name_it": "Frattura del Vuoto", "name_en": "Void Rift",
     "description_it": "Un varco tra i piani si apre. Solo Ergolat conosce il prezzo.",
     "description_en": "A rift between planes opens. Only Ergolat knows the cost.",
     "flavor_tags": ["vuoto", "ergolat", "alveora"],
     "modifier_type": None, "modifier_value": 0},
    {"slug": "guerra_locale", "sort_order": 11, "category": "guerra",
     "name_it": "Guerra Locale", "name_en": "Local War",
     "description_it": "Due fazioni continentali si affrontano. Non toccano ancora la tua gilda.",
     "description_en": "Two continental factions clash. They don't yet touch your guild.",
     "flavor_tags": ["guerra", "politica"],
     "modifier_type": None, "modifier_value": 0},
    {"slug": "presenza_mostri", "sort_order": 12, "category": "mostri",
     "name_it": "Presenza di Mostri", "name_en": "Monster Presence",
     "description_it": "Creature strane si aggirano. Voci nei mercati.",
     "description_en": "Strange creatures roam. Whispers in the markets.",
     "flavor_tags": ["mostri", "voci"],
     "modifier_type": None, "modifier_value": 0},
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


async def seed_continent_event_catalog() -> dict:
    now_iso = _iso(_now())
    inserted = 0
    for c in CATALOG_SEED:
        r = await db.continent_event_catalog.update_one(
            {"slug": c["slug"]},
            {"$setOnInsert": {**c, "is_active": True, "created_at": now_iso}},
            upsert=True,
        )
        if r.upserted_id:
            inserted += 1
    return {"total": len(CATALOG_SEED), "inserted": inserted}


async def _emit_audit(event_type: str, actor_guild_id: Optional[str],
                      related_entity_id: str, metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type=event_type, actor_user_id=None,
            actor_guild_id=actor_guild_id, source="world_events",
            related_entity_id=related_entity_id, metadata=metadata,
        )
    except Exception as exc:
        logger.debug("world_events.audit_emit skipped %s: %s", event_type, exc)


def _pub(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if not k.startswith("_")}
    out.pop("_id", None)
    return out


async def _get_active_event_for_continent(slug: str) -> Optional[dict]:
    """Best-effort expire scaduti, poi ritorna evento active se esiste."""
    now = _now()
    now_iso = _iso(now)
    # Expire fallback (idempotent CAS)
    try:
        await db.continent_event_instances.update_many(
            {"continent_slug": slug, "status": "active",
             "ends_at": {"$lte": now_iso}},
            {"$set": {"status": "expired", "expired_at": now_iso}},
        )
    except Exception as exc:
        logger.debug("expire fallback skipped: %s", exc)
    doc = await db.continent_event_instances.find_one(
        {"continent_slug": slug, "status": "active"}, {"_id": 0},
    )
    if not doc:
        return None
    cat = await db.continent_event_catalog.find_one(
        {"slug": doc["event_slug"]}, {"_id": 0},
    )
    return {"instance": _pub(doc), "catalog": _pub(cat) if cat else None}


# ── PUBLIC ROUTES ────────────────────────────────────────────────────
@router.get("/continent/{slug}/active")
async def get_active_for_continent(slug: str):
    data = await _get_active_event_for_continent(slug)
    if not data:
        return {"active": None}
    return {"active": data}


@router.get("/mine")
async def get_active_for_my_continent(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, gate = await has_world_access(guild["id"])
    if not has_acc:
        raise HTTPException(403, gate.get("reason", "access_denied"))
    pres = await db.guild_world_presence.find_one(
        {"guild_id": guild["id"], "status": "active"}, {"_id": 0},
    )
    if not pres:
        raise HTTPException(409, "no_active_presence")
    data = await _get_active_event_for_continent(pres["continent_slug"])
    return {"continent_slug": pres["continent_slug"], "active": data}


# ── ADMIN ROUTES ────────────────────────────────────────────────────
class CreateEventBody(BaseModel):
    continent_slug: str
    event_slug: str
    starts_at: str  # ISO
    ends_at: str    # ISO
    activate_now: bool = False


@admin_router.post("")
async def create_event(body: CreateEventBody,
                       admin: dict = Depends(get_admin_user)):
    cat = await db.continent_event_catalog.find_one(
        {"slug": body.event_slug, "is_active": True}, {"_id": 0},
    )
    if not cat:
        raise HTTPException(404, "event_slug_not_in_catalog_or_disabled")
    cont = await db.world_continents.find_one(
        {"slug": body.continent_slug}, {"_id": 0, "slug": 1},
    )
    if not cont:
        raise HTTPException(404, "continent_not_found")
    # Try to activate now if requested — CAS check: no other active in continent
    status = "active" if body.activate_now else "scheduled"
    if status == "active":
        existing = await db.continent_event_instances.find_one(
            {"continent_slug": body.continent_slug, "status": "active"},
            {"_id": 0, "id": 1},
        )
        if existing:
            raise HTTPException(409, "another_event_active_on_continent")
    now_iso = _iso(_now())
    doc = {
        "id": str(uuid.uuid4()),
        "continent_slug": body.continent_slug,
        "event_slug": body.event_slug,
        "status": status,
        "starts_at": body.starts_at,
        "ends_at": body.ends_at,
        "created_by": admin.get("id"),
        "created_at": now_iso,
    }
    await db.continent_event_instances.insert_one(doc)
    await _emit_audit("CONTINENT_EVENT_CREATED", None, doc["id"],
                      {"continent_slug": body.continent_slug,
                       "event_slug": body.event_slug, "status": status})
    if status == "active":
        await _emit_audit("CONTINENT_EVENT_ACTIVATED", None, doc["id"],
                          {"continent_slug": body.continent_slug,
                           "event_slug": body.event_slug})
    return {"instance": _pub(doc)}


@admin_router.post("/{eid}/activate")
async def activate_event(eid: str, admin: dict = Depends(get_admin_user)):
    doc = await db.continent_event_instances.find_one({"id": eid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "event_not_found")
    if doc["status"] != "scheduled":
        raise HTTPException(409, f"cannot_activate_status_{doc['status']}")
    # CAS: no other active in same continent
    other = await db.continent_event_instances.find_one(
        {"continent_slug": doc["continent_slug"], "status": "active"},
        {"_id": 0, "id": 1},
    )
    if other:
        raise HTTPException(409, "another_event_active_on_continent")
    now_iso = _iso(_now())
    r = await db.continent_event_instances.find_one_and_update(
        {"id": eid, "status": "scheduled"},
        {"$set": {"status": "active", "activated_at": now_iso}},
        projection={"_id": 0},
    )
    if not r:
        raise HTTPException(409, "race_lost_on_activate")
    r["status"] = "active"
    r["activated_at"] = now_iso
    await _emit_audit("CONTINENT_EVENT_ACTIVATED", None, eid,
                      {"continent_slug": r["continent_slug"],
                       "event_slug": r["event_slug"]})
    return {"instance": _pub(r)}


@admin_router.post("/{eid}/expire")
async def expire_event(eid: str, admin: dict = Depends(get_admin_user)):
    now_iso = _iso(_now())
    r = await db.continent_event_instances.find_one_and_update(
        {"id": eid, "status": {"$in": ["scheduled", "active"]}},
        {"$set": {"status": "expired", "expired_at": now_iso}},
        projection={"_id": 0},
    )
    if not r:
        raise HTTPException(409, "already_expired_or_not_found")
    r["status"] = "expired"
    r["expired_at"] = now_iso
    await _emit_audit("CONTINENT_EVENT_EXPIRED", None, eid,
                      {"continent_slug": r["continent_slug"],
                       "event_slug": r["event_slug"]})
    return {"instance": _pub(r)}


@admin_router.get("/all")
async def list_events(continent_slug: Optional[str] = None,
                      status: Optional[str] = None,
                      limit: int = 50,
                      admin: dict = Depends(get_admin_user)):
    limit = max(1, min(int(limit), 200))
    q: dict = {}
    if continent_slug:
        q["continent_slug"] = continent_slug
    if status:
        q["status"] = status
    docs = await db.continent_event_instances.find(q, {"_id": 0}).sort(
        "created_at", -1,
    ).limit(limit).to_list(limit)
    return {"instances": [_pub(d) for d in docs], "count": len(docs)}


@admin_router.get("/catalog")
async def admin_get_catalog(admin: dict = Depends(get_admin_user)):
    docs = await db.continent_event_catalog.find(
        {}, {"_id": 0}).sort("sort_order", 1).to_list(50)
    return {"catalog": [_pub(d) for d in docs]}


__all__ = ["router", "admin_router", "seed_continent_event_catalog",
           "_get_active_event_for_continent"]
