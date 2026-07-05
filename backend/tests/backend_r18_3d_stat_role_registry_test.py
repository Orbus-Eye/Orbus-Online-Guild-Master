"""R18.3d — Phase B4 · Stat/Role Registry Test Suite.

Tests both static invariants (registry parsing, mapping locked, unwired
module) and script-guard invariants (BLOCKED field hard-stop, SAFE-only
apply scope). NO DB writes performed by any test in this suite (registry
apply is dry-run only).

Author: e1_dev (R18.3d Phase B4)
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import pytest
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.stat_role_registry import (
    BLOCKED_RUNTIME_FIELDS,
    DESIGN_STAT_MAPPING_6_TO_5,
    LIVE_ROLES_ATOMIC,
    LIVE_STATS_ATOMIC,
    SAFE_METADATA_FIELDS,
    compute_registry_sha256,
    get_stat_role_mapping,
    load_registry,
    validate_registry_or_raise,
)

REGISTRY_PATH = Path("/app/memory/r18_3d_stat_role_mapping_registry.json")
APPLY_SCRIPT = "app.scripts.round18_3d_apply_metadata"
BACKEND_ROOT = "/app/backend"
BACKLOG_PATH = Path("/app/memory/backlog.md")

_ENV = dotenv_values("/app/backend/.env")
PROD_MONGO_URL = _ENV["MONGO_URL"]
PROD_DB_NAME = _ENV["DB_NAME"]


# ── 1. Mapping 6→5 locked (parametrized) ────────────────────────────
@pytest.mark.parametrize("design_it,expected_live", [
    ("Forza", "strength"),
    ("Destrezza", "agility"),
    ("Costituzione", "endurance"),
    ("Intelligenza", "intellect"),
    ("Saggezza", "intellect"),
    ("Carisma", "faith"),
])
def test_1_mapping_6_to_5_locked(design_it, expected_live):
    assert DESIGN_STAT_MAPPING_6_TO_5[design_it] == expected_live
    reg = load_registry()
    mapping = reg["stat_system"]["design_stat_mapping_6_to_5_LOCKED"]
    assert mapping[design_it]["live"] == expected_live


# ── 2. Registry JSON parses ─────────────────────────────────────────
def test_2_registry_parses():
    reg = load_registry()
    assert reg["registry_version"] == "R18.3d.v1"
    assert isinstance(reg["live_classes_18"], list)
    assert isinstance(reg["canonical_design_only_16"], list)
    validate_registry_or_raise()  # explicit validation


# ── 3. 18 live classes covered vs DB ────────────────────────────────
def test_3_live_classes_18_match_db():
    async def _run():
        client = AsyncIOMotorClient(PROD_MONGO_URL)
        db = client[PROD_DB_NAME]
        db_slugs = {c["slug"] async for c in db.adventurer_classes.find({}, {"slug": 1})}
        client.close()
        return db_slugs

    db_slugs = asyncio.run(_run())
    reg = load_registry()
    registry_slugs = {e["class_slug"] for e in reg["live_classes_18"]}
    assert len(reg["live_classes_18"]) == 18, (
        f"expected 18 live entries, got {len(reg['live_classes_18'])}"
    )
    missing = db_slugs - registry_slugs
    extra = registry_slugs - db_slugs
    assert not missing, f"live DB slugs missing from registry: {missing}"
    assert not extra, f"registry has slugs not in DB: {extra}"


# ── 4. 16 canonical design-only covered ─────────────────────────────
def test_4_canonical_design_only_16():
    reg = load_registry()
    design_only = reg["canonical_design_only_16"]
    assert len(design_only) == 16, (
        f"expected 16 design-only, got {len(design_only)}"
    )
    for entry in design_only:
        assert entry.get("design_only") is True
        assert entry.get("in_live_db") is False
        assert entry.get("canonical_slug_candidate")
        assert entry.get("canonical_name_it")


# ── 5. Apply script uses only SAFE fields ───────────────────────────
def test_5_apply_script_scope_safe_only():
    reg = load_registry()
    scope = reg["safe_metadata_fields_apply_scope"]
    fields = set(scope["fields_to_apply_via_set"])
    assert fields == set(SAFE_METADATA_FIELDS), (
        f"scope fields mismatch: {fields} vs {SAFE_METADATA_FIELDS}"
    )
    blocked = set(scope["blocked_fields_never_touch"])
    for bf in BLOCKED_RUNTIME_FIELDS:
        assert bf in blocked, f"blocked list missing {bf}"


# ── 6. Zero runtime wiring of stat_role_registry module ─────────────
def test_6_registry_module_unwired():
    """Grep-based test: verify no runtime module (excluding scripts, tests,
    and stat_role_registry.py itself) imports from app.core.stat_role_registry.
    """
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-l",
         "from app.core.stat_role_registry",
         "/app/backend/app/"],
        capture_output=True, text=True,
    )
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    # exclude the module itself and scripts/tests
    disallowed = [
        ln for ln in lines
        if not ln.endswith("stat_role_registry.py")
        and "/scripts/" not in ln
        and "/tests/" not in ln
    ]
    assert not disallowed, (
        f"stat_role_registry imported by runtime code paths: {disallowed}"
    )


# ── 7. Zero player-facing leak (no new metadata fields exposed) ─────
def test_7_no_player_facing_leak():
    """Verify that adventurers/services.py list-adventurers endpoint does NOT
    emit any of the 5 SAFE metadata fields (they belong to adventurer_classes,
    not to adventurer docs — but a defensive check on public API surface).
    """
    services_src = Path("/app/backend/app/adventurers/services.py").read_text()
    for f in SAFE_METADATA_FIELDS:
        assert f"'{f}'" not in services_src and f'"{f}"' not in services_src, (
            f"SAFE metadata field {f} leaked into adventurers/services.py"
        )


# ── 8. Bard drift documented + backlog entry present ────────────────
def test_8_bard_drift_documented():
    reg = load_registry()
    bard = next(
        (e for e in reg["live_classes_18"] if e["class_slug"] == "bard"),
        None,
    )
    assert bard is not None, "bard entry missing from registry"
    assert bard.get("drift_flag") == "bard_role_support_not_in_valid_roles"
    assert bard.get("needs_PM_review") is True
    # backlog entry
    backlog_content = BACKLOG_PATH.read_text()
    assert "R18.3d.followup — Bard Role Drift Resolution" in backlog_content, (
        "backlog missing R18.3d.followup Bard Role Drift entry"
    )


# ── 9. Paladin faith accepted ──────────────────────────────────────
def test_9_paladin_faith_accepted():
    reg = load_registry()
    pal = next(
        (e for e in reg["live_classes_18"] if e["class_slug"] == "paladin"),
        None,
    )
    assert pal is not None
    assert pal["mapped_primary_stat_live"] == "faith"
    assert pal["design_primary_stat_it"] == "Carisma"
    assert pal["role_display_it"] == "Healer/Tank"
    assert "Holy" in pal["class_role_tags"]
    assert "Support" in pal["class_role_tags"]


# ── 10. Guard hard-stop rejects BLOCKED field ──────────────────────
@pytest.mark.parametrize("blocked_field", [
    "primary_stat", "role", "base_strength", "is_playable",
])
def test_10_guard_hard_stop_blocked_field(blocked_field):
    from app.scripts.round18_3d_apply_metadata import (
        GuardHardStop,
        _guard_payload,
    )
    bad_payload = {"role_display_it": "X", blocked_field: "malicious"}
    with pytest.raises(GuardHardStop) as exc:
        _guard_payload(bad_payload)
    assert blocked_field in str(exc.value)


# ── 11. Apply script dry-run exits 0 ────────────────────────────────
def test_11_apply_script_dry_run_exit_0():
    res = subprocess.run(
        ["python", "-m", APPLY_SCRIPT, "--dry-run"],
        capture_output=True, text=True, cwd=BACKEND_ROOT,
    )
    assert res.returncode == 0, (
        f"dry-run exit={res.returncode}\nstdout={res.stdout[-800:]}"
        f"\nstderr={res.stderr[-400:]}"
    )
    assert "DRY_RUN complete" in res.stdout
    assert "16 eligible" in res.stdout or "plan: 16" in res.stdout


# ── 12. Apply script --apply without ack fails 30 ──────────────────
def test_12_apply_without_ack_fails_30():
    res = subprocess.run(
        ["python", "-m", APPLY_SCRIPT, "--apply"],
        capture_output=True, text=True, cwd=BACKEND_ROOT,
    )
    assert res.returncode == 30, (
        f"expected exit 30, got {res.returncode}\n{res.stdout[-400:]}"
    )


# ── 13. Registry SHA256 computable ─────────────────────────────────
def test_13_registry_sha256_computable():
    sha = compute_registry_sha256()
    assert len(sha) == 64
    # verify consistency
    sha2 = compute_registry_sha256()
    assert sha == sha2


# ── 14. get_stat_role_mapping helper unwired ───────────────────────
def test_14_get_stat_role_mapping_helper():
    entry = get_stat_role_mapping("warrior")
    assert entry is not None
    assert entry["mapped_primary_stat_live"] == "strength"
    # unknown slug returns None
    assert get_stat_role_mapping("this_does_not_exist_slug") is None


# ── 15. Priority critical slugs present ────────────────────────────
def test_15_priority_critical_slugs():
    reg = load_registry()
    critical = set(reg.get("priority_critical_slugs") or [])
    expected = {"paladin", "warrior", "rogue",
                "cacciatore_di_mostri", "cacciatore_del_vuoto"}
    assert critical == expected, f"critical slugs mismatch: {critical}"
