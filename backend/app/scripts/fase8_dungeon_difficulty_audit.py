"""FASE 8A (2026-08-08) — Audit + simulazione difficoltà dungeon.

Stampa le tabelle usate per il rebalance (e per il documento
memory/fase8_dungeon_difficulty_rebalance.md):

  1. potere squadra per livello × fascia di equipaggiamento;
  2. nuova curva recommended_power vs vecchia (per ogni dungeon);
  3. matrice livello-squadra × livello-dungeon → rating, gate, chance
     (con la NUOVA curva logistica);
  4. verifica dell'acceptance: Lv15 media vs dungeon Lv40 → sotto gate.

Esecuzione (pure, nessun DB):
    python -m app.scripts.fase8_dungeon_difficulty_audit
"""
from __future__ import annotations

from app.shared.power_model import (
    TIERS,
    member_power,
    raid_recommended_power_for,
    recommended_power_for,
    team_power,
)


# Curva PRE-rebalance (Fase 2.3) per il confronto before/after.
OLD_CURVE: dict[str, tuple[int, int, int]] = {
    # slug: (required_level, old_recommended_power, team_size)
    "training-yard": (1, 15, 3),
    "sewer-nest": (1, 35, 3),
    "goblin-warrens": (5, 117, 5),
    "bandit-hideout": (5, 75, 3),
    "druid-grove": (10, 267, 5),
    "shadow-crypts": (10, 283, 5),
    "cursed-mines": (15, 333, 5),
    "sunken-library": (15, 215, 3),
    "lich-sanctum": (20, 408, 5),
    "dragons-hoard": (25, 642, 7),
    "storm-spire": (25, 483, 5),
    "wolf-den-5p": (10, 260, 5),
    "frost-cave-5p": (15, 310, 5),
    "salt-marsh-5p": (20, 360, 5),
    "iron-foundry-5p": (25, 410, 5),
    "silent-monastery-5p": (30, 460, 5),
    "pirate-fleet-5p": (35, 510, 5),
    "obsidian-arena-5p": (40, 560, 5),
    "clockwork-vault-5p": (45, 610, 5),
    "voidspire-5p": (50, 660, 5),
    "infernal-pit-5p": (60, 760, 5),
    "celestial-citadel-5p": (65, 810, 5),
    "world-tree-roots-5p": (70, 1600, 7),
}

OLD_RAIDS = {
    "moonfall-vigil": (40, 1500, 10),
    "broken-bastion-siege": (60, 2400, 15),
    "necropolis-bells": (70, 3500, 20),
    "dragon-vault": (80, 8000, 40),
}

LEVELS = (10, 15, 20, 30, 40, 50, 60, 70, 80)


def _chance(team: int, rec: int) -> int:
    from app.expeditions.formulas import compute_success_chance
    return compute_success_chance(team, rec)


def _gate(rec: int) -> int:
    from app.expeditions.power_gate import required_team_power_for
    return required_team_power_for({"recommended_power": rec})


def main() -> None:
    print("=" * 72)
    print("TABELLA 1 — potere squadra (5 membri) per livello × fascia equip")
    print("=" * 72)
    header = "Lv   " + "".join(f"{t[:14]:>16}" for t in TIERS)
    print(header)
    for lvl in LEVELS:
        row = f"{lvl:<5}" + "".join(
            f"{team_power(lvl, 5, t):>16}" for t in TIERS
        )
        print(row)

    print()
    print("=" * 72)
    print("TABELLA 2 — curva recommended_power: vecchia → nuova (per slug)")
    print("=" * 72)
    print(f"{'slug':<24}{'Lv':>4}{'size':>5}{'old':>7}{'new':>7}{'×':>6}"
          f"{'gate old':>9}{'gate new':>9}")
    for slug, (lvl, old, size) in OLD_CURVE.items():
        new = recommended_power_for(lvl, size)
        ratio = new / old if old else 0
        print(f"{slug:<24}{lvl:>4}{size:>5}{old:>7}{new:>7}{ratio:>6.2f}"
              f"{int(0.60 * old):>9}{_gate(new):>9}")

    print()
    print("=" * 72)
    print("TABELLA 3 — raid: curva vecchia → nuova")
    print("=" * 72)
    for slug, (lvl, old, size) in OLD_RAIDS.items():
        new = raid_recommended_power_for(lvl, size)
        print(f"{slug:<24}Lv{lvl:<4}size {size:<4}{old:>7} → {new:>7}"
              f"  (×{new / old:.2f})")

    print()
    print("=" * 72)
    print("TABELLA 4 — squadra Lv × dungeon Lv → rating% / esito (curva NUOVA)")
    print("  esiti: BLOCK = sotto il PWR gate; n% = chance di successo")
    print("=" * 72)
    for tier in TIERS:
        print(f"\n-- fascia: {tier} --")
        print("SqLv \\ DgLv" + "".join(f"{d:>10}" for d in LEVELS))
        for sq in LEVELS:
            cells = []
            for dg in LEVELS:
                rec = recommended_power_for(dg, 5)
                team = team_power(sq, 5, tier)
                rating = round(100 * team / rec)
                if team < _gate(rec):
                    cells.append(f"{rating}%BLOCK")
                else:
                    cells.append(f"{rating}%→{_chance(team, rec)}%")
            print(f"{sq:<11}" + "".join(f"{c:>10}" for c in cells))

    print()
    print("=" * 72)
    print("ACCETTAZIONE — squadra Lv15 vs dungeon (curva NUOVA)")
    print("=" * 72)
    for tier in TIERS:
        team = team_power(15, 5, tier)
        for dg in (15, 20, 25, 30, 40):
            rec = recommended_power_for(dg, 5)
            gate = _gate(rec)
            status = ("BLOCK" if team < gate
                      else f"{_chance(team, rec)}%")
            print(f"Lv15 {tier:<18} vs Dg Lv{dg:<3} "
                  f"(rec {rec}, gate {gate}, team {team}) → {status}")


if __name__ == "__main__":
    main()
