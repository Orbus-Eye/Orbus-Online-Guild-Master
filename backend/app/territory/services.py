"""ROUND 6B.1 — Territory services.

Provides:
- `ensure_guild_structures_doc(db, guild_id)`: lazy-create the document for
  a guild that does not yet have one (used on first GET).
- `get_territory(db, guild_id)`: fetch the document, lazily create if missing.
- `purchase_structure(db, guild, slug)`: unlock a structure at Lv1 (no atomic deduction yet in 6B.1).
- `upgrade_structure(db, guild, slug)`: bump a structure level by +1 (no atomic deduction yet).

Errors are raised as HTTPException with a structured `detail` dict so the
frontend can render localized banners (UI lives in 6B.2).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.territory.costs import cost_for
from app.territory.structures import (
    VALID_STRUCTURE_SLUGS,
    default_structures_doc,
    get_prerequisites,
    get_structure_max_level,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_doc(doc: dict) -> dict:
    """Strip the BSON `_id` and return only the public shape."""
    return {
        "id": doc["id"],
        "guild_id": doc["guild_id"],
        "structures": doc["structures"],
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def ensure_guild_structures_doc(db, guild_id: str) -> dict:
    """Lazy creation: if no doc exists for this guild, insert a default one.

    Idempotent and race-safe via the unique index on `guild_id` (created at
    boot in `app.core.indexes`). On DuplicateKeyError we re-read.
    """
    existing = await db.guild_structures.find_one({"guild_id": guild_id})
    if existing:
        return existing
    now = _utc_now_iso()
    doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "structures": default_structures_doc(),
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.guild_structures.insert_one(doc)
    except Exception:
        # If a parallel request beat us to it, just re-read.
        existing = await db.guild_structures.find_one({"guild_id": guild_id})
        if existing:
            return existing
        raise
    return doc


async def get_territory(db, guild_id: str) -> dict:
    doc = await ensure_guild_structures_doc(db, guild_id)
    return _public_doc(doc)


def _validate_slug(slug: str) -> None:
    if slug not in VALID_STRUCTURE_SLUGS:
        raise HTTPException(
            status_code=422,
            detail={"code": "structure_slug.invalid", "slug": slug},
        )


def _check_prerequisites(structures: dict, slug: str) -> None:
    """Raise 423 (Locked) if any prerequisite is unmet."""
    reqs = get_prerequisites(slug)
    if not reqs:
        return
    unmet = []
    for req_slug, req_level in reqs.items():
        cur = structures.get(req_slug) or {}
        if int(cur.get("level", 0)) < int(req_level):
            unmet.append({"structure": req_slug, "min_level": req_level,
                          "current_level": int(cur.get("level", 0))})
    if unmet:
        raise HTTPException(
            status_code=423,
            detail={"code": "structure.prerequisites_unmet", "unmet": unmet},
        )


def _check_resources(guild: dict, cost: dict) -> None:
    """In 6B.1: validate gold and presence of materials in DB. No deduction.

    Atomic transaction lives in 6B.2.
    Materials are NOT validated against actual inventory yet (kept for 6B.2).
    """
    gold_required = int(cost.get("gold", 0))
    if int(guild.get("gold", 0)) < gold_required:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "resources.gold_insufficient",
                "required": gold_required,
                "available": int(guild.get("gold", 0)),
            },
        )
    # Materials check is intentionally deferred to 6B.2 atomic flow.


async def purchase_structure(db, guild: dict, slug: str) -> dict:
    """Move a structure from Lv0 (locked) → Lv1 (unlocked).

    Errors:
      - 422 structure_slug.invalid
      - 409 structure.already_unlocked (already Lv≥1)
      - 423 structure.prerequisites_unmet
      - 422 resources.gold_insufficient
    """
    _validate_slug(slug)
    doc = await ensure_guild_structures_doc(db, guild["id"])
    cur = doc["structures"].get(slug, {})
    cur_level = int(cur.get("level", 0))
    if cur_level >= 1:
        raise HTTPException(
            status_code=409,
            detail={"code": "structure.already_unlocked", "slug": slug,
                    "current_level": cur_level},
        )
    _check_prerequisites(doc["structures"], slug)
    cost = cost_for(slug, 1) or {}
    _check_resources(guild, cost)

    now = _utc_now_iso()
    update_path = f"structures.{slug}"
    new_struct = {
        "level": 1,
        "is_unlocked": True,
        "purchased_at": now,
        "upgraded_at": now,
        "acquired_via": "purchase",
    }
    await db.guild_structures.update_one(
        {"id": doc["id"]},
        {"$set": {update_path: new_struct, "updated_at": now}},
    )
    # Audit (best-effort; failures don't block business flow).
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="guild_structure_purchased",
            actor_user_id=guild.get("owner_user_id"),
            actor_guild_id=guild["id"],
            source="territory.purchase",
            gold_delta=-int(cost.get("gold", 0)),
            metadata={"structure_slug": slug, "from_level": 0, "to_level": 1,
                      "cost": cost},
        )
    except Exception:
        pass
    return await get_territory(db, guild["id"])


async def upgrade_structure(db, guild: dict, slug: str) -> dict:
    """Bump a structure level by +1 (Lv N → Lv N+1).

    Errors:
      - 422 structure_slug.invalid
      - 423 structure.locked (current level is 0 → purchase first)
      - 409 structure.already_max_level
      - 423 structure.prerequisites_unmet (re-checked against new effective level)
      - 422 resources.gold_insufficient
      - 422 structure.upgrade_not_available (None in cost table = legacy-only)
    """
    _validate_slug(slug)
    doc = await ensure_guild_structures_doc(db, guild["id"])
    cur = doc["structures"].get(slug, {})
    cur_level = int(cur.get("level", 0))
    if cur_level < 1:
        raise HTTPException(
            status_code=423,
            detail={"code": "structure.locked", "slug": slug,
                    "hint": "Call POST /api/territory/purchase first."},
        )
    max_lv = get_structure_max_level(slug, allow_legacy=False)
    if cur_level >= max_lv:
        raise HTTPException(
            status_code=409,
            detail={"code": "structure.already_max_level", "slug": slug,
                    "current_level": cur_level, "max_level": max_lv},
        )
    next_level = cur_level + 1
    cost = cost_for(slug, next_level)
    if cost is None:
        # Migration-only level — cannot be reached via user upgrade.
        raise HTTPException(
            status_code=422,
            detail={"code": "structure.upgrade_not_available", "slug": slug,
                    "target_level": next_level,
                    "hint": "This level can only be unlocked via legacy migration."},
        )
    _check_prerequisites(doc["structures"], slug)
    _check_resources(guild, cost)

    now = _utc_now_iso()
    update_path = f"structures.{slug}"
    new_struct = {
        "level": next_level,
        "is_unlocked": True,
        "purchased_at": cur.get("purchased_at") or now,
        "upgraded_at": now,
        "acquired_via": cur.get("acquired_via") or "purchase",
    }
    await db.guild_structures.update_one(
        {"id": doc["id"]},
        {"$set": {update_path: new_struct, "updated_at": now}},
    )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="guild_structure_upgraded",
            actor_user_id=guild.get("owner_user_id"),
            actor_guild_id=guild["id"],
            source="territory.upgrade",
            gold_delta=-int(cost.get("gold", 0)),
            metadata={"structure_slug": slug,
                      "from_level": cur_level, "to_level": next_level,
                      "cost": cost},
        )
    except Exception:
        pass
    return await get_territory(db, guild["id"])


__all__ = [
    "ensure_guild_structures_doc",
    "get_territory",
    "purchase_structure",
    "upgrade_structure",
]
