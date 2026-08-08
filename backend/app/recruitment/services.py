"""Recruitment services (Phase 5.5c.3 + Phase 11.2 refresh limit).

Phase 11.2 adds a daily refresh limit:
- 3 free refreshes per UTC day per guild
- Beyond free: paid scaling 10g / 20g / 30g (cap)
- Window resets on UTC date change (lazy)
- GET /candidates returns persisted offer without consuming any refresh
- POST /refresh forces a new roll, atomically applies limit + cost
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.shared.constants import (
    OFFER_TTL_MINUTES,
    RECRUITMENT_CANDIDATES_PER_OFFER,
    RECRUITMENT_COST_GOLD,
)

# ROUND 6B FASE A — primitive helpers moved to `app.adventurers.common` to
# break the circular import with `app.adventurers.generator`. The legacy
# private names are re-exported here so existing callers (tests, onboarding,
# scripts) keep working unchanged.
from app.adventurers.common import (  # noqa: F401  (re-exported)
    _rng,
    _weighted_choice,
    _generate_name,
    _roll_stat,
    _pick_random_traits,
    _apply_trait_effects,
    _generate_candidate,
    _generate_classless_candidate,
)


# Phase 11.2 refresh policy
FREE_REFRESHES_PER_DAY = 3
PAID_REFRESH_PRICES = [10, 20, 30]  # 1st paid, 2nd paid, 3rd+ paid (cap)
MAX_CLASSLESS_RECRUITS_PER_GUILD = 3


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
    # ROUND 6A.1 — expose `total_power` in the recruitment payload so the
    # Recruitment card can show the same unified power value used by the
    # roster/raid/expedition UIs. Computed from the same `adventurer_base_power`
    # single-source-of-truth helper (no equipment at candidate stage).
    from app.expeditions.formulas import adventurer_base_power

    base_power = adventurer_base_power(doc)
    return {
        "candidate_id": doc["id"],
        "name": doc["name"],
        "adventurer_class_id": doc.get("adventurer_class_id"),
        "class_name": doc.get("class_name"),
        "class_role": doc.get("class_role"),
        "class_slug": doc.get("class_slug"),
        "canonical_class_slug": doc.get("canonical_class_slug"),
        "class_proficiency": doc.get("class_proficiency"),
        "class_hall_id": doc.get("class_hall_id"),
        "recruit_status": doc.get("recruit_status"),
        "class_selection_required": (
            doc.get("recruit_status") == "recruit_unassigned"
            and not doc.get("class_slug")
        ),
        "class_display_name_it": (
            "Senza Classe"
            if doc.get("recruit_status") == "recruit_unassigned"
            else doc.get("class_name")
        ),
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
        "base_power": base_power,
        "equipment_power": 0,  # candidates have no equipment yet
        "total_power": base_power,  # mirror roster shape for UI parity
        "cost": RECRUITMENT_COST_GOLD,
        "cost_gold": RECRUITMENT_COST_GOLD,
    }


async def _hydrate_trait_subdocs(db, candidates: list[dict]) -> None:
    """ROUND 6A.2b — backfill `display_name_it` / `display_name` on legacy
    trait subdocs at read time.

    Recruitment offers persisted before the trait IT migration store the
    legacy subdoc shape `{id, name="disciplined", description, ...}` with no
    display fields. We do ONE batched lookup against `adventurer_traits` and
    enrich each subdoc in-place so `candidate_public()` (and any downstream
    `recruit_from_offer`) sees the IT names without needing a sync rewrite.

    Mutates `candidates` in-place. Safe to call with empty/None traits.
    """
    trait_ids: set[str] = set()
    trait_name_keys: set[str] = set()
    for c in candidates or []:
        for t in c.get("traits") or []:
            if isinstance(t, dict):
                tid = t.get("id") or t.get("trait_id")
                if tid:
                    trait_ids.add(tid)
                n = (t.get("name") or "").strip().lower()
                if n:
                    trait_name_keys.add(n)
    if not trait_ids and not trait_name_keys:
        return
    by_id: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    cursor = db.adventurer_traits.find(
        {
            "$or": [
                {"id": {"$in": list(trait_ids)}} if trait_ids else {"id": None},
                (
                    {"name": {"$in": list(trait_name_keys)}}
                    if trait_name_keys
                    else {"name": None}
                ),
            ]
        },
        {"_id": 0, "id": 1, "name": 1, "display_name": 1, "display_name_it": 1},
    )
    async for m in cursor:
        if m.get("id"):
            by_id[m["id"]] = m
        nk = (m.get("name") or "").strip().lower()
        if nk:
            by_name[nk] = m
    for c in candidates or []:
        for t in c.get("traits") or []:
            if not isinstance(t, dict):
                continue
            master = by_id.get(t.get("id") or t.get("trait_id")) or by_name.get(
                (t.get("name") or "").strip().lower()
            )
            if not master:
                continue
            if not t.get("display_name"):
                t["display_name"] = (
                    master.get("display_name") or master.get("name") or ""
                )
            if not t.get("display_name_it"):
                t["display_name_it"] = master.get("display_name_it") or ""


async def _roll_and_persist_offer(db, guild: dict) -> list[dict]:
    """Generate a fresh 4-candidate offer, replacing any prior persisted one.

    Delegates to `app.adventurers.generator.generate_classless_candidate`
    which centralises rarity weighting (incl. Legendary), post-roll guards
    (≥3 positive traits + ≥1 stat at floor for Legendary), Test* filtering,
    neutral stats and audit log emit (`adventurer_generated`).
    """
    from app.adventurers.generator import (
        filter_safe_trait_pool,
        generate_classless_candidate,
    )

    traits_pool = await filter_safe_trait_pool(db)
    # Backward-compat: the previous code also queried `adventurer_traits`
    # (legacy collection name). Merge both if present.
    legacy_traits = await db.adventurer_traits.find(
        {"is_active": True, "is_test": {"$ne": True}}, {"_id": 0}
    ).to_list(100)
    traits_pool = (traits_pool or []) + [
        t
        for t in (legacy_traits or [])
        if not (
            t.get("name", "").startswith("Test") or t.get("slug", "").startswith("test")
        )
    ]

    await db.recruitment_offers.delete_many({"guild_id": guild["id"]})
    now = utc_now()
    candidates = []
    for _ in range(RECRUITMENT_CANDIDATES_PER_OFFER):
        c = await generate_classless_candidate(
            db,
            guild_id=guild["id"],
            now=now,
            trait_pool=traits_pool,
            audit_source="recruitment",
        )
        # The legacy generator added `expires_at`; the new wrapper preserves
        # it because we still go through `_generate_candidate`.
        candidates.append(c)
    if candidates:
        await db.recruitment_offers.insert_many([dict(c) for c in candidates])
    return candidates


async def get_or_init_candidates_for_guild(db, guild: dict) -> dict:
    """Phase 11.2: GET candidates does NOT consume refresh or gold.

    - If a persisted offer exists (≥1 candidate), return it as-is.
    - If no persisted offer exists (fresh guild or all consumed), generate
      one — this initial seed does NOT count as a refresh.
    """
    # ROUND 16.0.1 — Build deprecated-class id set so we can filter out
    # pre-existing offers that pre-date the Phase 2 migration. The recruitment
    # generator already excludes deprecated classes at roll time; this filter
    # protects the read path against the ~2.2k stale offers still in DB.
    deprecated_class_ids: set[str] = set()
    async for dep in db.adventurer_classes.find(
        {"$or": [{"is_base_class": False}, {"deprecated_at": {"$ne": None}}]},
        {"_id": 0, "id": 1},
    ):
        deprecated_class_ids.add(dep["id"])

    existing = (
        await db.recruitment_offers.find({"guild_id": guild["id"]}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(50)
    )

    if existing:
        # Filter expired offers on read (defensive — TTL may lag)
        now = utc_now()
        valid = []
        for o in existing:
            # ROUND 16.0.1 — skip offers whose class was deprecated after
            # the Phase 2 migration (necromancer / assassin / berserker).
            if o.get("adventurer_class_id") in deprecated_class_ids:
                continue
            try:
                if datetime.fromisoformat(o["expires_at"]) > now:
                    valid.append(o)
            except Exception:
                valid.append(o)
        if valid:
            await _hydrate_trait_subdocs(db, valid)
            return {
                "candidates": [candidate_public(c) for c in valid],
                "guild_gold": guild.get("gold", 0),
                "cost_gold": RECRUITMENT_COST_GOLD,
                "expires_in_minutes": OFFER_TTL_MINUTES,
                **refresh_status_payload(guild),
            }

    # No valid offer → initial seed (does NOT consume a refresh)
    candidates = await _roll_and_persist_offer(db, guild)
    await _hydrate_trait_subdocs(db, candidates)
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
            detail=f"Oro insufficiente (servono {cost}, ne hai {gold})",
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
        match,
        update,
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_guild:
        # Concurrent refresh or gold race
        raise HTTPException(
            status_code=409,
            detail="Le offerte sono cambiate nel frattempo: riprova",
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
    # The classless onboarding contract allows at most three undecided
    # recruits in a guild.  Check before consuming the offer so a rejection
    # never destroys the player's candidate.
    offer_preview = await db.recruitment_offers.find_one(
        {"id": candidate_id, "guild_id": guild["id"]},
        {"_id": 0, "recruit_status": 1, "class_slug": 1, "class_name": 1},
    )
    preview_is_classless = bool(
        offer_preview
        and (
            offer_preview.get("recruit_status") == "recruit_unassigned"
            or (
                not offer_preview.get("class_slug")
                and not offer_preview.get("class_name")
            )
        )
    )
    if preview_is_classless:
        undecided = await db.adventurers.count_documents(
            {
                "guild_id": guild["id"],
                "recruit_status": "recruit_unassigned",
                "is_retired": {"$ne": True},
            }
        )
        if undecided >= MAX_CLASSLESS_RECRUITS_PER_GUILD:
            raise HTTPException(
                status_code=423,
                detail={
                    "code": "recruit.classless_cap_reached",
                    "current": undecided,
                    "cap": MAX_CLASSLESS_RECRUITS_PER_GUILD,
                    "user_message": (
                        "Hai già tre reclute senza classe. Assegna una Sala "
                        "o congedane una prima di reclutarne altre."
                    ),
                },
            )
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

    # ROUND 11.2 TASK 1 — Post-insert cap verification with compensating
    # rollback. The pre-debit `assert_not_over_cap` dependency cannot
    # serialize two concurrent recruits on a 1-slot-left roster (both pass
    # the count check before either insert lands). We insert the adventurer
    # FIRST, then re-count: if the total exceeds the cap, the loser is the
    # one whose post-insert count is > cap (deterministic via MongoDB
    # serialization). Loser → delete own insert + refund gold + restore offer.

    adventurer_doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "name": offer["name"],
        "adventurer_class_id": offer.get("adventurer_class_id"),
        "class_name": offer.get("class_name"),
        "class_role": offer.get("class_role"),
        "class_proficiency": offer.get("class_proficiency"),
        "class_slug": offer.get("class_slug"),
        "canonical_class_slug": offer.get("canonical_class_slug"),
        "class_hall_id": offer.get("class_hall_id"),
        "class_hall_assigned_at": offer.get("class_hall_assigned_at"),
        "hall_master_witness_npc": offer.get("hall_master_witness_npc"),
        "recruit_status": (
            offer.get("recruit_status")
            or (
                "class_assigned"
                if offer.get("adventurer_class_id") or offer.get("class_name")
                else "recruit_unassigned"
            )
        ),
        "narrative_intro_shown": bool(
            offer.get(
                "narrative_intro_shown",
                bool(offer.get("adventurer_class_id") or offer.get("class_name")),
            )
        ),
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
        # ROUND 6A.1 — explicit defaults (was relying on `adventurer_public`
        # to inject these). Now persisted so future code that reads raw
        # docs (without going through the public projection) gets sane
        # values without `.get(..., default)` ceremony.
        "is_starter": False,
        "rename_count": 0,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.adventurers.insert_one(adventurer_doc)

    # Concurrency backstop for the per-guild classless cap.  If two hires
    # race past the pre-check, the one observing count > 3 compensates fully.
    if adventurer_doc["recruit_status"] == "recruit_unassigned":
        undecided = await db.adventurers.count_documents(
            {
                "guild_id": guild["id"],
                "recruit_status": "recruit_unassigned",
                "is_retired": {"$ne": True},
            }
        )
        if undecided > MAX_CLASSLESS_RECRUITS_PER_GUILD:
            await db.adventurers.delete_one({"id": adventurer_doc["id"]})
            await db.guilds.update_one(
                {"id": guild["id"]},
                {
                    "$inc": {"gold": RECRUITMENT_COST_GOLD},
                    "$set": {"updated_at": now.isoformat()},
                },
            )
            try:
                await db.recruitment_offers.insert_one(
                    {k: v for k, v in offer.items() if k != "_id"}
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=423,
                detail={
                    "code": "recruit.classless_cap_reached",
                    "current": undecided - 1,
                    "cap": MAX_CLASSLESS_RECRUITS_PER_GUILD,
                    "user_message": (
                        "Limite di tre reclute senza classe raggiunto. "
                        "L'offerta è stata ripristinata."
                    ),
                },
            )

    # ROUND 11.2 TASK 1 — Post-insert cap verification (compensating).
    # If two concurrent recruits both pass the pre-debit assert_not_over_cap
    # check on a 1-slot-left roster, both will land their insert. The loser
    # is determined here: whoever sees count > cap AFTER its own insert
    # rolls back (delete this adv + refund gold + restore offer).
    try:
        from app.territory.guards import compute_adventurer_cap_state

        cap_state = await compute_adventurer_cap_state(db, guild["id"])
        if int(cap_state.get("current", 0)) > int(cap_state.get("cap", 0)):
            # We are over cap → we are the loser. Compensate.
            await db.adventurers.delete_one({"id": adventurer_doc["id"]})
            await db.guilds.update_one(
                {"id": guild["id"]},
                {
                    "$inc": {"gold": RECRUITMENT_COST_GOLD},
                    "$set": {"updated_at": now.isoformat()},
                },
            )
            offer_to_restore = {k: v for k, v in offer.items() if k != "_id"}
            try:
                await db.recruitment_offers.insert_one(offer_to_restore)
            except Exception:
                pass
            raise HTTPException(
                status_code=423,
                detail={
                    "code": "roster_over_capacity",
                    "current": int(cap_state.get("current", 0)),
                    "cap": int(cap_state.get("cap", 0)),
                    "user_message": "Capienza avventurieri raggiunta. "
                    "Potenzia Dormitori o congeda.",
                },
            )
    except HTTPException:
        raise
    except Exception:
        pass
    # Phase 14 — daily quest progress (best-effort)
    try:
        from app.quests.services import increment_quest_progress

        await increment_quest_progress(db, guild["id"], "recruit")
    except Exception:
        pass
    # ROUND 6D — contract progress (best-effort)
    try:
        from app.contracts.services import increment_contract_progress

        await increment_contract_progress(db, guild["id"], "recruits_added", 1)
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
    "MAX_CLASSLESS_RECRUITS_PER_GUILD",
]
