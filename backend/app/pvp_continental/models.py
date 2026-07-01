"""ROUND 16.3 Phase 7A — PvP Continental Pydantic schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChallengePayload(BaseModel):
    adventurer_ids: list[str] = Field(min_length=5, max_length=5)


class RespondPayload(BaseModel):
    adventurer_ids: list[str] = Field(min_length=5, max_length=5)


class DeclinePayload(BaseModel):
    """Empty body reserved for future decline reasons."""
    pass


BattleStatus = Literal[
    "pending_response", "resolving", "resolved", "expired", "declined"
]
BattleOutcome = Literal[
    "challenger_win", "defender_win", "draw", "defender_forfeit"
]
