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


DUNGEON_CURVE: dict[str, ContentCurve] = {
    "training-yard": ContentCurve(1, 15, 12, "tutorial"),
    # FASE 2.3 (2026-08-08) — la linea principale non è più "tutta da 3":
    # base 5, con i 3 come incursioni rapide e i 7 come grandi imprese.
    # I recommended_power dei dungeon passati a size maggiore scalano
    # ×(size_nuova/size_vecchia) così la difficoltà PER MEMBRO resta
    # identica. Tabella e razionale: memory/fase2_design_bilanciamento.md §6.
    # Team size autoritativa per slug: DUNGEON_TEAM_SIZE_TARGETS (sotto).
    "sewer-nest": ContentCurve(1, 35, 25, "tutorial"),
    "goblin-warrens": ContentCurve(5, 117, 50, "tutorial"),
    "bandit-hideout": ContentCurve(5, 75, 55, "tutorial"),
    "druid-grove": ContentCurve(10, 267, 150, "tutorial"),
    "shadow-crypts": ContentCurve(10, 283, 160, "tutorial"),
    "cursed-mines": ContentCurve(15, 333, 220, "early"),
    "sunken-library": ContentCurve(15, 215, 240, "early"),
    "lich-sanctum": ContentCurve(20, 408, 320, "early"),
    "dragons-hoard": ContentCurve(25, 642, 420, "early"),
    "storm-spire": ContentCurve(25, 483, 450, "early"),
    # Five-adventurer line.
    "wolf-den-5p": ContentCurve(10, 260, 150, "tutorial"),
    "frost-cave-5p": ContentCurve(15, 310, 225, "early"),
    "salt-marsh-5p": ContentCurve(20, 360, 300, "early"),
    "iron-foundry-5p": ContentCurve(25, 410, 400, "early"),
    "silent-monastery-5p": ContentCurve(30, 460, 500, "early"),
    "pirate-fleet-5p": ContentCurve(35, 510, 600, "mid"),
    "obsidian-arena-5p": ContentCurve(40, 560, 700, "mid"),
    "clockwork-vault-5p": ContentCurve(45, 610, 800, "mid"),
    "voidspire-5p": ContentCurve(50, 660, 900, "mid"),
    "infernal-pit-5p": ContentCurve(60, 760, 1100, "high"),
    "celestial-citadel-5p": ContentCurve(65, 810, 1250, "high"),
    # Seven-adventurer endgame dungeon. The former 860 target belonged to the
    # legacy five-member composition and understated current team power.
    "world-tree-roots-5p": ContentCurve(70, 1600, 1400, "high"),
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


RAID_CURVE: dict[str, ContentCurve] = {
    "moonfall-vigil": ContentCurve(40, 1500, 900, "mid"),
    "broken-bastion-siege": ContentCurve(60, 2400, 1500, "high"),
    "necropolis-bells": ContentCurve(70, 3500, 2200, "high"),
    "dragon-vault": ContentCurve(80, 8000, 3200, "endgame"),
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
