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
    # ROUND 16.x P1 — public races catalog (no auth).
    from app.races.routes import router as races_router
    # ROUND 16.3 Phase 7A — PvP Continental (backend)
    from app.pvp_continental import router as pvp_continental_router, admin_router as pvp_continental_admin_router
    # ROUND 12 — Seasons + PvP Arena
    from app.seasons.routes import router as seasons_router, admin_router as seasons_admin_router
    from app.pvp.routes import router as pvp_router
    from app.rewards.routes import router as rewards_router, admin_router as rewards_admin_router
    from app.admin.ops_routes import router as admin_ops_router
    from app.admin.game_health_routes import router as admin_game_health_router
    from app.admin.audit_routes import router as admin_audit_router  # ROUND 16.A Phase 3
    # ROUND 15 — Phase 3 — Achievements + Guild XP/Level
    from app.achievements.routes import router as achievements_router
    # ROUND 16.0 — Class Halls
    from app.class_halls.routes import router as class_halls_router
    # ROUND 16.1 Phase 1 — Dashboard data-driven cards
    from app.dashboard.routes import router as dashboard_router
    # ROUND 16.3 Phase 1 — World Boss V1 Alveora
    from app.world_boss import router as world_boss_router, admin_router as world_boss_admin_router, seed_world_boss_catalog
    # ROUND 16.3 Phase 2 — Mondo & 8 Mastocontinenti V1
    from app.world import router as world_router, admin_router as world_admin_router, seed_world_continents
    # ROUND 16.3 Phase 3 — Continent events + Site contracts
    from app.world_events import (
        router as world_events_router,
        admin_router as world_events_admin_router,
        seed_continent_event_catalog,
    )
    from app.site_contracts import (
        router as site_income_router,
        admin_router as site_income_admin_router,
        seed_site_income_config,
        ensure_indexes as ensure_site_income_indexes,
    )
    # ROUND 16.3 Phase 4 — Continent resources + leaderboards
    from app.resources import (
        router as resources_router,
        leaderboard_router as continent_lb_router,
        admin_router as resources_admin_router,
        admin_lb_router as continent_lb_admin_router,
        seed_resource_catalog,
        ensure_indexes as ensure_resource_indexes,
    )
    # ROUND 16.3 Phase 5A — Legendary Forge
    from app.legendary_forge import (
        router as legendary_forge_router,
        admin_router as legendary_forge_admin_router,
        seed_legendary_forge_catalog,
        ensure_indexes as ensure_legendary_forge_indexes,    )
    # ROUND 16.3 Phase 5B — Arfus Forge
    from app.arfus_forge import (
        router as arfus_forge_router,
        admin_router as arfus_forge_admin_router,
        seed_arfus_forge_catalog,
        ensure_indexes as ensure_arfus_forge_indexes,
    )
    # ROUND 16.3 Phase 6 — Trade Pacts + Guild Specialization
    from app.trade_pacts import (
        router as trade_pacts_router,
        admin_router as trade_pacts_admin_router,
        ensure_indexes as ensure_trade_pacts_indexes,
    )
    from app.guild_specialization import (
        router as guild_spec_router,
        admin_router as guild_spec_admin_router,
        seed_guild_specialization_catalog,
        ensure_indexes as ensure_guild_spec_indexes,
    )
    # ROUND 16.3 Phase 7B — PvP Seasons (leaderboard + cosmetics)
    from app.pvp_season import (
        router as pvp_season_router,
        admin_router as pvp_season_admin_router,
        ensure_indexes as ensure_pvp_season_indexes,
    )
    # ROUND 16.3 Phase 8 V1 — Stables & Mounts (cosmetic + narrative)
    from app.stables import (
        router as stables_router,
        admin_router as stables_admin_router,
        ensure_stables_indexes,
        ensure_mount_catalog,
        ensure_narrative_routes,
    )

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
    app.include_router(admin_game_health_router)
    app.include_router(admin_audit_router)
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
    app.include_router(races_router)
    app.include_router(pvp_continental_router)
    app.include_router(pvp_continental_admin_router)
    app.include_router(seasons_router)
    app.include_router(seasons_admin_router)
    app.include_router(pvp_router)
    app.include_router(rewards_router)
    app.include_router(rewards_admin_router)
    app.include_router(admin_ops_router)
    app.include_router(achievements_router)
    app.include_router(class_halls_router)
    app.include_router(dashboard_router)
    app.include_router(world_boss_router)
    app.include_router(world_boss_admin_router)
    app.include_router(world_router)
    app.include_router(world_admin_router)
    app.include_router(world_events_router)
    app.include_router(world_events_admin_router)
    app.include_router(site_income_router)
    app.include_router(site_income_admin_router)
    app.include_router(resources_router)
    app.include_router(continent_lb_router)
    app.include_router(resources_admin_router)
    app.include_router(continent_lb_admin_router)
    app.include_router(legendary_forge_router)
    app.include_router(legendary_forge_admin_router)
    app.include_router(arfus_forge_router)
    app.include_router(arfus_forge_admin_router)
    app.include_router(trade_pacts_router)
    app.include_router(trade_pacts_admin_router)
    app.include_router(guild_spec_router)
    app.include_router(guild_spec_admin_router)
    app.include_router(pvp_season_router)
    app.include_router(pvp_season_admin_router)
    app.include_router(stables_router)
    app.include_router(stables_admin_router)

    # Seed continent event catalog + site income config on startup (idempotent)
    @app.on_event("startup")
    async def _seed_r163_phase3_startup():
        import logging
        log = logging.getLogger("orbus")
        try:
            r1 = await seed_continent_event_catalog()
            log.info("ROUND 16.3 Phase 3 continent events catalog: %s", r1)
        except Exception as exc:
            log.warning("continent_event_catalog seed failed: %s", exc)
        try:
            r2 = await seed_site_income_config()
            log.info("ROUND 16.3 Phase 3 site income config: %s", r2)
        except Exception as exc:
            log.warning("site_income_config seed failed: %s", exc)
        try:
            await ensure_site_income_indexes()
        except Exception as exc:
            log.debug("site_income_indexes ensure failed: %s", exc)
        try:
            r3 = await seed_resource_catalog()
            log.info("ROUND 16.3 Phase 4 resource catalog: %s", r3)
        except Exception as exc:
            log.warning("resource_catalog seed failed: %s", exc)
        try:
            await ensure_resource_indexes()
        except Exception as exc:
            log.debug("resource_indexes ensure failed: %s", exc)
        try:
            r4 = await seed_legendary_forge_catalog()
            log.info("ROUND 16.3 Phase 5A legendary forge catalog: %s", r4)
        except Exception as exc:
            log.warning("legendary_forge_catalog seed failed: %s", exc)
        try:
            await ensure_legendary_forge_indexes()
        except Exception as exc:
            log.debug("legendary_forge_indexes ensure failed: %s", exc)
        try:
            r5 = await seed_arfus_forge_catalog()
            log.info("ROUND 16.3 Phase 5B arfus forge catalog: %s", r5)
        except Exception as exc:
            log.warning("arfus_forge_catalog seed failed: %s", exc)
        try:
            await ensure_arfus_forge_indexes()
        except Exception as exc:
            log.debug("arfus_forge_indexes ensure failed: %s", exc)
        try:
            await ensure_trade_pacts_indexes()
        except Exception as exc:
            log.debug("trade_pacts_indexes ensure failed: %s", exc)
        try:
            r6 = await seed_guild_specialization_catalog()
            log.info("ROUND 16.3 Phase 6 guild specialization catalog: %s", r6)
        except Exception as exc:
            log.warning("guild_specialization_catalog seed failed: %s", exc)
        try:
            await ensure_guild_spec_indexes()
        except Exception as exc:
            log.debug("guild_spec_indexes ensure failed: %s", exc)
        try:
            await ensure_pvp_season_indexes()
            log.info("ROUND 16.3 Phase 7B pvp_season indexes ensured")
        except Exception as exc:
            log.debug("pvp_season_indexes ensure failed: %s", exc)

    # Seed world boss catalog on startup (idempotent)
    @app.on_event("startup")
    async def _seed_world_boss_startup():
        try:
            await seed_world_boss_catalog()
        except Exception as exc:
            import logging
            logging.getLogger("orbus.world_boss").warning(
                "world_boss seed failed: %s", exc)

    return app


__all__ = ["create_app", "_resolve_cors_origins"]
