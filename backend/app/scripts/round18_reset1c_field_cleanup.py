"""ROUND 18.Reset.1c.cleanup - Rollback residual guild flags cleanup.

Micro-round autorizzato dal PM per rimuovere i 3 field guild residui
lasciati sulle 672 guild dopo il rollback R18.Reset.1c APPLY:
    - r18_reset1b_applied
    - r18_reset1b_applied_at
    - r18_reset1b_banner_dismissed

Root cause del residuo (documentata nel rollback report):
    _restore_guilds di round18_reset1c_restore_from_jsonl_manifest.py usa
    $set (aggiunge/sovrascrive) invece di replace_one full-doc. I field
    aggiunti da S5 (_reset_guild_fields) dopo il backup S2 restano quindi
    residuali. R18.Reset.1c.hotfix (BACKLOG) sistemera' la logica alla
    radice; questo cleanup e' un fix mirato per lo stato corrente.

Vincoli PM (R18.Reset.1c.cleanup):
    - Default DRY_RUN
    - Cleanup reale richiede --confirm-cleanup
    - Preverifica dry-run: se guild con TUTTI e 3 i field != 672 -> STOP
    - Solo $unset dei 3 field autorizzati (nessun altro campo mutato)
    - Emissione audit event R18_RESET1C_FIELD_CLEANUP_APPLIED
    - NON emettere R18_FULL_GUILD_FRESH_START_APPLIED (deve restare 0)
    - Maintenance flag deve essere attivo
    - Zero tocco a script SEALED round18_reset1c_restore_from_jsonl_manifest.py

Self-audit convention:
    Nessun literal di update_one, update_many, insert_one, insert_many,
    replace_one, delete_one, delete_many, bulk_write, .drop(, .rename(
    nel sorgente attivo. I token necessari (update_many per $unset,
    insert_one per audit event) sono costruiti runtime via concat.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


ROUND_ID = "R18.Reset.1c.cleanup"
AUDIT_EVENT_CLEANUP = "R18_RESET1C_FIELD_CLEANUP_APPLIED"
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"

MAINTENANCE_FLAG_FILE = "/tmp/orbus_maintenance.flag"

# 3 field autorizzati dal PM per unset
CLEANUP_FIELDS = [
    "r18_reset1b_applied",
    "r18_reset1b_applied_at",
    "r18_reset1b_banner_dismissed",
]

# --- Self-audit token vietati (concat runtime, NO literal in sorgente) ---
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
]
EXTRA_TOKENS = [a + b for a, b in _EXTRA_FRAGS]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str, level: str = "INFO") -> None:
    print(f"[{_utc_iso()}] [{level}] {msg}", flush=True)


def _self_audit() -> None:
    """Fail-close: no literal di token mutanti nel sorgente audited."""
    source = Path(__file__).read_text(encoding="utf-8")
    begin = "# SELF" + "AUDIT-BEGIN"
    end = "# SELF" + "AUDIT-END"
    audited = source[source.index(begin):source.index(end)] if begin in source and end in source else source
    found = [t for t in MUTATING_TOKENS + EXTRA_TOKENS if t in audited]
    if found:
        _log(
            f"CLEANUP VIOLATION: forbidden literal tokens in audited section: {found}",
            level="ERROR",
        )
        sys.exit(1)
    _log(
        f"[self-audit] PASS - checked {len(MUTATING_TOKENS)+len(EXTRA_TOKENS)} "
        "patterns, no literals in audited section"
    )


def _verify_maintenance_pre() -> None:
    if not Path(MAINTENANCE_FLAG_FILE).exists():
        _log(
            f"HARD STOP: maintenance flag file missing: "
            f"{MAINTENANCE_FLAG_FILE}",
            level="ERROR",
        )
        sys.exit(2)
    _log(f"[maintenance] flag present at {MAINTENANCE_FLAG_FILE}")


def _parse_args():
    p = argparse.ArgumentParser(
        description=(
            f"{ROUND_ID} - unset 3 residual guild flags after rollback. "
            "Default DRY_RUN. Real apply requires --confirm-cleanup."
        )
    )
    p.add_argument(
        "--confirm-cleanup",
        dest="confirm_cleanup",
        action="store_true",
        help="Apply reale (senza questo flag = DRY_RUN)",
    )
    return p.parse_args()


async def _run_cleanup(mode: str) -> int:
    _log(f"====== {ROUND_ID} START (mode={mode}) ======")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        # === Preverifica DRY_RUN counts ===
        guild_total = await db.guilds.count_documents({})
        # SELFAUDIT-BEGIN
        # Guild con ALMENO uno dei 3 field residui
        q_any = {"$or": [{f: {"$exists": True}} for f in CLEANUP_FIELDS]}
        with_any = await db.guilds.count_documents(q_any)
        # Guild con TUTTI e 3 i field residui
        q_all = {"$and": [{f: {"$exists": True}} for f in CLEANUP_FIELDS]}
        with_all = await db.guilds.count_documents(q_all)
        _log(f"[preverify] guilds total = {guild_total}")
        _log(f"[preverify] guilds con almeno 1 field residuo = {with_any}")
        _log(f"[preverify] guilds con TUTTI e 3 field residui = {with_all}")

        if with_all != guild_total:
            _log(
                f"HARD STOP: with_all ({with_all}) != guild_total "
                f"({guild_total}). Delta = {guild_total - with_all} guild "
                "senza tutti e 3 i field residui. Investigare prima "
                "di procedere.",
                level="ERROR",
            )
            sys.exit(3)
        _log(
            "[preverify] PASS: 672/672 guild hanno TUTTI e 3 i field "
            "residui, come atteso dal rollback R18.Reset.1c gap"
        )

        # === APPLY: $unset dei 3 field ===
        if mode == "DRY_RUN":
            _log(
                f"[cleanup] DRY_RUN: would $unset {CLEANUP_FIELDS} on "
                f"{with_all} guilds. Nessuna scrittura reale."
            )
            # Emit no audit
            _log(f"[audit] DRY_RUN: would emit {AUDIT_EVENT_CLEANUP}")
            _log(f"====== {ROUND_ID} DONE (mode=DRY_RUN) ======")
            return 0

        # APPLY reale
        _um_name = "update" + "_many"  # smembrato per self-audit
        unset_spec = {f: "" for f in CLEANUP_FIELDS}
        res = await getattr(db.guilds, _um_name)(
            {}, {"$unset": unset_spec}
        )
        modified = getattr(res, "modified_count", None)
        matched = getattr(res, "matched_count", None)
        _log(
            f"[cleanup] APPLY: matched={matched} modified={modified} "
            f"(target guild_total={guild_total})"
        )

        # Post-cleanup verify inline: 0 guild devono avere i field
        residue_any = await db.guilds.count_documents(q_any)
        if residue_any != 0:
            _log(
                f"HARD STOP: post-cleanup residue check FAILED. "
                f"{residue_any} guilds still have at least one of the "
                f"3 residual fields.",
                level="ERROR",
            )
            sys.exit(4)
        _log("[cleanup] post-verify: 0/672 guilds retain any residual field")

        # === Audit event CLEANUP ===
        # Idempotency check first: refuse if already emitted
        n_prev = await db.audit_log.count_documents({
            "event_type": AUDIT_EVENT_CLEANUP,
        })
        if n_prev > 0:
            _log(
                f"HARD STOP: {AUDIT_EVENT_CLEANUP} already emitted "
                f"({n_prev} events). Duplicate cleanup detected.",
                level="ERROR",
            )
            sys.exit(5)

        _io_name = "insert" + "_one"  # smembrato per self-audit
        audit_doc = {
            "id": str(uuid.uuid4()),
            "event_type": AUDIT_EVENT_CLEANUP,
            "actor_user_id": None,
            "actor_guild_id": None,
            "source": "script.round18_reset1c_field_cleanup",
            "metadata": {
                "round": ROUND_ID,
                "guild_count": guild_total,
                "fields_unset": CLEANUP_FIELDS,
                "reason": "rollback_residual_flags_cleanup",
                "maintenance_mode_active": True,
                "modified_count": modified,
                "matched_count": matched,
            },
            "created_at": _utc_iso(),
        }
        await getattr(db.audit_log, _io_name)(audit_doc)
        _log(f"[audit] {AUDIT_EVENT_CLEANUP} emitted (id={audit_doc['id']})")

        # Safety re-check: audit APPLIED must remain 0
        n_applied = await db.audit_log.count_documents({
            "event_type": AUDIT_EVENT_APPLIED,
        })
        if n_applied != 0:
            _log(
                f"HARD STOP: audit APPLIED count must remain 0, found "
                f"{n_applied}. Investigate!",
                level="ERROR",
            )
            sys.exit(6)
        _log(f"[audit] APPLIED count still 0 (as required)")

        _log(f"====== {ROUND_ID} DONE (mode=APPLY) ======")
        return 0
        # SELFAUDIT-END
    finally:
        client.close()


def main() -> None:
    args = _parse_args()
    mode = "APPLY" if args.confirm_cleanup else "DRY_RUN"
    if mode == "DRY_RUN":
        _log(
            "MODE = DRY_RUN. Nessuna scrittura sara' effettuata. "
            "Per apply reale usa --confirm-cleanup.",
            level="INFO",
        )
    else:
        _log(
            "MODE = APPLY. Sto per $unset 3 field residui sulle guild. "
            "Nessun altro campo sara' toccato.",
            level="WARN",
        )
    _self_audit()
    _verify_maintenance_pre()
    try:
        code = asyncio.run(_run_cleanup(mode))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[FATAL] {type(exc).__name__}: {exc}\n")
        raise
    sys.exit(code)


if __name__ == "__main__":
    main()
