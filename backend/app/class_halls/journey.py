"""Classless recruit → safe trial → Class Hall assignment journey."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.audit.log import write_audit
from app.adventurers.classless import is_explicit_classless_recruit
from app.class_halls.catalog import (
    ClassHallProfile,
    class_hall_choices_public,
    get_class_hall_profile,
)
from app.class_halls.feature_flags import assignment_enabled_for_hall


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _error(status: int, code: str, message: str, **extra) -> HTTPException:
    return HTTPException(
        status_code=status,
        detail={"code": code, "user_message": message, **extra},
    )


def _require_live_hall(hall_id: str) -> ClassHallProfile:
    profile = get_class_hall_profile(hall_id)
    if not profile:
        raise _error(404, "class_hall.unknown_hall", "Sala di Classe non riconosciuta.")
    if profile.lifecycle != "ACTIVE" or profile.readiness != "APPROVED":
        raise _error(
            423,
            "class_hall.not_ready",
            "Questa Sala non è ancora pronta per i tester.",
        )
    if not assignment_enabled_for_hall(profile.hall_id):
        raise _error(
            423,
            "class_hall.assignment_disabled",
            "La scelta di questa Sala non è ancora abilitata sul server.",
        )
    return profile


def _is_classless(adventurer: dict) -> bool:
    return is_explicit_classless_recruit(adventurer)


async def list_assignment_choices() -> list[dict]:
    """Public read model. Disabled choices remain visible with a gate marker."""
    choices = class_hall_choices_public()
    for choice in choices:
        choice["assignment_enabled"] = assignment_enabled_for_hall(choice["hall_id"])
    return choices


async def start_safe_trial(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
    actor_user_id: str | None,
) -> dict:
    profile = _require_live_hall(hall_id)
    adventurer = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adventurer:
        raise _error(
            404, "class_hall.adventurer_not_found", "Avventuriero non trovato."
        )
    if not _is_classless(adventurer):
        raise _error(
            409,
            "class_hall.class_already_chosen",
            "Questo avventuriero ha già scelto il proprio sentiero.",
        )

    existing = await db.class_hall_trial_sessions.find_one(
        {
            "guild_id": guild_id,
            "adventurer_id": adventurer_id,
            "hall_id": profile.hall_id,
            "status": {"$in": ["started", "completed"]},
        },
        {"_id": 0},
    )
    if existing:
        return existing

    now = _now()
    trial = {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "adventurer_id": adventurer_id,
        "hall_id": profile.hall_id,
        "canonical_class_slug": profile.canonical_class_slug,
        "status": "started",
        "safe_mode": True,
        "rewards_enabled": False,
        "script_version": profile.readiness_version,
        "required_steps": list(profile.trial_steps),
        "started_at": now.isoformat(),
        "completed_at": None,
        "expires_at": now + timedelta(hours=2),
    }
    await db.class_hall_trial_sessions.insert_one(dict(trial))
    try:
        await write_audit(
            db,
            event_type="class_hall_safe_trial_started",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            related_entity_id=adventurer_id,
            source="class_halls.safe_trial",
            metadata={"hall_id": profile.hall_id, "trial_id": trial["id"]},
        )
    except Exception:
        pass
    return trial


async def complete_safe_trial(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
    trial_id: str,
    completed_steps: list[str],
    actor_user_id: str | None,
) -> dict:
    profile = _require_live_hall(hall_id)
    if tuple(completed_steps or ()) != profile.trial_steps:
        raise _error(
            400,
            "class_hall.trial_steps_invalid",
            "Completa nell'ordine tutti i passaggi della prova sicura.",
        )
    now = _now()
    trial = await db.class_hall_trial_sessions.find_one_and_update(
        {
            "id": trial_id,
            "guild_id": guild_id,
            "adventurer_id": adventurer_id,
            "hall_id": profile.hall_id,
            "status": "started",
            "safe_mode": True,
            "rewards_enabled": False,
            "expires_at": {"$gt": now},
        },
        {
            "$set": {
                "status": "completed",
                "completed_at": now.isoformat(),
                "completion_attestation": "safe_script_ack",
            }
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not trial:
        trial = await db.class_hall_trial_sessions.find_one(
            {
                "id": trial_id,
                "guild_id": guild_id,
                "adventurer_id": adventurer_id,
                "hall_id": profile.hall_id,
            },
            {"_id": 0},
        )
        if not trial:
            raise _error(404, "class_hall.trial_not_found", "Prova sicura non trovata.")
        if trial.get("status") != "completed":
            raise _error(
                409, "class_hall.trial_not_active", "La prova non è più attiva."
            )
    try:
        await write_audit(
            db,
            event_type="class_hall_safe_trial_completed",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            related_entity_id=adventurer_id,
            source="class_halls.safe_trial",
            metadata={"hall_id": profile.hall_id, "trial_id": trial_id},
        )
    except Exception:
        pass
    return trial


async def _resolve_class_doc(db, profile: ClassHallProfile) -> dict | None:
    for slug in (profile.canonical_class_slug, *profile.legacy_class_slugs):
        doc = await db.adventurer_classes.find_one(
            {"slug": slug, "is_active": {"$ne": False}},
            {"_id": 0, "id": 1, "slug": 1},
        )
        if doc:
            return doc
    return None


async def reconcile_starter_item_reward(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    profile: ClassHallProfile,
) -> dict:
    """Deliver exactly one starter item, safely retrying partial failures."""
    grant_id = f"class_hall_starter::{adventurer_id}::{profile.hall_id}"
    item = await db.items.find_one(
        {"slug": profile.starter_item_slug, "is_active": {"$ne": False}},
        {"_id": 0},
    )
    if not item:
        await db.adventurers.update_one(
            {"id": adventurer_id, "guild_id": guild_id},
            {"$set": {"starter_item_reward_status": "catalog_missing"}},
        )
        return {
            "status": "catalog_missing",
            "grant_id": grant_id,
            "item_slug": profile.starter_item_slug,
        }

    now = _now().isoformat()
    await db.class_hall_reward_grants.update_one(
        {"_id": grant_id},
        {
            "$setOnInsert": {
                "_id": grant_id,
                "guild_id": guild_id,
                "adventurer_id": adventurer_id,
                "hall_id": profile.hall_id,
                "item_id": item["id"],
                "item_slug": profile.starter_item_slug,
                "status": "pending",
                "created_at": now,
            }
        },
        upsert=True,
    )

    already_delivered = await db.inventory_items.find_one(
        {
            "guild_id": guild_id,
            "item_id": item["id"],
            "class_hall_grant_ids": grant_id,
        },
        {"_id": 0, "id": 1},
    )
    if not already_delivered:
        updated = await db.inventory_items.update_one(
            {
                "guild_id": guild_id,
                "item_id": item["id"],
                "class_hall_grant_ids": {"$ne": grant_id},
            },
            {
                "$inc": {"quantity": 1},
                "$addToSet": {"class_hall_grant_ids": grant_id},
                "$set": {"updated_at": now},
            },
        )
        if not getattr(updated, "matched_count", 0):
            inventory_id = str(uuid.uuid4())
            try:
                await db.inventory_items.insert_one(
                    {
                        "id": inventory_id,
                        "instance_id": inventory_id,
                        "guild_id": guild_id,
                        "item_id": item["id"],
                        "quantity": 1,
                        "class_hall_grant_ids": [grant_id],
                        "acquired_at": now,
                        "created_at": now,
                        "updated_at": now,
                        "is_bound": False,
                        "refinement_level": 0,
                        "enchants": [],
                        "affixes": [],
                        "reroll_count": 0,
                    }
                )
            except DuplicateKeyError:
                await db.inventory_items.update_one(
                    {
                        "guild_id": guild_id,
                        "item_id": item["id"],
                        "class_hall_grant_ids": {"$ne": grant_id},
                    },
                    {
                        "$inc": {"quantity": 1},
                        "$addToSet": {"class_hall_grant_ids": grant_id},
                        "$set": {"updated_at": now},
                    },
                )

    await db.class_hall_reward_grants.update_one(
        {"_id": grant_id},
        {"$set": {"status": "delivered", "delivered_at": now}},
    )
    await db.adventurers.update_one(
        {"id": adventurer_id, "guild_id": guild_id, "class_hall_id": profile.hall_id},
        {
            "$set": {
                "starter_item_reward_status": "delivered",
                "starter_item_reward_grant_id": grant_id,
            }
        },
    )
    return {
        "status": "delivered",
        "grant_id": grant_id,
        "item_id": item["id"],
        "item_slug": profile.starter_item_slug,
        "item_name_it": item.get("name_it") or item.get("name"),
    }


async def confirm_class_hall_assignment(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
    trial_id: str,
    explicit_confirmation: bool,
    actor_user_id: str | None,
) -> dict:
    profile = _require_live_hall(hall_id)
    if explicit_confirmation is not True:
        raise _error(
            400,
            "class_hall.explicit_confirmation_required",
            "Conferma esplicitamente la Sala scelta.",
        )
    adventurer = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adventurer:
        raise _error(
            404, "class_hall.adventurer_not_found", "Avventuriero non trovato."
        )
    if adventurer.get("class_hall_id"):
        if adventurer.get("class_hall_id") != profile.hall_id:
            raise _error(
                409,
                "class_hall.different_hall_already_chosen",
                "La Sala è già stata scelta e non può essere sostituita.",
            )
        reward = await reconcile_starter_item_reward(
            db,
            guild_id=guild_id,
            adventurer_id=adventurer_id,
            profile=profile,
        )
        fresh = await db.adventurers.find_one(
            {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
        )
        return {
            "adventurer": fresh or adventurer,
            "reward": reward,
            "idempotent": True,
        }
    if not _is_classless(adventurer):
        raise _error(
            409,
            "class_hall.invalid_classless_state",
            "Lo stato della recluta non consente la scelta di una Sala.",
        )

    trial = await db.class_hall_trial_sessions.find_one(
        {
            "id": trial_id,
            "guild_id": guild_id,
            "adventurer_id": adventurer_id,
            "hall_id": profile.hall_id,
            "status": "completed",
            "safe_mode": True,
            "rewards_enabled": False,
            "completion_attestation": "safe_script_ack",
        },
        {"_id": 0, "id": 1, "completed_at": 1},
    )
    if not trial:
        raise _error(
            423,
            "class_hall.safe_trial_required",
            "Completa prima la prova sicura di questa Sala.",
        )
    class_doc = await _resolve_class_doc(db, profile)
    if not class_doc:
        raise _error(
            503,
            "class_hall.class_catalog_missing",
            "Il catalogo della classe non è pronto sul server.",
        )

    now = _now().isoformat()
    assignment_id = str(uuid.uuid4())
    assignment_event = {
        "assignment_id": assignment_id,
        "hall_id": profile.hall_id,
        "canonical_class_slug": profile.canonical_class_slug,
        "class_proficiency": profile.class_proficiency,
        "trial_id": trial_id,
        "assigned_at": now,
        "actor_user_id": actor_user_id,
        "readiness_version": profile.readiness_version,
    }
    assigned = await db.adventurers.find_one_and_update(
        {
            "id": adventurer_id,
            "guild_id": guild_id,
            "recruit_status": "recruit_unassigned",
            "class_slug": None,
            "canonical_class_slug": None,
            "class_proficiency": None,
            "class_hall_id": None,
        },
        {
            "$set": {
                "adventurer_class_id": class_doc["id"],
                "class_name": profile.class_name_it,
                "class_role": profile.class_role,
                "class_proficiency": profile.class_proficiency,
                "class_slug": profile.canonical_class_slug,
                "canonical_class_slug": profile.canonical_class_slug,
                "class_hall_id": profile.hall_id,
                "class_hall_assigned_at": now,
                "hall_master_witness_npc": profile.hall_master_witness_npc,
                "recruit_status": "class_assigned",
                "narrative_intro_shown": True,
                "class_assignment_status": "COMMITTED",
                "class_assignment_id": assignment_id,
                "class_assignment_source": "class_hall",
                "class_assignment_readiness_version": profile.readiness_version,
                "starter_item_reward_status": "pending",
                "updated_at": now,
            },
            "$push": {"class_assignment_history": assignment_event},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not assigned:
        current = await db.adventurers.find_one(
            {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
        )
        if current and current.get("class_hall_id") == profile.hall_id:
            assigned = current
        else:
            raise _error(
                409,
                "class_hall.assignment_race_lost",
                "La recluta è cambiata durante la scelta. Ricarica il roster.",
            )

    reward = await reconcile_starter_item_reward(
        db,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
        profile=profile,
    )
    try:
        await write_audit(
            db,
            event_type="class_hall_class_committed",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            related_entity_id=adventurer_id,
            source="class_halls.confirm",
            metadata={
                "assignment_id": assigned.get("class_assignment_id"),
                "hall_id": profile.hall_id,
                "canonical_class_slug": profile.canonical_class_slug,
                "trial_id": trial_id,
                "starter_item_reward_status": reward["status"],
            },
        )
    except Exception:
        pass
    fresh = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    return {
        "adventurer": fresh or assigned,
        "reward": reward,
        "idempotent": False,
    }


__all__ = [
    "complete_safe_trial",
    "confirm_class_hall_assignment",
    "list_assignment_choices",
    "reconcile_starter_item_reward",
    "start_safe_trial",
]
