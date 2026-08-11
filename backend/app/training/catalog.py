"""FASE 9I — ADDESTRAMENTO (solo XP): curva e costanti.

Il vecchio contenuto di questo modulo (SPEC_DEFINITIONS ROUND 6C, costi
di specializzazione, respec) è stato eliminato insieme alle
specializzazioni: l'Addestramento ora fornisce SOLO esperienza.

Design della velocità (derivata dalla curva XP reale del runtime,
`xp_required_for_next_level(L) = 125 · L^1.5`):

  * una sessione PIENA di 24 ore vale il **75% del livello corrente**
    (TRAINING_LEVEL_FRACTION_PER_DAY = 0.75);
  * col bonus recupero (+50%) si arriva a ~1.13 livelli in 24h:
    utile ma LENTA — dungeon e raid restano il leveling principale
    (una singola run di dungeon dà una frazione di livello in minuti,
    non in ore);
  * al livello massimo (80) non ci si può addestrare (xp/h = 0).

Simulazione (xp/h base, % di livello in 24h — verificata dai test):

  | Lv | xp richiesti | xp/h | 24h (base) | 24h (+50% recupero) |
  |----|-------------|------|-----------|---------------------|
  |  1 |         125 |    4 | ~77%      | ~115%               |
  | 10 |        3953 |  124 | ~75%      | ~113%               |
  | 20 |       11180 |  350 | ~75%      | ~113%               |
  | 40 |       31623 |  989 | ~75%      | ~113%               |
  | 60 |       58095 | 1816 | ~75%      | ~113%               |
  | 80 |       cap   |    0 | —         | —                   |

Bonus recupero (+50%): SOLO per l'Addestramento; si applica quando il
livello dell'avventuriero è sotto il benchmark di gilda (media dei 5
avventurieri attivi più alti). NON si somma ad altri moltiplicatori XP:
l'XP di addestramento è piatta — niente tratti xp_gain, niente
consumabili (Pietra della Conoscenza), niente catch-up spedizioni.
"""
from __future__ import annotations

import math

from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.progression import xp_required_for_next_level

TRAINING_CAPACITY = 2                 # avventurieri contemporanei per gilda
TRAINING_MAX_HOURS = 24               # durata massima singola sessione
TRAINING_MIN_HOURS = 1
TRAINING_LEVEL_FRACTION_PER_DAY = 0.75
TRAINING_CATCHUP_MULTIPLIER = 1.5     # +50% per chi è sotto il benchmark
CATCHUP_TOP_N = 5                     # benchmark: media dei top-5 livelli


def training_xp_per_hour(level: int) -> int:
    """XP/ora base per un avventuriero del livello dato (0 al cap)."""
    lvl = max(1, int(level or 1))
    if lvl >= ADVENTURER_MAX_LEVEL:
        return 0
    threshold = xp_required_for_next_level(lvl)
    return max(1, math.ceil(
        threshold * TRAINING_LEVEL_FRACTION_PER_DAY / TRAINING_MAX_HOURS
    ))


def catchup_benchmark_level(roster_levels: list[int]) -> int:
    """Benchmark di gilda: media (arrotondata) dei top-5 livelli."""
    top = sorted((int(v or 1) for v in roster_levels), reverse=True)[:CATCHUP_TOP_N]
    if not top:
        return 1
    return int(round(sum(top) / len(top)))


def has_training_catchup(level: int, benchmark_level: int) -> bool:
    return int(level or 1) < int(benchmark_level or 1)


def training_xp_for_session(
    level: int, hours: float, *, catchup: bool,
) -> int:
    """XP totale maturata per `hours` ore di addestramento (flat, server-side)."""
    rate = training_xp_per_hour(level)
    if rate <= 0 or hours <= 0:
        return 0
    multiplier = TRAINING_CATCHUP_MULTIPLIER if catchup else 1.0
    return int(math.floor(rate * min(hours, TRAINING_MAX_HOURS) * multiplier))


def simulate_training_curve(levels=(1, 10, 20, 40, 60, 80)) -> list[dict]:
    """Tabella di simulazione per report/test (xp/h e frazione di livello/24h)."""
    rows = []
    for lvl in levels:
        rate = training_xp_per_hour(lvl)
        threshold = xp_required_for_next_level(lvl)
        day_base = rate * TRAINING_MAX_HOURS
        rows.append({
            "level": lvl,
            "xp_required": threshold,
            "xp_per_hour": rate,
            "xp_24h_base": day_base,
            "level_fraction_24h_base": (
                round(day_base / threshold, 3) if threshold else 0.0
            ),
            "level_fraction_24h_catchup": (
                round(day_base * TRAINING_CATCHUP_MULTIPLIER / threshold, 3)
                if threshold else 0.0
            ),
        })
    return rows


__all__ = [
    "CATCHUP_TOP_N",
    "TRAINING_CAPACITY",
    "TRAINING_CATCHUP_MULTIPLIER",
    "TRAINING_LEVEL_FRACTION_PER_DAY",
    "TRAINING_MAX_HOURS",
    "TRAINING_MIN_HOURS",
    "catchup_benchmark_level",
    "has_training_catchup",
    "simulate_training_curve",
    "training_xp_for_session",
    "training_xp_per_hour",
]
