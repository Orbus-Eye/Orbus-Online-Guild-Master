"""ROUND 11.2 TASK 6 G1-G2 — Public catalog routes (traits + stats).

Both endpoints PUBLIC by design. They consume:
  * `db.adventurer_traits` for the traits catalog (data-driven, filtered
    to drop `is_test=True` or `is_active=False`).
  * `app.stats.public_catalog.STATS_CATALOG` for the stats catalog
    (code-defined, single source of truth co-located with the docs).

Response shapes are intentionally stable and PII-safe; the same payloads
back the in-game Guide tabs and any future external integration.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.database import db
from app.stats.public_catalog import get_public_stats_catalog


router = APIRouter(prefix="/api", tags=["catalog"])


_TRAIT_NEGATIVE_FALLBACK_RE = None  # placeholder kept for future heuristics


def _trait_polarity(doc: dict) -> str:
    """Stable polarity mapping: positive | negative | mixed.

    Prefers the explicit `polarity` field (Phase 14.3-c canonical seed).
    Falls back to the legacy `is_positive` flag for older docs that never
    received the migration.
    """
    p = (doc.get("polarity") or "").strip().lower()
    if p in ("positive", "negative", "mixed"):
        return p
    return "positive" if doc.get("is_positive", True) else "negative"


def _trait_public_catalog_row(doc: dict) -> dict:
    """Public projection — never leaks `code`, `is_test`, internal flags."""
    display_it = (
        doc.get("display_name_it")
        or doc.get("display_name")
        or doc.get("display_name_en")
        or doc.get("name")
        or ""
    )
    display_en = doc.get("display_name_en") or doc.get("display_name") or ""
    description_it = doc.get("description") or ""
    description_en = doc.get("description_en") or description_it or ""
    return {
        "id": doc.get("id"),
        "display_name_it": display_it,
        "display_name_en": display_en,
        "description_it": description_it,
        "description_en": description_en,
        "rarity": (doc.get("rarity") or "common").lower(),
        "polarity": _trait_polarity(doc),
        "affected_stat": doc.get("affected_stat"),
        "modifier_type": doc.get("modifier_type"),
        "modifier_value": doc.get("modifier_value"),
    }


@router.get("/traits/catalog")
async def public_traits_catalog():
    """Public traits catalog consumed by the Guide.

    Filters:
      * `is_active != False` — only active traits.
      * `is_test != True`    — never expose internal/test traits.

    Sort: rarity (common→epic) then display name ascending so the order
    is stable across reloads.
    """
    rows = await db.adventurer_traits.find(
        {"is_active": {"$ne": False}, "is_test": {"$ne": True}},
        {"_id": 0},
    ).to_list(1000)
    out = [_trait_public_catalog_row(r) for r in rows]
    # Stable ordering for UI: rarity bucket (common < uncommon < rare < epic)
    # then by IT display name.
    rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
    out.sort(key=lambda r: (rarity_order.get(r["rarity"], 9), r["display_name_it"] or ""))
    return {"total": len(out), "traits": out}


@router.get("/stats/catalog")
async def public_stats_catalog():
    """Public stats catalog consumed by the Guide (static, code-defined)."""
    stats = get_public_stats_catalog()
    return {"total": len(stats), "stats": stats}


__all__ = ["router"]
