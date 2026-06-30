"""ROUND 16.0 — Class Halls service layer.

Class Halls are per-guild containers tracking which of the 10 base
classes are "unlocked" inside the guild (the guild has at least one
adventurer of that class) and which specializations have been unlocked
for each hall. They live under the Training Territory as logical
children — `training_territory_id` references the parent structure.

Storage:
    Collection `class_halls`, PK `{guild_id}::{class_slug}` (string `_id`).

Mutations:
    * `seed_class_halls_for_guild(db, guild_id, *, actor_user_id)`:
      idempotent; ensures one row per base class. Unlocked if the guild
      already owns ≥1 adventurer of that class.
    * `unlock_specialization(db, guild_id, class_slug, spec_slug,
      actor_user_id)`: appends a spec to `unlocked_specializations` and
      writes an audit event. No-op if the spec is already unlocked.

Reads:
    * `list_class_halls(db, guild_id)` returns rows projected without
      the Mongo `_id` (UI-safe).
    * `get_class_hall(db, guild_id, class_slug)` single row.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException

from app.audit.log import write_audit


BASE_CLASS_SLUGS: tuple[str, ...] = (
    "warrior", "rogue", "mage", "priest", "ranger",
    "paladin", "druid", "monk", "bard", "warlock",
)


def _hall_id(guild_id: str, class_slug: str) -> str:
    return f"{guild_id}::{class_slug}"


def _strip_internal(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out


async def seed_class_halls_for_guild(
    db, *, guild_id: str, actor_user_id: Optional[str] = None,
) -> dict[str, int]:
    """Idempotent seed of one row per base class for a guild."""
    now = datetime.now(timezone.utc)
    # Snapshot of class_slug usage for this guild (case-insensitive on
    # class_name → match base class names capitalized too).
    pipe = [
        {"$match": {"guild_id": guild_id}},
        {"$group": {"_id": "$class_slug", "c": {"$sum": 1}}},
    ]
    rows = await db.adventurers.aggregate(pipe).to_list(50)
    counts = {(r["_id"] or "").lower(): r["c"] for r in rows if r["_id"]}

    # Locate the parent training_grounds structure id (if available).
    training_struct = await db.guild_structures.find_one(
        {"guild_id": guild_id},
        {"_id": 0, "structures": 1, "id": 1},
    )
    training_id: Optional[str] = None
    if training_struct:
        # `guild_structures` doc holds a sub-doc keyed by slug
        struct_map = training_struct.get("structures") or {}
        tg = struct_map.get("training_grounds")
        if isinstance(tg, dict):
            training_id = tg.get("id") or training_struct.get("id")

    inserted = 0
    skipped = 0
    for slug in BASE_CLASS_SLUGS:
        existing = await db.class_halls.find_one({"_id": _hall_id(guild_id, slug)})
        if existing:
            skipped += 1
            continue
        has_advs = counts.get(slug, 0) > 0
        doc = {
            "_id": _hall_id(guild_id, slug),
            "guild_id": guild_id,
            "class_slug": slug,
            "is_unlocked": has_advs,
            "unlocked_at": now if has_advs else None,
            "level": 1,
            "unlocked_specializations": [],
            "training_territory_id": training_id,
            "created_at": now,
            "updated_at": now,
        }
        await db.class_halls.insert_one(doc)
        await write_audit(
            db, event_type="class_hall_seeded_round160",
            actor_user_id=actor_user_id, actor_guild_id=guild_id,
            source="round160.class_halls",
            metadata={"class_slug": slug, "is_unlocked": has_advs},
        )
        inserted += 1
    return {"inserted": inserted, "skipped": skipped}


async def list_class_halls(db, *, guild_id: str) -> list[dict[str, Any]]:
    cursor = db.class_halls.find({"guild_id": guild_id})
    out: list[dict[str, Any]] = []
    async for d in cursor:
        out.append(_strip_internal(d))
    out.sort(key=lambda x: x.get("class_slug") or "")
    return out


async def get_class_hall(
    db, *, guild_id: str, class_slug: str,
) -> Optional[dict[str, Any]]:
    doc = await db.class_halls.find_one({"_id": _hall_id(guild_id, class_slug)})
    if not doc:
        return None
    return _strip_internal(doc)


async def unlock_specialization(
    db, *, guild_id: str, class_slug: str, specialization_slug: str,
    actor_user_id: Optional[str] = None,
) -> dict[str, Any]:
    if class_slug not in BASE_CLASS_SLUGS:
        raise HTTPException(404, {
            "code": "class_hall.unknown_class",
            "user_message": f"Classe '{class_slug}' non riconosciuta.",
        })
    spec = await db.class_specializations.find_one(
        {"slug": specialization_slug, "class_slug": class_slug},
        {"_id": 0, "slug": 1, "class_slug": 1, "display_name_it": 1,
         "is_active": 1, "is_unlockable": 1, "requires_class_hall_level": 1},
    )
    if not spec or not spec.get("is_active"):
        raise HTTPException(404, {
            "code": "class_hall.unknown_specialization",
            "user_message": "Specializzazione non disponibile.",
        })
    if not spec.get("is_unlockable", True):
        raise HTTPException(403, {
            "code": "class_hall.specialization_not_unlockable",
            "user_message": "Specializzazione non sbloccabile.",
        })
    hall = await db.class_halls.find_one({"_id": _hall_id(guild_id, class_slug)})
    if not hall:
        # Lazy-create the hall if missing (e.g. new class added after seed).
        await seed_class_halls_for_guild(db, guild_id=guild_id,
                                         actor_user_id=actor_user_id)
        hall = await db.class_halls.find_one(
            {"_id": _hall_id(guild_id, class_slug)})
    if not hall.get("is_unlocked"):
        raise HTTPException(423, {
            "code": "class_hall.locked",
            "user_message": (
                "Class Hall bloccata. Recluta almeno un avventuriero di questa "
                "classe per sbloccarla."
            ),
        })
    required_level = int(spec.get("requires_class_hall_level") or 1)
    if int(hall.get("level") or 1) < required_level:
        raise HTTPException(423, {
            "code": "class_hall.insufficient_level",
            "user_message": (
                f"Class Hall livello {hall.get('level')} insufficiente. "
                f"Richiesto Lv {required_level}."
            ),
        })
    if specialization_slug in (hall.get("unlocked_specializations") or []):
        # Idempotent: no audit row written.
        return _strip_internal(hall)
    now = datetime.now(timezone.utc)
    await db.class_halls.update_one(
        {"_id": _hall_id(guild_id, class_slug)},
        {"$addToSet": {"unlocked_specializations": specialization_slug},
         "$set": {"updated_at": now}},
    )
    await write_audit(
        db, event_type="class_specialization_unlocked",
        actor_user_id=actor_user_id, actor_guild_id=guild_id,
        source="class_halls.unlock_specialization",
        metadata={"class_slug": class_slug,
                  "specialization_slug": specialization_slug},
    )
    return await get_class_hall(db, guild_id=guild_id, class_slug=class_slug)


__all__ = [
    "BASE_CLASS_SLUGS",
    "seed_class_halls_for_guild",
    "list_class_halls",
    "get_class_hall",
    "unlock_specialization",
]
