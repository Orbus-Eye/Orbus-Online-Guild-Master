"""ROUND 6A.1 — Adventurer generator (server-authoritative).

Centralised entry point for creating adventurer candidates. Wraps the
legacy `recruitment._generate_candidate` and adds:
  • Legendary/Epic post-roll guards (≥N positive traits, ≥1 stat at floor).
  • Audit log emit on every generated candidate.
  • Safe fallbacks: empty trait pool, no Test* traits, no Test* classes.
  • Deterministic seed support for tests (`new_rng_for_tests`).

NEVER returns Legendary via paid boost or premium — all randomness is
server-side and gated by `RARITY_WEIGHTS`.
"""
from __future__ import annotations

import logging
import random as _legacy_random  # Round 11.4d — kept for any module-level seed only
import secrets
random = secrets.SystemRandom()  # PvP-ready: crypto-grade RNG
from datetime import datetime, timezone
from typing import Optional

from app.audit.log import write_audit
from app.shared.constants import (
    RARITY_POSITIVE_TRAIT_MIN,
    RARITY_STAT_MAX_FLOOR,
    RARITY_WEIGHTS,
)


logger = logging.getLogger("orbus.adventurers.generator")

_CORE_STATS = ("strength", "agility", "intellect", "endurance", "faith")


def new_rng_for_tests(seed: int) -> random.Random:
    """Return a fresh Random instance seeded deterministically. Tests only."""
    return random.Random(seed)


def _weighted_choice(rng: random.Random, choices: list) -> str:
    total = sum(w for _, w in choices)
    r = rng.uniform(0, total)
    upto = 0.0
    for value, weight in choices:
        upto += weight
        if upto >= r:
            return value
    return choices[-1][0]


def _count_positive_traits(traits: list[dict]) -> int:
    return sum(1 for t in traits or [] if t.get("is_positive"))


def _stat_max_value(candidate: dict) -> int:
    vals = [int(candidate.get(s, 0)) for s in _CORE_STATS]
    return max(vals) if vals else 0


async def filter_safe_trait_pool(db) -> list[dict]:
    """Return active traits with NO Test* in name/slug. Safe fallback []."""
    try:
        rows = await db.traits.find(
            {"is_active": True, "is_test": {"$ne": True}},
            {"_id": 0},
        ).to_list(500)
    except Exception as exc:
        logger.warning("trait pool fetch failed: %s", exc)
        return []
    safe = [
        t for t in rows
        if not (t.get("name", "").startswith("Test")
                or t.get("slug", "").startswith("test"))
    ]
    return safe


async def filter_safe_class_pool(db) -> list[dict]:
    """Return active **base** classes with NO Test* in name/slug.

    Round 16.0: filters by `is_base_class=True` to exclude the 3
    deprecated classes (berserker, assassin, necromancer) which now exist
    only as specializations attached to their successor base class.
    Recruitment, candidate generation and class selection UIs must rely
    on this helper to stay aligned with the 10 base classes.
    """
    rows = await db.adventurer_classes.find(
        {
            "is_active": True,
            "is_test": {"$ne": True},
            "$or": [
                # Backwards compat: documents seeded before Round 16 lack
                # the explicit flag; treat *active* ones as base by
                # default ONLY if they are NOT deprecated.
                {"is_base_class": True},
                {"$and": [
                    {"is_base_class": {"$exists": False}},
                    {"deprecated_at": None},
                ]},
            ],
        },
        {"_id": 0},
    ).to_list(100)
    safe = [
        c for c in rows
        if not (c.get("name", "").startswith("Test")
                or c.get("slug", "").startswith("test"))
    ]
    return safe


def _enforce_legendary_floor(
    rng: random.Random, candidate: dict, rarity: str
) -> dict:
    """Post-roll guard: bump at least one stat to the rarity floor if not met.

    Idempotent and conservative: only bumps the *highest* stat to the floor
    (the adv stays narratively believable; we don't max all stats).
    """
    floor = RARITY_STAT_MAX_FLOOR.get(rarity)
    if not floor:
        return candidate
    if _stat_max_value(candidate) >= floor:
        return candidate
    # Pick the current strongest stat and lift it to the floor.
    best_stat = max(_CORE_STATS, key=lambda s: candidate.get(s, 0))
    candidate[best_stat] = floor
    return candidate


def _ensure_trait_floor(
    *,
    rng: random.Random,
    candidate: dict,
    traits: list[dict] | None,
    rarity: str,
) -> dict:
    """ROUND 6B FASE C — apply the positive-trait floor for the candidate's
    rarity.

    Mutates `candidate["traits"]` in place when possible and returns it.
    If the trait pool is too thin for the required floor, logs a single
    info line and leaves the candidate untouched (the row is still valid
    for save — Round 6A explicitly forbids injecting synthetic Test*
    traits as a fallback).
    """
    min_pos = RARITY_POSITIVE_TRAIT_MIN.get(rarity, 0)
    if min_pos <= 0:
        return candidate

    positives = [t for t in (traits or []) if t.get("is_positive")]
    current_pos = _count_positive_traits(candidate.get("traits", []))
    if current_pos >= min_pos:
        return candidate

    if len(positives) < min_pos:
        # Pool insufficient: log once, candidate still valid for save.
        logger.info(
            "rarity=%s traits_pool=%d positives=%d < required=%d "
            "(fallback ok, no Test* injected)",
            rarity, len(traits or []), len(positives), min_pos,
        )
        return candidate

    picked = rng.sample(positives, min_pos)
    existing_ids = {t["id"] for t in candidate.get("traits", [])}
    new_traits = [t for t in picked if t["id"] not in existing_ids][:min_pos]
    candidate["traits"] = (candidate.get("traits") or []) + [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t.get("description", ""),
            "modifier_type": t["modifier_type"],
            "affected_stat": t["affected_stat"],
            "modifier_value": t["modifier_value"],
            "is_positive": True,
        }
        for t in new_traits
    ]
    return candidate


async def _emit_generated_audit(
    db,
    *,
    candidate: dict,
    guild_id: str,
    rarity: str,
    klass: dict,
    audit_source: str,
) -> None:
    """Best-effort audit log for a freshly-generated candidate. Failures
    are swallowed (logged at WARN) so generation is never blocked by the
    audit pipeline."""
    try:
        await write_audit(
            db,
            event_type="adventurer_generated",
            actor_user_id=None,                  # system-generated
            actor_guild_id=guild_id,
            related_entity_id=candidate["id"],
            source=audit_source,
            metadata={
                "rarity": rarity,
                "traits_count": len(candidate.get("traits", [])),
                "positive_traits_count": _count_positive_traits(candidate.get("traits", [])),
                "class_slug": klass.get("slug"),
                "stat_max": _stat_max_value(candidate),
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit emit failed for adv %s: %s", candidate["id"], exc)


async def generate_candidate(
    db,
    *,
    guild_id: str,
    now: Optional[datetime] = None,
    rng: Optional[random.Random] = None,
    class_pool: Optional[list[dict]] = None,
    trait_pool: Optional[list[dict]] = None,
    audit: bool = True,
    audit_source: str = "recruitment",
) -> dict:
    """Generate ONE adventurer candidate dict ready for inventory upsert.

    Args:
        guild_id: owning guild.
        now: timestamp (default UTC now).
        rng: deterministic Random (tests); production uses module rng.
        class_pool / trait_pool: optional pre-filtered pools (perf).
        audit: emit `adventurer_generated` audit log row.
    """
    # ROUND 6B FASE A — circular import resolved: pure primitives now live
    # in `app.adventurers.common`. We pass `forced_rarity` directly so we
    # no longer need the old `_rec.RARITY_WEIGHTS` monkey-patch trick.
    # ROUND 6B FASE C — body simplified (CC≈3, was CC≈21) by extracting the
    # trait-floor guard and the audit emit into private helpers.
    from app.adventurers.common import _generate_candidate as _legacy_gen
    from app.adventurers.common import _rng as _module_rng

    now = now or datetime.now(timezone.utc)
    rng = rng or _module_rng

    classes = class_pool if class_pool is not None else await filter_safe_class_pool(db)
    if not classes:
        # Fallback: no safe classes available → caller must handle
        raise RuntimeError("adventurer_generator: no safe classes in pool")

    traits = trait_pool if trait_pool is not None else await filter_safe_trait_pool(db)

    # Rarity is decided HERE so we can run post-roll guards before the
    # base generator returns.
    rarity = _weighted_choice(rng, RARITY_WEIGHTS)
    klass = rng.choice(classes)

    # Build the candidate via the shared generator. `forced_rarity` injects
    # our pre-decided rarity so stat-roll logic stays in ONE place.
    candidate = _legacy_gen(
        klass,
        guild_id,
        now,
        traits_pool=traits,
        rng=rng,
        forced_rarity=rarity,
    )

    # Post-roll guards (Legendary/Epic) — applied AFTER stats are rolled.
    candidate = _enforce_legendary_floor(rng, candidate, rarity)
    candidate = _ensure_trait_floor(
        rng=rng, candidate=candidate, traits=traits, rarity=rarity,
    )

    if audit:
        await _emit_generated_audit(
            db,
            candidate=candidate,
            guild_id=guild_id,
            rarity=rarity,
            klass=klass,
            audit_source=audit_source,
        )

    return candidate


__all__ = [
    "generate_candidate",
    "filter_safe_class_pool",
    "filter_safe_trait_pool",
    "new_rng_for_tests",
    "_weighted_choice",
    "_count_positive_traits",
    "_stat_max_value",
]
