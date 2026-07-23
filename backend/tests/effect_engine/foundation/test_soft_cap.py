"""RT2-A · test_soft_cap.py

Unit tests + i 5 casi boundary OBBLIGATORI (verbatim P0Q10).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime.soft_caps import (
    INTELLIGENCE_SOFT_CAP,
    POST_CAP_EFFECTIVE_RETURN,
    SoftCapError,
    effective_intelligence,
    format_display,
    soft_cap_applied,
    soft_cap_delta,
)


# ─── Casi boundary OBBLIGATORI (verbatim P0Q10) ────────────────────────
@pytest.mark.parametrize(
    "nominal, expected_display",
    [
        (99, "99.0"),
        (100, "100.0"),
        (101, "100.5"),
        (105, "102.5"),
        (200, "150.0"),
    ],
)
def test_soft_cap_mandatory_boundary_cases(nominal, expected_display):
    """5 casi obbligatori RT1: 99→99.0, 100→100.0, 101→100.5, 105→102.5, 200→150.0."""
    result = effective_intelligence(nominal)
    assert format_display(result) == expected_display


def test_soft_cap_constants():
    assert INTELLIGENCE_SOFT_CAP == 100
    assert POST_CAP_EFFECTIVE_RETURN == Decimal("0.5")


def test_zero_and_below():
    assert effective_intelligence(0) == Decimal("0.0000")
    assert effective_intelligence(-5) == Decimal("0.0000")  # clamp
    assert effective_intelligence(None) == Decimal("0.0000")


def test_pre_cap_identity():
    for x in [1, 25, 50, 75, 99, 100]:
        assert effective_intelligence(x) == Decimal(x).quantize(Decimal("0.0001"))


def test_post_cap_scaling():
    # 100 + (x - 100) * 0.5
    assert effective_intelligence(120) == Decimal("110.0000")
    assert effective_intelligence(150) == Decimal("125.0000")
    assert effective_intelligence(1000) == Decimal("550.0000")


def test_non_numeric_raises():
    with pytest.raises(SoftCapError):
        effective_intelligence("not-a-number")
    with pytest.raises(SoftCapError):
        effective_intelligence(object())


def test_soft_cap_applied_predicate():
    assert soft_cap_applied(100) is False
    assert soft_cap_applied(99) is False
    assert soft_cap_applied(101) is True
    assert soft_cap_applied(1000) is True


def test_soft_cap_delta():
    assert soft_cap_delta(100) == Decimal("0.0000")
    assert soft_cap_delta(200) == Decimal("50.0000")  # 200 - 150 = 50
    assert soft_cap_delta(101) == Decimal("0.5000")  # 101 - 100.5


def test_format_display_precision():
    assert format_display(Decimal("102.5000")) == "102.5"
    assert format_display(Decimal("102.5500")) == "102.6"  # ROUND_HALF_UP
    assert format_display(Decimal("102.4400")) == "102.4"


def test_int_and_float_input_equivalence():
    assert effective_intelligence(200) == effective_intelligence(200.0)
    assert effective_intelligence(200) == effective_intelligence(Decimal(200))
