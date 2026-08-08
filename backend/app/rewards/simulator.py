"""Read-only reward simulations; never writes or grants inventory."""
from __future__ import annotations

import random

from app.rewards.source_engine import SOURCE_POLICIES


MAX_TESTER_TRIALS = 5_000_000


def simulate_company_ring(
    *,
    trials: int,
    seed: int = 20260729,
) -> dict:
    """Simulate the private ring roll without exposing a grant path."""
    count = int(trials)
    if count < 1 or count > MAX_TESTER_TRIALS:
        raise ValueError("reward.simulation.trials_out_of_range")
    probability = float(
        SOURCE_POLICIES["company_ring_ultra_rare"][
            "private_drop_probability"
        ]
    )
    rng = random.Random(seed)
    successes = sum(rng.random() < probability for _ in range(count))
    expected = count * probability
    return {
        "simulation_only": True,
        "grants_created": 0,
        "inventory_mutations": 0,
        "trials": count,
        "seed": seed,
        "successes": successes,
        "expected_successes": expected,
        "probability": probability,
        "one_in": round(1 / probability),
    }


def source_inflation_projection(
    *,
    eligible_runs: int,
    grants_per_run: float,
    duplicate_conversion_rate: float = 0.0,
) -> dict:
    """Project gross/net grants for a source before enabling its pool."""
    runs = max(0, int(eligible_runs))
    rate = max(0.0, float(grants_per_run))
    conversion = min(1.0, max(0.0, float(duplicate_conversion_rate)))
    gross = runs * rate
    converted = gross * conversion
    return {
        "eligible_runs": runs,
        "gross_grants": gross,
        "duplicate_conversions": converted,
        "net_new_items": gross - converted,
        "requires_review": gross - converted > 10_000,
    }


__all__ = [
    "MAX_TESTER_TRIALS",
    "simulate_company_ring",
    "source_inflation_projection",
]
