"""ROUND 16.3 Phase 7B — Pydantic models for PvP seasons."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SeasonCurrentResponse(BaseModel):
    id: str
    season_number: int
    started_at: str
    ends_at: str
    status: str
    time_remaining_seconds: int


class LeaderboardEntry(BaseModel):
    rank: int
    guild_id: str
    guild_name: str
    elo: int
    wins: int
    losses: int
    draws: int
    is_my_guild: bool = False
    cosmetics_awarded: list[str] = Field(default_factory=list)


class LeaderboardResponse(BaseModel):
    season_id: str
    season_number: int
    continent_slug: str
    finalized: bool
    entries: list[LeaderboardEntry]


class AllContinentsResponse(BaseModel):
    season_id: str
    season_number: int
    finalized: bool
    by_continent: dict[str, list[LeaderboardEntry]]


class UnlockedCosmetic(BaseModel):
    id: str
    cosmetic_slug: str
    type: str
    name_it: str
    continent_slug: str
    season_number: int
    rank_awarded: int
    unlocked_at: str


class CosmeticsMineResponse(BaseModel):
    guild_id: str
    total: int
    by_type: dict[str, int]
    items: list[UnlockedCosmetic]


class CosmeticCatalogEntry(BaseModel):
    cosmetic_slug: str
    type: str
    name_it: str
    description_it: str
    rank_required: int
    continent_slug: str


class CosmeticCatalogResponse(BaseModel):
    total: int
    entries: list[CosmeticCatalogEntry]


__all__ = [
    "SeasonCurrentResponse",
    "LeaderboardEntry",
    "LeaderboardResponse",
    "AllContinentsResponse",
    "UnlockedCosmetic",
    "CosmeticsMineResponse",
    "CosmeticCatalogEntry",
    "CosmeticCatalogResponse",
]
