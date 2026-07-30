from __future__ import annotations

import pytest

from app.stats.runtime import feature_flags
from app.stats.runtime.wiring.feature_flags import (
    EffectGateContext,
    effect_gate_snapshot,
    is_effect_gate_open,
)


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for flag in feature_flags.ALL_FLAGS:
        monkeypatch.delenv(
            f"ORBUS_FLAG_{flag.upper()}",
            raising=False,
        )
    feature_flags.reset_cache()
    yield
    feature_flags.reset_cache()


def _context(**overrides):
    values = {
        "is_test_user": True,
        "environment_is_localhost_isolated": True,
        "mongo_target_allowlisted": True,
    }
    values.update(overrides)
    return EffectGateContext(**values)


def test_effect_flag_is_default_off_and_flag_total_remains_eight():
    assert len(feature_flags.ALL_FLAGS) == 8
    assert not feature_flags.is_enabled("item_effect_engine_enabled")
    assert "item_effect_engine_enabled" in feature_flags.RT2_C_RUNTIME_ATTIVABILE
    assert "item_effect_engine_enabled" not in feature_flags.RT2_FUTURE_CONSTANTS


def test_effect_gate_requires_transient_first():
    assert is_effect_gate_open(_context()) == (
        False,
        "TRANSIENT_STATE_DISABLED",
    )


def test_effect_gate_requires_effect_flag(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    feature_flags.reset_cache()
    assert is_effect_gate_open(_context()) == (
        False,
        "ITEM_EFFECT_ENGINE_DISABLED",
    )


def test_effect_gate_all_conditions_open(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    monkeypatch.setenv("ORBUS_FLAG_ITEM_EFFECT_ENGINE_ENABLED", "true")
    feature_flags.reset_cache()
    assert is_effect_gate_open(_context()) == (True, "GATE_OPEN")
    assert effect_gate_snapshot() == {
        "cdv_transient_state_enabled": True,
        "item_effect_engine_enabled": True,
    }


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"is_test_user": False}, "TEST_USER_BOUNDARY_VIOLATION"),
        (
            {"environment_is_localhost_isolated": False},
            "ENVIRONMENT_NOT_LOCALHOST_ISOLATED",
        ),
        ({"mongo_target_allowlisted": False}, "DB_NOT_ALLOWLISTED"),
    ],
)
def test_effect_gate_runtime_boundaries(monkeypatch, override, reason):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    monkeypatch.setenv("ORBUS_FLAG_ITEM_EFFECT_ENGINE_ENABLED", "true")
    feature_flags.reset_cache()
    assert is_effect_gate_open(_context(**override)) == (False, reason)


def test_truthy_non_boolean_context_value_fails_closed(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    monkeypatch.setenv("ORBUS_FLAG_ITEM_EFFECT_ENGINE_ENABLED", "true")
    feature_flags.reset_cache()
    assert is_effect_gate_open(_context(is_test_user=1)) == (
        False,
        "TEST_USER_BOUNDARY_VIOLATION",
    )
