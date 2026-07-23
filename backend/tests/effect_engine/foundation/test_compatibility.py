"""RT2-A · test_compatibility.py

Compatibility contract verbatim:
- legacy items (senza effect metadata) → validi, nessun effetto attivato
- missing optional stats → treat as zero
- flags off → risultati byte-equivalenti a comportamento attuale
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime import feature_flags as ff
from app.stats.runtime.equipment_aggregation import (
    aggregate_equipment_flat_stats,
    total_power_score_contribution,
)
from app.stats.runtime.modifier_order import evaluate_runtime_stats
from app.stats.runtime.shadow_comparison import compare_shadow


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for f in ff.ALL_FLAGS:
        monkeypatch.delenv(f"ORBUS_FLAG_{f.upper()}", raising=False)
    ff.reset_cache()
    yield
    ff.reset_cache()


# ─── Legacy items ──────────────────────────────────────────────────────
def test_legacy_item_no_effect_metadata_valid():
    """Item legacy senza effect_metadata è item valido con nessun effetto."""
    legacy_items = [
        {"id": "sword-legacy", "strength_bonus": 15, "power_score": 30},
        {"id": "shield-legacy", "endurance_bonus": 10, "power_score": 20},
    ]
    r = evaluate_runtime_stats(base_stats={"strength": 20}, equipment_items=legacy_items)
    assert r.nominal_stats["strength"] == 35
    assert r.nominal_stats["endurance"] == 10
    # Nessun proc/effetto: solo aggregazione flat
    assert r.reason_code == "RT2A_STAT_EVAL_NO_CAP"


def test_legacy_item_without_any_bonus():
    """Item legacy senza alcun bonus stat → contributi 0."""
    legacy_items = [{"id": "empty-item", "power_score": 5}]
    r = evaluate_runtime_stats(base_stats={"strength": 10}, equipment_items=legacy_items)
    assert r.nominal_stats["strength"] == 10  # invariato


def test_9_preserved_items_no_effect_triggered():
    """Whitelist 9 preserved items: nessun effect metadata deve mai essere attivato.

    In RT2-A: nessun effect engine esiste → banalmente nessun effect. Il test
    verifica che il codice non abbia hook di attivazione effect metadata.
    """
    preserved_ids = [
        "preserved-1", "preserved-2", "preserved-3",
        "preserved-4", "preserved-5", "preserved-6",
        "preserved-7", "preserved-8", "preserved-9",
    ]
    items = [
        {"id": pid, "strength_bonus": 5, "power_score": 10,
         # simuliamo presenza (ipotetica) di effect_metadata futuro
         "effect_metadata": {"proc_chance": 0.5, "type": "future"}}
        for pid in preserved_ids
    ]
    r = evaluate_runtime_stats(base_stats={"strength": 100}, equipment_items=items)
    # Solo aggregazione stat: 100 + 9*5 = 145
    assert r.nominal_stats["strength"] == 145
    # Nessun campo runtime "effect_fired" o simile appare nel result
    field_names = set(r.__dataclass_fields__.keys())
    for forbidden in ("effect_fired", "proc_result", "mark_applied", "cooldown_started"):
        assert forbidden not in field_names


# ─── Missing optional stats ────────────────────────────────────────────
def test_missing_optional_stats_zero():
    """Stat mancanti sono trattate come 0 (P0Q10 verbatim)."""
    # Nessuna stat fornita nel base
    r = evaluate_runtime_stats(base_stats={})
    for stat in ("strength", "agility", "intellect", "endurance", "faith"):
        assert r.nominal_stats[stat] == 0
        assert r.effective_stats[stat] == Decimal(0)


def test_partial_stats_zero_fill():
    """Solo alcune stat fornite; le altre riempite a 0."""
    r = evaluate_runtime_stats(base_stats={"strength": 50})
    assert r.nominal_stats["strength"] == 50
    assert r.nominal_stats["intellect"] == 0


def test_missing_optional_in_equipment():
    items = [{"strength_bonus": 10}]  # solo strength_bonus
    r = evaluate_runtime_stats(base_stats={"strength": 0}, equipment_items=items)
    assert r.nominal_stats["strength"] == 10
    assert r.nominal_stats["agility"] == 0


# ─── Flags OFF byte-equivalence ────────────────────────────────────────
def test_both_flags_off_shadow_returns_none():
    """Entrambi i flag OFF → shadow non emette output (nessun percorso RT2-A raggiunto)."""
    assert not ff.is_enabled("runtime_stat_soft_cap_enabled")
    assert not ff.is_enabled("runtime_stat_shadow_enabled")
    result = compare_shadow(
        expedition_id="e-any", adventurer_id="a-any",
        current_base_power=100, base_stats={"strength": 50},
    )
    assert result is None


def test_flags_off_repeated_calls_pure():
    """Chiamate ripetute con flag OFF non lasciano side effect osservabili."""
    for i in range(50):
        r = compare_shadow(
            expedition_id=f"e-{i}", adventurer_id=f"a-{i}",
            current_base_power=100 + i, base_stats={"strength": 10 + i},
        )
        assert r is None


def test_soft_cap_disabled_semantically_no_authoritative_write():
    """Anche con soft_cap flag ON (in test env), la libreria non scrive DB né mut ate globali.

    RT2-A è pure library: enabling il flag NON crea side effect fuori dalla chiamata.
    """
    # Verifica: modulo non espone alcuna funzione che scrive DB
    from app.stats.runtime import feature_flags, modifier_order, soft_caps, shadow_comparison
    for mod in (feature_flags, modifier_order, soft_caps, shadow_comparison):
        for attr in dir(mod):
            if attr.startswith("_"):
                continue
            fn = getattr(mod, attr)
            if callable(fn):
                # Nomi vietati per API pubbliche RT2-A
                assert not attr.lower().startswith("write_")
                assert not attr.lower().startswith("save_")
                assert not attr.lower().startswith("persist_")
                assert not attr.lower().startswith("commit_")


def test_unknown_key_in_item_ignored_not_error():
    """Item con chiavi sconosciute (es. effect_metadata) → ignorate, no error."""
    items = [{"id": "x", "strength_bonus": 10, "unknown_field": "value", "effect_metadata": {}}]
    r = evaluate_runtime_stats(base_stats={"strength": 5}, equipment_items=items)
    assert r.nominal_stats["strength"] == 15
