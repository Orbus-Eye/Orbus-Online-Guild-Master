"""RT2-A · test_shadow_comparison.py"""
from __future__ import annotations

import pytest

from app.stats.runtime import feature_flags as ff
from app.stats.runtime.shadow_comparison import (
    ShadowComparisonResult,
    compare_shadow,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for f in ff.ALL_FLAGS:
        monkeypatch.delenv(f"ORBUS_FLAG_{f.upper()}", raising=False)
    ff.reset_cache()
    yield
    ff.reset_cache()


def _sample_base():
    return {"strength": 50, "agility": 30, "intellect": 80, "endurance": 20, "faith": 10}


def test_flag_off_returns_none():
    """Flag OFF → nessun calcolo, ritorna None (P0Q05 verbatim)."""
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=100,
        base_stats=_sample_base(),
    )
    assert result is None


def test_flag_on_returns_result(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=100,
        base_stats=_sample_base(),
    )
    assert isinstance(result, ShadowComparisonResult)


def test_all_10_diagnostic_fields_present(monkeypatch):
    """P0Q05 verbatim: 10 diagnostic fields obbligatori."""
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=100,
        base_stats=_sample_base(),
    )
    expected_fields = {
        "expedition_id", "adventurer_id", "nominal_intelligence",
        "effective_intelligence", "current_base_power", "candidate_base_power",
        "power_delta", "soft_cap_applied", "evaluation_duration_ms", "reason_code",
    }
    assert set(result.__dataclass_fields__.keys()) == expected_fields


def test_soft_cap_reflected(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=100,
        base_stats={"intellect": 200},
    )
    assert result.soft_cap_applied is True
    assert result.nominal_intelligence == 200
    assert result.effective_intelligence == 150.0


def test_power_delta_signed(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    # base has stats summing high; current_base_power=0 → candidate way higher → delta positive
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=0,
        base_stats=_sample_base(),
    )
    assert result.power_delta == result.candidate_base_power


def test_failure_returns_diagnostic_no_raise(monkeypatch):
    """Candidate failure NON deve propagare exception. Gameplay untouched."""
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    # base_stats con chiave sconosciuta → ModifierOrderError caught internally
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=100,
        base_stats={"unknown_stat_xyz": 999},
    )
    assert result is not None
    assert result.reason_code == "RT2A_SHADOW_CANDIDATE_FAILURE"


def test_shadow_never_modifies_input(monkeypatch):
    """Shadow evaluation è read-only. Input dict NON deve essere mutato."""
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    base = _sample_base()
    base_copy = dict(base)
    compare_shadow(
        expedition_id="e1", adventurer_id="a1",
        current_base_power=100, base_stats=base,
    )
    assert base == base_copy  # input untouched


def test_evaluation_duration_ms_positive(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    result = compare_shadow(
        expedition_id="e1", adventurer_id="a1",
        current_base_power=100, base_stats=_sample_base(),
    )
    assert result.evaluation_duration_ms >= 0.0
