"""Test Fase 0 per il motore di risoluzione spedizioni (funzioni pure)."""
from __future__ import annotations

from app.expeditions.resolver import (
    AdventurerSnapshot,
    DungeonSpec,
    calculate_success_chance,
    calculate_team_power,
    resolve_expedition,
)


# ─── Fixtures locali (helper factories) ───────────────────────────────────
def _adv(role: str, level: int = 1, stats: int = 10, name: str | None = None) -> AdventurerSnapshot:
    return AdventurerSnapshot(
        id=f"adv-{role.lower()}-{level}",
        name=name or f"{role} {level}",
        role=role,
        level=level,
        strength=stats,
        agility=stats,
        intellect=stats,
        vitality=stats,
    )


_DUNGEON = DungeonSpec(
    slug="goblin-warrens",
    name="Tane dei Goblin",
    recommended_power=100,
    base_gold_reward=80,
    base_xp_reward=50,
)


# ─── 1. Team bilanciato ──────────────────────────────────────────────────
def test_balanced_team_includes_full_composition_bonus():
    team = [_adv("Tank"), _adv("Healer"), _adv("DPS")]
    # Ogni avventuriero: stat_sum=40, level*2=2, base per membro = 42
    # base totale = 42*3 = 126, comp bonus = 5+5+5+10 = 25
    power = calculate_team_power(team)
    assert power == 126 + 25


# ─── 2. Team solo DPS ────────────────────────────────────────────────────
def test_only_dps_team_gets_only_dps_bonus():
    team = [_adv("DPS"), _adv("DPS")]
    # base = (40+2)*2 = 84, bonus = 5 (solo DPS)
    power = calculate_team_power(team)
    assert power == 84 + 5


# ─── 3. Clamp minimo ─────────────────────────────────────────────────────
def test_success_chance_clamped_to_min_10():
    # team debolissimo contro dungeon fortissimo
    chance = calculate_success_chance(team_power=0, recommended_power=1000)
    assert chance == 10


# ─── 4. Clamp massimo ────────────────────────────────────────────────────
def test_success_chance_clamped_to_max_95():
    # team fortissimo contro dungeon debolissimo
    chance = calculate_success_chance(team_power=5000, recommended_power=10)
    assert chance == 95


# ─── 5. Team forte -> 95 ─────────────────────────────────────────────────
def test_strong_team_vs_weak_dungeon_hits_max():
    team = [_adv("Tank", level=50, stats=50), _adv("Healer", level=50, stats=50), _adv("DPS", level=50, stats=50)]
    power = calculate_team_power(team)
    chance = calculate_success_chance(power, recommended_power=50)
    assert chance == 95


# ─── 6. Team debole -> 10 ────────────────────────────────────────────────
def test_weak_team_vs_strong_dungeon_hits_min():
    team = [_adv("DPS", level=1, stats=1)]
    power = calculate_team_power(team)
    chance = calculate_success_chance(power, recommended_power=1000)
    assert chance == 10


# ─── 7. Determinismo con seed ────────────────────────────────────────────
def test_resolve_expedition_is_deterministic_with_seed():
    team = [_adv("Tank"), _adv("Healer"), _adv("DPS")]
    r1 = resolve_expedition(team, _DUNGEON, rng_seed=42)
    r2 = resolve_expedition(team, _DUNGEON, rng_seed=42)
    assert r1.outcome == r2.outcome
    assert r1.roll == r2.roll
    assert r1.gold_reward == r2.gold_reward
    assert r1.xp_per_member == r2.xp_per_member
    assert r1.loot_dropped == r2.loot_dropped
    assert r1.report_text == r2.report_text


def test_resolve_expedition_different_seeds_can_differ():
    team = [_adv("Tank"), _adv("Healer"), _adv("DPS")]
    # con success_chance 95 lo sfido a produrre almeno un roll diverso in 50 seed
    rolls = {resolve_expedition(team, _DUNGEON, rng_seed=s).roll for s in range(50)}
    assert len(rolls) > 1


# ─── 8. Report in italiano, contiene lessico esito ───────────────────────
def test_success_report_mentions_success_language():
    # Forziamo un successo con team fortissimo
    team = [_adv("Tank", level=50, stats=50), _adv("Healer", level=50, stats=50), _adv("DPS", level=50, stats=50)]
    r = resolve_expedition(team, _DUNGEON, rng_seed=1)
    assert r.outcome == "success"
    assert "riuscita" in r.report_text.lower()


def test_failure_report_mentions_failure_language():
    # Forziamo un fallimento con team debolissimo vs dungeon fortissimo
    hard_dungeon = DungeonSpec(
        slug="deep-abyss",
        name="Abisso Profondo",
        recommended_power=100000,
        base_gold_reward=100,
        base_xp_reward=100,
    )
    team = [_adv("DPS", level=1, stats=1)]
    r = resolve_expedition(team, hard_dungeon, rng_seed=1)
    assert r.outcome == "failure"
    text = r.report_text.lower()
    assert ("fallita" in text) or ("ritirata" in text)


# ─── 9. Ricompensa fallimento è ridotta ─────────────────────────────────
def test_failure_rewards_are_reduced():
    hard_dungeon = DungeonSpec(
        slug="deep-abyss",
        name="Abisso Profondo",
        recommended_power=100000,
        base_gold_reward=200,
        base_xp_reward=150,
    )
    team = [_adv("DPS", level=1, stats=1)]
    r = resolve_expedition(team, hard_dungeon, rng_seed=7)
    assert r.outcome == "failure"
    assert r.gold_reward == round(200 * 0.25)
    assert r.xp_per_member == round(150 * 0.4)
    assert r.loot_dropped is False
