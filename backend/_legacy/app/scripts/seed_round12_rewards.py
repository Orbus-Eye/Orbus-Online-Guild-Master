"""ROUND 12.C — Idempotent seed of cosmetic preseason rewards."""
from __future__ import annotations

import asyncio
import logging

from app.core.database import db
from app.rewards.services import ensure_reward_indexes, insert_reward
from app.seasons.services import ensure_season_indexes

logger = logging.getLogger("orbus.seed_round12_rewards")

REWARDS = [
    {
        "reward_id": "preseason_veteran_title",
        "reward_type": "title",
        "name_it": "Veterano della Preseason",
        "name_en": "Preseason Veteran",
        "description_it": "Hai partecipato alla prima Preseason delle Arene di Orbus.",
        "criteria": {"min_participation": True},
    },
    {
        "reward_id": "first_arena_badge",
        "reward_type": "badge",
        "name_it": "Prima Arena",
        "name_en": "First Arena",
        "description_it": "Hai completato la tua prima sfida nelle Arene della Gloria.",
        "criteria": {"min_matches": 1},
    },
    {
        "reward_id": "bronze_arena_frame",
        "reward_type": "frame",
        "name_it": "Cornice del Bronzo delle Arene",
        "name_en": "Bronze Arena Frame",
        "description_it": "Cornice profilo concessa a chi raggiunge almeno il Bronzo nelle Arene.",
        "criteria": {"min_league": "bronze"},
    },
    {
        "reward_id": "glory_master_title",
        "reward_type": "title",
        "name_it": "Maestro della Gloria",
        "name_en": "Master of Glory",
        "description_it": "Riconoscimento onorifico per chi raggiunge il vertice della Preseason.",
        "criteria": {"min_league": "master"},
    },
]


async def run():
    await ensure_season_indexes(db)
    await ensure_reward_indexes(db)
    season = await db.seasons.find_one({"status": "active"})
    if not season:
        return {"status": "skipped", "reason": "no_active_season"}
    inserted, skipped = 0, 0
    for r in REWARDS:
        existing = await db.season_rewards.find_one({"reward_id": r["reward_id"]})
        if existing:
            skipped += 1
            continue
        await insert_reward(db, {**r, "season_id": season["season_id"]})
        inserted += 1
    return {"status": "done", "inserted": inserted, "skipped": skipped,
            "season_id": season["season_id"]}


if __name__ == "__main__":
    print(asyncio.run(run()))
