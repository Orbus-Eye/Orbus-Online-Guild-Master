"""ROUND 6B.3 — Seed for Territory atomic-debit materials.

Two reagents referenced by `app.territory.costs.UPGRADE_COSTS` were missing
from the `items` collection:
  - `lesser_arcane_dust`
  - `greater_arcane_dust`

`iron_shard` already exists (added by an earlier seed pass). This seed is
idempotent: it ONLY inserts a row when `db.items.find_one({slug=...})`
returns None.

Field values follow the same shape as other Round 4/5 materials (rarity,
item_type, name, description) — chosen conservatively. Game designer
should review `power_band` / `gold_value` for balance pass.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("orbus.seed_territory_materials")

_MATERIALS = [
    {
        "slug": "lesser_arcane_dust",
        "name": "Lesser Arcane Dust",
        "description": "Polvere arcana di scarto. Componente comune per "
                       "potenziare strutture di livello medio.",
        "item_type": "material",
        "category": "material",
        "rarity": "Uncommon",
        "gold_value": 25,
    },
    {
        "slug": "greater_arcane_dust",
        "name": "Greater Arcane Dust",
        "description": "Polvere arcana raffinata. Reagente raro per le "
                       "strutture di alto livello del Territorio.",
        "item_type": "material",
        "category": "material",
        "rarity": "Rare",
        "gold_value": 100,
    },
]


async def seed_territory_materials(db) -> dict:
    """Idempotent: insert any missing reagent. Returns a small report.

    ROUND 11.1 P1 hotfix: also backfills `power_score: 0` on any item
    missing the field (materials seeded pre-Round-6E never had it, which
    raised KeyError on `GET /api/inventory`).
    """
    now = datetime.now(timezone.utc).isoformat()
    inserted: list[str] = []
    skipped: list[str] = []
    for m in _MATERIALS:
        existing = await db.items.find_one({"slug": m["slug"]}, {"_id": 0, "id": 1})
        if existing:
            skipped.append(m["slug"])
            continue
        doc = {
            "id": str(uuid.uuid4()),
            **m,
            "power_score": 0,            # ROUND 11.1 P1 — required by `item_public`
            "is_test": False,
            "created_at": now,
            "updated_at": now,
        }
        try:
            await db.items.insert_one(doc)
            inserted.append(m["slug"])
        except Exception as exc:  # noqa: BLE001
            # Likely a unique-index race with another worker — re-read and skip.
            logger.warning("seed_territory_materials insert raced on %s: %s",
                           m["slug"], exc)
            skipped.append(m["slug"])
    # ROUND 11.1 P1 — idempotent backfill of `power_score` for legacy rows
    # that pre-date the field. Safe to re-run on every boot.
    backfill = await db.items.update_many(
        {"power_score": {"$exists": False}},
        {"$set": {"power_score": 0}},
    )
    logger.info(
        "Round 6B.3 territory materials: inserted=%s skipped=%s "
        "power_score_backfill=%d",
        inserted, skipped, backfill.modified_count,
    )
    return {
        "inserted": inserted,
        "skipped": skipped,
        "power_score_backfill": backfill.modified_count,
    }


__all__ = ["seed_territory_materials"]
