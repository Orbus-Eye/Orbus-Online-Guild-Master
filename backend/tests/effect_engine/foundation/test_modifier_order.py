"""RT2-A · test_modifier_order.py

Verifica ordine deterministico 9-step + rounding + error handling.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime.modifier_order import (
    ModifierOrderError,
    derived_base_power,
    evaluate_runtime_stats,
)


def test_base_only():
    base = {"strength": 10, "agility": 5, "intellect": 3, "endurance": 2, "faith": 1}
    result = evaluate_runtime_stats(base_stats=base)
    assert result.nominal_stats == base
    assert result.effective_stats["strength"] == Decimal(10)
    assert result.soft_cap_applied is False
    assert result.evaluation_duration_ns >= 0


def test_step2_equipment_flat():
    base = {"strength": 10, "intellect": 5}
    items = [{"strength_bonus": 20, "intellect_bonus": 10}]
    result = evaluate_runtime_stats(base_stats=base, equipment_items=items)
    assert result.nominal_stats["strength"] == 30
    assert result.nominal_stats["intellect"] == 15


def test_step3_permanent_modifiers():
    base = {"strength": 10}
    perm = {"strength": 5}
    result = evaluate_runtime_stats(base_stats=base, permanent_modifiers=perm)
    assert result.nominal_stats["strength"] == 15


def test_step4_temporary_modifiers():
    base = {"strength": 10}
    temp = {"strength": 3}
    result = evaluate_runtime_stats(base_stats=base, temporary_modifiers_at_start=temp)
    assert result.nominal_stats["strength"] == 13


def test_step5_percent_modifiers():
    base = {"strength": 100}
    pct = {"strength": 20}  # +20%
    result = evaluate_runtime_stats(base_stats=base, percent_modifiers=pct)
    assert result.nominal_stats["strength"] == 120


def test_step5_percent_debuff():
    base = {"strength": 100}
    pct = {"strength": -25}  # -25%
    result = evaluate_runtime_stats(base_stats=base, percent_modifiers=pct)
    assert result.nominal_stats["strength"] == 75


def test_step6_clamp_negative_to_zero():
    base = {"strength": 5}
    perm = {"strength": -50}  # crea nominal negativo
    result = evaluate_runtime_stats(base_stats=base, permanent_modifiers=perm)
    assert result.nominal_stats["strength"] == 0  # clamp


def test_step7_soft_cap_applied():
    base = {"intellect": 200}
    result = evaluate_runtime_stats(base_stats=base)
    assert result.nominal_stats["intellect"] == 200
    assert result.effective_stats["intellect"] == Decimal("150.0000")
    assert result.soft_cap_applied is True
    assert result.soft_cap_delta == Decimal("50.0000")


def test_step7_intellect_no_cap_others_untouched():
    """Solo intellect subisce soft cap; le altre stat rimangono nominali."""
    base = {"strength": 500, "intellect": 500}
    result = evaluate_runtime_stats(base_stats=base)
    assert result.effective_stats["strength"] == Decimal(500)
    assert result.effective_stats["intellect"] == Decimal("300.0000")


def test_step8_derived_base_power():
    base = {"strength": 10, "agility": 5, "intellect": 3, "endurance": 2, "faith": 1}
    result = evaluate_runtime_stats(base_stats=base)
    # sum = 21; level=1 → +2 → 23
    assert derived_base_power(result, level=1) == 23
    assert derived_base_power(result, level=10) == 41


def test_full_9_step_composition():
    """Composizione 9-step su esempio combinato."""
    base = {"strength": 50, "intellect": 80}
    items = [{"strength_bonus": 10, "intellect_bonus": 15}]
    perm = {"strength": 5}
    temp = {"intellect": 10}
    pct = {"strength": 10, "intellect": 0}
    result = evaluate_runtime_stats(
        base_stats=base,
        equipment_items=items,
        permanent_modifiers=perm,
        temporary_modifiers_at_start=temp,
        percent_modifiers=pct,
    )
    # Str: (50+10+5+0)*(1.10) = 65*1.10 = 71.5 → ROUND_HALF_UP → 72
    # Int: (80+15+0+10)*(1.00) = 105 → soft cap → 100 + 5*0.5 = 102.5
    assert result.nominal_stats["strength"] == 72
    assert result.nominal_stats["intellect"] == 105
    assert result.effective_stats["intellect"] == Decimal("102.5000")
    assert result.soft_cap_applied is True


def test_unknown_stat_field_in_base_raises():
    with pytest.raises(ModifierOrderError):
        evaluate_runtime_stats(base_stats={"strength": 10, "unknown_stat": 5})


def test_missing_optional_treated_as_zero():
    base = {"strength": 10}  # solo strength; altre stat mancanti
    result = evaluate_runtime_stats(base_stats=base)
    for s in ("agility", "intellect", "endurance", "faith"):
        assert result.nominal_stats[s] == 0
        assert result.effective_stats[s] == Decimal(0)


def test_none_input_safe():
    result = evaluate_runtime_stats(base_stats={"strength": 10}, equipment_items=None,
                                    permanent_modifiers=None, temporary_modifiers_at_start=None,
                                    percent_modifiers=None)
    assert result.nominal_stats["strength"] == 10


def test_it_alias_in_base_rejected():
    """Solo runtime canonical names in base_stats; IT alias → validation error."""
    with pytest.raises(ModifierOrderError):
        evaluate_runtime_stats(base_stats={"forza": 10})


def test_unknown_keys_in_optional_dicts_ignored():
    """Modifier dicts opzionali: chiavi sconosciute → silently ignored."""
    base = {"strength": 10}
    perm = {"strength": 5, "unknown": 99}
    result = evaluate_runtime_stats(base_stats=base, permanent_modifiers=perm)
    assert result.nominal_stats["strength"] == 15


def test_reason_code():
    r1 = evaluate_runtime_stats(base_stats={"intellect": 50})
    assert r1.reason_code == "RT2A_STAT_EVAL_NO_CAP"
    r2 = evaluate_runtime_stats(base_stats={"intellect": 200})
    assert r2.reason_code == "RT2A_STAT_EVAL_OK"


def test_result_is_frozen_dataclass():
    result = evaluate_runtime_stats(base_stats={"strength": 10})
    with pytest.raises((AttributeError, Exception)):
        result.nominal_stats = {}  # frozen
