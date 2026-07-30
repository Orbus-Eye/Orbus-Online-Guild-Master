"""Canonical reward-source eligibility engine.

Catalog presence is never a drop chance. A source policy decides rarity,
level, binding, lockout, first-clear behaviour and duplicate handling.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Mapping

from app.items.catalog_contract import (
    ULTRA_RARE_RANDOM_DROP_SLUG,
    effective_catalog_required_level,
)
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.rarity import CANONICAL_RARITIES, canonicalize_rarity


SOURCE_POLICIES = {
    "class_hall_assignment": {
        "rarities": ("Common", "Uncommon"),
        "binding": "hard",
        "first_clear_only": True,
        "lockout": "assignment",
        "duplicate_policy": "deny",
    },
    "class_hall_item_track": {
        "rarities": ("Common", "Uncommon", "Rare", "Epic"),
        "binding": "hard",
        "first_clear_only": True,
        "lockout": "milestone",
        "duplicate_policy": "convert_fragment",
    },
    "ordinary_dungeon": {
        "rarities": ("Common", "Uncommon", "Rare", "Epic"),
        "binding": "soft",
        "first_clear_only": False,
        "lockout": "none",
        "duplicate_policy": "allow_stack_or_convert",
    },
    "raid_level40": {
        "rarities": ("Uncommon", "Rare"),
        "binding": "soft",
        "first_clear_only": False,
        "lockout": "raid_cooldown",
        "duplicate_policy": "convert_fragment",
    },
    "raid_level60": {
        "rarities": ("Rare", "Epic"),
        "binding": "soft",
        "first_clear_only": False,
        "lockout": "raid_cooldown",
        "duplicate_policy": "convert_fragment",
    },
    "raid_level70": {
        "rarities": ("Rare", "Epic"),
        "binding": "soft",
        "first_clear_only": False,
        "lockout": "raid_cooldown",
        "duplicate_policy": "convert_fragment",
    },
    "raid_level80_victory": {
        "rarities": ("Epic", "Legendary"),
        "binding": "hard",
        "first_clear_only": False,
        "lockout": "raid_cooldown",
        "duplicate_policy": "convert_fragment",
    },
    "crafting": {
        "rarities": CANONICAL_RARITIES[:-1],
        "binding": "soft",
        "first_clear_only": False,
        "lockout": "recipe_inputs",
        "duplicate_policy": "allow",
    },
    "mission_event_reputation": {
        "rarities": ("Common", "Uncommon", "Rare", "Epic"),
        "binding": "soft",
        "first_clear_only": False,
        "lockout": "source_defined",
        "duplicate_policy": "convert_fragment",
    },
    "company_ring_ultra_rare": {
        "rarities": ("Unique",),
        "binding": "hard",
        "first_clear_only": False,
        "lockout": "world_boss_secret_roll",
        "duplicate_policy": "global_unique_deny",
        # Decimal probability: 0.000001 = 0.0001% = one in one million.
        "private_drop_probability": 0.000001,
    },
    "unique_endgame_milestone": {
        "rarities": ("Unique",),
        "binding": "hard",
        "first_clear_only": True,
        "lockout": "server_owned_milestone",
        "duplicate_policy": "deny",
    },
}


def reward_grant_key(
    *,
    guild_id: str,
    source_policy_id: str,
    source_instance_id: str,
    item_slug: str,
) -> str:
    raw = "|".join((
        guild_id,
        source_policy_id,
        source_instance_id,
        item_slug,
    ))
    return sha256(raw.encode("utf-8")).hexdigest()


def evaluate_reward_eligibility(
    *,
    item: Mapping[str, object],
    source_policy_id: str,
    adventurer_level: int,
    first_clear: bool = False,
    already_owned: bool = False,
    global_unique_already_granted: bool = False,
) -> dict:
    policy = SOURCE_POLICIES.get(source_policy_id)
    reasons: list[str] = []
    rarity = canonicalize_rarity(item.get("rarity"))
    slug = str(item.get("slug") or "").strip().casefold()
    if policy is None:
        return {"eligible": False, "reasons": ["reward.source.unknown"]}
    if rarity not in policy["rarities"]:
        reasons.append("reward.rarity.not_allowed_by_source")
    required_level = effective_catalog_required_level(item)
    if int(adventurer_level) < required_level:
        reasons.append("reward.level.too_low")
    if policy["first_clear_only"] and not first_clear:
        reasons.append("reward.first_clear.required")
    if rarity == "Legendary" and int(adventurer_level) < ADVENTURER_MAX_LEVEL:
        reasons.append("reward.legendary.max_level_required")
    if rarity == "Unique":
        company_ring_source = (
            source_policy_id == "company_ring_ultra_rare"
            and slug == ULTRA_RARE_RANDOM_DROP_SLUG
        )
        milestone_source = (
            source_policy_id == "unique_endgame_milestone"
            and slug != ULTRA_RARE_RANDOM_DROP_SLUG
        )
        if not (company_ring_source or milestone_source):
            reasons.append("reward.unique.source_forbidden")
        if int(adventurer_level) < ADVENTURER_MAX_LEVEL:
            reasons.append("reward.unique.max_level_required")
    if global_unique_already_granted and rarity == "Unique":
        reasons.append("reward.unique.already_granted")
    duplicate_action = "grant"
    if already_owned:
        duplicate_action = policy["duplicate_policy"]
        if duplicate_action in {"deny", "global_unique_deny"}:
            reasons.append("reward.duplicate.denied")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "source_policy_id": source_policy_id,
        "binding_policy": policy["binding"],
        "lockout": policy["lockout"],
        "duplicate_action": duplicate_action,
        "required_level": required_level,
    }


__all__ = [
    "SOURCE_POLICIES",
    "evaluate_reward_eligibility",
    "reward_grant_key",
]
