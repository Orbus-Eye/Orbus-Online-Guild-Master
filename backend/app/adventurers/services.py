"""Adventurers + classes + traits services (Phase 5.5d + Phase 14.3-c)."""

import logging
import re
from fastapi import HTTPException

from app.classes import class_role_for
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
    raw_name = t.get("name") or ""
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
            t.get("code"),
            raw_name,
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
        "is_positive": (
            doc.get("is_positive") if doc.get("is_positive") is not None else True
        ),
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
    # ROUND 18.3a.1 hotfix — serializer difensivo. Alcuni doc seedati da
    # R18.3a (`cacciatore_di_mostri`, `cacciatore_del_vuoto`) potrebbero
    # mancare di campi come `role` finché PM Q7-Q24 non sigilla i valori.
    # Uso `.get(field, <sensible_default>)` per resilienza (defense in
    # depth). NON è pulizia opportunistica: previene HTTP 500 su schema
    # evolution futura.
    return {
        "id": doc.get("id"),
        "name": doc.get("name") or doc.get("slug") or "",
        # ROUND 15.1 — IT display name (falls back to `name` until the
        # seed migration has touched the doc).
        "display_name_it": doc.get("display_name_it")
        or doc.get("name")
        or doc.get("slug")
        or "",
        "slug": doc.get("slug"),
        # ROUND 18.3a.1 — default "TBD" placeholder, PM decision deferred
        # (see Q7-Q24 in `orbus_world_roadmap.md`).
        "role": doc.get("role", "TBD"),
        "description": doc.get("description", ""),
        # ROUND 16.0 — base_* keys defaulted with `.get(..., 0)` so that
        # newly seeded classes (e.g. warlock) without legacy base stats
        # do not crash the projector. The R15 + R16 catalog uses
        # `primary_stat` / `secondary_stats` as the canonical signal.
        "base_strength": int(doc.get("base_strength", 0) or 0),
        "base_agility": int(doc.get("base_agility", 0) or 0),
        "base_intellect": int(doc.get("base_intellect", 0) or 0),
        "base_endurance": int(doc.get("base_endurance", 0) or 0),
        "base_faith": int(doc.get("base_faith", 0) or 0),
        "is_active": doc.get("is_active", True),
        # ROUND 15 — class identity (Fase 1). All optional in the
        # projection; the FE shows "—" if missing on legacy/test docs.
        "primary_stat": doc.get("primary_stat"),
        "secondary_stats": doc.get("secondary_stats") or [],
        "allowed_weapon_tags": doc.get("allowed_weapon_tags") or [],
        "allowed_armor_tags": doc.get("allowed_armor_tags") or [],
        "preferred_item_tags": doc.get("preferred_item_tags") or [],
        "role_tags": doc.get("role_tags") or [],
        "xp_primary_stat_policy": doc.get("xp_primary_stat_policy")
        or {"enabled": False},
        "guide_description_it": doc.get("guide_description_it") or "",
        "guide_description_en": doc.get("guide_description_en") or "",
        # ROUND 16.0.1 — expose Round 16 catalogue flags so admin UI can
        # separate active base classes from deprecated specializations.
        "is_base_class": bool(doc.get("is_base_class", False)),
        "is_specialization": bool(doc.get("is_specialization", False)),
        "parent_class_slug": doc.get("parent_class_slug"),
        "deprecated_at": doc.get("deprecated_at"),
        # ROUND 18.3a.1 — expose R18 migration-target metadata so admin
        # UI can distinguish hidden migration classes from live ones.
        "is_playable": doc.get("is_playable", True),
        "migration_target_only": bool(doc.get("migration_target_only", False)),
        "source_round": doc.get("source_round"),
        "role_placeholder": bool(doc.get("role_placeholder", False)),
        "role_pm_decision_pending": bool(doc.get("role_pm_decision_pending", False)),
    }


def adventurer_public(doc: dict) -> dict:
    """Public projection. Caller must inject `_equipment_slots` + `_equipment_power`
    via `_load_equipment_for_*` (Phase 6) when including equipment info; otherwise
    defaults to empty slots + zero equipment power."""
    # Lazy import to avoid a circular dep between adventurers ↔ equipment domains.
    from app.equipment.services import _empty_slot_map
    from app.adventurers.career import (
        career_effective_stats,
        career_progress_snapshot,
    )
    from app.shared.progression import xp_required_for_next_level
    from app.shared.constants import ADVENTURER_MAX_LEVEL

    eq_slots = doc.get("_equipment_slots") or _empty_slot_map()
    eq_power = int(doc.get("_equipment_power", 0))
    base_power = _adventurer_unit_power(doc)
    career = career_progress_snapshot(doc)
    base_stats = {
        stat: int(doc.get(stat, 0) or 0)
        for stat in ("strength", "agility", "intellect", "endurance", "faith")
    }
    effective_stats = career_effective_stats(doc, base_stats)
    recruit_status = doc.get("recruit_status")
    is_classless = (
        recruit_status == "recruit_unassigned"
        and not doc.get("class_slug")
        and not doc.get("class_proficiency")
    )
    class_slug = (
        None
        if is_classless
        else (doc.get("class_slug") or (doc.get("class_name") or "").lower() or None)
    )
    return {
        "id": doc["id"],
        "guild_id": doc["guild_id"],
        "name": doc["name"],
        "adventurer_class_id": doc.get("adventurer_class_id"),
        "class_name": doc.get("class_name"),
        # ROUND 6E — lowercase slug exposed for client-side class-eligibility
        # filters (e.g. RespecModal). Resolved by readers via a class lookup
        # join (`list_adventurers_for_guild`) or from the doc when already
        # present. Falls back to a `class_name` lowercasing if neither is
        # available — safe because spec eligibility uses lowercase slugs.
        "class_slug": class_slug,
        "canonical_class_slug": doc.get("canonical_class_slug") or class_slug,
        "class_proficiency": doc.get("class_proficiency"),
        "class_hall_id": doc.get("class_hall_id"),
        "class_hall_assigned_at": doc.get("class_hall_assigned_at"),
        "hall_master_witness_npc": doc.get("hall_master_witness_npc"),
        "recruit_status": recruit_status,
        "class_selection_required": is_classless,
        "class_display_name_it": (
            "Senza Classe" if is_classless else doc.get("class_name")
        ),
        "narrative_intro_shown": bool(doc.get("narrative_intro_shown", False)),
        "starter_item_reward_status": doc.get("starter_item_reward_status"),
        # FASE 9B — il ruolo deriva SEMPRE dalla classe (registry canonico
        # DPS/TANK/HEALER); il campo doc resta solo come fallback legacy.
        "class_role": (
            class_role_for(class_slug) or doc.get("class_role")
        ),
        "rarity": career["rarity"],
        "career": career,
        "level": doc.get("level", 1),
        "experience": doc.get("experience", 0),
        "experience_to_next_level": (
            xp_required_for_next_level(doc.get("level", 1))
            if int(doc.get("level", 1) or 1) < ADVENTURER_MAX_LEVEL
            else None
        ),
        "strength": effective_stats["strength"],
        "agility": effective_stats["agility"],
        "intellect": effective_stats["intellect"],
        "endurance": effective_stats["endurance"],
        "faith": effective_stats["faith"],
        "base_stats": base_stats,
        "rarity_stat_multiplier": career["stat_multiplier"],
        "stamina": doc.get("stamina", 100),
        "morale": doc.get("morale", 100),
        "is_available": doc.get("is_available", True),
        # ROUND 16.3 Phase 4 (post-verify) — expose canonical lock state.
        # `status` complements `is_available` with the fine-grained lock
        # type ("idle" / "expedition" / "raid" / "world_boss" /
        # "resource_gathering"). Consumers should treat `is_available`
        # as the authoritative gate; `status` explains why.
        "status": doc.get("status")
        or ("idle" if doc.get("is_available", True) else "unavailable"),
        "current_mission_id": doc.get("current_mission_id"),
        "current_mission_type": doc.get("current_mission_type"),
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
        # FASE 9C — le specializzazioni selezionabili NON esistono più:
        # il payload non le espone (i campi legacy sul doc vengono
        # rimossi dalla migration 9M). Il ruolo è fisso per classe.
        # ROUND 16.0 Phase 3 — flavour identity (race + gender).
        "race_slug": doc.get("race_slug"),
        "race_name_it": doc.get("race_name_it"),  # joined by services if needed
        "gender": doc.get("gender"),
        # FASE 6 — ritratto personalizzato (None → avatar razziale FE).
        "custom_avatar_url": doc.get("custom_avatar_url") or None,
        "equipment": eq_slots,
        # FASE 3.3 — consumabile attivo (scomparto "Consumabile").
        "active_consumable": doc.get("active_consumable") or None,
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
    ROUND 16.0 Phase 3 — single batched join with `races` to populate
    `race_name_it` on every adventurer DTO.
    """
    from app.equipment.services import _empty_slot_map, _load_equipment_for_guild

    query = {"guild_id": guild_id}
    if not include_retired:
        query["is_retired"] = {"$ne": True}
    rows = (
        await db.adventurers.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    )
    equip_map = await _load_equipment_for_guild(db, guild_id)
    race_name_cache = await _load_race_name_cache(
        db,
        slugs={r.get("race_slug") for r in rows if r.get("race_slug")},
    )
    out = []
    for r in rows:
        slots, power = equip_map.get(r["id"], (_empty_slot_map(), 0))
        r["_equipment_slots"] = slots
        r["_equipment_power"] = power
        if r.get("race_slug"):
            r["race_name_it"] = race_name_cache.get(r["race_slug"])
        out.append(adventurer_public(r))
    return out


async def _load_race_name_cache(db, *, slugs: set[str]) -> dict[str, str]:
    """Batch-fetch `race_name_it` for a set of race slugs (cached per request)."""
    if not slugs:
        return {}
    cursor = db.races.find(
        {"slug": {"$in": list(slugs)}, "is_active": True},
        {"_id": 0, "slug": 1, "name_it": 1},
    )
    return {r["slug"]: r.get("name_it") async for r in cursor}


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
        raise HTTPException(status_code=404, detail="Avventuriero non trovato")
    traits = adv.get("traits") or []
    base_stats = {s: int(adv.get(s, 0)) for s in TRAIT_AFFECTABLE_STATS}
    trait_stats = (
        apply_trait_modifiers(base_stats, traits) if traits else dict(base_stats)
    )
    from app.adventurers.career import (
        career_effective_stats,
        career_stat_multiplier,
    )
    effective_stats = career_effective_stats(adv, trait_stats)
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
        applied.append(
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "modifier_type": mtype,
                "affected_stat": affected,
                "modifier_value": val,
                "is_positive": t.get("is_positive", True),
                "delta_summary": delta,
            }
        )
    return {
        "adventurer_id": adv["id"],
        "base_stats": base_stats,
        "effective_stats": effective_stats,
        "rarity_stat_multiplier": career_stat_multiplier(adv),
        "applied_traits": applied,
        "base_power": base_power,
        "effective_power": effective_power,
        "power_delta": effective_power - base_power,
        "xp_gain_percent": xp_pct,
    }


RENAME_MAX_LIFETIME = 2
# Adventurer rename: letters (incl. Unicode accents), spaces and apostrophe only.
RENAME_NAME_RE = re.compile(r"^[\w\s'\-]+$", re.UNICODE)


async def rename_adventurer(
    db, guild_id: str, adventurer_id: str, new_name: str
) -> dict:
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
        raise HTTPException(status_code=404, detail="Avventuriero non trovato")
    current_count = int(adv.get("rename_count", 0))
    if current_count >= RENAME_MAX_LIFETIME:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Limite rinomine raggiunto ({current_count}/"
                f"{RENAME_MAX_LIFETIME}). Nessuna rinomina ulteriore consentita."
            ),
        )
    # ROUND 11.2 TASK 1bis — Uniqueness vale SOLO tra avventurieri ATTIVI
    # della stessa gilda. Retired/archived mantengono il loro nome storico
    # nei report (chronicle, expedition_members snapshot, audit) ma NON
    # bloccano la riassegnazione del nome ad un nuovo adv attivo.
    # Coerente con `is_retired` flag introdotto in Round 6B.4.
    collision = await db.adventurers.find_one(
        {
            "guild_id": guild_id,
            "id": {"$ne": adventurer_id},
            "is_retired": {"$ne": True},
            "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"},
        },
        {"_id": 0, "id": 1},
    )
    if collision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "adventurer.name.duplicate_active",
                "user_message": "Esiste già un avventuriero attivo con questo "
                "nome nella tua gilda.",
            },
        )
    now_iso = (
        __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat()
    )
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
