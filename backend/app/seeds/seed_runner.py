"""Seed runner (Phase 5.5g).

Three idempotent seeds + orchestrator. The tester seed is gated by APP_ENV
so it never writes to a production DB. Content seeds (classes/traits,
dungeons/items) run in all environments to keep the catalog in sync.
"""
import os
import logging
import uuid
from datetime import datetime, timezone

from app.admin.services import validate_item_monetization
from app.core.security import hash_password
from app.seeds.seed_data import (
    CLASS_SEED,
    TRAIT_SEED,
    DUNGEON_SEED,
    ITEM_SEED,
)
from app.shared.constants import (
    TESTER_EMAIL,
    TESTER_USERNAME,
    TESTER_PASSWORD,
)


logger = logging.getLogger("orbus")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def seed_classes_and_traits(db) -> None:
    """Idempotent content seed (runs in all envs, including production)."""
    now = _utc_now_iso()
    for c in CLASS_SEED:
        await db.adventurer_classes.update_one(
            {"slug": c["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "name": c["name"],
                    "slug": c["slug"],
                    "role": c["role"],
                    "description": c["description"],
                    "base_strength": c["base_strength"],
                    "base_agility": c["base_agility"],
                    "base_intellect": c["base_intellect"],
                    "base_endurance": c["base_endurance"],
                    "base_faith": c["base_faith"],
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )

    for t in TRAIT_SEED:
        await db.adventurer_traits.update_one(
            {"name": t["name"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "name": t["name"],
                    "description": t["description"],
                    "modifier_type": t["modifier_type"],
                    "affected_stat": t["affected_stat"],
                    "modifier_value": t["modifier_value"],
                    "is_positive": t["is_positive"],
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d classes and %d traits", len(CLASS_SEED), len(TRAIT_SEED))


async def seed_dungeons_and_items(db) -> None:
    """Idempotent Phase-3 content seed."""
    now = _utc_now_iso()
    for d in DUNGEON_SEED:
        await db.dungeons.update_one(
            {"slug": d["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "slug": d["slug"],
                    "name": d["name"],
                    "description": d["description"],
                    "difficulty": d["difficulty"],
                    "required_team_size": d["required_team_size"],
                    "base_duration_seconds": d["base_duration_seconds"],
                    "recommended_power": d["recommended_power"],
                    "base_gold_reward": d["base_gold_reward"],
                    "base_xp_reward": d["base_xp_reward"],
                    # Phase 11.2: data-driven gate dict (optional)
                    "gate": d.get("gate") or {},
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )

    for it in ITEM_SEED:
        full = {
            "level_required": 1,
            "is_tradeable": True,
            "is_cosmetic": False,
            "affects_economy": False,
            "affects_ranking": False,
            "can_be_sold_for_gold": True,
            "can_be_sold_for_real_money": False,
            **it,
        }
        validate_item_monetization(full)
        await db.items.update_one(
            {"slug": full["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "slug": full["slug"],
                    "name": full["name"],
                    "description": full["description"],
                    "item_type": full["item_type"],
                    "rarity": full["rarity"],
                    "level_required": full["level_required"],
                    "power_score": full["power_score"],
                    "strength_bonus": full["strength_bonus"],
                    "agility_bonus": full["agility_bonus"],
                    "intellect_bonus": full["intellect_bonus"],
                    "endurance_bonus": full["endurance_bonus"],
                    "faith_bonus": full["faith_bonus"],
                    "is_tradeable": full["is_tradeable"],
                    "is_cosmetic": full["is_cosmetic"],
                    "affects_combat": full["affects_combat"],
                    "affects_economy": full["affects_economy"],
                    "affects_ranking": full["affects_ranking"],
                    "can_be_sold_for_gold": full["can_be_sold_for_gold"],
                    "can_be_sold_for_real_money": full["can_be_sold_for_real_money"],
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d dungeons and %d items", len(DUNGEON_SEED), len(ITEM_SEED))


async def seed_tester(db) -> None:
    """Idempotent dev/preview tester account. Gated by APP_ENV (never runs in prod)."""
    app_env = os.environ.get("APP_ENV", "development")
    if app_env == "production":
        logger.info("APP_ENV=production → skipping tester seed")
        return
    # Phase 5.6b: hard-fail in non-prod if the tester password is somehow blank.
    if not TESTER_PASSWORD:
        raise RuntimeError(
            "TESTER_PASSWORD is empty; set it in the environment or restore the "
            "default in app/shared/constants.py before running in non-prod."
        )
    now = _utc_now_iso()
    existing = await db.users.find_one({"email": TESTER_EMAIL})
    if existing:
        if not existing.get("is_admin"):
            await db.users.update_one(
                {"email": TESTER_EMAIL},
                {"$set": {"is_admin": True, "updated_at": now}},
            )
            logger.info("Promoted existing tester to is_admin=True")
        else:
            logger.info("Tester account already exists with is_admin=True")
        return
    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": TESTER_EMAIL,
            "username": TESTER_USERNAME,
            "password_hash": hash_password(TESTER_PASSWORD),
            "is_admin": True,
            "created_at": now,
            "updated_at": now,
        }
    )
    logger.info("Seeded tester account: %s (is_admin=True)", TESTER_EMAIL)


async def unbake_legacy_traits(db) -> None:
    """Phase 13: one-time migration that strips flat trait baking from
    legacy adventurers and persists a `phase13_unbaked` marker.

    Pre-Phase 13, recruitment baked flat trait modifiers directly into
    the adventurer's stat fields. From Phase 13 traits are resolved
    dynamically, so the stored stats must represent the pre-trait
    rolled values. Existing adventurers are unbaked exactly once:
    for each flat trait targeting str/agi/int/end/fai we subtract
    `modifier_value` from the stored stat, clamp to ≥ 1 (matches the
    pre-Phase-13 invariant), and set `phase13_unbaked=true`.

    Idempotent via the marker flag; safe to call on every startup.
    """
    cursor = db.adventurers.find(
        {"phase13_unbaked": {"$ne": True}}, {"_id": 0}
    )
    affected = ("strength", "agility", "intellect", "endurance", "faith")
    n_updated = 0
    async for adv in cursor:
        traits = adv.get("traits") or []
        if not traits:
            await db.adventurers.update_one(
                {"id": adv["id"]}, {"$set": {"phase13_unbaked": True}}
            )
            continue
        deltas = {s: 0 for s in affected}
        for t in traits:
            if t.get("modifier_type") == "flat" and t.get("affected_stat") in affected:
                deltas[t["affected_stat"]] += int(t.get("modifier_value", 0) or 0)
        new_stats = {}
        for s in affected:
            new_stats[s] = max(1, int(adv.get(s, 0)) - deltas[s])
        await db.adventurers.update_one(
            {"id": adv["id"]},
            {"$set": {**new_stats, "phase13_unbaked": True}},
        )
        n_updated += 1
    if n_updated:
        logger.info("Phase 13: unbaked legacy traits on %d adventurers", n_updated)


async def run_all_seeds(db) -> None:
    """Orchestrator: run all seeds in order."""
    await seed_classes_and_traits(db)
    await seed_dungeons_and_items(db)
    await seed_tester(db)
    await unbake_legacy_traits(db)


__all__ = [
    "seed_classes_and_traits",
    "seed_dungeons_and_items",
    "seed_tester",
    "unbake_legacy_traits",
    "run_all_seeds",
]
