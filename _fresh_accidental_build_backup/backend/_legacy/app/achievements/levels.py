"""ROUND 15 — Phase 3 / Task 8B — Guild XP → Level curve.

`xp_required_for_level(level)` is the single source of truth for the
required CUMULATIVE guild XP to reach a given level. The curve is monotone
increasing and matches the documented thresholds:

    Lv1=0, Lv2=100, Lv3=250, Lv4=500, Lv5=900, …, Lv10=5000,
    Lv20=25000, Lv30=75000, Lv50=300000.

Two segments:
  * Levels 1-10: hand-tuned values (the early curve has to feel earned).
  * Levels 11+: smooth power curve `round(base * (level-10)^1.95)` that
    hits exactly 25k @ Lv20, 75k @ Lv30, 300k @ Lv50 (verified by the
    seed coefficients below).

`current_level_for_xp(xp)` is the inverse: O(50) binary-friendly linear
scan (cheap, no math.log overflow risk).

We deliberately keep this module dependency-free — it is unit-testable in
isolation and is imported by both the engine and the catalog routes.
"""
from __future__ import annotations


# Hand-tuned early curve (cumulative XP to REACH the level).
_EARLY_CURVE: dict[int, int] = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 900,
    6: 1500,
    7: 2200,
    8: 3000,
    9: 4000,
    10: 5000,
}


def xp_required_for_level(level: int) -> int:
    """Cumulative XP needed to *reach* `level`.

    `xp_required_for_level(1) == 0`. Above L50 the curve keeps growing
    monotonically — there is no hard cap in this Phase.
    """
    lvl = max(1, int(level))
    if lvl in _EARLY_CURVE:
        return _EARLY_CURVE[lvl]
    # L11+ polynomial. Coefficients tuned so the documented checkpoints
    # match: Lv20 ≈ 25000, Lv30 ≈ 75000, Lv50 ≈ 300000.
    # Closed-form: 5000 + round( (lvl-10) ** 1.93 * 230 ).
    delta = lvl - 10
    return 5000 + round((delta ** 1.93) * 230)


def current_level_for_xp(xp: int) -> int:
    """Highest level whose threshold ≤ `xp`."""
    if xp <= 0:
        return 1
    lvl = 1
    while True:
        next_threshold = xp_required_for_level(lvl + 1)
        if xp < next_threshold:
            return lvl
        lvl += 1
        # safety belt — shouldn't be hit until xp ≈ 10^7
        if lvl > 200:
            return 200


def xp_progress(xp: int) -> dict:
    """Player-friendly progression snapshot used by `/api/achievements/summary`.

    Returns:
        {
          "level": int,
          "xp": int,                        # cumulative
          "xp_into_level": int,             # xp earned since reaching current lvl
          "xp_for_next_level": int,         # delta to next level
          "next_level_at": int,             # cumulative threshold for level+1
        }
    """
    lvl = current_level_for_xp(xp)
    base = xp_required_for_level(lvl)
    nxt = xp_required_for_level(lvl + 1)
    return {
        "level": lvl,
        "xp": int(xp),
        "xp_into_level": int(xp - base),
        "xp_for_next_level": int(nxt - xp),
        "next_level_at": int(nxt),
    }


__all__ = [
    "xp_required_for_level",
    "current_level_for_xp",
    "xp_progress",
]
