"""Leaderboard routes (Phase 9.1 + ROUND 11.3 multi-category).

* `/guilds` — legacy peak-power ranking (Phase 9.1).
* `/raids` — legacy raid-score ranking (Phase 19).
* `/` (NEW R11.3) — unified multi-category endpoint with `?category=`
  parameter, 8 categories, 60s in-memory cache.
* `/categories` (NEW R11.3) — catalog of available categories for the FE
  picker (slug + IT label + IT description).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Header, Query, Request, Response

from app.core.database import db
from app.leaderboard.multi_category import (
    category_meta,
    get_category_rows,
    list_categories,
)
from app.leaderboard.services import get_guild_leaderboard, get_raids_leaderboard


router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


async def _resolve_caller_guild_public_id(request: Request, authorization: str | None) -> str | None:
    """Best-effort resolution of the caller's guild public_id.

    Multi-category leaderboard is PUBLIC (no auth required), but if a
    valid token is present we use it to fill `is_me` + `my_entry`. On any
    auth failure we return None silently — we don't 401 a public endpoint.

    Resolution order:
      1. `access_token` httpOnly cookie (current Round 11 flow).
      2. `Authorization: Bearer <jwt>` (legacy + test compat).
    """
    import jwt
    from app.core.security import ACCESS_COOKIE_NAME, JWT_SECRET, JWT_ALGORITHM
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        return None
    try:
        g = await db.guilds.find_one(
            {"owner_user_id": user_id},
            {"_id": 0, "public_id": 1, "id": 1},
        )
        if not g:
            return None
        return g.get("public_id") or g["id"][:8]
    except Exception:
        return None


@router.get("/guilds")
async def list_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=1000),
):
    """Public guild leaderboard ordered by peak team power (Phase 8 sticky field)."""
    return await get_guild_leaderboard(db, limit=limit, offset=offset)


@router.get("/raids")
async def list_raid_leaderboard(
    limit: int = Query(20, ge=1, le=100),  # cap intenzionale 100 — privacy + perf
    offset: int = Query(0, ge=0, le=1000),
):
    """Phase 19 — Public raid leaderboard ordered by max_raid_score.

    Privacy: applies the same `is_test_user=True` filter as `/guilds`.
    Returns one row per (guild, raid_dungeon_slug) showing the best score.
    `limit ∈ [1, 100]`, `offset ∈ [0, 1000]` — cap intentional for perf.
    """
    return await get_raids_leaderboard(db, limit=limit, offset=offset)


@router.get("/categories")
async def list_leaderboard_categories(scope: str = Query("global")):
    """ROUND 11.3 — Catalog of multi-category leaderboard slugs (FE picker).
    ROUND 12 — `?scope=season` returns the seasonal category catalog.
    """
    if scope == "season":
        from app.leaderboard.seasonal import list_seasonal_categories
        return {"scope": "season", "categories": list_seasonal_categories()}
    return {"scope": "global", "categories": list_categories()}


@router.get("")
async def list_multi_category(
    request: Request,
    response: Response,
    category: str = Query(..., min_length=2, max_length=64),
    limit: int = Query(50, ge=1, le=100),
    scope: str = Query("global"),
    season: str = Query("current"),
    authorization: str | None = Header(default=None),
):
    """ROUND 11.3 — Multi-category leaderboard.
    ROUND 12 — `?scope=season&season=<slug|current>` switches to seasonal
    aggregates. Default scope=global preserves backward compatibility.

    `?category=<slug>` is required. 60s in-memory cache; sets `X-Cache: hit|miss`.
    If the caller is authenticated (cookie/Bearer), the response also
    includes `my_entry` with the caller's guild rank.
    Privacy: test artifacts and test users excluded.
    """
    if scope == "season":
        from app.seasons.services import get_current_season, get_season_by_slug
        from app.leaderboard.seasonal import get_seasonal_rows, seasonal_category_meta
        if season == "current":
            s = await get_current_season(db)
        else:
            s = await get_season_by_slug(db, season)
        if not s:
            response.headers["X-Cache"] = "miss"
            return {"scope": "season", "season": season, "category": category,
                    "entries": [], "my_entry": None, "computed_at": datetime.now(timezone.utc).isoformat()}
        rows, hit = await get_seasonal_rows(db, category, s["season_id"])
        meta = seasonal_category_meta(category)
    else:
        rows, hit = await get_category_rows(db, category)
        meta = category_meta(category)
    response.headers["X-Cache"] = "hit" if hit else "miss"

    # Resolve caller's guild (for `is_me` + `my_entry`). PUBLIC endpoint —
    # auth resolution is best-effort.
    me_public_id = await _resolve_caller_guild_public_id(request, authorization)

    # Materialise the public projection with rank + is_me.
    entries = []
    my_entry = None
    for idx, row in enumerate(rows[:limit]):
        is_me = (me_public_id is not None and row["guild_public_id"] == me_public_id)
        out = {
            "rank": idx + 1,
            "guild_public_id": row["guild_public_id"],
            "guild_name": row["guild_name"],
            "score": row["score"],
            "is_me": is_me,
        }
        # ROUND 12.C — Pass-through `league` for seasonal arena_* entries.
        if "league" in row:
            out["league"] = row["league"]
        entries.append(out)

    # If the caller is not in the top `limit`, scan the rest for `my_entry`.
    if me_public_id is not None and not any(e["is_me"] for e in entries):
        for idx, row in enumerate(rows):
            if row["guild_public_id"] == me_public_id:
                my_entry = {
                    "rank": idx + 1,
                    "guild_public_id": row["guild_public_id"],
                    "guild_name": row["guild_name"],
                    "score": row["score"],
                    "is_me": True,
                }
                if "league" in row:
                    my_entry["league"] = row["league"]
                break
    elif me_public_id is not None:
        my_entry = next((e for e in entries if e["is_me"]), None)

    # ROUND 12.C — Use the scope-aware meta computed above (no double resolution).
    return {
        "category": meta["slug"],
        "category_label_it": meta["label_it"],
        "category_description_it": meta["description_it"],
        "scope": scope,
        "season_slug": (s["slug"] if scope == "season" and s else None),
        "entries": entries,
        "my_entry": my_entry,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["router"]
