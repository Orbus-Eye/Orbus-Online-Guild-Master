"""Phase 17.5 — Onboarding service (starter roster).

Generates the initial roster of adventurers for a new guild so the player can
immediately dispatch team-size-5 expeditions. Idempotent and backfill-safe.
"""
from .services import ensure_starter_roster

__all__ = ["ensure_starter_roster"]
