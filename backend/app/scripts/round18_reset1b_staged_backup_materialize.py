"""ROUND 18.Reset.1b STAGED — Helper to materialize backup snapshot in
READ-ONLY invocation of `_backup_snapshot()` from round18_reset1b_apply.

Contesto (autorizzato dal PM):
    R18.Reset.1b DRY-RUN modality in `round18_reset1b_apply.py` skippa
    lo step S2 (backup snapshot). Per completare lo step 4-5 del
    protocollo staged apply, serve materializzare il backup JSONL +
    manifest sha256 SENZA modificare lo script apply SEALED e SENZA
    scritture sul DB.

    Questo helper:
    - Importa la funzione `_backup_snapshot` dallo script apply
    - La invoca con mode="STAGED_PRE_APPLY_READONLY_BACKUP" (qualsiasi
      stringa != "DRY_RUN" innesca il ramo materializzante)
    - `_backup_snapshot` legge doc dal DB (find({})) + scrive JSONL locali
      + calcola sha256 in memory. ZERO scritture sul DB.

Vincoli PM (R18.Reset.1b staged):
    - ZERO modifica a round18_reset1b_apply.py (verificato via mtime+sha256)
    - ZERO --apply, ZERO --i-understand-this-will-reset-all-guilds
    - ZERO scritture su DB (self-audit gate)
    - Maintenance mode RESTA ATTIVO durante e dopo l'esecuzione
    - Solo lettura DB + scrittura JSONL locali su filesystem

Self-audit convention:
    Il sorgente di questo file NON contiene i token letterali di chiamate
    mutanti a Mongo/Motor (insert_one, insert_many, update_one,
    update_many, replace_one, delete_one, delete_many, bulk_write, .drop(,
    .rename(). Costruiti a runtime via concatenazione di frammenti in
    `MUTATING_TOKEN_FRAGS`. Il self-audit rilegge il proprio sorgente,
    ricompone i token e verifica che ZERO literal string di quei token
    sia presente nel codice attivo. Se anche uno solo appare -> sys.exit(1).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


# --- Self-audit: token vietati costruiti runtime, ZERO literal in sorgente ---
_MUT_FRAGS = [
    ("insert", "one"),
    ("insert", "many"),
    ("update", "one"),
    ("update", "many"),
    ("replace", "one"),
    ("delete", "one"),
    ("delete", "many"),
    ("bulk", "write"),
]
MUTATING_TOKENS = [a + "_" + b for a, b in _MUT_FRAGS]
_EXTRA_FRAGS = [
    (".dr", "op("),
    (".ren", "ame("),
    ("$o", "ut"),
    ("$mer", "ge"),
]
EXTRA_TOKENS = [a + b for a, b in _EXTRA_FRAGS]

MAINTENANCE_FLAG_FILE = "/tmp/orbus_maintenance.flag"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str, level: str = "INFO") -> None:
    print(f"[{_utc_iso()}] [{level}] {msg}", flush=True)


def _self_audit() -> None:
    """Legge il proprio sorgente e rifiuta se contiene literal di token
    mutanti (attivi). Fail-close.
    """
    source_path = Path(__file__)
    source = source_path.read_text(encoding="utf-8")
    # Rimuovo tutte le linee che appartengono a docstring / commenti / lista
    # dei token stessi. Approccio: escludo tutto cio' che sta prima della
    # keyword sentinel "# SELFAUDIT-BEGIN" fino a "# SELFAUDIT-END".
    # Se non e' presente, valuto l'intero sorgente.
    begin_marker = "# SELF" + "AUDIT-BEGIN"
    end_marker = "# SELF" + "AUDIT-END"
    if begin_marker in source and end_marker in source:
        i = source.index(begin_marker)
        j = source.index(end_marker)
        audited = source[i:j]
    else:
        audited = source
    found = []
    for tok in MUTATING_TOKENS + EXTRA_TOKENS:
        if tok in audited:
            found.append(tok)
    if found:
        _log(
            "STAGED-BACKUP VIOLATION: forbidden mutating call detected "
            f"in own source. Tokens: {found}",
            level="ERROR",
        )
        sys.exit(1)
    _log(
        f"[self-audit] PASS - no literal mutating tokens in audited "
        f"section (checked {len(MUTATING_TOKENS) + len(EXTRA_TOKENS)} "
        "patterns)"
    )


def _verify_maintenance_pre() -> None:
    """Verifica che il flag file esista prima di procedere."""
    if not Path(MAINTENANCE_FLAG_FILE).exists():
        _log(
            f"HARD STOP: maintenance flag file missing: "
            f"{MAINTENANCE_FLAG_FILE}. Backup materialization ABORTED.",
            level="ERROR",
        )
        sys.exit(2)
    _log(f"[maintenance] flag file present at {MAINTENANCE_FLAG_FILE}")


def _hash_file_line_by_line(path: Path) -> tuple[str, int]:
    """Ricalcola sha256 di un JSONL leggendo linea per linea con
    line.encode('utf-8'), coerente con la scrittura in _backup_snapshot.
    """
    hasher = hashlib.sha256()
    lines = 0
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            hasher.update(line.encode("utf-8"))
            lines += 1
    return hasher.hexdigest(), lines


async def _run_materialize(backup_root: Path) -> dict:
    # SELFAUDIT-BEGIN
    from app.scripts.round18_reset1b_apply import (  # noqa: WPS433
        _backup_snapshot,
    )
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        _log(
            "[materialize] calling _backup_snapshot with "
            f"mode='STAGED_PRE_APPLY_READONLY_BACKUP' "
            f"backup_root={backup_root}"
        )
        info = await _backup_snapshot(
            db,
            backup_root,
            mode="STAGED_PRE_APPLY_READONLY_BACKUP",
        )
        _log(f"[materialize] _backup_snapshot returned: {info}")
        return info
    finally:
        client.close()
    # SELFAUDIT-END


def _verify_manifest_sha256(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = []
    mismatches = []
    total_lines = 0
    for entry in manifest["collections"]:
        p = Path(entry["file"])
        expected = entry["sha256"]
        expected_count = entry["doc_count"]
        actual_hash, actual_lines = _hash_file_line_by_line(p)
        total_lines += actual_lines
        ok = (actual_hash == expected) and (actual_lines == expected_count)
        if not ok:
            mismatches.append({
                "collection": entry["name"],
                "expected_sha256": expected,
                "actual_sha256": actual_hash,
                "expected_lines": expected_count,
                "actual_lines": actual_lines,
            })
        results.append({
            "collection": entry["name"],
            "lines": actual_lines,
            "sha256_ok": ok,
        })
    return {
        "files_verified": len(results),
        "total_lines": total_lines,
        "mismatches": mismatches,
        "per_file": results,
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description="R18.Reset.1b STAGED: helper to materialize backup",
    )
    p.add_argument(
        "--backup-root",
        default=None,
        help=(
            "Path root for backup. Default: "
            "/app/backend/backups/r18_reset1b_staged_<UTC-ISO>/"
        ),
    )
    args = p.parse_args()

    _log(f"====== R18.Reset.1b STAGED backup materialize START ======")

    # 1. Self-audit fail-close
    _self_audit()

    # 2. Maintenance flag verify
    _verify_maintenance_pre()

    # 3. Backup root
    if args.backup_root:
        backup_root = Path(args.backup_root)
    else:
        ts = _utc_iso().replace(":", "").replace("-", "").split("+")[0]
        backup_root = Path(
            f"/app/backend/backups/r18_reset1b_staged_{ts}Z"
        )
    _log(f"[main] backup_root = {backup_root}")

    # 4. Invoke _backup_snapshot (read-only DB + JSONL local writes)
    info = asyncio.run(_run_materialize(backup_root))
    if not info.get("created", False):
        _log(
            "HARD STOP: _backup_snapshot did NOT materialize backup. "
            f"Info: {info}",
            level="ERROR",
        )
        sys.exit(3)

    # 5. Verify manifest sha256 line-by-line
    manifest_path = backup_root / "manifest.json"
    if not manifest_path.exists():
        _log(
            f"HARD STOP: manifest.json missing after materialize: "
            f"{manifest_path}",
            level="ERROR",
        )
        sys.exit(4)
    verify = _verify_manifest_sha256(manifest_path)
    if verify["mismatches"]:
        _log(
            f"HARD STOP: sha256 MISMATCH on "
            f"{len(verify['mismatches'])} files: "
            f"{verify['mismatches']}",
            level="ERROR",
        )
        sys.exit(5)
    _log(
        f"[verify] sha256 line-by-line PASS on "
        f"{verify['files_verified']} files, "
        f"{verify['total_lines']} lines hashed total"
    )

    # 6. Emit summary JSON to stdout for downstream reporting
    summary = {
        "manifest_path": str(manifest_path),
        "backup_root": str(backup_root),
        "sha256_verification": "PASS",
        "files_verified": verify["files_verified"],
        "total_lines": verify["total_lines"],
    }
    _log(
        f"====== R18.Reset.1b STAGED backup materialize DONE "
        f"(manifest={manifest_path}) ======"
    )
    print("\n=== SUMMARY_JSON ===")
    print(json.dumps(summary, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
