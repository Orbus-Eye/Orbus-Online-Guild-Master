"""ROUND 11.3 TASK B — Item required-level gate.

Sibling of `expeditions.level_gate`. Centralised resolution of an item's
required adventurer level + a structured 423 raiser used by the equip
service (and any future "auto-equip" / "swap" / "preview equip" endpoint).

Why a dedicated module:
  * Same call-site discipline as TASK A: 5 different surfaces could need
    this gate (equip, auto-equip, preview-equip, swap-equipment, admin
    grant-equip). Centralising avoids drift.
  * Legacy items lack `level_required` (or have it set to the default `1`)
    even when rarity demands a much higher gate (e.g. seeded Legendary
    raid drops). We derive a conservative default from `rarity` so old
    catalog rows behave correctly without a backfill migration.

Error contract (HTTP 423 — Locked, mirrors `adventurer.level_too_low`):

    {
        "code": "equipment.level_requirement_not_met",
        "source": "equipment.equip" | "equipment.auto_unequip" | ...,
        "item_slug": "<slug>",
        "required_level": <int>,
        "current_level": <int>,
        "user_message": "Questo oggetto richiede Lv X (..)"
    }

PII: NO email, NO _id, NO user_id. `item_slug` is public catalog data
(already exposed via `/api/items`).
"""
from __future__ import annotations

from fastapi import HTTPException


# ─── Rarity → level mapping ───────────────────────────────────────────────────
# Used ONLY when the seed lacks an explicit `level_required` > 1. Conservative
# enough that legacy items don't suddenly become unequippable for active
# tester accounts, strict enough that future Legendary/Signature drops are
# properly gated. Brief umano: Common=1, Uncommon=3, Rare=5, Epic=8,
# Legendary=12, Signature=spec_level default 5.
_RARITY_TO_MIN_LEVEL: dict[str, int] = {
    "Common": 1,
    "Uncommon": 3,
    "Rare": 5,
    "Epic": 8,
    "Legendary": 12,
    "Signature": 5,
}


def resolve_item_required_level(item: dict) -> int:
    """Return the effective `required_adventurer_level` for an item.

    Resolution order (first non-None wins):
      1. Explicit `required_adventurer_level` field (Round 11.3+ items).
      2. Legacy `level_required` field if > 1.
      3. Rarity-derived default (table above).
      4. Final fallback: 1.

    Raid items typically carry an explicit `required_adventurer_level=12-15`
    in their seed; the rarity-derived path is only the safety net for the
    handful of Round-4 Legendaries that pre-date this gate.
    """
    explicit = item.get("required_adventurer_level")
    if isinstance(explicit, int) and explicit >= 1:
        return explicit
    legacy = item.get("level_required")
    if isinstance(legacy, int) and legacy > 1:
        return legacy
    rarity = item.get("rarity", "Common")
    return _RARITY_TO_MIN_LEVEL.get(rarity, 1)


def enforce_item_level_requirement(
    item: dict,
    adventurer: dict,
    *,
    source: str,
) -> None:
    """Raise 423 if `adventurer.level` < item's required level.

    `source` is a stable string (e.g. "equipment.equip",
    "equipment.auto_unequip", "equipment.preview") used by the FE to branch
    error UI and by audit dashboards to count blocked attempts per surface.
    """
    required = resolve_item_required_level(item)
    if required <= 1:
        return
    current = int(adventurer.get("level", 1) or 1)
    if current >= required:
        return
    raise HTTPException(
        status_code=423,
        detail={
            "code": "equipment.level_requirement_not_met",
            "source": source,
            # Slug is public catalog data — safe to expose. We deliberately
            # do NOT echo back the rarity or stat bonuses (anti-spoiler).
            "item_slug": item.get("slug"),
            "required_level": required,
            "current_level": current,
            "user_message": (
                f"Questo oggetto richiede Lv{required} "
                f"(attuale: Lv{current})."
            ),
        },
    )


__all__ = [
    "resolve_item_required_level",
    "enforce_item_level_requirement",
]
