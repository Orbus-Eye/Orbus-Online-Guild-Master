"""Admin domain services (Phase 5.5f).

Pure CRUD on the four seed collections (classes, traits, dungeons, items)
plus the monetization invariant enforcer and a couple of utility helpers.
All ops accept the Motor `db` handle so they are unit-testable.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


VALID_ROLES = ("Tank", "DPS", "Healer")
VALID_AFFECTED_STAT = ("strength", "agility", "intellect", "endurance", "faith", "xp_gain")
VALID_ITEM_TYPES = ("weapon", "armor", "accessory", "consumable")
VALID_RARITIES = ("Common", "Uncommon", "Rare", "Epic")


def validate_item_monetization(item: dict) -> None:
    """Reject inconsistent flags: real-money sale only allowed for pure cosmetics."""
    if item.get("can_be_sold_for_real_money"):
        if (
            not item.get("is_cosmetic", False)
            or item.get("affects_combat", False)
            or item.get("affects_economy", False)
            or item.get("affects_ranking", False)
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid item: can_be_sold_for_real_money requires "
                    "is_cosmetic=true AND affects_combat=false AND "
                    "affects_economy=false AND affects_ranking=false"
                ),
            )


def _slug_ok(s: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s or ""))


def _strip_db_fields(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "_id"}


def _build_item_doc(payload: dict, existing: Optional[dict] = None) -> dict:
    base = dict(existing) if existing else {
        "id": str(uuid.uuid4()),
        "level_required": 1,
        "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 0,
        "endurance_bonus": 0, "faith_bonus": 0,
        "is_tradeable": True, "is_cosmetic": False,
        "affects_combat": True, "affects_economy": False, "affects_ranking": False,
        "can_be_sold_for_gold": True, "can_be_sold_for_real_money": False,
        "is_active": True,
    }
    for k in ("name", "slug", "description", "item_type", "rarity"):
        if k in payload:
            base[k] = str(payload[k]).strip()
    for k in ("level_required", "power_score", "strength_bonus", "agility_bonus",
              "intellect_bonus", "endurance_bonus", "faith_bonus"):
        if k in payload:
            base[k] = int(payload[k])
    for k in ("is_tradeable", "is_cosmetic", "affects_combat", "affects_economy",
              "affects_ranking", "can_be_sold_for_gold",
              "can_be_sold_for_real_money", "is_active"):
        if k in payload:
            base[k] = bool(payload[k])
    return base


__all__ = [
    "VALID_ROLES",
    "VALID_AFFECTED_STAT",
    "VALID_ITEM_TYPES",
    "VALID_RARITIES",
    "validate_item_monetization",
    "_slug_ok",
    "_strip_db_fields",
    "_build_item_doc",
    "utc_now",
]
