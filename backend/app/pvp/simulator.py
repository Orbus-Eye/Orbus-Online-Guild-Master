"""ROUND 12.A — Server-authoritative combat simulation.

Crypto-grade RNG (R11.4d). Produces:
  * `outcome` ∈ {"attacker_win", "defender_win", "draw"}.
  * `final_attack_score`, `final_defense_score`.
  * `report_it` — player-facing 3-5 round narrative in IT.
  * `combat_version="12.1"`, `rng_version="systemrandom_v1"`.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Any

_rng = secrets.SystemRandom()

COMBAT_VERSION = "12.1"
RNG_VERSION = "systemrandom_v1"

# Role bonus (composition synergy).
ROLE_BONUS = {"Tank": 0.05, "Healer": 0.05, "DPS": 0.03}
ROLE_TRIO_BONUS = 0.08


def _team_base_score(snapshot: dict) -> tuple[float, dict]:
    """Compute the pre-randomness team score from a snapshot.

    `snapshot["adventurers"]` — list of {id, name, class, role, level,
    stats: {atk,def,pwr,...}, equip_bonus (int), traits (list)}.

    Returns (score, breakdown).
    """
    advs = snapshot.get("adventurers", []) or []
    total = 0.0
    role_set: set[str] = set()
    for a in advs:
        lvl = int(a.get("level", 1))
        stats = a.get("stats") or {}
        stat_sum = sum(int(v) for v in stats.values() if isinstance(v, (int, float)))
        equip_bonus = int(a.get("equip_bonus", 0))
        trait_bonus = 2 * len(a.get("traits") or [])  # +2 per trait, capped by count
        per = lvl * 10 + stat_sum + equip_bonus + trait_bonus
        total += per
        if a.get("role"):
            role_set.add(a["role"])
    # Composition bonus
    role_mult = 1.0
    for role, bonus in ROLE_BONUS.items():
        if role in role_set:
            role_mult += bonus
    if {"Tank", "Healer", "DPS"}.issubset(role_set):
        role_mult += ROLE_TRIO_BONUS
    composed = total * role_mult
    return composed, {
        "raw_total": int(total),
        "roles_present": sorted(role_set),
        "role_multiplier": round(role_mult, 4),
        "composed_score": int(composed),
    }


def _swing() -> float:
    """Returns a random multiplier in [0.92, 1.08]."""
    return 0.92 + (_rng.random() * 0.16)


def _build_report_it(
    attacker_snap: dict, defender_snap: dict,
    att_breakdown: dict, def_breakdown: dict,
    att_swing: float, def_swing: float,
    outcome: str, final_att: float, final_def: float,
) -> list[str]:
    rounds: list[str] = []
    att_name = attacker_snap.get("guild_name", "Attaccante")
    def_name = defender_snap.get("guild_name", "Difensore")

    # Round 1 — opening
    rounds.append(
        f"⚔️ Apertura — {att_name} schiera {', '.join(att_breakdown['roles_present']) or 'una formazione mista'}, "
        f"mentre {def_name} risponde con {', '.join(def_breakdown['roles_present']) or 'una formazione mista'}."
    )

    # Round 2 — first clash
    if "Tank" in att_breakdown["roles_present"]:
        rounds.append(f"🛡️ Il Tank di {att_name} apre il varco assorbendo il primo assalto.")
    elif "DPS" in att_breakdown["roles_present"]:
        rounds.append(f"🗡️ I DPS di {att_name} aprono con un'offensiva fulminea.")
    else:
        rounds.append(f"⚡ {att_name} carica disordinatamente: senza Tank, prende danno extra.")

    # Round 3 — defensive response
    if "Healer" in def_breakdown["roles_present"]:
        rounds.append(f"💚 L'Healer di {def_name} stabilizza il fronte difensivo.")
    elif "Tank" in def_breakdown["roles_present"]:
        rounds.append(f"🛡️ Il Tank di {def_name} mantiene la posizione.")
    else:
        rounds.append(f"💥 {def_name} resiste senza supporto: una scelta rischiosa.")

    # Round 4 — composition vibe
    att_mul = att_breakdown["role_multiplier"]
    def_mul = def_breakdown["role_multiplier"]
    if att_mul > def_mul + 0.05:
        rounds.append(f"✨ La sinergia di {att_name} domina lo scambio centrale.")
    elif def_mul > att_mul + 0.05:
        rounds.append(f"🛡️ La compattezza di {def_name} regge l'urto.")
    else:
        rounds.append("⚖️ Le due formazioni si bilanciano in equilibrio precario.")

    # Round 5 — closing
    if outcome == "attacker_win":
        rounds.append(f"🏆 Esito — {att_name} chiude lo scontro con un margine decisivo.")
    elif outcome == "defender_win":
        rounds.append(f"🛡️ Esito — {def_name} respinge l'assalto e mantiene il controllo.")
    else:
        rounds.append("🤝 Esito — Lo scontro si chiude in parità sostanziale.")

    return rounds


def simulate(attacker_snapshot: dict, defender_snapshot: dict, *, match_id: str, season_id: str) -> dict:
    """Resolve the match. Pure function except for `_rng` (crypto-grade)."""
    att_score, att_breakdown = _team_base_score(attacker_snapshot)
    def_score, def_breakdown = _team_base_score(defender_snapshot)

    att_swing = _swing()
    def_swing = _swing()
    final_att = att_score * att_swing
    final_def = def_score * def_swing

    if final_att > final_def * 1.05:
        outcome = "attacker_win"
    elif final_att < final_def * 0.95:
        outcome = "defender_win"
    else:
        outcome = "draw"

    report = _build_report_it(
        attacker_snapshot, defender_snapshot,
        att_breakdown, def_breakdown, att_swing, def_swing,
        outcome, final_att, final_def,
    )
    seed_hash = hashlib.sha256(f"{match_id}:{season_id}".encode()).hexdigest()[:16]

    return {
        "outcome": outcome,
        "final_attack_score": int(round(final_att)),
        "final_defense_score": int(round(final_def)),
        "attacker_breakdown": att_breakdown,
        "defender_breakdown": def_breakdown,
        "report_it": report,
        "combat_version": COMBAT_VERSION,
        "rng_version": RNG_VERSION,
        "seed_hash": seed_hash,
    }


__all__ = ["simulate", "COMBAT_VERSION", "RNG_VERSION"]
