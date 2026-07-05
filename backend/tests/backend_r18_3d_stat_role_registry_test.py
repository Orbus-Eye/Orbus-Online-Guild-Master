"""R18.3d — Phase B4 · Stat/Role Registry Test Suite (Q10.b correction).

Coverage:
    - 27 canonical classes locked (Q10.b)
    - 16 legacy live documented separately (not counted as canonical)
    - excluded_manifest_entries present (empty by design)
    - dry-run modifies ONLY canonical ∩ live (not legacy)
    - 5 SAFE fields only
    - guard hard-stop on BLOCKED fields
    - legacy live hard-stop on plan
    - Bard drift documented + backlog entry
    - Paladin faith accepted
    - Registry module unwired

Zero DB writes.
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
    load_registry,
)

REGISTRY_PATH = Path("/app/memory/r18_3d_stat_role_mapping_registry.json")
APPLY_SCRIPT = "app.scripts.round18_3d_apply_metadata"
BACKEND_ROOT = "/app/backend"
BACKLOG_PATH = Path("/app/memory/backlog.md")

_ENV = dotenv_values("/app/backend/.env")
PROD_MONGO_URL = _ENV["MONGO_URL"]
PROD_DB_NAME = _ENV["DB_NAME"]

CANONICAL_27_SLUGS_LOCKED = {
    "alchimista", "artificiere", "astrologo", "bardo", "burattinaio",
    "cacciatore_del_sangue", "cacciatore_del_vuoto", "cacciatore_di_mostri",
    "cartografo", "cavaliere_della_morte", "cavaliere_di_draghi", "cronista",
    "druido", "fabbro_arcano", "giocatore_d_azzardo", "guerriero", "ladro",
    "mago", "mercante", "monaco", "negromante", "paladino", "parassita",
    "pittore", "runista", "sciamano", "sognatore",
}


# ── 1. Mapping 6→5 locked ───────────────────────────────────────────
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
    mapping = reg["stat_mapping_6_to_5"]
    assert mapping[design_it]["live"] == expected_live


# ── 2. Registry JSON parses + meta structure ────────────────────────
def test_2_registry_parses_meta_present():
    reg = load_registry()
    meta = reg.get("meta")
    assert meta is not None, "top-level 'meta' missing"
    assert meta["canonical_classes"] == 27
    assert meta["registry_version"] == "R18.3d.v2"
    assert meta["source_round"] == "R18.3d Phase B (Q10.b correction applied)"


# ── 3. 27 canonical slugs LOCKED ────────────────────────────────────
def test_3_canonical_27_locked():
    reg = load_registry()
    canonical = reg["canonical_classes"]
    assert len(canonical) == 27, (
        f"expected 27 canonical entries, got {len(canonical)}"
    )
    slugs = {e["slug"] for e in canonical}
    assert slugs == CANONICAL_27_SLUGS_LOCKED, (
        f"canonical slug set mismatch. "
        f"extra: {slugs - CANONICAL_27_SLUGS_LOCKED}, "
        f"missing: {CANONICAL_27_SLUGS_LOCKED - slugs}"
    )
    # No duplicates
    assert len(slugs) == 27


# ── 4. Legacy live documented separately ────────────────────────────
def test_4_legacy_live_documented_separately():
    reg = load_registry()
    legacy = reg["legacy_live_classes"]
    assert isinstance(legacy, list)
    # Legacy count must match meta
    meta = reg["meta"]
    assert len(legacy) == meta["legacy_live_classes_count"]
    # Legacy slugs must NOT overlap with canonical
    legacy_slugs = {e["live_slug"] for e in legacy}
    canonical_slugs = {e["slug"] for e in reg["canonical_classes"]}
    overlap = legacy_slugs & canonical_slugs
    assert not overlap, (
        f"legacy_live overlap with canonical: {overlap}"
    )
    # Every legacy entry declares canonical_target=false
    for entry in legacy:
        assert entry.get("canonical_target") is False
        assert entry.get("legacy_live") is True


# ── 5. Legacy live matches live DB catalog ──────────────────────────
def test_5_legacy_live_matches_db():
    async def _run():
        client = AsyncIOMotorClient(PROD_MONGO_URL)
        db = client[PROD_DB_NAME]
        db_slugs = {c["slug"] async for c in db.adventurer_classes.find({}, {"slug": 1})}
        client.close()
        return db_slugs

    db_slugs = asyncio.run(_run())
    reg = load_registry()
    legacy_slugs = {e["live_slug"] for e in reg["legacy_live_classes"]}
    canonical_slugs_in_db = {
        e["slug"] for e in reg["canonical_classes"]
        if e.get("exists_in_live_db")
    }
    # Every DB slug must be either in legacy or in canonical-with-exists_in_live_db
    documented_slugs = legacy_slugs | canonical_slugs_in_db
    missing = db_slugs - documented_slugs
    extra_legacy = legacy_slugs - db_slugs
    assert not missing, f"DB slugs not documented in registry: {missing}"
    assert not extra_legacy, (
        f"legacy_live entries not in DB: {extra_legacy}"
    )


# ── 6. Excluded manifest entries present (empty by design) ──────────
def test_6_excluded_manifest_entries_present():
    reg = load_registry()
    assert "excluded_manifest_entries" in reg
    excluded = reg["excluded_manifest_entries"]
    assert isinstance(excluded, list)
    assert len(excluded) == reg["meta"]["excluded_manifest_entries_count"]


# ── 7. 5 SAFE fields exclusive scope ────────────────────────────────
def test_7_safe_fields_scope():
    reg = load_registry()
    scope = reg["safe_metadata_fields_apply_scope"]
    fields = set(scope["fields_to_apply_via_set"])
    assert fields == set(SAFE_METADATA_FIELDS)
    blocked = set(scope["blocked_fields_never_touch"])
    for bf in BLOCKED_RUNTIME_FIELDS:
        assert bf in blocked


# ── 8. Eligible apply intersection = canonical ∩ live ────────────────
def test_8_eligible_apply_is_canonical_intersect_live():
    reg = load_registry()
    scope = reg["safe_metadata_fields_apply_scope"]
    eligible = set(scope["eligible_apply_slugs"])
    canonical_in_live = {
        e["slug"] for e in reg["canonical_classes"]
        if e.get("exists_in_live_db")
    }
    assert eligible == canonical_in_live, (
        f"eligible_apply_slugs mismatch. "
        f"eligible={eligible} vs canonical∩live={canonical_in_live}"
    )
    # Meta count consistency
    assert reg["meta"]["canonical_live_count"] == len(canonical_in_live)


# ── 9. Registry module unwired ─────────────────────────────────────
def test_9_registry_module_unwired():
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-l",
         "from app.core.stat_role_registry",
         "/app/backend/app/"],
        capture_output=True, text=True,
    )
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    disallowed = [
        ln for ln in lines
        if not ln.endswith("stat_role_registry.py")
        and "/scripts/" not in ln
        and "/tests/" not in ln
    ]
    assert not disallowed, (
        f"stat_role_registry imported by runtime paths: {disallowed}"
    )


# ── 10. No player-facing leak in adventurers service ────────────────
def test_10_no_player_facing_leak():
    services_src = Path("/app/backend/app/adventurers/services.py").read_text()
    for f in SAFE_METADATA_FIELDS:
        assert f"'{f}'" not in services_src and f'"{f}"' not in services_src, (
            f"SAFE metadata field {f} leaked into adventurers/services.py"
        )


# ── 11. Bard drift documented + backlog ────────────────────────────
def test_11_bard_drift_documented():
    reg = load_registry()
    bard_legacy = next(
        (e for e in reg["legacy_live_classes"] if e["live_slug"] == "bard"),
        None,
    )
    assert bard_legacy is not None
    assert bard_legacy.get("drift_flag") == "bard_role_support_not_in_valid_roles"
    assert bard_legacy.get("needs_PM_review") is True
    # canonical entry 'bardo' should reference the alias
    bardo = next(
        (e for e in reg["canonical_classes"] if e["slug"] == "bardo"),
        None,
    )
    assert bardo is not None
    assert bardo.get("alias_from_live_slug") == "bard"
    # Backlog entry
    backlog = BACKLOG_PATH.read_text()
    assert "R18.3d.followup — Bard Role Drift Resolution" in backlog


# ── 12. Paladin faith accepted (canonical 'paladino') ──────────────
def test_12_paladin_faith_accepted():
    reg = load_registry()
    paladino = next(
        (e for e in reg["canonical_classes"] if e["slug"] == "paladino"),
        None,
    )
    assert paladino is not None
    assert paladino["mapped_primary_stat_live"] == "faith"
    assert paladino["design_primary_stat_it"] == "Carisma"
    assert paladino["role_display_it"] == "Healer/Tank"
    assert "Holy" in paladino["class_role_tags"]
    assert paladino["alias_from_live_slug"] == "paladin"


# ── 13. Guard hard-stop rejects BLOCKED fields ──────────────────────
@pytest.mark.parametrize("blocked_field", [
    "primary_stat", "role", "base_strength", "is_playable",
])
def test_13_guard_hard_stop_blocked_field(blocked_field):
    from app.scripts.round18_3d_apply_metadata import (
        GuardHardStop,
        _guard_payload,
    )
    bad_payload = {"role_display_it": "X", blocked_field: "malicious"}
    with pytest.raises(GuardHardStop) as exc:
        _guard_payload(bad_payload)
    assert blocked_field in str(exc.value)


# ── 14. Legacy live hard-stop: plan never contains legacy slug ─────
def test_14_legacy_live_hard_stop_in_plan():
    from app.scripts.round18_3d_apply_metadata import _plan_apply
    reg = load_registry()
    plan = _plan_apply(reg)
    plan_slugs = {p["slug"] for p in plan}
    legacy_hardstop = set(
        reg["safe_metadata_fields_apply_scope"]["legacy_live_slugs_hard_stop"]
    )
    leaks = plan_slugs & legacy_hardstop
    assert not leaks, f"legacy slugs leaked into plan: {leaks}"
    # And plan slugs must all be canonical
    canonical_slugs = {e["slug"] for e in reg["canonical_classes"]}
    non_canonical = plan_slugs - canonical_slugs
    assert not non_canonical, f"non-canonical slugs in plan: {non_canonical}"


# ── 15. Dry-run exits 0 and modifies only canonical ∩ live ──────────
def test_15_dry_run_only_canonical_intersect_live():
    res = subprocess.run(
        ["python", "-m", APPLY_SCRIPT, "--dry-run"],
        capture_output=True, text=True, cwd=BACKEND_ROOT,
    )
    assert res.returncode == 0, (
        f"dry-run exit={res.returncode}\nstdout={res.stdout[-800:]}\n"
        f"stderr={res.stderr[-400:]}"
    )
    assert "DRY_RUN complete" in res.stdout
    reg = load_registry()
    expected_count = reg["meta"]["canonical_live_count"]
    assert f"plan: {expected_count} canonical class(es) eligible" in res.stdout, (
        f"expected plan={expected_count}; stdout tail={res.stdout[-500:]}"
    )
    # Verify no legacy slug appears in dry-run output
    for slug in reg["safe_metadata_fields_apply_scope"]["legacy_live_slugs_hard_stop"]:
        assert f" · {slug}:" not in res.stdout, (
            f"legacy slug {slug} appeared in dry-run plan"
        )


# ── 16. --apply without ack fails with exit 30 ─────────────────────
def test_16_apply_without_ack_fails_30():
    res = subprocess.run(
        ["python", "-m", APPLY_SCRIPT, "--apply"],
        capture_output=True, text=True, cwd=BACKEND_ROOT,
    )
    assert res.returncode == 30, (
        f"expected exit 30, got {res.returncode}"
    )


# ── 17. Registry SHA256 computable ─────────────────────────────────
def test_17_registry_sha256_computable():
    sha = compute_registry_sha256()
    assert len(sha) == 64
    assert sha == compute_registry_sha256()


# ── 18. Priority critical slugs (5) present in canonical ───────────
def test_18_priority_critical_slugs():
    reg = load_registry()
    critical = set(reg.get("priority_critical_slugs") or [])
    expected = {"paladino", "guerriero", "ladro",
                "cacciatore_di_mostri", "cacciatore_del_vuoto"}
    assert critical == expected
    # And they must be present in canonical
    canonical_slugs = {e["slug"] for e in reg["canonical_classes"]}
    assert critical.issubset(canonical_slugs)


# ── 19. Meta counts internally consistent ──────────────────────────
def test_19_meta_counts_internally_consistent():
    reg = load_registry()
    m = reg["meta"]
    assert m["canonical_classes"] == len(reg["canonical_classes"])
    assert m["legacy_live_classes_count"] == len(reg["legacy_live_classes"])
    assert m["excluded_manifest_entries_count"] == len(reg["excluded_manifest_entries"])
    canonical_in_live = sum(
        1 for e in reg["canonical_classes"] if e.get("exists_in_live_db")
    )
    assert m["canonical_live_count"] == canonical_in_live
    assert m["design_only_classes_count"] == m["canonical_classes"] - m["canonical_live_count"]


# ── 20. No BLOCKED field appears anywhere in canonical entries ─────
def test_20_no_blocked_fields_in_canonical_entries():
    reg = load_registry()
    forbidden_top_level = {
        "primary_stat", "secondary_stats", "role",
        "is_playable", "is_active", "is_canonical",
        "base_strength", "base_agility", "base_intellect",
        "base_endurance", "base_faith",
    }
    for entry in reg["canonical_classes"]:
        overlap = set(entry.keys()) & forbidden_top_level
        assert not overlap, (
            f"canonical entry {entry.get('slug')} contains BLOCKED top-level keys: {overlap}"
        )
