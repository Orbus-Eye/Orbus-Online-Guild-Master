"""Server-owned T8 tester-release readiness gate."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Mapping

from app.items.catalog_contract import (
    ITEM_CATALOG_TARGET_TOTAL,
    ITEM_CATALOG_VERSION_T6,
    RARITY_CATALOG_TARGETS,
    ULTRA_RARE_RANDOM_DROP_SLUG,
)
from app.items.final_catalog import FINAL_ITEM_CATALOG
from app.shared.constants import ADVENTURER_MAX_LEVEL


T8_CHECKLIST_KEYS = (
    "desktop_navigation",
    "mobile_navigation",
    "classless_hall_journey",
    "item_lore_and_sources",
    "dungeon_and_raid_reports",
    "reset_repeatability",
)


def audit_t8_runtime_catalog(rows: list[dict]) -> dict:
    active = [
        row for row in rows
        if row.get("catalog_version") == ITEM_CATALOG_VERSION_T6
        and row.get("is_active") is True
        and row.get("is_test") is not True
    ]
    expected_identity = {
        (item["slug"], item["blueprint_id"])
        for item in FINAL_ITEM_CATALOG
    }
    actual_identity = {
        (item.get("slug"), item.get("blueprint_id"))
        for item in active
    }
    rarity_counts = Counter(item.get("rarity") for item in active)
    class_counts = Counter(
        item.get("canonical_class_slug")
        for item in active
        if item.get("catalog_scope") == "class"
    )
    universal_count = sum(
        item.get("catalog_scope") == "universal" for item in active
    )
    missing_required = []
    economy_violations = []
    endgame_violations = []
    random_unique_slugs = []
    for item in active:
        slug = str(item.get("slug") or "?")
        required = (
            "display_name_it",
            "lore_source",
            "flavor_text_it",
            "gameplay_effect_it",
            "slot_type",
            "source",
            "source_policy_id",
            "item_binding_policy",
            "acquisition_mode",
            "acquisition_sources",
        )
        if any(not item.get(field) for field in required):
            missing_required.append(slug)
        if item.get("can_be_sold_for_real_money") is not False:
            economy_violations.append(slug)
        if (
            item.get("rarity") in {"Legendary", "Unique"}
            and int(item.get("required_adventurer_level", 0) or 0)
            != ADVENTURER_MAX_LEVEL
        ):
            endgame_violations.append(slug)
        if item.get("acquisition_mode") == "ultra_rare_random_drop":
            random_unique_slugs.append(slug)

    catalog_gate = {
        "total_exact": len(active) == ITEM_CATALOG_TARGET_TOTAL,
        "identity_exact": actual_identity == expected_identity,
        "rarities_exact": dict(rarity_counts) == RARITY_CATALOG_TARGETS,
        "classes_exact": (
            len(class_counts) == 27
            and set(class_counts.values()) == {50}
        ),
        "universal_exact": universal_count == 150,
        "required_fields_complete": not missing_required,
    }
    economy_gate = {
        "no_real_money_items": not economy_violations,
        "endgame_level_80": not endgame_violations,
        "only_company_ring_is_random_unique": (
            random_unique_slugs == [ULTRA_RARE_RANDOM_DROP_SLUG]
        ),
    }
    return {
        "catalog_version": ITEM_CATALOG_VERSION_T6,
        "ready": all(catalog_gate.values()) and all(economy_gate.values()),
        "catalog_gate": catalog_gate,
        "economy_gate": economy_gate,
        "total": len(active),
        "rarity_counts": dict(rarity_counts),
        "class_counts": dict(sorted(class_counts.items())),
        "universal_count": universal_count,
        "diagnostics": {
            "missing_required_slugs": missing_required[:25],
            "economy_violation_slugs": economy_violations[:25],
            "endgame_violation_slugs": endgame_violations[:25],
            "random_unique_slugs": random_unique_slugs,
        },
    }


def normalized_t8_checklist(source: Mapping | None) -> dict:
    source = source or {}
    checks = {
        key: bool(source.get(key))
        for key in T8_CHECKLIST_KEYS
    }
    return {
        "checks": checks,
        "completed": all(checks.values()),
        "completed_count": sum(checks.values()),
        "required_count": len(T8_CHECKLIST_KEYS),
        "notes": str(source.get("notes") or ""),
        "recorded_at": source.get("recorded_at"),
        "recorded_by_user_id": source.get("recorded_by_user_id"),
    }


async def build_t8_release_readiness(
    db,
    *,
    user: dict,
    guild: dict | None,
    vertical_slice: dict,
) -> dict:
    rows = await db.items.find(
        {"catalog_version": ITEM_CATALOG_VERSION_T6},
        {"_id": 0},
    ).to_list(ITEM_CATALOG_TARGET_TOTAL + 100)
    catalog = audit_t8_runtime_catalog(rows)
    checklist_row = await db.tester_release_checklists.find_one(
        {"target_user_id": user["id"]},
        {"_id": 0},
        sort=[("recorded_at", -1)],
    )
    checklist = normalized_t8_checklist(checklist_row)
    automated_gate = {
        "t5_vertical_slice": bool(
            vertical_slice.get("t5_completion_ready")
        ),
        "t6_runtime_catalog": bool(catalog["ready"]),
        "reset_available": guild is not None,
    }
    automated_ready = all(automated_gate.values())
    return {
        "release_contract": "t8.tester-release.v1",
        "target_user": {
            "id": user.get("id"),
            "email": user.get("email"),
        },
        "guild_id": guild.get("id") if guild else None,
        "automated_ready": automated_ready,
        "t8_release_ready": automated_ready and checklist["completed"],
        "automated_gate": automated_gate,
        "catalog": catalog,
        "human_checklist": checklist,
        "class_sets_included": False,
        "automatic_tuning_allowed": False,
        "shared_environment_write_authorized": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = [
    "T8_CHECKLIST_KEYS",
    "audit_t8_runtime_catalog",
    "build_t8_release_readiness",
    "normalized_t8_checklist",
]
