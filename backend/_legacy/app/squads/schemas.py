"""Squads Pydantic schemas (ROUND 6A.2a)."""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


VALID_SQUAD_TYPES = {"dungeon_3", "dungeon_5", "raid_20"}
SQUAD_SIZE = {"dungeon_3": 3, "dungeon_5": 5, "raid_20": 20}


class RaidPartiesIn(BaseModel):
    party_1: list[str] = Field(..., min_length=5, max_length=5)
    party_2: list[str] = Field(..., min_length=5, max_length=5)
    party_3: list[str] = Field(..., min_length=5, max_length=5)
    party_4: list[str] = Field(..., min_length=5, max_length=5)


class SquadCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=32)
    squad_type: str
    adventurer_ids: list[str]
    raid_parties: Optional[RaidPartiesIn] = None

    @field_validator("squad_type")
    @classmethod
    def _valid_type(cls, v):
        if v not in VALID_SQUAD_TYPES:
            raise ValueError(f"squad_type must be one of {sorted(VALID_SQUAD_TYPES)}")
        return v

    @field_validator("name")
    @classmethod
    def _no_html(cls, v):
        v = (v or "").strip()
        if "<" in v or ">" in v:
            raise ValueError("name.html_forbidden")
        return v


class SquadUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=32)
    adventurer_ids: Optional[list[str]] = None
    raid_parties: Optional[RaidPartiesIn] = None

    @field_validator("name")
    @classmethod
    def _no_html(cls, v):
        if v is None:
            return v
        v = v.strip()
        if "<" in v or ">" in v:
            raise ValueError("name.html_forbidden")
        return v


__all__ = ["SquadCreateIn", "SquadUpdateIn", "RaidPartiesIn", "VALID_SQUAD_TYPES", "SQUAD_SIZE"]
