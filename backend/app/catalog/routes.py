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
    """Stable polarity mapping: positive | negative | mixed | neutral.

    Phase 14.3-c canonical seed stamps `polarity` explicitly. Older Round 4
    seeds (≈31 of the 41 active traits) leave it empty — we recover it from:
      1. `is_positive` boolean flag (most legacy seeds set this),
      2. `modifier_value` sign as last resort.
    Returns "neutral" only when the trait has no measurable effect at all.
    """
    p = (doc.get("polarity") or "").strip().lower()
    if p in ("positive", "negative", "mixed", "neutral"):
        return p
    if doc.get("is_positive") is True:
        return "positive"
    if doc.get("is_positive") is False:
        return "negative"
    mv = doc.get("modifier_value")
    if isinstance(mv, (int, float)):
        if mv > 0:
            return "positive"
        if mv < 0:
            return "negative"
    return "neutral"


def _trait_gameplay_effect(doc: dict) -> dict:
    """Compose the player-facing effect summary for the Guide.

    Returns a dict with:
      - `summary_it` / `summary_en`: 1-line readable effect.
      - `affects_power` (bool): does the trait change PWR computation?
      - `is_situational` (bool): only triggers in specific contexts.
      - `is_capped` (bool): effect has a maximum value.
    NEVER invents effects — if the trait has no modifier_value or affected_stat,
    returns the explicit fallback string used by the FE.
    """
    affected = (doc.get("affected_stat") or "").strip()
    mtype = (doc.get("modifier_type") or "").strip().lower()
    mv = doc.get("modifier_value")
    affects_power = bool(affected) and mv not in (None, 0)
    if not affected or mv in (None, 0):
        return {
            "summary_it": "Tratto descrittivo: al momento non modifica direttamente i calcoli principali.",
            "summary_en": "Flavor trait: it does not currently modify core calculations.",
            "affects_power": False,
            "is_situational": False,
            "is_capped": False,
        }
    sign = "+" if (isinstance(mv, (int, float)) and mv > 0) else ""
    unit = "%" if mtype == "percent" else ""
    return {
        "summary_it": f"Modifica la statistica «{affected}» di {sign}{mv}{unit}.",
        "summary_en": f"Adjusts stat «{affected}» by {sign}{mv}{unit}.",
        "affects_power": affects_power,
        "is_situational": False,  # reserved for future seeds
        "is_capped": False,       # reserved for future seeds
    }


def _trait_public_catalog_row(doc: dict) -> dict:
    """Public projection — never leaks `code`, `is_test`, internal flags.

    ROUND 11.2 EXT TASK 9: schema enriched with `polarity` fallback, gameplay
    effect summary, and explicit `affects_power` flag so the Guide can render
    the catalog without inventing effects.
    """
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
    effect = _trait_gameplay_effect(doc)
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
        # TASK 9 additions — gameplay effect for the Guide page.
        "gameplay_effect_it": effect["summary_it"],
        "gameplay_effect_en": effect["summary_en"],
        "affects_power": effect["affects_power"],
        "is_situational": effect["is_situational"],
        "is_capped": effect["is_capped"],
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
    # Polarity breakdown helps the FE render headline counts without
    # re-iterating the full list.
    counts = {"positive": 0, "negative": 0, "mixed": 0, "neutral": 0}
    for r in out:
        counts[r["polarity"]] = counts.get(r["polarity"], 0) + 1
    return {"total": len(out), "traits": out, "counts": counts}


@router.get("/stats/catalog")
async def public_stats_catalog():
    """Public stats catalog consumed by the Guide (static, code-defined)."""
    stats = get_public_stats_catalog()
    return {"total": len(stats), "stats": stats}


__all__ = ["router"]
