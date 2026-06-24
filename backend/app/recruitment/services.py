"""Recruitment services (Phase 5.5c.3).

Pure business logic: candidate generation (RNG via secrets.SystemRandom for
cryptographic entropy, behavior-identical to the prior server.py inline
impl) + the two-step atomic recruit flow (claim offer → conditional gold
decrement → insert adventurer with offer-saved stats, refund on race).
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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def candidate_public(doc: dict) -> dict:
    """Project a recruitment_offer doc to the public candidate shape."""
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
        # Phase 2 fix: both `cost` and `cost_gold` are returned for legacy clients
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
    """Pick 0–2 distinct traits with weighted distribution: 50%/35%/15%."""
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
    """Apply 'flat' modifiers on the 5 main stats; floor at 1.

    `percent` modifiers (e.g. Quick Learner xp_gain) are deferred to expedition
    reward calc — not applied here.
    """
    affected = ("strength", "agility", "intellect", "endurance", "faith")
    for t in traits:
        if t.get("modifier_type") == "flat" and t.get("affected_stat") in affected:
            key = t["affected_stat"]
            stats[key] = max(1, int(stats[key]) + int(t.get("modifier_value", 0)))
    return stats


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
    stats = _apply_trait_effects(stats, traits)
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


async def generate_candidates_for_guild(db, guild: dict) -> dict:
    """Generate `RECRUITMENT_CANDIDATES_PER_OFFER` candidates, replace prior
    offers, and return the public-shaped payload.
    """
    classes = await db.adventurer_classes.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)
    if not classes:
        raise HTTPException(status_code=500, detail="No adventurer classes seeded")

    # Replace prior offers for this guild
    await db.recruitment_offers.delete_many({"guild_id": guild["id"]})

    traits_pool = await db.adventurer_traits.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)

    now = utc_now()
    candidates = [
        _generate_candidate(_rng.choice(classes), guild["id"], now, traits_pool)
        for _ in range(RECRUITMENT_CANDIDATES_PER_OFFER)
    ]
    await db.recruitment_offers.insert_many([dict(c) for c in candidates])

    return {
        "candidates": [candidate_public(c) for c in candidates],
        "guild_gold": guild.get("gold", 0),
        "cost_gold": RECRUITMENT_COST_GOLD,
        "expires_in_minutes": OFFER_TTL_MINUTES,
    }


async def recruit_from_offer(db, guild: dict, candidate_id: str) -> dict:
    """Atomic two-step recruit: claim offer → conditional gold decrement.

    On gold-race failure the offer is best-effort restored so the user can
    retry once they have funds. Returns `(adventurer_doc, updated_guild)`.
    """
    # Step 1: atomically claim the offer (delete) — owner-scoped lookup
    offer = await db.recruitment_offers.find_one_and_delete(
        {"id": candidate_id, "guild_id": guild["id"]},
        projection={"_id": 0},
    )
    if not offer:
        raise HTTPException(
            status_code=404, detail="Candidate not found or already recruited"
        )

    # Expiry check (applicative — supports envs without TTL background pass yet)
    try:
        exp = datetime.fromisoformat(offer["expires_at"])
    except Exception:
        exp = utc_now() + timedelta(minutes=1)
    if exp < utc_now():
        raise HTTPException(status_code=404, detail="Candidate offer has expired")

    # Step 2: atomically decrement gold with affordability check
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
        # Best-effort offer refund so user can retry once they have gold
        offer_to_restore = {k: v for k, v in offer.items() if k != "_id"}
        try:
            await db.recruitment_offers.insert_one(offer_to_restore)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Insufficient gold")

    # Step 3: create the adventurer from offer-saved stats (NOT client-provided)
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
    "recruit_from_offer",
]
