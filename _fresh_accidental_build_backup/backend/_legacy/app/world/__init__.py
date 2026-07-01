"""ROUND 16.3 Phase 2 — Mondo & 8 Mastocontinenti V1.

Compact single-file world module:
- Seed 8 continents (Ambash/Velur/Soe/Efreto/Irthe/Nathos/Ergolat/Aveol)
- Access gate: guild must have >=1 raid with status="completed"
- CAS-protected join/change with 30-day cooldown
- No hard delete: history via `guild_world_presence` with `status=active|archived`
- Neighbors picker (max 8, activity bucket only, no fine competitive data)
- Admin toggle + dev-only grant utility

Public: `router`, `admin_router`, `seed_world_continents`.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.world")

router = APIRouter(prefix="/api/world", tags=["world"])
admin_router = APIRouter(prefix="/api/admin/world", tags=["admin", "world"])

CHANGE_COOLDOWN_DAYS = 30

CONTINENTS_SEED = [
    {
        "slug": "ambash", "sort_order": 1,
        "name_it": "Ambash", "name_en": "Ambash",
        "domain_it": "Magia", "domain_en": "Magic",
        "deity_it": "Sorgente Arcana", "deity_en": "Arcane Source",
        "description_it": "Ambash è il continente delle torri di cristallo e delle biblioteche fluttuanti. La sua terra pulsa di correnti arcane e forma i più grandi maghi di Orbus.",
        "description_en": "Ambash is the continent of crystal towers and floating libraries. Its land throbs with arcane currents and forges Orbus's greatest mages.",
        "theme_tags": ["magia", "arcano", "biblioteche", "cristalli"],
    },
    {
        "slug": "velur", "sort_order": 2,
        "name_it": "Velur", "name_en": "Velur",
        "domain_it": "Reincarnazione", "domain_en": "Reincarnation",
        "deity_it": "Ruota delle Ere", "deity_en": "Wheel of Ages",
        "description_it": "Velur ospita le colline dei ricordi e i giardini dove le anime tornano. Ogni albero è memoria, ogni pietra è un nome che è stato.",
        "description_en": "Velur holds hills of memory and gardens where souls return. Each tree is memory, each stone a name that once was.",
        "theme_tags": ["reincarnazione", "memoria", "cicli", "giardini"],
    },
    {
        "slug": "soe", "sort_order": 3,
        "name_it": "Soe", "name_en": "Soe",
        "domain_it": "Natura", "domain_en": "Nature",
        "deity_it": "Radice Madre", "deity_en": "Mother Root",
        "description_it": "Soe è un unico immenso bosco vivo. I sentieri si spostano di notte e le gilde imparano a leggere il vento come una lingua.",
        "description_en": "Soe is one immense living forest. Paths shift by night and guilds learn to read the wind as a language.",
        "theme_tags": ["natura", "foresta", "verde", "vento"],
    },
    {
        "slug": "efreto", "sort_order": 4,
        "name_it": "Efreto", "name_en": "Efreto",
        "domain_it": "Elementi", "domain_en": "Elements",
        "deity_it": "Quattro Voci", "deity_en": "Four Voices",
        "description_it": "Efreto è terra di deserti, fiumi di magma, cime ghiacciate e monsoni perenni. Qui i quattro elementi si combattono e si abbracciano ogni giorno.",
        "description_en": "Efreto is a land of deserts, magma rivers, frozen peaks and perennial monsoons. Here the four elements fight and embrace daily.",
        "theme_tags": ["fuoco", "acqua", "terra", "aria", "elementi"],
    },
    {
        "slug": "irthe", "sort_order": 5,
        "name_it": "Irthe", "name_en": "Irthe",
        "domain_it": "Morte", "domain_en": "Death",
        "deity_it": "Silente Guardiano", "deity_en": "Silent Warden",
        "description_it": "Irthe è il continente delle necropoli affrescate e dei riti al crepuscolo. Non si teme la fine qui: la si onora come inizio.",
        "description_en": "Irthe is the continent of frescoed necropoli and twilight rites. Death is not feared here: it is honoured as beginning.",
        "theme_tags": ["morte", "necropoli", "riti", "silenzio"],
    },
    {
        "slug": "nathos", "sort_order": 6,
        "name_it": "Nathos", "name_en": "Nathos",
        "domain_it": "Vita", "domain_en": "Life",
        "deity_it": "Cuore Verde", "deity_en": "Green Heart",
        "description_it": "Nathos è la culla dei guaritori e delle sorgenti che curano l'anima. I mercati traboccano di frutta impossibile e di canti antichi.",
        "description_en": "Nathos is the cradle of healers and springs that mend the soul. Markets brim with impossible fruit and ancient songs.",
        "theme_tags": ["vita", "guarigione", "mercati", "canto"],
    },
    {
        "slug": "ergolat", "sort_order": 7,
        "name_it": "Ergolat", "name_en": "Ergolat",
        "domain_it": "Vuoto", "domain_en": "Void",
        "deity_it": "Luna Morta", "deity_en": "Dead Moon",
        "description_it": "Ergolat è il continente più temuto: obelischi neri, silenzi anomali, e la Luna Morta che sorride. Qui Alveora tessé i primi fili del vuoto.",
        "description_en": "Ergolat is the most feared continent: black obelisks, uncanny silences and the smiling Dead Moon. Here Alveora wove the first void threads.",
        "theme_tags": ["vuoto", "obelischi", "luna_morta", "alveora"],
    },
    {
        "slug": "aveol", "sort_order": 8,
        "name_it": "Aveol", "name_en": "Aveol",
        "domain_it": "Ordine", "domain_en": "Order",
        "deity_it": "Bilancia Eterna", "deity_en": "Eternal Balance",
        "description_it": "Aveol è la terra delle città geometriche e delle leggi che nessuno può ignorare. I suoi consigli scrivono trattati che regolano gli otto continenti.",
        "description_en": "Aveol is the land of geometric cities and laws none may ignore. Its councils draft treaties that rule all eight continents.",
        "theme_tags": ["ordine", "leggi", "città", "consigli"],
    },
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def seed_world_continents() -> dict:
    """Idempotent seed of 8 continents (upsert on slug)."""
    now_iso = _utc_now().isoformat()
    inserted = 0
    for c in CONTINENTS_SEED:
        r = await db.world_continents.update_one(
            {"slug": c["slug"]},
            {"$setOnInsert": {**c, "is_active": True, "created_at": now_iso}},
            upsert=True,
        )
        if r.upserted_id:
            inserted += 1
    return {"total": len(CONTINENTS_SEED), "inserted": inserted}


async def _emit_audit(event_type: str, actor_guild_id: Optional[str],
                      related_entity_id: str, metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type=event_type, actor_user_id=None,
            actor_guild_id=actor_guild_id, source="world",
            related_entity_id=related_entity_id, metadata=metadata,
        )
    except Exception as exc:
        logger.debug("world.audit_emit skipped %s: %s", event_type, exc)


# ── Access gate ─────────────────────────────────────────────────────
async def has_world_access(guild_id: str) -> tuple[bool, dict]:
    """True if guild has completed >=1 raid (raids.status='completed').

    Decisione documentata: usa `db.raids` (raid endgame) NON `db.expeditions`
    per gate coerente con la lore (il raid è il rito d'accesso al Mondo).
    """
    n = await db.raids.count_documents({
        "guild_id": guild_id, "status": "completed",
    })
    if n >= 1:
        return True, {}
    return False, {
        "reason": "first_raid_required",
        "requirement": "Completa il tuo primo raid per accedere al Mondo di Orbus",
        "cta": "/raids",
    }


async def _get_active_presence(guild_id: str) -> Optional[dict]:
    return await db.guild_world_presence.find_one(
        {"guild_id": guild_id, "status": "active"}, {"_id": 0},
    )


def _public_continent(c: dict) -> dict:
    out = {k: v for k, v in c.items() if not k.startswith("_")}
    out.pop("_id", None)
    return out


def _public_presence(p: dict) -> dict:
    out = {k: v for k, v in p.items() if not k.startswith("_")}
    out.pop("_id", None)
    return out


# ── Pydantic bodies ─────────────────────────────────────────────────
class TogglePayload(BaseModel):
    is_active: bool


# ── PUBLIC ROUTES ───────────────────────────────────────────────────
@router.get("/overview")
async def overview(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, gate = await has_world_access(guild["id"])
    if not has_acc:
        return {"access": False, **gate}
    presence = await _get_active_presence(guild["id"])
    if not presence:
        conts = await db.world_continents.find(
            {"is_active": True}, {"_id": 0},
        ).sort("sort_order", 1).to_list(20)
        return {"access": True, "continent": None,
                "continents_available": [_public_continent(c) for c in conts]}
    cont = await db.world_continents.find_one(
        {"slug": presence["continent_slug"]}, {"_id": 0},
    )
    guilds_in = await db.guild_world_presence.count_documents(
        {"continent_slug": presence["continent_slug"], "status": "active"},
    )
    return {
        "access": True,
        "continent": _public_continent(cont) if cont else None,
        "presence": _public_presence(presence),
        "next_change_available_at": presence.get("next_change_available_at"),
        "guilds_in_continent_count": guilds_in,
    }


@router.get("/continents")
async def list_continents():
    conts = await db.world_continents.find(
        {"is_active": True}, {"_id": 0},
    ).sort("sort_order", 1).to_list(20)
    return {"continents": [_public_continent(c) for c in conts]}


@router.get("/continents/{slug}")
async def get_continent(slug: str):
    c = await db.world_continents.find_one({"slug": slug}, {"_id": 0})
    if not c or not c.get("is_active", True):
        raise HTTPException(404, "continent_not_found_or_inactive")
    return {"continent": _public_continent(c)}


async def _validate_and_get_target(slug: str) -> dict:
    c = await db.world_continents.find_one({"slug": slug}, {"_id": 0})
    if not c:
        raise HTTPException(404, "continent_not_found")
    if not c.get("is_active", True):
        raise HTTPException(409, "continent_inactive")
    return c


@router.post("/continents/{slug}/join")
async def join_continent(slug: str,
                          current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, gate = await has_world_access(guild["id"])
    if not has_acc:
        raise HTTPException(403, gate.get("reason", "access_denied"))
    await _validate_and_get_target(slug)
    existing = await _get_active_presence(guild["id"])
    if existing:
        raise HTTPException(409, "already_has_active_presence")
    now = _utc_now()
    now_iso = now.isoformat()
    next_change = (now + timedelta(days=CHANGE_COOLDOWN_DAYS)).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"], "continent_slug": slug,
        "joined_at": now_iso, "last_changed_at": now_iso,
        "next_change_available_at": next_change,
        "change_count": 0, "status": "active",
        "created_at": now_iso, "updated_at": now_iso,
    }
    # CAS: race safety — no other active presence must exist
    dup = await db.guild_world_presence.find_one(
        {"guild_id": guild["id"], "status": "active"}, {"_id": 0, "id": 1},
    )
    if dup:
        raise HTTPException(409, "race_lost_already_active")
    await db.guild_world_presence.insert_one(doc)
    doc.pop("_id", None)
    # History append (append-only, no hard delete elsewhere)
    await db.guild_world_presence_history.insert_one({
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"], "continent_slug": slug,
        "action": "joined", "at": now_iso, "presence_id": doc["id"],
    })
    await _emit_audit("WORLD_CONTINENT_JOINED", guild["id"], doc["id"],
                      {"continent_slug": slug})
    return {"presence": _public_presence(doc)}


@router.post("/continents/{slug}/change")
async def change_continent(slug: str,
                            current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, gate = await has_world_access(guild["id"])
    if not has_acc:
        raise HTTPException(403, gate.get("reason", "access_denied"))
    target = await _validate_and_get_target(slug)
    existing = await _get_active_presence(guild["id"])
    if not existing:
        raise HTTPException(409, "no_active_presence_to_change")
    if existing["continent_slug"] == slug:
        raise HTTPException(409, "already_in_this_continent")
    now = _utc_now()
    try:
        next_change = datetime.fromisoformat(existing["next_change_available_at"])
    except Exception:
        next_change = now
    if now < next_change:
        raise HTTPException(423, {
            "error": "cooldown_not_expired",
            "next_change_available_at": existing["next_change_available_at"],
        })
    now_iso = now.isoformat()
    new_next = (now + timedelta(days=CHANGE_COOLDOWN_DAYS)).isoformat()
    # CAS flip old → archived (only if still active)
    flipped = await db.guild_world_presence.find_one_and_update(
        {"id": existing["id"], "status": "active"},
        {"$set": {"status": "archived", "archived_at": now_iso,
                  "updated_at": now_iso}},
    )
    if not flipped:
        raise HTTPException(409, "race_lost_on_archive")
    new_doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"], "continent_slug": slug,
        "joined_at": existing["joined_at"], "last_changed_at": now_iso,
        "next_change_available_at": new_next,
        "change_count": int(existing.get("change_count", 0)) + 1,
        "status": "active",
        "created_at": now_iso, "updated_at": now_iso,
    }
    await db.guild_world_presence.insert_one(new_doc)
    new_doc.pop("_id", None)
    await db.guild_world_presence_history.insert_one({
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "continent_slug": slug,
        "from_slug": existing["continent_slug"],
        "action": "changed", "at": now_iso, "presence_id": new_doc["id"],
    })
    await _emit_audit(
        "WORLD_CONTINENT_CHANGED", guild["id"], new_doc["id"],
        {"from": existing["continent_slug"], "to": slug,
         "change_count": new_doc["change_count"]},
    )
    return {"presence": _public_presence(new_doc)}


def _activity_bucket(last_active_iso: Optional[str]) -> str:
    if not last_active_iso:
        return "inactive"
    try:
        last = datetime.fromisoformat(last_active_iso)
    except Exception:
        return "inactive"
    delta = _utc_now() - last
    if delta < timedelta(days=1):
        return "attiva_oggi"
    if delta < timedelta(days=7):
        return "attiva_settimana"
    if delta < timedelta(days=30):
        return "attiva_mese"
    return "inattiva"


@router.get("/neighbors")
async def neighbors(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    has_acc, gate = await has_world_access(guild["id"])
    if not has_acc:
        raise HTTPException(403, gate.get("reason", "access_denied"))
    presence = await _get_active_presence(guild["id"])
    if not presence:
        raise HTTPException(409, "no_active_presence")
    slug = presence["continent_slug"]
    total = await db.guild_world_presence.count_documents(
        {"continent_slug": slug, "status": "active"},
    )
    # 8 peers, excluding self, sorted by joined_at proximity to self.
    self_join = presence.get("joined_at", "")
    peers = await db.guild_world_presence.find(
        {"continent_slug": slug, "status": "active",
         "guild_id": {"$ne": guild["id"]}},
        {"_id": 0, "guild_id": 1, "joined_at": 1},
    ).to_list(200)
    peers.sort(key=lambda p: abs(str(p.get("joined_at", "")).__hash__()
                                    ^ str(self_join).__hash__()))
    peers = peers[:8]
    gids = [p["guild_id"] for p in peers]
    gdocs = await db.guilds.find(
        {"id": {"$in": gids}},
        {"_id": 0, "id": 1, "name": 1, "level": 1,
         "banner_text": 1, "last_active_at": 1, "updated_at": 1},
    ).to_list(20)
    gmap = {g["id"]: g for g in gdocs}
    out = []
    for p in peers:
        g = gmap.get(p["guild_id"], {})
        last_act = g.get("last_active_at") or g.get("updated_at")
        out.append({
            "guild_id": p["guild_id"],
            "name": g.get("name", "?"),
            "level": g.get("level", 1),
            "banner_text": g.get("banner_text", ""),
            "activity": _activity_bucket(last_act),
        })
    return {"total_in_continent": total, "nearby_guilds": out}


# ── ADMIN ROUTES ────────────────────────────────────────────────────
@admin_router.get("/continents-stats")
async def admin_continents_stats(admin: dict = Depends(get_admin_user)):
    cur = db.guild_world_presence.aggregate([
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$continent_slug", "count": {"$sum": 1}}},
    ])
    rows = await cur.to_list(20)
    by_slug = {r["_id"]: r["count"] for r in rows}
    conts = await db.world_continents.find(
        {}, {"_id": 0}).sort("sort_order", 1).to_list(20)
    stats = [{"slug": c["slug"], "name_it": c["name_it"],
              "is_active": c.get("is_active", True),
              "guilds_count": by_slug.get(c["slug"], 0)}
             for c in conts]
    return {"stats": stats,
            "total_guilds_placed": sum(by_slug.values())}


@admin_router.post("/dev/grant-first-raid/{guild_id}")
async def dev_grant_first_raid(guild_id: str,
                                admin: dict = Depends(get_admin_user)):
    """Preview-only utility: inserts a fake completed raid to unlock world access."""
    if os.environ.get("APP_ENV") == "production":
        raise HTTPException(403, "not_available_in_production")
    now_iso = _utc_now().isoformat()
    fake_id = str(uuid.uuid4())
    await db.raids.insert_one({
        "id": fake_id, "guild_id": guild_id,
        "status": "completed",
        "started_at": now_iso, "ends_at": now_iso, "completed_at": now_iso,
        "recovered": False,
        "_dev_first_raid_grant": True,
        "raid_dungeon_slug": "dev_bootstrap",
        "created_at": now_iso, "updated_at": now_iso,
    })
    await _emit_audit(
        "WORLD_ACCESS_GRANTED", guild_id, guild_id,
        {"via": "dev_grant_first_raid", "raid_id": fake_id},
    )
    return {"status": "ok", "raid_id": fake_id}


@admin_router.patch("/continents/{slug}")
async def admin_toggle_continent(slug: str, payload: TogglePayload,
                                  admin: dict = Depends(get_admin_user)):
    r = await db.world_continents.find_one_and_update(
        {"slug": slug},
        {"$set": {"is_active": bool(payload.is_active)}},
        projection={"_id": 0},
    )
    if not r:
        raise HTTPException(404, "continent_not_found")
    r["is_active"] = bool(payload.is_active)
    return {"continent": _public_continent(r)}


__all__ = ["router", "admin_router", "seed_world_continents",
           "has_world_access", "CHANGE_COOLDOWN_DAYS", "CONTINENTS_SEED"]
