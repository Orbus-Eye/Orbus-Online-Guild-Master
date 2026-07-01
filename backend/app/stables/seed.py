"""ROUND 16.3 Phase 8 V1 — Seed + indexes for stables domain."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.stables.catalog import (
    ANTI_P2W_FLAGS, MOUNT_CATALOG_V1, NARRATIVE_ROUTES_V1,
)


logger = logging.getLogger("orbus.stables")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_stables_indexes(database=None) -> None:
    if database is None:
        from app.core.database import db as _db
        database = _db
    try:
        await database.mount_catalog.create_index("slug", unique=True,
                                                  name="mount_slug_unique")
        await database.mount_catalog.create_index("domain_slug",
                                                  name="mount_domain_idx")
        await database.guild_mount_ownership.create_index(
            [("guild_id", 1), ("mount_slug", 1)],
            unique=True, name="guild_mount_unique",
        )
        await database.guild_mount_ownership.create_index(
            [("guild_id", 1), ("is_active", 1)],
            name="guild_mount_active_idx",
        )
        await database.narrative_routes.create_index("slug", unique=True,
                                                     name="narrative_slug_unique")
        await database.narrative_route_completions.create_index(
            [("guild_id", 1), ("route_slug", 1)],
            unique=True, name="guild_route_completion_unique",
        )
        await database.narrative_rewards_unlocked.create_index(
            [("guild_id", 1), ("reward_slug", 1)],
            unique=True, name="guild_narr_reward_unique",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("stables indexes ensure failed: %s", exc)


async def ensure_mount_catalog(database=None) -> dict:
    """Idempotent seed of MOUNT_CATALOG_V1 (upsert by slug).

    Applies anti-P2W flags on every insert/update. Never touches user data.
    """
    if database is None:
        from app.core.database import db as _db
        database = _db
    inserted = 0
    updated = 0
    now = _now_iso()
    for entry in MOUNT_CATALOG_V1:
        doc = {**entry, **ANTI_P2W_FLAGS}
        # Anti-drift: even if catalog file were edited to try to set flags
        # to True, this line hard-overrides to False. Removing this check
        # would need a policy update in /app/memory/pytest_db_isolation_policy.md
        # (and eventually a dedicated anti-P2W policy doc).
        for flag in ("affects_combat", "affects_economy", "affects_ranking",
                     "affects_travel_time", "can_be_sold_for_real_money"):
            doc[flag] = False
        existing = await database.mount_catalog.find_one(
            {"slug": doc["slug"]}, {"_id": 0, "id": 1},
        )
        if existing:
            await database.mount_catalog.update_one(
                {"slug": doc["slug"]},
                {"$set": {**doc, "updated_at": now}},
            )
            updated += 1
        else:
            doc["id"] = str(uuid.uuid4())
            doc["created_at"] = now
            doc["updated_at"] = now
            await database.mount_catalog.insert_one({**doc})
            inserted += 1
    logger.info("ROUND 16.3 Phase 8 V1 mount_catalog: %d inserted, %d updated",
                inserted, updated)
    return {"inserted": inserted, "updated": updated,
            "total": len(MOUNT_CATALOG_V1)}


async def ensure_narrative_routes(database=None) -> dict:
    """Idempotent seed of NARRATIVE_ROUTES_V1 (upsert by slug)."""
    if database is None:
        from app.core.database import db as _db
        database = _db
    inserted = 0
    updated = 0
    now = _now_iso()
    for entry in NARRATIVE_ROUTES_V1:
        doc = {**entry, "is_active": True}
        existing = await database.narrative_routes.find_one(
            {"slug": doc["slug"]}, {"_id": 0, "id": 1},
        )
        if existing:
            await database.narrative_routes.update_one(
                {"slug": doc["slug"]},
                {"$set": {**doc, "updated_at": now}},
            )
            updated += 1
        else:
            doc["id"] = str(uuid.uuid4())
            doc["created_at"] = now
            doc["updated_at"] = now
            await database.narrative_routes.insert_one({**doc})
            inserted += 1
    logger.info("ROUND 16.3 Phase 8 V1 narrative_routes: %d inserted, %d updated",
                inserted, updated)
    return {"inserted": inserted, "updated": updated,
            "total": len(NARRATIVE_ROUTES_V1)}


__all__ = [
    "ensure_stables_indexes",
    "ensure_mount_catalog", "ensure_narrative_routes",
]
