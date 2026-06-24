"""Leaderboard routes (Phase 9.1).

`GET /api/leaderboard/guilds` — PUBLIC (no JWT required). Deliberately does
NOT use `Depends(get_current_user)`. Returns a paginated, privacy-preserving
ranked list of guilds.
"""
from fastapi import APIRouter, Query

from app.core.database import db
from app.leaderboard.services import get_guild_leaderboard


router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/guilds")
async def list_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=1000),
):
    """Public guild leaderboard ordered by peak team power (Phase 8 sticky field)."""
    return await get_guild_leaderboard(db, limit=limit, offset=offset)


__all__ = ["router"]
