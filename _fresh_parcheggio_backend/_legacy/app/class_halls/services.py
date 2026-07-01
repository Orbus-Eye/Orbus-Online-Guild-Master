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
    "paladin", "druid", "monk", "bard", "warlock", "alchemist",
)


# ROUND 16.1 Phase 3 — Specializations per class (mirrors FE constant).
# Used to project specialization slugs into the API response so the
# FE no longer needs to hard-code per-class spec lists.
SPECS_BY_CLASS: dict[str, tuple[str, ...]] = {
    "warrior": ("berserker_spec", "guardian_spec", "weapon_master_spec"),
    "rogue": ("assassin_spec", "duelist_spec", "shadow_spec"),
    "mage": ("necromancer_spec", "elementalist_spec", "arcanist_spec"),
    "priest": ("healer_spec", "exorcist_spec", "oracle_spec"),
    "ranger": ("marksman_spec", "monster_hunter_spec", "scout_spec"),
    "paladin": ("oath_defender_spec", "rune_knight_spec", "vindicator_spec"),
    "druid": ("leafwarden_spec", "shapeshifter_spec", "shaman_spec"),
    "monk": ("inner_fist_spec", "spirit_guardian_spec", "ascetic_spec"),
    "bard": ("warsinger_spec", "herald_spec", "inspiration_weaver_spec"),
    "warlock": ("demon_pact_spec", "void_pact_spec", "stellar_pact_spec"),
    "alchemist": ("bombardier_spec", "toxicologist_spec", "transmuter_spec"),
}


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


async def enrich_halls_for_ui(db, *, guild_id: str,
                                halls: list[dict]) -> list[dict]:
    """ROUND 16.1 Phase 3 — augment hall dicts with FE-facing context:

    - `adventurers_of_class`: int — guild members of that class.
    - `top_adventurers`: list of up to 3 dicts (id, name, level, total_power).
    - `available_to_specialize`: int — class members without a spec.
    - `specializations`: list of dicts (slug, name_it/en, role, unlocked).
    - `bonuses`: empty list (placeholder — bonuses arrive in Round 16.A).
    """
    if not halls:
        return halls
    # Adventurers per class (single query).
    pipe = [
        {"$match": {"guild_id": guild_id, "is_retired": {"$ne": True}}},
        {"$group": {
            "_id": "$class_slug",
            "count": {"$sum": 1},
            "no_spec_count": {"$sum": {"$cond": [
                {"$or": [{"$eq": [{"$ifNull": ["$specialization_slug", None]}, None]},
                          {"$eq": ["$specialization_slug", ""]}]}, 1, 0]}},
        }},
    ]
    rows = {r["_id"]: r async for r in db.adventurers.aggregate(pipe)}

    # Top-3 per class (small dataset; iterate per hall — cheaper than $unionWith).
    async def _top3(class_slug: str) -> list[dict]:
        cur = db.adventurers.find(
            {"guild_id": guild_id, "class_slug": class_slug,
             "is_retired": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1, "level": 1,
             "base_power": 1, "equipment_power": 1,
             "specialization_slug": 1},
        ).sort([("level", -1), ("base_power", -1)]).limit(3)
        items: list[dict] = []
        async for a in cur:
            items.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "level": int(a.get("level") or 1),
                "total_power": int((a.get("base_power") or 0)
                                    + (a.get("equipment_power") or 0)),
                "specialization_slug": a.get("specialization_slug"),
            })
        return items

    # Spec catalog (one query for all specs in halls' classes).
    all_slugs: list[str] = []
    for s in SPECS_BY_CLASS.values():
        all_slugs.extend(s)
    spec_docs = {d["slug"]: d async for d in db.class_specializations.find(
        {"slug": {"$in": all_slugs}, "is_active": {"$ne": False}},
        {"_id": 0, "slug": 1, "class_slug": 1, "role": 1,
         "display_name_it": 1, "display_name_en": 1,
         "is_unlockable": 1, "requires_class_hall_level": 1},
    )}

    enriched: list[dict] = []
    for h in halls:
        cs = h.get("class_slug")
        row = rows.get(cs) or {"count": 0, "no_spec_count": 0}
        unlocked_specs = set(h.get("unlocked_specializations") or [])
        specs_payload = []
        for spec_slug in SPECS_BY_CLASS.get(cs, ()):
            sd = spec_docs.get(spec_slug) or {}
            specs_payload.append({
                "slug": spec_slug,
                "name_it": sd.get("display_name_it") or spec_slug,
                "name_en": sd.get("display_name_en") or spec_slug,
                "role": sd.get("role"),
                "is_unlocked": spec_slug in unlocked_specs,
                "is_unlockable": bool(sd.get("is_unlockable", True))
                                    and bool(h.get("is_unlocked")),
                "requires_class_hall_level":
                    int(sd.get("requires_class_hall_level") or 1),
            })
        enriched.append({
            **h,
            "adventurers_of_class": int(row["count"]),
            "available_to_specialize": int(row["no_spec_count"]),
            "top_adventurers": await _top3(cs),
            "specializations": specs_payload,
            # Bonuses: arrive in Round 16.A — keep shape for forward compat.
            "bonuses": [],
            "unlock_hint_it": (
                None if h.get("is_unlocked") else
                "Recluta almeno un avventuriero di questa classe per sbloccare la Sala."
            ),
            "unlock_hint_en": (
                None if h.get("is_unlocked") else
                "Recruit at least one adventurer of this class to unlock the Hall."
            ),
        })
    return enriched


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
    "SPECS_BY_CLASS",
    "seed_class_halls_for_guild",
    "list_class_halls",
    "enrich_halls_for_ui",
    "get_class_hall",
    "unlock_specialization",
]
