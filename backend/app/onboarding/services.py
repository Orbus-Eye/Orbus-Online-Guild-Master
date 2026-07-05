"""Phase 17.5 — Starter roster auto-population.

Decision §I.1 (ROUND 5): every guild must own at least 5 adventurers so that
team-size-5 expeditions and the 20-adventurer raid roster gate are reachable.

`ensure_starter_roster(db, guild_id)` is idempotent:
  • If `count(adventurers where guild_id=X) >= 5` → no-op.
  • Otherwise generate `5 - existing` Common adventurers (uniform random class)
    and persist them with `is_starter=True`.

Generation re-uses the canonical recruitment helpers so the starter advs have
exactly the same stat/trait distribution as Common candidates — no power
inflation, no rarity boost, no PvP advantage.

R18.Reset.1b.hotfix.write_freeze_full (gate 7): `ensure_starter_roster_for_all_guilds`
(L1) e' decorata con `@frozen_when_active` per rispettare
`ORBUS_INTERNAL_JOB_FREEZE` durante la finestra di apply. Zero cambi di
logica al job; solo un guard all'ingresso.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from app.recruitment.services import (
    _generate_name,
    _pick_random_traits,
    _roll_stat,
)
from app.shared.constants import RARITY_BONUS
from app.audit.log import write_audit
from app.core.job_freeze import frozen_when_active


logger = logging.getLogger("orbus.onboarding")

STARTER_TARGET = 5  # locked by §I.1


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_starter_adventurer(klass: dict, guild_id: str, traits_pool: List[dict]) -> dict:
    """Build a Common-rarity adventurer doc. Stats/traits use the same
    formulas as recruitment so starters are not advantaged."""
    rarity = "Common"
    bonus = RARITY_BONUS[rarity]
    now = _utc_now_iso()
    return {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": _generate_name(),
        "adventurer_class_id": klass["id"],
        "class_name": klass["name"],
        "class_role": klass["role"],
        "rarity": rarity,
        "level": 1,
        "experience": 0,
        "strength": _roll_stat(klass["base_strength"], bonus),
        "agility": _roll_stat(klass["base_agility"], bonus),
        "intellect": _roll_stat(klass["base_intellect"], bonus),
        "endurance": _roll_stat(klass["base_endurance"], bonus),
        "faith": _roll_stat(klass["base_faith"], bonus),
        "stamina": 100,
        "morale": 100,
        "traits": _pick_random_traits(traits_pool),
        "is_available": True,
        "is_starter": True,
        "created_at": now,
        "updated_at": now,
    }


async def ensure_starter_roster(db, guild_id: str, *, user_id: str | None = None) -> int:
    """Top up the guild's roster up to STARTER_TARGET if below.

    Returns the number of adventurers actually inserted (0 if no-op).
    """
    existing = await db.adventurers.count_documents({"guild_id": guild_id})
    needed = max(0, STARTER_TARGET - existing)
    if needed == 0:
        return 0

    classes = await db.adventurer_classes.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)
    if not classes:
        logger.warning("ensure_starter_roster: no classes seeded yet, skip")
        return 0
    traits_pool = await db.adventurer_traits.find(
        {"is_active": True, "is_test": {"$ne": True}}, {"_id": 0}
    ).to_list(200)

    # Round-robin classes so the starter party is role-diverse
    import random
    inserted = 0
    pool = list(classes)
    random.shuffle(pool)
    for i in range(needed):
        klass = pool[i % len(pool)]
        doc = _build_starter_adventurer(klass, guild_id, traits_pool)
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
                    "class_role": doc["class_role"],
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


__all__ = ["ensure_starter_roster", "ensure_starter_roster_for_all_guilds", "STARTER_TARGET"]
