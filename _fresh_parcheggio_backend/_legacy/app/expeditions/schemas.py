"""Expeditions request/response Pydantic schemas (Phase 5.5e).

Behaviour contract:
- `dungeon_id` is a UUID4 string (8-64 chars).
- `adventurer_ids` validated 1-10 raw; per-dungeon team-size enforcement
  happens in the service (`_dispatch_expedition`) so error messages can
  reference the dungeon's `required_team_size`.
"""
from pydantic import BaseModel, Field


class ExpeditionCreateIn(BaseModel):
    dungeon_id: str = Field(min_length=8, max_length=64)
    adventurer_ids: list[str] = Field(min_length=1, max_length=10)


# Backward-compat alias for the original server.py symbol used by some tests
ExpeditionStartIn = ExpeditionCreateIn


__all__ = ["ExpeditionCreateIn", "ExpeditionStartIn"]
