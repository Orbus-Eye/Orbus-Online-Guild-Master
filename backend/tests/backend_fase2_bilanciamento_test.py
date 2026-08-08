"""FASE 2 (2026-08-08) — Test puri del nuovo bilanciamento.

Copre: curva logistica di successo, Rating di Potenza, moltiplicatore
Overpower, gate a potere del gruppo, catch-up XP top-5.
Nessun Mongo richiesto (eseguire con --noconftest).
Design: memory/fase2_design_bilanciamento.md
"""
import pytest
from fastapi import HTTPException

from app.expeditions.catchup import catchup_multiplier
from app.expeditions.formulas import (
    compute_success_chance,
    overpower_loot_multiplier,
    power_rating,
)
from app.expeditions.power_gate import (
    enforce_min_team_power,
    required_team_power_for,
)


# ── Rating di Potenza ────────────────────────────────────────────────────

def test_rating_parita_e_overpower():
    assert power_rating(100, 100) == 100
    assert power_rating(150, 100) == 150
    assert power_rating(50, 100) == 50
    assert power_rating(300, 100) == 300  # nessun cap sul rating


def test_rating_recommended_zero_non_esplode():
    assert power_rating(50, 0) > 0


# ── Curva di successo ────────────────────────────────────────────────────

def test_curva_punti_di_riferimento():
    """Punti FASE 8A (k=5.5): la curva punisce di più l'underpower.
    Vedi memory/fase8_dungeon_difficulty_rebalance.md."""
    assert compute_success_chance(100, 100) == 50   # parità
    assert compute_success_chance(125, 100) == 80
    assert compute_success_chance(150, 100) == 94
    assert compute_success_chance(75, 100) == 20
    assert compute_success_chance(50, 100) == 6


def test_niente_piu_cap_95():
    """Il bug storico: tutto saturava a 95. Ora il 100% esiste davvero."""
    assert compute_success_chance(200, 100) == 100  # rating 200 → garantito
    assert compute_success_chance(500, 100) == 100
    # E la zona 175-199 supera comunque il vecchio cap:
    assert compute_success_chance(175, 100) > 95


def test_floor_al_5_percento():
    assert compute_success_chance(1, 1000) == 5
    assert compute_success_chance(0, 100) == 5


def test_curva_relativa_non_assoluta():
    """Stesso delta assoluto, scala diversa → chance diversa (il difetto
    della vecchia formula lineare è rimosso)."""
    small = compute_success_chance(60, 50)     # +10 su base 50 → rating 120
    large = compute_success_chance(1010, 1000)  # +10 su base 1000 → rating 101
    assert small > large


def test_curva_monotona():
    prev = 0
    for tp in range(0, 260, 5):
        c = compute_success_chance(tp, 100)
        assert c >= prev
        prev = c


# ── Overpower ────────────────────────────────────────────────────────────

def test_overpower_gradini():
    assert overpower_loot_multiplier(100) == 1.0
    assert overpower_loot_multiplier(124) == 1.0
    assert overpower_loot_multiplier(125) == 1.5   # esempio del design
    assert overpower_loot_multiplier(149) == 1.5
    assert overpower_loot_multiplier(150) == 2.0
    assert overpower_loot_multiplier(175) == 2.5
    assert overpower_loot_multiplier(200) == 3.0


def test_overpower_cap_economico():
    assert overpower_loot_multiplier(400) == 3.0
    assert overpower_loot_multiplier(9999) == 3.0


def test_overpower_sotto_parita_neutro():
    assert overpower_loot_multiplier(80) == 1.0
    assert overpower_loot_multiplier(0) == 1.0


# ── Gate a potere ────────────────────────────────────────────────────────

def test_soglia_gate_70_percento():
    """FASE 8A — gate alzato dal 60% al 70% del potere consigliato."""
    assert required_team_power_for({"recommended_power": 100}) == 70
    assert required_team_power_for({"recommended_power": 333}) == 234
    assert required_team_power_for({"recommended_power": 15}) == 11


def test_gate_blocca_sotto_soglia():
    dungeon = {"recommended_power": 100, "slug": "test-dungeon"}
    with pytest.raises(HTTPException) as exc:
        enforce_min_team_power(69, dungeon, source="expedition.dispatch")
    detail = exc.value.detail
    assert exc.value.status_code == 423
    assert detail["code"] == "team.power_too_low"
    assert detail["required_team_power"] == 70
    assert "user_message" in detail


def test_gate_passa_alla_soglia_esatta():
    dungeon = {"recommended_power": 100, "slug": "test-dungeon"}
    enforce_min_team_power(70, dungeon, source="expedition.dispatch")
    enforce_min_team_power(150, dungeon, source="expedition.preview")


# ── Catch-up XP top-5 ────────────────────────────────────────────────────

def test_catchup_attivo_sotto_soglia():
    top = [15, 12, 11, 10, 10]
    assert catchup_multiplier(top, 5) == 1.25
    assert catchup_multiplier(top, 9) == 1.25


def test_catchup_non_per_chi_e_gia_arrivato():
    top = [15, 12, 11, 10, 10]
    assert catchup_multiplier(top, 10) == 1.0
    assert catchup_multiplier(top, 40) == 1.0


def test_catchup_spento_se_top5_incompleti():
    assert catchup_multiplier([12, 11, 10, 9, 8], 5) == 1.0   # il 5° è Lv8
    assert catchup_multiplier([15, 15, 15], 5) == 1.0         # gilda piccola
    assert catchup_multiplier([], 5) == 1.0
