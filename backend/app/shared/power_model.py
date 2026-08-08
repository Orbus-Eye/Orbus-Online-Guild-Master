"""FASE 8A (2026-08-08) — Modello formale del potere delle squadre.

Questo modulo è la BASE MATEMATICA del rebalance di difficoltà: modella
il potere reale ottenibile da squadre rappresentative a ogni livello,
derivato dalle formule effettive del gioco (misurate, non stimate):

  * stat iniziali: somma base di classe ≈ 32 (catalogo R16) + jitter
    medio +2.5 → ~34 alla creazione (`common._roll_stat`);
  * level-up: +1 stat core per livello (`services._resolve_levelup`);
  * potere base membro: somma_stat + livello×2 (`formulas`);
  * item: power_score = rarità + level//20; bonus primario =
    rarità + min(4, level//20); secondario ≈ ⌊primario/3⌋ da Rare in su
    (`items.final_catalog`); 10 slot fisici;
  * bonus ruoli squadra: fino a +25 (`compute_team_power`).

Le 4 fasce di equipaggiamento simulate ("tier"):
  sottopotenziata / media / ben_equipaggiata / molto_forte
La NUOVA curva recommended_power è definita come il potere della
squadra **media** di pari livello → parità = 50% di successo.

Usato da: script di audit `fase8_dungeon_difficulty_audit`, curve in
`content_curve.py` (valori derivati e fissati come literal), test di
accettazione. Vedi memory/fase8_dungeon_difficulty_rebalance.md.
"""
from __future__ import annotations

# ── Costanti misurate dal codice reale ───────────────────────────────────
BASE_STATS_START = 34      # somma 5 stat alla creazione (media con jitter)
STAT_GAIN_PER_LEVEL = 1    # +1 stat core per level-up
LEVEL_POWER_FACTOR = 2     # potere = stats + level*2
TEAM_ROLE_BONUS = 25       # Tank+Healer+DPS presenti (5+5+5+10)

# Rarità → "rarity score" (specchio di RARITY_BONUS del catalogo T6).
RARITY_SCORE = {"common": 1, "uncommon": 2, "rare": 4, "epic": 7,
                "legendary": 11}


def member_base_power(level: int) -> int:
    """Potere base (senza equip) di un avventuriero medio al livello L."""
    lvl = max(1, int(level))
    stats = BASE_STATS_START + (lvl - 1) * STAT_GAIN_PER_LEVEL
    return stats + lvl * LEVEL_POWER_FACTOR


def item_power(level: int, rarity_score: int) -> int:
    """Potere di UN item del catalogo a quel livello/rarità.

    power_score + bonus stat primaria + secondaria (da Rare in su).
    """
    lvl = max(1, int(level))
    ps = rarity_score + lvl // 20
    primary = rarity_score + min(4, lvl // 20)
    secondary = max(1, primary // 3) if rarity_score >= 4 else 0
    return ps + primary + secondary


# ── Fasce di equipaggiamento (tier) ──────────────────────────────────────
# (slot riempiti, rarity score prevalente) in funzione del livello.

def _tier_profile(level: int, tier: str) -> tuple[int, int]:
    lvl = max(1, int(level))
    if tier == "sottopotenziata":
        filled = min(10, 3 + lvl // 15)
        score = RARITY_SCORE["common"]
    elif tier == "media":
        filled = min(10, 5 + lvl // 12)
        if lvl < 12:
            score = RARITY_SCORE["common"]
        elif lvl < 35:
            score = RARITY_SCORE["uncommon"]
        elif lvl < 60:
            score = RARITY_SCORE["rare"]
        else:
            score = RARITY_SCORE["epic"]
    elif tier == "ben_equipaggiata":
        filled = 10
        if lvl < 20:
            score = RARITY_SCORE["uncommon"]
        elif lvl < 50:
            score = RARITY_SCORE["rare"]
        else:
            score = RARITY_SCORE["epic"]
    elif tier == "molto_forte":
        filled = 10
        if lvl < 25:
            score = RARITY_SCORE["rare"]
        elif lvl < 70:
            score = RARITY_SCORE["epic"]
        else:
            score = RARITY_SCORE["legendary"]
    else:
        raise ValueError(f"tier sconosciuto: {tier}")
    return filled, score


TIERS = ("sottopotenziata", "media", "ben_equipaggiata", "molto_forte")


def member_power(level: int, tier: str = "media") -> int:
    """Potere totale (base + equip) di un membro della fascia data."""
    filled, score = _tier_profile(level, tier)
    return member_base_power(level) + filled * item_power(level, score)


def team_power(level: int, size: int, tier: str = "media") -> int:
    """Potere squadra: size membri della fascia + bonus ruoli pieno."""
    return size * member_power(level, tier) + TEAM_ROLE_BONUS


def recommended_power_for(level: int, size: int) -> int:
    """NUOVA curva: parità con la squadra MEDIA di pari livello.

    Arrotondata a multipli di 5 per leggibilità dei cataloghi.
    """
    raw = team_power(level, size, "media")
    return int(round(raw / 5.0)) * 5


RAID_SEVERITY = 1.15  # i raid sono più severi del contenuto pari livello


def raid_recommended_power_for(level: int, roster_size: int) -> int:
    """Curva raid: squadra media × severità raid (+15%), round a 25."""
    raw = roster_size * member_power(level, "media") * RAID_SEVERITY + 50
    return int(round(raw / 25.0)) * 25


__all__ = [
    "BASE_STATS_START", "STAT_GAIN_PER_LEVEL", "LEVEL_POWER_FACTOR",
    "TEAM_ROLE_BONUS", "RARITY_SCORE", "TIERS", "RAID_SEVERITY",
    "member_base_power", "item_power", "member_power", "team_power",
    "recommended_power_for", "raid_recommended_power_for",
]
