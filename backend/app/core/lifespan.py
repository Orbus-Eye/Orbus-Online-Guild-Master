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
    logger.info("Orbus backend ready (env=%s)", os.environ.get("APP_ENV", "development"))
    yield
    mongo_client.close()


__all__ = ["lifespan"]
