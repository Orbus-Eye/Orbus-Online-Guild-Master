"""Guilds routes (Phase 5.5c + 11.3 onboarding).

Mounted under prefix `/api/guilds`.
"""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.expeditions.services import complete_due_expeditions
from app.guilds.schemas import GuildCreateIn, OnboardingPatchIn
from app.guilds.services import (
    compute_dashboard_stats,
    compute_onboarding_state,
    create_guild_for_user,
    guild_public,
    patch_onboarding,
    user_guild_or_404,
)
from app.onboarding.services import ensure_starter_roster


router = APIRouter(prefix="/api/guilds", tags=["guilds"])


@router.post("", status_code=201)
async def create_guild(
    payload: GuildCreateIn, current_user: dict = Depends(get_current_user)
):
    guild_doc = await create_guild_for_user(
        db, current_user["id"], payload.name, payload.description
    )
    # ROUND 5 §I.1 — auto-pop 5 starter adventurers (idempotent).
    try:
        await ensure_starter_roster(db, guild_doc["id"], user_id=current_user["id"])
    except Exception:  # noqa: BLE001
        pass
    return {"guild": guild_public(guild_doc)}


@router.get("/me")
async def get_my_guild(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    # Phase 5.5e: lazy completion sweep
    await complete_due_expeditions(db, guild["id"])
    # Re-fetch guild after sweep (gold/level/onboarding may have changed)
    guild = await user_guild_or_404(db, current_user["id"])

    payload = guild_public(guild)
    stats = await compute_dashboard_stats(db, guild)
    payload.update(stats)
    # Phase 11.3: derive onboarding suggested step from real state + lazy migration
    onboarding = await compute_onboarding_state(db, guild, stats)
    payload.update(onboarding)
    return {"guild": payload}


@router.patch("/onboarding")
async def update_onboarding(
    payload: OnboardingPatchIn,
    current_user: dict = Depends(get_current_user),
):
    """Phase 11.3 — Update onboarding fields (step / dismissed / completed)."""
    guild = await user_guild_or_404(db, current_user["id"])
    updated_guild = await patch_onboarding(
        db,
        guild,
        step=payload.step,
        dismissed=payload.dismissed,
        completed=payload.completed,
    )
    stats = await compute_dashboard_stats(db, updated_guild)
    onboarding = await compute_onboarding_state(db, updated_guild, stats)
    return {
        "guild": guild_public(updated_guild),
        **onboarding,
    }


__all__ = ["router"]
