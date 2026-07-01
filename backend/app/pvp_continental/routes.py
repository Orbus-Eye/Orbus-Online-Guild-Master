"""ROUND 16.3 Phase 7A — PvP Continental public routes."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.pvp_continental.services import (
    create_challenge, decline_challenge, get_battle_detail,
    list_battles_mine, list_opponents, respond_to_challenge,
)


router = APIRouter(prefix="/api/pvp", tags=["pvp_continental"])


def _coerce_adv_ids(payload: dict | None) -> list[str]:
    """Round 16.3 Iter B (P2.4) — extract adventurer_ids WITHOUT Pydantic
    pre-validation so that guild-level gate (403) and defender lookup
    (404) fire before payload shape errors (422 → 400)."""
    if not isinstance(payload, dict):
        return []
    raw = payload.get("adventurer_ids") or []
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if isinstance(x, (str, int))]


@router.get("/opponents")
async def opponents(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    rows = await list_opponents(db, guild)
    return {"opponents": rows, "count": len(rows)}


@router.post("/challenge/{defender_guild_id}")
async def challenge(
    defender_guild_id: str,
    payload: dict = Body(default_factory=dict),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await create_challenge(
        db, challenger_guild=guild,
        defender_guild_id=defender_guild_id,
        adventurer_ids=_coerce_adv_ids(payload),
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
    battle_id: str,
    payload: dict = Body(default_factory=dict),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await respond_to_challenge(
        db, defender_guild=guild, battle_id=battle_id,
        adventurer_ids=_coerce_adv_ids(payload),
    )


@router.post("/battles/{battle_id}/decline")
async def decline(
    battle_id: str,
    payload: dict = Body(default_factory=dict),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await decline_challenge(
        db, defender_guild=guild, battle_id=battle_id,
    )
