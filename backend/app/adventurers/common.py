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


__all__ = [
    "_rng",
    "_weighted_choice",
    "_generate_name",
    "_roll_stat",
    "_pick_random_traits",
    "_apply_trait_effects",
    "_generate_candidate",
]
