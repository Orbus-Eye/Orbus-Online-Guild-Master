"""ROUND 6B.1 — Pydantic schemas for /api/territory."""
from pydantic import BaseModel, Field


class PurchaseIn(BaseModel):
    structure_slug: str = Field(..., min_length=1, max_length=64)


class UpgradeIn(BaseModel):
    structure_slug: str = Field(..., min_length=1, max_length=64)
