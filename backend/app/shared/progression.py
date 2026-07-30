"""Pure adventurer progression rules shared by runtime services and tests."""
from __future__ import annotations

from app.shared.constants import (
    ADVENTURER_MAX_LEVEL,
    ADVENTURER_XP_CURVE_EXPONENT,
    XP_THRESHOLD_PER_LEVEL,
)


def xp_required_for_next_level(level: int) -> int:
    """XP needed to advance once; max-level adventurers cannot advance."""
    current_level = max(1, int(level or 1))
    if current_level >= ADVENTURER_MAX_LEVEL:
        return 0
    return int(
        round(
            XP_THRESHOLD_PER_LEVEL
            * (current_level ** ADVENTURER_XP_CURVE_EXPONENT)
        )
    )


def cumulative_xp_required_for_level(level: int) -> int:
    """Total XP required to reach a level from level 1."""
    target = min(ADVENTURER_MAX_LEVEL, max(1, int(level or 1)))
    return sum(xp_required_for_next_level(current) for current in range(1, target))


def can_adventurer_level_up(level: int, experience: int) -> bool:
    """Return whether one more level may be consumed from residual XP."""
    current_level = max(1, int(level or 1))
    current_experience = max(0, int(experience or 0))
    return (
        current_level < ADVENTURER_MAX_LEVEL
        and current_experience >= xp_required_for_next_level(current_level)
    )


__all__ = [
    "can_adventurer_level_up",
    "cumulative_xp_required_for_level",
    "xp_required_for_next_level",
]
