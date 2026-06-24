"""Guilds domain Pydantic schemas (Phase 5.5c + 11.3 onboarding)."""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GuildCreateIn(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    description: str = Field(default="", max_length=300)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("name must be at least 3 characters")
        return v


class OnboardingPatchIn(BaseModel):
    """Body for PATCH /api/guilds/onboarding.

    All fields optional; only those provided are applied. `step` must be in
    [1, 5] and is monotonically increasing (server clamps regressions).
    """
    step: Optional[int] = Field(default=None, ge=1, le=5)
    dismissed: Optional[bool] = None
    completed: Optional[bool] = None


__all__ = ["GuildCreateIn", "OnboardingPatchIn"]

