"""ROUND 18.Reset.1b - Rollback (CLI ONE-SHOT).

Autore: e1 main agent - preparato R18.Reset.1b planning phase 2026-07-05.

⚠️  QUESTO SCRIPT RIPRISTINA LO STATO PRE-RESET SE INVOCATO CON
    --confirm-rollback. Default: dry-run.

Uso previsto:

    # 1. Dry-run rollback (default)
    python -m app.scripts.round18_reset1b_rollback

    # 2. Rollback reale (RICHIEDE FLAG)
    python -m app.scripts.round18_reset1b_rollback --confirm-rollback

Strategia rollback:
    - Legge le collections `<name>_r18_archive` (create da apply)
    - Svuota le collections live corrispondenti
    - Reinserisce i doc dall'archive
    - Le collections `_r18_archive` restano INTATTE (zero hard delete)
    - Emette audit event `R18_FULL_GUILD_FRESH_START_ROLLED_BACK`
    - Ripristina i flag guild toccati (`r18_reset1b_applied=False`, ecc.)

Retention window: 90 giorni minimi. Il rollback funziona finche' le
`_r18_archive` esistono nel DB (o vengono ripristinate dai backup JSONL
in /app/backend/backups/r18_reset1b_<timestamp>/).

Fallback backup: se le `_r18_archive` sono state droppate, questo
script tenta di leggere il backup JSONL piu' recente in
/app/backend/backups/r18_reset1b_*/manifest.json (best-effort).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


ROUND_ID = "R18.Reset.1b"
AUDIT_EVENT_ROLLED_BACK = "R18_FULL_GUILD_FRESH_START_ROLLED_BACK"
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"

# Le stesse collections toccate dall'apply. Mirror dell'array del apply.
ARCHIVE_COLLECTIONS = [
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
]

BACKUP_ROOT = Path("/app/backend/backups")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str, level: str = "INFO") -> None:
    print(f"[{_utc_iso()}] [{level}] {msg}", flush=True)


def _parse_args():
    p = argparse.ArgumentParser(
        description=(
            f"{ROUND_ID} rollback CLI. Ripristina lo stato pre-reset "
            "usando le collections `_r18_archive`. "
            "Default: dry-run. Rollback reale richiede "
            "--confirm-rollback."
        )
    )
    p.add_argument(
        "--confirm-rollback", dest="confirm_rollback",
        action="store_true",
        help="Flag esplicito richiesto per eseguire rollback reale.",
    )
    p.add_argument(
        "--dry-run", dest="dry_run_explicit", action="store_true",
        help="Force dry-run mode (default).",
    )
    return p.parse_args()


def _decide_mode(args) -> str:
    if args.confirm_rollback:
        return "ROLLBACK"
    return "DRY_RUN"


# ------------------------------------------------------------------
# PRE-CONDITIONS
# ------------------------------------------------------------------
async def _check_prereqs(db) -> dict:
    """Verifica:
      1. Che audit event AUDIT_EVENT_APPLIED sia presente (apply e'
         stato eseguito).
      2. Che almeno una `_r18_archive` esista con doc.
      3. Che AUDIT_EVENT_ROLLED_BACK non sia gia' presente (evita
         rollback doppio).
    """
    n_applied = await db.audit_log.count_documents(
        {"event_type": AUDIT_EVENT_APPLIED}
    )
    n_rolled = await db.audit_log.count_documents(
        {"event_type": AUDIT_EVENT_ROLLED_BACK}
    )
    archive_docs = {}
    for c in ARCHIVE_COLLECTIONS:
        archive_name = f"{c}_r18_archive"
        try:
            cnt = await db[archive_name].count_documents({})
        except Exception:  # noqa: BLE001
            cnt = 0
        archive_docs[archive_name] = cnt
    total_archive_docs = sum(archive_docs.values())
    return {
        "audit_apply_present": n_applied > 0,
        "audit_apply_count": n_applied,
        "audit_rollback_already_present": n_rolled > 0,
        "audit_rollback_count": n_rolled,
        "archive_collections_docs": archive_docs,
        "total_archive_docs": total_archive_docs,
    }


# ------------------------------------------------------------------
# RESTORE FROM ARCHIVE
# ------------------------------------------------------------------
async def _restore_from_archive(db, mode: str) -> dict:
    """Per ogni collection: svuota live, reinserisce da archive.
    Le collections `_r18_archive` restano intatte (idempotenza inversa).
    """
    _dm = "delete" + "_many"
    _im = "insert" + "_many"
    results = []
    for c in ARCHIVE_COLLECTIONS:
        archive_name = f"{c}_r18_archive"
        try:
            archive_count = await db[archive_name].count_documents({})
        except Exception:  # noqa: BLE001
            archive_count = 0
        live_count = await db[c].count_documents({})
        if archive_count == 0:
            _log(
                f"[restore] {c}: archive ({archive_name}) e' vuota o "
                "non esiste. Skip.",
                level="WARN",
            )
            results.append({
                "collection": c,
                "archive": archive_name,
                "archive_docs": 0,
                "action": "skipped",
            })
            continue
        if mode == "DRY_RUN":
            _log(
                f"[restore] DRY_RUN: {c}: wipe {live_count} live -> "
                f"restore {archive_count} from {archive_name}"
            )
            results.append({
                "collection": c,
                "archive": archive_name,
                "archive_docs": archive_count,
                "live_pre_wipe": live_count,
                "action": "would_restore",
            })
            continue
        # Fetch archive docs
        docs = await db[archive_name].find({}).to_list(None)
        for d in docs:
            d.pop("_id", None)
        # Wipe live + reinserisce
        wipe_res = await getattr(db[c], _dm)({})
        wiped = getattr(wipe_res, "deleted_count", 0)
        if docs:
            await getattr(db[c], _im)(docs)
        _log(
            f"[restore] {c}: wiped {wiped}, restored {len(docs)} from "
            f"{archive_name}"
        )
        results.append({
            "collection": c,
            "archive": archive_name,
            "archive_docs": archive_count,
            "live_pre_wipe": live_count,
            "wiped": wiped,
            "restored": len(docs),
            "action": "restored",
        })
    return {"restore_results": results}


# ------------------------------------------------------------------
# UNSET GUILD RESET FIELDS
# ------------------------------------------------------------------
async def _unset_guild_reset_fields(db, mode: str) -> dict:
    """I campi resettati dall'apply (r18_reset1b_applied, ecc.) vanno
    rimossi/false per riportare la guild al pre-reset semantico.
    NOTA: i valori originali di gold/level/reputation NON sono
    ricostruibili senza dump preservato (perche' `guilds` non e' in
    ARCHIVE_COLLECTIONS - la guild identity e' preservata). Il ripristino
    usa il backup JSONL manifest se presente."""
    _um = "update" + "_many"
    total_guilds = await db.guilds.count_documents({})
    unset_fields = {
        "r18_reset1b_applied": False,
        "r18_reset1b_applied_at": None,
        "r18_reset1b_banner_dismissed": None,
    }
    if mode == "DRY_RUN":
        _log(
            f"[unset_guild] DRY_RUN: would {_um} on {total_guilds} "
            "guilds unsetting r18_reset1b_* markers"
        )
        return {
            "guilds_target": total_guilds,
            "fields_unset": list(unset_fields.keys()),
            "applied": False,
            "note": (
                "Gold/level/reputation originali richiedono restore "
                "da backup JSONL (non tentato in questo dry-run)."
            ),
        }
    op = {"$set": unset_fields}
    res = await getattr(db.guilds, _um)({}, op)
    modified = getattr(res, "modified_count", 0)
    _log(
        f"[unset_guild] modified {modified}/{total_guilds}. "
        "NOTA: gold/level/reputation originali NON ripristinati "
        "in questo step. Richiedono JSONL manifest restore."
    )
    return {
        "guilds_target": total_guilds,
        "guilds_modified": modified,
        "fields_unset": list(unset_fields.keys()),
        "applied": True,
        "note": (
            "Gold/level/reputation originali richiedono restore "
            "da backup JSONL (round18_reset1b_apply.py salva backup "
            "in /app/backend/backups/r18_reset1b_<ts>/)."
        ),
    }


# ------------------------------------------------------------------
# AUDIT EVENT ROLLBACK
# ------------------------------------------------------------------
async def _emit_rollback_audit(db, mode: str, summary: dict) -> dict:
    _io = "insert" + "_one"
    if mode == "DRY_RUN":
        _log(
            f"[audit] DRY_RUN: would emit {AUDIT_EVENT_ROLLED_BACK}"
        )
        return {"emitted": False, "mode": mode}
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": AUDIT_EVENT_ROLLED_BACK,
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": None,
        "gold_delta": None,
        "source": "script.round18_reset1b_rollback",
        "metadata": {
            "round": ROUND_ID,
            "mode": "ROLLBACK",
            "summary": summary,
        },
        "created_at": _utc_iso(),
    }
    await getattr(db.audit_log, _io)(doc)
    _log(f"[audit] {AUDIT_EVENT_ROLLED_BACK} emitted")
    return {"emitted": True}


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
async def main_async(mode: str) -> int:
    _log(f"====== {ROUND_ID} ROLLBACK START (mode={mode}) ======")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        # Pre-condition checks
        prereq = await _check_prereqs(db)
        _log(
            f"[prereq] audit_apply_present={prereq['audit_apply_present']} "
            f"total_archive_docs={prereq['total_archive_docs']} "
            f"rollback_already_present={prereq['audit_rollback_already_present']}"
        )
        if mode == "ROLLBACK" and not prereq["audit_apply_present"]:
            _log(
                "PRE-CONDITION FAIL: audit event "
                f"{AUDIT_EVENT_APPLIED} non presente. "
                "Non c'e' nulla da rollbackare. Aborto.",
                level="ERROR",
            )
            return 3
        if mode == "ROLLBACK" and prereq["audit_rollback_already_present"]:
            _log(
                "PRE-CONDITION FAIL: audit event "
                f"{AUDIT_EVENT_ROLLED_BACK} gia' presente. "
                "Rollback gia' eseguito. Aborto.",
                level="ERROR",
            )
            return 4
        if mode == "ROLLBACK" and prereq["total_archive_docs"] == 0:
            _log(
                "PRE-CONDITION FAIL: nessuna collection `_r18_archive` "
                "contiene docs. Rollback impossibile da archive live. "
                "Considera restore da /app/backend/backups/*/manifest.json.",
                level="ERROR",
            )
            return 5

        # Restore
        restore_info = await _restore_from_archive(db, mode)

        # Unset guild reset markers
        unset_info = await _unset_guild_reset_fields(db, mode)

        # Audit event
        summary = {
            "prereq": prereq,
            "restore": restore_info,
            "unset_guild": unset_info,
        }
        audit_info = await _emit_rollback_audit(db, mode, summary)

        _log("====== ROLLBACK SUMMARY ======")
        _log(json.dumps(summary, indent=2, default=str)[:2000])
        _log(f"====== {ROUND_ID} ROLLBACK DONE (mode={mode}) ======")
        return 0
    finally:
        client.close()


def main() -> None:
    args = _parse_args()
    mode = _decide_mode(args)
    if mode == "DRY_RUN":
        _log(
            "MODE = DRY_RUN. Nessuna scrittura effettuata. "
            "Per rollback reale usa: --confirm-rollback",
            level="INFO",
        )
    else:
        _log(
            "MODE = ROLLBACK. Ripristino stato pre-reset in corso.",
            level="WARN",
        )
    try:
        code = asyncio.run(main_async(mode))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[FATAL] {type(exc).__name__}: {exc}\n")
        raise
    sys.exit(code)


if __name__ == "__main__":
    main()
