"""ROUND 16.3 Phase 8 V1 — Pydantic models for stables."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SetActiveMountPayload(BaseModel):
    """Payload for `POST /api/stables/set-active`.

    `mount_slug=None` (or omitted) means "deselect current active mount"
    (the guild walks on foot narratively). Otherwise the slug must belong
    to a mount already owned by the guild.
    """
    mount_slug: Optional[str] = None


class AdminGrantMountPayload(BaseModel):
    guild_id: str
    mount_slug: str
