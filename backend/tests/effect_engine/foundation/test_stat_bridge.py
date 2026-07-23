"""RT2-A · test_stat_bridge.py"""
from __future__ import annotations

import pytest

from app.stats.runtime.stat_bridge import (
    RUNTIME_STATS,
    StatBridgeError,
    is_runtime_stat,
    known_it_aliases,
    to_runtime,
)


def test_runtime_stats_are_5_canonical():
    assert RUNTIME_STATS == ("strength", "agility", "intellect", "endurance", "faith")


@pytest.mark.parametrize(
    "input_name, expected",
    [
        ("Forza", "strength"),
        ("forza", "strength"),
        ("FORZA", "strength"),
        ("vigore", "strength"),
        ("Potenza", "strength"),
        ("strength", "strength"),
        ("Destrezza", "agility"),
        ("Agilità", "agility"),
        ("Agilita", "agility"),
        ("agility", "agility"),
        ("Intelligenza", "intellect"),
        ("Intelletto", "intellect"),
        ("Volontà", "intellect"),
        ("Volonta", "intellect"),
        ("saggezza", "intellect"),
        ("intellect", "intellect"),
        ("Costituzione", "endurance"),
        ("Resistenza", "endurance"),
        ("endurance", "endurance"),
        ("Fede", "faith"),
        ("Spirito", "faith"),
        ("Carisma", "faith"),
        ("faith", "faith"),
    ],
)
def test_it_and_runtime_bridge(input_name, expected):
    assert to_runtime(input_name) == expected


def test_is_runtime_stat():
    for s in RUNTIME_STATS:
        assert is_runtime_stat(s)
    assert not is_runtime_stat("nonexistent")
    assert not is_runtime_stat("Forza")  # only runtime canonical name


def test_unknown_key_raises():
    with pytest.raises(StatBridgeError):
        to_runtime("gibberish_key")
    with pytest.raises(StatBridgeError):
        to_runtime("")


def test_known_it_aliases_completeness():
    aliases = known_it_aliases()
    # Deve includere le 5 canonical + aliases IT
    assert "forza" in aliases
    assert "destrezza" in aliases
    assert "intelligenza" in aliases
    assert "costituzione" in aliases
    assert "fede" in aliases
    # Aliases stessi normalizzati
    for a in aliases:
        assert a == a.lower()
