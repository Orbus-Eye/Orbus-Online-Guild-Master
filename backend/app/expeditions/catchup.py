"""FASE 2.4 (2026-08-08) — Bonus XP di recupero ("catch-up") di gilda.

Regola minima richiesta (estendibile): quando i 5 avventurieri di livello
più alto della gilda hanno TUTTI raggiunto il livello 10, ogni
avventuriero sotto il livello 10 guadagna +25% di esperienza.

`CATCHUP_TIERS` è una tabella (soglia_livello, bonus) pensata per
crescere in futuro (es. aggiungere (30, 0.25)): si applica il bonus del
tier più alto la cui soglia è stata raggiunta dai top-5 e NON ancora
dall'avventuriero.

La parte pura (`catchup_multiplier`) non tocca il DB → unit-testabile.
Vedi memory/fase2_design_bilanciamento.md §7.
"""
from __future__ import annotations

CATCHUP_TIERS: tuple[tuple[int, float], ...] = (
    (10, 0.25),
)

TOP_N = 5


def catchup_multiplier(top_levels: list[int], adventurer_level: int) -> float:
    """Moltiplicatore XP per un avventuriero dato lo stato dei top-N.

    `top_levels` = livelli dei TOP_N avventurieri più alti della gilda
    (meno di TOP_N elementi → gilda troppo piccola, nessun bonus).
    """
    if len(top_levels) < TOP_N:
        return 1.0
    floor_level = min(int(v or 1) for v in top_levels[:TOP_N])
    lvl = int(adventurer_level or 1)
    best = 1.0
    for threshold, bonus in CATCHUP_TIERS:
        if floor_level >= threshold and lvl < threshold:
            best = max(best, 1.0 + bonus)
    return best


async def guild_top_levels(db, guild_id: str) -> list[int]:
    """Livelli dei TOP_N avventurieri attivi (non congedati) della gilda."""
    rows = await db.adventurers.find(
        {"guild_id": guild_id, "is_retired": {"$ne": True}},
        {"_id": 0, "level": 1},
    ).sort("level", -1).limit(TOP_N).to_list(TOP_N)
    return [int(r.get("level", 1) or 1) for r in rows]


__all__ = ["CATCHUP_TIERS", "TOP_N", "catchup_multiplier", "guild_top_levels"]
