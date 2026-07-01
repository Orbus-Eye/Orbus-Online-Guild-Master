"""ROUND 16.3 Phase 7A — PvP Continental public routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.pvp_continental.models import (
    ChallengePayload, DeclinePayload, RespondPayload,
)
from app.pvp_continental.services import (
    create_challenge, decline_challenge, get_battle_detail,
    list_battles_mine, list_opponents, respond_to_challenge,
)


router = APIRouter(prefix="/api/pvp", tags=["pvp_continental"])


@router.get("/opponents")
async def opponents(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    rows = await list_opponents(db, guild)
    return {"opponents": rows, "count": len(rows)}


@router.post("/challenge/{defender_guild_id}")
async def challenge(
    defender_guild_id: str,
    payload: ChallengePayload,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await create_challenge(
        db, challenger_guild=guild,
        defender_guild_id=defender_guild_id,
        adventurer_ids=payload.adventurer_ids,
    )


@router.get("/battles/mine")
async def battles_mine(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await list_battles_mine(db, guild)


@router.get("/battles/{battle_id}")
async def battle_detail(
    battle_id: str, current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_battle_detail(db, guild=guild, battle_id=battle_id)


@router.post("/battles/{battle_id}/respond")
async def respond(
    battle_id: str, payload: RespondPayload,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await respond_to_challenge(
        db, defender_guild=guild, battle_id=battle_id,
        adventurer_ids=payload.adventurer_ids,
    )


@router.post("/battles/{battle_id}/decline")
async def decline(
    battle_id: str, payload: DeclinePayload | None = None,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await decline_challenge(
        db, defender_guild=guild, battle_id=battle_id,
    )
