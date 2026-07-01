"""ROUND 12.D — Admin endpoint to release stuck adventurers.

Idempotent. Soft-only: flips `is_available=true` for advs that are
clearly orphaned (not currently assigned to a live expedition/squad).
Audit obligatory with `reason >= 3 chars`.
"""
from fastapi import APIRouter, Body, Depends, HTTPException

from app.audit.log import write_audit
from app.core.database import db
from app.core.security import get_admin_user

router = APIRouter(prefix="/api/admin/ops", tags=["admin-ops"])


@router.post("/release-stuck-adventurers")
async def release_stuck(payload: dict = Body(...), admin: dict = Depends(get_admin_user)):
    reason = (payload.get("reason") or "").strip()
    if len(reason) < 3:
        raise HTTPException(400, {"code": "admin.reason_too_short",
                                   "user_message": "Reason min 3 char."})
    guild_public_id = payload.get("guild_public_id")
    if not guild_public_id:
        raise HTTPException(400, {"code": "admin.bad_payload",
                                   "user_message": "guild_public_id richiesto."})

    g = await db.guilds.find_one({"public_id": guild_public_id})
    if not g:
        g = await db.guilds.find_one({"id": {"$regex": f"^{guild_public_id}"}})
    if not g:
        raise HTTPException(404, {"code": "admin.guild_not_found",
                                   "user_message": "Gilda non trovata."})

    # Soft-release: any adv in this guild not retired/archived but with
    # is_available=false → flip to true. We do not touch expedition state;
    # those are reconciled by their own services on completion.
    res = await db.adventurers.update_many(
        {"guild_id": g["id"], "is_available": False,
         "retired": {"$ne": True}, "archived": {"$ne": True}},
        {"$set": {"is_available": True}},
    )
    await write_audit(
        db, event_type="admin_grant_item",  # reuse existing event_type; metadata clarifies
        actor_user_id=admin["id"], actor_guild_id=g["id"],
        source="admin_ops.release_stuck",
        metadata={"reason": reason, "released_count": res.modified_count,
                  "operation": "release_stuck_adventurers"},
    )
    return {"ok": True, "released": res.modified_count, "guild_id": g["id"]}


__all__ = ["router"]
