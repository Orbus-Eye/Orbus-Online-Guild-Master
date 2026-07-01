"""ROUND 12.C — Reward routes (public listing + admin grant)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_admin_user
from app.rewards.services import grant_rewards, list_rewards
from app.seasons.services import get_current_season, get_season_by_slug

router = APIRouter(prefix="/api/seasons", tags=["rewards"])
admin_router = APIRouter(prefix="/api/admin/seasons", tags=["admin-rewards"])


@router.get("/{slug}/rewards")
async def public_list_rewards(slug: str):
    s = await get_season_by_slug(db, slug)
    if not s:
        if slug == "current":
            s = await get_current_season(db)
        if not s:
            raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    rows = await list_rewards(db, s["season_id"])
    safe = [{
        "reward_id": r["reward_id"], "reward_type": r["reward_type"],
        "name_it": r["name_it"], "name_en": r.get("name_en"),
        "description_it": r.get("description_it", ""),
        "criteria": r.get("criteria") or {},
        "cosmetic_only": True,
    } for r in rows]
    return {"season_slug": s["slug"], "rewards": safe, "total": len(safe)}


@admin_router.post("/{season_id}/grant_rewards")
async def admin_grant_rewards(
    season_id: str, payload: dict = Body(...), admin: dict = Depends(get_admin_user),
):
    reason = (payload.get("reason") or "").strip()
    if len(reason) < 3:
        raise HTTPException(400, {"code": "admin.reason_too_short",
                                   "user_message": "Reason deve avere almeno 3 caratteri."})
    dry_run = bool(payload.get("dry_run", False))
    res = await grant_rewards(
        db, season_id=season_id, actor_user_id=admin["id"], reason=reason, dry_run=dry_run,
    )
    return res


__all__ = ["router", "admin_router"]
