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

    # CORS — env-gated (see _resolve_cors_origins).
    # ROUND 11.1 Slice 2 — `allow_credentials=True` is incompatible with
    # `allow_origins=["*"]` per CORS spec. In dev/preview we therefore use
    # `allow_origin_regex=".*"` (with explicit credential allowance) so the
    # cookie-based auth flow can complete preflight from any origin.
    cors_origins = _resolve_cors_origins()
    if cors_origins == ["*"]:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=".*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ROUND 11.1 Slice 2 — CSRF double-submit on cookie-authed mutating
    # requests. Bearer-authed requests (legacy 14gg fallback) are exempt
    # because the attacker cannot forge a Bearer header from a cross-site
    # context. Login/register/csrf/logout/refresh exempt for bootstrap.
    from app.core.csrf import CSRFMiddleware
    app.add_middleware(CSRFMiddleware)

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
    from app.quests.routes import router as quests_router
    from app.crafting.routes import router as crafting_router
    from app.market.routes import router as market_router
    from app.chronicle.routes import router as chronicle_router
    from app.consortiums.routes import router as consortiums_router
    from app.forge.routes import router as forge_router
    from app.raids import router as raids_router
    from app.chat.routes import router as chat_router
    from app.shop.routes import router as shop_router
    from app.auction.routes import router as auction_router
    from app.squads.routes import router as squads_router
    from app.territory.routes import router as territory_router
    from app.training.routes import router as training_router
    from app.contracts.routes import router as contracts_router
    # ROUND 11.2 TASK 6 G1-G2 — public traits + stats catalog (no auth).
    from app.catalog.routes import router as catalog_router
    # ROUND 11.2 EXT TASK 10 M1+M4 — public materials catalog (no auth).
    from app.materials.routes import router as materials_router
    # ROUND 12 — Seasons + PvP Arena
    from app.seasons.routes import router as seasons_router, admin_router as seasons_admin_router
    from app.pvp.routes import router as pvp_router
    from app.rewards.routes import router as rewards_router, admin_router as rewards_admin_router

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
    app.include_router(quests_router)
    app.include_router(crafting_router)
    app.include_router(market_router)
    app.include_router(chronicle_router)
    app.include_router(consortiums_router)
    app.include_router(forge_router)
    app.include_router(raids_router)
    app.include_router(chat_router)
    app.include_router(shop_router)
    app.include_router(auction_router)
    app.include_router(squads_router)
    app.include_router(territory_router)
    app.include_router(training_router)
    app.include_router(contracts_router)
    app.include_router(catalog_router)
    app.include_router(materials_router)
    app.include_router(seasons_router)
    app.include_router(seasons_admin_router)
    app.include_router(pvp_router)
    app.include_router(rewards_router)
    app.include_router(rewards_admin_router)

    return app


__all__ = ["create_app", "_resolve_cors_origins"]
