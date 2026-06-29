"""ROUND 6D — Contract services (lazy reset, atomic claim, progress hook).

Pattern mirrors `app.quests.services` (the existing daily+weekly quest loop):
all state is embedded as nested fields on the `guilds` doc (`daily_contract_state`,
`weekly_contract_state`, `guild_milestone_state`), every mutation uses
`find_one_and_update` or `$inc` with a conditional filter (CAS) so concurrent
claims/refreshes never race.

Public surface:
  • `get_today_contracts(db, guild_id)`     — daily list + reset window
  • `get_weekly_contracts(db, guild_id)`    — weekly list + reset window
  • `get_milestones(db, guild_id)`          — full milestone tree + unlock tier
  • `claim_daily_contract(db, guild_id, slug)`
  • `claim_weekly_contract(db, guild_id, slug)`
  • `claim_milestone(db, guild_id, slug)`
  • `increment_contract_progress(db, guild_id, objective_type, amount)`
        — best-effort fan-out hook called from 6 business modules. Updates
          BOTH daily + weekly + milestone counters when their objective_type
          matches. Failures are swallowed (logged) so business writes never
          abort because of a quest-style write race.

Reset semantics:
  • Daily resets at UTC midnight (window keyed by `YYYY-MM-DD`).
  • Weekly resets on ISO Monday (week keyed by `YYYY-Www`).
  • Milestones NEVER reset — they're persistent achievements.

Reward: gold ($inc), materials (inventory rows), reputation ($inc).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.contracts.catalog import (
    DAILY_BY_SLUG,
    DAILY_CONTRACTS,
    MILESTONES_ALL,
    MILESTONES_BY_SLUG,
    MILESTONES_TIER_1,
    MILESTONES_TIER_2,
    MILESTONES_TIER_3,
    TIER_UNLOCK_REQUIRES,
    VALID_OBJECTIVE_TYPES,
    WEEKLY_BY_SLUG,
    select_active_weekly,
)

logger = logging.getLogger("orbus.contracts")

# Contract Board structure slug (ROUND 6D — required prereq for contracts).
CONTRACT_BOARD_SLUG = "contract_board"


# ──────────────────────────────────────────────────────────────────────
# Date helpers (UTC, server-authoritative)
# ──────────────────────────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _today_utc_date() -> str:
    return _now_utc().strftime("%Y-%m-%d")


def _iso_week_key(dt: datetime | None = None) -> str:
    dt = dt or _now_utc()
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _iso_week_index(dt: datetime | None = None) -> int:
    """Monotonic week index used to rotate the pool deterministically."""
    dt = dt or _now_utc()
    iso_year, iso_week, _ = dt.isocalendar()
    return iso_year * 53 + iso_week


def _tomorrow_midnight_utc() -> datetime:
    now = _now_utc()
    return (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _next_monday_utc() -> datetime:
    now = _now_utc()
    days_ahead = (7 - now.weekday()) % 7 or 7
    return (now + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


# ──────────────────────────────────────────────────────────────────────
# Defense-in-depth helpers — never trust an embedded field without a
# fallback. Lesson from the Round 6C `class_slug` bug.
# ──────────────────────────────────────────────────────────────────────
async def _get_contract_board_level(db, guild_id: str) -> int:
    """Return the unlocked Contract Board level (0 = locked, 1+ = unlocked).

    Always reads from `guild_structures` — the source of truth for territory.
    Never trusts a cached field on `guilds`.
    """
    row = await db.guild_structures.find_one(
        {"guild_id": guild_id},
        {"_id": 0, f"structures.{CONTRACT_BOARD_SLUG}": 1},
    )
    cb = (row or {}).get("structures", {}).get(CONTRACT_BOARD_SLUG) or {}
    if not cb.get("is_unlocked"):
        return 0
    return int(cb.get("level", 0))


def _err(code: str, msg: str, *, status: int = 422, **extra) -> HTTPException:
    return HTTPException(
        status_code=status,
        detail={"code": code, "user_message": msg, **extra},
    )


async def _get_unlocked_structure_slugs(db, guild_id: str) -> set[str]:
    """Return the set of structure slugs currently unlocked for the guild.

    Used by `_is_contract_actionable` to filter feature-gated daily/weekly
    contracts at generation time (no clutter with contracts the player can't
    yet make progress on).
    """
    row = await db.guild_structures.find_one(
        {"guild_id": guild_id}, {"_id": 0, "structures": 1},
    )
    structures = (row or {}).get("structures") or {}
    return {slug for slug, s in structures.items()
            if isinstance(s, dict) and s.get("is_unlocked")
            and int(s.get("level", 0)) >= 1}


def _is_contract_actionable(contract: dict, unlocked_slugs: set[str]) -> bool:
    """True iff this contract's feature_gate (if any) is satisfied."""
    gate = contract.get("feature_gate")
    if not gate:
        return True
    needed_slug = gate.get("slug")
    return needed_slug in unlocked_slugs


# ──────────────────────────────────────────────────────────────────────
# DAILY contracts — state + lazy reset + claim
# ──────────────────────────────────────────────────────────────────────
def _empty_daily_state() -> dict:
    return {
        "window_start_utc": _today_utc_date(),
        "contracts": {c["slug"]: {"progress": 0, "claimed": False, "claimed_at": None}
                      for c in DAILY_CONTRACTS},
    }


async def _ensure_daily_fresh(db, guild_id: str) -> dict:
    today = _today_utc_date()
    g = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "daily_contract_state": 1},
    )
    state = (g or {}).get("daily_contract_state")
    if not state or state.get("window_start_utc") != today:
        fresh = _empty_daily_state()
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"daily_contract_state": fresh}},
        )
        return fresh
    # Defensive: add slugs introduced after the window opened (catalog growth).
    contracts = dict(state.get("contracts", {}))
    changed = False
    for c in DAILY_CONTRACTS:
        if c["slug"] not in contracts:
            contracts[c["slug"]] = {"progress": 0, "claimed": False, "claimed_at": None}
            changed = True
    if changed:
        state["contracts"] = contracts
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"daily_contract_state": state}},
        )
    return state


async def get_today_contracts(db, guild_id: str) -> dict:
    tg_level = await _get_contract_board_level(db, guild_id)
    if tg_level < 1:
        return {
            "contract_board_level": 0,
            "locked": True,
            "next_reset_at": _tomorrow_midnight_utc().isoformat(),
            "contracts": [],
        }
    state = await _ensure_daily_fresh(db, guild_id)
    # ROUND 6E — feature-gate filter so locked-feature contracts never
    # clutter the UI (e.g. raid daily appears only after war_room Lv1).
    unlocked = await _get_unlocked_structure_slugs(db, guild_id)
    out = []
    for defn in DAILY_CONTRACTS:
        if not _is_contract_actionable(defn, unlocked):
            continue
        s = state["contracts"].get(defn["slug"]) or {}
        progress = int(s.get("progress", 0))
        claimed = bool(s.get("claimed", False))
        completed = progress >= defn["objective_target"]
        out.append({
            "slug": defn["slug"],
            "display_key": defn["display_key"],
            "objective_type": defn["objective_type"],
            "objective_target": defn["objective_target"],
            "progress": progress,
            "reward_gold": defn["reward_gold"],
            "reward_materials": defn["reward_materials"],
            "reward_reputation": defn["reward_reputation"],
            "claimed": claimed,
            "claimed_at": s.get("claimed_at"),
            "completed": completed,
            "can_claim": completed and not claimed,
        })
    return {
        "contract_board_level": tg_level,
        "locked": False,
        "window_start_utc": state["window_start_utc"],
        "next_reset_at": _tomorrow_midnight_utc().isoformat(),
        "contracts": out,
    }


# ──────────────────────────────────────────────────────────────────────
# WEEKLY contracts — state + lazy rotation + claim
# ──────────────────────────────────────────────────────────────────────
def _empty_weekly_state(eligible_pool: list[dict] | None = None) -> dict:
    week_idx = _iso_week_index()
    if eligible_pool is None:
        active = select_active_weekly(week_idx)
    else:
        # ROUND 6E — gate-aware selection: rotate over the *eligible* subset
        # so a guild never sees fewer than WEEKLY_ACTIVE_COUNT entries when
        # the pool can still satisfy that floor.
        from app.contracts.catalog import WEEKLY_ACTIVE_COUNT
        n = len(eligible_pool)
        if n == 0:
            active = []
        else:
            active = [eligible_pool[(week_idx + i) % n]
                      for i in range(min(WEEKLY_ACTIVE_COUNT, n))]
    return {
        "rotation_week": _iso_week_key(),
        "rotation_week_index": week_idx,
        "active_slugs": [c["slug"] for c in active],
        "contracts": {c["slug"]: {"progress": 0, "claimed": False, "claimed_at": None,
                                  "completed_at": None}
                      for c in active},
    }


async def _ensure_weekly_fresh(db, guild_id: str) -> dict:
    week = _iso_week_key()
    g = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "weekly_contract_state": 1},
    )
    state = (g or {}).get("weekly_contract_state")
    if not state or state.get("rotation_week") != week:
        # ROUND 6E — filter the pool by guild's unlocked structures BEFORE
        # rotation, so we don't waste an active slot on a gated contract.
        unlocked = await _get_unlocked_structure_slugs(db, guild_id)
        from app.contracts.catalog import WEEKLY_CONTRACT_POOL
        eligible = [c for c in WEEKLY_CONTRACT_POOL
                    if _is_contract_actionable(c, unlocked)]
        fresh = _empty_weekly_state(eligible)
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"weekly_contract_state": fresh}},
        )
        return fresh
    return state


async def get_weekly_contracts(db, guild_id: str) -> dict:
    tg_level = await _get_contract_board_level(db, guild_id)
    if tg_level < 1:
        return {
            "contract_board_level": 0,
            "locked": True,
            "next_reset_at": _next_monday_utc().isoformat(),
            "contracts": [],
        }
    state = await _ensure_weekly_fresh(db, guild_id)
    # ROUND 6E — feature-gate filter (same as daily).
    unlocked = await _get_unlocked_structure_slugs(db, guild_id)
    out = []
    for slug in state.get("active_slugs", []):
        defn = WEEKLY_BY_SLUG.get(slug)
        if not defn:
            continue
        if not _is_contract_actionable(defn, unlocked):
            continue
        s = state["contracts"].get(slug) or {}
        progress = int(s.get("progress", 0))
        claimed = bool(s.get("claimed", False))
        completed = progress >= defn["objective_target"]
        out.append({
            "slug": slug,
            "display_key": defn["display_key"],
            "objective_type": defn["objective_type"],
            "objective_target": defn["objective_target"],
            "progress": progress,
            "reward_gold": defn["reward_gold"],
            "reward_materials": defn["reward_materials"],
            "reward_reputation": defn["reward_reputation"],
            "claimed": claimed,
            "claimed_at": s.get("claimed_at"),
            "completed": completed,
            "completed_at": s.get("completed_at"),
            "can_claim": completed and not claimed,
        })
    return {
        "contract_board_level": tg_level,
        "locked": False,
        "rotation_week": state["rotation_week"],
        "next_reset_at": _next_monday_utc().isoformat(),
        "contracts": out,
    }


# ──────────────────────────────────────────────────────────────────────
# MILESTONES — persistent, 3-tier progressive unlock, never reset
# ──────────────────────────────────────────────────────────────────────
def _empty_milestone_state() -> dict:
    return {
        "milestones": {
            m["slug"]: {"progress": 0, "completed": False, "completed_at": None,
                        "claimed": False, "claimed_at": None}
            for m in MILESTONES_ALL
        },
    }


async def _ensure_milestone_fresh(db, guild_id: str) -> dict:
    g = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "guild_milestone_state": 1},
    )
    state = (g or {}).get("guild_milestone_state")
    if not state:
        fresh = _empty_milestone_state()
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"guild_milestone_state": fresh}},
        )
        return fresh
    # Catalog growth — add new milestone slugs without resetting existing.
    ms = dict(state.get("milestones", {}))
    changed = False
    for m in MILESTONES_ALL:
        if m["slug"] not in ms:
            ms[m["slug"]] = {"progress": 0, "completed": False, "completed_at": None,
                             "claimed": False, "claimed_at": None}
            changed = True
    if changed:
        state["milestones"] = ms
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"guild_milestone_state": state}},
        )
    return state


def _tier_unlocked(state_milestones: dict, tier: int) -> bool:
    """A tier is unlocked iff every previous-tier milestone is `claimed`."""
    prev = TIER_UNLOCK_REQUIRES.get(tier)
    if prev is None:
        return True
    needed = (
        MILESTONES_TIER_1 if prev == 1
        else MILESTONES_TIER_2 if prev == 2
        else MILESTONES_TIER_3
    )
    if not needed:
        # Previous tier has no entries yet (placeholder) — we treat that
        # as "unlocked" for forward-compat with the empty Tier 2 placeholder.
        return True
    return all(
        (state_milestones.get(m["slug"]) or {}).get("claimed") is True
        for m in needed
    )


async def get_milestones(db, guild_id: str) -> dict:
    tg_level = await _get_contract_board_level(db, guild_id)
    if tg_level < 1:
        return {
            "contract_board_level": 0,
            "locked": True,
            "tiers": {1: False, 2: False, 3: False},
            "milestones": [],
        }
    state = await _ensure_milestone_fresh(db, guild_id)
    ms = state["milestones"]
    tiers = {t: _tier_unlocked(ms, t) for t in (1, 2, 3)}
    out = []
    for defn in MILESTONES_ALL:
        s = ms.get(defn["slug"]) or {}
        progress = int(s.get("progress", 0))
        completed = bool(s.get("completed", False))
        claimed = bool(s.get("claimed", False))
        out.append({
            "slug": defn["slug"],
            "tier": defn["tier"],
            "display_key": defn["display_key"],
            "objective_type": defn["objective_type"],
            "objective_target": defn["objective_target"],
            "progress": progress,
            "reward_gold": defn["reward_gold"],
            "reward_materials": defn["reward_materials"],
            "reward_reputation": defn["reward_reputation"],
            "completed": completed,
            "completed_at": s.get("completed_at"),
            "claimed": claimed,
            "claimed_at": s.get("claimed_at"),
            "tier_unlocked": tiers[defn["tier"]],
            "can_claim": completed and not claimed and tiers[defn["tier"]],
        })
    return {
        "contract_board_level": tg_level,
        "locked": False,
        "tiers": tiers,
        "milestones": out,
    }


# ──────────────────────────────────────────────────────────────────────
# CLAIM (atomic, idempotent — CAS on `claimed: False`)
# ──────────────────────────────────────────────────────────────────────
async def _award_reward(db, *, guild_id: str, reward: dict) -> None:
    """Apply gold + reputation to guild atomically; insert material rows."""
    inc: dict = {}
    gold = int(reward.get("reward_gold", 0) or 0)
    rep = int(reward.get("reward_reputation", 0) or 0)
    if gold:
        inc["gold"] = gold
    if rep:
        inc["reputation"] = rep
    if inc:
        await db.guilds.update_one({"id": guild_id}, {"$inc": inc})
    # Materials: append qty to existing rows or insert new rows.
    now_iso = _now_utc().isoformat()
    for mat in reward.get("reward_materials") or []:
        slug = mat.get("slug")
        qty = int(mat.get("qty") or 0)
        if not slug or qty <= 0:
            continue
        # Idempotency on materials is "best effort" — we just stack qty.
        existing = await db.inventory_items.find_one(
            {"guild_id": guild_id, "item_id": slug, "is_material": True},
            {"_id": 0, "id": 1, "quantity": 1},
        )
        if existing:
            await db.inventory_items.update_one(
                {"id": existing["id"]},
                {"$inc": {"quantity": qty}, "$set": {"updated_at": now_iso}},
            )
        else:
            await db.inventory_items.insert_one({
                "id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": slug,
                "quantity": qty,
                "acquired_at": now_iso,
                "is_material": True,
                "is_bound": True,
                "refinement_level": 0,
                "enchants": [],
                "affixes": [],
                "reroll_count": 0,
                "bound_to_adventurer_id": None,
                "bound_reason": None,
                "bound_at": None,
            })


async def _audit(db, event_type: str, *, actor_user_id: str | None,
                 guild_id: str, related_entity_id: str | None,
                 metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type=event_type,
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            source="contracts.claim",
            related_entity_id=related_entity_id,
            metadata=metadata,
        )
    except Exception:  # noqa: BLE001
        pass


async def claim_daily_contract(db, *, guild_id: str, actor_user_id: str,
                               slug: str) -> dict:
    defn = DAILY_BY_SLUG.get(slug)
    if not defn:
        raise _err("contracts.unknown_slug", "Contratto sconosciuto.", status=404)
    if await _get_contract_board_level(db, guild_id) < 1:
        raise _err("contracts.locked", "Sblocca prima la Bacheca Contratti.")
    today = _today_utc_date()
    await _ensure_daily_fresh(db, guild_id)
    updated = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            "daily_contract_state.window_start_utc": today,
            f"daily_contract_state.contracts.{slug}.claimed": False,
            f"daily_contract_state.contracts.{slug}.progress": {
                "$gte": defn["objective_target"]
            },
        },
        {
            "$set": {
                f"daily_contract_state.contracts.{slug}.claimed": True,
                f"daily_contract_state.contracts.{slug}.claimed_at": _now_utc().isoformat(),
            },
        },
        projection={"_id": 0, "id": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise _err("contracts.not_claimable",
                   "Contratto non reclamabile (non completato o già claimato).")
    await _award_reward(db, guild_id=guild_id, reward=defn)
    await _audit(db, "contract_claimed",
                 actor_user_id=actor_user_id, guild_id=guild_id,
                 related_entity_id=None,
                 metadata={"scope": "daily", "slug": slug,
                           "reward_gold": defn["reward_gold"],
                           "reward_reputation": defn["reward_reputation"]})
    # ROUND 13b — seasonal `contracts_completed` (idempotent via the
    # atomic `claimed:False → True` CAS above; claim cannot fire twice).
    try:
        from app.seasons.season_stats import increment_seasonal_stat
        await increment_seasonal_stat(
            db, guild_id=guild_id, field="contracts_completed", delta=1,
            source="contract_daily", source_id=f"daily:{slug}:{today}",
        )
    except Exception:
        pass
    return {"scope": "daily", "slug": slug, "claimed": True,
            "reward": {"gold": defn["reward_gold"],
                       "materials": defn["reward_materials"],
                       "reputation": defn["reward_reputation"]}}


async def claim_weekly_contract(db, *, guild_id: str, actor_user_id: str,
                                slug: str) -> dict:
    defn = WEEKLY_BY_SLUG.get(slug)
    if not defn:
        raise _err("contracts.unknown_slug", "Contratto sconosciuto.", status=404)
    if await _get_contract_board_level(db, guild_id) < 1:
        raise _err("contracts.locked", "Sblocca prima la Bacheca Contratti.")
    week = _iso_week_key()
    state = await _ensure_weekly_fresh(db, guild_id)
    if slug not in (state.get("active_slugs") or []):
        raise _err("contracts.not_active_this_week",
                   "Contratto non attivo per questa settimana.")
    updated = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            "weekly_contract_state.rotation_week": week,
            f"weekly_contract_state.contracts.{slug}.claimed": False,
            f"weekly_contract_state.contracts.{slug}.progress": {
                "$gte": defn["objective_target"]
            },
        },
        {
            "$set": {
                f"weekly_contract_state.contracts.{slug}.claimed": True,
                f"weekly_contract_state.contracts.{slug}.claimed_at": _now_utc().isoformat(),
            },
        },
        projection={"_id": 0, "id": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise _err("contracts.not_claimable",
                   "Contratto non reclamabile (non completato o già claimato).")
    await _award_reward(db, guild_id=guild_id, reward=defn)
    await _audit(db, "contract_claimed",
                 actor_user_id=actor_user_id, guild_id=guild_id,
                 related_entity_id=None,
                 metadata={"scope": "weekly", "slug": slug,
                           "reward_gold": defn["reward_gold"],
                           "reward_reputation": defn["reward_reputation"]})
    # ROUND 13b — seasonal `contracts_completed` (idempotent via claimed CAS).
    try:
        from app.seasons.season_stats import increment_seasonal_stat
        await increment_seasonal_stat(
            db, guild_id=guild_id, field="contracts_completed", delta=1,
            source="contract_weekly", source_id=f"weekly:{slug}:{week}",
        )
    except Exception:
        pass
    return {"scope": "weekly", "slug": slug, "claimed": True,
            "reward": {"gold": defn["reward_gold"],
                       "materials": defn["reward_materials"],
                       "reputation": defn["reward_reputation"]}}


async def claim_milestone(db, *, guild_id: str, actor_user_id: str,
                          slug: str) -> dict:
    defn = MILESTONES_BY_SLUG.get(slug)
    if not defn:
        raise _err("contracts.unknown_slug", "Milestone sconosciuta.", status=404)
    if await _get_contract_board_level(db, guild_id) < 1:
        raise _err("contracts.locked", "Sblocca prima la Bacheca Contratti.")
    state = await _ensure_milestone_fresh(db, guild_id)
    if not _tier_unlocked(state["milestones"], defn["tier"]):
        raise _err("contracts.tier_locked",
                   f"Completa prima i milestone del Tier {defn['tier']-1}.")
    updated = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            f"guild_milestone_state.milestones.{slug}.claimed": False,
            f"guild_milestone_state.milestones.{slug}.progress": {
                "$gte": defn["objective_target"]
            },
        },
        {
            "$set": {
                f"guild_milestone_state.milestones.{slug}.claimed": True,
                f"guild_milestone_state.milestones.{slug}.completed": True,
                f"guild_milestone_state.milestones.{slug}.claimed_at": _now_utc().isoformat(),
            },
        },
        projection={"_id": 0, "id": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise _err("contracts.not_claimable",
                   "Milestone non reclamabile (non completata o già claimata).")
    await _award_reward(db, guild_id=guild_id, reward=defn)
    await _audit(db, "guild_milestone_claimed",
                 actor_user_id=actor_user_id, guild_id=guild_id,
                 related_entity_id=slug,
                 metadata={"slug": slug, "tier": defn["tier"],
                           "reward_gold": defn["reward_gold"],
                           "reward_reputation": defn["reward_reputation"]})
    # ROUND 13b — seasonal `contracts_completed` (idempotent via claimed CAS).
    try:
        from app.seasons.season_stats import increment_seasonal_stat
        await increment_seasonal_stat(
            db, guild_id=guild_id, field="contracts_completed", delta=1,
            source="contract_milestone", source_id=f"milestone:{slug}",
        )
    except Exception:
        pass
    return {"scope": "milestone", "slug": slug, "claimed": True,
            "reward": {"gold": defn["reward_gold"],
                       "materials": defn["reward_materials"],
                       "reputation": defn["reward_reputation"]}}


# ──────────────────────────────────────────────────────────────────────
# Producer hook — fan-out increment over daily + weekly + milestones.
# Called from 6 business modules. NEVER raises. NEVER blocks the parent
# business write — failures only log.
# ──────────────────────────────────────────────────────────────────────
async def increment_contract_progress(
    db, guild_id: str, objective_type: str, amount: int = 1,
) -> None:
    """Single fan-out point. Increments daily + weekly + milestone counters
    where `objective_type` matches. Best-effort; logs but never raises.

    Daily / weekly skip the increment if the Contract Board is locked (no
    point in tracking progress on a feature the player can't yet access).
    Milestones tick regardless — they're persistent and the unlock gate
    only blocks claiming, not progress accumulation.
    """
    if objective_type not in VALID_OBJECTIVE_TYPES:
        logger.warning("contracts.increment: unknown objective_type=%s", objective_type)
        return
    if amount <= 0:
        return
    try:
        cb_level = await _get_contract_board_level(db, guild_id)
        # 1) Daily — only if board unlocked and within the current window
        if cb_level >= 1:
            today = _today_utc_date()
            for c in DAILY_CONTRACTS:
                if c["objective_type"] != objective_type:
                    continue
                await db.guilds.update_one(
                    {
                        "id": guild_id,
                        "daily_contract_state.window_start_utc": today,
                        f"daily_contract_state.contracts.{c['slug']}.claimed": False,
                    },
                    {"$inc": {
                        f"daily_contract_state.contracts.{c['slug']}.progress": amount,
                    }},
                )
        # 2) Weekly — only if board unlocked and within the current rotation
        if cb_level >= 1:
            week = _iso_week_key()
            for c in (WEEKLY_BY_SLUG.get(s)
                      for s in (
                          (await db.guilds.find_one(
                              {"id": guild_id},
                              {"_id": 0, "weekly_contract_state.active_slugs": 1},
                          )) or {}
                      ).get("weekly_contract_state", {}).get("active_slugs", [])):
                if not c or c["objective_type"] != objective_type:
                    continue
                await db.guilds.update_one(
                    {
                        "id": guild_id,
                        "weekly_contract_state.rotation_week": week,
                        f"weekly_contract_state.contracts.{c['slug']}.claimed": False,
                    },
                    {"$inc": {
                        f"weekly_contract_state.contracts.{c['slug']}.progress": amount,
                    }},
                )
        # 3) Milestones — always (persistent achievements)
        await _ensure_milestone_fresh(db, guild_id)
        for m in MILESTONES_ALL:
            if m["objective_type"] != objective_type:
                continue
            # Increment, then check if we just crossed the threshold so we
            # can stamp `completed_at` + emit the public chronicle event.
            after = await db.guilds.find_one_and_update(
                {
                    "id": guild_id,
                    f"guild_milestone_state.milestones.{m['slug']}.claimed": False,
                    f"guild_milestone_state.milestones.{m['slug']}.completed": False,
                },
                {"$inc": {
                    f"guild_milestone_state.milestones.{m['slug']}.progress": amount,
                }},
                projection={
                    "_id": 0,
                    f"guild_milestone_state.milestones.{m['slug']}": 1,
                },
                return_document=ReturnDocument.AFTER,
            )
            if not after:
                continue
            ms = (after.get("guild_milestone_state") or {}).get("milestones", {})
            cur = ms.get(m["slug"]) or {}
            if int(cur.get("progress", 0)) >= m["objective_target"] and not cur.get("completed"):
                await db.guilds.update_one(
                    {
                        "id": guild_id,
                        f"guild_milestone_state.milestones.{m['slug']}.completed": False,
                    },
                    {"$set": {
                        f"guild_milestone_state.milestones.{m['slug']}.completed": True,
                        f"guild_milestone_state.milestones.{m['slug']}.completed_at": _now_utc().isoformat(),
                    }},
                )
                await _audit(db, "guild_milestone_reached",
                             actor_user_id=None, guild_id=guild_id,
                             related_entity_id=m["slug"],
                             metadata={"slug": m["slug"], "tier": m["tier"]})
    except Exception as exc:  # noqa: BLE001
        logger.warning("contracts.increment failed: %s", exc)


__all__ = [
    "CONTRACT_BOARD_SLUG",
    "get_today_contracts",
    "get_weekly_contracts",
    "get_milestones",
    "claim_daily_contract",
    "claim_weekly_contract",
    "claim_milestone",
    "increment_contract_progress",
]
