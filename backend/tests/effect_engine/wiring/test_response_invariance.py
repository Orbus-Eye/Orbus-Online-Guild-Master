"""RT2-B-2A · Test feature flag registry invariants + activation semantics.

Copre B2Q07 verbatim: FF server-side startup, evaluated once at lifecycle entry
(frozen per operation), default OFF, no dynamic update via DB/API.
"""
from __future__ import annotations

import pytest

from app.stats.runtime import feature_flags


def test_all_flags_still_eight():
    """T-2A-27 (updated RT2-B-2B-2-1): ALL_FLAGS conta esattamente 8 (RT2-A: 2, RT2-B: 3, future: 3)."""
    assert len(feature_flags.ALL_FLAGS) == 8


def test_rt2b_runtime_attivabile_contains_cdv():
    """T-2A-28: `cdv_transient_state_enabled` è in RT2_B_RUNTIME_ATTIVABILE."""
    assert "cdv_transient_state_enabled" in feature_flags.RT2_B_RUNTIME_ATTIVABILE


def test_cdv_no_longer_in_future_constants():
    """T-2A-29: `cdv_transient_state_enabled` NON è più in RT2_FUTURE_CONSTANTS."""
    assert "cdv_transient_state_enabled" not in feature_flags.RT2_FUTURE_CONSTANTS


def test_cdv_flag_default_off(disable_cdv_flag):
    """T-2A-30: default OFF (senza env var settata)."""
    assert feature_flags.is_enabled("cdv_transient_state_enabled") is False


def test_cdv_flag_activation_via_env(enable_cdv_flag):
    """T-2A-31: env var truthy → flag attivo (activation locale/test)."""
    assert feature_flags.is_enabled("cdv_transient_state_enabled") is True


def test_future_constants_still_hard_forced_false(monkeypatch):
    """T-2A-32: item_effect_engine/cdv_item_hooks/effect_observability HARD-forced False."""
    for flag in feature_flags.RT2_FUTURE_CONSTANTS:
        monkeypatch.setenv(feature_flags._env_var_name(flag), "true")
    feature_flags.reset_cache()
    try:
        for flag in feature_flags.RT2_FUTURE_CONSTANTS:
            assert feature_flags.is_enabled(flag) is False, (
                f"future constant {flag} bypassed hard-force"
            )
    finally:
        feature_flags.reset_cache()


def test_soft_cap_flag_not_authoritative_by_default(monkeypatch):
    """T-2A-33: `runtime_stat_soft_cap_enabled` default False (soft cap non autoritativo per B2Q07)."""
    monkeypatch.delenv("ORBUS_FLAG_RUNTIME_STAT_SOFT_CAP_ENABLED", raising=False)
    feature_flags.reset_cache()
    try:
        assert feature_flags.is_enabled("runtime_stat_soft_cap_enabled") is False
    finally:
        feature_flags.reset_cache()


def test_unknown_flag_returns_false():
    """T-2A-34: flag sconosciuto → False + audit ERROR (fail-safe)."""
    assert feature_flags.is_enabled("this_flag_does_not_exist_xyz") is False
