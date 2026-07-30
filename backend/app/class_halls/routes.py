"""ROUND 16.0 — Class Halls REST routes."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query

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
from app.class_halls.journey import (
    complete_safe_trial,
    confirm_class_hall_assignment,
    list_assignment_choices,
    start_safe_trial,
)
from app.adventurers.services import adventurer_public
from app.class_halls.item_track import (
    claim_class_hall_track_item,
    get_class_hall_item_track,
)
from app.class_halls.collection_book import get_class_hall_collection_book
from app.class_halls.build_lab import get_class_hall_build_lab


router = APIRouter(prefix="/api/class-halls", tags=["class-halls"])


@router.get("")
async def get_my_class_halls(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    halls = await list_class_halls(db, guild_id=guild["id"])
    # Lazy seed for guilds that predate Round 16.
    if not halls:
        await seed_class_halls_for_guild(
            db, guild_id=guild["id"], actor_user_id=user["id"]
        )
        halls = await list_class_halls(db, guild_id=guild["id"])
    # ROUND 16.1 Phase 3 — enrich with adventurer counts + top3 + specs.
    halls = await enrich_halls_for_ui(db, guild_id=guild["id"], halls=halls)
    unlocked_count = sum(1 for h in halls if h.get("is_unlocked"))
    specs_unlocked = sum(len(h.get("unlocked_specializations") or []) for h in halls)
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


@router.get("/assignment/choices")
async def get_class_hall_assignment_choices(
    user: dict = Depends(get_current_user),
):
    await user_guild_or_404(db, user["id"])
    return {"halls": await list_assignment_choices()}


@router.post("/{hall_id}/trial/start")
async def post_start_class_hall_trial(
    hall_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, user["id"])
    adventurer_id = (payload or {}).get("adventurer_id")
    if not isinstance(adventurer_id, str) or not adventurer_id.strip():
        raise HTTPException(
            400,
            {
                "code": "class_hall.bad_payload",
                "user_message": "Avventuriero mancante o non valido.",
            },
        )
    trial = await start_safe_trial(
        db,
        guild_id=guild["id"],
        adventurer_id=adventurer_id,
        hall_id=hall_id,
        actor_user_id=user["id"],
    )
    return {"trial": trial}


@router.post("/{hall_id}/trial/complete")
async def post_complete_class_hall_trial(
    hall_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, user["id"])
    trial = await complete_safe_trial(
        db,
        guild_id=guild["id"],
        adventurer_id=(payload or {}).get("adventurer_id") or "",
        hall_id=hall_id,
        trial_id=(payload or {}).get("trial_id") or "",
        completed_steps=(payload or {}).get("completed_steps") or [],
        actor_user_id=user["id"],
    )
    return {"trial": trial}


@router.post("/{hall_id}/class/confirm")
async def post_confirm_class_hall_assignment(
    hall_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, user["id"])
    result = await confirm_class_hall_assignment(
        db,
        guild_id=guild["id"],
        adventurer_id=(payload or {}).get("adventurer_id") or "",
        hall_id=hall_id,
        trial_id=(payload or {}).get("trial_id") or "",
        explicit_confirmation=(payload or {}).get("explicit_confirmation") is True,
        actor_user_id=user["id"],
    )
    return {
        "adventurer": adventurer_public(result["adventurer"]),
        "reward": result["reward"],
        "idempotent": result["idempotent"],
        "micro_log_it": (
            f"{result['adventurer']['name']} ha scelto "
            f"{result['adventurer']['class_name']} davanti a "
            f"{result['adventurer']['hall_master_witness_npc']}."
        ),
    }


@router.get("/{hall_id}/item-track")
async def get_hall_item_track(
    hall_id: str,
    adventurer_id: str = Query(..., min_length=8, max_length=64),
    user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, user["id"])
    return await get_class_hall_item_track(
        db,
        guild_id=guild["id"],
        adventurer_id=adventurer_id,
        hall_id=hall_id,
    )


@router.post("/{hall_id}/item-track/{item_slug}/claim")
async def post_claim_hall_track_item(
    hall_id: str,
    item_slug: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, user["id"])
    return await claim_class_hall_track_item(
        db,
        guild_id=guild["id"],
        adventurer_id=(payload or {}).get("adventurer_id") or "",
        hall_id=hall_id,
        item_slug=item_slug,
        actor_user_id=user["id"],
    )


@router.get("/{hall_id}/build-lab")
async def get_hall_build_lab(
    hall_id: str,
    adventurer_id: str = Query(..., min_length=8, max_length=64),
    user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, user["id"])
    return await get_class_hall_build_lab(
        db,
        guild_id=guild["id"],
        adventurer_id=adventurer_id,
        hall_id=hall_id,
    )


@router.get("/collection-book")
async def get_collection_book(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await get_class_hall_collection_book(
        db,
        guild_id=guild["id"],
    )


@router.get("/{class_slug}")
async def get_class_hall_detail(
    class_slug: str,
    user: dict = Depends(get_current_user),
):
    if class_slug not in BASE_CLASS_SLUGS:
        raise HTTPException(
            404,
            {
                "code": "class_hall.unknown_class",
                "user_message": f"Classe '{class_slug}' non riconosciuta.",
            },
        )
    guild = await user_guild_or_404(db, user["id"])
    hall = await get_class_hall(db, guild_id=guild["id"], class_slug=class_slug)
    if not hall:
        # Lazy seed.
        await seed_class_halls_for_guild(
            db, guild_id=guild["id"], actor_user_id=user["id"]
        )
        hall = await get_class_hall(db, guild_id=guild["id"], class_slug=class_slug)
    return {"hall": hall}


@router.post("/{class_slug}/unlock-specialization")
async def post_unlock_specialization(
    class_slug: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    spec_slug = (payload or {}).get("specialization_slug")
    if not spec_slug or not isinstance(spec_slug, str):
        raise HTTPException(
            400,
            {
                "code": "class_hall.bad_payload",
                "user_message": "Specializzazione mancante o non valida.",
            },
        )
    guild = await user_guild_or_404(db, user["id"])
    hall = await unlock_specialization(
        db,
        guild_id=guild["id"],
        class_slug=class_slug,
        specialization_slug=spec_slug,
        actor_user_id=user["id"],
    )
    return {"hall": hall}
