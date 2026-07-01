"""ROUND 16.0.1 — Seed Alchemist as the 11th base class.

Adds:
  - 1 base class row in `adventurer_classes` (slug=alchemist, is_base_class=true)
  - 3 specializations in `class_specializations`
  - 1 Class Hall row per active guild (~12.861 entries), is_unlocked=false
  - Audit log entries (whitelisted: `alchemist_class_seeded`,
    `alchemist_class_halls_seeded`)

The script is idempotent: rerun produces 0 writes.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Base class definition ──────────────────────────────────────────
ALCHEMIST_BASE_CLASS = {
    "slug": "alchemist",
    "name": "Alchemist",
    "display_name_it": "Alchimista",
    "name_en": "Alchemist",
    "role": "DPS",
    "secondary_role": "Support",
    "primary_stat": "intellect",
    "secondary_stats": ["agility", "endurance"],
    "description": "Pragmatic scholar who turns herbs, minerals and essences into weapons and cures.",
    "description_it": (
        "L'Alchimista trasforma erbe, minerali e essenze in armi e cure. "
        "Lancia bombe, distilla veleni, prepara elisir. Studioso pragmatico, "
        "sfrutta la chimica più che la magia pura."
    ),
    "allowed_weapon_tags": ["dagger", "tome", "alchemical_flask"],
    "allowed_armor_tags": ["light", "robe"],
    # Stat baselines roughly aligned with mage / rogue mixes.
    "base_strength": 3,
    "base_agility": 6,
    "base_intellect": 9,
    "base_endurance": 6,
    "base_faith": 4,
    "is_active": True,
    "is_base_class": True,
    "is_specialization": False,
    "xp_primary_stat_policy": {"enabled": True, "threshold_per_level": 0.5},
    "round_intro": "16.0.1",
}

# ── Specializations ────────────────────────────────────────────────
ALCHEMIST_SPECS = [
    {
        "slug": "bombardier_spec",
        "name_it": "Bombardiere",
        "parent_class_slug": "alchemist",
        "role": "DPS",
        "description_it": (
            "Bombardiere: artigliere alchemico, devastante in aree affollate. "
            "Lancia ordigni esplosivi di precisione contro nemici corazzati e fortificazioni."
        ),
        "counter_tags": ["counter_siege"],
        "is_active": True,
    },
    {
        "slug": "toxicologist_spec",
        "name_it": "Tossicologo",
        "parent_class_slug": "alchemist",
        "role": "DPS",
        "description_it": (
            "Tossicologo: maestro di veleni e antidoti, devastante contro creature vive. "
            "Inietta tossine debilitanti e neutralizza malattie."
        ),
        "counter_tags": ["counter_poison", "counter_disease"],
        "is_active": True,
    },
    {
        "slug": "transmuter_spec",
        "name_it": "Trasmutatore",
        "parent_class_slug": "alchemist",
        "role": "Support",
        "description_it": (
            "Trasmutatore: piega la materia, dissolve maledizioni e barriere arcane. "
            "Trasforma componenti grezzi in materiali rari."
        ),
        "counter_tags": ["counter_curse", "counter_magic_barrier"],
        "is_active": True,
    },
]


async def _audit_emit(db, *, event_type: str, payload: dict, user_id: str | None = None) -> None:
    from app.audit.log import write_audit
    await write_audit(
        db,
        event_type=event_type,
        actor_user_id=user_id,
        source="round160_1_seed",
        metadata=payload,
    )


async def seed_alchemist_class(db, *, dry_run: bool = False) -> dict[str, int]:
    """Insert / refresh the Alchemist base-class row.

    Idempotency: if a doc with slug='alchemist' already exists AND has
    is_base_class=True and is_active=True, leave it untouched.
    """
    existing = await db.adventurer_classes.find_one({"slug": "alchemist"})
    now_iso = utc_now_iso()

    if existing:
        already_ok = (
            existing.get("is_base_class") is True
            and existing.get("is_active") is True
            and existing.get("display_name_it") == "Alchimista"
            and existing.get("round_intro") == "16.0.1"
        )
        if already_ok:
            return {"inserted": 0, "updated": 0}
        if dry_run:
            return {"inserted": 0, "updated": 1}
        await db.adventurer_classes.update_one(
            {"slug": "alchemist"},
            {"$set": {**ALCHEMIST_BASE_CLASS, "updated_at": now_iso,
                       "deprecated_at": None, "is_test": False}},
        )
        await _audit_emit(db, event_type="alchemist_class_seeded",
                          payload={"slug": "alchemist", "action": "updated"})
        return {"inserted": 0, "updated": 1}

    if dry_run:
        return {"inserted": 1, "updated": 0}
    doc = {
        "id": str(uuid.uuid4()),
        **ALCHEMIST_BASE_CLASS,
        "created_at": now_iso,
        "updated_at": now_iso,
        "is_test": False,
    }
    await db.adventurer_classes.insert_one(doc)
    await _audit_emit(db, event_type="alchemist_class_seeded",
                      payload={"slug": "alchemist", "action": "inserted", "id": doc["id"]})
    return {"inserted": 1, "updated": 0}


async def seed_alchemist_specs(db, *, dry_run: bool = False) -> dict[str, int]:
    inserted = 0
    skipped = 0
    now_iso = utc_now_iso()
    for spec in ALCHEMIST_SPECS:
        existing = await db.class_specializations.find_one({"slug": spec["slug"]})
        if existing and existing.get("is_active") and \
                set(existing.get("counter_tags") or []) == set(spec["counter_tags"]):
            skipped += 1
            continue
        if dry_run:
            inserted += 1
            continue
        if existing:
            await db.class_specializations.update_one(
                {"slug": spec["slug"]},
                {"$set": {**spec, "updated_at": now_iso}},
            )
        else:
            doc = {"id": str(uuid.uuid4()), **spec,
                   "created_at": now_iso, "updated_at": now_iso}
            await db.class_specializations.insert_one(doc)
        inserted += 1
    return {"inserted_or_updated": inserted, "skipped": skipped}


async def seed_alchemist_class_halls(db, *, dry_run: bool = False) -> dict[str, int]:
    """Create one Class Hall row per active guild for the alchemist class.

    PK is implicit (guild_id, class_slug). The script enforces uniqueness via
    upsert semantics; rerun → 0 writes.
    """
    inserted = 0
    skipped = 0
    now_iso = utc_now_iso()
    guilds = [g async for g in db.guilds.find({}, {"_id": 0, "id": 1})]
    for g in guilds:
        gid = g["id"]
        existing = await db.class_halls.find_one(
            {"guild_id": gid, "class_slug": "alchemist"}, {"_id": 0})
        if existing:
            skipped += 1
            continue
        if dry_run:
            inserted += 1
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "guild_id": gid,
            "class_slug": "alchemist",
            "is_unlocked": False,
            "is_active": True,
            "level": 0,
            "unlocked_specializations": [],
            "round_intro": "16.0.1",
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        await db.class_halls.insert_one(doc)
        inserted += 1
    if inserted:
        await _audit_emit(db, event_type="alchemist_class_halls_seeded",
                          payload={"inserted": inserted, "skipped": skipped,
                                   "total_guilds": len(guilds)})
    return {"inserted": inserted, "skipped": skipped, "total_guilds": len(guilds)}


async def main(dry_run: bool = False) -> dict[str, Any]:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    try:
        r_class = await seed_alchemist_class(db, dry_run=dry_run)
        r_spec = await seed_alchemist_specs(db, dry_run=dry_run)
        r_halls = await seed_alchemist_class_halls(db, dry_run=dry_run)
        return {"dry_run": dry_run, "class": r_class, "specs": r_spec, "halls": r_halls}
    finally:
        cli.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    out = asyncio.run(main(dry_run=dry))
    print(out)
