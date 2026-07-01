"""ROUND 13a — Idempotent lore enrichment seed for dungeons + raid_dungeons.

Applies `DUNGEON_LORE_PATCHES` / `RAID_LORE_PATCHES` (from
`app.content.lore_meta`) to existing documents. Adds:
  * `name_it`, `description_it`-friendly fields (kept additive).
  * `lore_theme`, `content_family`, `emotional_tone`, `location_hint`,
    `narrative_hook`, `enemy_families`, `boss_name` (raid only),
    `spoiler_level`, `lore_reviewed=True`, `lore_reviewed_at`,
    `lore_source="orbus_lore_book_v1"`.

Idempotent: re-runs are no-ops once `lore_reviewed=True`. No slug or
existing `name` modified.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.core.database import db
from app.content.lore_meta import DUNGEON_LORE_PATCHES, RAID_LORE_PATCHES

logger = logging.getLogger("orbus.seed_round13a_dungeon_raid_lore")

LORE_SOURCE = "orbus_lore_book_v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _patch_dungeons() -> dict:
    updated = 0
    skipped = 0
    missing_in_db: list[str] = []
    for slug, patch in DUNGEON_LORE_PATCHES.items():
        existing = await db.dungeons.find_one(
            {"slug": slug}, {"_id": 0, "slug": 1, "lore_reviewed": 1}
        )
        if existing is None:
            missing_in_db.append(slug)
            continue
        if existing.get("lore_reviewed"):
            skipped += 1
            continue
        set_fields = {
            **patch,
            "lore_reviewed": True,
            "lore_reviewed_at": _now(),
            "lore_source": LORE_SOURCE,
        }
        await db.dungeons.update_one({"slug": slug}, {"$set": set_fields})
        updated += 1
    return {
        "dungeons_updated": updated,
        "dungeons_skipped_already_reviewed": skipped,
        "patches_missing_in_db": missing_in_db,
    }


async def _patch_raids() -> dict:
    updated = 0
    skipped = 0
    missing: list[str] = []
    for slug, patch in RAID_LORE_PATCHES.items():
        existing = await db.raid_dungeons.find_one(
            {"slug": slug}, {"_id": 0, "slug": 1, "lore_reviewed": 1}
        )
        if existing is None:
            missing.append(slug)
            continue
        if existing.get("lore_reviewed"):
            skipped += 1
            continue
        set_fields = {
            **patch,
            "lore_reviewed": True,
            "lore_reviewed_at": _now(),
            "lore_source": LORE_SOURCE,
        }
        await db.raid_dungeons.update_one({"slug": slug}, {"$set": set_fields})
        updated += 1
    return {
        "raids_updated": updated,
        "raids_skipped_already_reviewed": skipped,
        "patches_missing_in_db": missing,
    }


async def run() -> dict:
    dres = await _patch_dungeons()
    rres = await _patch_raids()
    out = {"status": "done", "dungeons": dres, "raids": rres}
    logger.info("ROUND 13a dungeon/raid lore: %s", out)
    return out


if __name__ == "__main__":
    print(asyncio.run(run()))
