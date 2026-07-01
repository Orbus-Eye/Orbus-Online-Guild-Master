"""ROUND 4 — Forge routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.territory.guards import require_unlocked
from app.forge.services import (
    refine_instance,
    enchant_options,
    apply_enchant,
    reroll_affixes,
    disenchant_instance,
    list_sets,
    list_enchants,
    adventurer_equipment_detail,
)


router = APIRouter(prefix="/api", tags=["forge"])


class EnchantApplyPayload(BaseModel):
    enchant_slug: str


@router.post("/inventory/{instance_id}/refine", dependencies=[Depends(require_unlocked("forge.refine"))])
async def refine_route(
    instance_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await refine_instance(
        db, guild=guild, user_id=current_user["id"], instance_id=instance_id,
    )


@router.post("/inventory/{instance_id}/enchant-options")
async def enchant_options_route(
    instance_id: str,
    n: int = Query(4, ge=3, le=5),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await enchant_options(db, guild=guild, instance_id=instance_id, n=n)


@router.post("/inventory/{instance_id}/enchant", dependencies=[Depends(require_unlocked("forge.enchant"))])
async def enchant_route(
    instance_id: str,
    payload: EnchantApplyPayload,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await apply_enchant(
        db, guild=guild, user_id=current_user["id"],
        instance_id=instance_id, enchant_slug=payload.enchant_slug,
    )


@router.post("/inventory/{instance_id}/disenchant", dependencies=[Depends(require_unlocked("forge.disenchant"))])
async def disenchant_route(
    instance_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await disenchant_instance(
        db, guild=guild, user_id=current_user["id"], instance_id=instance_id,
    )


@router.post("/inventory/{instance_id}/reroll-affixes", dependencies=[Depends(require_unlocked("forge.reroll"))])
async def reroll_route(
    instance_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await reroll_affixes(
        db, guild=guild, user_id=current_user["id"], instance_id=instance_id,
    )


@router.get("/sets")
async def list_sets_route():
    rows = await list_sets(db)
    return {"sets": rows}


@router.get("/enchants")
async def list_enchants_route():
    rows = await list_enchants(db)
    return {"enchants": rows}


@router.get("/adventurers/{adventurer_id}/equipment-detail")
async def adventurer_equipment_route(
    adventurer_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"]}, {"_id": 0, "id": 1},
    )
    if not adv:
        from fastapi import HTTPException
        raise HTTPException(404, "adventurer not found")
    return await adventurer_equipment_detail(db, adventurer_id, guild["id"])


__all__ = ["router"]
