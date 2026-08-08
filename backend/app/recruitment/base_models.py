"""Deterministic player-authored adventurer creation.

The old rotating candidate pool and freeze bench are intentionally not used.
After the five free founders, the player commissions one neutral base model
at a time and chooses every identity field exposed by this contract.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.adventurers.common import build_base_adventurer
from app.territory.guards import compute_adventurer_cap_state


BASE_MODEL_STARTING_COST_GOLD = 100
BASE_MODEL_COST_STEP_GOLD = 25
BASE_MODEL_COST_CAP_GOLD = 2500
FREE_FOUNDER_COUNT = 5

_NAME_RE = re.compile(r"^[\w\s'\-]+$", re.UNICODE)


def base_model_cost_for_created_total(created_total: int) -> int:
    """Progressive gold cost after the five free founding adventurers."""
    total = max(0, int(created_total or 0))
    if total < FREE_FOUNDER_COUNT:
        return 0
    return min(
        BASE_MODEL_COST_CAP_GOLD,
        BASE_MODEL_STARTING_COST_GOLD
        + (total - FREE_FOUNDER_COUNT) * BASE_MODEL_COST_STEP_GOLD,
    )


def base_model_cost_for_active_roster(active_roster: int) -> int:
    """Compatibility alias for old callers; argument now means created total."""
    return base_model_cost_for_created_total(active_roster)


async def get_base_model_options(db, *, guild_id: str) -> dict:
    cap_state = await compute_adventurer_cap_state(db, guild_id)
    active = int(cap_state["current"])
    created_total = await db.adventurers.count_documents({"guild_id": guild_id})
    races = await db.races.find(
        {"is_active": True, "is_playable": True},
        {
            "_id": 0,
            "slug": 1,
            "name_it": 1,
            "name_en": 1,
            "lore_group": 1,
        },
    ).sort("name_it", 1).to_list(200)
    return {
        "method": "player_authored_base_model",
        "random_generation": False,
        "free_founders": FREE_FOUNDER_COUNT,
        "active_roster": active,
        "created_total": int(created_total),
        "roster_cap": int(cap_state["cap"]),
        "cost_gold": base_model_cost_for_created_total(created_total),
        "starting_rarity": "Common",
        "starting_level": 1,
        "starting_stats": {
            "strength": 5,
            "agility": 5,
            "intellect": 5,
            "endurance": 5,
            "faith": 5,
        },
        "genders": [
            {"id": "female", "name_it": "Femmina"},
            {"id": "male", "name_it": "Maschio"},
        ],
        "races": races,
    }


async def create_base_model(
    db,
    *,
    guild: dict,
    actor_user_id: str,
    name: str,
    race_slug: str,
    gender: str,
) -> tuple[dict, dict]:
    """Create one Common, classless, deterministic adventurer."""
    normalized_name = " ".join(name.strip().split())
    if not (2 <= len(normalized_name) <= 40) or not _NAME_RE.fullmatch(
        normalized_name
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "base_model.invalid_name",
                "user_message": (
                    "Il nome deve contenere 2-40 caratteri: lettere, spazi, "
                    "apostrofi o trattini."
                ),
            },
        )
    if gender not in {"female", "male"}:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "base_model.invalid_gender",
                "user_message": "Scegli il genere del nuovo avventuriero.",
            },
        )
    race = await db.races.find_one(
        {"slug": race_slug, "is_active": True, "is_playable": True},
        {"_id": 0, "slug": 1},
    )
    if not race:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "base_model.invalid_race",
                "user_message": "Scegli una razza giocabile valida.",
            },
        )
    duplicate = await db.adventurers.find_one(
        {
            "guild_id": guild["id"],
            "is_retired": {"$ne": True},
            "name": {"$regex": f"^{re.escape(normalized_name)}$", "$options": "i"},
        },
        {"_id": 0, "id": 1},
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "base_model.name_in_use",
                "user_message": "Un avventuriero attivo usa già questo nome.",
            },
        )

    cap_state = await compute_adventurer_cap_state(db, guild["id"])
    active = int(cap_state["current"])
    if active >= int(cap_state["cap"]):
        raise HTTPException(
            status_code=423,
            detail={
                "code": "roster_over_capacity",
                "current": active,
                "cap": int(cap_state["cap"]),
                "user_message": "Potenzia i Dormitori prima di creare un nuovo modello.",
            },
        )
    created_total = await db.adventurers.count_documents({"guild_id": guild["id"]})
    cost = base_model_cost_for_created_total(created_total)
    now = datetime.now(timezone.utc)
    updated_guild = await db.guilds.find_one_and_update(
        {"id": guild["id"], "gold": {"$gte": cost}},
        {"$inc": {"gold": -cost}, "$set": {"updated_at": now.isoformat()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_guild:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "economy.insufficient_gold",
                "cost_gold": cost,
                "user_message": f"Servono {cost} oro per formare questo avventuriero.",
            },
        )

    adventurer = build_base_adventurer(
        guild["id"],
        name=normalized_name,
        now=now,
        race_slug=race_slug,
        gender=gender,
    )
    try:
        await db.adventurers.insert_one(dict(adventurer))
    except Exception:
        await db.guilds.update_one(
            {"id": guild["id"]},
            {"$inc": {"gold": cost}, "$set": {"updated_at": now.isoformat()}},
        )
        raise

    # A second request can pass the pre-insert capacity check concurrently.
    # Re-count after insertion and roll this model back if it lost that race.
    post_insert_cap = await compute_adventurer_cap_state(db, guild["id"])
    if int(post_insert_cap["current"]) > int(post_insert_cap["cap"]):
        await db.adventurers.delete_one(
            {"id": adventurer["id"], "guild_id": guild["id"]}
        )
        await db.guilds.update_one(
            {"id": guild["id"]},
            {"$inc": {"gold": cost}, "$set": {"updated_at": now.isoformat()}},
        )
        raise HTTPException(
            status_code=409,
            detail={
                "code": "roster.capacity_race",
                "user_message": (
                    "Un'altra creazione ha occupato l'ultimo posto disponibile. "
                    "L'oro è stato restituito."
                ),
            },
        )

    try:
        from app.audit.log import write_audit

        await write_audit(
            db,
            event_type="adventurer_base_model_created",
            actor_user_id=actor_user_id,
            actor_guild_id=guild["id"],
            related_entity_id=adventurer["id"],
            source="recruitment.base_model",
            gold_delta=-cost,
            metadata={
                "name": normalized_name,
                "race_slug": race_slug,
                "gender": gender,
                "rarity": "Common",
                "random_generation": False,
            },
        )
    except Exception:
        pass
    return adventurer, updated_guild


__all__ = [
    "BASE_MODEL_COST_CAP_GOLD",
    "BASE_MODEL_COST_STEP_GOLD",
    "BASE_MODEL_STARTING_COST_GOLD",
    "FREE_FOUNDER_COUNT",
    "base_model_cost_for_active_roster",
    "base_model_cost_for_created_total",
    "create_base_model",
    "get_base_model_options",
]
