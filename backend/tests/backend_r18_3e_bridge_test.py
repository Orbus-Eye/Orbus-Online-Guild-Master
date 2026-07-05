"""ROUND 18.3e Phase B — Bridge Registry Test Suite (15 punti minimo).

═══════════════════════════════════════════════════════════════════════
🔒 CLOSED & SEALED — R18.3e Phase B — 2026-07-05T20:15:00Z UTC
🔒 SEAL AUTHORITY: PM Orchestrator
🔒 SEAL NOTE: Contract lock documentale del test suite R18.3e Phase B.
🔒 15 test PASS (breakdown: cross-ref canonical R18.3d/3e, bridge_status
🔒 registry, hard-stop guard, APPLY_ENABLED=False lock, sealed integrity
🔒 16 file, canonical_it_set_27_locked coherence). Test suite READ-ONLY:
🔒 nessuna scrittura DB, nessun runtime wiring. Enforcement rimane
🔒 documentale (banner header). Byte-identical enforcement: verify
🔒 manuale con sha256sum + aggregate seal registry R18.3e.
═══════════════════════════════════════════════════════════════════════

Test suite dedicata al registry documentale R18.3e (Legacy EN ↔ Canonical IT).
Tutti i test sono READ-ONLY: nessuna scrittura DB, nessun runtime wiring.

Wired to runtime: NO. Test suite pura (non caricata dal boot dell'app).
"""
from __future__ import annotations

import hashlib
import importlib
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

# ─── Paths ───────────────────────────────────────────────────────────────
REPO_ROOT = Path("/app")
REGISTRY_JSON = REPO_ROOT / "memory" / "r18_3e_bridge_registry.json"
REGISTRY_MD = REPO_ROOT / "memory" / "r18_3e_bridge_registry.md"
DECISION_LOCK_JSON = REPO_ROOT / "memory" / "r18_3e_phase_b_pm_decisions.json"
DECISION_LOCK_MD = REPO_ROOT / "memory" / "r18_3e_phase_b_pm_decisions.md"
APPLY_SCRIPT = REPO_ROOT / "backend" / "app" / "scripts" / "round18_3e_apply_bridge.py"
R18_3D_REGISTRY_JSON = REPO_ROOT / "memory" / "r18_3d_stat_role_mapping_registry.json"

BLOCKED_FIELDS_13 = {
    "class_slug", "display_name_it", "primary_stat", "secondary_stats", "role",
    "base_strength", "base_agility", "base_intellect", "base_endurance",
    "base_faith", "is_playable", "is_active", "is_canonical",
}

VALID_BRIDGE_STATUS = {
    "mapped_canonical", "mapped_alias", "deprecated_alias",
    "technical_placeholder", "test_artifact", "canonical_native",
    "ambiguous_pending_pm",
}


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def decision_lock() -> dict:
    return json.loads(DECISION_LOCK_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def r18_3d_canonical_27() -> set[str]:
    d = json.loads(R18_3D_REGISTRY_JSON.read_text(encoding="utf-8"))
    return {c["slug"] for c in d["canonical_classes"]}


# ─── Test 1 — Decision lock parsabile con 14 risposte ────────────────────
def test_01_decision_lock_parsable_14_answers(decision_lock):
    answers = decision_lock.get("answers_verbatim", {})
    q_ids = set(answers.keys())
    expected = {f"Q{i}" for i in range(1, 15)}
    assert q_ids == expected, f"Expected Q1..Q14, got {sorted(q_ids)}"
    # Every answer has 'answer' + 'detail'
    for q, a in answers.items():
        assert "answer" in a and "detail" in a, f"{q} missing answer/detail"


# ─── Test 2 — Registry JSON schema valid + parsabile ─────────────────────
def test_02_registry_schema_valid(registry):
    required_top = {
        "meta", "canonical_it_set_27_locked", "bridge_status_enum",
        "safe_fields_apply_scope", "bridge_entries", "reverse_map_canonical_to_legacy",
        "canonical_not_referenced_by_bridge", "backlog_entries_registered_by_this_registry",
    }
    assert required_top.issubset(set(registry.keys())), (
        f"Missing top-level keys: {required_top - set(registry.keys())}"
    )
    meta = registry["meta"]
    assert meta["round"] == "R18.3e"
    assert meta["phase"] == "B"
    assert meta["stage"] == "B2_real_apply_completed_and_sealed"
    assert meta["seal_status"] == "CLOSED_AND_SEALED_R18_3E_PHASE_B"
    assert meta["runtime_wired"] is False
    assert meta["governance"]["audit_event_emitted"] is False
    assert meta["governance"]["player_facing_change"] is False


# ─── Test 3 — 16 legacy coperti con 5 SAFE field ─────────────────────────
def test_03_16_legacy_coverage_with_5_safe_fields(registry):
    entries = registry["bridge_entries"]
    legacy_expected = {
        "warrior", "rogue", "mage", "priest", "ranger", "monk", "paladin",
        "druid", "alchemist", "bard", "warlock", "necromancer", "assassin",
        "berserker", "recruit_unassigned", "test-class-5e0064",
    }
    slugs_in_registry = {e["slug"] for e in entries}
    assert legacy_expected.issubset(slugs_in_registry), (
        f"Missing legacy slugs: {legacy_expected - slugs_in_registry}"
    )
    safe_keys = {"canonical_slug", "alias_target", "bridge_status", "bridge_source_round"}
    for e in entries:
        assert safe_keys.issubset(set(e.keys())), (
            f"Entry {e['slug']} missing SAFE fields: {safe_keys - set(e.keys())}"
        )


# ─── Test 4 — Mapping verbatim vs decisioni PM ───────────────────────────
def test_04_mapping_matches_pm_decisions(registry, decision_lock):
    entries_by_slug = {e["slug"]: e for e in registry["bridge_entries"]}
    for pm_row in decision_lock["mapping_official_locked"]:
        slug = pm_row["legacy_slug"]
        e = entries_by_slug.get(slug)
        assert e is not None, f"Missing entry for {slug}"
        assert e["canonical_slug"] == pm_row["canonical_slug"], (
            f"{slug}.canonical_slug drift: registry={e['canonical_slug']!r}, "
            f"pm={pm_row['canonical_slug']!r}"
        )
        assert e["alias_target"] == pm_row["alias_target"], (
            f"{slug}.alias_target drift: registry={e['alias_target']!r}, "
            f"pm={pm_row['alias_target']!r}"
        )
        assert e["bridge_status"] == pm_row["bridge_status"], (
            f"{slug}.bridge_status drift: registry={e['bridge_status']!r}, "
            f"pm={pm_row['bridge_status']!r}"
        )


# ─── Test 5 — canonical_slug valid = uno dei 27 canonical o null ─────────
def test_05_canonical_slug_ref_in_27_or_null(registry, r18_3d_canonical_27):
    canon_registry = set(registry["canonical_it_set_27_locked"])
    assert canon_registry == r18_3d_canonical_27, (
        "R18.3e canonical set drift vs R18.3d locked canonical set"
    )
    for e in registry["bridge_entries"]:
        cs = e["canonical_slug"]
        assert cs is None or cs in canon_registry, (
            f"{e['slug']}.canonical_slug={cs!r} NOT in canonical 27"
        )
        at = e.get("alias_target")
        assert at is None or at in canon_registry, (
            f"{e['slug']}.alias_target={at!r} NOT in canonical 27 (v1 constraint)"
        )


# ─── Test 6 — bridge_status = uno degli enum ammessi ─────────────────────
def test_06_bridge_status_enum(registry):
    enum_registry = set(registry["bridge_status_enum"])
    assert enum_registry == VALID_BRIDGE_STATUS, (
        f"Enum drift: registry={enum_registry}, expected={VALID_BRIDGE_STATUS}"
    )
    for e in registry["bridge_entries"]:
        assert e["bridge_status"] in VALID_BRIDGE_STATUS, (
            f"{e['slug']}.bridge_status={e['bridge_status']!r} not in enum"
        )


# ─── Test 7 — Zero apply reale (script sempre in dry-run) ────────────────
def test_07_script_apply_enabled_locked_false():
    text = APPLY_SCRIPT.read_text(encoding="utf-8")
    assert "APPLY_ENABLED: bool = False" in text, (
        "APPLY_ENABLED must be locked to False in R18.3e Phase B"
    )
    # Import the module and check the flag at module load time
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    try:
        module = importlib.import_module("app.scripts.round18_3e_apply_bridge")
        importlib.reload(module)
        assert module.APPLY_ENABLED is False


        # Dry-run must complete without SystemExit
        buf = io.StringIO()
        with redirect_stdout(buf):
            report = module.dry_run()
        assert report["mode"] == "dry_run"
        assert report["apply_enabled"] is False
        assert report["would_modify_count"] == 18
        assert report["errors_count"] == 0
        assert report["skipped_count"] == 0
        assert report["audit_event_would_emit"]["actually_emitted"] is False
        assert report["backup_snapshot_would_write"]["actually_written"] is False
    finally:
        sys.path.pop(0)


# ─── Test 8 — Guard hard-stop test parametrizzato sui 13 field BLOCKED ───
@pytest.mark.parametrize("blocked_field", sorted(BLOCKED_FIELDS_13))
def test_08_guard_hard_stop_blocked_field_param(blocked_field):
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    try:
        module = importlib.import_module("app.scripts.round18_3e_apply_bridge")
        importlib.reload(module)
        payload = {
            "canonical_slug": "guerriero",
            "alias_target": None,
            "bridge_status": "mapped_canonical",
            "bridge_source_round": module.SOURCE_ROUND_TAG,
            "bridge_applied_at": "2026-07-05T18:39:19Z",
            blocked_field: "malicious_value",
        }
        with pytest.raises(SystemExit) as excinfo:
            module._guard_payload_hard_stop(payload, slug="poisoned")
        assert "BLOCKED field" in str(excinfo.value) or "non-SAFE key" in str(excinfo.value)
    finally:
        sys.path.pop(0)


# ─── Test 9 — Script --apply senza ack → fail-fast ───────────────────────
def test_09_script_apply_without_ack_fails_fast():
    proc = subprocess.run(
        [sys.executable, "-m", "app.scripts.round18_3e_apply_bridge", "--apply"],
        cwd=str(REPO_ROOT / "backend"),
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode != 0, "Expected non-zero exit code without ack"
    # BLOCKED message must appear (APPLY_ENABLED=False takes precedence)
    err = (proc.stderr + proc.stdout).lower()
    assert "blocked" in err or "fail-fast" in err, (
        f"Expected fail-fast/blocked message, got stderr={proc.stderr!r} stdout={proc.stdout!r}"
    )


# ─── Test 10 — Zero runtime wiring del futuro loader ─────────────────────
def test_10_zero_runtime_wiring():
    """Assicura che nessun modulo runtime importi il bridge registry o lo script."""
    # Search only in runtime dirs (exclude tests, scripts, __pycache__, migrations)
    backend_app = REPO_ROOT / "backend" / "app"
    runtime_files: list[Path] = []
    for p in backend_app.rglob("*.py"):
        parts = p.parts
        if any(x in parts for x in ("__pycache__", "tests", "scripts")):
            continue
        runtime_files.append(p)
    disallowed_imports = [
        "from app.scripts.round18_3e_apply_bridge",
        "import round18_3e_apply_bridge",
        "r18_3e_bridge_registry",
    ]
    hits: list[str] = []
    for f in runtime_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for needle in disallowed_imports:
            if needle in text:
                hits.append(f"{f}: {needle!r}")
    assert not hits, f"Runtime wiring detected: {hits}"


# ─── Test 11 — Zero touch to blocked fields in registry entries ──────────
def test_11_no_blocked_fields_in_registry_entries(registry):
    """Il registry non deve MAI contenere BLOCKED fields nelle entries
    (tranne come metadati informativi, es. adventurers_live/display_name_it_live
    che NON vengono applicati)."""
    for e in registry["bridge_entries"]:
        for f in BLOCKED_FIELDS_13:
            # Applicative rule: field 'X' as-is in the entry means "would apply X".
            # We allow *_live/*_snapshot suffixed keys (informational).
            assert f not in e, (
                f"Entry {e['slug']} contains BLOCKED apply-scope field {f!r}"
            )


# ─── Test 12 — technical_placeholder / test_artifact correttamente separati
def test_12_technical_placeholder_and_test_artifact_separated(registry):
    tp = [e for e in registry["bridge_entries"] if e["bridge_status"] == "technical_placeholder"]
    ta = [e for e in registry["bridge_entries"] if e["bridge_status"] == "test_artifact"]
    tp_slugs = {e["slug"] for e in tp}
    ta_slugs = {e["slug"] for e in ta}
    assert tp_slugs == {"recruit_unassigned"}, f"technical_placeholder mismatch: {tp_slugs}"
    assert ta_slugs == {"test-class-5e0064"}, f"test_artifact mismatch: {ta_slugs}"
    # Both should have canonical_slug=None and alias_target=None
    for e in tp + ta:
        assert e["canonical_slug"] is None
        assert e["alias_target"] is None


# ─── Test 13 — Registry SHA256 self-hash computable ──────────────────────
def test_13_registry_sha256_computable():
    h_json = hashlib.sha256(REGISTRY_JSON.read_bytes()).hexdigest()
    h_md = hashlib.sha256(REGISTRY_MD.read_bytes()).hexdigest()
    h_lock_json = hashlib.sha256(DECISION_LOCK_JSON.read_bytes()).hexdigest()
    h_lock_md = hashlib.sha256(DECISION_LOCK_MD.read_bytes()).hexdigest()
    for h in (h_json, h_md, h_lock_json, h_lock_md):
        assert len(h) == 64
        int(h, 16)  # valid hex


# ─── Test 14 — R18.3d registry intatto (regression, in-process, no subprocess) ─
def test_14_r18_3d_registry_intact():
    """Regression check in-process: verifica che il registry R18.3d Phase B
    contenga esattamente 27 canonical + 16 legacy e che il meta.seal_status
    sia CLOSED_AND_SEALED_DOCUMENTAL_ONLY.

    Sostituisce il vecchio subprocess pytest (deprecato per race/deadlock).
    """
    r18_3d = json.loads(R18_3D_REGISTRY_JSON.read_text(encoding="utf-8"))
    canonical = r18_3d["canonical_classes"]
    legacy = r18_3d["legacy_live_classes"]
    meta = r18_3d["meta"]
    assert len(canonical) == 27, f"R18.3d canonical drift: {len(canonical)} != 27"
    assert len(legacy) == 16, f"R18.3d legacy drift: {len(legacy)} != 16"
    assert meta.get("canonical_classes") == 27
    assert meta.get("legacy_live_classes_count") == 16
    assert meta.get("seal_status") == "CLOSED_AND_SEALED_DOCUMENTAL_ONLY"
    # Cross-ref: R18.3e registry must reference the same canonical set
    r18_3e = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    canon_3d_slugs = {c["slug"] for c in canonical}
    canon_3e_slugs = set(r18_3e["canonical_it_set_27_locked"])
    assert canon_3d_slugs == canon_3e_slugs, (
        f"Canonical set drift R18.3d vs R18.3e:\n"
        f"  in 3d not 3e: {canon_3d_slugs - canon_3e_slugs}\n"
        f"  in 3e not 3d: {canon_3e_slugs - canon_3d_slugs}"
    )


# ─── Test 15 — Sealed integrity (in-process SHA256 static check, no subprocess)
# Hash noti dal R18.3d Phase B Closure Report (SEAL @ 2026-07-05T18:05:00Z).
# Qualsiasi drift su questi 5 hash indica corruzione dei sigilli R18.3d.
R18_3D_SEALED_HASHES_KNOWN = {
    "/app/memory/r18_3d_stat_role_mapping_registry.json":
        "3dec65cab59a92a36d52db7187fa3ae6aa01450e7160378722faa1bf54e2bb16",
    "/app/memory/r18_3d_stat_role_mapping_registry.md":
        "2e360cfec4fa59db0f57e6a6dec6332eb6bca9d589d923ca27552cc16937c398",
    "/app/backend/app/core/stat_role_registry.py":
        "e1e083e3b923fcf547baa3cb1fee27816ef4a149217f49d47699c62c08ab134b",
    "/app/backend/app/scripts/round18_3d_apply_metadata.py":
        "b439f429adabccf62897dae78fa163df5b2ba8c404d65f7f5f51f575f50c61d7",
    "/app/backend/tests/backend_r18_3d_stat_role_registry_test.py":
        "12ee2df3316147985c3a83b4e30c9c38fac45facd260f8898f8f53f2aef7c1e2",
}


def test_15_sealed_integrity_16_files():
    """Verifica in-process (no subprocess pytest, no ricorsione):
    - I 16 file sealed esistono
    - Ogni file ha SHA256 con 64 hex-digit valid
    - I 5 file R18.3d Phase B hanno SHA256 identico al closure report noto
    - I 11 file R18.Reset.1b/1.2/1c NON hanno hash zero e sono leggibili
    """
    sealed_paths = [
        REPO_ROOT / "backend/app/core/job_freeze.py",
        REPO_ROOT / "backend/app/scripts/round18_reset1b_apply_v1_1.py",
        REPO_ROOT / "backend/app/scripts/round18_reset1b_apply_v1_2.py",
        REPO_ROOT / "backend/app/scripts/round18_reset1b_apply_v1_3.py",
        REPO_ROOT / "backend/app/scripts/round18_reset1b_staged_backup_materialize.py",
        REPO_ROOT / "backend/app/scripts/round18_reset1c_field_cleanup.py",
        REPO_ROOT / "backend/tests/backend_round1b_write_freeze_full_test.py",
        REPO_ROOT / "backend/tests/backend_round1b_hotfix_starter_kit_test.py",
        REPO_ROOT / "backend/tests/backend_round1b_hotfix_v1_2_starter_stats_test.py",
        REPO_ROOT / "backend/tests/backend_round1b_hotfix_v1_3_schema_compat_test.py",
        REPO_ROOT / "backend/tests/backend_r18_reset2_banner_dismiss_test.py",
        REPO_ROOT / "backend/app/core/stat_role_registry.py",
        REPO_ROOT / "backend/app/scripts/round18_3d_apply_metadata.py",
        REPO_ROOT / "backend/tests/backend_r18_3d_stat_role_registry_test.py",
        REPO_ROOT / "memory/r18_3d_stat_role_mapping_registry.json",
        REPO_ROOT / "memory/r18_3d_stat_role_mapping_registry.md",
    ]
    assert len(sealed_paths) == 16, f"Expected 16 sealed files, got {len(sealed_paths)}"

    # 1) All 16 files exist + hash valid-hex + non-zero
    zero_hash = "0" * 64
    for p in sealed_paths:
        assert p.exists(), f"Sealed file missing: {p}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert len(h) == 64, f"Invalid hex length for {p}: {len(h)}"
        int(h, 16)  # hex validation
        assert h != zero_hash, f"Zero hash detected for {p}"

    # 2) 5 R18.3d files SHA256 match closure report known hashes (byte-identical)
    drifts: list[str] = []
    for path_str, expected in R18_3D_SEALED_HASHES_KNOWN.items():
        path = Path(path_str)
        assert path.exists(), f"R18.3d sealed file missing: {path}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            drifts.append(f"{path_str}: expected={expected}, actual={actual}")
    assert not drifts, "R18.3d sealed SHA256 DRIFT detected:\n" + "\n".join(drifts)
