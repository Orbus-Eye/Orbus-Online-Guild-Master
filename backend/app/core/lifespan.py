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
from app.seeds.seed_forge import run_forge_seeds, run_forge_migration
from app.seeds.seed_round5 import run_round5_seeds_and_migrations


logger = logging.getLogger("orbus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_indexes(db)
    await ensure_audit_indexes(db)
    await ensure_market_indexes(db)
    await ensure_consortium_indexes(db)
    await run_forge_migration(db)
    await run_forge_seeds(db)
    await run_all_seeds(db)
    await run_round5_seeds_and_migrations(db)
    logger.info("Orbus backend ready (env=%s)", os.environ.get("APP_ENV", "development"))
    yield
    mongo_client.close()


__all__ = ["lifespan"]
