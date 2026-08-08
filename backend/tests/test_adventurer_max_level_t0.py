"""T0 authoritative adventurer maximum level."""
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.progression import (
    can_adventurer_level_up,
    xp_required_for_next_level,
)


def test_levelup_rule_never_allows_crossing_authoritative_cap():
    assert ADVENTURER_MAX_LEVEL == 80
    assert can_adventurer_level_up(ADVENTURER_MAX_LEVEL - 1, 100_000)
    assert not can_adventurer_level_up(ADVENTURER_MAX_LEVEL, 100_000)
    assert not can_adventurer_level_up(ADVENTURER_MAX_LEVEL + 1, 100_000)


def test_xp_curve_reaches_level_80_without_a_hidden_legacy_wall():
    assert xp_required_for_next_level(15) == 7262
    assert xp_required_for_next_level(79) == 87771
    assert xp_required_for_next_level(80) == 0
