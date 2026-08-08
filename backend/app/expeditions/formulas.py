"""Pure expedition math — no I/O, no Mongo, fully unit-testable.

These functions are the single source of truth for the team-power /
success-chance / equipment-delta calculations that the routes in
`server.py` consume.
"""
import math
from typing import Iterable

from app.shared.constants import (
    GUARANTEED_SUCCESS_RATING,
    OVERPOWER_BONUS_PER_STEP,
    OVERPOWER_LOOT_MULTIPLIER_CAP,
    OVERPOWER_STEP_PCT,
    SUCCESS_CHANCE_MIN,
    SUCCESS_CHANCE_MAX,
    SUCCESS_CURVE_K,
)


# Phase 13 — primary stats whose values are modifiable by traits.
TRAIT_AFFECTABLE_STATS = ("strength", "agility", "intellect", "endurance", "faith")
TRAIT_XP_STAT = "xp_gain"


def apply_trait_modifiers(stats: dict, traits: list) -> dict:
    """Apply trait modifiers to a stat dict, returning a new dict.

    Stacking policy (Phase 13):
      * flat:    additive sum (Σ modifier_value)
      * percent: additive sum on percent (1 + Σpct/100) applied once
    Clamp: each effective stat ≥ 0, then round() to int.
    Only TRAIT_AFFECTABLE_STATS are touched here; `xp_gain` is resolved
    at expedition completion (see services).
    """
    out = {s: float(stats.get(s, 0)) for s in TRAIT_AFFECTABLE_STATS}
    flat_delta = {s: 0.0 for s in TRAIT_AFFECTABLE_STATS}
    pct_delta = {s: 0.0 for s in TRAIT_AFFECTABLE_STATS}
    for t in traits or []:
        affected = t.get("affected_stat")
        if affected not in TRAIT_AFFECTABLE_STATS:
            continue
        mtype = t.get("modifier_type")
        val = float(t.get("modifier_value", 0) or 0)
        if mtype == "flat":
            flat_delta[affected] += val
        elif mtype == "percent":
            pct_delta[affected] += val
    result = {}
    for s in TRAIT_AFFECTABLE_STATS:
        eff = (out[s] + flat_delta[s]) * (1.0 + pct_delta[s] / 100.0)
        result[s] = max(0, int(round(eff)))
    return result


def sum_xp_percent(traits: list) -> float:
    """Sum of percent modifiers targeting xp_gain (additive stacking)."""
    total = 0.0
    for t in traits or []:
        if t.get("affected_stat") == TRAIT_XP_STAT and t.get("modifier_type") == "percent":
            total += float(t.get("modifier_value", 0) or 0)
    return total


def adventurer_base_power(adv: dict) -> int:
    """Career-adjusted power (no traits, equipment or composition).

    Stored stats stay unmodified; career rarity is applied at resolution time.
    """
    from app.adventurers.career import career_effective_stats
    stats = career_effective_stats(adv)
    return (
        sum(stats.values())
        + int(adv.get("level", 1)) * 2
    )


def adventurer_effective_power(adv: dict) -> int:
    """Phase 13 + ROUND 6C: trait-aware + specialization-aware base power.

    Application order: base stats → trait modifiers → specialization modifiers
    → career-rarity multiplier → sum + level*2. Equipment power is separate in
    `adventurers/services.py`.

    Falls back to raw stats when adv has no traits AND no specialization.
    """
    from app.training.catalog import apply_specialization_modifiers
    from app.adventurers.career import career_effective_stats
    traits = adv.get("traits") or []
    spec = adv.get("specialization")
    if not traits and not spec:
        return adventurer_base_power(adv)
    base = {s: int(adv.get(s, 0)) for s in TRAIT_AFFECTABLE_STATS}
    after_traits = apply_trait_modifiers(base, traits) if traits else base
    after_spec = apply_specialization_modifiers(after_traits, spec)
    after_rarity = career_effective_stats(adv, after_spec)
    return sum(after_rarity.values()) + int(adv.get("level", 1)) * 2


def item_equip_power(item: dict) -> int:
    """Equipment power contribution of a single equipped item."""
    return (
        int(item.get("strength_bonus", 0))
        + int(item.get("agility_bonus", 0))
        + int(item.get("intellect_bonus", 0))
        + int(item.get("endurance_bonus", 0))
        + int(item.get("faith_bonus", 0))
        + int(item.get("power_score", 0))
    )


def compute_team_power(members: Iterable[dict]) -> int:
    """Team power = sum(per-member contribution) + role/composition bonuses.

    Per-member contribution is `total_power_snapshot` when present (Phase 6+),
    otherwise the legacy base formula. Role bonuses: +5 for any Tank, +5 for
    any Healer, +5 for any DPS, +10 if all three roles are present.
    """
    def get(a, key):
        return a.get(key, a.get(key + "_snapshot", 0))

    base = 0
    roles = set()
    for a in members:
        if a.get("total_power_snapshot") is not None:
            base += int(a["total_power_snapshot"])
        else:
            base += (
                int(get(a, "strength"))
                + int(get(a, "agility"))
                + int(get(a, "intellect"))
                + int(get(a, "endurance"))
                + int(get(a, "faith"))
                + int(get(a, "level") or 1) * 2
            )
        role = a.get("class_role") or a.get("role_snapshot")
        if role:
            roles.add(role)
    if "Tank" in roles:
        base += 5
    if "Healer" in roles:
        base += 5
    if "DPS" in roles:
        base += 5
    if {"Tank", "Healer", "DPS"}.issubset(roles):
        base += 10
    return base


def power_rating(team_power: int, recommended_power: int) -> int:
    """FASE 2 — Rating di Potenza: percentuale squadra vs contenuto.

    100 = parità col potere consigliato; può superare 100 senza limiti
    (l'eccedenza alimenta l'Overpower). Vedi
    memory/fase2_design_bilanciamento.md.
    """
    rec = max(1, int(recommended_power or 1))
    return int(round(100.0 * max(0, int(team_power or 0)) / rec))


def compute_success_chance(team_power: int, recommended_power: int) -> int:
    """FASE 2 — curva logistica centrata sulla parità (rating 100 → 50%).

    chance(R) = 100 / (1 + e^(−k·(R−100)/100)), k = SUCCESS_CURVE_K.
    Punti di riferimento: R50→10%, R75→25%, R100→50%, R125→75%,
    R150→90%, R≥200→100% garantito. Clamp [MIN, MAX] = [5, 100].

    Sostituisce la vecchia formula lineare in punti assoluti
    (`50 + PT − PC`, cap 95) che saturava sempre al 95%: questa è
    RELATIVA, quindi scala uguale dal tutorial all'endgame.
    """
    rating = power_rating(team_power, recommended_power)
    if rating >= GUARANTEED_SUCCESS_RATING:
        return SUCCESS_CHANCE_MAX
    raw = 100.0 / (1.0 + math.exp(-SUCCESS_CURVE_K * (rating - 100) / 100.0))
    chance = int(round(raw))
    if chance < SUCCESS_CHANCE_MIN:
        return SUCCESS_CHANCE_MIN
    if chance > SUCCESS_CHANCE_MAX:
        return SUCCESS_CHANCE_MAX
    return chance


def overpower_loot_multiplier(rating: int) -> float:
    """FASE 2 — moltiplicatore drop dall'eccedenza di rating oltre 100.

    1 + 0.5 per ogni 25 punti pieni di Overpower, cap ×3.0:
    R125→×1.5, R150→×2.0, R175→×2.5, R≥200→×3.0.
    Si applica a item lootati e quantità materiali, NON a oro/XP.
    """
    overpower = max(0, int(rating or 0) - 100)
    steps = overpower // OVERPOWER_STEP_PCT
    return float(min(
        OVERPOWER_LOOT_MULTIPLIER_CAP,
        1.0 + OVERPOWER_BONUS_PER_STEP * steps,
    ))


def build_equipment_delta(
    members_for_power: list[dict],
    dungeon: dict,
    final_team_power: int,
    success_chance_with_eq: int,
) -> dict:
    """Return the 5 Phase-7 delta fields + narrative line.

    The function expects each member dict to carry
    `total_power_snapshot` and `equipment_power_snapshot` (computed by the
    expedition starter).
    """
    equipment_base_power_bonus = sum(
        int(m.get("equipment_power_snapshot", 0)) for m in members_for_power
    )
    item_effect_power_bonus = sum(
        int(m.get("item_effect_power_bonus", 0)) for m in members_for_power
    )
    class_item_resonance_bonus = sum(
        int(m.get("class_item_resonance_bonus", 0))
        for m in members_for_power
    )
    equipment_power_bonus = (
        equipment_base_power_bonus
        + item_effect_power_bonus
        + class_item_resonance_bonus
    )
    members_base_only = [
        {
            **m,
            "total_power_snapshot": int(m["total_power_snapshot"])
            - int(m.get("equipment_power_snapshot", 0))
            - int(m.get("item_effect_power_bonus", 0))
            - int(m.get("class_item_resonance_bonus", 0)),
        }
        for m in members_for_power
    ]
    base_team_power = compute_team_power(members_base_only)
    success_chance_without_eq = compute_success_chance(
        base_team_power, dungeon["recommended_power"]
    )

    if equipment_power_bonus == 0:
        narrative = "Nessun equipaggiamento è stato consumato in questa spedizione."
    elif item_effect_power_bonus or class_item_resonance_bonus:
        breakdown = (
            f"L'equipaggiamento base ha aggiunto +{equipment_base_power_bonus} "
            f"e gli effetti degli item di lore +{item_effect_power_bonus} "
            f"e la risonanza dei sentieri +{class_item_resonance_bonus} "
            "al potere della squadra. "
        )
        if success_chance_without_eq == success_chance_with_eq:
            narrative = (
                breakdown
                + "La probabilità di successo era già al massimo "
                f"({success_chance_with_eq}%)."
            )
        else:
            narrative = (
                breakdown
                + "La probabilità di successo è aumentata dal "
                f"{success_chance_without_eq}% al {success_chance_with_eq}%."
            )
    elif success_chance_without_eq == success_chance_with_eq:
        narrative = (
            f"L'equipaggiamento ha aggiunto +{equipment_power_bonus} al potere della squadra. "
            f"La probabilità di successo era già al massimo ({success_chance_with_eq}%)."
        )
    else:
        narrative = (
            f"L'equipaggiamento ha aggiunto +{equipment_power_bonus} al potere della squadra, "
            f"aumentando la probabilità di successo dal {success_chance_without_eq}% "
            f"al {success_chance_with_eq}%."
        )
    return {
        "base_team_power": base_team_power,
        "equipment_base_power_bonus": equipment_base_power_bonus,
        "item_effect_power_bonus": item_effect_power_bonus,
        "class_item_resonance_bonus": class_item_resonance_bonus,
        "equipment_power_bonus": equipment_power_bonus,
        "final_team_power": final_team_power,
        "success_chance_without_equipment": success_chance_without_eq,
        "success_chance_with_equipment": success_chance_with_eq,
        "equipment_delta_text": narrative,
    }
