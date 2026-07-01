"""ROUND 15 — Fase 2 / Monte Carlo material drop simulation.

Runs 5000 simulated expedition completions against a representative T2
dungeon (Shadow Crypts) and reports the empirical per-material drop
rate versus the documented baseline + boosted rate.

No DB writes. Pure roller invocation against a mock item catalog.

Run:
    cd /app/backend
    python3 -m app.scripts.round15_phase2_evidence_monte_carlo
"""
from __future__ import annotations

import asyncio
from collections import Counter

from app.expeditions.material_drop_tables import (
    BOOST_FACTOR,
    RARITY_CAP,
    TIER_MATERIAL_TABLE,
    boosted_rate,
    roll_materials_for_dungeon,
)


N_RUNS = 5000


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._i = 0

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        v = self._docs[self._i]
        self._i += 1
        return v


class _FakeColl:
    def find(self, *a, **kw):
        return _FakeCursor([
            {"slug": "iron_shard"}, {"slug": "raw_leather"},
            {"slug": "healing_herb"}, {"slug": "arcane_dust"},
            {"slug": "dull_gem"}, {"slug": "dragon_essence"},
        ])


class _FakeDB:
    items = _FakeColl()


async def main():
    dungeon = {"slug": "shadow-crypts", "base_xp_reward": 60}
    counts: Counter = Counter()
    rarity_counts: Counter = Counter()
    bucket = {"with_mats": 0, "no_mats": 0}

    for _ in range(N_RUNS):
        drops = await roll_materials_for_dungeon(_FakeDB(), dungeon, True)
        if drops:
            bucket["with_mats"] += 1
        else:
            bucket["no_mats"] += 1
        for d in drops:
            counts[d["slug"]] += 1
            rarity_counts[d["rarity"]] += 1

    print(f"=== Monte Carlo — Shadow Crypts T2 — {N_RUNS} runs ===\n")
    print(f"  with_materials: {bucket['with_mats']} ({bucket['with_mats']*100/N_RUNS:.1f}%)")
    print(f"  no_materials:   {bucket['no_mats']} ({bucket['no_mats']*100/N_RUNS:.1f}%)\n")

    print(f"=== Per-material empirical vs documented ===")
    print(f"  {'slug':18s} {'rarity':10s} {'baseline':>10s} {'+70%boost':>12s} {'cap':>8s} {'final':>8s} {'observed':>10s}")
    for slug, rarity, base, _q in TIER_MATERIAL_TABLE["T2"]:
        boosted = round(base * BOOST_FACTOR, 4)
        cap = RARITY_CAP[rarity]
        final = boosted_rate(base, rarity)
        observed = counts[slug] / N_RUNS
        ratio = observed / base if base else 0
        marker = "✅" if observed >= base * BOOST_FACTOR * 0.85 else "⚠"
        print(f"  {slug:18s} {rarity:10s} {base*100:>9.1f}% "
              f"{boosted*100:>11.1f}% {cap*100:>7.1f}% "
              f"{final*100:>7.1f}% {observed*100:>9.2f}% "
              f"(ratio_vs_baseline={ratio:.2f}x) {marker}")

    print(f"\n=== Per-rarity totals (counts) ===")
    for r in ("common", "uncommon", "rare", "epic", "legendary"):
        cnt = rarity_counts.get(r, 0)
        print(f"  {r:10s} = {cnt:5d}  cap={RARITY_CAP[r]*100:>5.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
