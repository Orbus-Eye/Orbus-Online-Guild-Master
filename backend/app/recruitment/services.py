"""Recruitment services (Phase 5.5c.3 + Phase 11.2 refresh limit).

Phase 11.2 adds a daily refresh limit:
- 3 free refreshes per UTC day per guild
- Beyond free: paid scaling 10g / 20g / 30g (cap)
- Window resets on UTC date change (lazy)
- GET /candidates returns persisted offer without consuming any refresh
- POST /refresh forces a new roll, atomically applies limit + cost
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.shared.constants import (
    FIRST_NAMES,
    LAST_NAMES,
    OFFER_TTL_MINUTES,
    RARITY_BONUS,
    RARITY_WEIGHTS,
    RECRUITMENT_CANDIDATES_PER_OFFER,
    RECRUITMENT_COST_GOLD,
)


_rng = secrets.SystemRandom()


# Phase 11.2 refresh policy
FREE_REFRESHES_PER_DAY = 3
PAID_REFRESH_PRICES = [10, 20, 30]  # 1st paid, 2nd paid, 3rd+ paid (cap)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _today_utc_start() -> datetime:
    n = utc_now()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def _tomorrow_utc_start() -> datetime:
    return _today_utc_start() + timedelta(days=1)


def _next_refresh_cost(paid_count: int) -> int:
    if paid_count <= 0:
        return PAID_REFRESH_PRICES[0]
    if paid_count >= len(PAID_REFRESH_PRICES):
        return PAID_REFRESH_PRICES[-1]
    return PAID_REFRESH_PRICES[paid_count]


def _refresh_state(guild: dict) -> tuple[int, int, datetime, bool]:
    """Return (total_count_today, paid_count_today, window_start_utc, needs_reset).

    `needs_reset=True` means the stored window is missing OR predates today UTC
    — callers must roll the counters back to (0, 0) and treat the next refresh
    as the first one of a new day. The CAS match in `refresh_candidates_for_guild`
    branches on this flag so a fresh guild (no field yet) matches via `$exists:False`.
    """
    today = _today_utc_start()
    window_raw = guild.get("recruitment_refresh_window_start_utc")
    if not window_raw:
        return (0, 0, today, True)
    try:
        window_dt = datetime.fromisoformat(window_raw)
    except Exception:
        return (0, 0, today, True)
    if window_dt < today:
        return (0, 0, today, True)
    total = int(guild.get("recruitment_refresh_count_today", 0))
    paid = int(guild.get("recruitment_paid_refresh_count_today", 0))
    return (total, paid, window_dt, False)


def refresh_status_payload(guild: dict) -> dict:
    """Public refresh-state shape (added to GET/POST responses)."""
    total, paid, window_start, _needs_reset = _refresh_state(guild)
    free_remaining = max(0, FREE_REFRESHES_PER_DAY - total)
    next_cost = 0 if free_remaining > 0 else _next_refresh_cost(paid)
    gold = int(guild.get("gold", 0))
    can_refresh = (free_remaining > 0) or (gold >= next_cost)
    return {
        "refreshes_remaining_today": free_remaining,
        "next_refresh_cost_gold": next_cost,
        "next_refresh_reset_at": _tomorrow_utc_start().isoformat(),
        "can_refresh": bool(can_refresh),
        "free_refreshes_per_day": FREE_REFRESHES_PER_DAY,
    }


def candidate_public(doc: dict) -> dict:
    return {
        "candidate_id": doc["id"],
        "name": doc["name"],
        "adventurer_class_id": doc["adventurer_class_id"],
        "class_name": doc["class_name"],
        "class_role": doc["class_role"],
        "rarity": doc["rarity"],
        "level": doc["level"],
        "experience": doc["experience"],
        "strength": doc["strength"],
        "agility": doc["agility"],
        "intellect": doc["intellect"],
        "endurance": doc["endurance"],
        "faith": doc["faith"],
        "stamina": doc["stamina"],
        "morale": doc["morale"],
        "traits": doc.get("traits", []),
        "cost": RECRUITMENT_COST_GOLD,
        "cost_gold": RECRUITMENT_COST_GOLD,
    }


def _weighted_choice(choices):
    total = sum(w for _, w in choices)
    r = _rng.uniform(0, total)
    upto = 0
    for value, weight in choices:
        upto += weight
        if upto >= r:
            return value
    return choices[-1][0]


def _generate_name() -> str:
    first = _rng.choice(FIRST_NAMES)
    if _rng.random() < 0.6:
        return f"{first} {_rng.choice(LAST_NAMES)}"
    return first


def _roll_stat(base: int, rarity_bonus: int) -> int:
    return max(1, base + _rng.randint(-1, 2) + rarity_bonus)


def _pick_random_traits(traits_pool: list) -> list:
    if not traits_pool:
        return []
    r = _rng.random()
    if r < 0.50:
        count = 0
    elif r < 0.85:
        count = 1
    else:
        count = 2
    count = min(count, len(traits_pool))
    if count == 0:
        return []
    chosen = _rng.sample(traits_pool, count)
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t.get("description", ""),
            "modifier_type": t["modifier_type"],
            "affected_stat": t["affected_stat"],
            "modifier_value": t["modifier_value"],
            "is_positive": t["is_positive"],
        }
        for t in chosen
    ]


def _apply_trait_effects(stats: dict, traits: list) -> dict:
    """Phase 13: deprecated no-op kept for backward import-compat.

    Pre-Phase-13 this baked flat trait modifiers into the rolled stat
    dict at offer-generation time. Phase 13 made traits dynamic
    (resolved at power-calc / expedition time), so this helper is now
    a pass-through. Kept exported because external tests/imports may
    reference it.
    """
    return dict(stats)


def _generate_candidate(
    klass: dict,
    guild_id: str,
    now: datetime,
    traits_pool: list | None = None,
) -> dict:
    rarity = _weighted_choice(RARITY_WEIGHTS)
    bonus = RARITY_BONUS[rarity]
    stats = {
        "strength": _roll_stat(klass["base_strength"], bonus),
        "agility": _roll_stat(klass["base_agility"], bonus),
        "intellect": _roll_stat(klass["base_intellect"], bonus),
        "endurance": _roll_stat(klass["base_endurance"], bonus),
        "faith": _roll_stat(klass["base_faith"], bonus),
    }
    traits = _pick_random_traits(traits_pool or [])
    # Phase 13: traits are no longer baked into stats at recruitment.
    # They are now resolved dynamically (power calc, expedition, preview).
    # `_apply_trait_effects` is now a no-op kept for import-compat.
    return {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": _generate_name(),
        "adventurer_class_id": klass["id"],
        "class_name": klass["name"],
        "class_role": klass["role"],
        "rarity": rarity,
        "level": 1,
        "experience": 0,
        **stats,
        "stamina": 100,
        "morale": 100,
        "traits": traits,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=OFFER_TTL_MINUTES)).isoformat(),
    }


async def _roll_and_persist_offer(db, guild: dict) -> list[dict]:
    """Generate a fresh 4-candidate offer, replacing any prior persisted one."""
    classes = await db.adventurer_classes.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)
    if not classes:
        raise HTTPException(status_code=500, detail="No adventurer classes seeded")
    traits_pool = await db.adventurer_traits.find(
        {"is_active": True, "is_test": {"$ne": True}}, {"_id": 0}
    ).to_list(100)

    await db.recruitment_offers.delete_many({"guild_id": guild["id"]})
    now = utc_now()
    candidates = [
        _generate_candidate(_rng.choice(classes), guild["id"], now, traits_pool)
        for _ in range(RECRUITMENT_CANDIDATES_PER_OFFER)
    ]
    await db.recruitment_offers.insert_many([dict(c) for c in candidates])
    return candidates


async def get_or_init_candidates_for_guild(db, guild: dict) -> dict:
    """Phase 11.2: GET candidates does NOT consume refresh or gold.

    - If a persisted offer exists (≥1 candidate), return it as-is.
    - If no persisted offer exists (fresh guild or all consumed), generate
      one — this initial seed does NOT count as a refresh.
    """
    existing = await db.recruitment_offers.find(
        {"guild_id": guild["id"]}, {"_id": 0}
    ).sort("created_at", 1).to_list(50)

    if existing:
        # Filter expired offers on read (defensive — TTL may lag)
        now = utc_now()
        valid = []
        for o in existing:
            try:
                if datetime.fromisoformat(o["expires_at"]) > now:
                    valid.append(o)
            except Exception:
                valid.append(o)
        if valid:
            return {
                "candidates": [candidate_public(c) for c in valid],
                "guild_gold": guild.get("gold", 0),
                "cost_gold": RECRUITMENT_COST_GOLD,
                "expires_in_minutes": OFFER_TTL_MINUTES,
                **refresh_status_payload(guild),
            }

    # No valid offer → initial seed (does NOT consume a refresh)
    candidates = await _roll_and_persist_offer(db, guild)
    return {
        "candidates": [candidate_public(c) for c in candidates],
        "guild_gold": guild.get("gold", 0),
        "cost_gold": RECRUITMENT_COST_GOLD,
        "expires_in_minutes": OFFER_TTL_MINUTES,
        **refresh_status_payload(guild),
    }


async def refresh_candidates_for_guild(db, guild: dict) -> dict:
    """Phase 11.2: POST /refresh — atomically check limit/cost, then roll.

    On gold-required and insufficient → HTTP 402 Payment Required.
    Atomicity: a single conditional `find_one_and_update` guards the daily
    counter + window reset + gold debit. The offer is then rolled.
    """
    today = _today_utc_start()
    now = utc_now()
    today_iso = today.isoformat()

    # Determine effective state (with lazy reset semantics)
    total, paid, window_start, needs_reset = _refresh_state(guild)

    # Decide cost & next counters
    if total < FREE_REFRESHES_PER_DAY:
        cost = 0
    else:
        cost = _next_refresh_cost(paid)

    gold = int(guild.get("gold", 0))
    if cost > gold:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient gold (need {cost}, have {gold})",
        )

    # Build atomic CAS match — gate on expected current state so concurrent
    # refresh calls cannot race past the daily cap.
    match: dict = {"id": guild["id"], "gold": {"$gte": cost}}
    if needs_reset:
        # No prior window OR yesterday — accept either case. Counters reset.
        match["$or"] = [
            {"recruitment_refresh_window_start_utc": {"$exists": False}},
            {"recruitment_refresh_window_start_utc": {"$lt": today_iso}},
        ]
        new_total = 1
        new_paid = 0 if cost == 0 else 1
    else:
        match["recruitment_refresh_window_start_utc"] = window_start.isoformat()
        match["recruitment_refresh_count_today"] = total
        match["recruitment_paid_refresh_count_today"] = paid
        new_total = total + 1
        new_paid = paid if cost == 0 else paid + 1

    update = {
        "$set": {
            "recruitment_refresh_count_today": new_total,
            "recruitment_paid_refresh_count_today": new_paid,
            "recruitment_refresh_window_start_utc": today_iso,
            "updated_at": now.isoformat(),
        }
    }
    if cost > 0:
        update["$inc"] = {"gold": -cost}

    updated_guild = await db.guilds.find_one_and_update(
        match, update, projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_guild:
        # Concurrent refresh or gold race
        raise HTTPException(
            status_code=409,
            detail="Refresh state changed concurrently, please retry",
        )

    candidates = await _roll_and_persist_offer(db, updated_guild)
    return {
        "candidates": [candidate_public(c) for c in candidates],
        "guild_gold": updated_guild.get("gold", 0),
        "cost_gold": RECRUITMENT_COST_GOLD,
        "expires_in_minutes": OFFER_TTL_MINUTES,
        "refresh_cost_paid": cost,
        **refresh_status_payload(updated_guild),
    }


# Backward-compat: generate_candidates_for_guild now delegates to the
# get-or-init flow so legacy callers (tests that hit GET expecting a fresh
# roster) still work. The legacy semantics of "always re-roll on GET" is
# DEPRECATED — Phase 11.2 separates view from refresh.
async def generate_candidates_for_guild(db, guild: dict) -> dict:
    return await get_or_init_candidates_for_guild(db, guild)


async def recruit_from_offer(db, guild: dict, candidate_id: str) -> dict:
    offer = await db.recruitment_offers.find_one_and_delete(
        {"id": candidate_id, "guild_id": guild["id"]},
        projection={"_id": 0},
    )
    if not offer:
        raise HTTPException(
            status_code=404, detail="Candidate not found or already recruited"
        )

    try:
        exp = datetime.fromisoformat(offer["expires_at"])
    except Exception:
        exp = utc_now() + timedelta(minutes=1)
    if exp < utc_now():
        raise HTTPException(status_code=404, detail="Candidate offer has expired")

    now = utc_now()
    updated_guild = await db.guilds.find_one_and_update(
        {"id": guild["id"], "gold": {"$gte": RECRUITMENT_COST_GOLD}},
        {
            "$inc": {"gold": -RECRUITMENT_COST_GOLD},
            "$set": {"updated_at": now.isoformat()},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_guild:
        offer_to_restore = {k: v for k, v in offer.items() if k != "_id"}
        try:
            await db.recruitment_offers.insert_one(offer_to_restore)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Insufficient gold")

    adventurer_doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "name": offer["name"],
        "adventurer_class_id": offer["adventurer_class_id"],
        "class_name": offer["class_name"],
        "class_role": offer["class_role"],
        "rarity": offer["rarity"],
        "level": offer["level"],
        "experience": offer["experience"],
        "strength": offer["strength"],
        "agility": offer["agility"],
        "intellect": offer["intellect"],
        "endurance": offer["endurance"],
        "faith": offer["faith"],
        "stamina": offer["stamina"],
        "morale": offer["morale"],
        "traits": offer.get("traits", []),
        "is_available": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.adventurers.insert_one(adventurer_doc)
    # Phase 14 — daily quest progress (best-effort)
    try:
        from app.quests.services import increment_quest_progress
        await increment_quest_progress(db, guild["id"], "recruit")
    except Exception:
        pass
    return adventurer_doc, updated_guild


__all__ = [
    "candidate_public",
    "_weighted_choice",
    "_generate_name",
    "_roll_stat",
    "_pick_random_traits",
    "_apply_trait_effects",
    "_generate_candidate",
    "generate_candidates_for_guild",
    "get_or_init_candidates_for_guild",
    "refresh_candidates_for_guild",
    "refresh_status_payload",
    "recruit_from_offer",
    "FREE_REFRESHES_PER_DAY",
    "PAID_REFRESH_PRICES",
]
