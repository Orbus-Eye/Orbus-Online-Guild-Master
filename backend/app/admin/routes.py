"""Admin routes (Phase 5.5f).

Mounted under prefix `/api/admin`. All 16 endpoints require an admin bearer
token via `Depends(get_admin_user)`. Endpoint paths, payloads, validation
order and status codes are byte-identical with the previous inline impl in
`server.py`.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.adventurers.services import class_public, trait_public
from app.admin.services import (
    VALID_AFFECTED_STAT,
    VALID_ITEM_TYPES,
    VALID_RARITIES,
    VALID_ROLES,
    _build_item_doc,
    _slug_ok,
    _strip_db_fields,
    utc_now,
    validate_item_monetization,
)
from app.core.database import db
from app.core.security import get_admin_user
from app.dungeons.services import dungeon_public
from app.items.services import item_public


router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── Admin: Classes ───────────────────────────────────────────────────────────
@router.get("/classes")
async def admin_list_classes(_: dict = Depends(get_admin_user)):
    rows = await db.adventurer_classes.find({}, {"_id": 0}).sort("name", ASCENDING).to_list(200)
    return {"classes": [class_public(r) for r in rows]}


@router.post("/classes", status_code=201)
async def admin_create_class(payload: dict, _: dict = Depends(get_admin_user)):
    required = ["name", "slug", "role", "base_strength", "base_agility",
                "base_intellect", "base_endurance", "base_faith"]
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if not _slug_ok(payload["slug"]):
        raise HTTPException(400, "slug must be kebab-case (a-z, 0-9, hyphens)")
    if payload["role"] not in VALID_ROLES:
        raise HTTPException(400, "role must be one of Tank/DPS/Healer")
    now = utc_now()
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "slug": payload["slug"].strip(),
        "role": payload["role"],
        "description": payload.get("description", "").strip(),
        "base_strength": int(payload["base_strength"]),
        "base_agility": int(payload["base_agility"]),
        "base_intellect": int(payload["base_intellect"]),
        "base_endurance": int(payload["base_endurance"]),
        "base_faith": int(payload["base_faith"]),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.adventurer_classes.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "A class with this slug already exists")
    return {"class": class_public(doc)}


@router.patch("/classes/{class_id}")
async def admin_update_class(class_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Class not found")
    updates = {}
    for k in ("name", "description"):
        if k in payload:
            updates[k] = str(payload[k]).strip()
    for k in ("base_strength", "base_agility", "base_intellect",
              "base_endurance", "base_faith"):
        if k in payload:
            updates[k] = int(payload[k])
    if "role" in payload:
        if payload["role"] not in VALID_ROLES:
            raise HTTPException(400, "role must be one of Tank/DPS/Healer")
        updates["role"] = payload["role"]
    if "is_active" in payload:
        updates["is_active"] = bool(payload["is_active"])
    if updates:
        updates["updated_at"] = utc_now().isoformat()
        await db.adventurer_classes.update_one({"id": class_id}, {"$set": updates})
    updated = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    return {"class": class_public(updated)}


@router.post("/classes/{class_id}/toggle-active")
async def admin_toggle_class(class_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Class not found")
    new_active = not existing.get("is_active", True)
    await db.adventurer_classes.update_one(
        {"id": class_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    return {"class": class_public(updated)}


# ─── Admin: Traits ────────────────────────────────────────────────────────────
@router.get("/traits")
async def admin_list_traits(_: dict = Depends(get_admin_user)):
    rows = await db.adventurer_traits.find({}, {"_id": 0}).sort("name", ASCENDING).to_list(200)
    return {"traits": [trait_public(r) for r in rows]}


@router.post("/traits", status_code=201)
async def admin_create_trait(payload: dict, _: dict = Depends(get_admin_user)):
    for k in ("name", "modifier_type", "affected_stat", "modifier_value"):
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if payload["modifier_type"] not in ("flat", "percent"):
        raise HTTPException(400, "modifier_type must be flat|percent")
    if payload["affected_stat"] not in VALID_AFFECTED_STAT:
        raise HTTPException(400, f"affected_stat must be one of {VALID_AFFECTED_STAT}")
    now = utc_now()
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "description": payload.get("description", "").strip(),
        "modifier_type": payload["modifier_type"],
        "affected_stat": payload["affected_stat"],
        "modifier_value": float(payload["modifier_value"]),
        "is_positive": bool(payload.get("is_positive", True)),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.adventurer_traits.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "A trait with this name already exists")
    return {"trait": trait_public(doc)}


@router.patch("/traits/{trait_id}")
async def admin_update_trait(trait_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Trait not found")
    updates = {}
    for k in ("name", "description"):
        if k in payload:
            updates[k] = str(payload[k]).strip()
    if "modifier_type" in payload:
        if payload["modifier_type"] not in ("flat", "percent"):
            raise HTTPException(400, "modifier_type must be flat|percent")
        updates["modifier_type"] = payload["modifier_type"]
    if "affected_stat" in payload:
        if payload["affected_stat"] not in VALID_AFFECTED_STAT:
            raise HTTPException(400, f"affected_stat must be one of {VALID_AFFECTED_STAT}")
        updates["affected_stat"] = payload["affected_stat"]
    if "modifier_value" in payload:
        updates["modifier_value"] = float(payload["modifier_value"])
    if "is_positive" in payload:
        updates["is_positive"] = bool(payload["is_positive"])
    if "is_active" in payload:
        updates["is_active"] = bool(payload["is_active"])
    if updates:
        updates["updated_at"] = utc_now().isoformat()
        await db.adventurer_traits.update_one({"id": trait_id}, {"$set": updates})
    updated = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    return {"trait": trait_public(updated)}


@router.post("/traits/{trait_id}/toggle-active")
async def admin_toggle_trait(trait_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Trait not found")
    new_active = not existing.get("is_active", True)
    await db.adventurer_traits.update_one(
        {"id": trait_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    return {"trait": trait_public(updated)}


# ─── Admin: Dungeons ──────────────────────────────────────────────────────────
@router.get("/dungeons")
async def admin_list_dungeons(_: dict = Depends(get_admin_user)):
    rows = await db.dungeons.find({}, {"_id": 0}).sort("difficulty", 1).to_list(200)
    return {"dungeons": [dungeon_public(r) for r in rows]}


@router.post("/dungeons", status_code=201)
async def admin_create_dungeon(payload: dict, _: dict = Depends(get_admin_user)):
    required = ["name", "slug", "difficulty", "required_team_size",
                "base_duration_seconds", "recommended_power",
                "base_gold_reward", "base_xp_reward"]
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if not _slug_ok(payload["slug"]):
        raise HTTPException(400, "slug must be kebab-case")
    now = utc_now()
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "slug": payload["slug"].strip(),
        "description": payload.get("description", "").strip(),
        "difficulty": int(payload["difficulty"]),
        "required_team_size": int(payload["required_team_size"]),
        "base_duration_seconds": int(payload["base_duration_seconds"]),
        "recommended_power": int(payload["recommended_power"]),
        "base_gold_reward": int(payload["base_gold_reward"]),
        "base_xp_reward": int(payload["base_xp_reward"]),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.dungeons.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "A dungeon with this slug already exists")
    return {"dungeon": dungeon_public(doc)}


@router.patch("/dungeons/{dungeon_id}")
async def admin_update_dungeon(dungeon_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Dungeon not found")
    updates = {}
    for k in ("name", "description"):
        if k in payload:
            updates[k] = str(payload[k]).strip()
    for k in ("difficulty", "required_team_size", "base_duration_seconds",
              "recommended_power", "base_gold_reward", "base_xp_reward"):
        if k in payload:
            updates[k] = int(payload[k])
    if "is_active" in payload:
        updates["is_active"] = bool(payload["is_active"])
    if updates:
        updates["updated_at"] = utc_now().isoformat()
        await db.dungeons.update_one({"id": dungeon_id}, {"$set": updates})
    updated = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    return {"dungeon": dungeon_public(updated)}


@router.post("/dungeons/{dungeon_id}/toggle-active")
async def admin_toggle_dungeon(dungeon_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Dungeon not found")
    new_active = not existing.get("is_active", True)
    await db.dungeons.update_one(
        {"id": dungeon_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    return {"dungeon": dungeon_public(updated)}


# ─── Admin: Items ─────────────────────────────────────────────────────────────
@router.get("/items")
async def admin_list_items(_: dict = Depends(get_admin_user)):
    rows = await db.items.find({}, {"_id": 0}).sort("name", 1).to_list(500)
    return {"items": [item_public(r) for r in rows]}


@router.post("/items", status_code=201)
async def admin_create_item(payload: dict, _: dict = Depends(get_admin_user)):
    required = ["name", "slug", "item_type", "rarity", "power_score"]
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if not _slug_ok(payload["slug"]):
        raise HTTPException(400, "slug must be kebab-case")
    if payload["item_type"] not in VALID_ITEM_TYPES:
        raise HTTPException(400, f"item_type must be one of {VALID_ITEM_TYPES}")
    if payload["rarity"] not in VALID_RARITIES:
        raise HTTPException(400, f"rarity must be one of {VALID_RARITIES}")
    doc = _build_item_doc(payload)
    now = utc_now()
    doc["created_at"] = now.isoformat()
    doc["updated_at"] = now.isoformat()
    validate_item_monetization(doc)
    try:
        await db.items.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "An item with this slug already exists")
    return {"item": item_public(doc)}


@router.patch("/items/{item_id}")
async def admin_update_item(item_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Item not found")
    if "item_type" in payload and payload["item_type"] not in VALID_ITEM_TYPES:
        raise HTTPException(400, f"item_type must be one of {VALID_ITEM_TYPES}")
    if "rarity" in payload and payload["rarity"] not in VALID_RARITIES:
        raise HTTPException(400, f"rarity must be one of {VALID_RARITIES}")
    merged = _build_item_doc(payload, existing=existing)
    merged["updated_at"] = utc_now().isoformat()
    validate_item_monetization(merged)
    await db.items.update_one({"id": item_id}, {"$set": _strip_db_fields(merged)})
    updated = await db.items.find_one({"id": item_id}, {"_id": 0})
    return {"item": item_public(updated)}


@router.post("/items/{item_id}/toggle-active")
async def admin_toggle_item(item_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Item not found")
    new_active = not existing.get("is_active", True)
    await db.items.update_one(
        {"id": item_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.items.find_one({"id": item_id}, {"_id": 0})
    return {"item": item_public(updated)}


# ═════════════════════════════════════════════════════════════════════════
# Phase 16.1 — Admin Cleanup: flag-test-users
# ═════════════════════════════════════════════════════════════════════════
# Aggressive bulk-flag endpoint. Idempotent CAS write, audit-trailed.
# NO HARD DELETE: every assertion checked at runtime. Designed for prod use
# behind the admin JWT, called via the bundle (not the standalone script).
from app.admin.services import flag_test_users_aggressive  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402


class CleanupFlagPayload(BaseModel):
    mode: str = Field(pattern="^(dry_run|apply)$")
    confirm_apply: bool = False


@router.post("/cleanup/flag-test-users")
async def admin_cleanup_flag_test_users(
    payload: CleanupFlagPayload,
    current_admin: dict = Depends(get_admin_user),
):
    if payload.mode == "apply" and not payload.confirm_apply:
        raise HTTPException(
            400,
            "confirm_apply=true is required for mode=apply (double-gate safety)",
        )
    return await flag_test_users_aggressive(
        db,
        mode=payload.mode,
        actor_admin_id=current_admin.get("id"),
    )


__all__ = ["router"]
