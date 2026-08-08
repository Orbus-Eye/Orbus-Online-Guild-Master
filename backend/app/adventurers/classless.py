"""Shared guards for the explicit ``recruit_unassigned`` lifecycle state."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException


def is_explicit_classless_recruit(adventurer: dict) -> bool:
    """Return True only for new classless writes, never legacy null conflicts."""
    return (
        adventurer.get("recruit_status") == "recruit_unassigned"
        and not adventurer.get("class_slug")
        and not adventurer.get("canonical_class_slug")
        and not adventurer.get("class_proficiency")
        and not adventurer.get("class_hall_id")
    )


def require_class_hall_assignment(
    adventurers: Iterable[dict],
    *,
    source: str,
) -> None:
    blocked = [
        {
            "adventurer_id": adventurer.get("id"),
            "name": adventurer.get("name"),
        }
        for adventurer in adventurers
        if is_explicit_classless_recruit(adventurer)
    ]
    if not blocked:
        return
    raise HTTPException(
        status_code=423,
        detail={
            "code": "class_hall.selection_required",
            "source": source,
            "classless_adventurers": blocked,
            "count": len(blocked),
            "user_message": (
                "Una o più reclute non hanno ancora scelto una Sala di Classe. "
                "Completa prima il loro sentiero."
            ),
        },
    )


__all__ = [
    "is_explicit_classless_recruit",
    "require_class_hall_assignment",
]
