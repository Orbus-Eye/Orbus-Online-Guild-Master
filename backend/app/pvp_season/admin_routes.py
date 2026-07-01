"""ROUND 16.3 Phase 7B — Admin routes for PvP seasons (dev-gated)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.security import get_admin_user
from app.pvp_season.services import (
    finalize_season,
    finalize_season_if_due,
    get_or_bootstrap_active_season,
)


router = APIRouter(prefix="/api/admin/pvp-season", tags=["admin", "pvp_season"])


def _dev_gate() -> None:
    if (os.environ.get("APP_ENV") or "development").lower() == "production":
        raise HTTPException(
            status_code=403,
            detail={"code": "pvp_season.dev_disabled_in_prod",
                    "user_message":
                    "Il force-snapshot dev è disabilitato in produzione."},
        )


@router.get("/stats")
async def admin_stats(admin: dict = Depends(get_admin_user)):
    total_seasons = await db.pvp_seasons.count_documents({})
    finalized_count = await db.pvp_seasons.count_documents(
        {"status": "finalized"},
    )
    active_count = await db.pvp_seasons.count_documents(
        {"status": "active"},
    )
    lb_rows = await db.pvp_season_leaderboards.count_documents({})
    cosmetics = await db.pvp_cosmetics_unlocked.count_documents({})
    unique_guilds_awarded = len(
        await db.pvp_cosmetics_unlocked.distinct("guild_id"),
    )
    latest_active = await db.pvp_seasons.find_one(
        {"status": "active"}, {"_id": 0},
    )
    return {
        "totals": {
            "seasons": total_seasons,
            "finalized": finalized_count,
            "active": active_count,
            "leaderboard_rows": lb_rows,
            "cosmetics_awarded": cosmetics,
            "unique_guilds_awarded": unique_guilds_awarded,
        },
        "latest_active": latest_active,
    }


@router.post("/dev/force-snapshot")
async def dev_force_snapshot(admin: dict = Depends(get_admin_user)):
    """Force snapshot + rollover of the current active season.

    Bypasses the ends_at gate by finalizing whatever is currently active.
    Requires APP_ENV != production.
    """
    _dev_gate()
    active = await get_or_bootstrap_active_season(db)
    # If we just bootstrapped (season_number ≥1, ends_at in future),
    # force-finalize it anyway (for testing rollover in dev).
    result = await finalize_season(db, active["id"])
    return {"forced": True, "result": result}


@router.post("/dev/finalize-if-due")
async def dev_finalize_if_due(admin: dict = Depends(get_admin_user)):
    """Explicit trigger for the on-visit rollover check (dev/testing)."""
    _dev_gate()
    result = await finalize_season_if_due(db)
    return {"result": result}
