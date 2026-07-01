"""ROUND 12.A — Elo rating helpers for PvP Arena.

Classic K=32 Elo. `expected_a = 1 / (1 + 10^((rating_b - rating_a)/400))`.
Rating floor=0; no ceiling.
"""
from __future__ import annotations

K_FACTOR = 32
RATING_FLOOR = 0


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def rating_delta(rating_a: int, rating_b: int, outcome: str) -> int:
    """`outcome` ∈ {"win", "draw", "loss"} → delta for player A."""
    score_map = {"win": 1.0, "draw": 0.5, "loss": 0.0}
    if outcome not in score_map:
        raise ValueError(f"invalid outcome: {outcome}")
    delta = K_FACTOR * (score_map[outcome] - expected_score(rating_a, rating_b))
    return int(round(delta))


def apply_match(rating_attacker: int, rating_defender: int, outcome: str) -> tuple[int, int]:
    """Returns the new (attacker_rating, defender_rating) after the match.
    `outcome` is the attacker's outcome.
    """
    inv = {"win": "loss", "loss": "win", "draw": "draw"}[outcome]
    da = rating_delta(rating_attacker, rating_defender, outcome)
    dd = rating_delta(rating_defender, rating_attacker, inv)
    new_a = max(RATING_FLOOR, rating_attacker + da)
    new_d = max(RATING_FLOOR, rating_defender + dd)
    return new_a, new_d


__all__ = ["expected_score", "rating_delta", "apply_match", "K_FACTOR"]
