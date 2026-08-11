"""FASE 9C — Class Halls service layer (senza specializzazioni).

Le Sale di Classe sono contenitori per-gilda che tracciano quali delle
27 classi canoniche sono "sbloccate" (la gilda ha almeno un avventuriero
di quella classe). Le specializzazioni sbloccabili NON esistono più:
la classe dà un ruolo fisso (registry `app.classes`).

Storage:
    Collection `class_halls`, PK `{guild_id}::{class_slug}` (string `_id`).
    Le righe legacy delle 11 classi inglesi pre-Round 16 (warrior, …)
    vengono rimosse dalla migration 9M; il seed qui sotto crea solo le
    27 canoniche.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.audit.log import write_audit
from app.classes import CLASS_REGISTRY, registry_entry


# FASE 9B — le Sale sono le 27 classi canoniche del registry.
BASE_CLASS_SLUGS: tuple[str, ...] = tuple(CLASS_REGISTRY.keys())


def _hall_id(guild_id: str, class_slug: str) -> str:
    return f"{guild_id}::{class_slug}"


def _strip_internal(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out


async def seed_class_halls_for_guild(
    db, *, guild_id: str, actor_user_id: Optional[str] = None,
) -> dict[str, int]:
    """Idempotent seed of one row per canonical class for a guild."""
    now = datetime.now(timezone.utc)
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
            "training_territory_id": training_id,
            "created_at": now,
            "updated_at": now,
        }
        await db.class_halls.insert_one(doc)
        await write_audit(
            db, event_type="class_hall_seeded_round160",
            actor_user_id=actor_user_id, actor_guild_id=guild_id,
            source="fase9.class_halls",
            metadata={"class_slug": slug, "is_unlocked": has_advs},
        )
        inserted += 1
    return {"inserted": inserted, "skipped": skipped}


async def list_class_halls(db, *, guild_id: str) -> list[dict[str, Any]]:
    # FASE 9C — le righe legacy (slug inglesi pre-R16) non vengono più
    # esposte: solo le 27 Sale canoniche.
    cursor = db.class_halls.find({
        "guild_id": guild_id,
        "class_slug": {"$in": list(BASE_CLASS_SLUGS)},
    })
    out: list[dict[str, Any]] = []
    async for d in cursor:
        out.append(_strip_internal(d))
    out.sort(key=lambda x: x.get("class_slug") or "")
    return out


async def enrich_halls_for_ui(db, *, guild_id: str,
                                halls: list[dict]) -> list[dict]:
    """Augment hall dicts with FE-facing context.

    FASE 9C — niente più specializzazioni: la Sala espone identità di
    classe (registry), ruolo FISSO, conteggi e top-3 avventurieri.
    """
    if not halls:
        return halls
    pipe = [
        {"$match": {"guild_id": guild_id, "is_retired": {"$ne": True}}},
        {"$group": {"_id": "$class_slug", "count": {"$sum": 1}}},
    ]
    rows = {r["_id"]: r async for r in db.adventurers.aggregate(pipe)}

    async def _top3(class_slug: str) -> list[dict]:
        cur = db.adventurers.find(
            {"guild_id": guild_id, "class_slug": class_slug,
             "is_retired": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1, "level": 1,
             "base_power": 1, "equipment_power": 1},
        ).sort([("level", -1), ("base_power", -1)]).limit(3)
        items: list[dict] = []
        async for a in cur:
            items.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "level": int(a.get("level") or 1),
                "total_power": int((a.get("base_power") or 0)
                                    + (a.get("equipment_power") or 0)),
            })
        return items

    enriched: list[dict] = []
    for h in halls:
        cs = h.get("class_slug")
        row = rows.get(cs) or {"count": 0}
        entry = registry_entry(cs or "")
        enriched.append({
            **h,
            "adventurers_of_class": int(row["count"]),
            "top_adventurers": await _top3(cs),
            # FASE 9B — identità canonica dal registry.
            "class_role": entry.class_role if entry else None,
            "class_name_it": entry.class_name if entry else cs,
            "class_identity_it": entry.class_identity if entry else None,
            "class_mechanics_it": entry.class_mechanics if entry else None,
            "class_strengths_it": list(entry.strengths) if entry else [],
            "class_emblem": entry.emblem if entry else None,
            "primary_stat": entry.primary_stat if entry else None,
            "armor_tags": list(entry.armor_tags) if entry else [],
            "weapon_tags": list(entry.weapon_tags) if entry else [],
            "unlock_hint_it": (
                None if h.get("is_unlocked") else
                "Assegna almeno un avventuriero a questa classe per "
                "sbloccare la Sala."
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


__all__ = [
    "BASE_CLASS_SLUGS",
    "seed_class_halls_for_guild",
    "list_class_halls",
    "enrich_halls_for_ui",
    "get_class_hall",
]
