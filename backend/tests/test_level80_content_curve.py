"""Level-80 dungeon and raid progression contract."""
from collections import defaultdict

from app.dungeons.encounters import DUNGEON_ENCOUNTERS
from app.expeditions.level_gate import (
    legacy_min_level_for_dungeon,
    legacy_min_level_for_raid,
)
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.content_curve import (
    ADVENTURER_LEVEL_BANDS,
    DUNGEON_CURVE,
    DUNGEON_TEAM_SIZE_TARGETS,
    RAID_CURVE,
    adventurer_level_band,
)


def test_level_bands_cover_every_level_exactly_once():
    covered = [
        level
        for start, end, _name in ADVENTURER_LEVEL_BANDS
        for level in range(start, end + 1)
    ]
    assert covered == list(range(1, ADVENTURER_MAX_LEVEL + 1))
    assert adventurer_level_band(1) == "novizio"
    assert adventurer_level_band(80) == "endgame"


def test_current_dungeons_form_monotonic_party_curves_up_to_level_70():
    levels = sorted({entry.required_level for entry in DUNGEON_CURVE.values()})
    assert levels[0] == 1
    assert levels[-1] == 70
    assert all(1 <= b - a <= 10 for a, b in zip(levels, levels[1:]))
    tracks = defaultdict(list)
    for slug, entry in DUNGEON_CURVE.items():
        # FASE 8A: la curva dimensiona il potere sulla team size
        # autoritativa post-redistribuzione 3/5/7 (Fase 2.3), non su
        # quella storica di DUNGEON_ENCOUNTERS (es. sunken-library è
        # un'incursione da 3: chiede meno potere di un 5-piazze pari
        # livello, per design).
        size = DUNGEON_TEAM_SIZE_TARGETS.get(
            slug, DUNGEON_ENCOUNTERS[slug].team_size
        )
        tracks[size].append(entry)
    assert set(tracks) == {3, 5, 7}
    for entries in tracks.values():
        ordered = sorted(
            entries,
            key=lambda entry: (entry.required_level, entry.recommended_power),
        )
        assert all(
            later.recommended_power >= earlier.recommended_power
            for earlier, later in zip(ordered, ordered[1:])
        )


def test_raids_bridge_high_level_and_end_at_the_cap():
    ordered = sorted(RAID_CURVE.values(), key=lambda entry: entry.required_level)
    assert [entry.required_level for entry in ordered] == [40, 60, 70, 80]
    assert ordered[-1].required_level == ADVENTURER_MAX_LEVEL
    assert all(
        later.recommended_power > earlier.recommended_power
        for earlier, later in zip(ordered, ordered[1:])
    )


def test_runtime_gate_prefers_authoritative_curve_over_stale_db_values():
    assert legacy_min_level_for_dungeon(
        {"slug": "world-tree-roots-5p", "required_level": 14}
    ) == 70
    assert legacy_min_level_for_raid(
        {"slug": "dragon-vault", "min_adventurer_level": 12, "tier": 2}
    ) == 80
