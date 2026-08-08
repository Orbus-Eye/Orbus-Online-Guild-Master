"""Reachable, exactly-once acquisition track for all five Hall items."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.audit.log import write_audit
from app.class_halls.catalog import get_class_hall_profile
from app.items.services import item_public


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error(status: int, code: str, message: str, **extra) -> HTTPException:
    return HTTPException(
        status_code=status,
        detail={"code": code, "user_message": message, **extra},
    )


async def _completed_expedition_count(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
) -> int:
    memberships = await db.expedition_members.find(
        {"adventurer_id": adventurer_id},
        {"_id": 0, "expedition_id": 1},
    ).to_list(500)
    expedition_ids = list(
        {
            row.get("expedition_id")
            for row in memberships
            if row.get("expedition_id")
        }
    )
    if not expedition_ids:
        return 0
    return await db.expeditions.count_documents(
        {
            "id": {"$in": expedition_ids},
            "guild_id": guild_id,
            "status": {"$in": ["completed", "success", "failed"]},
        }
    )


async def _load_track_context(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
) -> tuple[object, dict, list[dict]]:
    profile = get_class_hall_profile(hall_id)
    if not profile:
        raise _error(
            404,
            "class_hall.unknown_hall",
            "Sala di Classe non riconosciuta.",
        )
    adventurer = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id},
        {"_id": 0},
    )
    if not adventurer:
        raise _error(
            404,
            "class_hall.adventurer_not_found",
            "Avventuriero non trovato.",
        )
    if adventurer.get("class_hall_id") != hall_id:
        raise _error(
            409,
            "class_hall.item_track_wrong_hall",
            "Questo sentiero appartiene alla Sala scelta dall'avventuriero.",
        )
    items = await db.items.find(
        {
            "source": f"class_hall:{hall_id}",
            "is_active": {"$ne": False},
        },
        {"_id": 0},
    ).sort("acquisition_track_order", 1).to_list(10)
    if len(items) != 5:
        raise _error(
            503,
            "class_hall.item_track_incomplete",
            "Il Sentiero degli oggetti non è ancora completo per questa Sala.",
            expected=5,
            actual=len(items),
        )
    return profile, adventurer, items


async def get_class_hall_item_track(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
) -> dict:
    profile, adventurer, items = await _load_track_context(
        db,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
        hall_id=hall_id,
    )
    item_ids = [item["id"] for item in items]
    grants = await db.class_hall_item_grants.find(
        {
            "guild_id": guild_id,
            "adventurer_id": adventurer_id,
            "item_id": {"$in": item_ids},
            "status": "delivered",
        },
        {"_id": 0, "item_id": 1},
    ).to_list(10)
    claimed_item_ids = {row["item_id"] for row in grants}

    signature = next(
        item for item in items if item.get("acquisition_track_order") == 0
    )
    signature_equipped = await db.equipped_items.find_one(
        {
            "guild_id": guild_id,
            "adventurer_id": adventurer_id,
            "item_id": signature["id"],
        },
        {"_id": 0, "id": 1},
    )
    completed_expeditions = await _completed_expedition_count(
        db,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
    )
    level = int(adventurer.get("level") or 1)

    progress = {
        "signature_item_equipped": bool(signature_equipped),
        "completed_expeditions": completed_expeditions,
        "adventurer_level": level,
    }
    track: list[dict] = []
    for item in items:
        order = int(item.get("acquisition_track_order") or 0)
        if order == 0:
            claimed = adventurer.get("starter_item_reward_status") == "delivered"
            eligible = claimed
            requirement = {
                "milestone": "class_hall_chosen",
                "current": 1 if claimed else 0,
                "target": 1,
            }
        elif order == 1:
            claimed = item["id"] in claimed_item_ids
            eligible = bool(signature_equipped)
            requirement = {
                "milestone": "signature_item_equipped",
                "current": 1 if signature_equipped else 0,
                "target": 1,
            }
        elif order == 2:
            claimed = item["id"] in claimed_item_ids
            eligible = completed_expeditions >= 1
            requirement = {
                "milestone": "first_expedition_completed",
                "current": completed_expeditions,
                "target": 1,
            }
        elif order == 3:
            claimed = item["id"] in claimed_item_ids
            eligible = level >= 2
            requirement = {
                "milestone": "adventurer_level_2",
                "current": level,
                "target": 2,
            }
        else:
            claimed = item["id"] in claimed_item_ids
            eligible = completed_expeditions >= 3
            requirement = {
                "milestone": "three_expeditions_completed",
                "current": completed_expeditions,
                "target": 3,
            }
        status = "claimed" if claimed else ("claimable" if eligible else "locked")
        track.append(
            {
                "order": order,
                "status": status,
                "requirement": requirement,
                "item": item_public(item),
            }
        )

    return {
        "hall": {
            "hall_id": profile.hall_id,
            "hall_name_it": profile.hall_name_it,
            "class_slug": profile.canonical_class_slug,
            "class_name_it": profile.class_name_it,
            "hall_master_witness_npc": profile.hall_master_witness_npc,
        },
        "adventurer": {
            "id": adventurer["id"],
            "name": adventurer.get("name"),
            "level": level,
            "class_slug": adventurer.get("canonical_class_slug"),
        },
        "progress": progress,
        "items": track,
        "claimed_count": sum(row["status"] == "claimed" for row in track),
        "total_count": len(track),
    }


async def _deliver_track_item(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
    item: dict,
    actor_user_id: str | None,
) -> dict:
    grant_id = f"class_hall_track::{adventurer_id}::{item['slug']}"
    claim_token = str(uuid.uuid4())
    now = _now_iso()
    await db.class_hall_item_grants.update_one(
        {"_id": grant_id},
        {
            "$setOnInsert": {
                "_id": grant_id,
                "guild_id": guild_id,
                "adventurer_id": adventurer_id,
                "hall_id": hall_id,
                "item_id": item["id"],
                "item_slug": item["slug"],
                "status": "pending",
                "claim_token": claim_token,
                "created_at": now,
            }
        },
        upsert=True,
    )
    grant = await db.class_hall_item_grants.find_one(
        {"_id": grant_id},
        {"_id": 0},
    )
    idempotent = bool(
        grant
        and (
            grant.get("status") == "delivered"
            or grant.get("claim_token") != claim_token
        )
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
                        "reserved_qty": 0,
                        "class_hall_grant_ids": [grant_id],
                        "source": "class_hall_item_track",
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

    await db.class_hall_item_grants.update_one(
        {"_id": grant_id},
        {"$set": {"status": "delivered", "delivered_at": now}},
    )
    if not idempotent:
        try:
            await write_audit(
                db,
                event_type="class_hall_item_track_claimed",
                actor_user_id=actor_user_id,
                actor_guild_id=guild_id,
                item_slug=item["slug"],
                item_template_id=item["id"],
                quantity=1,
                source="class_halls.item_track",
                related_entity_id=adventurer_id,
                metadata={"hall_id": hall_id, "grant_id": grant_id},
            )
        except Exception:
            pass
    return {
        "status": "delivered",
        "grant_id": grant_id,
        "item_id": item["id"],
        "item_slug": item["slug"],
        "item_name_it": item.get("display_name_it") or item.get("name"),
        "idempotent": idempotent,
    }


async def claim_class_hall_track_item(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    hall_id: str,
    item_slug: str,
    actor_user_id: str | None,
) -> dict:
    if not adventurer_id:
        raise _error(
            400,
            "class_hall.bad_payload",
            "Avventuriero mancante o non valido.",
        )
    track = await get_class_hall_item_track(
        db,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
        hall_id=hall_id,
    )
    entry = next(
        (row for row in track["items"] if row["item"]["slug"] == item_slug),
        None,
    )
    if not entry:
        raise _error(
            404,
            "class_hall.item_track_item_not_found",
            "Questo oggetto non appartiene al Sentiero della Sala.",
        )
    if entry["order"] == 0:
        raise _error(
            409,
            "class_hall.signature_reward_via_assignment",
            "L'item-firma viene consegnato dalla scelta della Sala.",
        )
    if entry["status"] == "locked":
        raise _error(
            423,
            "class_hall.item_track_requirement_not_met",
            "Completa prima la tappa richiesta dal Sentiero degli oggetti.",
            requirement=entry["requirement"],
        )

    item = await db.items.find_one(
        {
            "id": entry["item"]["id"],
            "source": f"class_hall:{hall_id}",
            "is_active": {"$ne": False},
        },
        {"_id": 0},
    )
    reward = await _deliver_track_item(
        db,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
        hall_id=hall_id,
        item=item,
        actor_user_id=actor_user_id,
    )
    fresh_track = await get_class_hall_item_track(
        db,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
        hall_id=hall_id,
    )
    return {"reward": reward, "track": fresh_track}


__all__ = [
    "claim_class_hall_track_item",
    "get_class_hall_item_track",
]
