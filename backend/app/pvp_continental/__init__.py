"""ROUND 16.3 Phase 7A — PvP Continental (backend, Iteration 1)."""
from app.pvp_continental.routes import router  # noqa: F401
from app.pvp_continental.admin_routes import router as admin_router  # noqa: F401

__all__ = ["router", "admin_router"]
