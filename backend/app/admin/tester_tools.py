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
- GET  /smoke-matrix
- GET  /vertical-slice
- POST /grant-adventurers
- POST /set-max
- POST /set-min
- POST /reset-class-hall-journey
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.adventurers.classless import is_explicit_classless_recruit
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.admin.tester_journey import (
    build_classless_tester_adventurer,
    build_tester_smoke_matrix,
    build_tester_vertical_slice,
    release_tester_equipment,
    reset_tester_class_hall_journey,
)
from app.admin.tester_release import (
    T8_CHECKLIST_KEYS,
    build_t8_release_readiness,
)
from app.core.database import db
from app.core.security import get_admin_user
from app.territory.structures import (
    STRUCTURE_CATALOG,
    default_structures_doc,
)

logger = logging.getLogger("orbus.tester_tools")

router = APIRouter(prefix="/api/admin/tester-tools",
                   tags=["admin", "tester-tools"])
TESTER_FULL_ROSTER_SIZE = 39
TESTER_MIN_ROSTER_SIZE = 3


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


class GrantAdventurersIn(TargetIn):
    target_count: int = Field(
        default=20,
        ge=5,
        le=50,
        description=(
            "Rosa tester desiderata. Il valore 20 prepara un raid; "
            "27 copre tutte le Class Hall; 33 aggiunge sei supporti "
            "non risonanti; 39 prepara due squadre supporto indipendenti "
            "per i dungeon da sette e il confronto controllato."
        ),
    )


class TesterReleaseChecklistIn(TargetIn):
    desktop_navigation: bool = False
    mobile_navigation: bool = False
    classless_hall_journey: bool = False
    item_lore_and_sources: bool = False
    dungeon_and_raid_reports: bool = False
    reset_repeatability: bool = False
    notes: str = Field(default="", max_length=2000)


@router.get("/status")
async def status(target_email: str,
                 admin: dict = Depends(get_admin_user)):
    """Stato test-user: guild, oro, roster e stato della scelta di classe."""
    user = await _resolve_target_user(target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    active_adventurers = []
    if guild:
        active_adventurers = await db.adventurers.find(
            {
                "guild_id": guild["id"],
                "is_retired": {"$ne": True},
                "retired": {"$ne": True},
                "archived": {"$ne": True},
            },
            {"_id": 0},
        ).to_list(500)
    classless_count = sum(
        is_explicit_classless_recruit(adventurer)
        for adventurer in active_adventurers
    )
    assigned_count = sum(
        bool(
            adventurer.get("class_hall_id")
            and adventurer.get("canonical_class_slug")
        )
        for adventurer in active_adventurers
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
        "roster": {
            "active_count": len(active_adventurers),
            "classless_count": classless_count,
            "assigned_count": assigned_count,
            "invalid_class_state_count": (
                len(active_adventurers) - classless_count - assigned_count
            ),
        },
        "tools_enabled": _tools_enabled(),
        "env": os.environ.get("APP_ENV", "?"),
    }


@router.get("/smoke-matrix")
async def smoke_matrix(target_email: str,
                       admin: dict = Depends(get_admin_user)):
    """Matrice read-only della slice tester e della roadmap item-first."""
    user = await _resolve_target_user(target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    return await build_tester_smoke_matrix(db, user=user, guild=guild)


@router.get("/vertical-slice")
async def vertical_slice(target_email: str,
                         admin: dict = Depends(get_admin_user)):
    """Telemetria read-only Hall → item → dungeon → raid → nuova build."""
    user = await _resolve_target_user(target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    return await build_tester_vertical_slice(db, user=user, guild=guild)


@router.get("/release-readiness")
async def release_readiness(
    target_email: str,
    admin: dict = Depends(get_admin_user),
):
    """T8 gate: regressione automatica + checklist umana desktop/mobile."""
    user = await _resolve_target_user(target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]},
        {"_id": 0},
    )
    vertical = await build_tester_vertical_slice(
        db,
        user=user,
        guild=guild,
    )
    return await build_t8_release_readiness(
        db,
        user=user,
        guild=guild,
        vertical_slice=vertical,
    )


@router.post("/release-checklist")
async def save_release_checklist(
    body: TesterReleaseChecklistIn,
    admin: dict = Depends(get_admin_user),
):
    """Record an explicit human T8 check without authorizing deployment."""
    user = await _resolve_target_user(body.target_email, admin)
    now = _now_iso()
    checks = {
        key: bool(getattr(body, key))
        for key in T8_CHECKLIST_KEYS
    }
    doc = {
        "id": str(uuid.uuid4()),
        "target_user_id": user["id"],
        "target_email": user.get("email"),
        **checks,
        "notes": body.notes.strip(),
        "recorded_at": now,
        "recorded_by_user_id": admin.get("id"),
        "class_sets_included": False,
        "deployment_authorized": False,
    }
    await db.tester_release_checklists.insert_one(doc)
    await _emit_audit(
        "TESTER_RELEASE_CHECKLIST_RECORDED",
        admin.get("id"),
        user.get("id"),
        {
            "completed_count": sum(checks.values()),
            "required_count": len(T8_CHECKLIST_KEYS),
            "deployment_authorized": False,
        },
    )
    return {
        "recorded": True,
        "completed": all(checks.values()),
        "completed_count": sum(checks.values()),
        "required_count": len(T8_CHECKLIST_KEYS),
        "recorded_at": now,
        "deployment_authorized": False,
    }


async def _tester_trait_pool() -> list[dict]:
    traits = await db.adventurer_traits.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    ).to_list(500)
    if traits:
        return traits
    return await db.traits.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    ).to_list(500)


@router.post("/grant-adventurers")
async def grant_adventurers(body: GrantAdventurersIn,
                            admin: dict = Depends(get_admin_user)):
    """Crea una rosa tester fino al numero richiesto di avventurieri attivi.

    Ogni nuova recluta resta senza classe finché il tester non sceglie
    esplicitamente una Class Hall. Chiamate ripetute non duplicano reclute
    oltre il target richiesto.
    """
    user = await _resolve_target_user(body.target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    if not guild:
        raise HTTPException(409, "target_has_no_guild")
    guild_id = guild["id"]
    current = await db.adventurers.count_documents(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True},
         "archived": {"$ne": True}},
    )
    target_count = body.target_count
    to_create = max(0, target_count - current)
    snap_id = await _snapshot_state(
        user["id"], guild_id, "grant-adventurers",
    )
    traits_pool = await _tester_trait_pool()
    created = []
    for _ in range(to_create):
        doc = build_classless_tester_adventurer(
            guild_id,
            traits_pool=traits_pool,
            level=5,
            extra={"tester_grant_source": "grant-adventurers"},
        )
        await db.adventurers.insert_one(doc)
        created.append(doc["id"])
    await _emit_audit(
        "TESTER_TOOL_INVOKED", admin.get("id"), user["id"],
        {"tool": "grant-adventurers", "created": len(created),
         "already_existed": current, "snapshot_id": snap_id},
    )
    return {
        "created": len(created),
        "already_existed": current,
        "total_after": current + len(created),
        "target_count": target_count,
        "snapshot_id": snap_id,
        "class_selection_required": True,
    }


@router.post("/reset-class-hall-journey")
async def reset_class_hall_journey(
    body: TargetIn,
    admin: dict = Depends(get_admin_user),
):
    """Crea un viaggio pulito preservando account, gilda e storico."""
    if body.confirm is not True:
        raise HTTPException(
            400,
            {
                "code": "tester_journey.explicit_confirmation_required",
                "user_message": (
                    "Conferma esplicitamente la creazione di un nuovo "
                    "viaggio tester."
                ),
            },
        )
    user = await _resolve_target_user(body.target_email, admin)
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0},
    )
    if not guild:
        raise HTTPException(409, "target_has_no_guild")
    snap_id = await _snapshot_state(
        user["id"],
        guild["id"],
        "reset-class-hall-journey",
    )
    result = await reset_tester_class_hall_journey(
        db,
        user=user,
        guild=guild,
        snapshot_id=snap_id,
    )
    await _emit_audit(
        "TESTER_TOOL_INVOKED",
        admin.get("id"),
        user["id"],
        {
            "tool": "reset-class-hall-journey",
            "snapshot_id": snap_id,
            "reset_id": result["reset_id"],
            "archived_adventurers": result["archived_adventurers"],
            "created_classless_adventurers": (
                result["created_classless_adventurers"]
            ),
        },
    )
    return result


@router.post("/set-max")
async def set_max(body: TargetIn,
                   admin: dict = Depends(get_admin_user)):
    """Porta l'account a stato MAX per la copertura T5 completa."""
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
                  "max_team_power_ever": 9999,
                  "reputation": 1000, "updated_at": now}},
    )
    structure_updates = {
        f"structures.{slug}.level": int(meta["max_level"])
        for slug, meta in STRUCTURE_CATALOG.items()
    }
    structure_updates.update(
        {
            f"structures.{slug}.is_unlocked": True
            for slug in STRUCTURE_CATALOG
        }
    )
    structure_updates["updated_at"] = now
    await db.guild_structures.update_one(
        {"guild_id": guild_id},
        {
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "created_at": now,
            },
            "$set": structure_updates,
        },
        upsert=True,
    )
    # Roster: 27 classi + due squadre indipendenti di quattro supporti.
    await db.adventurers.update_many(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True},
         "archived": {"$ne": True}},
        {"$set": {"level": ADVENTURER_MAX_LEVEL, "experience": 0,
                  "is_available": True,
                  "updated_at": now}},
    )
    active = await db.adventurers.count_documents(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True},
         "archived": {"$ne": True}},
    )
    # Se meno di 20, aggiunge reclute senza classe: anche nello stato MAX
    # la scelta della Hall resta sempre un'azione esplicita del tester.
    if active < TESTER_FULL_ROSTER_SIZE:
        traits_pool = await _tester_trait_pool()
        docs = [
            build_classless_tester_adventurer(
                guild_id,
                traits_pool=traits_pool,
                level=ADVENTURER_MAX_LEVEL,
                extra={"tester_grant_source": "set-max"},
            )
            for _ in range(TESTER_FULL_ROSTER_SIZE - active)
        ]
        if docs:
            await db.adventurers.insert_many(docs)
    await _emit_audit(
        "TESTER_TOOL_INVOKED", admin.get("id"), user["id"],
        {"tool": "set-max", "snapshot_id": snap_id},
    )
    return {
        "applied": "MAX",
        "snapshot_id": snap_id,
        "guild_id": guild_id,
        "active_roster": max(active, TESTER_FULL_ROSTER_SIZE),
        "class_selection_required": True,
    }


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
    # Ripristina anche le strutture: MIN non deve conservare sblocchi MAX.
    await db.guild_structures.update_one(
        {"guild_id": guild_id},
        {
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "created_at": now,
            },
            "$set": {
                "structures": default_structures_doc(),
                "updated_at": now,
            },
        },
        upsert=True,
    )
    # Archivia (soft-retire) tutti tranne i primi tre attivi.
    advs = await db.adventurers.find(
        {"guild_id": guild_id,
         "is_retired": {"$ne": True}, "retired": {"$ne": True},
         "archived": {"$ne": True}},
        {"_id": 0, "id": 1},
    ).sort("created_at", 1).to_list(200)
    keep = advs[:TESTER_MIN_ROSTER_SIZE]
    archive = advs[TESTER_MIN_ROSTER_SIZE:]
    keep_ids = [a["id"] for a in keep]
    if keep_ids:
        await db.adventurers.update_many(
            {"id": {"$in": keep_ids}},
            {"$set": {"level": 1, "experience": 0,
                      "is_available": True, "is_retired": False,
                      "retired": False, "archived": False,
                      "updated_at": now}},
        )
    archived_count = 0
    equipment_released = 0
    if archive:
        archive_ids = [a["id"] for a in archive]
        equipment_released = await release_tester_equipment(
            db,
            guild_id=guild_id,
            adventurer_ids=archive_ids,
        )
        r = await db.adventurers.update_many(
            {"guild_id": guild_id, "id": {"$in": archive_ids}},
            {"$set": {"is_retired": True, "retired": True,
                      "archived": True, "is_available": False,
                      "archived_by_tester_tool": True,
                      "updated_at": now}},
        )
        archived_count = r.modified_count
    created = 0
    if len(keep_ids) < TESTER_MIN_ROSTER_SIZE:
        traits_pool = await _tester_trait_pool()
        docs = [
            build_classless_tester_adventurer(
                guild_id,
                traits_pool=traits_pool,
                level=1,
                extra={"tester_grant_source": "set-min"},
            )
            for _ in range(TESTER_MIN_ROSTER_SIZE - len(keep_ids))
        ]
        if docs:
            await db.adventurers.insert_many(docs)
            created = len(docs)
    await _emit_audit(
        "TESTER_TOOL_INVOKED", admin.get("id"), user["id"],
        {"tool": "set-min", "archived": archived_count,
         "kept_active": len(keep_ids), "created": created,
         "equipment_released": equipment_released,
         "snapshot_id": snap_id},
    )
    return {"applied": "MIN", "archived": archived_count,
            "kept_active": len(keep_ids), "created": created,
            "active_roster": len(keep_ids) + created,
            "equipment_released": equipment_released,
            "snapshot_id": snap_id}


__all__ = ["router"]
