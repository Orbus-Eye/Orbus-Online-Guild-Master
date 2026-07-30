"""Player-authored adventurer creation routes.

The random candidate pool, paid refresh and freeze bench have been removed
from the player-facing API. The historical service modules remain only as
migration references until their stored data is cleaned up.
"""
from fastapi import APIRouter, Depends

from app.adventurers.services import adventurer_public
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.recruitment.base_models import (
    create_base_model,
    get_base_model_options,
)
from app.recruitment.schemas import BaseModelCreateIn


router = APIRouter(prefix="/api/recruitment", tags=["recruitment"])


@router.get("/model")
async def get_model_creation_options(
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_base_model_options(db, guild_id=guild["id"])


@router.post("/model", status_code=201)
async def post_create_base_model(
    payload: BaseModelCreateIn,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    adventurer, updated_guild = await create_base_model(
        db,
        guild=guild,
        actor_user_id=current_user["id"],
        name=payload.name,
        race_slug=payload.race_slug,
        gender=payload.gender,
    )
    return {
        "adventurer": adventurer_public(adventurer),
        "guild": {"gold": updated_guild["gold"]},
    }


__all__ = ["router"]
