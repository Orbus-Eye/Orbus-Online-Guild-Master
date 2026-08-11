"""FASE 9I — ADDESTRAMENTO routes (solo XP; niente specializzazioni).

I vecchi endpoint ROUND 6C/6E (`/catalog`, `/specialize/{id}`,
`/respec/{id}`) sono stati RIMOSSI insieme alle specializzazioni.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.training.services import (
    cancel_training_session,
    start_training_session,
    training_overview,
    training_preview,
)


router = APIRouter(prefix="/api/training", tags=["training"])


class StartTrainingIn(BaseModel):
    adventurer_id: str = Field(..., min_length=8, max_length=64)
    duration_hours: int = Field(..., ge=1, le=24)


@router.get("")
async def get_training(current_user: dict = Depends(get_current_user)):
    """Stato della sala: sessioni attive (con countdown server-side),
    capacità 0/2·1/2·2/2, benchmark di gilda e storico recente."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await training_overview(db, guild=guild)


@router.get("/preview/{adventurer_id}")
async def get_training_preview(
    adventurer_id: str,
    current_user: dict = Depends(get_current_user),
):
    """XP/h, bonus recupero (+50% sotto il benchmark) e XP prevista."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await training_preview(
        db, guild=guild, adventurer_id=adventurer_id,
    )


@router.post("/start")
async def post_start_training(
    payload: StartTrainingIn,
    current_user: dict = Depends(get_current_user),
):
    """Avvia una sessione (max 24h, max 2 contemporanee, server-side)."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await start_training_session(
        db,
        guild=guild,
        actor_user_id=current_user["id"],
        adventurer_id=payload.adventurer_id,
        duration_hours=payload.duration_hours,
    )


@router.post("/{session_id}/cancel")
async def post_cancel_training(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Interrompe la sessione: XP per le ore INTERE trascorse, poi rilascio."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await cancel_training_session(
        db, guild=guild, session_id=session_id,
    )


__all__ = ["router"]
