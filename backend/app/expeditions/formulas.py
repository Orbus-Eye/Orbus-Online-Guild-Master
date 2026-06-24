"""Pure expedition math — no I/O, no Mongo, fully unit-testable.

These functions are the single source of truth for the team-power /
success-chance / equipment-delta calculations that the routes in
`server.py` consume.
"""
from typing import Iterable

from app.shared.constants import (
    SUCCESS_CHANCE_MIN,
    SUCCESS_CHANCE_MAX,
)


def adventurer_base_power(adv: dict) -> int:
    """Base power of an adventurer (no equipment, no composition bonus)."""
    return (
        int(adv["strength"])
        + int(adv["agility"])
        + int(adv["intellect"])
        + int(adv["endurance"])
        + int(adv["faith"])
        + int(adv.get("level", 1)) * 2
    )


def item_equip_power(item: dict) -> int:
    """Equipment power contribution of a single equipped item."""
    return (
        int(item.get("strength_bonus", 0))
        + int(item.get("agility_bonus", 0))
        + int(item.get("intellect_bonus", 0))
        + int(item.get("endurance_bonus", 0))
        + int(item.get("faith_bonus", 0))
        + int(item.get("power_score", 0))
    )


def compute_team_power(members: Iterable[dict]) -> int:
    """Team power = sum(per-member contribution) + role/composition bonuses.

    Per-member contribution is `total_power_snapshot` when present (Phase 6+),
    otherwise the legacy base formula. Role bonuses: +5 for any Tank, +5 for
    any Healer, +5 for any DPS, +10 if all three roles are present.
    """
    def get(a, key):
        return a.get(key, a.get(key + "_snapshot", 0))

    base = 0
    roles = set()
    for a in members:
        if a.get("total_power_snapshot") is not None:
            base += int(a["total_power_snapshot"])
        else:
            base += (
                int(get(a, "strength"))
                + int(get(a, "agility"))
                + int(get(a, "intellect"))
                + int(get(a, "endurance"))
                + int(get(a, "faith"))
                + int(get(a, "level") or 1) * 2
            )
        role = a.get("class_role") or a.get("role_snapshot")
        if role:
            roles.add(role)
    if "Tank" in roles:
        base += 5
    if "Healer" in roles:
        base += 5
    if "DPS" in roles:
        base += 5
    if {"Tank", "Healer", "DPS"}.issubset(roles):
        base += 10
    return base


def compute_success_chance(team_power: int, recommended_power: int) -> int:
    """Success chance % clamped to [SUCCESS_CHANCE_MIN, SUCCESS_CHANCE_MAX]."""
    raw = 50 + (team_power - recommended_power)
    if raw < SUCCESS_CHANCE_MIN:
        return SUCCESS_CHANCE_MIN
    if raw > SUCCESS_CHANCE_MAX:
        return SUCCESS_CHANCE_MAX
    return raw


def build_equipment_delta(
    members_for_power: list[dict],
    dungeon: dict,
    final_team_power: int,
    success_chance_with_eq: int,
) -> dict:
    """Return the 5 Phase-7 delta fields + narrative line.

    The function expects each member dict to carry
    `total_power_snapshot` and `equipment_power_snapshot` (computed by the
    expedition starter).
    """
    equipment_power_bonus = sum(
        int(m.get("equipment_power_snapshot", 0)) for m in members_for_power
    )
    members_base_only = [
        {
            **m,
            "total_power_snapshot": int(m["total_power_snapshot"])
            - int(m.get("equipment_power_snapshot", 0)),
        }
        for m in members_for_power
    ]
    base_team_power = compute_team_power(members_base_only)
    success_chance_without_eq = compute_success_chance(
        base_team_power, dungeon["recommended_power"]
    )

    if equipment_power_bonus == 0:
        narrative = "No equipment was used on this run."
    elif success_chance_without_eq == success_chance_with_eq:
        narrative = (
            f"Equipment contributed +{equipment_power_bonus} team power. "
            f"Success chance was already at maximum ({success_chance_with_eq}%)."
        )
    else:
        narrative = (
            f"Equipment contributed +{equipment_power_bonus} team power, "
            f"improving success chance from {success_chance_without_eq}% "
            f"to {success_chance_with_eq}%."
        )
    return {
        "base_team_power": base_team_power,
        "equipment_power_bonus": equipment_power_bonus,
        "final_team_power": final_team_power,
        "success_chance_without_equipment": success_chance_without_eq,
        "success_chance_with_equipment": success_chance_with_eq,
        "equipment_delta_text": narrative,
    }
