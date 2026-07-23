"""RT2-A · test_equipment_aggregation.py"""
from __future__ import annotations

from app.stats.runtime.equipment_aggregation import (
    aggregate_equipment_flat_stats,
    total_power_score_contribution,
)
from app.stats.runtime.stat_bridge import RUNTIME_STATS


def test_none_input():
    result = aggregate_equipment_flat_stats(None)
    assert result == {s: 0 for s in RUNTIME_STATS}


def test_empty_iterable():
    assert aggregate_equipment_flat_stats([]) == {s: 0 for s in RUNTIME_STATS}


def test_single_item_all_stats():
    items = [{
        "strength_bonus": 5,
        "agility_bonus": 3,
        "intellect_bonus": 8,
        "endurance_bonus": 2,
        "faith_bonus": 1,
    }]
    result = aggregate_equipment_flat_stats(items)
    assert result == {"strength": 5, "agility": 3, "intellect": 8, "endurance": 2, "faith": 1}


def test_multiple_items_sum():
    items = [
        {"strength_bonus": 5, "intellect_bonus": 10},
        {"strength_bonus": 3, "agility_bonus": 2},
        {"intellect_bonus": 7},
    ]
    result = aggregate_equipment_flat_stats(items)
    assert result["strength"] == 8
    assert result["intellect"] == 17
    assert result["agility"] == 2
    assert result["endurance"] == 0
    assert result["faith"] == 0


def test_missing_optional_stats_treated_as_zero():
    items = [{"strength_bonus": 5}]  # no other stats
    result = aggregate_equipment_flat_stats(items)
    assert result["strength"] == 5
    assert result["agility"] == 0


def test_none_values_safe():
    items = [{"strength_bonus": None, "intellect_bonus": 10}]
    result = aggregate_equipment_flat_stats(items)
    assert result["strength"] == 0
    assert result["intellect"] == 10


def test_malformed_values_treated_as_zero():
    items = [{"strength_bonus": "abc", "intellect_bonus": "5"}]
    result = aggregate_equipment_flat_stats(items)
    assert result["strength"] == 0  # malformed → skip
    assert result["intellect"] == 5  # numeric string is coercible


def test_unknown_keys_ignored():
    items = [{"strength_bonus": 5, "unknown_bonus": 100, "power_score": 50}]
    result = aggregate_equipment_flat_stats(items)
    assert result["strength"] == 5
    # power_score NOT aggregated here
    assert "power_score" not in result


def test_non_dict_items_ignored():
    items = [None, "string", 42, {"strength_bonus": 5}]
    result = aggregate_equipment_flat_stats(items)
    assert result["strength"] == 5


def test_power_score_contribution():
    items = [{"power_score": 10}, {"power_score": 25}, {"power_score": None}]
    assert total_power_score_contribution(items) == 35
    assert total_power_score_contribution(None) == 0
    assert total_power_score_contribution([]) == 0


def test_legacy_item_no_effect_metadata():
    """Item legacy senza effect_metadata è valido e produce solo stat aggregation."""
    legacy = [{"id": "sword_of_legacy", "strength_bonus": 12, "power_score": 30}]
    result = aggregate_equipment_flat_stats(legacy)
    ps = total_power_score_contribution(legacy)
    assert result["strength"] == 12
    assert ps == 30
