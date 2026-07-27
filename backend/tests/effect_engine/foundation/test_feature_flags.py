"""RT2-A · test_feature_flags.py"""
from __future__ import annotations

import os

import pytest

from app.stats.runtime import feature_flags as ff


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Reset env + cache prima di ogni test."""
    for f in ff.ALL_FLAGS:
        monkeypatch.delenv(f"ORBUS_FLAG_{f.upper()}", raising=False)
    ff.reset_cache()
    yield
    ff.reset_cache()


def test_all_flags_count_is_8():
    """RT2-B-2B-2-1 · 2026-02: aggiunto `cdv_drain_transitions_enabled`
    (RT2_B_RUNTIME_ATTIVABILE cresce a 3 flag). Totale 8."""
    assert len(ff.ALL_FLAGS) == 8
    assert ff.ALL_FLAGS == (
        ff.RT2_A_RUNTIME_ATTIVABILE | ff.RT2_B_RUNTIME_ATTIVABILE | ff.RT2_FUTURE_CONSTANTS
    )


def test_default_all_off():
    """P0Q04 verbatim: tutti i flag default false."""
    for f in ff.ALL_FLAGS:
        assert ff.is_enabled(f) is False


def test_rt2a_active_flags_are_two():
    assert ff.RT2_A_RUNTIME_ATTIVABILE == frozenset({
        "runtime_stat_soft_cap_enabled",
        "runtime_stat_shadow_enabled",
    })


def test_rt2b_active_flags_are_three():
    """RT2-B-2B-2-1 · PM Message 170 B2B2Q13 verbatim (2026-02):
    - `cdv_transient_state_enabled` (RT2-B-2A)
    - `cdv_class_transitions_enabled` (RT2-B-2B-1)
    - `cdv_drain_transitions_enabled` (RT2-B-2B-2-1, nuovo, default OFF, surgical kill-switch)
    """
    assert ff.RT2_B_RUNTIME_ATTIVABILE == frozenset({
        "cdv_transient_state_enabled",
        "cdv_class_transitions_enabled",
        "cdv_drain_transitions_enabled",
    })


def test_rt2_future_constants_are_three():
    """Post-RT2-B-2A: `cdv_transient_state_enabled` è stato spostato a
    RT2_B_RUNTIME_ATTIVABILE. Future constants residui = 3."""
    assert ff.RT2_FUTURE_CONSTANTS == frozenset({
        "item_effect_engine_enabled",
        "cdv_item_hooks_enabled",
        "effect_observability_enabled",
    })


def test_soft_cap_enabled_via_env(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SOFT_CAP_ENABLED", "true")
    ff.reset_cache()
    assert ff.is_enabled("runtime_stat_soft_cap_enabled") is True


def test_shadow_enabled_via_env(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "1")
    ff.reset_cache()
    assert ff.is_enabled("runtime_stat_shadow_enabled") is True


def test_truthy_values(monkeypatch):
    for val in ("1", "true", "True", "TRUE", "yes", "YES", "on", "ON"):
        monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", val)
        ff.reset_cache()
        assert ff.is_enabled("runtime_stat_shadow_enabled") is True, f"failed for {val!r}"


def test_falsy_values(monkeypatch):
    for val in ("0", "false", "FALSE", "no", "off", ""):
        monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", val)
        ff.reset_cache()
        assert ff.is_enabled("runtime_stat_shadow_enabled") is False, f"failed for {val!r}"


def test_invalid_value_falls_back_false(monkeypatch, caplog):
    """Invalid value → log ERROR + return False (fail-safe P0Q04)."""
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "gibberish_val")
    ff.reset_cache()
    with caplog.at_level("ERROR"):
        assert ff.is_enabled("runtime_stat_shadow_enabled") is False


def test_future_constants_hard_forced_false(monkeypatch):
    """RT2-A enforcement: le 4 costanti future restano False anche con env=true."""
    for flag in ff.RT2_FUTURE_CONSTANTS:
        monkeypatch.setenv(f"ORBUS_FLAG_{flag.upper()}", "true")
        ff.reset_cache()
        assert ff.is_enabled(flag) is False, (
            f"{flag} must remain False in RT2-A even with env truthy"
        )


def test_unknown_flag_returns_false(caplog):
    with caplog.at_level("ERROR"):
        assert ff.is_enabled("nonexistent_flag_xyz") is False


def test_missing_env_is_false():
    """Missing flag → false (P0Q04 fail-safe)."""
    # Autouse fixture ha già rimosso env
    assert ff.is_enabled("runtime_stat_soft_cap_enabled") is False


def test_all_flags_status_snapshot():
    status = ff.all_flags_status()
    assert set(status.keys()) == set(ff.ALL_FLAGS)
    assert all(v is False for v in status.values())


def test_no_client_channel():
    """P0Q04 vieta canali client. Verifica dichiarativa: modulo NON espone
    setter, NON legge da API, NON legge da DB dinamico."""
    # is_enabled è l'unica API pubblica per lettura
    exposed = {name for name in dir(ff) if not name.startswith("_")}
    # Nessun setter, nessuna funzione di attivazione runtime
    assert not any(name.startswith("set_") for name in exposed)
    assert not any(name.startswith("enable_") for name in exposed)
    assert not any(name.startswith("disable_") for name in exposed)
