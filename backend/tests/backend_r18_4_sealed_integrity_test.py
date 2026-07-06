"""ROUND 18.4 — Phase B4 Sealed Integrity Test Suite (30 files aggregate).

Verifica statica in-process (no subprocess pytest, no ricorsione) di **30 sigilli**:
  - 19 pre-esistenti (11 R18.Reset + 5 R18.3d + 3 R18.3e) — byte-identical dal
    registry /app/memory/r18_3e_seal_registry.json
  - 11 nuovi R18.4 sealed post-B4 (SHA256 hard-coded post-banner)

Ogni drift → fail immediato con path + expected/actual hash.

Governance:
  - NO subprocess pytest (evita ricorsione)
  - NO write DB
  - NO touch a alcun file (read-only integrity check)
  - Test isolato, deterministico, riproducibile

Sealed file di R18.3e già coperti dal test 15 in
`backend_r18_3e_bridge_test.py` (16 file). Qui aggiungiamo verifica esaustiva
di TUTTI i 30 sigilli attivi post-B4.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


# ─── 19 sigilli pre-esistenti (byte-identical registry R18.3e) ───────────
# Path relativi al repo root /app; SHA256 dal registry aggregate R18.3e.
R18_PREEXISTING_19_SEALED_HASHES: dict[str, str] = json.loads(
    Path("/app/memory/r18_3e_seal_registry.json").read_text(encoding="utf-8")
    if Path("/app/memory/r18_3e_seal_registry.json").exists() else "{}"
).get("pre_existing_19_byte_identical", {})


# Extract flat mapping {path: sha256} dai 3 gruppi del registry
def _flatten_preexisting_19() -> dict[str, str]:
    reg = json.loads(
        Path("/app/memory/r18_3e_seal_registry.json").read_text(encoding="utf-8")
    )
    flat: dict[str, str] = {}
    # Aggregate 5 new + 3 pre-existing groups
    for path, meta in reg["r18_3e_new_seals_5"]["sealed_files"].items():
        sha = meta["sha256"] if isinstance(meta, dict) else meta
        flat[f"/app/{path}"] = sha
    for grp_name, grp in reg["pre_existing_19_byte_identical"].items():
        if isinstance(grp, dict):
            for path, sha in grp.items():
                flat[f"/app/{path}"] = sha
    return flat


# ─── 11 nuovi sigilli R18.4 (SHA256 hard-coded POST-banner apposition) ──
R18_4_NEW_11_SEALED_HASHES: dict[str, str] = {
    "/app/memory/r18_4_phase_b2_pm_decisions.md":
        "83b5f60813cef99cc30d8f4704860ec7f17a40da0de64093b706efa2de974566",
    "/app/memory/r18_4_phase_b2_pm_decisions.json":
        "c73e6743a6fbb26177deb7e941ce6e900f38b3db08fd894451d8859711832be4",
    "/app/memory/r18_4_class_bound_registry.md":
        "e26065a1da92e98278163ee7a2dd757d65dbddbacb668ff43df2e44a3611b43c",
    "/app/memory/r18_4_class_bound_registry.json":
        "c3a58e3d94f0053870a12197b29c02e0ec7d17ddae5d85496ca17584d0a2059d",
    "/app/backend/app/scripts/round18_4_backfill_slot_type.py":
        "7108bf189415468bc7148f70186d6b5f2e1f7a618f712cbb2f02693e00ab54e6",
    "/app/backend/app/scripts/round18_4_apply_class_bound.py":
        "fda696467001d313128630735a4e91dc03f0af3cf8eb9da43ef4ca7e8f2c26fa",
    "/app/backend/app/scripts/round18_4_backfill_slot_type_apply.py":
        "6a9a3c5cb50fc97c436fe39a71d39657d199885fd0ae35d335e08c8dc60c8461",
    "/app/backend/app/scripts/round18_4_apply_class_bound_apply.py":
        "1358d42fa051623ed5e06a44ee8b5279fb11fd99afc44bb0596f06d312ec42b3",
    "/app/backend/tests/backend_r18_4_class_bound_test.py":
        "f0644e2c3df869c0344afb2e831f2fffc8759eaef7554ed1764d7ba0a74d5d28",
    "/app/memory/r18_4_phase_b3_dry_run_prereport.md":
        "3bb1484826710a9a8b688e6152150ad2c8a860352daaaf1978b1a686aef76d59",
    "/app/memory/r18_4_phase_b3_real_apply_report.md":
        "de0c9b4661ac17b9b16ea7bd4b1e90ec7909a7b46b899563eb04c8e2fad94585",
}


# ═════════════════════════════════════════════════════════════════════
# Test 1 — 19 pre-existing sealed files byte-identical
# ═════════════════════════════════════════════════════════════════════

def test_r18_4_b4_seal_01_preexisting_19_byte_identical():
    """I 19 sigilli pre-esistenti (R18.Reset + R18.3d + R18.3e) devono
    essere byte-identical al registry aggregate R18.3e."""
    hashes = _flatten_preexisting_19()
    assert len(hashes) == 19, f"expected 19 pre-existing sealed paths, got {len(hashes)}"

    drifts: list[str] = []
    missing: list[str] = []
    for path_str, expected in hashes.items():
        path = Path(path_str)
        if not path.exists():
            missing.append(path_str)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            drifts.append(
                f"  {path_str}\n    expected: {expected}\n    actual:   {actual}"
            )
    assert not missing, "Pre-existing sealed files MISSING:\n" + "\n".join(missing)
    assert not drifts, (
        "R18 pre-existing sealed SHA256 DRIFT (governance violation):\n"
        + "\n".join(drifts)
    )


# ═════════════════════════════════════════════════════════════════════
# Test 2 — 11 new R18.4 sealed files byte-identical to post-banner hashes
# ═════════════════════════════════════════════════════════════════════

def test_r18_4_b4_seal_02_new_11_byte_identical():
    """Gli 11 nuovi sigilli R18.4 (post-banner apposition) devono essere
    byte-identical agli hash registrati nel report B4."""
    assert len(R18_4_NEW_11_SEALED_HASHES) == 11, (
        f"expected 11 new R18.4 sealed paths, got {len(R18_4_NEW_11_SEALED_HASHES)}"
    )

    drifts: list[str] = []
    missing: list[str] = []
    for path_str, expected in R18_4_NEW_11_SEALED_HASHES.items():
        path = Path(path_str)
        if not path.exists():
            missing.append(path_str)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            drifts.append(
                f"  {path_str}\n    expected: {expected}\n    actual:   {actual}"
            )
    assert not missing, "R18.4 sealed files MISSING:\n" + "\n".join(missing)
    assert not drifts, (
        "R18.4 sealed SHA256 DRIFT (governance violation):\n" + "\n".join(drifts)
    )


# ═════════════════════════════════════════════════════════════════════
# Test 3 — Aggregate count = 30 sealed files
# ═════════════════════════════════════════════════════════════════════

def test_r18_4_b4_seal_03_aggregate_count_30():
    """Il totale aggregato dei sigilli attivi post-B4 deve essere esattamente 30."""
    preexisting = _flatten_preexisting_19()
    total = len(preexisting) + len(R18_4_NEW_11_SEALED_HASHES)
    assert total == 30, f"expected 30 total sealed files, got {total}"


# ═════════════════════════════════════════════════════════════════════
# Test 4 — All 30 hashes are valid hex, 64 chars, non-zero
# ═════════════════════════════════════════════════════════════════════

def test_r18_4_b4_seal_04_hash_shape_validity():
    """Ogni hash deve essere 64-char hex non-zero."""
    zero_hash = "0" * 64
    all_hashes = {**_flatten_preexisting_19(), **R18_4_NEW_11_SEALED_HASHES}
    for path_str, h in all_hashes.items():
        assert len(h) == 64, f"invalid hex length for {path_str}: {len(h)}"
        int(h, 16)  # hex validation
        assert h != zero_hash, f"zero hash detected for {path_str}"


# ═════════════════════════════════════════════════════════════════════
# Test 5 — No duplicate paths across the 30 set
# ═════════════════════════════════════════════════════════════════════

def test_r18_4_b4_seal_05_no_duplicate_paths():
    """Nessun path deve apparire sia in pre-existing che in new R18.4."""
    preexisting_paths = set(_flatten_preexisting_19().keys())
    new_paths = set(R18_4_NEW_11_SEALED_HASHES.keys())
    overlap = preexisting_paths & new_paths
    assert overlap == set(), f"unexpected overlap: {overlap}"
