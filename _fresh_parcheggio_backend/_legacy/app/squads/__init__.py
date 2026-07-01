"""Squads domain (ROUND 6A.2a) — Custom adventurer squads.

Squads are a pure UX convenience: pre-saved adventurer groupings for
dungeons (3p / 5p) and raids (20p, 4 parties × 5). They store ONLY the
`adventurer_ids` (+ `raid_parties` for raid_20) — `total_power` is always
re-derived from live adventurer state to avoid stale snapshots after
level-ups or gear changes.

NEVER provide any power bonus or stat modification. NEVER hard-delete.
"""
from app.squads.routes import router

__all__ = ["router"]
