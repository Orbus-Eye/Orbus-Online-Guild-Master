"""RT2-A · test_loadout_snapshot.py

Verifica costruzione snapshot + immutabilità + campi minimi.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime.loadout_snapshot import build_loadout_snapshot
from app.stats.runtime.models import LoadoutSnapshot, SNAPSHOT_VERSION


def _sample_base():
    return {"strength": 50, "agility": 30, "intellect": 80, "endurance": 20, "faith": 10}


def test_snapshot_has_all_minimum_fields():
    snap = build_loadout_snapshot(
        adventurer_id="adv-1",
        expedition_id="exp-1",
        base_stats=_sample_base(),
    )
    # Verifica presenza dei 12 campi minimi obbligatori
    assert snap.adventurer_id == "adv-1"
    assert snap.expedition_id == "exp-1"
    assert isinstance(snap.base_stats, dict)
    assert isinstance(snap.equipment_derived_flat_stats, dict)
    assert isinstance(snap.permanent_modifiers, dict)
    assert isinstance(snap.temporary_modifiers_at_start, dict)
    assert isinstance(snap.nominal_stats, dict)
    assert isinstance(snap.effective_stats, dict)
    assert isinstance(snap.soft_cap_result, bool)
    assert isinstance(snap.source_item_blueprint_list, tuple)
    assert snap.snapshot_version == SNAPSHOT_VERSION == 1
    assert snap.created_at.endswith("+00:00") or "T" in snap.created_at


def test_snapshot_is_frozen_immutable():
    snap = build_loadout_snapshot(
        adventurer_id="adv-1",
        expedition_id="exp-1",
        base_stats=_sample_base(),
    )
    # Frozen dataclass: qualunque tentativo di set deve fallire.
    with pytest.raises((Exception,)):
        snap.adventurer_id = "hacked"


def test_snapshot_reflects_soft_cap_applied():
    base = {"intellect": 200}
    snap = build_loadout_snapshot(
        adventurer_id="a1", expedition_id="e1", base_stats=base,
    )
    assert snap.soft_cap_result is True
    assert snap.effective_stats["intellect"] == Decimal("150.0000")


def test_snapshot_captures_equipment():
    items = [
        {"id": "sword-1", "strength_bonus": 10, "power_score": 25},
        {"blueprint_id": "helmet-x", "endurance_bonus": 5},
    ]
    snap = build_loadout_snapshot(
        adventurer_id="a1",
        expedition_id="e1",
        base_stats=_sample_base(),
        equipment_items=items,
    )
    assert snap.equipment_derived_flat_stats["strength"] == 10
    assert snap.equipment_derived_flat_stats["endurance"] == 5
    # blueprint list contiene gli id
    assert "sword-1" in snap.source_item_blueprint_list
    assert "helmet-x" in snap.source_item_blueprint_list


def test_snapshot_prefers_stable_slug_over_legacy_uuid():
    snap = build_loadout_snapshot(
        adventurer_id="a1",
        expedition_id="e1",
        base_stats=_sample_base(),
        equipment_items=[
            {
                "id": "random-mongo-uuid",
                "slug": "lama-primo-giuramento",
                "strength_bonus": 1,
            }
        ],
    )
    assert snap.source_item_blueprint_list == ("lama-primo-giuramento",)


def test_snapshot_captures_modifiers():
    snap = build_loadout_snapshot(
        adventurer_id="a1",
        expedition_id="e1",
        base_stats=_sample_base(),
        permanent_modifiers={"strength": 10},
        temporary_modifiers_at_start={"faith": 5},
    )
    assert snap.permanent_modifiers["strength"] == 10
    assert snap.temporary_modifiers_at_start["faith"] == 5


def test_snapshot_diagnostic_dict_excludes_full_loadout():
    """to_diagnostic_dict deve escludere loadout completo (P0Q05 verbatim)."""
    items = [{"id": "big-secret-item", "strength_bonus": 999}]
    snap = build_loadout_snapshot(
        adventurer_id="a1", expedition_id="e1",
        base_stats=_sample_base(), equipment_items=items,
    )
    diag = snap.to_diagnostic_dict()
    # Contiene solo diagnostica sicura
    assert diag["adventurer_id"] == "a1"
    assert diag["expedition_id"] == "e1"
    assert "loadout" not in diag  # NO full loadout
    assert "equipment_items" not in diag
    assert "source_item_blueprint_list" not in diag  # solo blueprint_count aggregato
    assert isinstance(diag["blueprint_count"], int)


def test_snapshot_requires_ids():
    with pytest.raises(ValueError):
        build_loadout_snapshot(
            adventurer_id="", expedition_id="e1", base_stats=_sample_base()
        )
    with pytest.raises(ValueError):
        build_loadout_snapshot(
            adventurer_id="a1", expedition_id="", base_stats=_sample_base()
        )


def test_snapshot_multiple_builds_do_not_share_state():
    """RT2-A snapshot immutable ⇒ costruzioni successive indipendenti."""
    base = _sample_base()
    s1 = build_loadout_snapshot(adventurer_id="a1", expedition_id="e1", base_stats=base)
    base["strength"] = 999
    s2 = build_loadout_snapshot(adventurer_id="a1", expedition_id="e2", base_stats=base)
    # s1 non deve essere mutato da modifica esterna al dict base
    assert s1.base_stats["strength"] == 50
    assert s2.base_stats["strength"] == 999
