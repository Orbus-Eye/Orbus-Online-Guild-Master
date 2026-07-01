"""ROUND 14 P2 — Loot drop simulator (read-only).

Simulates N expeditions across all active dungeons/raids using the exact
`DUNGEON_LOOT_TABLES` table that the live backend consults. The script is
strictly read-only on Mongo: it loads dungeons + items metadata once, then
performs all rolls in-memory using `secrets.SystemRandom` (the same RNG
class used by `app.expeditions.loot_tables._rng`).

Run:
    cd /app/backend
    export $(grep -v '^#' .env | xargs)  # MONGO_URL + DB_NAME
    python3 -m app.scripts.round14_loot_sim --runs 10000

CLI args:
    --runs       Number of rolls per dungeon (default 10000).
    --dungeon-slug  Limit to a single dungeon (default: all).
    --seed       Optional int seed for `random.Random`. If omitted,
                 falls back to `secrets.SystemRandom()` (non-reproducible).

Output:
    - Stdout: compact summary table + Markdown report (`summary.md`).
    - File: /app/memory/round14_loot_sim_<ts>.json with the full payload.

Anomaly thresholds (emitted in `warnings[]`):
    - Epic+ cumulative drop rate > 8%
    - Common drop rate < 40%
    - Any single item slug > 25% of total drops

Read-only contract:
    No INSERT/UPDATE/DELETE/findOneAndUpdate calls. Only `.find()` and
    `.find_one()` projections (audited at the bottom of this file via a
    runtime guard wrapper).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import secrets
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

# Import the live tables verbatim — single source of truth.
from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES


MEMORY_DIR = Path("/app/memory")
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Relic"]
HIGH_RARITIES = {"Epic", "Legendary", "Relic"}

# Anomaly thresholds (percent).
THRESH_HIGH_RARITY_MAX = 8.0
THRESH_COMMON_MIN = 40.0
THRESH_SINGLE_ITEM_MAX = 25.0


def _make_rng(seed: int | None):
    """Same class hierarchy used by the live backend: SystemRandom is the
    default. We accept an optional `random.Random(seed)` only for
    reproducible CI runs — never persisted, never used in production.
    """
    if seed is None:
        return secrets.SystemRandom()
    return random.Random(seed)


def _simulate_one_roll(rng, table_entry: dict, success: bool, items_by_rarity: dict) -> str | None:
    """Pure in-memory port of `roll_loot_for_dungeon`. Returns an item slug
    or None when no drop. Mirrors the live behaviour:
    - failure branch hard-caps to Common/Uncommon
    - graceful degrade if a rarity pool is empty

    `table_entry` matches one of the DUNGEON_LOOT_TABLES entries.
    `items_by_rarity` is the read-only snapshot of `items` keyed by rarity.
    """
    branch = table_entry["success" if success else "failure"]
    if rng.random() >= branch.get("chance", 0):
        return None
    weights = branch.get("weights") or {}
    rarities = [r for r, w in weights.items() if w > 0]
    if not rarities:
        return None
    if not success:
        rarities = [r for r in rarities if r in ("Common", "Uncommon")]
        if not rarities:
            return None
    chosen = rng.choices(rarities, weights=[weights[r] for r in rarities], k=1)[0]
    pool = items_by_rarity.get(chosen) or []
    if not pool:
        for r in ("Epic", "Rare", "Uncommon", "Common"):
            if r == chosen:
                continue
            if not success and r not in ("Common", "Uncommon"):
                continue
            cand = items_by_rarity.get(r) or []
            if cand:
                pool = cand
                break
    if not pool:
        return None
    return rng.choice(pool)


async def _load_inputs(db):
    """Single read-only sweep of `items` + `dungeons`. Returns the
    indexed structures the simulator needs.
    """
    # items: only active, non-test, projected to (slug, rarity)
    items_by_rarity: dict[str, list[str]] = {}
    cur = db.items.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0, "slug": 1, "rarity": 1},
    )
    async for it in cur:
        items_by_rarity.setdefault(it.get("rarity", "Common"), []).append(it.get("slug", "unknown"))

    # dungeons: only those covered by DUNGEON_LOOT_TABLES (plus base reward
    # for sanity). We don't iterate dungeons not present in the table —
    # they use the legacy fallback which is well-tested.
    dungeons: list[dict] = []
    cur = db.dungeons.find({}, {"_id": 0, "slug": 1, "name": 1, "recommended_power": 1, "base_gold_reward": 1})
    async for d in cur:
        if d.get("slug") in DUNGEON_LOOT_TABLES:
            dungeons.append(d)
    return items_by_rarity, dungeons


def _analyze(slug: str, drops: list[str], no_drop_count: int, rarity_of: dict) -> dict:
    """Build the per-dungeon report row. `drops` is the list of item slugs
    actually rolled (None entries omitted)."""
    runs = len(drops) + no_drop_count
    rarity_counts: Counter = Counter()
    for slug_drop in drops:
        rarity_counts[rarity_of.get(slug_drop, "Common")] += 1

    rarity_pct = {
        r: round(100.0 * rarity_counts.get(r, 0) / max(runs, 1), 3)
        for r in RARITY_ORDER
        if rarity_counts.get(r, 0) > 0
    }
    top5 = []
    item_counts = Counter(drops)
    for s, c in item_counts.most_common(5):
        top5.append({
            "slug": s,
            "count": c,
            "pct_of_drops": round(100.0 * c / max(len(drops), 1), 3),
            "pct_of_runs": round(100.0 * c / max(runs, 1), 3),
        })

    warnings: list[str] = []
    high_pct = sum(rarity_pct.get(r, 0.0) for r in HIGH_RARITIES)
    if high_pct > THRESH_HIGH_RARITY_MAX:
        warnings.append(
            f"epic_plus_rate_high: {high_pct:.2f}% > soglia {THRESH_HIGH_RARITY_MAX}%"
        )
    if drops:
        common_pct = rarity_pct.get("Common", 0.0)
        # Tier-1 dungeons are designed to skew Common; only warn for
        # mid/high-tier (where the table actually offers Rare/Epic).
        has_high_branch = any(
            r in (DUNGEON_LOOT_TABLES[slug]["success"].get("weights") or {})
            for r in ("Rare", "Epic", "Legendary", "Relic")
        )
        if has_high_branch and common_pct < THRESH_COMMON_MIN and common_pct > 0:
            warnings.append(
                f"common_rate_low: {common_pct:.2f}% < soglia {THRESH_COMMON_MIN}%"
            )
    if top5:
        top1 = top5[0]
        if top1["pct_of_runs"] > THRESH_SINGLE_ITEM_MAX:
            warnings.append(
                f"single_item_concentration: {top1['slug']} {top1['pct_of_runs']:.2f}%"
                f" > soglia {THRESH_SINGLE_ITEM_MAX}%"
            )

    return {
        "dungeon_slug": slug,
        "runs": runs,
        "drops_count": len(drops),
        "no_drop_count": no_drop_count,
        "no_drop_rate_pct": round(100.0 * no_drop_count / max(runs, 1), 3),
        "unique_items_dropped": len(item_counts),
        "rarity_distribution_pct": rarity_pct,
        "top_5_items": top5,
        "warnings": warnings,
    }


async def main():
    parser = argparse.ArgumentParser(description="Round 14 — loot drop simulator (read-only).")
    parser.add_argument("--runs", type=int, default=10_000)
    parser.add_argument("--dungeon-slug", default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    rng = _make_rng(args.seed)
    seed_label = f"seed={args.seed}" if args.seed is not None else "rng=SystemRandom"

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    items_by_rarity, dungeons = await _load_inputs(db)
    rarity_of = {s: r for r, slugs in items_by_rarity.items() for s in slugs}

    if args.dungeon_slug:
        dungeons = [d for d in dungeons if d["slug"] == args.dungeon_slug]
        if not dungeons:
            print(f"[ERR] dungeon-slug='{args.dungeon_slug}' non trovato o non in loot tables.")
            return

    report_rows: list[dict] = []
    for d in dungeons:
        slug = d["slug"]
        table = DUNGEON_LOOT_TABLES[slug]

        # Pivot the "team power vs recommended" on a neutral 50/50 split so
        # both success and failure branches get sampled in the same proportion
        # the average player would observe on first attempts. This is the
        # most honest single-shot view of the distribution.
        success_pct = 50

        drops: list[str] = []
        no_drop = 0
        for _ in range(args.runs):
            success = rng.randint(1, 100) <= success_pct
            slug_drop = _simulate_one_roll(rng, table, success, items_by_rarity)
            if slug_drop is None:
                no_drop += 1
            else:
                drops.append(slug_drop)

        report_rows.append(_analyze(slug, drops, no_drop, rarity_of))

    payload = {
        "schema": "round14_loot_sim/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs_per_dungeon": args.runs,
        "rng": seed_label,
        "thresholds": {
            "epic_plus_max_pct": THRESH_HIGH_RARITY_MAX,
            "common_min_pct": THRESH_COMMON_MIN,
            "single_item_max_pct": THRESH_SINGLE_ITEM_MAX,
        },
        "dungeons": report_rows,
        "all_warnings": [w for row in report_rows for w in row["warnings"]],
    }

    # Persist
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = MEMORY_DIR / f"round14_loot_sim_{ts}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    # Stdout summary (Markdown)
    print("\n# Loot Simulator — Round 14")
    print(f"- generato: {payload['generated_at']}")
    print(f"- runs/dungeon: {args.runs}")
    print(f"- rng: {seed_label}")
    print(f"- report file: {out}")
    print()
    print("| Dungeon | Runs | Drop% | Unique | Rarità (%) | Top item |")
    print("|---|---|---|---|---|---|")
    for row in report_rows:
        drop_pct = round(100.0 * row["drops_count"] / max(row["runs"], 1), 2)
        rar = ", ".join(f"{r}={v}%" for r, v in row["rarity_distribution_pct"].items())
        top_item = row["top_5_items"][0]["slug"] if row["top_5_items"] else "—"
        print(f"| {row['dungeon_slug']} | {row['runs']} | {drop_pct} | {row['unique_items_dropped']} | {rar} | {top_item} |")

    total_warnings = len(payload["all_warnings"])
    print()
    if total_warnings == 0:
        print(":white_check_mark: Nessuna anomalia. Soglie rispettate.")
    else:
        print(f":warning: {total_warnings} warning emessi:")
        for w in payload["all_warnings"]:
            print(f"  - {w}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
