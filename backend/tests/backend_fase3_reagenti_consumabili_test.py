"""FASE 3 (2026-08-08) — Test puri: reagenti per dungeon/raid + consumabili.

Nessun Mongo richiesto (eseguire con --noconftest).
Design: memory/fase3_design_reagenti_crafting.md
"""
import random

from app.expeditions.reagent_tables import (
    DUNGEON_PRIMARY_REAGENT,
    RAID_PRIMARY_REAGENT,
    primary_reagent_for_dungeon,
    raid_reagent_grant,
    roll_primary_reagent,
)
from app.adventurers.consumables import (
    consumable_power_bonus,
    consumable_xp_multiplier,
)
from app.shared.content_curve import DUNGEON_CURVE, RAID_CURVE


# ── Copertura e univocità della mappa reagenti ───────────────────────────

def test_ogni_dungeon_della_curve_ha_un_reagente():
    """Regola d'oro: UN reagente principale per ogni dungeon attivo."""
    missing = [slug for slug in DUNGEON_CURVE if slug not in DUNGEON_PRIMARY_REAGENT]
    assert missing == [], f"dungeon senza reagente principale: {missing}"


def test_ogni_raid_ha_un_reagente():
    missing = [slug for slug in RAID_CURVE if slug not in RAID_PRIMARY_REAGENT]
    assert missing == [], f"raid senza reagente: {missing}"


def test_reagenti_raid_esclusivi():
    """I reagenti dei raid NON devono cadere in nessun dungeon."""
    raid_mats = {entry[0] for entry in RAID_PRIMARY_REAGENT.values()}
    dungeon_mats = {entry[0] for entry in DUNGEON_PRIMARY_REAGENT.values()}
    overlap = raid_mats & dungeon_mats
    assert overlap == set(), f"reagenti raid presenti anche nei dungeon: {overlap}"


def test_dragon_essence_solo_dragon_vault():
    assert RAID_PRIMARY_REAGENT["dragon-vault"][0] == "dragon_essence"


# ── Roll del reagente ────────────────────────────────────────────────────

def test_roll_dungeon_mappato_ritorna_solo_il_suo_reagente():
    rng = random.Random(42)
    seen = set()
    for _ in range(200):
        drops = roll_primary_reagent("lich-sanctum", True, rng=rng)
        for d in drops:
            seen.add(d["slug"])
            assert d["qty"] >= 1
    assert seen == {"ossa_antiche"}


def test_roll_dungeon_non_mappato_vuoto():
    assert roll_primary_reagent("slug-inesistente", True) == []
    assert primary_reagent_for_dungeon("slug-inesistente") is None


def test_roll_fallimento_dimezza_il_rate():
    rng_ok = random.Random(7)
    rng_ko = random.Random(7)
    hits_ok = sum(
        1 for _ in range(2000)
        if roll_primary_reagent("training-yard", True, rng=rng_ok)
    )
    hits_ko = sum(
        1 for _ in range(2000)
        if roll_primary_reagent("training-yard", False, rng=rng_ko)
    )
    assert hits_ko < hits_ok


def test_raid_garantito_a_vittoria():
    rng = random.Random(1)
    for _ in range(50):
        drops = raid_reagent_grant("moonfall-vigil", "victory", rng=rng)
        assert len(drops) == 1
        assert drops[0]["slug"] == "polvere_di_luna"
        assert 2 <= drops[0]["qty"] <= 3


def test_raid_sconfitta_niente_reagente():
    assert raid_reagent_grant("moonfall-vigil", "defeat") == []
    assert raid_reagent_grant("moonfall-vigil", "wipe") == []


# ── Consumabili: letture pure ────────────────────────────────────────────

def _adv(active):
    return {"active_consumable": active}


def test_power_boost_applicato():
    adv = _adv({"type": "power_boost", "magnitude": 8, "charges_left": 3})
    assert consumable_power_bonus(adv) == 8
    assert consumable_xp_multiplier(adv) == 1.0


def test_xp_boost_applicato():
    """La Pietra della Conoscenza: +50% XP."""
    adv = _adv({"type": "xp_boost", "magnitude": 0.5, "charges_left": 5})
    assert consumable_xp_multiplier(adv) == 1.5
    assert consumable_power_bonus(adv) == 0


def test_cariche_esaurite_nessun_effetto():
    adv = _adv({"type": "xp_boost", "magnitude": 0.5, "charges_left": 0})
    assert consumable_xp_multiplier(adv) == 1.0
    adv2 = _adv({"type": "power_boost", "magnitude": 8, "charges_left": 0})
    assert consumable_power_bonus(adv2) == 0


def test_nessun_consumabile_neutro():
    assert consumable_power_bonus({}) == 0
    assert consumable_xp_multiplier({}) == 1.0
    assert consumable_power_bonus({"active_consumable": None}) == 0
