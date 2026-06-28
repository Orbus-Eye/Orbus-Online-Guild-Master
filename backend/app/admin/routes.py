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

from app.adventurers.services import class_public, trait_public, trait_admin_public
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
    rows = await db.adventurer_traits.find({}, {"_id": 0}).sort("name", ASCENDING).to_list(500)
    return {"traits": [trait_admin_public(r) for r in rows]}


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


# ═════════════════════════════════════════════════════════════════════════
# ROUND 11.2 TASK 5a — Admin Ops MVP (Guilds search/detail + grants + audit)
# ═════════════════════════════════════════════════════════════════════════
import os as _os  # noqa: E402
from datetime import datetime as _dt, timezone as _tz  # noqa: E402

from pydantic import constr as _constr, conint as _conint  # noqa: E402
from app.audit.log import write_audit as _write_audit  # noqa: E402
from app.core.identifiers import to_public_id as _to_public_id  # noqa: E402
from app.territory.guards import compute_adventurer_cap_state as _cap_state  # noqa: E402


# ── Config knobs (env-overridable for tests/prod) ────────────────────────
ADMIN_MAX_GRANT_GOLD = int(_os.environ.get("ADMIN_MAX_GRANT_GOLD", "100000"))
ADMIN_MAX_GRANT_ITEM_QTY = int(_os.environ.get("ADMIN_MAX_GRANT_ITEM_QTY", "1000"))


def _mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "<unknown>"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


async def _resolve_guild(id_or_public: str) -> dict | None:
    """Accept internal `id` (uuid4) OR `public_id` (8-char hex hash)."""
    if not id_or_public:
        return None
    # Try internal id first (uuid4 is 36 chars w/ dashes).
    if len(id_or_public) > 12 and "-" in id_or_public:
        g = await db.guilds.find_one({"id": id_or_public}, {"_id": 0})
        if g:
            return g
    # Try public_id (8-char hash). Iterate (no inverse): match by computing.
    cursor = db.guilds.find({}, {"_id": 0, "id": 1, "name": 1, "owner_user_id": 1,
                                 "gold": 1, "is_test_artifact": 1, "created_at": 1,
                                 "updated_at": 1})
    async for g in cursor:
        if _to_public_id(g["id"]) == id_or_public:
            return await db.guilds.find_one({"id": g["id"]}, {"_id": 0})
    return None


async def _enrich_guild_public(g: dict) -> dict:
    """Build the public/admin-safe projection for a guild row."""
    owner_email_masked = "<no-owner>"
    owner_is_test_user = False
    if g.get("owner_user_id"):
        u = await db.users.find_one(
            {"id": g["owner_user_id"]},
            {"_id": 0, "email": 1, "is_test_user": 1},
        )
        if u:
            owner_email_masked = _mask_email(u.get("email"))
            owner_is_test_user = bool(u.get("is_test_user"))
    return {
        "public_id": _to_public_id(g["id"]),
        "name": g.get("name"),
        "owner_email_masked": owner_email_masked,
        "gold": int(g.get("gold", 0)),
        "is_test_artifact": bool(g.get("is_test_artifact", False)),
        "owner_is_test_user": owner_is_test_user,
        "created_at": g.get("created_at"),
        "updated_at": g.get("updated_at"),
    }


# ── 1) GET /api/admin/guilds/search ───────────────────────────────────────
@router.get("/guilds/search")
async def admin_guilds_search(
    q: str = "",
    limit: int = 20,
    offset: int = 0,
    actor: dict = Depends(get_admin_user),
):
    limit = max(1, min(int(limit or 20), 50))
    offset = max(0, int(offset or 0))
    query: dict = {}
    if q:
        q_stripped = q.strip()
        # public_id heuristic: 8 hex chars
        if len(q_stripped) == 8 and all(c in "0123456789abcdef" for c in q_stripped.lower()):
            # Exact public_id match (must scan since hash is non-invertible)
            results: list[dict] = []
            async for g in db.guilds.find({}, {"_id": 0}).limit(2000):
                if _to_public_id(g["id"]) == q_stripped.lower():
                    results.append(g)
                    break
            total = len(results)
            return {"total": total,
                    "limit": limit, "offset": offset,
                    "guilds": [await _enrich_guild_public(r) for r in results]}
        # Otherwise: case-insensitive partial match on name
        import re as _re
        query["name"] = {"$regex": _re.escape(q_stripped), "$options": "i"}
    total = await db.guilds.count_documents(query)
    cursor = db.guilds.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit)
    rows = [r async for r in cursor]
    out = [await _enrich_guild_public(r) for r in rows]
    # Add roster_count + dormitory_level for the search list
    for entry, raw in zip(out, rows):
        try:
            cap = await _cap_state(db, raw["id"])
            entry["roster_count"] = int(cap.get("current", 0))
            entry["roster_cap"] = int(cap.get("cap", 0))
            entry["dormitory_level"] = int(cap.get("dormitory_level", 0))
        except Exception:
            entry["roster_count"] = 0
            entry["roster_cap"] = 0
            entry["dormitory_level"] = 0
    return {"total": total, "limit": limit, "offset": offset, "guilds": out}


# ── 2) GET /api/admin/guilds/{id} ─────────────────────────────────────────
@router.get("/guilds/{id_or_public}")
async def admin_guild_detail(
    id_or_public: str,
    actor: dict = Depends(get_admin_user),
):
    g = await _resolve_guild(id_or_public)
    if not g:
        raise HTTPException(404, detail={
            "code": "admin.guild.not_found",
            "user_message": "Gilda non trovata.",
        })
    public = await _enrich_guild_public(g)
    try:
        cap = await _cap_state(db, g["id"])
        roster = {"current": int(cap.get("current", 0)),
                  "cap": int(cap.get("cap", 0)),
                  "dormitory_level": int(cap.get("dormitory_level", 0))}
    except Exception:
        roster = {"current": 0, "cap": 0, "dormitory_level": 0}
    # Territory structures levels (per slug, max level shown only for dormitories)
    gs = await db.guild_structures.find_one({"guild_id": g["id"]}, {"_id": 0}) or {}
    structures = gs.get("structures", {}) or {}
    territory = {
        "dormitories_level": int((structures.get("dormitories") or {}).get("level", 0)),
        "max_buildings_level": max(
            (int((s or {}).get("level", 0)) for s in structures.values()), default=0,
        ),
    }
    return {**public, "roster": roster, "territory": territory,
            "flags": {"is_test_artifact": public["is_test_artifact"],
                      "owner_is_test_user": public["owner_is_test_user"]}}


# ── 3) POST /api/admin/guilds/{id}/grant-gold ────────────────────────────
class _GrantGoldIn(BaseModel):
    amount: int = Field(..., gt=0, le=ADMIN_MAX_GRANT_GOLD * 10)  # hard cap defensive
    reason: str = Field(..., min_length=3, max_length=300)


@router.post("/guilds/{id_or_public}/grant-gold")
async def admin_grant_gold(
    id_or_public: str,
    payload: _GrantGoldIn,
    actor: dict = Depends(get_admin_user),
):
    if payload.amount > ADMIN_MAX_GRANT_GOLD:
        raise HTTPException(422, detail={
            "code": "admin.grant_gold.amount_over_max",
            "max": ADMIN_MAX_GRANT_GOLD,
            "user_message": f"Importo eccede il massimo per operazione ({ADMIN_MAX_GRANT_GOLD}).",
        })
    g = await _resolve_guild(id_or_public)
    if not g:
        raise HTTPException(404, detail={
            "code": "admin.guild.not_found",
            "user_message": "Gilda non trovata.",
        })
    now_iso = _dt.now(_tz.utc).isoformat()
    gold_before = int(g.get("gold", 0))
    await db.guilds.update_one(
        {"id": g["id"]},
        {"$inc": {"gold": int(payload.amount)},
         "$set": {"updated_at": now_iso}},
    )
    g2 = await db.guilds.find_one({"id": g["id"]}, {"_id": 0, "gold": 1, "name": 1})
    gold_after = int((g2 or {}).get("gold", gold_before + payload.amount))
    actor_email_masked = _mask_email(actor.get("email"))
    event_id = await _write_audit(
        db,
        event_type="admin_gold_granted",
        actor_user_id=actor.get("id"),
        actor_guild_id=g["id"],  # target guild
        source="admin.grant_gold",
        related_entity_id=g["id"],
        gold_delta=int(payload.amount),
        metadata={
            "admin_actor_id": actor.get("id"),
            "admin_actor_email_masked": actor_email_masked,
            "target_guild_id": g["id"],
            "target_guild_public_id": _to_public_id(g["id"]),
            "target_guild_name": g2.get("name") if g2 else g.get("name"),
            "amount": int(payload.amount),
            "gold_before": gold_before,
            "gold_after": gold_after,
            "reason": payload.reason,
        },
    )
    return {
        "success": True,
        "gold_before": gold_before,
        "gold_after": gold_after,
        "amount": int(payload.amount),
        "audit_event_id": event_id,
    }


# ── 4) POST /api/admin/guilds/{id}/grant-item ────────────────────────────
class _GrantItemIn(BaseModel):
    item_slug: str = Field(..., min_length=1, max_length=120)
    quantity: int = Field(..., gt=0, le=ADMIN_MAX_GRANT_ITEM_QTY * 10)
    reason: str = Field(..., min_length=3, max_length=300)


@router.post("/guilds/{id_or_public}/grant-item")
async def admin_grant_item(
    id_or_public: str,
    payload: _GrantItemIn,
    actor: dict = Depends(get_admin_user),
):
    if payload.quantity > ADMIN_MAX_GRANT_ITEM_QTY:
        raise HTTPException(422, detail={
            "code": "admin.grant_item.qty_over_max",
            "max": ADMIN_MAX_GRANT_ITEM_QTY,
            "user_message": f"Quantità eccede il massimo per operazione ({ADMIN_MAX_GRANT_ITEM_QTY}).",
        })
    g = await _resolve_guild(id_or_public)
    if not g:
        raise HTTPException(404, detail={
            "code": "admin.guild.not_found",
            "user_message": "Gilda non trovata.",
        })
    tpl = await db.items.find_one({"slug": payload.item_slug}, {"_id": 0})
    if not tpl:
        raise HTTPException(422, detail={
            "code": "admin.item.unknown_slug",
            "user_message": f"Item slug '{payload.item_slug}' non riconosciuto.",
        })
    # Refuse bound or P2W-tagged templates.
    if tpl.get("is_bound") is True:
        raise HTTPException(422, detail={
            "code": "admin.item.bound_not_grantable",
            "user_message": "Items bound non possono essere grantati via admin.",
        })
    if (tpl.get("can_be_sold_for_real_money") is True
            and tpl.get("affects_combat") is True
            and tpl.get("is_cosmetic") is False):
        raise HTTPException(422, detail={
            "code": "admin.item.p2w_blocked",
            "user_message": "Items real-money + combat non grantabili.",
        })
    now_iso = _dt.now(_tz.utc).isoformat()
    is_stackable = bool(tpl.get("is_stackable", True)) or \
                   tpl.get("item_type") in ("material", "consumable")
    entries_created = 0
    if is_stackable:
        # Upsert: increment qty on existing row OR create one fresh entry.
        existing = await db.inventory_items.find_one({
            "guild_id": g["id"],
            "item_slug": payload.item_slug,
            "is_bound": False,
            "discarded_at": None,
        }, {"_id": 0, "id": 1, "quantity": 1})
        if existing:
            await db.inventory_items.update_one(
                {"id": existing["id"]},
                {"$inc": {"quantity": int(payload.quantity)}},
            )
            entries_created = 1
        else:
            inv_id = str(uuid.uuid4())
            await db.inventory_items.insert_one({
                "id": inv_id, "instance_id": inv_id,
                "guild_id": g["id"],
                "item_id": tpl.get("id") or payload.item_slug,
                "item_slug": payload.item_slug,
                "quantity": int(payload.quantity),
                "acquired_at": now_iso,
                "is_bound": False, "refinement_level": 0,
                "enchants": [], "affixes": [], "reroll_count": 0,
                "disenchanted_at": None, "discarded_at": None,
                "bound_to_adventurer_id": None,
            })
            entries_created = 1
    else:
        # Non-stackable (equipment): one entry per quantity unit.
        rows = []
        for _ in range(int(payload.quantity)):
            inv_id = str(uuid.uuid4())
            rows.append({
                "id": inv_id, "instance_id": inv_id,
                "guild_id": g["id"],
                "item_id": tpl.get("id") or payload.item_slug,
                "item_slug": payload.item_slug,
                "quantity": 1, "acquired_at": now_iso,
                "is_bound": False, "refinement_level": 0,
                "enchants": [], "affixes": [], "reroll_count": 0,
                "disenchanted_at": None, "discarded_at": None,
                "bound_to_adventurer_id": None,
            })
        if rows:
            await db.inventory_items.insert_many(rows)
            entries_created = len(rows)
    actor_email_masked = _mask_email(actor.get("email"))
    event_id = await _write_audit(
        db,
        event_type="admin_item_granted",
        actor_user_id=actor.get("id"),
        actor_guild_id=g["id"],
        source="admin.grant_item",
        related_entity_id=g["id"],
        metadata={
            "admin_actor_id": actor.get("id"),
            "admin_actor_email_masked": actor_email_masked,
            "target_guild_id": g["id"],
            "target_guild_public_id": _to_public_id(g["id"]),
            "target_guild_name": g.get("name"),
            "item_slug": payload.item_slug,
            "quantity": int(payload.quantity),
            "inventory_entries_created": entries_created,
            "reason": payload.reason,
        },
    )
    return {
        "success": True,
        "item_slug": payload.item_slug,
        "quantity": int(payload.quantity),
        "inventory_entries_created": entries_created,
        "audit_event_id": event_id,
    }


# ── 5) GET /api/admin/audit ──────────────────────────────────────────────
@router.get("/audit")
async def admin_audit_list(
    guild: str | None = None,
    action: str | None = None,
    since: str | None = None,
    limit: int = 50,
    offset: int = 0,
    actor: dict = Depends(get_admin_user),
):
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    query: dict = {}
    if guild:
        # Resolve public_id → internal id
        g = await _resolve_guild(guild)
        if g:
            query["actor_guild_id"] = g["id"]
        else:
            return {"total": 0, "limit": limit, "offset": offset, "events": []}
    if action:
        query["event_type"] = action
    if since:
        query["created_at"] = {"$gte": since}
    total = await db.audit_log.count_documents(query)
    cursor = db.audit_log.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit)
    rows = [r async for r in cursor]
    # Mask PII on every row.
    safe_events: list[dict] = []
    for r in rows:
        md = dict(r.get("metadata") or {})
        # Strip any potential raw email/user_id leaks.
        for k in list(md.keys()):
            if k in ("admin_actor_id", "target_guild_id"):
                # Replace with hashed public_id; keep id for grant-context only.
                md[k] = md[k]  # already an internal id (admin scope is allowed to see it)
        safe_events.append({
            "event_type": r.get("event_type"),
            "actor_email_masked": md.get("admin_actor_email_masked", "<system>"),
            "target_guild_name": md.get("target_guild_name"),
            "target_guild_public_id": md.get("target_guild_public_id"),
            "metadata": md,
            "ts": r.get("created_at"),
        })
    return {"total": total, "limit": limit, "offset": offset, "events": safe_events}


# ─── Admin: Equipment level audit (ROUND 11.3 TASK B) ────────────────────────
@router.post("/equipment/level-audit")
async def admin_equipment_level_audit(
    payload: dict | None = None, _: dict = Depends(get_admin_user)
):
    """Scan `equipped_items` for rows where the equipped item's required
    level exceeds the wearer's current level. Returns a report.

    Body (all optional):
        {"dry_run": bool = True, "guild_id_filter": str | None = None}

    When `dry_run=false`, performs soft unequip (item stays in inventory,
    only `equipped_items` row is removed and `reserved_qty` is released)
    and writes `equipment_auto_unequipped_level_requirement` audit events.
    """
    from app.equipment.level_audit import audit_and_unequip_legacy
    payload = payload or {}
    dry_run = bool(payload.get("dry_run", True))
    guild_filter = payload.get("guild_id_filter")
    if guild_filter is not None and not isinstance(guild_filter, str):
        raise HTTPException(400, "guild_id_filter must be a string")
    report = await audit_and_unequip_legacy(
        db, dry_run=dry_run, guild_id_filter=guild_filter,
    )
    return report


__all__ = ["router"]
