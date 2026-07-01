"""ROUND 12.A — Season public + admin routes.

Public: read-only season metadata + leaderboard delegation.
Admin: lifecycle (create / activate / end / archive / recompute), gated
by `get_admin_user` + reason ≥ 3 chars.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.audit.log import write_audit
from app.core.database import db
from app.core.security import get_admin_user, get_current_user
from app.seasons.services import (
    activate_season as svc_activate,
    archive_season as svc_archive,
    create_season as svc_create,
    end_season as svc_end,
    get_current_season,
    get_season_by_slug,
    list_seasons,
)

router = APIRouter(prefix="/api/seasons", tags=["seasons"])
admin_router = APIRouter(prefix="/api/admin/seasons", tags=["admin-seasons"])


def _countdown_for(season: dict | None) -> dict | None:
    if not season:
        return None
    try:
        ends = datetime.fromisoformat(season["ends_at"])
    except Exception:
        return None
    now = datetime.now(timezone.utc)
    delta = ends - now
    return {
        "seconds_remaining": max(0, int(delta.total_seconds())),
        "days_remaining": max(0, delta.days),
        "ends_at": season["ends_at"],
    }


# ─── PUBLIC ───────────────────────────────────────────────────────────────────
@router.get("/current")
async def current_season():
    s = await get_current_season(db)
    if not s:
        raise HTTPException(404, {
            "code": "season.no_active",
            "user_message": "Nessuna stagione attiva al momento.",
        })
    return {"season": s, "countdown": _countdown_for(s)}


@router.get("")
async def all_seasons(_: dict = Depends(get_current_user)):
    """Returns all non-draft seasons; admins may include drafts via dedicated admin route."""
    rows = await list_seasons(db, include_drafts=False)
    return {"seasons": rows, "total": len(rows)}


@router.get("/{slug}")
async def season_detail(slug: str):
    s = await get_season_by_slug(db, slug)
    if not s:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    return {"season": s, "countdown": _countdown_for(s) if s["status"] == "active" else None}


@router.get("/{slug}/leaderboards")
async def season_leaderboards_entry(slug: str):
    """Entry-point that surfaces the available categories for the given season.
    Detailed entries are served by `/api/leaderboard?scope=season&season=<slug>&category=<cat>`.
    """
    s = await get_season_by_slug(db, slug)
    if not s:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    from app.leaderboard.seasonal import list_seasonal_categories
    return {
        "season_slug": s["slug"],
        "season_name_it": s["name_it"],
        "status": s["status"],
        "categories": list_seasonal_categories(),
    }


# ─── ADMIN ────────────────────────────────────────────────────────────────────
def _check_reason(reason: str | None) -> str:
    r = (reason or "").strip()
    if len(r) < 3:
        raise HTTPException(400, {
            "code": "admin.reason_too_short",
            "user_message": "La motivazione deve avere almeno 3 caratteri.",
        })
    return r


@admin_router.post("/create")
async def admin_create_season(
    payload: dict = Body(...),
    admin: dict = Depends(get_admin_user),
):
    reason = _check_reason(payload.get("reason"))
    s = await svc_create(
        db,
        slug=payload["slug"],
        name_it=payload["name_it"],
        name_en=payload.get("name_en") or payload["name_it"],
        lore_theme=payload.get("lore_theme", "equilibrio"),
        starts_at=payload["starts_at"],
        ends_at=payload["ends_at"],
        actor_user_id=admin["id"],
        reason=reason,
        status=payload.get("status", "draft"),
    )
    return {"season": s}


@admin_router.post("/{season_id}/activate")
async def admin_activate(season_id: str, payload: dict = Body(...), admin: dict = Depends(get_admin_user)):
    reason = _check_reason(payload.get("reason"))
    s = await svc_activate(db, season_id=season_id, actor_user_id=admin["id"], reason=reason)
    return {"season": s}


@admin_router.post("/{season_id}/end")
async def admin_end(season_id: str, payload: dict = Body(...), admin: dict = Depends(get_admin_user)):
    reason = _check_reason(payload.get("reason"))
    s = await svc_end(db, season_id=season_id, actor_user_id=admin["id"], reason=reason)
    return {"season": s}


@admin_router.post("/{season_id}/archive")
async def admin_archive(season_id: str, payload: dict = Body(...), admin: dict = Depends(get_admin_user)):
    reason = _check_reason(payload.get("reason"))
    s = await svc_archive(db, season_id=season_id, actor_user_id=admin["id"], reason=reason)
    return {"season": s}


@admin_router.post("/{season_id}/recompute")
async def admin_recompute(season_id: str, payload: dict = Body(...), admin: dict = Depends(get_admin_user)):
    """Stub: triggers an audit + invalidates the seasonal leaderboard cache.
    Full aggregate recompute is deferred to 12.C (currently rows are server-
    authoritative on every read, so cache invalidation is sufficient).
    """
    reason = _check_reason(payload.get("reason"))
    season = await db.seasons.find_one({"season_id": season_id})
    if not season:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    from app.leaderboard.seasonal import invalidate_seasonal_cache
    invalidate_seasonal_cache(season["slug"])
    await write_audit(
        db, event_type="season_scores_recomputed", actor_user_id=admin["id"],
        source="seasons.recompute",
        metadata={"season_id": season_id, "slug": season["slug"], "reason": reason},
    )
    return {"ok": True, "season_id": season_id, "slug": season["slug"]}


__all__ = ["router", "admin_router"]
