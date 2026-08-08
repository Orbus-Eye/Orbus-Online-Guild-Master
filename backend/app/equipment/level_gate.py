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

from app.items.catalog_contract import effective_catalog_required_level


def resolve_item_required_level(item: dict) -> int:
    """Return the effective `required_adventurer_level` for an item.

    Resolution order (first non-None wins):
      1. Legendary/Unique hard gate at the authoritative max level.
      2. Explicit `required_adventurer_level` field (Round 11.3+ items).
      3. Legacy `level_required` field if > 1.
      4. Rarity-derived default from the canonical catalog contract.
      5. Final fallback: 1.

    Endgame rarity overrides intentionally win over legacy explicit values:
    old Legendary rows at level 8/9/12 must not bypass the new max-level rule.
    """
    return effective_catalog_required_level(item)


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
