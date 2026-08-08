"""Phase 17.5 / Round 18.6 — starter roster auto-population.

Decision §I.1 (ROUND 5): every guild must own at least 5 adventurers so that
team-size-5 expeditions and the 20-adventurer raid roster gate are reachable.

`ensure_starter_roster(db, guild_id)` is idempotent:
  • If `count(adventurers where guild_id=X) >= 5` → no-op.
  • Otherwise generate `5 - existing` Common, classless adventurers and persist
    them with `is_starter=True`.

Every new adventurer starts without a class.  Starter stats are neutral, so the
initial roll never biases the first Class Hall choice; activities remain gated
until the player completes that choice.

R18.Reset.1b.hotfix.write_freeze_full (gate 7): `ensure_starter_roster_for_all_guilds`
(L1) e' decorata con `@frozen_when_active` per rispettare
`ORBUS_INTERNAL_JOB_FREEZE` durante la finestra di apply. Zero cambi di
logica al job; solo un guard all'ingresso.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.adventurers.common import build_base_adventurer
from app.audit.log import write_audit
from app.core.job_freeze import frozen_when_active


logger = logging.getLogger("orbus.onboarding")

STARTER_TARGET = 5  # locked by §I.1
STARTER_NAMES = (
    "Prima Recluta",
    "Seconda Recluta",
    "Terza Recluta",
    "Quarta Recluta",
    "Quinta Recluta",
)
STARTER_IDENTITIES = (
    ("human", "female"),
    ("dwarf_mountain", "male"),
    ("high_elf", "female"),
    ("half_orc", "male"),
    ("halfling_lightfoot", "female"),
)


def _build_starter_adventurer(guild_id: str, starter_index: int) -> dict:
    """Build one deterministic Common founder with no rolled properties."""
    now = datetime.now(timezone.utc)
    race_slug, gender = STARTER_IDENTITIES[starter_index]
    return build_base_adventurer(
        guild_id,
        name=STARTER_NAMES[starter_index],
        now=now,
        race_slug=race_slug,
        gender=gender,
        is_starter=True,
    )


async def ensure_starter_roster(db, guild_id: str, *, user_id: str | None = None) -> int:
    """Top up the guild's roster up to STARTER_TARGET if below.

    Returns the number of adventurers actually inserted (0 if no-op).
    """
    # Reconcile founders created by the older classless seed, which did not
    # persist race/gender yet.
    for starter_index, starter_name in enumerate(STARTER_NAMES):
        race_slug, gender = STARTER_IDENTITIES[starter_index]
        await db.adventurers.update_one(
            {
                "guild_id": guild_id,
                "name": starter_name,
                "is_starter": True,
                "$or": [
                    {"race_slug": {"$exists": False}},
                    {"race_slug": None},
                ],
            },
            {"$set": {"race_slug": race_slug}},
        )
        await db.adventurers.update_one(
            {
                "guild_id": guild_id,
                "name": starter_name,
                "is_starter": True,
                "$or": [
                    {"gender": {"$exists": False}},
                    {"gender": None},
                ],
            },
            {"$set": {"gender": gender}},
        )
    existing = await db.adventurers.count_documents({"guild_id": guild_id})
    needed = max(0, STARTER_TARGET - existing)
    if needed == 0:
        return 0

    inserted = 0
    for starter_index in range(existing, STARTER_TARGET):
        doc = _build_starter_adventurer(guild_id, starter_index)
        await db.adventurers.insert_one(doc)
        inserted += 1
        # Audit (best-effort)
        try:
            await write_audit(
                db,
                event_type="starter_roster_seeded",
                actor_user_id=user_id,
                actor_guild_id=guild_id,
                source="onboarding.ensure_starter_roster",
                related_entity_id=doc["id"],
                metadata={
                    "class_state": "unassigned",
                    "class_selection_required": True,
                    "rarity": doc["rarity"],
                    "is_starter": True,
                },
            )
        except Exception:  # noqa: BLE001
            pass

    logger.info("starter roster seeded: guild=%s inserted=%d", guild_id, inserted)
    return inserted


@frozen_when_active(
    "orbus.onboarding.starter_roster_for_all_guilds",
    freeze_return_value={
        "guilds_checked": 0,
        "guilds_topped_up": 0,
        "advs_inserted": 0,
        "skipped_due_to_freeze": True,
    },
)
async def ensure_starter_roster_for_all_guilds(db) -> dict:
    """Backfill helper for lifespan boot. Walks every guild and tops up roster."""
    summary = {"guilds_checked": 0, "guilds_topped_up": 0, "advs_inserted": 0}
    cursor = db.guilds.find({}, {"_id": 0, "id": 1, "owner_user_id": 1})
    async for g in cursor:
        summary["guilds_checked"] += 1
        n = await ensure_starter_roster(db, g["id"], user_id=g.get("owner_user_id"))
        if n > 0:
            summary["guilds_topped_up"] += 1
            summary["advs_inserted"] += n
    if summary["advs_inserted"]:
        logger.info(
            "starter roster backfill: checked=%d topped=%d advs=%d",
            summary["guilds_checked"],
            summary["guilds_topped_up"],
            summary["advs_inserted"],
        )
    return summary


__all__ = [
    "ensure_starter_roster",
    "ensure_starter_roster_for_all_guilds",
    "STARTER_NAMES",
    "STARTER_IDENTITIES",
    "STARTER_TARGET",
]
