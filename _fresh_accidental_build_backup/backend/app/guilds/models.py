"""Modelli Pydantic per il dominio Gilde."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GuildCreateInput(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    description: str = Field(default="", max_length=500)


class GuildPublic(BaseModel):
    id: str
    owner_user_id: str
    name: str
    description: str
    level: int
    reputation: int
    gold: int
    created_at: str
    updated_at: str
