"""ROUND 16.0 — Class Halls REST routes."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.class_halls.services import (
    BASE_CLASS_SLUGS,
    enrich_halls_for_ui,
    get_class_hall,
    list_class_halls,
    seed_class_halls_for_guild,
    unlock_specialization,
)


router = APIRouter(prefix="/api/class-halls", tags=["class-halls"])


@router.get("")
async def get_my_class_halls(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    halls = await list_class_halls(db, guild_id=guild["id"])
    # Lazy seed for guilds that predate Round 16.
    if not halls:
        await seed_class_halls_for_guild(
            db, guild_id=guild["id"], actor_user_id=user["id"])
        halls = await list_class_halls(db, guild_id=guild["id"])
    # ROUND 16.1 Phase 3 — enrich with adventurer counts + top3 + specs.
    halls = await enrich_halls_for_ui(db, guild_id=guild["id"], halls=halls)
    unlocked_count = sum(1 for h in halls if h.get("is_unlocked"))
    specs_unlocked = sum(len(h.get("unlocked_specializations") or [])
                          for h in halls)
    return {
        "halls": halls,
        "base_classes": list(BASE_CLASS_SLUGS),
        "kpi": {
            "halls_unlocked": unlocked_count,
            "halls_total": len(halls),
            "specs_unlocked": specs_unlocked,
            "specs_total": len(halls) * 3,
        },
    }


@router.get("/{class_slug}")
async def get_class_hall_detail(
    class_slug: str, user: dict = Depends(get_current_user),
):
    if class_slug not in BASE_CLASS_SLUGS:
        raise HTTPException(404, {
            "code": "class_hall.unknown_class",
            "user_message": f"Classe '{class_slug}' non riconosciuta.",
        })
    guild = await user_guild_or_404(db, user["id"])
    hall = await get_class_hall(
        db, guild_id=guild["id"], class_slug=class_slug)
    if not hall:
        # Lazy seed.
        await seed_class_halls_for_guild(
            db, guild_id=guild["id"], actor_user_id=user["id"])
        hall = await get_class_hall(
            db, guild_id=guild["id"], class_slug=class_slug)
    return {"hall": hall}


@router.post("/{class_slug}/unlock-specialization")
async def post_unlock_specialization(
    class_slug: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    spec_slug = (payload or {}).get("specialization_slug")
    if not spec_slug or not isinstance(spec_slug, str):
        raise HTTPException(400, {
            "code": "class_hall.bad_payload",
            "user_message": "Specializzazione mancante o non valida.",
        })
    guild = await user_guild_or_404(db, user["id"])
    hall = await unlock_specialization(
        db, guild_id=guild["id"], class_slug=class_slug,
        specialization_slug=spec_slug, actor_user_id=user["id"],
    )
    return {"hall": hall}
