"""ASGI lifespan (Phase 5.5g).

Startup: ensure MongoDB indexes + run idempotent seeds + log readiness.
Shutdown: close the Motor client. Identical semantics to the legacy
`lifespan` inside `server.py`.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import db, mongo_client
from app.core.indexes import create_all_indexes
from app.seeds.seed_runner import run_all_seeds
from app.audit.log import ensure_audit_indexes
from app.market.services import ensure_market_indexes
from app.consortiums.services import ensure_consortium_indexes
from app.chat.services import ensure_chat_indexes
from app.shop.services import ensure_shop_indexes
from app.seeds.seed_forge import run_forge_seeds, run_forge_migration
from app.seeds.seed_round5 import run_round5_seeds_and_migrations
from app.seeds.seed_territory_materials import seed_territory_materials
from app.inventory.bound import (
    backfill_bound_fields_if_missing,
    ensure_bound_indexes,
)


logger = logging.getLogger("orbus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_indexes(db)
    await ensure_audit_indexes(db)
    await ensure_market_indexes(db)
    await ensure_consortium_indexes(db)
    await ensure_chat_indexes(db)
    await ensure_shop_indexes(db)
    # ROUND 12 — Seasons + PvP indexes (idempotent).
    from app.seasons.services import ensure_season_indexes
    from app.pvp.services import ensure_pvp_indexes
    from app.rewards.services import ensure_reward_indexes
    await ensure_season_indexes(db)
    await ensure_pvp_indexes(db)
    await ensure_reward_indexes(db)
    # ROUND 12 — preseason + demo opponents seed (preview-only, idempotent).
    try:
        from app.scripts.seed_round12_preseason import run as _seed_preseason
        from app.scripts.seed_round12_rewards import run as _seed_rewards
        from app.scripts.seed_round12_demo_opponents import run as _seed_demos
        from app.scripts.seed_round12_release_tester_roster import (
            run as _seed_release_tester,
        )
        # ROUND 13a — Recovery + Lore pack seeds (idempotent, additive).
        from app.scripts.seed_round13a_dungeon_raid_lore import run as _seed_r13a_dr
        from app.scripts.seed_round13a_items_lore import run as _seed_r13a_items
        await _seed_preseason()
        await _seed_rewards()
        await _seed_demos()
        # ROUND 12.D.3 — preview-only: free tester's stuck adventurers
        # so they can build a PvP defense team. No-op in production.
        await _seed_release_tester()
        # ROUND 13a — Apply lore patches to dungeons/raids + items.
        await _seed_r13a_dr()
        await _seed_r13a_items()
    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger("orbus").warning("ROUND 12 seed at startup failed: %s", exc)
    await run_forge_migration(db)
    await run_forge_seeds(db)
    await run_all_seeds(db)
    await run_round5_seeds_and_migrations(db)
    await seed_territory_materials(db)  # ROUND 6B.3 — idempotent material seed
    # ROUND 6B.4 — adventurer-bound schema migration + sparse index.
    # Both calls are idempotent: safe to run on every boot.
    bound_result = await backfill_bound_fields_if_missing(db)
    logger.info("ROUND 6B.4 bound fields backfill: %s", bound_result)
    await ensure_bound_indexes(db)
    # ROUND 6C signature visibility — seed `db.items` templates for every
    # signature catalog entry so `/api/inventory` joins resolve, and
    # backfill missing inventory rows for advs whose signature_item_id was
    # wiped by the pytest orphan cleanup (now fixed in conftest.py).
    from app.training.seed_signature import (
        backfill_missing_signature_inventory_rows,
        seed_signature_templates,
    )
    sig_tpl = await seed_signature_templates(db)
    logger.info("ROUND 6C signature templates: %s", sig_tpl)
    sig_bf = await backfill_missing_signature_inventory_rows(db)
    logger.info("ROUND 6C signature backfill: %s", sig_bf)
    # ROUND 16.3 Phase 1 — seed World Boss catalog Alveora
    try:
        from app.world_boss import seed_world_boss_catalog
        await seed_world_boss_catalog()
        logger.info("ROUND 16.3 Phase 1 world boss catalog: seeded (idempotent)")
    except Exception as exc:
        logger.warning("world_boss seed failed: %s", exc)
    logger.info("Orbus backend ready (env=%s)", os.environ.get("APP_ENV", "development"))
    yield
    mongo_client.close()


__all__ = ["lifespan"]
