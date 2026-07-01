"""ROUND 11.2 TASK 6 G3 — Public stats catalog (data-driven).

Single source of truth for the player-facing stats documentation.
Consumed by `GET /api/stats/catalog` and rendered in the Guide page.

Rule: document ONLY stats that are actually used by the Adventurer model
and have implemented effects. Stats marked `implemented=False` are
descriptive-only and surfaced with an "effetto non ancora applicato"
notice on the FE.

When adding a new stat: update this catalog + the i18n locales
(`frontend/src/i18n/lang/{it,en}.json`) so the Guide stays in sync.
"""
from __future__ import annotations


# Each entry mirrors the Adventurer base stats. Numeric stats only —
# we exclude derived/computed values (PWR is included as a synthesis stat
# to explain the relationship).
STATS_CATALOG: list[dict] = [
    {
        "key": "strength",
        "display_name_it": "Forza",
        "display_name_en": "Strength",
        "description_it": "Determina il danno fisico inflitto e la capacità di equipaggiare armi pesanti.",
        "description_en": "Determines physical damage and ability to equip heavy weapons.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats", "expedition-preview"],
        "implemented": True,
    },
    {
        "key": "agility",
        "display_name_it": "Agilità",
        "display_name_en": "Agility",
        "description_it": "Influenza schivata, iniziativa e probabilità di colpi critici.",
        "description_en": "Influences dodge, initiative, and critical-hit chance.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats"],
        "implemented": True,
    },
    {
        "key": "intellect",
        "display_name_it": "Intelletto",
        "display_name_en": "Intellect",
        "description_it": "Aumenta la potenza degli incantesimi e il rendimento dei contratti tecnici.",
        "description_en": "Boosts spell power and yield on intellectual contracts.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats"],
        "implemented": True,
    },
    {
        "key": "endurance",
        "display_name_it": "Resistenza",
        "display_name_en": "Endurance",
        "description_it": "Determina HP base e resistenza a fatigue/morale loss durante le spedizioni.",
        "description_en": "Sets base HP and fatigue/morale resistance during expeditions.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats", "roster-health"],
        "implemented": True,
    },
    {
        "key": "faith",
        "display_name_it": "Fede",
        "display_name_en": "Faith",
        "description_it": "Migliora cura ricevuta, resistenze magiche e bonus su classi sacre.",
        "description_en": "Improves healing received, magic resistance, and sacred-class bonuses.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats"],
        "implemented": True,
    },
    {
        "key": "stamina",
        "display_name_it": "Stamina",
        "display_name_en": "Stamina",
        "description_it": "Energia disponibile per le spedizioni. Si rigenera con il tempo / strutture / inn.",
        "description_en": "Available energy for expeditions. Regenerates over time / via buildings / inn.",
        "affects_pwr": False,
        "ui_locations": ["adventurer-card", "expedition-preview"],
        "implemented": True,
    },
    {
        "key": "morale",
        "display_name_it": "Morale",
        "display_name_en": "Morale",
        "description_it": "Stato d'animo. Basso → penalità a XP/loot fino al recupero (Inn).",
        "description_en": "Mood state. Low → XP/loot penalties until recovery (Inn).",
        "affects_pwr": False,
        "ui_locations": ["adventurer-card", "roster-health"],
        "implemented": True,
    },
    {
        "key": "level",
        "display_name_it": "Livello",
        "display_name_en": "Level",
        "description_it": "Livello attuale dell'avventuriero (1-30). Sblocca specializzazioni a Lv5+.",
        "description_en": "Current adventurer level (1-30). Unlocks specializations at Lv5+.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats", "all-rosters"],
        "implemented": True,
    },
    {
        "key": "experience",
        "display_name_it": "Esperienza",
        "display_name_en": "Experience",
        "description_it": "Punti XP accumulati. Si guadagnano da spedizioni, contratti e training.",
        "description_en": "Accumulated XP. Earned from expeditions, contracts, and training.",
        "affects_pwr": False,
        "ui_locations": ["adventurer-card", "detail-stats"],
        "implemented": True,
    },
    {
        "key": "power_score",
        "display_name_it": "PWR (Punteggio Potere)",
        "display_name_en": "PWR (Power Score)",
        "description_it": "Sintesi numerica del potere totale: somma pesata di STR+AGI+INT+END+FTH + bonus equip + specializzazione. Usato per il match-making delle spedizioni e per il roster ranking.",
        "description_en": "Total power score: weighted sum of STR+AGI+INT+END+FTH + equipment bonus + specialization. Used for expedition match-making and roster ranking.",
        "affects_pwr": True,  # is the synthesis itself
        "ui_locations": ["adventurer-card", "detail-stats", "ranking", "expedition-preview"],
        "implemented": True,
    },
    {
        "key": "rarity",
        "display_name_it": "Rarità",
        "display_name_en": "Rarity",
        "description_it": "Common / Uncommon / Rare / Epic / Legendary. Influenza stats iniziali e cap.",
        "description_en": "Common / Uncommon / Rare / Epic / Legendary. Influences starting stats and caps.",
        "affects_pwr": True,
        "ui_locations": ["adventurer-card", "detail-stats", "recruitment"],
        "implemented": True,
    },
]


def get_public_stats_catalog() -> list[dict]:
    """Return the public stats catalog list (defensive copy)."""
    return [dict(s) for s in STATS_CATALOG]


__all__ = ["STATS_CATALOG", "get_public_stats_catalog"]
