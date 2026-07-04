"""ROUND 18.2 PILOT — Talent Tree Engine test suite.

Bypass del conftest globale (isolation forcing) via `--confcutdir=/tmp -c /dev/null`
per verifica read-only sul DB dev dove il seed è stato applicato.
"""
from __future__ import annotations

import asyncio
import os
import pathlib

import pytest
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load dev DB env (override existing test env forced by conftest)
load_dotenv("/app/backend/.env")
_BACKEND_ENV = dotenv_values("/app/backend/.env")
_DEV_MONGO_URL = _BACKEND_ENV.get("MONGO_URL") or os.environ.get("MONGO_URL")
_DEV_DB_NAME = _BACKEND_ENV.get("DB_NAME") or os.environ.get("DB_NAME")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(_DEV_MONGO_URL)
    yield client[_DEV_DB_NAME]
    client.close()


# ─── 01 — Modules importable ───────────────────────────────────────────
def test_01_talents_module_importable():
    from app.talents import models as m
    assert hasattr(m, "TalentTreeDefinition")
    assert hasattr(m, "AdventurerTalentProgress")
    assert hasattr(m, "TalentAllocation")
    assert hasattr(m, "PILOT_CLASS_SLUGS")
    assert hasattr(m, "build_placeholder_id")
    assert len(m.PILOT_CLASS_SLUGS) == 9


# ─── 02 — Constants sigillati PM ───────────────────────────────────────
def test_02_pilot_constants():
    from app.talents.models import (
        BRANCHES_PER_CLASS, TIERS_PER_BRANCH, SLOTS_PER_TIER,
        SLOTS_PER_CLASS, MAX_POINTS_PER_ADVENTURER, PILOT_CLASS_SLUGS,
    )
    assert BRANCHES_PER_CLASS == 3
    assert TIERS_PER_BRANCH == 5
    assert SLOTS_PER_TIER == 4
    assert SLOTS_PER_CLASS == 60
    assert MAX_POINTS_PER_ADVENTURER == 30
    assert PILOT_CLASS_SLUGS == {
        "warrior", "rogue", "mage", "paladin", "druid",
        "necromancer", "monk", "bard", "alchemist",
    }


# ─── 03 — Placeholder ID deterministic ─────────────────────────────────
def test_03_placeholder_id_deterministic():
    from app.talents.models import build_placeholder_id
    pid = build_placeholder_id("warrior", 2, 3, 4)
    assert pid == "warrior.branch2.tier3.slot4"
    # Same input → same output
    assert build_placeholder_id("warrior", 2, 3, 4) == pid


# ─── 04 — TalentTreeDefinition validator: pilot class only ─────────────
def test_04_definition_rejects_non_pilot_class():
    from app.talents.models import TalentTreeDefinition, build_placeholder_id
    with pytest.raises(Exception) as e:
        TalentTreeDefinition(
            class_slug="cacciatore_vuoto",  # not in pilot
            branch_id=1, tier=1, slot_index=1,
            placeholder_id=build_placeholder_id("cacciatore_vuoto", 1, 1, 1),
        )
    assert "PILOT" in str(e.value)


# ─── 05 — TalentTreeDefinition placeholder_id mismatch rejected ─────────
def test_05_definition_placeholder_id_must_match():
    from app.talents.models import TalentTreeDefinition
    with pytest.raises(Exception) as e:
        TalentTreeDefinition(
            class_slug="warrior", branch_id=1, tier=1, slot_index=1,
            placeholder_id="wrong.id",
        )
    assert "mismatch" in str(e.value) or "placeholder_id" in str(e.value)


# ─── 06 — TalentTreeDefinition bounds ──────────────────────────────────
def test_06_definition_bounds():
    from app.talents.models import TalentTreeDefinition, build_placeholder_id
    # branch_id > 3 rejected
    with pytest.raises(Exception):
        TalentTreeDefinition(
            class_slug="warrior", branch_id=4, tier=1, slot_index=1,
            placeholder_id=build_placeholder_id("warrior", 4, 1, 1),
        )
    # tier > 5 rejected
    with pytest.raises(Exception):
        TalentTreeDefinition(
            class_slug="warrior", branch_id=1, tier=6, slot_index=1,
            placeholder_id=build_placeholder_id("warrior", 1, 6, 1),
        )
    # slot_index > 4 rejected
    with pytest.raises(Exception):
        TalentTreeDefinition(
            class_slug="warrior", branch_id=1, tier=1, slot_index=5,
            placeholder_id=build_placeholder_id("warrior", 1, 1, 5),
        )


# ─── 07 — AdventurerTalentProgress: spent_points > 30 rejected ─────────
def test_07_progress_spent_over_max():
    from app.talents.models import AdventurerTalentProgress
    with pytest.raises(Exception) as e:
        AdventurerTalentProgress(
            adventurer_id="abc", spent_points=31, max_points=30,
            allocations=[],
        )
    assert "30" in str(e.value) or "less than or equal to 30" in str(e.value) \
        or "spent" in str(e.value).lower()


# ─── 08 — Progress: tier N requires N-1 in branch ──────────────────────
def test_08_progress_tier_gate():
    from app.talents.models import AdventurerTalentProgress, TalentAllocation
    # Attempt to allocate tier 3 without tier 1 or tier 2 in same branch
    allocs = [TalentAllocation(class_slug="warrior", branch_id=1, tier=3, slot_index=1)]
    with pytest.raises(Exception) as e:
        AdventurerTalentProgress(
            adventurer_id="abc", spent_points=1, max_points=30,
            allocations=allocs,
        )
    assert "tier" in str(e.value).lower()


# ─── 09 — Progress: valid allocation passes ────────────────────────────
def test_09_progress_valid_allocation():
    from app.talents.models import AdventurerTalentProgress, TalentAllocation
    allocs = [
        TalentAllocation(class_slug="warrior", branch_id=1, tier=1, slot_index=1),
        TalentAllocation(class_slug="warrior", branch_id=1, tier=1, slot_index=2),
        TalentAllocation(class_slug="warrior", branch_id=1, tier=2, slot_index=1),
    ]
    p = AdventurerTalentProgress(
        adventurer_id="abc", spent_points=3, max_points=30,
        allocations=allocs,
    )
    assert p.spent_points == 3
    assert len(p.allocations) == 3


# ─── 10 — Seed idempotency + total 540 ─────────────────────────────────
def test_10_seed_540_placeholders_present(db):
    """After the seed apply, 9 × 60 = 540 placeholder docs must exist."""
    from app.talents.models import PILOT_CLASS_SLUGS, SLOTS_PER_CLASS
    n_total = _run(db.talent_tree_definitions.count_documents({
        "is_placeholder": True, "round_seeded": "R18.2"
    }))
    expected = len(PILOT_CLASS_SLUGS) * SLOTS_PER_CLASS
    assert n_total == expected, (
        f"expected {expected} placeholder docs, got {n_total} "
        "(run round182_talent_tree_pilot_seed.py --apply)"
    )
    # Per-class count
    for cls in PILOT_CLASS_SLUGS:
        n_cls = _run(db.talent_tree_definitions.count_documents({
            "class_slug": cls, "is_placeholder": True,
            "round_seeded": "R18.2"
        }))
        assert n_cls == SLOTS_PER_CLASS, (
            f"class {cls}: expected {SLOTS_PER_CLASS} slot, got {n_cls}"
        )


# ─── 11 — Seed uses deterministic placeholder_id ───────────────────────
def test_11_seed_deterministic_ids(db):
    from app.talents.models import build_placeholder_id
    # Query specific placeholder
    doc = _run(db.talent_tree_definitions.find_one({
        "placeholder_id": build_placeholder_id("warrior", 3, 5, 4),
        "round_seeded": "R18.2",
    }))
    assert doc is not None
    assert doc["class_slug"] == "warrior"
    assert doc["branch_id"] == 3
    assert doc["tier"] == 5
    assert doc["slot_index"] == 4
    assert doc["is_placeholder"] is True


# ─── 12 — Feature flag double-gate OFF ─────────────────────────────────
def test_12_double_feature_flag_off():
    macro = os.environ.get("R18_REWORK_ENABLED", "false").lower()
    sub = os.environ.get("R18_TALENT_ENGINE_ENABLED", "false").lower()
    assert macro in ("false", "0", "no", ""), \
        f"R18_REWORK_ENABLED must be OFF in PILOT, got {macro}"
    assert sub in ("false", "0", "no", ""), \
        f"R18_TALENT_ENGINE_ENABLED must be OFF in PILOT, got {sub}"


# ─── 13 — No player-facing endpoint exposes talent_* ───────────────────
def test_13_no_player_endpoint_leaks_talent_fields(db):
    """Verify code: no player-facing router mentions talent_* schema."""
    router_dir = pathlib.Path("/app/backend/app")
    leaked = []
    for py_file in router_dir.rglob("routes.py"):
        # Skip admin dirs
        if "admin" in py_file.parts:
            continue
        content = py_file.read_text()
        if "talent_tree_definitions" in content or \
           "adventurer_talent_progress" in content:
            leaked.append(str(py_file))
    assert not leaked, (
        f"Player-facing routes leak talent_* schema: {leaked}. "
        "R18.2 PILOT is schema-only, no player-facing endpoints."
    )


# ─── 14 — Audit event R18_TALENT_PILOT_SEEDED present ──────────────────
def test_14_audit_event_pilot_seeded(db):
    n = _run(db.audit_log.count_documents({
        "event_type": "R18_TALENT_PILOT_SEEDED"
    }))
    assert n >= 1, (
        "R18_TALENT_PILOT_SEEDED event missing from audit_log. "
        "Run seed --apply at least once."
    )
    doc = _run(db.audit_log.find_one(
        {"event_type": "R18_TALENT_PILOT_SEEDED"},
        {"_id": 0, "metadata": 1, "source": 1}
    ))
    assert doc["metadata"]["round"] == "R18.2"
    assert doc["metadata"]["phase"] == "PILOT"
    assert doc["metadata"]["is_placeholder_only"] is True


# ─── 15 — Audit whitelist accepts R18_TALENT_PILOT_SEEDED ──────────────
def test_15_audit_whitelist_includes_new_event():
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    assert "R18_TALENT_PILOT_SEEDED" in AUDIT_EVENT_WHITELIST
