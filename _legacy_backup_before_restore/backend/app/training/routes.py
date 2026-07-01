"""ROUND 6C — Training routes (read catalog + apply spec)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.training.services import (
    apply_specialization,
    get_available_specs,
    respec_adventurer,
)


router = APIRouter(prefix="/api/training", tags=["training"])


class ApplySpecIn(BaseModel):
    spec_slug: str = Field(..., min_length=1, max_length=64)


class RespecIn(BaseModel):
    new_spec_slug: str = Field(..., min_length=1, max_length=64)
    discard_signature_items: bool = Field(default=False)


@router.get("/catalog")
async def get_training_catalog(current_user: dict = Depends(get_current_user)):
    """List the specs unlocked for this guild + the apply cost.

    Empty list (with `tier=null`) means the Campo di Addestramento is still
    locked — FE shows a "Sblocca per specializzare" CTA pointing to
    /territory.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_available_specs(db, guild_id=guild["id"])


@router.post("/specialize/{adventurer_id}")
async def post_specialize(
    adventurer_id: str,
    payload: ApplySpecIn,
    current_user: dict = Depends(get_current_user),
):
    """Apply a specialization to an adventurer.

    Atomic: gold debit + signature_item creation + adventurer field update
    all happen in sequence with structured failure detail. See
    `training.services.apply_specialization` for the 5-step flow.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    return await apply_specialization(
        db,
        guild_id=guild["id"],
        actor_user_id=current_user["id"],
        adventurer_id=adventurer_id,
        spec_slug=payload.spec_slug,
    )


@router.post("/respec/{adventurer_id}")
async def post_respec(
    adventurer_id: str,
    payload: RespecIn,
    current_user: dict = Depends(get_current_user),
):
    """ROUND 6E — Change an adventurer's specialization.

    Atomic, server-authoritative. Cost escalates by respec_count
    (800g→1200g→2000g, +1/2/3 lesser_arcane_dust). 24h cooldown.
    The current signature item must be explicitly discarded via the
    `discard_signature_items` flag (Q3=c — irreversible, no duplication).
    """
    guild = await user_guild_or_404(db, current_user["id"])
    return await respec_adventurer(
        db,
        guild_id=guild["id"],
        actor_user_id=current_user["id"],
        adventurer_id=adventurer_id,
        new_spec_slug=payload.new_spec_slug,
        discard_signature_items=payload.discard_signature_items,
    )


__all__ = ["router"]
