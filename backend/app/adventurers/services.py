"""Adventurers + classes + traits services (Phase 5.5d + Phase 14.3-c)."""
import logging
import re
from fastapi import HTTPException

from app.expeditions.formulas import (
    TRAIT_AFFECTABLE_STATS,
    TRAIT_XP_STAT,
    adventurer_base_power as _adventurer_unit_power,
    adventurer_effective_power as _adventurer_effective_power,
    apply_trait_modifiers,
    sum_xp_percent,
)


logger = logging.getLogger("orbus")

# Phase 14.3-c — runtime defense: even if a flagged test trait somehow
# ends up in `adventurers.traits[]` (e.g. created by a not-yet-restarted
# test fixture), the serializer must drop it. This regex is the same one
# used by the seed runner's cleanup pass.
_TEST_TRAIT_NAME_RE = re.compile(
    r"^(Test|TEST_|qa_|dev_|pytest_)|_[a-f0-9]{6,}$|^[a-f0-9-]{16,}$",
    re.IGNORECASE,
)


def _is_test_trait_doc(t: dict) -> bool:
    if not isinstance(t, dict):
        return True
    if t.get("is_test") is True or t.get("is_active") is False:
        return True
    return bool(_TEST_TRAIT_NAME_RE.search(t.get("name", "") or ""))


def _trait_display_name(t: dict) -> str:
    """Player-facing label. Prefers display_name → display_name_en → prettified name.

    Logs a warning when display_name is missing (signals an outdated seed).
    Never returns the raw `code` or `name` if a test pattern matches.
    """
    if not isinstance(t, dict):
        return ""
    raw_name = (t.get("name") or "")
    if t.get("display_name"):
        return t["display_name"]
    if t.get("display_name_en"):
        return t["display_name_en"]
    if raw_name:
        # Legacy seed traits without an explicit display_name fall back to a
        # prettified version of `name`. Logged at DEBUG only to avoid spam:
        # the canonical Italian catalog (Phase 14.3-c) always carries
        # display_name, so this branch only fires for the old English seed.
        logger.debug(
            "trait missing display_name: code=%s name=%s — using prettified fallback",
            t.get("code"), raw_name,
        )
        return raw_name.replace("_", " ").replace("-", " ").strip().title()
    return ""


def _polarity_for(t: dict) -> str:
    """Derive polarity from explicit field, falling back to legacy is_positive."""
    p = (t.get("polarity") or "").lower()
    if p in ("positive", "negative", "mixed"):
        return p
    return "positive" if t.get("is_positive", True) else "negative"


def trait_admin_public(doc: dict) -> dict:
    """Admin-safe trait projection — exposes EVERY moderation field so the
    admin panel can manage even quarantined/disabled traits. NEVER call
    from player-facing endpoints (use `trait_public` for those)."""
    if not doc:
        return {}
    return {
        "id": doc.get("id"),
        "name": doc.get("name") or "",
        "display_name": _trait_display_name(doc) or doc.get("name") or "",
        "display_name_it": doc.get("display_name_it") or "",
        "display_name_en": doc.get("display_name_en") or doc.get("display_name") or "",
        "slug": doc.get("slug") or "",
        "description": doc.get("description") or "",
        "rarity": (doc.get("rarity") or "common").lower(),
        "polarity": _polarity_for(doc),
        "is_positive": doc.get("is_positive") if doc.get("is_positive") is not None else True,
        "is_active": doc.get("is_active") if doc.get("is_active") is not None else True,
        "is_test": doc.get("is_test") is True,
        "modifier_type": doc.get("modifier_type") or "",
        "affected_stat": doc.get("affected_stat") or "",
        "modifier_value": doc.get("modifier_value"),
        "created_at": doc.get("created_at") or "",
        "updated_at": doc.get("updated_at") or "",
    }


def trait_public(doc: dict) -> dict:
    """Player-safe trait projection — never exposes `code`, `is_test` or
    internal-only flags. Tests and the player-facing UI consume this
    shape. Returns the empty dict for traits flagged as test/inactive
    so callers can safely filter via truthy checks.
    """
    if not doc or _is_test_trait_doc(doc):
        return {}
    return {
        "id": doc.get("id"),
        "display_name": _trait_display_name(doc),
        # ROUND 6A.2b — IT translation; UI prefers this when present.
        "display_name_it": doc.get("display_name_it") or "",
        "description": doc.get("description", "") or "",
        "rarity": (doc.get("rarity") or "common").lower(),
        "polarity": _polarity_for(doc),
    }


def trait_public_filtered_list(traits: list) -> list[dict]:
    """Apply `trait_public` and drop empties (i.e. dropped test traits)."""
    out = []
    for t in traits or []:
        v = trait_public(t)
        if v:
            out.append(v)
    return out


def class_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "slug": doc["slug"],
        "role": doc["role"],
        "description": doc.get("description", ""),
        "base_strength": doc["base_strength"],
        "base_agility": doc["base_agility"],
        "base_intellect": doc["base_intellect"],
        "base_endurance": doc["base_endurance"],
        "base_faith": doc["base_faith"],
        "is_active": doc.get("is_active", True),
    }


def adventurer_public(doc: dict) -> dict:
    """Public projection. Caller must inject `_equipment_slots` + `_equipment_power`
    via `_load_equipment_for_*` (Phase 6) when including equipment info; otherwise
    defaults to empty slots + zero equipment power."""
    # Lazy import to avoid a circular dep between adventurers ↔ equipment domains.
    from app.equipment.services import _empty_slot_map

    eq_slots = doc.get("_equipment_slots") or _empty_slot_map()
    eq_power = int(doc.get("_equipment_power", 0))
    base_power = _adventurer_unit_power(doc)
    return {
        "id": doc["id"],
        "guild_id": doc["guild_id"],
        "name": doc["name"],
        "adventurer_class_id": doc["adventurer_class_id"],
        "class_name": doc.get("class_name"),
        "class_role": doc.get("class_role"),
        "rarity": doc.get("rarity", "Common"),
        "level": doc.get("level", 1),
        "experience": doc.get("experience", 0),
        "strength": doc["strength"],
        "agility": doc["agility"],
        "intellect": doc["intellect"],
        "endurance": doc["endurance"],
        "faith": doc["faith"],
        "stamina": doc.get("stamina", 100),
        "morale": doc.get("morale", 100),
        "is_available": doc.get("is_available", True),
        "is_retired": bool(doc.get("is_retired", False)),
        "retired_at": doc.get("retired_at"),
        # ROUND 6B.3 Wave 1.5 — None for legacy records (treated as "user"
        # by readers). New retires set "user"; future automations may set
        # "system" / "auto_over_cap".
        "retired_by": doc.get("retired_by"),
        "retire_via": doc.get("retire_via"),
        "retirement_reason": doc.get("retirement_reason"),
        "is_starter": bool(doc.get("is_starter", False)),
        "rename_count": int(doc.get("rename_count", 0)),
        "rename_max": 2,
        "renames_remaining": max(0, 2 - int(doc.get("rename_count", 0))),
        "traits": trait_public_filtered_list(doc.get("traits", [])),
        # ROUND 6C — specialization snapshot (None when not yet specialized).
        # The snapshot is set at apply-time so future catalog rebalancing
        # never retroactively changes live adventurers' bonuses.
        "specialization": doc.get("specialization"),
        "equipment": eq_slots,
        "base_power": base_power,
        "equipment_power": eq_power,
        "total_power": base_power + eq_power,
        "created_at": doc["created_at"],
        "updated_at": doc.get("updated_at", doc["created_at"]),
    }


async def list_adventurers_for_guild(
    db, guild_id: str, *, include_retired: bool = False
) -> list[dict]:
    """Return all adventurers of a guild + equipment join, public-projected.

    ROUND 6B.2a — retired adventurers are EXCLUDED by default; pass
    `include_retired=True` for admin/history views.
    """
    from app.equipment.services import _empty_slot_map, _load_equipment_for_guild

    query = {"guild_id": guild_id}
    if not include_retired:
        query["is_retired"] = {"$ne": True}
    rows = (
        await db.adventurers.find(query, {"_id": 0})
        .sort("created_at", -1)
        .to_list(500)
    )
    equip_map = await _load_equipment_for_guild(db, guild_id)
    out = []
    for r in rows:
        slots, power = equip_map.get(r["id"], (_empty_slot_map(), 0))
        r["_equipment_slots"] = slots
        r["_equipment_power"] = power
        out.append(adventurer_public(r))
    return out


async def trait_preview_for_adventurer(db, guild_id: str, adventurer_id: str) -> dict:
    """Phase 13 — read-only preview of trait effects on stats / power.

    Returns base (no-trait) and effective (trait-applied) stats and power,
    plus a per-trait delta summary. Ownership is enforced; adventurers
    that don't belong to the caller's guild yield 404 (no leak).
    """
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    traits = adv.get("traits") or []
    base_stats = {s: int(adv.get(s, 0)) for s in TRAIT_AFFECTABLE_STATS}
    effective_stats = apply_trait_modifiers(base_stats, traits) if traits else dict(base_stats)
    base_power = _adventurer_unit_power(adv)
    effective_power = _adventurer_effective_power(adv)
    xp_pct = sum_xp_percent(traits)
    applied = []
    for t in traits:
        affected = t.get("affected_stat")
        mtype = t.get("modifier_type")
        val = t.get("modifier_value", 0) or 0
        if affected in TRAIT_AFFECTABLE_STATS and mtype == "flat":
            sign = "+" if val >= 0 else ""
            delta = f"{sign}{int(val)} {affected}"
        elif affected in TRAIT_AFFECTABLE_STATS and mtype == "percent":
            sign = "+" if val >= 0 else ""
            delta = f"{sign}{val}% {affected}"
        elif affected == TRAIT_XP_STAT and mtype == "percent":
            sign = "+" if val >= 0 else ""
            delta = f"{sign}{val}% xp_gain"
        else:
            delta = "no effect"
        applied.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "modifier_type": mtype,
            "affected_stat": affected,
            "modifier_value": val,
            "is_positive": t.get("is_positive", True),
            "delta_summary": delta,
        })
    return {
        "adventurer_id": adv["id"],
        "base_stats": base_stats,
        "effective_stats": effective_stats,
        "applied_traits": applied,
        "base_power": base_power,
        "effective_power": effective_power,
        "power_delta": effective_power - base_power,
        "xp_gain_percent": xp_pct,
    }


RENAME_MAX_LIFETIME = 2
# Adventurer rename: letters (incl. Unicode accents), spaces and apostrophe only.
RENAME_NAME_RE = re.compile(r"^[\w\s'\-]+$", re.UNICODE)


async def rename_adventurer(db, guild_id: str, adventurer_id: str, new_name: str) -> dict:
    """Phase 19.2 — rename adventurer with lifetime cap of 2. Free.

    Validation:
      • Adventurer must belong to caller's guild (404 if not — no leak).
      • `rename_count` must be < 2 (409 if exhausted).
      • Name length 2-30 (Pydantic enforces), pattern alphanum + spaces + apostrophe.
      • Uniqueness: case-insensitive within the guild (409 if collision).
    On success: increments `rename_count`, updates `name`, returns public projection.
    """
    from app.equipment.services import _empty_slot_map, _load_equipment_for_guild
    name = (new_name or "").strip()
    if not name or not RENAME_NAME_RE.match(name):
        raise HTTPException(
            status_code=422,
            detail="Nome non valido: usa lettere, spazi, apostrofo o trattino.",
        )
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    current_count = int(adv.get("rename_count", 0))
    if current_count >= RENAME_MAX_LIFETIME:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Limite rinomine raggiunto ({current_count}/"
                f"{RENAME_MAX_LIFETIME}). Nessuna rinomina ulteriore consentita."
            ),
        )
    # Case-insensitive uniqueness within the guild (exclude self)
    collision = await db.adventurers.find_one(
        {
            "guild_id": guild_id,
            "id": {"$ne": adventurer_id},
            "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"},
        },
        {"_id": 0, "id": 1},
    )
    if collision:
        raise HTTPException(
            status_code=409,
            detail="Esiste già un avventuriero con questo nome nella tua gilda.",
        )
    now_iso = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    await db.adventurers.update_one(
        {"id": adventurer_id, "guild_id": guild_id},
        {"$set": {"name": name, "updated_at": now_iso}, "$inc": {"rename_count": 1}},
    )
    # Re-fetch with the same equipment join as list endpoint, return public projection.
    fresh = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    equip_map = await _load_equipment_for_guild(db, guild_id)
    slots, power = equip_map.get(adventurer_id, (_empty_slot_map(), 0))
    fresh["_equipment_slots"] = slots
    fresh["_equipment_power"] = power
    return {"adventurer": adventurer_public(fresh)}


__all__ = [
    "class_public",
    "trait_public",
    "adventurer_public",
    "list_adventurers_for_guild",
    "trait_preview_for_adventurer",
    "rename_adventurer",
    "RENAME_MAX_LIFETIME",
    "RENAME_NAME_RE",
]
