"""ROUND 12.A — Idempotent preseason seed.

Inserts the `arena-preseason-2026` season as `active` if no other active
season exists. Safe to re-run: skips on duplicate.

Usage:
  python -m app.scripts.seed_round12_preseason
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from app.core.database import db
from app.audit.log import write_audit
from app.seasons.services import ensure_season_indexes

logger = logging.getLogger("orbus.seed_round12_preseason")


SLUG = "arena-preseason-2026"


async def run() -> dict:
    await ensure_season_indexes(db)

    existing_by_slug = await db.seasons.find_one({"slug": SLUG})
    if existing_by_slug:
        return {"status": "skipped", "reason": "slug_already_present",
                "season_id": existing_by_slug["season_id"]}

    active = await db.seasons.find_one({"status": "active"})
    if active:
        return {"status": "skipped", "reason": "another_active_season",
                "active_slug": active["slug"]}

    now = datetime.now(timezone.utc)
    season_id = str(uuid.uuid4())
    doc = {
        "season_id": season_id,
        "public_id": SLUG,
        "slug": SLUG,
        "name_it": "Preseason delle Arene",
        "name_en": "Arena Preseason",
        "lore_theme": "equilibrio",
        "status": "active",
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=90)).isoformat(),
        "scoring_version": 1,
        "rules_version": 1,
        "reward_version": 1,
        "is_ranked": True,
        "is_test": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "ended_at": None,
        "archived_at": None,
    }
    await db.seasons.insert_one(doc)
    await write_audit(
        db, event_type="season_created", source="seed.round12_preseason",
        metadata={"slug": SLUG, "season_id": season_id, "reason": "preseason bootstrap"},
    )
    await write_audit(
        db, event_type="season_activated", source="seed.round12_preseason",
        metadata={"slug": SLUG, "season_id": season_id, "reason": "preseason bootstrap"},
    )
    return {"status": "created", "season_id": season_id, "slug": SLUG}


if __name__ == "__main__":
    res = asyncio.run(run())
    print(res)
