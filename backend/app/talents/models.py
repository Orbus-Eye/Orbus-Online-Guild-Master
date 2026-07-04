"""ROUND 18.2 PILOT — Talent Tree Pydantic v2 models + validators.

Schema/engine only. Nessun talento reale, nessun bonus reale, nessun
effect_id. Solo placeholder deterministici per 9 classi live 1:1 sicure.

Structure PILOT:
  27 canonical classes × 3 branches × 5 tiers × 4 slots = 60 slot/classe
  9 classi PILOT × 60 = 540 doc placeholder totali

Validators enforced:
- class_slug MUST be in PILOT_CLASS_SLUGS (9 classi live 1:1)
- branch_id ∈ {1, 2, 3}
- tier ∈ {1, 2, 3, 4, 5}
- slot_index ∈ {1, 2, 3, 4}
- spent_points ≤ 30
- allocations length ≤ 30
- allocation prereq: tier N richiede ≥ (N-1) punti nel ramo
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ─── PILOT class slugs (Ondata 1 — 9 classi live 1:1 sicure) ──────────
PILOT_CLASS_SLUGS: set[str] = {
    "warrior",      # → Guerriero
    "rogue",        # → Ladro
    "mage",         # → Mago
    "paladin",      # → Paladino
    "druid",        # → Druido
    "necromancer",  # → Negromante
    "monk",         # → Monaco
    "bard",         # → Bardo
    "alchemist",    # → Alchimista
}

MAX_POINTS_PER_ADVENTURER: int = 30
BRANCHES_PER_CLASS: int = 3
TIERS_PER_BRANCH: int = 5
SLOTS_PER_TIER: int = 4
SLOTS_PER_CLASS: int = BRANCHES_PER_CLASS * TIERS_PER_BRANCH * SLOTS_PER_TIER  # 60


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_placeholder_id(class_slug: str, branch_id: int, tier: int, slot_index: int) -> str:
    """Deterministic ID for a talent slot placeholder."""
    return f"{class_slug}.branch{branch_id}.tier{tier}.slot{slot_index}"


class TalentTreeDefinition(BaseModel):
    """A single talent slot placeholder in the tree (schema-only, no effect)."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_slug: str
    branch_id: int = Field(ge=1, le=BRANCHES_PER_CLASS)
    tier: int = Field(ge=1, le=TIERS_PER_BRANCH)
    slot_index: int = Field(ge=1, le=SLOTS_PER_TIER)
    placeholder_id: str
    # requirements is a placeholder list for future prerequisites.
    # In R18.2 PILOT it stores only the implicit tier-N-requires-N-1 rule
    # (empty list means: no explicit slot prereq, just tier gate).
    requirements: List[str] = Field(default_factory=list)
    # Feature-flag / lifecycle markers
    is_placeholder: bool = True
    round_seeded: str = "R18.2"
    created_at: str = Field(default_factory=_utc_now_iso)

    @field_validator("class_slug")
    @classmethod
    def _class_must_be_pilot(cls, v: str) -> str:
        if v not in PILOT_CLASS_SLUGS:
            raise ValueError(
                f"class_slug '{v}' not in R18.2 PILOT set "
                f"({sorted(PILOT_CLASS_SLUGS)}). "
                "Non-pilot classes will be seeded in later ondate."
            )
        return v

    @model_validator(mode="after")
    def _placeholder_id_matches(self) -> "TalentTreeDefinition":
        expected = build_placeholder_id(
            self.class_slug, self.branch_id, self.tier, self.slot_index
        )
        if self.placeholder_id != expected:
            raise ValueError(
                f"placeholder_id '{self.placeholder_id}' mismatch, "
                f"expected '{expected}'"
            )
        return self


class TalentAllocation(BaseModel):
    """A single point spent on a slot by an adventurer."""
    model_config = ConfigDict(extra="forbid")

    class_slug: str
    branch_id: int = Field(ge=1, le=BRANCHES_PER_CLASS)
    tier: int = Field(ge=1, le=TIERS_PER_BRANCH)
    slot_index: int = Field(ge=1, le=SLOTS_PER_TIER)
    allocated_at: str = Field(default_factory=_utc_now_iso)

    @field_validator("class_slug")
    @classmethod
    def _class_must_be_pilot(cls, v: str) -> str:
        if v not in PILOT_CLASS_SLUGS:
            raise ValueError(
                f"class_slug '{v}' not in R18.2 PILOT set."
            )
        return v


class AdventurerTalentProgress(BaseModel):
    """Adventurer's talent progress state."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    adventurer_id: str
    spent_points: int = Field(default=0, ge=0, le=MAX_POINTS_PER_ADVENTURER)
    max_points: int = Field(default=MAX_POINTS_PER_ADVENTURER)
    allocations: List[TalentAllocation] = Field(default_factory=list)
    last_reset_at: Optional[str] = None
    round_created: str = "R18.2"
    created_at: str = Field(default_factory=_utc_now_iso)
    updated_at: str = Field(default_factory=_utc_now_iso)

    @model_validator(mode="after")
    def _validate_points_and_allocations(self) -> "AdventurerTalentProgress":
        # Rule 1: spent_points must not exceed max_points (Pydantic Field ge/le
        # already enforces individual bounds; explicit cross-check for safety).
        if self.spent_points > self.max_points:
            raise ValueError(
                f"spent_points={self.spent_points} > "
                f"max_points={self.max_points}"
            )
        # Rule 2: allocations length ≤ max_points
        if len(self.allocations) > self.max_points:
            raise ValueError(
                f"allocations length {len(self.allocations)} > "
                f"max_points={self.max_points}"
            )
        # Rule 3: allocations count coherent with spent_points
        if len(self.allocations) != self.spent_points:
            raise ValueError(
                f"allocations count {len(self.allocations)} != "
                f"spent_points {self.spent_points}"
            )
        # Rule 4: tier N gate — allocation to tier N requires ≥ (N-1)
        # allocations already in same branch. Skipped for tier=1.
        # Group allocations by (class_slug, branch_id)
        branch_counts_pre: dict[tuple[str, int, int], int] = {}
        # count how many allocations in same class+branch have tier < current
        # Simplified check: for each allocation, ensure at least (tier - 1)
        # prior allocations in the same class+branch with tier < current tier.
        for i, alloc in enumerate(self.allocations):
            same_branch_prior = [
                a for a in self.allocations[:i]
                if a.class_slug == alloc.class_slug
                and a.branch_id == alloc.branch_id
                and a.tier < alloc.tier
            ]
            required_prior = alloc.tier - 1
            if len(same_branch_prior) < required_prior:
                raise ValueError(
                    f"tier {alloc.tier} allocation requires ≥ "
                    f"{required_prior} prior points in same branch "
                    f"({alloc.class_slug} branch{alloc.branch_id}); "
                    f"found only {len(same_branch_prior)}"
                )
        return self


__all__ = [
    "PILOT_CLASS_SLUGS",
    "MAX_POINTS_PER_ADVENTURER",
    "BRANCHES_PER_CLASS",
    "TIERS_PER_BRANCH",
    "SLOTS_PER_TIER",
    "SLOTS_PER_CLASS",
    "build_placeholder_id",
    "TalentTreeDefinition",
    "TalentAllocation",
    "AdventurerTalentProgress",
]
