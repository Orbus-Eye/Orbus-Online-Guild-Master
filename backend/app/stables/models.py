"""ROUND 16.3 Phase 8 V1 — Pydantic models for stables."""
from __future__ import annotations

from pydantic import BaseModel


class SetActiveMountPayload(BaseModel):
    mount_slug: str


class AdminGrantMountPayload(BaseModel):
    guild_id: str
    mount_slug: str
