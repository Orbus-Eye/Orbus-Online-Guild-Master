"""RT2-A · test_rounding.py

Verifica ROUND_HALF_UP + precisione display (1 decimale) + internal (4 decimali).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime.soft_caps import effective_intelligence, format_display
from app.stats.runtime.modifier_order import derived_base_power, evaluate_runtime_stats


def test_display_1_decimal_round_half_up():
    assert format_display(Decimal("100.05")) == "100.1"  # round half up
    assert format_display(Decimal("100.04")) == "100.0"
    assert format_display(Decimal("100.15")) == "100.2"
    assert format_display(Decimal("100.14")) == "100.1"


def test_internal_4_decimals_precision():
    val = effective_intelligence(101)
    # 101 → 100.5; internal must be 100.5000
    assert val == Decimal("100.5000")
    assert str(val) == "100.5000"


def test_intermediate_no_rounding_for_pre_cap():
    for x in [50, 75, 99, 100]:
        assert effective_intelligence(x) == Decimal(x).quantize(Decimal("0.0001"))


def test_derived_power_round_half_up():
    """derived_base_power quantizes final total ROUND_HALF_UP."""
    # base sum with intellect at soft cap 200 → eff 150; others 0
    base = {"intellect": 200}
    result = evaluate_runtime_stats(base_stats=base)
    # effective = 150 (intellect) + 0*4; level=1 → +2 → 152
    assert derived_base_power(result, level=1) == 152


def test_percent_modifier_rounding_deterministic():
    """+33% su 100 = 133 esatto (nessun drift decimale)."""
    base = {"strength": 100}
    pct = {"strength": 33}
    r = evaluate_runtime_stats(base_stats=base, percent_modifiers=pct)
    assert r.nominal_stats["strength"] == 133


def test_percent_modifier_odd_rounding():
    """+15% su 7 = 8.05 → ROUND_HALF_UP → 8."""
    base = {"strength": 7}
    pct = {"strength": 15}
    r = evaluate_runtime_stats(base_stats=base, percent_modifiers=pct)
    # 7 * 1.15 = 8.05 → 8 (ROUND_HALF_UP quantize to 1)
    assert r.nominal_stats["strength"] == 8
