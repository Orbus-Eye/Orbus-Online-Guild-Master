"""FastAPI application factory + router registration."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.accounts.router import router as accounts_router
from app.core.config import get_settings
from app.core.database import connect, init_indexes, close
from app.core.seed import run_seed
from app.guilds.router import router as guilds_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orbus.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown: apri DB, crea indici, esegui seed."""
    connect()
    await init_indexes()
    await run_seed()
    logger.info("Orbus backend pronto.")
    yield
    await close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Orbus Online: Guild Master",
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health
    @app.get("/api/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "env": settings.app_env}

    # Domain routers
    app.include_router(accounts_router)
    app.include_router(guilds_router)

    return app


app = create_app()
