"""ROUND 16.5.1 B.2 — Admin Tester Tools.

Guard-rail rinforzati:
1. Admin-only (get_admin_user)
2. Target user con `is_test_user=True` OR email `@orbus.test`
3. `APP_ENV in ("development","preview")` OR `ENABLE_TESTER_TOOLS=true`
4. Snapshot pre-modifica salvato in `tester_tool_snapshots` collection
5. Audit `TESTER_TOOL_INVOKED` / `TESTER_TOOL_REJECTED` su ogni chiamata
6. Idempotenza: grant-adventurers non duplica; set-max/set-min chiedono
   `confirm=True` se ripetuti sullo stesso account entro 60 secondi.

Endpoint (tutti sotto `/api/admin/tester-tools`):
- GET  /status
- POST /grant-adventurers
- POST /set-max
- POST /set-min
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_admin_user

logger = logging.getLogger("orbus.tester_tools")

router = APIRouter(prefix="/api/admin/tester-tools",
                   tags=["admin", "tester-tools"])


# ═════════════════════════════════════════════════════════════════════
# Guard-rails
# ═════════════════════════════════════════════════════════════════════

def _tools_enabled() -> bool:
    """`APP_ENV in dev/preview` OR flag `ENABLE_TESTER_TOOLS=true`."""
    if os.environ.get("ENABLE_TESTER_TOOLS", "").lower() == "true":
        return True
    return os.environ.get("APP_ENV", "").lower() in (
        "development", "preview", "test", "dev",
    )


def _is_test_user(user: dict) -> bool:
    if user.get("is_test_user") is True:
        return True
    email = (user.get("email") or "").lower()
    return email.endswith("@orbus.test")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _emit_audit(event_type: str, admin_id: str,
                      target_user_id: Optional[str],
                      metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type=event_type, actor_user_id=admin_id,
            actor_guild_id=None, source="tester_tools",
            related_entity_id=target_user_id, metadata=metadata,
        )
    except Exception as exc:
        logger.debug("tester_tools.audit skipped %s: %s", event_type, exc)


async def _resolve_target_user(target_email: str, admin: dict) -> dict:
    """Trova l'utente target + verifica che sia un test user."""
    if not _tools_enabled():
        raise HTTPException(
            403, "tester_tools_disabled_in_this_environment",
        )
    user = await db.users.find_one(
        {"email": target_email.lower()}, {"_id": 0},
    )
    if not user:
        await _emit_audit(
            "TESTER_TOOL_REJECTED", admin.get("id"), None,
            {"reason": "target_not_found", "target_email": target_email},
        )
        raise HTTPException(404, "target_user_not_found")
    if not _is_test_user(user):
        await _emit_audit(
            "TESTER_TOOL_REJECTED", admin.get("id"), user.get("id"),
            {"reason": "not_a_test_user",
             "target_email": target_email},
        )
        raise HTTPException(
            403, "target_is_not_a_test_user_refusing_operation",
        )
    return user


async def _snapshot_state(user_id: str, guild_id: Optional[str],
                          reason: str) -> str:
    """Snapshot completo dello stato pre-modifica in collection
    dedicata. Ritorna lo snapshot_id."""
    snap_id = str(uuid.uuid4())
    guild = None
    advs = []
    if guild_id:
        guild = await db.guilds.find_one({"id": guild_id}, {"_id": 0})
        advs = await db.adventurers.find(
            {"guild_id": guild_id}, {"_id": 0},
        ).to_list(500)
    doc = {
        "id": snap_id,
        "target_user_id": user_id,
        "guild_id": guild_id,
        "reason": reason,
        "created_at": _now_iso(),
        "guild_snapshot": guild,
        "adventurer_count": len(advs),
        "adventurer_ids": [a.get("id") for a in advs],
    }
    await db.tester_tool_snapshots.insert_one(doc)
    return snap_id


async def _recent_invocation_within(user_id: str, tool: str,
                                    seconds: int = 60) -> bool:
    """Verifica se lo stesso tool è stato invocato sullo stesso utente
    negli ultimi N secondi (per l'idempotency check)."""
    since = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    since_iso = since.isoformat()
    prev = await db.tester_tool_snapshots.find_one(
        {"target_user_id": user_id, "reason": tool,
         "created_at": {"$gte": since_iso}},
        {"_id": 0, "id": 1},
    )
    return prev is not None


# ═════════════════════════════════════════════════════════════════════
# Endpoints
# ═════════════════════════════════════════════════════════════════════

class TargetIn(BaseModel):
    target_email: str
    confirm: bool = Field(default=False,
                          description="Richiesto se recent invocation")


@router.get("/status")
async def status(target_email: str,
                 admin: dict = Depends(get_admin_user)):
    """Stato test-user: guild, oro, roster, unlocks."""
    user = await _resolve_target_user(target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    adv_count = 0
    if guild:
        adv_count = await db.adventurers.count_documents(
            {"guild_id": guild["id"],
             "$and": [{"is_retired": {"$ne": True}},
                      {"retired": {"$ne": True}}]},
        )
    return {
        "target_user": {"id": user.get("id"),
                        "email": user.get("email"),
                        "is_test_user": _is_test_user(user)},
        "guild": {"id": guild.get("id") if guild else None,
                  "name": guild.get("name") if guild else None,
                  "level": guild.get("level", 1) if guild else None,
                  "gold": guild.get("gold", 0) if guild else None,
                  "max_team_power_ever": (
                      guild.get("max_team_power_ever", 0) if guild else 0
                  )},
        "roster": {"active_count": adv_count},
        "tools_enabled": _tools_enabled(),
        "env": os.environ.get("APP_ENV", "?"),
    }


async def _resolve_class_map(db) -> dict[str, str]:
    """Ritorna dict class_slug (lowercase) → adventurer_class_id.
    Cache O(1) lookup per grant-adventurers."""
    docs = await db.adventurer_classes.find(
        {"is_active": {"$ne": False}}, {"_id": 0, "id": 1, "slug": 1},
    ).to_list(50)
    return {d["slug"].lower(): d["id"] for d in docs if d.get("id")}


@router.post("/grant-adventurers")
async def grant_adventurers(body: TargetIn,
                            admin: dict = Depends(get_admin_user)):
    """Idempotente: crea avv extra fino a raggiungere 20 attivi (roster
    tipico per raid 5x4). NON duplica se ne ha già >= 20."""
    user = await _resolve_target_user(body.target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    if not guild:
        raise HTTPException(409, "target_has_no_guild")
    guild_id = guild["id"]
    now = _now_iso()
    current = await db.adventurers.count_documents(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True}},
    )
    target_count = 20
    to_create = max(0, target_count - current)
    snap_id = await _snapshot_state(
        user["id"], guild_id, "grant-adventurers",
    )
    # ROUND 16.5.1 BUG#3 fix — resolve class_id da adventurer_classes
    # (era omesso in R16.5.1 iniziale → adventurer_public() esplodeva
    # con KeyError su list_adventurers_for_guild).
    class_map = await _resolve_class_map(db)
    created = []
    _CLASSES = [("warrior", "Tank"), ("rogue", "DPS"),
                ("priest", "Healer"), ("mage", "DPS"),
                ("ranger", "DPS")]
    for i in range(to_create):
        cls_slug, cls_role = _CLASSES[i % len(_CLASSES)]
        class_id = class_map.get(cls_slug)
        if not class_id:  # fallback: prendi la prima classe attiva
            class_id = next(iter(class_map.values()), None)
        adv_id = str(uuid.uuid4())
        doc = {
            "id": adv_id, "guild_id": guild_id,
            "name": f"TesterAdv-{current + i + 1}",
            "level": 5, "experience": 0,
            "is_available": True, "is_retired": False,
            "retired": False, "archived": False, "frozen": False,
            "is_test_artifact": True,
            # Schema legittimo — deve superare adventurer_public()
            "adventurer_class_id": class_id,
            "class_name": cls_slug.capitalize(),
            "class_role": cls_role,
            "class": cls_slug.capitalize(),
            "role": cls_role,
            "rarity": "common",
            "is_starter": False,
            "morale": 100, "stamina": 100,
            "strength": 15, "agility": 10, "intellect": 8,
            "endurance": 12, "faith": 6,
            "stats": {"strength": 15, "agility": 10, "intellect": 8,
                      "endurance": 12, "faith": 6},
            "team_power": 55, "traits": [],
            "created_at": now, "updated_at": now,
        }
        await db.adventurers.insert_one(doc)
        created.append(adv_id)
    await _emit_audit(
        "TESTER_TOOL_INVOKED", admin.get("id"), user["id"],
        {"tool": "grant-adventurers", "created": len(created),
         "already_existed": current, "snapshot_id": snap_id},
    )
    return {
        "created": len(created),
        "already_existed": current,
        "total_after": current + len(created),
        "snapshot_id": snap_id,
    }


@router.post("/set-max")
async def set_max(body: TargetIn,
                  admin: dict = Depends(get_admin_user)):
    """Porta l'account a stato MAX: guild lv 15, oro 100k, roster 20
    lv 10, unlock avanzati (via max_team_power_ever alto)."""
    user = await _resolve_target_user(body.target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    if not guild:
        raise HTTPException(409, "target_has_no_guild")
    if await _recent_invocation_within(user["id"], "set-max", 60):
        if not body.confirm:
            raise HTTPException(
                409, "recent_invocation_within_60s_require_confirm",
            )
    guild_id = guild["id"]
    snap_id = await _snapshot_state(user["id"], guild_id, "set-max")
    now = _now_iso()
    await db.guilds.update_one(
        {"id": guild_id},
        {"$set": {"level": 15, "gold": 100000,
                  "max_team_power_ever": 999,
                  "reputation": 1000, "updated_at": now}},
    )
    # ROUND 16.5.1 BUG#4 fix — Set MAX deve anche unlockare le strutture
    # necessarie per i sistemi (raid richiede war_room lv 2+). Aggiungiamo
    # bump per tutte le strutture ai valori "MAX" ragionevoli.
    await db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "structures.dormitories.level": 10,
            "structures.dormitories.is_unlocked": True,
            "structures.war_room.level": 5,
            "structures.war_room.is_unlocked": True,
            "structures.training_grounds.level": 5,
            "structures.training_grounds.is_unlocked": True,
            "structures.forge.level": 5,
            "structures.forge.is_unlocked": True,
            "structures.market.level": 5,
            "structures.market.is_unlocked": True,
            "structures.library.level": 5,
            "structures.library.is_unlocked": True,
            "updated_at": now,
        }},
    )
    # Roster: garantisci 20 avv lv 10 attivi
    await db.adventurers.update_many(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True}},
        {"$set": {"level": 10, "is_available": True,
                  "updated_at": now}},
    )
    active = await db.adventurers.count_documents(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True}},
    )
    # Se meno di 20 → chiamo grant idempotente
    if active < 20:
        for _ in range(20 - active):
            await db.adventurers.insert_one({
                "id": str(uuid.uuid4()), "guild_id": guild_id,
                "name": f"MaxAdv-{uuid.uuid4().hex[:6]}",
                "level": 10, "is_available": True,
                "is_retired": False, "retired": False,
                "archived": False, "frozen": False,
                "is_test_artifact": True,
                "class_name": "Warrior", "class_role": "Tank",
                "class": "Warrior", "role": "Tank",
                "strength": 25, "agility": 15, "intellect": 15,
                "endurance": 20, "faith": 10, "team_power": 85,
                "traits": [], "created_at": now, "updated_at": now,
            })
    await _emit_audit(
        "TESTER_TOOL_INVOKED", admin.get("id"), user["id"],
        {"tool": "set-max", "snapshot_id": snap_id},
    )
    return {"applied": "MAX", "snapshot_id": snap_id, "guild_id": guild_id}


@router.post("/set-min")
async def set_min(body: TargetIn,
                  admin: dict = Depends(get_admin_user)):
    """Porta l'account a stato MIN: guild lv 1, oro 100, archivia
    avventurieri in eccesso (mantiene 3 attivi lv 1). NO hard delete —
    solo `is_retired=True` + snapshot per rollback."""
    user = await _resolve_target_user(body.target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    if not guild:
        raise HTTPException(409, "target_has_no_guild")
    if await _recent_invocation_within(user["id"], "set-min", 60):
        if not body.confirm:
            raise HTTPException(
                409, "recent_invocation_within_60s_require_confirm",
            )
    guild_id = guild["id"]
    snap_id = await _snapshot_state(user["id"], guild_id, "set-min")
    now = _now_iso()
    await db.guilds.update_one(
        {"id": guild_id},
        {"$set": {"level": 1, "gold": 100,
                  "max_team_power_ever": 0, "reputation": 0,
                  "updated_at": now}},
    )
    # Archivia (soft-retire) tutti tranne i primi 3 attivi
    advs = await db.adventurers.find(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True}},
        {"_id": 0, "id": 1},
    ).sort("created_at", 1).to_list(200)
    keep = advs[:3]
    archive = advs[3:]
    keep_ids = [a["id"] for a in keep]
    if keep_ids:
        await db.adventurers.update_many(
            {"id": {"$in": keep_ids}},
            {"$set": {"level": 1, "experience": 0,
                      "is_available": True, "updated_at": now}},
        )
    archived_count = 0
    if archive:
        r = await db.adventurers.update_many(
            {"id": {"$in": [a["id"] for a in archive]}},
            {"$set": {"is_retired": True, "retired": True,
                      "archived_by_tester_tool": True,
                      "updated_at": now}},
        )
        archived_count = r.modified_count
    await _emit_audit(
        "TESTER_TOOL_INVOKED", admin.get("id"), user["id"],
        {"tool": "set-min", "archived": archived_count,
         "kept_active": len(keep_ids), "snapshot_id": snap_id},
    )
    return {"applied": "MIN", "archived": archived_count,
            "kept_active": len(keep_ids), "snapshot_id": snap_id}


__all__ = ["router"]
