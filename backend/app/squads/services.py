"""Squads service (ROUND 6A.2a).

CRUD + validation + audit for `db.squads`. Soft-delete only.
NEVER provides power bonus — squads are a UX convenience layer.
"""
import html
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from app.audit.log import write_audit
from app.expeditions.formulas import adventurer_base_power
from app.squads.schemas import (
    RaidPartiesIn,
    SQUAD_SIZE,
    SquadCreateIn,
    SquadUpdateIn,
    VALID_SQUAD_TYPES,
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def squad_public(doc: dict, adv_index: dict) -> dict:
    """Project a squad doc into the API shape. NEVER expose owner_user_id."""
    # Re-derive total_power live from current adventurer state (no snapshots).
    members = [adv_index.get(aid) for aid in doc.get("adventurer_ids", [])]
    members = [m for m in members if m is not None]
    total_power = 0
    missing = []
    for aid in doc.get("adventurer_ids", []):
        adv = adv_index.get(aid)
        if adv is None:
            missing.append(aid)
        else:
            total_power += adventurer_base_power(adv)

    out = {
        "squad_id": doc["id"],
        "name": doc["name"],
        "squad_type": doc["squad_type"],
        "adventurer_ids": doc.get("adventurer_ids", []),
        "total_power": total_power,
        "member_count": len(members),
        "missing_adventurer_ids": missing,  # warn the UI: someone deleted/dismissed
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "is_archived": doc.get("is_archived", False),
    }
    if doc.get("squad_type") == "raid_20" and doc.get("raid_parties"):
        out["raid_parties"] = doc["raid_parties"]
    return out


def _sanitize_name(name: str) -> str:
    # HTML escape defense-in-depth (Pydantic validator rejects < >; this also
    # neutralizes &, ", ' for safe display).
    return html.escape((name or "").strip(), quote=True)


async def _name_exists_in_guild(
    db, guild_id: str, name: str, *, exclude_squad_id: Optional[str] = None
) -> bool:
    q = {
        "guild_id": guild_id,
        "is_archived": False,
        "name_lower": name.strip().lower(),
    }
    if exclude_squad_id:
        q["id"] = {"$ne": exclude_squad_id}
    return (await db.squads.find_one(q, {"_id": 1})) is not None


async def _load_guild_adventurer_index(db, guild_id: str) -> dict:
    """Return {adv_id: adv_doc} for the guild (excluding dismissed/dead)."""
    advs = await db.adventurers.find(
        {"guild_id": guild_id, "is_available": True}, {"_id": 0}
    ).to_list(2000)
    return {a["id"]: a for a in advs}


def _validate_size_and_uniqueness(squad_type: str, adventurer_ids: list[str]):
    expected = SQUAD_SIZE[squad_type]
    if len(adventurer_ids) != expected:
        raise HTTPException(
            status_code=422,
            detail=f"adventurer_ids.size_invalid (expected {expected}, got {len(adventurer_ids)})",
        )
    if len(set(adventurer_ids)) != len(adventurer_ids):
        raise HTTPException(status_code=422, detail="adventurer_ids.duplicate")


def _validate_raid_parties(parties: RaidPartiesIn, adventurer_ids: list[str]):
    party_lists = [parties.party_1, parties.party_2, parties.party_3, parties.party_4]
    # Each party size already enforced by Pydantic (5 exact). Intra/inter dedupe:
    union: list[str] = []
    for plist in party_lists:
        if len(set(plist)) != 5:
            raise HTTPException(status_code=422, detail="raid_parties.party_size_invalid")
        union.extend(plist)
    if len(set(union)) != 20:
        raise HTTPException(status_code=422, detail="raid_parties.cross_party_duplicate")
    if set(union) != set(adventurer_ids):
        raise HTTPException(status_code=422, detail="raid_parties.union_mismatch")


async def _validate_adventurers_belong_to_guild(
    db, guild_id: str, adventurer_ids: list[str]
):
    cursor = db.adventurers.find(
        {"guild_id": guild_id, "id": {"$in": adventurer_ids}}, {"_id": 0, "id": 1}
    )
    found = {d["id"] async for d in cursor}
    missing = set(adventurer_ids) - found
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"adventurer_ids.not_in_guild ({len(missing)} ids)",
        )


# ─── Public CRUD ──────────────────────────────────────────────────────────────


async def list_squads(db, guild_id: str, *, squad_type: Optional[str] = None) -> list[dict]:
    q = {"guild_id": guild_id, "is_archived": False}
    if squad_type:
        if squad_type not in VALID_SQUAD_TYPES:
            raise HTTPException(status_code=422, detail="squad_type.invalid")
        q["squad_type"] = squad_type
    docs = await db.squads.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    adv_index = await _load_guild_adventurer_index(db, guild_id)
    return [squad_public(d, adv_index) for d in docs]


async def get_squad(db, guild_id: str, squad_id: str) -> dict:
    doc = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="squad.not_found")
    if doc.get("is_archived"):
        raise HTTPException(status_code=404, detail="squad.archived")
    if doc.get("guild_id") != guild_id:
        # Hide existence to non-owners (no info leak).
        raise HTTPException(status_code=404, detail="squad.not_found")
    adv_index = await _load_guild_adventurer_index(db, guild_id)
    return squad_public(doc, adv_index)


async def create_squad(
    db, *, owner_user_id: str, guild_id: str, payload: SquadCreateIn
) -> dict:
    name_clean = _sanitize_name(payload.name)
    _validate_size_and_uniqueness(payload.squad_type, payload.adventurer_ids)
    if payload.squad_type == "raid_20":
        if payload.raid_parties is None:
            raise HTTPException(status_code=422, detail="raid_parties.required")
        _validate_raid_parties(payload.raid_parties, payload.adventurer_ids)
    elif payload.raid_parties is not None:
        raise HTTPException(status_code=422, detail="raid_parties.not_allowed_for_type")

    await _validate_adventurers_belong_to_guild(db, guild_id, payload.adventurer_ids)

    if await _name_exists_in_guild(db, guild_id, name_clean):
        raise HTTPException(status_code=409, detail="squad.name_taken")

    now = _now()
    doc = {
        "id": str(uuid.uuid4()),
        "owner_user_id": owner_user_id,
        "guild_id": guild_id,
        "name": name_clean,
        "name_lower": name_clean.lower(),
        "squad_type": payload.squad_type,
        "adventurer_ids": list(payload.adventurer_ids),
        "raid_parties": (
            payload.raid_parties.model_dump() if payload.raid_parties else None
        ),
        "is_archived": False,
        "created_at": now,
        "updated_at": now,
    }
    await db.squads.insert_one(doc)
    await write_audit(
        db,
        event_type="squad_created",
        actor_user_id=owner_user_id,
        actor_guild_id=guild_id,
        related_entity_id=doc["id"],
        metadata={
            "entity_type": "squad",
            "squad_type": doc["squad_type"],
            "member_count": len(doc["adventurer_ids"]),
        },
        source="api:/api/squads",
    )
    adv_index = await _load_guild_adventurer_index(db, guild_id)
    return squad_public(doc, adv_index)


async def update_squad(
    db,
    *,
    owner_user_id: str,
    guild_id: str,
    squad_id: str,
    payload: SquadUpdateIn,
) -> dict:
    existing = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    if not existing or existing.get("is_archived"):
        raise HTTPException(status_code=404, detail="squad.not_found")
    if existing.get("guild_id") != guild_id:
        raise HTTPException(status_code=404, detail="squad.not_found")

    updates: dict = {"updated_at": _now()}

    new_name = existing["name"]
    if payload.name is not None:
        new_name = _sanitize_name(payload.name)
        if await _name_exists_in_guild(
            db, guild_id, new_name, exclude_squad_id=squad_id
        ):
            raise HTTPException(status_code=409, detail="squad.name_taken")
        updates["name"] = new_name
        updates["name_lower"] = new_name.lower()

    new_ids = existing["adventurer_ids"]
    if payload.adventurer_ids is not None:
        _validate_size_and_uniqueness(existing["squad_type"], payload.adventurer_ids)
        await _validate_adventurers_belong_to_guild(db, guild_id, payload.adventurer_ids)
        updates["adventurer_ids"] = list(payload.adventurer_ids)
        new_ids = updates["adventurer_ids"]

    if existing["squad_type"] == "raid_20":
        if payload.raid_parties is not None:
            _validate_raid_parties(payload.raid_parties, new_ids)
            updates["raid_parties"] = payload.raid_parties.model_dump()
        elif payload.adventurer_ids is not None:
            # If member list changed without resupplying parties → invalid.
            raise HTTPException(status_code=422, detail="raid_parties.required_after_member_change")
    elif payload.raid_parties is not None:
        raise HTTPException(status_code=422, detail="raid_parties.not_allowed_for_type")

    await db.squads.update_one({"id": squad_id}, {"$set": updates})
    await write_audit(
        db,
        event_type="squad_updated",
        actor_user_id=owner_user_id,
        actor_guild_id=guild_id,
        related_entity_id=squad_id,
        metadata={
            "entity_type": "squad",
            "squad_type": existing["squad_type"],
            "fields": sorted(k for k in updates if k != "updated_at"),
        },
        source="api:/api/squads",
    )
    updated_doc = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    adv_index = await _load_guild_adventurer_index(db, guild_id)
    return squad_public(updated_doc, adv_index)


async def archive_squad(
    db, *, owner_user_id: str, guild_id: str, squad_id: str
) -> dict:
    existing = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    if not existing or existing.get("is_archived"):
        raise HTTPException(status_code=404, detail="squad.not_found")
    if existing.get("guild_id") != guild_id:
        raise HTTPException(status_code=404, detail="squad.not_found")
    await db.squads.update_one(
        {"id": squad_id},
        {"$set": {"is_archived": True, "updated_at": _now()}},
    )
    await write_audit(
        db,
        event_type="squad_archived",
        actor_user_id=owner_user_id,
        actor_guild_id=guild_id,
        related_entity_id=squad_id,
        metadata={"entity_type": "squad", "squad_type": existing["squad_type"]},
        source="api:/api/squads",
    )
    return {"squad_id": squad_id, "is_archived": True}


__all__ = [
    "list_squads",
    "get_squad",
    "create_squad",
    "update_squad",
    "archive_squad",
    "squad_public",
]
