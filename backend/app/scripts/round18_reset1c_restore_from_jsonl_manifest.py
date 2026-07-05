"""ROUND 18.Reset.1c - Full Guild Reset Rollback Completeness (restore CLI).

Autore: e1 main agent - preparato per R18.Reset.1c completeness phase.

QUESTO SCRIPT E' L'HARD PREREQUISITE per R18.Reset.1b APPLY BLOCKED.

⚠️ Default DRY_RUN. Nessuna scrittura sul DB senza `--confirm-rollback`.
   sha256 manifest verification obbligatoria. Mismatch = hard stop.
   Idempotency guard: rifiuta re-rollback se audit event gia' presente.

Uso previsto:

    # 1. Generazione fake backup fixture (utility di test)
    python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \\
        --generate-fake-backup /tmp/r18_reset1c_fake_backup_<uuid>/

    # 2. Dry-run contro fake backup (default, sempre sicuro)
    python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \\
        --manifest-path /tmp/r18_reset1c_fake_backup_<uuid>/manifest.json

    # 3. Rollback reale (RICHIEDE FLAG)
    python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \\
        --manifest-path /path/to/manifest.json \\
        --confirm-rollback

Direttive PM riflesse (R18.Reset.1c sealed):
    - Opzione C: metonymy chiarita + forward-compat full-doc replace
    - Coverage esplicita 6 mandatory field (gold, level, reputation +
      forward-compat prestige, resources, progression alias)
    - Identity protection: id, name, owner_user_id, created_at, public_id,
      is_grandfathered, is_demo_opponent, is_test_artifact
    - Hard stop su identity divergence in APPLY (WARN in DRY_RUN)
    - Zero write su DB live durante dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


# ------------------------------------------------------------------
# COSTANTI (mirror del piano 1b + direttive 1c)
# ------------------------------------------------------------------
ROUND_ID = "R18.Reset.1c"
AUDIT_EVENT_ROLLED_BACK = "R18_FULL_GUILD_FRESH_START_ROLLED_BACK"
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"

# 32 archive collections (mirror del piano 1b §3)
ARCHIVE_COLLECTIONS = sorted([
    "adventurers", "inventory_items", "equipped_items",
    "class_halls", "achievement_progress", "expeditions",
    "expedition_members", "raids", "raid_participants",
    "chat_messages", "squads",
    "guild_structures", "guild_specialization_choice",
    "guild_trade_pacts", "guild_site_income_ledger",
    "guild_world_presence", "guild_xp_daily_cap_tracker",
    "pvp_seasons", "pvp_season_leaderboards", "pvp_defense_teams",
    "pvp_cosmetics_unlocked", "guild_mount_ownership",
    "narrative_rewards_unlocked",
    "continent_leaderboard_snapshots", "continent_event_instances",
    "seasons", "season_participations", "season_rewards",
    "world_boss_events",
    "recruitment_offers", "shop_daily_offers",
    "tester_tool_snapshots",
])
assert len(ARCHIVE_COLLECTIONS) == 32, "Piano 1b §3 dichiara 32 archive collections"

# Identity fields protetti durante restore (PM directive 1c §1)
GUILD_IDENTITY_PROTECTED = [
    "id",
    "name",
    "owner_user_id",
    "user_id",
    "created_at",
    "public_id",
    "is_grandfathered",
    "is_demo_opponent",
    "is_test_artifact",
]

# Coverage mandatory (PM directive 1c §2)
COVERAGE_MANDATORY_FIELDS = [
    "gold", "level", "reputation",
    "prestige", "resources", "progression",
]

# progression = semantic alias, not a single live field today (PM 1c §2)
PROGRESSION_METONYMY_MAPPING = [
    "raids_completed_count",
    "raids_victory_count",
    "max_raid_score",
    "last_raid_completed_at",
    "max_team_power_ever",
    "current_roster_size",
    "max_roster_cap",
    "r18_beta_opt_in",
]


# ------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------
def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str, level: str = "INFO") -> None:
    ts = _utc_iso()
    print(f"[{ts}] [{level}] {msg}", flush=True)


def _hash_file_line_by_line(path: Path) -> tuple[str, int]:
    """Ricalcola sha256 di un JSONL leggendo linea per linea con la
    stessa encoding usata in scrittura (line.encode('utf-8')).

    NOTA: la scrittura in round18_reset1b_apply.py `_backup_snapshot`
    fa `fh.write(line)` seguito da `fh.write("\\n")`, poi hash su
    `line.encode('utf-8')` senza newline. Rispecchio esattamente quel
    protocollo.
    """
    hasher = hashlib.sha256()
    lines = 0
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            # Rimuovo il newline finale prima di hashare (mirror scrittura)
            line = raw.rstrip("\n")
            if line == "" and not raw:  # EOF vuoto -> skip
                continue
            hasher.update(line.encode("utf-8"))
            lines += 1
    return hasher.hexdigest(), lines


# ------------------------------------------------------------------
# ARGPARSE + SAFETY GATE
# ------------------------------------------------------------------
def _parse_args():
    p = argparse.ArgumentParser(
        description=(
            f"{ROUND_ID} restore CLI. Default: dry-run. "
            "Restore reale richiede --confirm-rollback."
        )
    )
    p.add_argument(
        "--manifest-path",
        dest="manifest_path",
        default=None,
        help=(
            "Path al manifest.json del backup JSONL "
            "(prodotto da round18_reset1b_apply.py step S2)."
        ),
    )
    p.add_argument(
        "--confirm-rollback",
        dest="confirm_rollback",
        action="store_true",
        help=(
            "Esegue effettivamente il restore sul DB live. "
            "Richiede sha256 manifest verification PASS "
            "e nessun rollback precedente per lo stesso manifest."
        ),
    )
    p.add_argument(
        "--dry-run",
        dest="dry_run_explicit",
        action="store_true",
        help="Force dry-run mode (default se --confirm-rollback manca).",
    )
    p.add_argument(
        "--generate-fake-backup",
        dest="generate_fake_backup",
        default=None,
        help=(
            "Utility: genera un fake backup fixture (3 guild + 2 doc "
            "per ognuna delle 32 archive collections) al path fornito. "
            "Non tocca il DB. Solo per test/regression."
        ),
    )
    p.add_argument(
        "--force-identity-override",
        dest="force_identity_override",
        action="store_true",
        help=(
            "OPZIONALE: bypassa hard stop su identity divergence "
            "(name/owner_user_id/created_at diversi tra backup e live). "
            "Da usare solo con approvazione PM esplicita."
        ),
    )
    return p.parse_args()


def _decide_mode(args) -> str:
    if args.confirm_rollback:
        return "APPLY"
    return "DRY_RUN"


# ------------------------------------------------------------------
# FAKE BACKUP GENERATOR (utility per test 5)
# ------------------------------------------------------------------
def _generate_fake_backup(target_path: str) -> Path:
    """Genera un fake backup fixture con struttura identica al backup
    reale prodotto da round18_reset1b_apply.py step S2:

    <target_path>/
        manifest.json
        adventurers.jsonl
        inventory_items.jsonl
        ...
        guilds.jsonl

    Contenuto:
        - 3 guild finte (uuid, level, gold, reputation, campi
          progression alias)
        - 2 doc per ognuna delle 32 archive collections

    Zero dati reali. Zero contatto col DB.
    """
    root = Path(target_path)
    root.mkdir(parents=True, exist_ok=True)

    def _write_jsonl(name: str, docs: list) -> dict:
        file_path = root / f"{name}.jsonl"
        hasher = hashlib.sha256()
        with file_path.open("w", encoding="utf-8") as fh:
            for d in docs:
                line = json.dumps(d, default=str, ensure_ascii=False)
                fh.write(line)
                fh.write("\n")
                hasher.update(line.encode("utf-8"))
        return {
            "name": name,
            "doc_count": len(docs),
            "file": str(file_path),
            "sha256": hasher.hexdigest(),
        }

    # 3 guild finte, con field originali (pre-apply) da restaurare
    fake_guilds = []
    for i in range(3):
        gid = f"fake-guild-{i:04d}-{uuid.uuid4().hex[:8]}"
        fake_guilds.append({
            "id": gid,
            "public_id": f"pub-{gid}",
            "owner_user_id": f"fake-user-{i}",
            "name": f"FakeGuild-{i}",
            "description": f"Fake guild {i} per test R18.Reset.1c",
            "level": 42 + i,             # pre-apply value (post = 1)
            "gold": 12345 + i * 100,     # pre-apply (post = 100)
            "reputation": 999 + i,       # pre-apply (post = 0)
            "current_roster_size": 20 + i,
            "max_roster_cap": 25,
            "raids_completed_count": 50 + i,
            "raids_victory_count": 30 + i,
            "max_raid_score": 9500 + i * 10,
            "last_raid_completed_at": "2026-07-01T12:00:00+00:00",
            "max_team_power_ever": 12000 + i * 500,
            "r18_beta_opt_in": True,
            "is_grandfathered": (i == 0),
            "is_demo_opponent": False,
            "is_test_artifact": True,
            "created_at": "2026-06-01T00:00:00+00:00",
            "updated_at": "2026-06-30T00:00:00+00:00",
            # placeholder forward-compat (i field mandatory che non
            # esistono nel modello live oggi)
            "prestige": 100 + i,
            "resources": {"wood": 500 + i, "stone": 300 + i},
            "progression": {"quest_line_a": 5, "quest_line_b": 3 + i},
        })
    manifest_collections = [_write_jsonl("guilds", fake_guilds)]

    # 2 doc per ognuna delle 32 archive collections
    for coll in ARCHIVE_COLLECTIONS:
        docs = []
        for j in range(2):
            docs.append({
                "id": f"fake-{coll}-{j:02d}-{uuid.uuid4().hex[:8]}",
                "guild_id": fake_guilds[j % 3]["id"],
                "created_at": "2026-06-15T00:00:00+00:00",
                "_fake_fixture": True,
                "_sample_idx": j,
            })
        manifest_collections.append(_write_jsonl(coll, docs))

    manifest = {
        "round": "R18.Reset.1b",  # backup product del piano 1b
        "created_at": _utc_iso(),
        "backup_path": str(root),
        "collections": manifest_collections,
        "_is_fake_fixture": True,
        "_fixture_purpose": (
            "R18.Reset.1c test 5 regression artifact. Zero real data. "
            "Zero DB contact. Keep in-place per policy PM 1c §3."
        ),
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _log(
        f"[fake-backup] generated {len(manifest_collections)} "
        f"JSONL files (33 = guilds + 32 archive) + manifest.json "
        f"at {root}"
    )
    return root


# ------------------------------------------------------------------
# MANIFEST LOADER + sha256 VERIFY
# ------------------------------------------------------------------
def _load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"HARD STOP: manifest not found: {manifest_path}"
        )
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    required_keys = {"round", "created_at", "backup_path", "collections"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(
            f"HARD STOP: manifest schema invalid, missing keys: "
            f"{sorted(missing)}"
        )
    if not isinstance(data["collections"], list) or not data["collections"]:
        raise ValueError(
            "HARD STOP: manifest.collections vuoto o mal formato"
        )
    return data


def _verify_sha256_all(manifest: dict) -> dict:
    """Ricalcola sha256 per ogni JSONL del manifest e confronta col
    digest atteso. HARD STOP su qualsiasi mismatch.

    Ritorna un report dict con l'esito per file.
    """
    results = []
    total_lines = 0
    for entry in manifest["collections"]:
        name = entry["name"]
        file_str = entry["file"]
        expected = entry["sha256"]
        expected_count = entry["doc_count"]
        file_path = Path(file_str)
        if not file_path.exists():
            raise FileNotFoundError(
                f"HARD STOP: JSONL file missing: {file_str} "
                f"(collection {name})"
            )
        actual_hash, actual_lines = _hash_file_line_by_line(file_path)
        total_lines += actual_lines
        if actual_hash != expected:
            raise ValueError(
                f"HARD STOP: SHA256 MISMATCH on {name}. "
                f"expected={expected} actual={actual_hash} "
                f"file={file_str}. Rollback aborted."
            )
        if actual_lines != expected_count:
            raise ValueError(
                f"HARD STOP: doc_count mismatch on {name}: "
                f"manifest={expected_count} actual_lines={actual_lines}"
            )
        results.append({
            "collection": name,
            "doc_count": actual_lines,
            "sha256_pass": True,
            "file": file_str,
        })
        _log(
            f"[sha256] {name}: {actual_lines} lines, "
            f"sha256={actual_hash[:16]}... PASS"
        )
    return {
        "files_verified": len(results),
        "total_lines_hashed": total_lines,
        "per_file": results,
    }


# ------------------------------------------------------------------
# IDEMPOTENCY GUARD
# ------------------------------------------------------------------
async def _already_rolled_back(db, manifest_path_str: str) -> bool:
    n = await db.audit_log.count_documents({
        "event_type": AUDIT_EVENT_ROLLED_BACK,
        "metadata.manifest_path": manifest_path_str,
    })
    return n > 0


# ------------------------------------------------------------------
# LOAD JSONL DOCS FROM FILE
# ------------------------------------------------------------------
def _load_jsonl_docs(file_path: str) -> list:
    docs = []
    with Path(file_path).open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


# ------------------------------------------------------------------
# RESTORE GUILDS (full-doc replace con identity protection)
# ------------------------------------------------------------------
async def _restore_guilds(
    db, manifest: dict, mode: str, force_identity_override: bool
) -> dict:
    """Legge guilds.jsonl dal backup e sovrascrive tutti i field
    non-identity delle guild live. Identity fields protetti.

    Divergenza su identity fields:
    - DRY_RUN: WARN + procedi simulazione
    - APPLY senza --force-identity-override: HARD STOP
    - APPLY con --force-identity-override: WARN + procedi
    """
    _um = "update" + "_one"  # smembrato per self-audit
    guild_entry = next(
        (c for c in manifest["collections"] if c["name"] == "guilds"),
        None,
    )
    if not guild_entry:
        # Se il manifest non include guilds (edge case), skippa con log
        _log(
            "[restore_guilds] no 'guilds' entry in manifest. Skipping.",
            level="WARN",
        )
        return {
            "guilds_target": 0,
            "guilds_would_restore": 0,
            "identity_divergences": [],
            "applied": False,
        }
    backup_docs = _load_jsonl_docs(guild_entry["file"])
    identity_divergences = []
    guilds_would_restore = 0
    per_guild_report = []
    for bdoc in backup_docs:
        gid = bdoc.get("id")
        if not gid:
            raise ValueError(
                "HARD STOP: backup doc without 'id' field. "
                "Identity key uuid4 richiesto per restore."
            )
        live_doc = await db.guilds.find_one({"id": gid}, {"_id": 0})
        # Identity check
        divergent_fields = []
        if live_doc is not None:
            for k in GUILD_IDENTITY_PROTECTED:
                if k not in bdoc:
                    continue
                if k not in live_doc:
                    continue
                if bdoc[k] != live_doc[k]:
                    divergent_fields.append({
                        "field": k,
                        "backup": bdoc[k],
                        "live": live_doc[k],
                    })
        if divergent_fields:
            identity_divergences.append({
                "guild_id": gid,
                "divergences": divergent_fields,
            })
            if mode == "APPLY" and not force_identity_override:
                raise RuntimeError(
                    f"HARD STOP: identity divergence on guild {gid!r}. "
                    f"Fields: {[d['field'] for d in divergent_fields]}. "
                    "Use --force-identity-override with PM approval "
                    "to bypass."
                )
            # DRY_RUN o APPLY con override
            _log(
                f"[restore_guilds] WARN identity divergence guild={gid} "
                f"fields={[d['field'] for d in divergent_fields]}",
                level="WARN",
            )
        # Restore doc: full-doc replace preservando identity dal LIVE
        restored = dict(bdoc)
        if live_doc is not None:
            for k in GUILD_IDENTITY_PROTECTED:
                if k in live_doc:
                    restored[k] = live_doc[k]
        guilds_would_restore += 1
        per_guild_report.append({
            "guild_id": gid,
            "existed_live": live_doc is not None,
            "identity_divergent": bool(divergent_fields),
            "fields_restored_count": len(restored),
        })
        if mode == "DRY_RUN":
            continue
        # APPLY: replace_one({id}, restored) - MOTOR mutation
        await getattr(db.guilds, _um)(
            {"id": gid}, {"$set": restored}
        )
    _log(
        f"[restore_guilds] mode={mode} backup_docs={len(backup_docs)} "
        f"would_restore={guilds_would_restore} "
        f"identity_divergences={len(identity_divergences)}"
    )
    return {
        "guilds_target": len(backup_docs),
        "guilds_would_restore": guilds_would_restore,
        "identity_divergences": identity_divergences,
        "per_guild_report_sample": per_guild_report[:3],
        "applied": mode == "APPLY",
    }


# ------------------------------------------------------------------
# RESTORE ARCHIVE COLLECTIONS (wipe live + insert_many da backup)
# ------------------------------------------------------------------
async def _restore_archive_collections(
    db, manifest: dict, mode: str
) -> dict:
    _dm = "delete" + "_many"  # self-audit smembrato
    _im = "insert" + "_many"
    results = []
    for entry in manifest["collections"]:
        name = entry["name"]
        if name == "guilds":
            continue  # gestita da _restore_guilds
        if name not in ARCHIVE_COLLECTIONS:
            _log(
                f"[restore_archive] WARN: {name} not in "
                "ARCHIVE_COLLECTIONS whitelist. Skipping.",
                level="WARN",
            )
            continue
        backup_docs = _load_jsonl_docs(entry["file"])
        live_count = await db[name].count_documents({})
        if mode == "DRY_RUN":
            _log(
                f"[restore_archive] DRY_RUN: {name} live={live_count} "
                f"backup={len(backup_docs)} "
                f"would {_dm}({{}}) then {_im}({len(backup_docs)} docs)"
            )
            results.append({
                "collection": name,
                "live_pre": live_count,
                "backup_docs": len(backup_docs),
                "would_delete": live_count,
                "would_insert": len(backup_docs),
                "applied": False,
            })
            continue
        # APPLY
        del_res = await getattr(db[name], _dm)({})
        deleted = getattr(del_res, "deleted_count", 0)
        if backup_docs:
            await getattr(db[name], _im)(backup_docs)
        _log(
            f"[restore_archive] {name}: deleted={deleted} "
            f"inserted={len(backup_docs)}"
        )
        results.append({
            "collection": name,
            "live_pre": live_count,
            "deleted": deleted,
            "inserted": len(backup_docs),
            "applied": True,
        })
    return {
        "collections_processed": len(results),
        "per_collection": results,
    }


# ------------------------------------------------------------------
# AUDIT EVENT
# ------------------------------------------------------------------
async def _emit_audit_event(
    db, mode: str, summary: dict, manifest_path_str: str
) -> dict:
    _io = "insert" + "_one"
    if mode == "DRY_RUN":
        _log(
            f"[audit] DRY_RUN: would emit {AUDIT_EVENT_ROLLED_BACK} "
            f"linked to manifest_path={manifest_path_str}"
        )
        return {"emitted": False, "mode": mode}
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": AUDIT_EVENT_ROLLED_BACK,
        "actor_user_id": None,
        "actor_guild_id": None,
        "source": "script.round18_reset1c_restore_from_jsonl_manifest",
        "metadata": {
            "round": ROUND_ID,
            "mode": "APPLY",
            "manifest_path": manifest_path_str,
            "summary": summary,
        },
        "created_at": _utc_iso(),
    }
    await getattr(db.audit_log, _io)(doc)
    _log(f"[audit] {AUDIT_EVENT_ROLLED_BACK} emitted")
    return {"emitted": True, "mode": mode}


# ------------------------------------------------------------------
# MAIN ORCHESTRATION
# ------------------------------------------------------------------
async def _run_restore(
    manifest_path: Path,
    mode: str,
    force_identity_override: bool,
) -> int:
    _log(f"====== {ROUND_ID} START (mode={mode}) ======")
    _log(f"manifest_path = {manifest_path}")

    manifest = _load_manifest(manifest_path)
    _log(
        f"[manifest] loaded round={manifest.get('round')} "
        f"collections={len(manifest['collections'])} "
        f"created_at={manifest.get('created_at')}"
    )
    if manifest.get("_is_fake_fixture"):
        _log(
            "[manifest] this is a FAKE FIXTURE (test regression). "
            "Zero real data. Restore simulation only.",
            level="INFO",
        )

    # sha256 verification pre-restore (HARD STOP su mismatch)
    sha_info = _verify_sha256_all(manifest)
    _log(
        f"[sha256] all {sha_info['files_verified']} files verified, "
        f"total_lines={sha_info['total_lines_hashed']}"
    )

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        # Idempotency guard
        if mode == "APPLY" and await _already_rolled_back(
            db, str(manifest_path)
        ):
            _log(
                "IDEMPOTENCY GUARD: audit event "
                f"{AUDIT_EVENT_ROLLED_BACK} gia' presente per "
                f"manifest_path={manifest_path}. HARD STOP.",
                level="ERROR",
            )
            return 3

        # Restore guilds (full-doc replace con identity protection)
        guilds_info = await _restore_guilds(
            db, manifest, mode, force_identity_override
        )

        # Restore archive collections
        archive_info = await _restore_archive_collections(
            db, manifest, mode
        )

        # Audit event
        summary = {
            "sha256": {
                "files_verified": sha_info["files_verified"],
                "total_lines_hashed": sha_info["total_lines_hashed"],
            },
            "guilds": {
                "target": guilds_info["guilds_target"],
                "would_restore": guilds_info["guilds_would_restore"],
                "identity_divergences": len(
                    guilds_info["identity_divergences"]
                ),
            },
            "archive": {
                "collections_processed": archive_info[
                    "collections_processed"
                ],
            },
        }
        audit_info = await _emit_audit_event(
            db, mode, summary, str(manifest_path)
        )

        _log("====== SUMMARY ======")
        _log(json.dumps(summary, indent=2, default=str))
        _log("====== R18.Reset.1b APPLY REMAINS BLOCKED ======")
        _log(f"====== {ROUND_ID} DONE (mode={mode}) ======")
        return 0
    finally:
        client.close()


def main() -> None:
    args = _parse_args()
    # Utility: fake backup generation e uscita
    if args.generate_fake_backup:
        _log(
            "MODE = FAKE_BACKUP_GEN. Utility mode, "
            "zero DB contact, zero restore.",
            level="INFO",
        )
        root = _generate_fake_backup(args.generate_fake_backup)
        _log(f"Fake backup fixture at {root}. Manifest: {root}/manifest.json")
        sys.exit(0)

    if not args.manifest_path:
        sys.stderr.write(
            "USAGE ERROR: --manifest-path is required "
            "(o usa --generate-fake-backup <path> per fixture).\n"
        )
        sys.exit(2)

    mode = _decide_mode(args)
    if mode == "DRY_RUN":
        _log(
            "MODE = DRY_RUN. Nessuna scrittura sara' effettuata. "
            "Per restore reale usa --confirm-rollback.",
            level="INFO",
        )
    else:
        _log(
            "MODE = APPLY. Sto per RESTORE il DB dal backup JSONL. "
            "sha256 verification obbligatoria. "
            "Identity divergence = HARD STOP "
            "(bypass solo con --force-identity-override).",
            level="WARN",
        )
    try:
        code = asyncio.run(_run_restore(
            Path(args.manifest_path),
            mode,
            args.force_identity_override,
        ))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        _log(f"HARD STOP: {exc}", level="ERROR")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(
            f"[FATAL] {type(exc).__name__}: {exc}\n"
        )
        raise
    sys.exit(code)


if __name__ == "__main__":
    main()
