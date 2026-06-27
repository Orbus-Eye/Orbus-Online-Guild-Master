"""Crafting routes (Phase 14.6 ROUND 3.B).

- GET  /api/recipes              → list recipes with per-guild eligibility
- POST /api/recipes/{slug}/craft → atomic craft action
"""
from fastapi import APIRouter, Depends, Query

from app.core.database import db
from app.core.security import get_current_user
from app.crafting.services import craft_recipe, list_recipes_with_eligibility
from app.guilds.services import user_guild_or_404
from app.territory.guards import require_unlocked


router = APIRouter(prefix="/api/recipes", tags=["crafting"])


@router.get("")
async def get_recipes(
    lang: str = Query(default="it", pattern=r"^(it|en)$"),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await list_recipes_with_eligibility(db, guild, lang=lang)


@router.post("/{recipe_slug}/craft", status_code=200, dependencies=[Depends(require_unlocked("workshop.craft.basic"))])
async def post_craft(
    recipe_slug: str,
    lang: str = Query(default="it", pattern=r"^(it|en)$"),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await craft_recipe(db, guild, recipe_slug, lang=lang)


__all__ = ["router"]
