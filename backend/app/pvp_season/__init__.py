"""ROUND 16.3 Phase 7B — PvP Season leaderboard + cosmetics (backend Iter1).

Weekly season snapshot of the continental Elo leaderboard.
Top 10 per continent receive strictly cosmetic rewards (title/badge/frame).
No gold/XP/loot/stat rewards. Anti-P2W by design.
"""
from app.pvp_season.routes import router  # noqa: F401
from app.pvp_season.admin_routes import router as admin_router  # noqa: F401
from app.pvp_season.services import ensure_indexes  # noqa: F401

__all__ = ["router", "admin_router", "ensure_indexes"]
