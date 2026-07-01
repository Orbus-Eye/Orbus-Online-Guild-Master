"""ROUND 16.3 Phase 8 V1 — Stables & Mounts (backend, Iter1).

Cosmetic + narrative mount system. **Zero balance impact by design.**
- All mounts: affects_combat=affects_economy=affects_ranking=affects_travel_time=False
- All rewards: narrative badges/titles (never gold/XP/materials)
- Free-to-earn only: starter quest, world boss drop, achievement, craft
"""
from app.stables.routes import router  # noqa: F401
from app.stables.admin_routes import router as admin_router  # noqa: F401
from app.stables.seed import (  # noqa: F401
    ensure_mount_catalog,
    ensure_narrative_routes,
    ensure_stables_indexes,
)

__all__ = [
    "router", "admin_router",
    "ensure_mount_catalog", "ensure_narrative_routes",
    "ensure_stables_indexes",
]
