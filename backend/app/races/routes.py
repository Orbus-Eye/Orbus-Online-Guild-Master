"""ROUND 16.x P1 — Public races catalog routes.

Exposes the 50 playable races seeded by
`app.scripts.round160_seed_races`. Read-only, no auth required (matches
the public catalog pattern used by `app.catalog.routes`).

Endpoints
---------
GET  /api/races                 — list all active + playable races
GET  /api/races/{slug}          — single race by slug

Response fields (per race)
--------------------------
- slug          (str, stable identifier)
- name_it       (str, italian display name)
- name_en       (str, english fallback)
- rarity        (common | uncommon | rare | epic)
- lore_group    (str, narrative grouping)
- is_playable   (bool)
- is_active     (bool)

`stat_modifiers`, `tags`, `description_it`, `created_at`, `updated_at`
are NOT exposed — they are internal/reserved for future flavor.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.database import db


router = APIRouter(prefix="/api", tags=["races"])


_PUBLIC_FIELDS = ("slug", "name_it", "name_en", "rarity", "lore_group", "is_playable", "is_active")


def _public(doc: dict) -> dict:
    return {k: doc.get(k) for k in _PUBLIC_FIELDS}


@router.get("/races")
async def list_races(
    rarity: str | None = Query(None, description="filter by rarity"),
    include_inactive: bool = Query(False, description="admin/debug: include is_active=false"),
):
    q: dict = {"is_playable": True}
    if not include_inactive:
        q["is_active"] = True
    if rarity:
        q["rarity"] = rarity
    cursor = db.races.find(q, {"_id": 0}).sort([("rarity", 1), ("slug", 1)])
    rows = await cursor.to_list(200)
    return {"total": len(rows), "races": [_public(r) for r in rows]}


@router.get("/races/{slug}")
async def get_race(slug: str):
    doc = await db.races.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="race_not_found")
    return {"race": _public(doc)}
