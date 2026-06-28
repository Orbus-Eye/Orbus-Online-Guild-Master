"""ROUND 11.2 EXT TASK 10 M1+M4 — Public materials catalog endpoint.

`GET /api/materials/catalog` — public, no auth. Returns the safe player-
facing list of materials (slug, display_name, rarity, description,
sources, used_for) joined from `items` collection × `MATERIAL_CATALOG`
overlay.

Filter contract:
  * `items.item_type == "material"`            (canonical taxonomy)
  * `items.is_active != False`                 (drop legacy inactive)
  * `items.is_test != True`                    (drop QA/test items)
  * `items.is_cosmetic != True`                (defense in depth)
  * slug present in `MATERIAL_CATALOG`         (curation gate — no leak
                                                of items that haven't
                                                been documented yet)

Equipment is never included by definition: `item_type='material'` excludes
weapons/armor/accessories/set/legendary slots. Plus the curated catalog
acts as a positive allow-list (an item is exposed ONLY if explicitly
documented). Belt and suspenders.

Admin grant is intentionally absent from the `sources` taxonomy.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.database import db
from app.materials.catalog import (
    MATERIAL_CATALOG,
    SOURCE_LABEL_EN,
    SOURCE_LABEL_IT,
    get_material_overlay,
)


router = APIRouter(prefix="/api", tags=["materials"])


def _project_material(item: dict, overlay: dict) -> dict:
    sources = []
    for s in overlay.get("sources", []) or []:
        stype = s.get("type")
        sources.append({
            "type": stype,
            "label_it": SOURCE_LABEL_IT.get(stype, stype),
            "label_en": SOURCE_LABEL_EN.get(stype, stype),
            "tier": s.get("tier"),
            "frequency": s.get("frequency"),
            "note_it": s.get("note"),
        })
    return {
        "slug": item["slug"],
        "display_name_it": item.get("display_name_it") or item.get("name") or item["slug"],
        "display_name_en": item.get("display_name_en") or item.get("name") or item["slug"],
        "rarity": overlay.get("rarity", "common"),
        "description_it": overlay.get("description_it") or "",
        "description_en": overlay.get("description_en") or "",
        "sources": sources,
        "used_for_it": list(overlay.get("used_for_it") or []),
    }


@router.get("/materials/catalog")
async def public_materials_catalog():
    """Player-facing materials list (no auth). Equipment NEVER included."""
    rows = await db.items.find(
        {
            "item_type": "material",
            "is_active": {"$ne": False},
            "is_test": {"$ne": True},
            "is_cosmetic": {"$ne": True},
        },
        {"_id": 0},
    ).to_list(200)
    out: list[dict] = []
    gaps: list[str] = []
    for r in rows:
        slug = r.get("slug")
        if not slug:
            continue
        overlay = get_material_overlay(slug)
        if overlay is None:
            # Documented gap — material exists in DB but not curated yet.
            # Skip from public exposure (safe default).
            gaps.append(slug)
            continue
        out.append(_project_material(r, overlay))
    # Stable sort: rarity bucket then IT display name.
    rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
    out.sort(key=lambda r: (rarity_order.get(r["rarity"], 9), r["display_name_it"]))
    return {"total": len(out), "materials": out, "content_gaps": gaps}


@router.get("/materials/lookup/{slug}")
async def public_material_lookup(slug: str):
    """ROUND 11.2 EXT-2 — Single-material lookup for inline UI popovers.

    Same security filter contract as `/api/materials/catalog`. Returns
    404 (not 200 with null) so the FE `MaterialSourceModal` can fail
    fast on equipment-slug attempts, removed/inactive/test items, and
    typos — without exposing existence.
    """
    from fastapi import HTTPException
    overlay = get_material_overlay(slug)
    if overlay is None:
        raise HTTPException(status_code=404, detail={"code": "material.not_found"})
    item = await db.items.find_one(
        {
            "slug": slug,
            "item_type": "material",
            "is_active": {"$ne": False},
            "is_test": {"$ne": True},
            "is_cosmetic": {"$ne": True},
        },
        {"_id": 0},
    )
    if item is None:
        raise HTTPException(status_code=404, detail={"code": "material.not_found"})
    return _project_material(item, overlay)


__all__ = ["router"]
