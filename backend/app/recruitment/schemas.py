"""Recruitment domain Pydantic schemas (Phase 5.5c.3)."""
from pydantic import BaseModel, Field


class RecruitIn(BaseModel):
    candidate_id: str = Field(min_length=8, max_length=64)


__all__ = ["RecruitIn"]
