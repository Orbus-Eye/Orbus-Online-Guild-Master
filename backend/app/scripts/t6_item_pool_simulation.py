"""Deterministic Monte Carlo gate for the T6 dungeon and raid item pools."""
from __future__ import annotations

from collections import Counter
import argparse
import json
import random

from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES
from app.items.final_catalog import FINAL_ITEM_CATALOG, validate_final_catalog
from app.raids.contracts import RAID_CONTRACTS
from app.raids.loot import RAID_ITEM_DROP_PROFILES
from app.rewards.source_engine import SOURCE_POLICIES


DEFAULT_ITERATIONS = 100_000
DEFAULT_SEED = 608_080


def _simulate_branch(
    *,
    chance: float,
    weights: dict[str, int],
    iterations: int,
    rng: random.Random,
) -> dict:
    rarity_counts: Counter[str] = Counter()
    rarities = tuple(weights)
    rarity_weights = [weights[rarity] for rarity in rarities]
    for _ in range(iterations):
        if rng.random() >= chance:
            continue
        rarity_counts[
            rng.choices(rarities, weights=rarity_weights, k=1)[0]
        ] += 1
    drops = sum(rarity_counts.values())
    return {
        "iterations": iterations,
        "drops": drops,
        "observed_drop_rate": drops / iterations,
        "expected_drop_rate": chance,
        "rarity_counts": dict(sorted(rarity_counts.items())),
    }


def _source_rarity_pairs() -> set[tuple[str, str, str]]:
    return {
        (
            str(source.get("source_type") or ""),
            str(source.get("source_slug") or ""),
            str(item.get("rarity") or ""),
        )
        for item in FINAL_ITEM_CATALOG
        for source in item.get("acquisition_sources", [])
        if source.get("source_slug")
    }


def build_simulation_report(
    *,
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
) -> dict:
    if iterations < 10_000:
        raise ValueError("T6 simulation requires at least 10,000 iterations")
    catalog = validate_final_catalog(FINAL_ITEM_CATALOG)
    source_pairs = _source_rarity_pairs()
    errors: list[str] = list(catalog["errors"])
    rng = random.Random(seed)

    dungeon_results = {}
    for slug, table in sorted(DUNGEON_LOOT_TABLES.items()):
        dungeon_results[slug] = {}
        for outcome in ("success", "failure"):
            branch = table[outcome]
            result = _simulate_branch(
                chance=float(branch["chance"]),
                weights=dict(branch.get("weights") or {}),
                iterations=iterations,
                rng=rng,
            ) if branch.get("weights") else {
                "iterations": iterations,
                "drops": 0,
                "observed_drop_rate": 0.0,
                "expected_drop_rate": float(branch["chance"]),
                "rarity_counts": {},
            }
            dungeon_results[slug][outcome] = result
            if abs(
                result["observed_drop_rate"] - result["expected_drop_rate"]
            ) > 0.012:
                errors.append(f"simulation.dungeon_rate:{slug}:{outcome}")
            if set(result["rarity_counts"]) & {"Legendary", "Unique"}:
                errors.append(f"simulation.dungeon_endgame_leak:{slug}:{outcome}")
        allowed = set(table["success"].get("weights") or {})
        for rarity in allowed:
            if ("dungeon", slug, rarity) not in source_pairs:
                errors.append(f"simulation.dungeon_pool_missing:{slug}:{rarity}")

    raid_results = {}
    for slug, outcomes in sorted(RAID_ITEM_DROP_PROFILES.items()):
        raid_results[slug] = {}
        contract = RAID_CONTRACTS[slug]["reward_profile"]
        for outcome, (chance, weights) in outcomes.items():
            result = _simulate_branch(
                chance=chance,
                weights=weights,
                iterations=iterations,
                rng=rng,
            )
            raid_results[slug][outcome] = result
            if abs(result["observed_drop_rate"] - chance) > 0.012:
                errors.append(f"simulation.raid_rate:{slug}:{outcome}")
            if "Unique" in result["rarity_counts"]:
                errors.append(f"simulation.raid_unique_leak:{slug}:{outcome}")
            for rarity in weights:
                if rarity not in contract["allowed_rarities"]:
                    errors.append(f"simulation.raid_contract:{slug}:{rarity}")
                if ("raid", slug, rarity) not in source_pairs:
                    errors.append(f"simulation.raid_pool_missing:{slug}:{rarity}")

    ring_probability = SOURCE_POLICIES[
        "company_ring_ultra_rare"
    ]["private_drop_probability"]
    if ring_probability != 0.000001:
        errors.append("simulation.company_ring_probability")

    return {
        "valid": not errors,
        "errors": errors,
        "seed": seed,
        "iterations_per_branch": iterations,
        "catalog": {
            "version": catalog["catalog_version"],
            "total": catalog["total"],
            "rarity_counts": catalog["rarity_counts"],
            "class_counts": catalog["class_counts"],
            "universal_count": catalog["universal_count"],
            "sha256": catalog["sha256"],
        },
        "dungeons": dungeon_results,
        "raids": raid_results,
        "company_ring": {
            "probability_per_eligible_guild_event": ring_probability,
            "expected_grants_per_million_eligible_rolls": (
                ring_probability * 1_000_000
            ),
            "included_in_dungeon_or_raid_pool": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    report = build_simulation_report(
        iterations=args.iterations,
        seed=args.seed,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_ITERATIONS",
    "DEFAULT_SEED",
    "build_simulation_report",
]
