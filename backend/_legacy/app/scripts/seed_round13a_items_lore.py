"""ROUND 13a — Idempotent lore + level enrichment seed for items.

Adds for every `db.items` row (non-test, non-inactive):
  * `required_adventurer_level` (explicit MAX(rarity_lvl, tier_lvl, raid_lvl))
  * `display_name_it` (override visivo; non sostituisce `name`/`slug`)
  * `display_name_en`
  * `flavor_text_it` (max ~200 char, può essere None per Common neutri)
  * `flavor_text_en`
  * `lore_tags` (array)
  * `lore_source = "orbus_lore_book_v1"`
  * `lore_reviewed = True`, `lore_reviewed_at`
  * `spoiler_level` ∈ {public, mystery, hidden, internal}

Idempotent: re-runs sono no-op se `lore_reviewed=True`. Slug invariati,
`name` invariato (backward compat).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.database import db

logger = logging.getLogger("orbus.seed_round13a_items_lore")

LORE_SOURCE = "orbus_lore_book_v1"

# Rarity → minimum required adventurer level
_RARITY_LVL = {
    "Common": 1, "Uncommon": 3, "Rare": 5,
    "Epic": 8, "Legendary": 12, "Signature": 5,
}

# Slug → manual lore-flavored display name (Italian).
# Per ogni rarità ho preparato un mix di nomi cultural-coherent.
# Common: nomi puliti, no lore heavy.
# Uncommon: riferimenti soft.
# Rare/Epic/Legendary: riferimenti lore espliciti.
SLUG_DISPLAY_NAME_IT: dict[str, str] = {
    # ─── Pattern automatici fallback per rarity ───
    # (popolato runtime se nessun override esplicito)
}

# Lore-flavored display names for Epic+ (cherry-picked).
SLUG_DISPLAY_IT_EPIC_LEGENDARY: dict[str, dict] = {
    # We only hard-code a handful here; others get generic IT rarity-aware default.
    "voidpiercer-bow": {"it": "Arco Trafittore del Vuoto", "en": "Voidpiercer Bow",
                        "flavor_it": "Le frecce non sibilano. Vuotano.",
                        "tags": ["vuoto", "filo-spezzato"], "spoiler": "mystery"},
    "oracle-pendant": {"it": "Pendente dell'Oracolo Cieco", "en": "Blind Oracle's Pendant",
                       "flavor_it": "Vede ciò che non c'è ancora — e ciò che non c'è più.",
                       "tags": ["memoria", "oracolo"], "spoiler": "mystery"},
    "phoenix-relic": {"it": "Eco della Sinfonia dei Fili", "en": "Echo of the String Symphony",
                      "flavor_it": "Pulsa al ritmo di una nota silenziosa.",
                      "tags": ["sinfonia", "filo-spezzato"], "spoiler": "mystery"},
    "dragon-mask": {"it": "Maschera della Luna Morta", "en": "Mask of the Dead Moon",
                    "flavor_it": "Chi la indossa vede solo metà dei suoi nemici.",
                    "tags": ["luna-morta", "alevora"], "spoiler": "mystery"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rarity_level(rarity: str) -> int:
    return _RARITY_LVL.get(rarity or "Common", 1)


def _resolve_req_level(item: dict) -> int:
    base = _rarity_level(item.get("rarity") or "Common")
    if item.get("source") == "raid":
        base = max(base, 12)
    if (item.get("tags") or []) and "raid" in (item.get("tags") or []):
        base = max(base, 12)
    # Existing explicit value wins if higher.
    explicit = item.get("required_adventurer_level")
    if isinstance(explicit, int) and explicit > base:
        base = explicit
    return base


def _build_display_it(item: dict) -> tuple[str, str]:
    """Return (it, en) display names. Conservative auto-gen."""
    slug = item.get("slug") or ""
    if slug in SLUG_DISPLAY_IT_EPIC_LEGENDARY:
        d = SLUG_DISPLAY_IT_EPIC_LEGENDARY[slug]
        return d["it"], d.get("en") or item.get("name") or slug
    # Auto: take english `name` and produce a plausible Italian-flavored variant.
    name = item.get("name") or slug.replace("-", " ").title()
    rarity = item.get("rarity") or "Common"
    # Auto Italian common-translation: keep `name` as fallback,
    # but prefix lore-flavored adjective for Epic/Legendary.
    if rarity == "Legendary":
        it = f"{name} dell'Oblio"
    elif rarity == "Epic":
        it = f"{name} del Filo Spezzato"
    elif rarity == "Rare":
        it = f"{name} delle Veglie"
    elif rarity == "Uncommon":
        it = f"{name} del Confine"
    else:
        it = name  # Common: leave as-is
    return it, name


def _build_flavor(item: dict) -> tuple[str | None, str | None]:
    slug = item.get("slug") or ""
    if slug in SLUG_DISPLAY_IT_EPIC_LEGENDARY:
        d = SLUG_DISPLAY_IT_EPIC_LEGENDARY[slug]
        return d.get("flavor_it"), d.get("flavor_en")
    rarity = item.get("rarity") or "Common"
    if rarity == "Common":
        return None, None
    if rarity == "Uncommon":
        return ("Un oggetto di confine: parla solo a chi lo ascolta.", None)
    if rarity == "Rare":
        return ("Si sente una vibrazione antica, come una nota mai suonata.", None)
    if rarity == "Epic":
        return ("Porta in sé l'eco del Filo Spezzato. Vibra senza vento.", None)
    if rarity == "Legendary":
        return ("Ricorda un sigillo. Non quale.", None)
    return None, None


def _build_lore_tags(item: dict) -> list[str]:
    slug = item.get("slug") or ""
    if slug in SLUG_DISPLAY_IT_EPIC_LEGENDARY:
        return SLUG_DISPLAY_IT_EPIC_LEGENDARY[slug].get("tags", [])
    rarity = item.get("rarity") or "Common"
    if rarity == "Common":
        return ["mundane"]
    if rarity == "Uncommon":
        return ["frontiera"]
    if rarity == "Rare":
        return ["veglie", "memoria"]
    if rarity == "Epic":
        return ["filo-spezzato"]
    if rarity == "Legendary":
        return ["oblio", "vuoto"]
    return []


def _spoiler_level(item: dict) -> str:
    rarity = item.get("rarity") or "Common"
    if rarity == "Legendary":
        return "mystery"
    return "public"


async def run() -> dict[str, Any]:
    flt = {
        "$and": [
            {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]},
            {"$or": [{"is_test": {"$ne": True}}, {"is_test": {"$exists": False}}]},
            {"$or": [{"slug": {"$not": {"$regex": "test|debug", "$options": "i"}}}]},
        ]
    }
    cursor = db.items.find(flt, {"_id": 0})
    updated = 0
    skipped = 0
    by_rarity: dict[str, int] = {}
    async for item in cursor:
        if item.get("lore_reviewed"):
            skipped += 1
            continue
        req_lvl = _resolve_req_level(item)
        disp_it, disp_en = _build_display_it(item)
        flavor_it, flavor_en = _build_flavor(item)
        set_fields: dict[str, Any] = {
            "required_adventurer_level": req_lvl,
            "display_name_it": disp_it,
            "display_name_en": disp_en,
            "lore_tags": _build_lore_tags(item),
            "lore_source": LORE_SOURCE,
            "lore_reviewed": True,
            "lore_reviewed_at": _now(),
            "spoiler_level": _spoiler_level(item),
        }
        if flavor_it is not None:
            set_fields["flavor_text_it"] = flavor_it
        if flavor_en is not None:
            set_fields["flavor_text_en"] = flavor_en
        await db.items.update_one({"slug": item["slug"]}, {"$set": set_fields})
        updated += 1
        rar = item.get("rarity") or "Common"
        by_rarity[rar] = by_rarity.get(rar, 0) + 1

    out = {
        "status": "done",
        "items_updated": updated,
        "items_skipped_already_reviewed": skipped,
        "by_rarity": by_rarity,
    }
    logger.info("ROUND 13a items lore+level: %s", out)
    return out


if __name__ == "__main__":
    print(asyncio.run(run()))
