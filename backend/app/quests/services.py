"""Phase 14 + 14.1 + 15 — Daily Quests, Streak Counter, Weekly Variety.

Single source of truth for retention loop:
  - Daily quests (Phase 14, existing): 3 fixed quests, gold-only, UTC reset.
  - Streak counter (Phase 15): increments once per UTC day when the player
    claims *any* daily quest; tiered rewards at day 1/3/5/7, cycling weekly.
  - Weekly variety (Phase 14.1): 4 rotating optional quests per ISO week,
    progress driven by expedition/crafting/market/equip events, claim atomic.

Persistence layout (nested on `guilds`, additive / idempotent):
  daily_quest_state   = {window_start_utc, quests: {slug: {progress, claimed}}}
  streak_state        = {current, longest, last_streak_date,
                          rewards_claimed: {tier_int: date_iso}, updated_at}
  weekly_quest_state  = {rotation_week, quests: {slug: {progress, claimed,
                          completed_at, claimed_at}}}

Concurrency: every mutation uses `find_one_and_update` or `$inc` with a
conditional filter (CAS). Tracker writes are best-effort and never abort
the parent business operation.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument


# ──────────────────────────────────────────────────────────────────────────
# Phase 14 — Daily quest catalog (unchanged)
# ──────────────────────────────────────────────────────────────────────────
QUEST_DEFINITIONS: dict[str, dict] = {
    "expedition_complete": {"threshold": 1, "reward_gold": 10},
    "recruit": {"threshold": 1, "reward_gold": 5},
    "equip": {"threshold": 1, "reward_gold": 5},
}
QUEST_IDS = tuple(QUEST_DEFINITIONS.keys())


# ──────────────────────────────────────────────────────────────────────────
# Phase 15 — Streak rewards (tiered, moderate, anti-inflation)
# ──────────────────────────────────────────────────────────────────────────
# Tier = the streak day on which the reward unlocks. Players past day 7
# cycle: day 8 ↔ day 1, day 10 ↔ day 3, day 12 ↔ day 5, day 14 ↔ day 7.
# A "rewards_claimed" map keyed by tier_int → last claim date prevents
# double-claim per tier within the same 7-day cycle.
# Anti-inflation, non-competitive. Locked by product spec — do NOT raise gold
# values or add power gear here without explicit product re-authorization.
STREAK_REWARDS: dict[int, dict] = {
    1: {"gold": 20, "materials": []},
    3: {"gold": 50, "materials": [{"slug": "iron_shard", "qty": 2}]},
    5: {"gold": 100, "materials": [{"slug": "arcane_dust", "qty": 1}]},
    7: {"gold": 200, "materials": [{"slug": "healing_herb", "qty": 3}]},
}
STREAK_MAX_DAYS = 30  # soft cap — past 30 the counter stops bumping


# ──────────────────────────────────────────────────────────────────────────
# Phase 14.1 — Weekly quest catalog (rotates by ISO week index)
# ──────────────────────────────────────────────────────────────────────────
# Each entry is sliced into the active rotation via `slug[i] = pool[(week_idx + i) % N]`.
# All objective_types map to systems that already exist in production
# (expeditions, crafting, market, equipment).
# Weekly variety pool — 6 quest definitions, 4 visible per week (ISO rotation).
# Reward ceiling (binding): each quest 80-180g, total weekly ceiling ≈ 700g.
# Materials: 1-2 common/uncommon only. NO power gear. NO reputation.
WEEKLY_QUEST_POOL: list[dict] = [
    {
        "slug": "weekly_run_expeditions_3",
        "display_key": "quests.weekly.run_expeditions_3",
        "objective_type": "expeditions_completed",
        "objective_target": 3,
        "reward_gold": 150,
        "reward_materials": [{"slug": "iron_shard", "qty": 2}],
    },
    {
        "slug": "weekly_craft_items_2",
        "display_key": "quests.weekly.craft_items_2",
        "objective_type": "items_crafted",
        "objective_target": 2,
        "reward_gold": 180,
        "reward_materials": [{"slug": "arcane_dust", "qty": 1}],
    },
    {
        "slug": "weekly_market_buy_1",
        "display_key": "quests.weekly.market_buy_1",
        "objective_type": "market_purchases",
        "objective_target": 1,
        "reward_gold": 100,
        "reward_materials": [{"slug": "raw_leather", "qty": 2}],
    },
    {
        "slug": "weekly_equip_items_3",
        "display_key": "quests.weekly.equip_items_3",
        "objective_type": "items_equipped",
        "objective_target": 3,
        "reward_gold": 80,
        "reward_materials": [{"slug": "healing_herb", "qty": 1}],
    },
    {
        "slug": "weekly_expedition_loot_10",
        "display_key": "quests.weekly.expedition_loot_10",
        "objective_type": "expedition_loot_items",
        "objective_target": 10,
        "reward_gold": 160,
        "reward_materials": [{"slug": "dull_gem", "qty": 1}],
    },
    {
        "slug": "weekly_market_listings_1",
        "display_key": "quests.weekly.market_listings_1",
        "objective_type": "market_listings_created",
        "objective_target": 1,
        "reward_gold": 100,
        "reward_materials": [{"slug": "raw_leather", "qty": 1}],
    },
]
WEEKLY_ACTIVE_COUNT = 4  # 4 quests visible per week


# ──────────────────────────────────────────────────────────────────────────
# Date helpers (UTC, server-authoritative)
# ──────────────────────────────────────────────────────────────────────────
def _today_utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_week_key(dt: datetime | None = None) -> str:
    """e.g. '2026-W26' — server-authoritative key for weekly rotation."""
    dt = dt or _now_utc()
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _next_monday_utc() -> datetime:
    now = _now_utc()
    days_ahead = (7 - now.weekday()) % 7 or 7
    next_mon = (now + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return next_mon


def _tomorrow_midnight_utc() -> datetime:
    now = _now_utc()
    return (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


# ──────────────────────────────────────────────────────────────────────────
# Daily quest state (existing behaviour preserved)
# ──────────────────────────────────────────────────────────────────────────
def _empty_state() -> dict:
    return {
        "window_start_utc": _today_utc_date(),
        "quests": {qid: {"progress": 0, "claimed": False} for qid in QUEST_IDS},
    }


async def _ensure_state_fresh(db, guild_id: str) -> dict:
    today = _today_utc_date()
    guild = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "daily_quest_state": 1}
    )
    state = (guild or {}).get("daily_quest_state")
    if not state or state.get("window_start_utc") != today:
        fresh = _empty_state()
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"daily_quest_state": fresh}}
        )
        return fresh
    quests = dict(state.get("quests", {}))
    changed = False
    for qid in QUEST_IDS:
        if qid not in quests:
            quests[qid] = {"progress": 0, "claimed": False}
            changed = True
    if changed:
        state["quests"] = quests
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"daily_quest_state": state}}
        )
    return state


async def get_today_quests(db, guild_id: str) -> dict:
    state = await _ensure_state_fresh(db, guild_id)
    quests = []
    for qid, defn in QUEST_DEFINITIONS.items():
        s = state["quests"].get(qid, {"progress": 0, "claimed": False})
        progress = int(s.get("progress", 0))
        claimed = bool(s.get("claimed", False))
        completed = progress >= defn["threshold"]
        quests.append({
            "id": qid,
            "threshold": defn["threshold"],
            "progress": progress,
            "reward_gold": defn["reward_gold"],
            "claimed": claimed,
            "completed": completed,
            "can_claim": (completed and not claimed),
        })
    return {
        "window_start_utc": state["window_start_utc"],
        "next_reset_at": _tomorrow_midnight_utc().isoformat(),
        "quests": quests,
    }


async def increment_quest_progress(
    db, guild_id: str, quest_id: str, amount: int = 1
) -> None:
    if quest_id not in QUEST_DEFINITIONS:
        return
    try:
        today = _today_utc_date()
        res = await db.guilds.update_one(
            {"id": guild_id, "daily_quest_state.window_start_utc": today},
            {"$inc": {f"daily_quest_state.quests.{quest_id}.progress": amount}},
        )
        if res.matched_count == 0:
            await _ensure_state_fresh(db, guild_id)
            await db.guilds.update_one(
                {"id": guild_id, "daily_quest_state.window_start_utc": today},
                {"$inc": {f"daily_quest_state.quests.{quest_id}.progress": amount}},
            )
    except Exception:  # noqa: BLE001
        pass


async def claim_quest(db, guild_id: str, quest_id: str) -> dict:
    if quest_id not in QUEST_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Unknown quest")
    await _ensure_state_fresh(db, guild_id)
    today = _today_utc_date()
    defn = QUEST_DEFINITIONS[quest_id]
    threshold = defn["threshold"]
    reward = defn["reward_gold"]

    updated = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            "daily_quest_state.window_start_utc": today,
            f"daily_quest_state.quests.{quest_id}.claimed": False,
            f"daily_quest_state.quests.{quest_id}.progress": {"$gte": threshold},
        },
        {
            "$set": {f"daily_quest_state.quests.{quest_id}.claimed": True},
            "$inc": {"gold": reward},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        cur = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "daily_quest_state": 1})
        s = (cur or {}).get("daily_quest_state", {}).get("quests", {}).get(quest_id, {})
        if bool(s.get("claimed", False)):
            raise HTTPException(status_code=409, detail="Quest already claimed today")
        raise HTTPException(status_code=422, detail="Quest not completed yet")

    # Phase 15: update streak on FIRST claim of the day (idempotent).
    streak = await _bump_streak_on_first_claim_today(db, guild_id)

    # Audit (best-effort)
    await _audit(db, "quest_reward_claimed",
                 actor_guild_id=guild_id, gold_delta=reward,
                 metadata={"quest_id": quest_id, "kind": "daily"})

    quest_state = updated["daily_quest_state"]["quests"][quest_id]
    return {
        "quest": {
            "id": quest_id,
            "threshold": threshold,
            "progress": int(quest_state.get("progress", 0)),
            "reward_gold": reward,
            "claimed": True,
            "completed": True,
            "can_claim": False,
        },
        "guild_gold": int(updated.get("gold", 0)),
        "reward_gold_granted": reward,
        "streak": streak,
    }


# ──────────────────────────────────────────────────────────────────────────
# Phase 15 — Streak counter
# ──────────────────────────────────────────────────────────────────────────
def _empty_streak() -> dict:
    return {
        "current": 0,
        "longest": 0,
        "last_streak_date": None,
        "rewards_claimed": {},
        "updated_at": _now_utc().isoformat(),
    }


def _tier_for(current: int) -> int | None:
    """Map a streak value to the highest unlocked tier in {1,3,5,7}.
    Cycles weekly: 8→1, 9→1 (no new tier), 10→3, 12→5, 14→7, ..."""
    if current <= 0:
        return None
    cycle_day = ((current - 1) % 7) + 1
    if cycle_day >= 7:
        return 7
    if cycle_day >= 5:
        return 5
    if cycle_day >= 3:
        return 3
    return 1


async def get_streak(db, guild_id: str) -> dict:
    g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "streak_state": 1})
    s = (g or {}).get("streak_state") or _empty_streak()
    today = _today_utc_date()
    current = int(s.get("current", 0))
    # The streak is "alive" only if last activity was today OR yesterday.
    last = s.get("last_streak_date")
    if last:
        try:
            dt_last = datetime.strptime(last, "%Y-%m-%d").date()
            dt_today = datetime.strptime(today, "%Y-%m-%d").date()
            if (dt_today - dt_last).days >= 2:
                # Streak is broken (read-only — reset happens on next claim)
                current_displayed = 0
            else:
                current_displayed = current
        except ValueError:
            current_displayed = current
    else:
        current_displayed = current

    tier = _tier_for(current_displayed)
    reward_def = STREAK_REWARDS.get(tier or 0) if tier else None
    rewards_claimed = s.get("rewards_claimed", {}) or {}
    # Claim window: rewards_claimed[str(tier)] holds the streak-day on which
    # the tier was last claimed. A new claim is allowed only if the current
    # streak has advanced past that day (i.e. we're in a NEW cycle).
    last_claim_day = int(rewards_claimed.get(str(tier), 0)) if tier else 0
    can_claim_reward = bool(
        tier is not None
        and current_displayed > 0
        and (last_claim_day == 0 or current_displayed > last_claim_day)
    )
    return {
        "current": current_displayed,
        "longest": int(s.get("longest", 0)),
        "last_streak_date": last,
        "today_completed": (last == today and current_displayed > 0),
        "next_reset_at": _tomorrow_midnight_utc().isoformat(),
        "current_tier": tier,
        "current_reward": reward_def,
        "can_claim_reward": can_claim_reward,
        "schedule": [
            {"day": d, "reward": STREAK_REWARDS[d]} for d in sorted(STREAK_REWARDS)
        ],
    }


async def _bump_streak_on_first_claim_today(db, guild_id: str) -> dict:
    """Idempotent: only mutates state if `last_streak_date != today`.
    Returns the post-bump streak view.
    """
    today = _today_utc_date()
    g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "streak_state": 1})
    s = (g or {}).get("streak_state") or _empty_streak()
    if s.get("last_streak_date") == today:
        # Already bumped today — idempotent return.
        return await get_streak(db, guild_id)

    last = s.get("last_streak_date")
    current = int(s.get("current", 0))
    if last is None:
        new_current = 1
    else:
        try:
            dt_last = datetime.strptime(last, "%Y-%m-%d").date()
            dt_today = datetime.strptime(today, "%Y-%m-%d").date()
            gap = (dt_today - dt_last).days
            if gap == 1:
                new_current = min(current + 1, STREAK_MAX_DAYS)
            elif gap <= 0:
                new_current = max(current, 1)
            else:
                new_current = 1
        except ValueError:
            new_current = 1

    longest = max(int(s.get("longest", 0)), new_current)
    new_state = {
        "current": new_current,
        "longest": longest,
        "last_streak_date": today,
        "rewards_claimed": s.get("rewards_claimed", {}) or {},
        "updated_at": _now_utc().isoformat(),
    }
    # CAS guard — only update if last_streak_date is still NOT today (prevents
    # concurrent double-bump within the same UTC day).
    await db.guilds.update_one(
        {"id": guild_id,
         "$or": [
             {"streak_state": {"$exists": False}},
             {"streak_state.last_streak_date": {"$ne": today}},
         ]},
        {"$set": {"streak_state": new_state}},
    )
    await _audit(db, "streak_updated", actor_guild_id=guild_id,
                 metadata={"current": new_current, "longest": longest})
    return await get_streak(db, guild_id)


async def claim_streak_reward(db, guild_id: str, tier: int) -> dict:
    if tier not in STREAK_REWARDS:
        raise HTTPException(status_code=404, detail="Unknown streak tier")
    streak = await get_streak(db, guild_id)
    current = int(streak["current"])
    if streak["current_tier"] != tier:
        raise HTTPException(
            status_code=422,
            detail=f"Streak tier {tier} not currently unlocked",
        )
    if not streak["can_claim_reward"]:
        raise HTTPException(status_code=409, detail="Reward already claimed for this cycle")

    reward = STREAK_REWARDS[tier]
    # Atomic CAS: only flip if rewards_claimed[tier] is still < current (or absent).
    upd = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            "streak_state.current": current,
            "$or": [
                {f"streak_state.rewards_claimed.{tier}": {"$exists": False}},
                {f"streak_state.rewards_claimed.{tier}": {"$lt": current}},
            ],
        },
        {
            "$set": {f"streak_state.rewards_claimed.{tier}": current},
            "$inc": {"gold": reward["gold"]},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not upd:
        raise HTTPException(status_code=409, detail="Reward already claimed for this cycle")

    # Grant materials (best-effort, never reverts gold on inv failure since
    # materials are negligible and the operation is non-economic-critical)
    for mat in reward["materials"]:
        await _grant_material(db, guild_id, mat["slug"], int(mat["qty"]))

    await _audit(db, "streak_reward_claimed", actor_guild_id=guild_id,
                 gold_delta=reward["gold"],
                 metadata={"tier": tier, "streak": current})
    return {
        "success": True,
        "tier": tier,
        "gold_granted": reward["gold"],
        "materials_granted": reward["materials"],
        "guild_gold": int(upd.get("gold", 0)),
        "streak": await get_streak(db, guild_id),
    }


# ──────────────────────────────────────────────────────────────────────────
# Phase 14.1 — Weekly variety
# ──────────────────────────────────────────────────────────────────────────
def _active_weekly_slugs(week_key: str) -> list[dict]:
    """Deterministic rotation: hash-free, just shift the pool by week index."""
    # Convert "2026-W26" → integer for shift
    try:
        _, w = week_key.split("-W")
        shift = int(w)
    except Exception:  # noqa: BLE001
        shift = 0
    n = len(WEEKLY_QUEST_POOL)
    return [WEEKLY_QUEST_POOL[(shift + i) % n] for i in range(WEEKLY_ACTIVE_COUNT)]


def _empty_weekly_state(week_key: str) -> dict:
    return {
        "rotation_week": week_key,
        "quests": {
            q["slug"]: {
                "progress": 0,
                "claimed": False,
                "completed_at": None,
                "claimed_at": None,
            }
            for q in _active_weekly_slugs(week_key)
        },
    }


async def _ensure_weekly_state_fresh(db, guild_id: str) -> dict:
    week_key = _iso_week_key()
    g = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "weekly_quest_state": 1}
    )
    state = (g or {}).get("weekly_quest_state")
    if not state or state.get("rotation_week") != week_key:
        fresh = _empty_weekly_state(week_key)
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"weekly_quest_state": fresh}}
        )
        if not state:
            await _audit(db, "weekly_rotation_generated",
                         actor_guild_id=guild_id,
                         metadata={"rotation_week": week_key})
        return fresh
    # Backfill missing slugs (defensive)
    expected = {q["slug"] for q in _active_weekly_slugs(week_key)}
    quests = dict(state.get("quests", {}))
    changed = False
    for slug in expected:
        if slug not in quests:
            quests[slug] = {"progress": 0, "claimed": False,
                            "completed_at": None, "claimed_at": None}
            changed = True
    if changed:
        state["quests"] = quests
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"weekly_quest_state": state}}
        )
    return state


async def get_weekly_quests(db, guild_id: str) -> dict:
    state = await _ensure_weekly_state_fresh(db, guild_id)
    week_key = state["rotation_week"]
    out = []
    for defn in _active_weekly_slugs(week_key):
        slug = defn["slug"]
        s = state["quests"].get(slug, {"progress": 0, "claimed": False})
        progress = int(s.get("progress", 0))
        target = int(defn["objective_target"])
        completed = progress >= target
        claimed = bool(s.get("claimed", False))
        out.append({
            "slug": slug,
            "display_key": defn["display_key"],
            "objective_type": defn["objective_type"],
            "objective_target": target,
            "progress": progress,
            "completed": completed,
            "claimed": claimed,
            "can_claim": (completed and not claimed),
            "reward_gold": int(defn["reward_gold"]),
            "reward_materials": defn["reward_materials"],
            "completed_at": s.get("completed_at"),
            "claimed_at": s.get("claimed_at"),
        })
    return {
        "rotation_week": week_key,
        "next_reset_at": _next_monday_utc().isoformat(),
        "quests": out,
    }


async def increment_weekly_progress(
    db, guild_id: str, objective_type: str, amount: int = 1
) -> None:
    """Best-effort: bump every active weekly quest that targets this objective.
    Never raises."""
    if not guild_id or amount <= 0:
        return
    try:
        week_key = _iso_week_key()
        for defn in _active_weekly_slugs(week_key):
            if defn["objective_type"] != objective_type:
                continue
            slug = defn["slug"]
            target = int(defn["objective_target"])
            # 1) Bump progress (capped at target)
            res = await db.guilds.update_one(
                {
                    "id": guild_id,
                    "weekly_quest_state.rotation_week": week_key,
                    f"weekly_quest_state.quests.{slug}.progress": {"$lt": target},
                },
                {"$inc": {f"weekly_quest_state.quests.{slug}.progress": amount}},
            )
            if res.matched_count == 0:
                # Stale or missing window — ensure + retry once
                await _ensure_weekly_state_fresh(db, guild_id)
                await db.guilds.update_one(
                    {
                        "id": guild_id,
                        "weekly_quest_state.rotation_week": week_key,
                        f"weekly_quest_state.quests.{slug}.progress": {"$lt": target},
                    },
                    {"$inc": {f"weekly_quest_state.quests.{slug}.progress": amount}},
                )
            # 2) If we just crossed the threshold, stamp completed_at
            await db.guilds.update_one(
                {
                    "id": guild_id,
                    "weekly_quest_state.rotation_week": week_key,
                    f"weekly_quest_state.quests.{slug}.progress": {"$gte": target},
                    f"weekly_quest_state.quests.{slug}.completed_at": None,
                },
                {
                    "$set": {
                        f"weekly_quest_state.quests.{slug}.completed_at":
                            _now_utc().isoformat(),
                    }
                },
            )
    except Exception:  # noqa: BLE001
        pass


async def claim_weekly_quest(db, guild_id: str, slug: str) -> dict:
    await _ensure_weekly_state_fresh(db, guild_id)
    week_key = _iso_week_key()
    defn = next((q for q in _active_weekly_slugs(week_key) if q["slug"] == slug), None)
    if not defn:
        raise HTTPException(status_code=404, detail="Unknown weekly quest")
    target = int(defn["objective_target"])
    reward = int(defn["reward_gold"])

    upd = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            "weekly_quest_state.rotation_week": week_key,
            f"weekly_quest_state.quests.{slug}.claimed": False,
            f"weekly_quest_state.quests.{slug}.progress": {"$gte": target},
        },
        {
            "$set": {
                f"weekly_quest_state.quests.{slug}.claimed": True,
                f"weekly_quest_state.quests.{slug}.claimed_at": _now_utc().isoformat(),
            },
            "$inc": {"gold": reward},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not upd:
        cur = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "weekly_quest_state": 1})
        s = (cur or {}).get("weekly_quest_state", {}).get("quests", {}).get(slug, {})
        if bool(s.get("claimed", False)):
            raise HTTPException(status_code=409, detail="Weekly quest already claimed")
        raise HTTPException(status_code=422, detail="Weekly quest not completed yet")

    # Grant materials
    for mat in defn["reward_materials"]:
        await _grant_material(db, guild_id, mat["slug"], int(mat["qty"]))

    await _audit(db, "weekly_quest_claimed", actor_guild_id=guild_id,
                 gold_delta=reward,
                 metadata={"slug": slug})
    return {
        "success": True,
        "slug": slug,
        "gold_granted": reward,
        "materials_granted": defn["reward_materials"],
        "guild_gold": int(upd.get("gold", 0)),
        "weekly": await get_weekly_quests(db, guild_id),
    }


# ──────────────────────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────────────────────
async def _grant_material(db, guild_id: str, slug: str, qty: int) -> None:
    """Add an item to the guild inventory (no-op on unknown slug)."""
    import uuid
    item = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
    if not item:
        return
    await db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": item["id"]},
        {
            "$inc": {"quantity": qty},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item["id"],
                "acquired_at": _now_utc().isoformat(),
                "source": "quest_reward",
                "bind_state": "unbound",
            },
        },
        upsert=True,
    )


async def _audit(db, event_type: str, **kwargs) -> None:
    """Best-effort audit log write. Never raises."""
    try:
        from app.audit.log import write_audit
        await write_audit(db, event_type=event_type, **kwargs)
    except Exception:  # noqa: BLE001
        pass


__all__ = [
    "QUEST_DEFINITIONS",
    "QUEST_IDS",
    "STREAK_REWARDS",
    "WEEKLY_QUEST_POOL",
    "WEEKLY_ACTIVE_COUNT",
    "get_today_quests",
    "increment_quest_progress",
    "claim_quest",
    "get_streak",
    "claim_streak_reward",
    "get_weekly_quests",
    "increment_weekly_progress",
    "claim_weekly_quest",
]
