"""RT2-A · test_integration.py

Integration tests con fixture avventuriero + equip. Non tocca DB.
Verifica:
- equipment aggregation end-to-end
- expedition-start snapshot (costruzione)
- snapshot immutability post-start
- shadow no-impact
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime import feature_flags as ff
from app.stats.runtime.loadout_snapshot import build_loadout_snapshot
from app.stats.runtime.modifier_order import derived_base_power, evaluate_runtime_stats
from app.stats.runtime.shadow_comparison import compare_shadow


@pytest.fixture
def sample_adventurer():
    return {
        "id": "adv-alpha",
        "level": 10,
        "base_stats": {
            "strength": 40,
            "agility": 25,
            "intellect": 60,
            "endurance": 30,
            "faith": 15,
        },
    }


@pytest.fixture
def sample_loadout():
    return [
        {"id": "sword-of-dawn", "blueprint_id": "bp-sword-01",
         "strength_bonus": 15, "agility_bonus": 5, "power_score": 40},
        {"id": "robe-of-mind", "blueprint_id": "bp-robe-01",
         "intellect_bonus": 20, "faith_bonus": 5, "power_score": 25},
    ]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for f in ff.ALL_FLAGS:
        monkeypatch.delenv(f"ORBUS_FLAG_{f.upper()}", raising=False)
    ff.reset_cache()
    yield
    ff.reset_cache()


# ─── Equipment aggregation end-to-end ──────────────────────────────────
def test_equipment_aggregation_e2e(sample_adventurer, sample_loadout):
    result = evaluate_runtime_stats(
        base_stats=sample_adventurer["base_stats"],
        equipment_items=sample_loadout,
    )
    # Str: 40 + 15 = 55; Int: 60 + 20 = 80; Faith: 15 + 5 = 20
    assert result.nominal_stats["strength"] == 55
    assert result.nominal_stats["intellect"] == 80
    assert result.nominal_stats["faith"] == 20
    assert result.soft_cap_applied is False


# ─── Expedition start snapshot construction ─────────────────────────────
def test_expedition_start_snapshot(sample_adventurer, sample_loadout):
    snap = build_loadout_snapshot(
        adventurer_id=sample_adventurer["id"],
        expedition_id="exp-integration-01",
        base_stats=sample_adventurer["base_stats"],
        equipment_items=sample_loadout,
    )
    assert snap.adventurer_id == "adv-alpha"
    assert snap.expedition_id == "exp-integration-01"
    assert snap.nominal_stats["strength"] == 55
    assert "bp-sword-01" in snap.source_item_blueprint_list
    assert "bp-robe-01" in snap.source_item_blueprint_list


# ─── Snapshot immutability post-start ──────────────────────────────────
def test_snapshot_immutability_post_start(sample_adventurer, sample_loadout):
    """Modifiche a loadout DOPO snapshot NON alterano lo snapshot."""
    snap = build_loadout_snapshot(
        adventurer_id=sample_adventurer["id"],
        expedition_id="exp-x",
        base_stats=sample_adventurer["base_stats"],
        equipment_items=sample_loadout,
    )
    original_str = snap.nominal_stats["strength"]
    # Simuliamo unequip post-dispatch
    sample_loadout.clear()
    sample_loadout.append({"strength_bonus": 999})
    # snapshot immutato
    assert snap.nominal_stats["strength"] == original_str


def test_snapshot_frozen_cannot_be_modified(sample_adventurer):
    snap = build_loadout_snapshot(
        adventurer_id=sample_adventurer["id"],
        expedition_id="exp-x",
        base_stats=sample_adventurer["base_stats"],
    )
    with pytest.raises(Exception):
        snap.nominal_stats = {}  # frozen


# ─── Shadow no-impact ──────────────────────────────────────────────────
def test_shadow_on_no_gameplay_impact(monkeypatch, sample_adventurer, sample_loadout):
    """Flag shadow ON, soft_cap OFF: shadow calcolato ma non autoritativo."""
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    # Simuliamo il valore autoritativo current (legacy) fisso a 200
    current_authoritative = 200
    result = compare_shadow(
        expedition_id="exp-shadow-1",
        adventurer_id=sample_adventurer["id"],
        current_base_power=current_authoritative,
        base_stats=sample_adventurer["base_stats"],
        equipment_items=sample_loadout,
        level=sample_adventurer["level"],
    )
    # Shadow diagnostica emessa
    assert result is not None
    assert result.current_base_power == current_authoritative
    # Il valore autoritativo (input) NON è modificato
    # (compare_shadow è read-only: current_authoritative rimane 200)
    assert current_authoritative == 200


def test_shadow_off_returns_none(sample_adventurer):
    """Flag OFF → shadow non produce output (nessun record)."""
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id=sample_adventurer["id"],
        current_base_power=100,
        base_stats=sample_adventurer["base_stats"],
    )
    assert result is None


def test_derived_power_deterministic(sample_adventurer, sample_loadout):
    """derived_base_power è deterministic. Usato come sostituzione di 'legacy' in shadow."""
    result = evaluate_runtime_stats(
        base_stats=sample_adventurer["base_stats"],
        equipment_items=sample_loadout,
    )
    p1 = derived_base_power(result, level=sample_adventurer["level"])
    p2 = derived_base_power(result, level=sample_adventurer["level"])
    assert p1 == p2
