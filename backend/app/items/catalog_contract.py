"""Canonical item-catalog contract for the item-first roadmap.

This module deliberately separates three concepts that legacy code mixed:

* catalog presence: how many distinct blueprints of each rarity exist;
* acquisition policy: which sources may award a blueprint;
* drop chance: a source-specific probability, never derived from presence.

It is read-only with respect to persistence. Seed/import paths can use
``validate_item_blueprint`` before writing; the public audit can inspect the
current catalog without mutating it.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping

from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.rarity import CANONICAL_RARITIES, canonicalize_rarity


ITEM_CATALOG_TARGET_TOTAL = 1500
ITEM_CATALOG_VERSION_T6 = "t6.final.v1"
ITEM_CLASS_COUNT = 27
ITEMS_PER_CLASS_TARGET = 50
CLASS_BOUND_ITEM_TARGET = ITEM_CLASS_COUNT * ITEMS_PER_CLASS_TARGET
UNIVERSAL_ITEM_TARGET = ITEM_CATALOG_TARGET_TOTAL - CLASS_BOUND_ITEM_TARGET

RARITY_CATALOG_TARGETS: dict[str, int] = {
    "Common": 525,
    "Uncommon": 375,
    "Rare": 300,
    "Epic": 225,
    "Legendary": 60,
    "Unique": 15,
}
RARITY_CATALOG_PRESENCE_PERCENT: dict[str, int] = {
    "Common": 35,
    "Uncommon": 25,
    "Rare": 20,
    "Epic": 15,
    "Legendary": 4,
    "Unique": 1,
}
RARITY_DEFAULT_REQUIRED_LEVEL: dict[str, int] = {
    "Common": 1,
    "Uncommon": 3,
    "Rare": 5,
    "Epic": 8,
    "Legendary": ADVENTURER_MAX_LEVEL,
    "Unique": ADVENTURER_MAX_LEVEL,
}

ENDGAME_RARITIES = frozenset({"Legendary", "Unique"})
ORDINARY_RANDOM_DROP_RARITIES = frozenset(
    {"Common", "Uncommon", "Rare", "Epic"}
)
ULTRA_RARE_RANDOM_DROP_SLUG = "l_unico_anello_della_compagnia"


def _assert_contract_is_exact() -> None:
    if tuple(RARITY_CATALOG_TARGETS) != CANONICAL_RARITIES:
        raise RuntimeError("item rarity contract order differs from canonical rarity")
    if sum(RARITY_CATALOG_TARGETS.values()) != ITEM_CATALOG_TARGET_TOTAL:
        raise RuntimeError("item rarity targets do not sum to catalog total")
    if sum(RARITY_CATALOG_PRESENCE_PERCENT.values()) != 100:
        raise RuntimeError("item rarity presence does not sum to 100%")
    for rarity, target in RARITY_CATALOG_TARGETS.items():
        expected = ITEM_CATALOG_TARGET_TOTAL * (
            RARITY_CATALOG_PRESENCE_PERCENT[rarity] / 100
        )
        if target != int(expected):
            raise RuntimeError(f"{rarity} target differs from presence percentage")


_assert_contract_is_exact()


def is_endgame_rarity(value: object) -> bool:
    return canonicalize_rarity(value) in ENDGAME_RARITIES


def ordinary_random_drop_allowed(value: object) -> bool:
    """Return whether a rarity may appear in ordinary random loot tables."""
    return canonicalize_rarity(value) in ORDINARY_RANDOM_DROP_RARITIES


def ultra_rare_random_drop_allowed(item: Mapping[str, object]) -> bool:
    """Only the canonical Company ring may use the ultra-rare random roll."""
    return (
        str(item.get("slug") or "").strip().casefold()
        == ULTRA_RARE_RANDOM_DROP_SLUG
        and canonicalize_rarity(item.get("rarity")) == "Unique"
    )


def effective_catalog_required_level(item: Mapping[str, object]) -> int:
    """Resolve the catalog gate, hard-locking endgame rarities at max level."""
    # `Signature` is a legacy progression marker, not one of the six catalog
    # rarity buckets. Preserve its historical gate while seeds migrate.
    if str(item.get("rarity") or "").strip().casefold() == "signature":
        return 5
    rarity = canonicalize_rarity(item.get("rarity")) or "Common"
    if rarity in ENDGAME_RARITIES:
        return ADVENTURER_MAX_LEVEL
    explicit = item.get("required_adventurer_level")
    if isinstance(explicit, int) and explicit >= 1:
        return explicit
    legacy = item.get("level_required")
    if isinstance(legacy, int) and legacy > 1:
        return legacy
    return RARITY_DEFAULT_REQUIRED_LEVEL.get(rarity, 1)


def validate_item_blueprint(
    item: Mapping[str, object],
    *,
    current_rarity_counts: Mapping[str, int] | None = None,
) -> list[str]:
    """Return stable validation errors for a prospective catalog blueprint."""
    errors: list[str] = []
    rarity = canonicalize_rarity(item.get("rarity"))
    if rarity is None:
        errors.append("item.rarity.invalid")
        return errors

    if current_rarity_counts is not None:
        current = int(current_rarity_counts.get(rarity, 0) or 0)
        if current >= RARITY_CATALOG_TARGETS[rarity]:
            errors.append("item.catalog.rarity_quota_exhausted")

    declared_drop = str(item.get("acquisition_mode") or "").strip().casefold()
    if declared_drop in {"ordinary_random_drop", "random_drop"}:
        if not ordinary_random_drop_allowed(rarity):
            errors.append("item.acquisition.ordinary_drop_forbidden")
    if declared_drop == "ultra_rare_random_drop":
        if not ultra_rare_random_drop_allowed(item):
            errors.append("item.acquisition.ultra_rare_drop_reserved")

    if rarity in ENDGAME_RARITIES:
        declared_level = item.get(
            "required_adventurer_level", item.get("level_required")
        )
        if declared_level not in (None, ADVENTURER_MAX_LEVEL):
            errors.append("item.level.endgame_requires_max_level")
    return errors


async def validate_catalog_write(
    db,
    item: Mapping[str, object],
    *,
    exclude_item_id: str | None = None,
) -> list[str]:
    """Validate an active blueprint against live catalog rarity quotas.

    Existing rows can be excluded during an update so keeping the same rarity
    does not consume a second slot. Inactive/test blueprints do not consume
    the public catalog quota.
    """
    if item.get("is_active", True) is False or item.get("is_test") is True:
        return validate_item_blueprint(item)
    query: dict = {"is_active": True, "is_test": {"$ne": True}}
    if exclude_item_id:
        query["id"] = {"$ne": exclude_item_id}
    rows = await db.items.find(
        query,
        {"_id": 0, "rarity": 1},
    ).to_list(2000)
    counts: Counter[str] = Counter()
    for row in rows:
        rarity = canonicalize_rarity(row.get("rarity"))
        if rarity:
            counts[rarity] += 1
    return validate_item_blueprint(item, current_rarity_counts=counts)


def audit_catalog_items(items: Iterable[Mapping[str, object]]) -> dict:
    """Build a deterministic, read-only quota audit for active blueprints."""
    counts: Counter[str] = Counter()
    invalid_rarity = 0
    total = 0
    for item in items:
        if item.get("is_active", True) is False or item.get("is_test") is True:
            continue
        total += 1
        rarity = canonicalize_rarity(item.get("rarity"))
        if rarity is None:
            invalid_rarity += 1
        else:
            counts[rarity] += 1

    by_rarity = {}
    has_overflow = False
    for rarity in CANONICAL_RARITIES:
        current = counts.get(rarity, 0)
        target = RARITY_CATALOG_TARGETS[rarity]
        overflow = max(current - target, 0)
        has_overflow = has_overflow or overflow > 0
        by_rarity[rarity] = {
            "current": current,
            "target": target,
            "remaining": max(target - current, 0),
            "overflow": overflow,
            "presence_percent": RARITY_CATALOG_PRESENCE_PERCENT[rarity],
        }

    return {
        "current_total": total,
        "target_total": ITEM_CATALOG_TARGET_TOTAL,
        "remaining_total": max(ITEM_CATALOG_TARGET_TOTAL - total, 0),
        "overflow_total": max(total - ITEM_CATALOG_TARGET_TOTAL, 0),
        "invalid_rarity_count": invalid_rarity,
        "has_quota_overflow": has_overflow,
        "by_rarity": by_rarity,
    }


def public_catalog_contract() -> dict:
    """Return the non-spoiler, player-safe catalog contract."""
    return {
        "target_total": ITEM_CATALOG_TARGET_TOTAL,
        "class_count": ITEM_CLASS_COUNT,
        "items_per_class_target": ITEMS_PER_CLASS_TARGET,
        "class_bound_target": CLASS_BOUND_ITEM_TARGET,
        "universal_target": UNIVERSAL_ITEM_TARGET,
        "adventurer_max_level": ADVENTURER_MAX_LEVEL,
        "rarities": [
            {
                "name": rarity,
                "target": RARITY_CATALOG_TARGETS[rarity],
                "presence_percent": RARITY_CATALOG_PRESENCE_PERCENT[rarity],
                "default_required_level": RARITY_DEFAULT_REQUIRED_LEVEL[rarity],
                "ordinary_random_drop_allowed": ordinary_random_drop_allowed(
                    rarity
                ),
            }
            for rarity in CANONICAL_RARITIES
        ],
        "presence_is_drop_chance": False,
    }


__all__ = [
    "CLASS_BOUND_ITEM_TARGET",
    "ENDGAME_RARITIES",
    "ITEM_CATALOG_TARGET_TOTAL",
    "ITEM_CATALOG_VERSION_T6",
    "ITEM_CLASS_COUNT",
    "ITEMS_PER_CLASS_TARGET",
    "ORDINARY_RANDOM_DROP_RARITIES",
    "RARITY_CATALOG_PRESENCE_PERCENT",
    "RARITY_CATALOG_TARGETS",
    "RARITY_DEFAULT_REQUIRED_LEVEL",
    "ULTRA_RARE_RANDOM_DROP_SLUG",
    "UNIVERSAL_ITEM_TARGET",
    "audit_catalog_items",
    "effective_catalog_required_level",
    "is_endgame_rarity",
    "ordinary_random_drop_allowed",
    "public_catalog_contract",
    "ultra_rare_random_drop_allowed",
    "validate_catalog_write",
    "validate_item_blueprint",
]
