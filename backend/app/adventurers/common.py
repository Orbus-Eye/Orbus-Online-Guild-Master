"""ROUND 6B FASE A — Shared adventurer generation primitives.

Extracted from `app/recruitment/services.py` to break the circular
dependency with `app/adventurers/generator.py`.

This module ONLY hosts the pure stat/trait/name primitives + the legacy
`_generate_candidate` factory. It has NO async DB calls, NO HTTP layer,
NO FastAPI imports — safe to import from anywhere in the codebase.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta

from app.shared.constants import (
    FIRST_NAMES,
    LAST_NAMES,
    OFFER_TTL_MINUTES,
    RARITY_BONUS,
    RARITY_WEIGHTS,
)


# Module-level cryptographic RNG; tests can pass their own `random.Random`
# instance to `_generate_candidate` for determinism via the helpers above.
_rng = secrets.SystemRandom()


def _canonical_role(klass: dict) -> str | None:
    """FASE 9B — ruolo canonico (DPS/TANK/HEALER) dal registry classi."""
    from app.classes import class_role_for
    return (
        class_role_for(str(klass.get("slug") or ""))
        or class_role_for(str(klass.get("name") or ""))
    )


def _weighted_choice(choices, rng=None):
    rng = rng or _rng
    total = sum(w for _, w in choices)
    r = rng.uniform(0, total)
    upto = 0
    for value, weight in choices:
        upto += weight
        if upto >= r:
            return value
    return choices[-1][0]


def _generate_name(rng=None) -> str:
    rng = rng or _rng
    first = rng.choice(FIRST_NAMES)
    if rng.random() < 0.6:
        return f"{first} {rng.choice(LAST_NAMES)}"
    return first


def _roll_stat(base: int, rarity_bonus: int, rng=None) -> int:
    rng = rng or _rng
    return max(1, base + rng.randint(-1, 2) + rarity_bonus)


def _pick_random_traits(traits_pool: list, rng=None) -> list:
    rng = rng or _rng
    if not traits_pool:
        return []
    r = rng.random()
    if r < 0.50:
        count = 0
    elif r < 0.85:
        count = 1
    else:
        count = 2
    count = min(count, len(traits_pool))
    if count == 0:
        return []
    chosen = rng.sample(traits_pool, count)
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


def _apply_trait_effects(stats: dict, _traits: list) -> dict:
    """Phase 13: deprecated no-op kept for backward import-compat."""
    return dict(stats)


def _generate_candidate(
    klass: dict,
    guild_id: str,
    now: datetime,
    traits_pool: list | None = None,
    *,
    rng=None,
    forced_rarity: str | None = None,
    rarity_weights=None,
    rarity_bonus=None,
) -> dict:
    """Generate ONE candidate dict.

    ROUND 6B FASE A:
      - `forced_rarity` + `rarity_weights` + `rarity_bonus` replace the
        old monkey-patch trick in generator.py. Callers that need to
        force a rarity pass `forced_rarity` directly; the heavy
        `RARITY_WEIGHTS` swap is no longer needed.
    """
    rng = rng or _rng
    weights = rarity_weights or RARITY_WEIGHTS
    bonus_map = rarity_bonus or RARITY_BONUS

    rarity = forced_rarity or _weighted_choice(weights, rng=rng)
    bonus = bonus_map[rarity]
    stats = {
        "strength": _roll_stat(klass["base_strength"], bonus, rng=rng),
        "agility": _roll_stat(klass["base_agility"], bonus, rng=rng),
        "intellect": _roll_stat(klass["base_intellect"], bonus, rng=rng),
        "endurance": _roll_stat(klass["base_endurance"], bonus, rng=rng),
        "faith": _roll_stat(klass["base_faith"], bonus, rng=rng),
    }
    traits = _pick_random_traits(traits_pool or [], rng=rng)
    return {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": _generate_name(rng=rng),
        "adventurer_class_id": klass["id"],
        "class_name": klass["name"],
        # ROUND 16.5.4c — ADJ-9: popola sempre `class_slug` in write path,
        # in modo che i futuri Auto-Equip / spec eligibility / filtri
        # non debbano più cadere sul fallback runtime. Il valore proviene
        # dal catalog `adventurer_classes` (fonte di verità unica).
        "class_slug": (klass.get("slug") or "").strip().lower() or None,
        # FASE 9B — ruolo canonico dal registry (fisso per classe);
        # il campo `role` del doc adventurer_classes è solo fallback.
        "class_role": _canonical_role(klass) or klass["role"],
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


def _generate_classless_candidate(
    guild_id: str,
    now: datetime,
    traits_pool: list | None = None,
    *,
    rng=None,
    forced_rarity: str | None = None,
    rarity_weights=None,
    rarity_bonus=None,
) -> dict:
    """Generate a neutral recruit who has not chosen a Class Hall yet.

    Class identity is intentionally absent.  The five core stats share the
    same base so recruitment cannot silently bias the later Hall choice.
    """
    rng = rng or _rng
    # Career rarity is never rolled. Legacy parameters remain accepted so old
    # seed/test callers do not crash, but every new classless recruit starts
    # Common and can only advance through completed dungeon/raid activity.
    rarity = "Common"
    bonus = 0
    stats = {
        stat: _roll_stat(5, bonus, rng=rng)
        for stat in ("strength", "agility", "intellect", "endurance", "faith")
    }
    return {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": _generate_name(rng=rng),
        "adventurer_class_id": None,
        "class_name": None,
        "class_role": None,
        "class_proficiency": None,
        "class_slug": None,
        "canonical_class_slug": None,
        "class_hall_id": None,
        "class_hall_assigned_at": None,
        "hall_master_witness_npc": None,
        "recruit_status": "recruit_unassigned",
        "narrative_intro_shown": False,
        "rarity": rarity,
        "level": 1,
        "experience": 0,
        "career_dungeons_completed": 0,
        "career_raids_completed": 0,
        **stats,
        "stamina": 100,
        "morale": 100,
        "traits": _pick_random_traits(traits_pool or [], rng=rng),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=OFFER_TTL_MINUTES)).isoformat(),
    }


def build_base_adventurer(
    guild_id: str,
    *,
    name: str,
    now: datetime,
    race_slug: str | None = None,
    gender: str | None = None,
    is_starter: bool = False,
) -> dict:
    """Build a deterministic player-authored adventurer model.

    No rarity, stat, trait, class or identity field is rolled. Class identity
    is deliberately deferred to the Class Hall journey.
    """
    return {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": name.strip(),
        "adventurer_class_id": None,
        "class_name": None,
        "class_role": None,
        "class_proficiency": None,
        "class_slug": None,
        "canonical_class_slug": None,
        "class_hall_id": None,
        "class_hall_assigned_at": None,
        "hall_master_witness_npc": None,
        "recruit_status": "recruit_unassigned",
        "narrative_intro_shown": False,
        "rarity": "Common",
        "level": 1,
        "experience": 0,
        "career_dungeons_completed": 0,
        "career_raids_completed": 0,
        "strength": 5,
        "agility": 5,
        "intellect": 5,
        "endurance": 5,
        "faith": 5,
        "stamina": 100,
        "morale": 100,
        "traits": [],
        "race_slug": race_slug,
        "gender": gender,
        "is_available": True,
        "is_starter": bool(is_starter),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


__all__ = [
    "_rng",
    "_weighted_choice",
    "_generate_name",
    "_roll_stat",
    "_pick_random_traits",
    "_apply_trait_effects",
    "_generate_candidate",
    "_generate_classless_candidate",
    "build_base_adventurer",
]
