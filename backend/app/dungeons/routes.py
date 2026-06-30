"""Dungeons routes (Phase 5.5c.2 + Phase 19.3 filters)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_optional_user
from app.dungeons.services import list_dungeons_for_guild


router = APIRouter(prefix="/api/dungeons", tags=["dungeons"])


_DIFF_ALIASES = {
    "facile": 1, "easy": 1, "1": 1,
    "medio": 2, "medium": 2, "2": 2,
    "difficile": 3, "hard": 3, "3": 3,
    "elite": 4, "4": 4,
}


@router.get("")
async def list_dungeons(
    current_user: Optional[dict] = Depends(get_optional_user),
    team_size: Optional[int] = Query(None, description="Filter by required_team_size (3,5,7)"),
    pwr_min: Optional[int] = Query(None, ge=1, le=9999),
    pwr_max: Optional[int] = Query(None, ge=1, le=9999),
    difficulty: Optional[str] = Query(None, description="int 1-4 OR facile/medio/difficile/elite"),
    status: Optional[str] = Query(None, description="available|locked"),
):
    """Phase 19.3 — server-side filters (all optional).

    • team_size ∈ {3,5,7} (validated, 422 otherwise)
    • pwr_min/pwr_max: integer range against `recommended_power`
    • difficulty: int 1-4 or italian alias (facile/medio/difficile/elite)
    • status: "available" (unlocked=True) or "locked" (unlocked=False)
    """
    # Validate inputs early (422 before DB hit)
    if team_size is not None and team_size not in (3, 5, 7):
        raise HTTPException(status_code=422, detail="dungeons.invalid_team_size")
    if pwr_min is not None and pwr_max is not None and pwr_min > pwr_max:
        raise HTTPException(status_code=422, detail="dungeons.invalid_pwr_range")
    diff_int: Optional[int] = None
    if difficulty is not None:
        key = difficulty.strip().lower()
        if key not in _DIFF_ALIASES:
            raise HTTPException(status_code=422, detail="dungeons.invalid_difficulty")
        diff_int = _DIFF_ALIASES[key]
    if status is not None and status not in ("available", "locked"):
        raise HTTPException(status_code=422, detail="dungeons.invalid_status")

    guild = None
    if current_user:
        guild = await db.guilds.find_one(
            {"owner_user_id": current_user["id"]}, {"_id": 0}
        )
    rows = await list_dungeons_for_guild(db, guild)

    # Apply post-projection filters (small dataset, ≤100 rows total)
    def keep(d: dict) -> bool:
        if team_size is not None and int(d.get("required_team_size", 0)) != team_size:
            return False
        rp = int(d.get("recommended_power", 0))
        if pwr_min is not None and rp < pwr_min:
            return False
        if pwr_max is not None and rp > pwr_max:
            return False
        if diff_int is not None and int(d.get("difficulty", 0)) != diff_int:
            return False
        if status == "available" and not d.get("unlocked"):
            return False
        if status == "locked" and d.get("unlocked"):
            return False
        return True

    filtered = [d for d in rows if keep(d)]
    return {
        "dungeons": filtered,
        "count": len(filtered),
        "filters_applied": {
            "team_size": team_size,
            "pwr_min": pwr_min,
            "pwr_max": pwr_max,
            "difficulty": diff_int,
            "status": status,
        },
    }


# ROUND 16.1 Phase 2 — Dungeon preview endpoint.
from app.core.security import get_current_user as _get_current_user  # noqa: E402
from app.guilds.services import user_guild_or_404 as _user_guild  # noqa: E402


@router.get("/{slug}/preview")
async def dungeon_preview(
    slug: str,
    team_ids: str = Query("", description="Comma-separated adventurer ids"),
    current_user: dict = Depends(_get_current_user),
):
    """Pre-launch preview: team_power, success_chance estimate, threats matrix,
    weakness suggestions. All bilingual IT+EN. Used by the FE pre-launch modal.
    """
    from app.dungeons.preview import build_dungeon_preview
    guild = await _user_guild(db, current_user["id"])
    ids = [t for t in (team_ids or "").split(",") if t]
    return await build_dungeon_preview(db, guild=guild, slug=slug, team_ids=ids)


__all__ = ["router"]
