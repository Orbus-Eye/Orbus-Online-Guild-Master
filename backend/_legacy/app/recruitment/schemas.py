"""Pydantic schemas for the Recruitment routes.

ROUND 11.3 TASK C adds `FreezeIn`, `UnfreezeIn`, `RecruitFrozenIn` for the
Recruit Freeze Bench endpoints. Field lengths mirror the UUID-shaped ids
used elsewhere in the codebase.
"""
from pydantic import BaseModel, Field


class RecruitIn(BaseModel):
    candidate_id: str = Field(min_length=8, max_length=64)


class FreezeIn(BaseModel):
    """POST /api/recruitment/freeze body — move a pool candidate to bench."""
    candidate_id: str = Field(min_length=8, max_length=64)


class UnfreezeIn(BaseModel):
    """POST /api/recruitment/unfreeze body — drop a bench slot."""
    frozen_id: str = Field(min_length=8, max_length=64)


class RecruitFrozenIn(BaseModel):
    """POST /api/recruitment/recruit-frozen body — hire from bench."""
    frozen_id: str = Field(min_length=8, max_length=64)


__all__ = ["RecruitIn", "FreezeIn", "UnfreezeIn", "RecruitFrozenIn"]
