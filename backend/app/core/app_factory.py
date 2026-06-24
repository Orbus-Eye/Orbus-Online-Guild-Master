"""FastAPI application factory (Phase 5.5g).

`create_app()` is the single entry point: configures FastAPI, mounts CORS,
the `/api/health` route, and all 10 domain routers. Everything else lives
in `app/<domain>/`. `server.py` is now a thin wrapper that exists only for
uvicorn/supervisor compatibility (`server:app`).
"""
import os
import logging

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.lifespan import lifespan


logger = logging.getLogger("orbus")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _resolve_cors_origins() -> list[str]:
    """In production, CORS_ORIGINS must be set explicitly (no '*').
    In dev/preview, defaults to ['*'] for convenience.
    """
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    app_env = os.environ.get("APP_ENV", "development")
    if app_env == "production":
        if not raw or raw == "*":
            raise RuntimeError(
                "APP_ENV=production requires CORS_ORIGINS to be set explicitly "
                "(comma-separated, no '*')."
            )
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if "*" in origins:
            raise RuntimeError("CORS_ORIGINS cannot contain '*' when APP_ENV=production.")
        return origins
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def _build_health_router() -> APIRouter:
    """Tiny `/api/health` endpoint (no domain logic; lives in the factory)."""
    r = APIRouter(prefix="/api")

    @r.get("/health")
    async def health():
        return {"status": "ok", "env": os.environ.get("APP_ENV", "development")}

    return r


def create_app() -> FastAPI:
    """Build and return the configured FastAPI app instance."""
    app = FastAPI(
        title="Orbus Online: Guild Master",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS — env-gated (see _resolve_cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint (no domain)
    app.include_router(_build_health_router())

    # Domain routers — each carries its own `/api/<domain>` prefix.
    # Imported here (function-local) so the rest of the module can be loaded
    # without triggering the full router import graph (useful for tooling).
    from app.auth.routes import router as auth_router
    from app.guilds.routes import router as guilds_router
    from app.dungeons.routes import router as dungeons_router
    from app.items.routes import router as items_router
    from app.expeditions.routes import router as expeditions_router
    from app.inventory.routes import router as inventory_router
    from app.recruitment.routes import router as recruitment_router
    from app.adventurers.routes import router as adventurers_router
    from app.equipment.routes import router as equipment_router
    from app.admin.routes import router as admin_router
    from app.leaderboard.routes import router as leaderboard_router

    app.include_router(auth_router)
    app.include_router(guilds_router)
    app.include_router(dungeons_router)
    app.include_router(items_router)
    app.include_router(expeditions_router)
    app.include_router(inventory_router)
    app.include_router(recruitment_router)
    app.include_router(adventurers_router)
    app.include_router(equipment_router)
    app.include_router(admin_router)
    app.include_router(leaderboard_router)

    return app


__all__ = ["create_app", "_resolve_cors_origins"]
