"""Pure audit for item-driven Class Hall build reachability."""

from __future__ import annotations

from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import CLASS_MECHANICS, resolve_class_mechanic


def audit_class_hall_build_reachability(items: list[dict] | tuple[dict, ...]) -> dict:
    items_by_hall: dict[str, list[dict]] = {}
    for item in items:
        source = str(item.get("source") or "")
        if not source.startswith("class_hall:"):
            continue
        items_by_hall.setdefault(source.split(":", 1)[1], []).append(item)

    paths = []
    for profile in CLASS_HALLS.values():
        mechanic = CLASS_MECHANICS[profile.canonical_class_slug]
        hall_items = items_by_hall.get(profile.hall_id, [])
        for build in mechanic.builds:
            activating_items = []
            declared_items = []
            invalid_declared_items = []
            for item in hall_items:
                if item.get("build_path_id") == build.build_id:
                    declared_items.append(item.get("slug"))
                if not item.get("slot_type"):
                    continue
                resolved = resolve_class_mechanic(
                    adventurer={
                        "canonical_class_slug": profile.canonical_class_slug,
                    },
                    equipment_items=[item],
                )
                active_build = resolved.get("active_build") or {}
                activates = (
                    active_build.get("resonance_active") is True
                    and active_build.get("build_id") == build.build_id
                )
                if activates:
                    activating_items.append(item.get("slug"))
                if (
                    item.get("build_path_id") == build.build_id
                    and not activates
                ):
                    invalid_declared_items.append(item.get("slug"))
            paths.append(
                {
                    "wave": mechanic.wave,
                    "hall_id": profile.hall_id,
                    "class_slug": profile.canonical_class_slug,
                    "class_name_it": profile.class_name_it,
                    "build_id": build.build_id,
                    "build_name_it": build.name_it,
                    "reachable": bool(activating_items),
                    "activating_item_slugs": sorted(
                        slug for slug in activating_items if slug
                    ),
                    "declared_item_slugs": sorted(
                        slug for slug in declared_items if slug
                    ),
                    "invalid_declared_item_slugs": sorted(
                        slug for slug in invalid_declared_items if slug
                    ),
                    "has_exactly_one_declared_item": len(declared_items) == 1,
                }
            )

    reachable_paths = sum(row["reachable"] for row in paths)
    exact_declared_paths = sum(
        row["has_exactly_one_declared_item"] for row in paths
    )
    invalid_declared_items = sum(
        len(row["invalid_declared_item_slugs"]) for row in paths
    )
    return {
        "expected_class_count": len(CLASS_MECHANICS),
        "expected_build_count": sum(
            len(mechanic.builds)
            for mechanic in CLASS_MECHANICS.values()
        ),
        "reachable_build_count": reachable_paths,
        "exact_declared_build_count": exact_declared_paths,
        "invalid_declared_item_count": invalid_declared_items,
        "all_builds_reachable": (
            reachable_paths == len(paths)
            and exact_declared_paths == len(paths)
            and invalid_declared_items == 0
        ),
        "missing_builds": [
            {
                "class_slug": row["class_slug"],
                "build_id": row["build_id"],
            }
            for row in paths
            if not row["reachable"]
        ],
        "paths": paths,
    }


def require_all_class_hall_builds_reachable(
    items: list[dict] | tuple[dict, ...],
) -> dict:
    audit = audit_class_hall_build_reachability(items)
    if not audit["all_builds_reachable"]:
        raise RuntimeError(
            "canonical Hall items must expose exactly one reachable item "
            f"for every build: reachable={audit['reachable_build_count']}/"
            f"{audit['expected_build_count']}, "
            f"declared={audit['exact_declared_build_count']}/"
            f"{audit['expected_build_count']}, "
            f"invalid={audit['invalid_declared_item_count']}"
        )
    return audit


__all__ = [
    "audit_class_hall_build_reachability",
    "require_all_class_hall_builds_reachable",
]
