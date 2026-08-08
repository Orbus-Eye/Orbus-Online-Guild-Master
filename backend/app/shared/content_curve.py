"""Authoritative level-80 PvE progression curve.

The curve keeps level gates, expected power and XP rewards together so a
content seed cannot be moved to a new level band without also being re-tuned.
It intentionally describes the current 23 dungeons and four raids; future
content must extend these tables instead of introducing local literals.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.shared.constants import ADVENTURER_MAX_LEVEL


@dataclass(frozen=True)
class ContentCurve:
    required_level: int
    recommended_power: int
    xp_reward: int
    bucket: str


ADVENTURER_LEVEL_BANDS: tuple[tuple[int, int, str], ...] = (
    (1, 10, "novizio"),
    (11, 20, "iniziato"),
    (21, 30, "avventuriero"),
    (31, 40, "esperto"),
    (41, 50, "veterano"),
    (51, 60, "eroe"),
    (61, 70, "maestro"),
    (71, ADVENTURER_MAX_LEVEL, "endgame"),
)


# FASE 8A (2026-08-08) — REBALANCE DIFFICOLTÀ. I recommended_power sono
# derivati dal modello formale `app/shared/power_model.py`: parità (=50%
# di successo) con la squadra MEDIA di pari livello. La vecchia curva
# cresceva molto più piano del potere reale (10 slot di equipaggiamento)
# e permetteva a squadre Lv15 di farmare contenuto Lv40.
# Eccezioni documentate:
#   * training-yard / sewer-nest: valori tutorial autorati (il modello
#     assume slot equip che una gilda day-1 non ha ancora);
#   * druid-grove / shadow-crypts: alzati al vincolo minimo ≥1.5× la
#     vecchia curva (il modello puro dava ×1.4).
# Tabelle e simulazioni: memory/fase8_dungeon_difficulty_rebalance.md
DUNGEON_CURVE: dict[str, ContentCurve] = {
    "training-yard": ContentCurve(1, 90, 12, "tutorial"),
    # FASE 2.3 — base 5, incursioni rapide da 3, grandi imprese da 7.
    # Team size autoritativa per slug: DUNGEON_TEAM_SIZE_TARGETS (sotto).
    "sewer-nest": ContentCurve(1, 110, 25, "tutorial"),
    "goblin-warrens": ContentCurve(5, 315, 50, "tutorial"),
    "bandit-hideout": ContentCurve(5, 200, 55, "tutorial"),
    "druid-grove": ContentCurve(10, 400, 150, "tutorial"),
    "shadow-crypts": ContentCurve(10, 425, 160, "tutorial"),
    "cursed-mines": ContentCurve(15, 535, 220, "early"),
    "sunken-library": ContentCurve(15, 330, 240, "early"),
    "lich-sanctum": ContentCurve(20, 670, 320, "early"),
    "dragons-hoard": ContentCurve(25, 1075, 420, "early"),
    "storm-spire": ContentCurve(25, 775, 450, "early"),
    # Five-adventurer line.
    "wolf-den-5p": ContentCurve(10, 390, 150, "tutorial"),
    "frost-cave-5p": ContentCurve(15, 535, 225, "early"),
    "salt-marsh-5p": ContentCurve(20, 670, 300, "early"),
    "iron-foundry-5p": ContentCurve(25, 775, 400, "early"),
    "silent-monastery-5p": ContentCurve(30, 850, 500, "early"),
    "pirate-fleet-5p": ContentCurve(35, 1100, 600, "mid"),
    "obsidian-arena-5p": ContentCurve(40, 1350, 700, "mid"),
    "clockwork-vault-5p": ContentCurve(45, 1425, 800, "mid"),
    "voidspire-5p": ContentCurve(50, 1570, 900, "mid"),
    "infernal-pit-5p": ContentCurve(60, 2240, 1100, "high"),
    "celestial-citadel-5p": ContentCurve(65, 2315, 1250, "high"),
    "world-tree-roots-5p": ContentCurve(70, 3335, 1400, "high"),
}

# Every rarity/source pair declared by the runtime dungeon loot tables. The
# catalog generator walks these lists so a configured rarity can never point
# at an empty authored pool.
DUNGEON_RARITY_SOURCE_POOLS: dict[str, tuple[str, ...]] = {
    "Common": (
        "training-yard", "sewer-nest", "goblin-warrens", "bandit-hideout",
        "druid-grove", "shadow-crypts", "cursed-mines", "sunken-library",
        "wolf-den-5p", "frost-cave-5p", "salt-marsh-5p",
        "iron-foundry-5p", "silent-monastery-5p", "pirate-fleet-5p",
        "infernal-pit-5p", "celestial-citadel-5p", "world-tree-roots-5p",
    ),
    "Uncommon": (
        "sewer-nest", "goblin-warrens", "bandit-hideout", "druid-grove",
        "shadow-crypts", "cursed-mines", "sunken-library", "lich-sanctum",
        "dragons-hoard", "storm-spire", "wolf-den-5p", "frost-cave-5p",
        "salt-marsh-5p", "iron-foundry-5p", "silent-monastery-5p",
        "pirate-fleet-5p", "obsidian-arena-5p", "clockwork-vault-5p",
        "voidspire-5p", "infernal-pit-5p", "celestial-citadel-5p",
        "world-tree-roots-5p",
    ),
    "Rare": (
        "druid-grove", "shadow-crypts", "cursed-mines", "sunken-library",
        "lich-sanctum", "dragons-hoard", "storm-spire", "iron-foundry-5p",
        "silent-monastery-5p", "pirate-fleet-5p", "obsidian-arena-5p",
        "clockwork-vault-5p", "voidspire-5p", "infernal-pit-5p",
        "celestial-citadel-5p", "world-tree-roots-5p",
    ),
    "Epic": (
        "lich-sanctum", "dragons-hoard", "storm-spire",
        "obsidian-arena-5p", "clockwork-vault-5p", "voidspire-5p",
        "infernal-pit-5p", "celestial-citadel-5p", "world-tree-roots-5p",
    ),
}


# FASE 2.3 — distribuzione 3/5/7 autoritativa per la linea principale.
# I dungeon con suffisso `-5p` restano a 5 (world-tree-roots-5p a 7) e
# NON compaiono qui. Lo script
# `app/scripts/fase2_redistribuzione_team_size.py` applica questa
# tabella al DB (required_team_size + recommended_power dalla curve).
DUNGEON_TEAM_SIZE_TARGETS: dict[str, int] = {
    "training-yard": 3,     # tutorial: il reclutamento iniziale dà 3 eroi
    "sewer-nest": 3,        # tutorial
    "goblin-warrens": 5,
    "bandit-hideout": 3,    # incursione rapida
    "druid-grove": 5,
    "shadow-crypts": 5,
    "cursed-mines": 5,
    "sunken-library": 3,    # incursione rapida
    "lich-sanctum": 5,
    "dragons-hoard": 7,     # grande impresa
    "storm-spire": 5,
}


# FASE 8A/8B — curva raid dal modello (squadra media × severità raid
# +15%): i raid sono più severi del contenuto pari livello e l'accesso
# diventa PWR-driven (vedi raids power gate, FASE 8B).
RAID_CURVE: dict[str, ContentCurve] = {
    "moonfall-vigil": ContentCurve(40, 3100, 900, "mid"),
    "broken-bastion-siege": ContentCurve(60, 7700, 1500, "high"),
    "necropolis-bells": ContentCurve(70, 10925, 2200, "high"),
    "dragon-vault": ContentCurve(80, 24100, 3200, "endgame"),
}


def adventurer_level_band(level: int) -> str:
    """Return the public progression band for an adventurer level."""
    value = min(ADVENTURER_MAX_LEVEL, max(1, int(level or 1)))
    for start, end, name in ADVENTURER_LEVEL_BANDS:
        if start <= value <= end:
            return name
    return "endgame"


__all__ = [
    "ADVENTURER_LEVEL_BANDS",
    "ContentCurve",
    "DUNGEON_CURVE",
    "DUNGEON_RARITY_SOURCE_POOLS",
    "DUNGEON_TEAM_SIZE_TARGETS",
    "RAID_CURVE",
    "adventurer_level_band",
]
