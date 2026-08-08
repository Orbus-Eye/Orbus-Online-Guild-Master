"""Phase 17.5 / Round 18.6 — onboarding service (starter roster).

Generates the initial roster of adventurers for a new guild so the player can
choose each adventurer's first Class Hall.  Every starter is classless;
activities unlock only after assignment.  Idempotent and backfill-safe.
"""
from .services import ensure_starter_roster

__all__ = ["ensure_starter_roster"]
