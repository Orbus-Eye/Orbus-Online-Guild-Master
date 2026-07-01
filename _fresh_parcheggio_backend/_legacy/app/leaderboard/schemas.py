"""Leaderboard schemas (Phase 9.1).

Public-facing — no JWT required. Strictly excludes sensitive fields from
the underlying `guilds` document (`owner_user_id`, password hashes, email,
admin flags). Only the safe subset is exposed.
"""
from typing import Optional

from pydantic import BaseModel, Field


class LeaderboardEntryOut(BaseModel):
    rank: int = Field(ge=1)
    guild_id: str
    guild_name: str
    level: int
    reputation: int
    max_team_power_ever: int
    highest_dungeon_slug: Optional[str] = None
    total_expeditions_completed: int = 0
    created_at: str


class LeaderboardOut(BaseModel):
    total: int
    limit: int
    offset: int
    entries: list[LeaderboardEntryOut]


__all__ = ["LeaderboardEntryOut", "LeaderboardOut"]
