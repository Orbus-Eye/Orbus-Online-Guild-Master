"""Phase 14.3-c — schema for the expedition preview endpoint."""
from typing import List

from pydantic import BaseModel, Field


class ExpeditionPreviewIn(BaseModel):
    dungeon_id: str = Field(..., min_length=1)
    adventurer_ids: List[str] = Field(..., min_length=1, max_length=10)


__all__ = ["ExpeditionPreviewIn"]
