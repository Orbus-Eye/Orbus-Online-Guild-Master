"""ROUND 16.3 Phase 8 V1 — Stables services.

Anti-P2W GUARANTEE: this module never writes to guild.gold, guild.reputation,
guild.level, adventurer.stats, guild_pvp_stats, item_instances or any
inventory/economy collection. Only:
    - guild_mount_ownership (ownership rows)
    - narrative_route_completions (one-shot per guild+route)
    - narrative_rewards_unlocked (cosmetic-only badges/titles/lore)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.audit.log import write_audit


logger = logging.getLogger("orbus.stables.services")


STARTER_MOUNT_SLUG = "ronzino-di-strada"
STARTER_QUEST_MIN_LEVEL = 5


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Catalog + ownership helpers ─────────────────────────────────────


async def _list_all_mounts(db) -> list[dict]:
    return await db.mount_catalog.find(
        {"is_active": True}, {"_id": 0},
    ).sort("slug", 1).to_list(200)


async def _get_mount(db, mount_slug: str) -> Optional[dict]:
    return await db.mount_catalog.find_one(
        {"slug": mount_slug, "is_active": True}, {"_id": 0},
    )


async def _my_ownership(db, guild_id: str) -> list[dict]:
    return await db.guild_mount_ownership.find(
        {"guild_id": guild_id}, {"_id": 0},
    ).to_list(200)


async def get_catalog_with_ownership(db, guild_id: str) -> dict:
    mounts = await _list_all_mounts(db)
    owned = await _my_ownership(db, guild_id)
    owned_slugs = {o["mount_slug"] for o in owned}
    active_slug = next(
        (o["mount_slug"] for o in owned if o.get("is_active")), None,
    )
    rows = []
    for m in mounts:
        rows.append({
            **m,
            "is_owned": (m["slug"] in owned_slugs),
            "is_active": (m["slug"] == active_slug),
        })
    return {"mounts": rows, "total": len(rows),
            "active_mount_slug": active_slug}


async def get_my_stable(db, guild_id: str) -> dict:
    owned = await _my_ownership(db, guild_id)
    mounts = await _list_all_mounts(db)
    catalog_by_slug = {m["slug"]: m for m in mounts}
    owned_rows = []
    active_mount = None
    for o in owned:
        cat = catalog_by_slug.get(o["mount_slug"])
        if not cat:
            continue
        row = {**cat, "is_active": bool(o.get("is_active")),
               "acquired_at": o.get("acquired_at"),
               "source_type": o.get("source_type")}
        owned_rows.append(row)
        if o.get("is_active"):
            active_mount = row
    return {"owned": owned_rows, "active_mount": active_mount,
            "total_owned": len(owned_rows)}


# ── Starter quest claim ─────────────────────────────────────────────


async def claim_starter_mount(db, guild: dict) -> dict:
    if int(guild.get("level") or 0) < STARTER_QUEST_MIN_LEVEL:
        # Fallback gate: world presence unlocked also counts as "ready".
        pres = await db.guild_world_presence.find_one(
            {"guild_id": guild["id"], "status": "active"}, {"_id": 0, "id": 1},
        )
        if pres is None:
            raise HTTPException(
                status_code=403,
                detail={"code": "stables.starter_gate",
                        "user_message":
                        "Devi raggiungere il livello 5 o sbloccare "
                        "una presenza continentale per ottenere la "
                        "cavalcatura iniziale.",
                        "current_level": int(guild.get("level") or 0),
                        "required_level": STARTER_QUEST_MIN_LEVEL},
            )
    # Idempotent claim via unique index (guild_id, mount_slug).
    doc = {
        "id": str(uuid.uuid4()), "guild_id": guild["id"],
        "mount_slug": STARTER_MOUNT_SLUG, "is_active": False,
        "acquired_at": _now_iso(), "source_type": "starter_quest",
        "source_ref": "starter_quest_v1",
    }
    try:
        await db.guild_mount_ownership.insert_one({**doc})
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail={"code": "stables.starter_already_claimed",
                    "user_message":
                    "Hai già ottenuto la cavalcatura iniziale."},
        )
    await write_audit(
        db, event_type="MOUNT_STARTER_CLAIMED",
        actor_guild_id=guild["id"],
        related_entity_id=STARTER_MOUNT_SLUG, source="stables",
        metadata={"mount_slug": STARTER_MOUNT_SLUG},
    )
    return {"acquired": True, "mount_slug": STARTER_MOUNT_SLUG}


# ── Set active mount (CAS unset old, set new) ───────────────────────


async def set_active_mount(db, guild: dict, mount_slug: str) -> dict:
    row = await db.guild_mount_ownership.find_one(
        {"guild_id": guild["id"], "mount_slug": mount_slug},
        {"_id": 0, "id": 1},
    )
    if not row:
        raise HTTPException(
            status_code=403,
            detail={"code": "stables.not_owned",
                    "user_message":
                    "Non possiedi questa cavalcatura."},
        )
    # Unset previous active(s) then set new.
    await db.guild_mount_ownership.update_many(
        {"guild_id": guild["id"], "is_active": True},
        {"$set": {"is_active": False}},
    )
    await db.guild_mount_ownership.update_one(
        {"guild_id": guild["id"], "mount_slug": mount_slug},
        {"$set": {"is_active": True}},
    )
    await write_audit(
        db, event_type="MOUNT_ACTIVE_SET",
        actor_guild_id=guild["id"],
        related_entity_id=mount_slug, source="stables",
        metadata={"mount_slug": mount_slug},
    )
    return {"active_mount_slug": mount_slug}


# ── Narrative routes (one-shot cosmetic reward) ─────────────────────


async def list_narrative_routes(db, guild: dict) -> dict:
    routes = await db.narrative_routes.find(
        {"is_active": True}, {"_id": 0},
    ).sort("slug", 1).to_list(50)
    completions = await db.narrative_route_completions.find(
        {"guild_id": guild["id"]}, {"_id": 0, "route_slug": 1},
    ).to_list(100)
    completed = {c["route_slug"] for c in completions}
    owned = await _my_ownership(db, guild["id"])
    owned_slugs = {o["mount_slug"] for o in owned}
    # Domain lookup from catalog.
    mounts = await _list_all_mounts(db)
    slug_to_domain = {m["slug"]: m["domain_slug"] for m in mounts}
    owned_domains = {slug_to_domain.get(s) for s in owned_slugs
                     if slug_to_domain.get(s)}
    rows = []
    for r in routes:
        required = set(r.get("required_mount_domains") or [])
        can = bool(required & owned_domains) if required else True
        missing = None
        if not can:
            missing = ("Serve una cavalcatura di uno di questi domini: "
                       + ", ".join(sorted(required)))
        rows.append({
            **r,
            "is_completed": (r["slug"] in completed),
            "can_travel": can and (r["slug"] not in completed),
            "missing_reason": missing if not can else None,
        })
    return {"routes": rows, "total": len(rows)}


async def travel_narrative_route(db, guild: dict, route_slug: str) -> dict:
    route = await db.narrative_routes.find_one(
        {"slug": route_slug, "is_active": True}, {"_id": 0},
    )
    if not route:
        raise HTTPException(
            status_code=404,
            detail={"code": "stables.route_not_found",
                    "user_message": "Rotta narrativa non trovata."},
        )
    # Check ownership of a compatible domain mount.
    required = set(route.get("required_mount_domains") or [])
    owned = await _my_ownership(db, guild["id"])
    if not owned:
        raise HTTPException(
            status_code=403,
            detail={"code": "stables.mount_required",
                    "user_message":
                    "Serve una cavalcatura compatibile per percorrere "
                    "questa rotta."},
        )
    mounts = await _list_all_mounts(db)
    slug_to_domain = {m["slug"]: m["domain_slug"] for m in mounts}
    mount_used = None
    for o in owned:
        dom = slug_to_domain.get(o["mount_slug"])
        if not required or dom in required:
            mount_used = o["mount_slug"]
            break
    if mount_used is None:
        raise HTTPException(
            status_code=403,
            detail={"code": "stables.wrong_domain",
                    "user_message":
                    "Nessuna delle tue cavalcature appartiene al dominio "
                    "richiesto per questa rotta."},
        )
    now = _now_iso()
    completion = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"], "route_slug": route_slug,
        "mount_slug_used": mount_used,
        "reward_slug_granted": route["reward_slug"],
        "completed_at": now,
    }
    try:
        await db.narrative_route_completions.insert_one({**completion})
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail={"code": "stables.route_already_completed",
                    "user_message":
                    "Hai già percorso questa rotta narrativa."},
        )
    # Grant the cosmetic-only reward (idempotent).
    reward_doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "reward_slug": route["reward_slug"],
        "reward_type": route["reward_type"],
        "reward_name_it": route.get("reward_name_it") or route["reward_slug"],
        "reward_description_it": route.get("reward_description_it") or "",
        "source_route_slug": route_slug,
        "unlocked_at": now,
    }
    try:
        await db.narrative_rewards_unlocked.insert_one({**reward_doc})
    except DuplicateKeyError:
        pass  # already unlocked (very unlikely given per-route unique)
    await write_audit(
        db, event_type="NARRATIVE_ROUTE_TRAVELED",
        actor_guild_id=guild["id"],
        related_entity_id=route_slug, source="stables",
        metadata={"route_slug": route_slug, "mount_slug_used": mount_used,
                  "reward_slug": route["reward_slug"],
                  "reward_type": route["reward_type"]},
    )
    return {"traveled": True, "route_slug": route_slug,
            "mount_slug_used": mount_used,
            "reward_slug": route["reward_slug"],
            "reward_name_it": route.get("reward_name_it"),
            "reward_type": route["reward_type"]}


async def list_narrative_rewards_mine(db, guild_id: str) -> dict:
    rows = await db.narrative_rewards_unlocked.find(
        {"guild_id": guild_id}, {"_id": 0},
    ).sort("unlocked_at", -1).to_list(200)
    return {"guild_id": guild_id, "total": len(rows), "rewards": rows}


# ── Admin grant (dev-only) ──────────────────────────────────────────


async def admin_grant_mount(db, guild_id: str, mount_slug: str) -> dict:
    mount = await _get_mount(db, mount_slug)
    if not mount:
        raise HTTPException(
            status_code=404,
            detail={"code": "stables.mount_not_found",
                    "user_message": "Cavalcatura non trovata."},
        )
    doc = {
        "id": str(uuid.uuid4()), "guild_id": guild_id,
        "mount_slug": mount_slug, "is_active": False,
        "acquired_at": _now_iso(),
        "source_type": "admin_grant",
        "source_ref": "admin_grant_dev",
    }
    try:
        await db.guild_mount_ownership.insert_one({**doc})
    except DuplicateKeyError:
        return {"granted": False, "reason": "already_owned"}
    await write_audit(
        db, event_type="MOUNT_ACQUIRED",
        actor_guild_id=guild_id,
        related_entity_id=mount_slug, source="stables",
        metadata={"mount_slug": mount_slug, "source_type": "admin_grant"},
    )
    return {"granted": True, "mount_slug": mount_slug}


__all__ = [
    "STARTER_MOUNT_SLUG", "STARTER_QUEST_MIN_LEVEL",
    "get_catalog_with_ownership", "get_my_stable",
    "claim_starter_mount", "set_active_mount",
    "list_narrative_routes", "travel_narrative_route",
    "list_narrative_rewards_mine",
    "admin_grant_mount",
]
