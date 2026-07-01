"""Equipment domain Pydantic schemas (Phase 5.5d)."""
from pydantic import BaseModel, Field


class EquipIn(BaseModel):
    item_id: str = Field(min_length=8, max_length=64)
    slot: str = Field(min_length=1, max_length=32)


class UnequipIn(BaseModel):
    slot: str = Field(min_length=1, max_length=32)


__all__ = ["EquipIn", "UnequipIn"]
