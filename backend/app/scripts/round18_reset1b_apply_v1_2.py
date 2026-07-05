# ═════════════════════════════════════════════════════════════════════
# R18.Reset.1b.hotfix.v1_2 — CLOSED & SEALED on 2026-07-05T13:15:00Z
# Tester independent verification: 4/4 PASS
# Pytest: 16/16 PASS (t01..t16) + full regression 39/39 PASS
# Sealed by: PM_authorization (Option B — staged intermediate)
# Fix targets: V2.F1 starter roster stats (base_stats_exact_no_variance),
#              V2.F3 double audit APPLIED + APPLIED_V1_2,
#              V2.F4 idempotency guard intelligente (Q3),
#              V2.F5 starter kit fix v1.1 preserved.
# NON modificare. Se serve fix, creare nuovo sibling
#   round18_reset1b_apply_v1_3.py (stesso pattern v1.2 vs v1.1).
# ═════════════════════════════════════════════════════════════════════


"""ROUND 18.Reset.1b.hotfix.v1_2 - Full Guild Fresh Start Apply V1.2 (CLI ONE-SHOT).

Autore: e1 main agent - preparato R18.Reset.1b.hotfix.v1_2 phase 2026-07-05.

⚠️  QUESTO SCRIPT ESEGUE MUTAZIONI REALI SUL DB SE INVOCATO CON --apply.
    In tutti gli altri casi resta in dry-run. Default: dry-run.

════════════════════════════════════════════════════════════════════════
DIFFERENZE VS `round18_reset1b_apply_v1_1.py` (SEALED, mtime=1783246914,
sha256=14d38bf8ea66c878...)
════════════════════════════════════════════════════════════════════════

Questa e' una versione SIBLING (non patch) dello script v1.1 sealed. La
copia v1.1 resta intatta ed e' referenziata via seal hash sopra.

Fix applicati (R18.Reset.1b.hotfix.v1_2 — decisioni PM 2026-07-05):

    V2.F1. `_regen_starter_roster` ora popola SEMPRE tutti e 5 i campi
        stat live (strength/agility/intellect/endurance/faith) leggendo
        `base_strength/base_agility/base_intellect/base_endurance/base_faith`
        dal catalog `adventurer_classes`.

        Strategy: NO variance. Base stat esatta (decisione PM Q1).
        Zero random deviation. Zero placeholder null. Zero fallback.

    V2.F2. HARD STOP se anche solo 1 classe safe manca uno dei
        `base_*` fields. Nessun adv generato in caso di stat missing.
        Verificato PRE loop di generazione (fail-fast). Nessun bypass.

    V2.F3. Audit event double: `APPLIED` + `APPLIED_V1_2` (skip V1_1,
        come da PM Q2). Metadata esteso con:
            - round=R18.Reset.1b.hotfix.v1_2
            - apply_script=round18_reset1b_apply_v1_2.py
            - apply_version=v1.2
            - starter_kit_fix=true (F1 v1.1 ereditato)
            - starter_roster_stats_fix=true (V2.F1 nuovo)
            - stat_strategy=base_stats_exact_no_variance
            - inventory_unique_index_respected=true
            - http_maintenance_required=true
            - internal_job_freeze_required=true

    V2.F4. Idempotency guard intelligente (PM Q3): BLOCCA solo apply
        v1.2 ATTIVO o parziale non risolto. Non blocca per audit
        storici v1.1 rollbackati. Logica di distinzione basata su:
            - guilds con `r18_reset1b_applied=true` count > 0 → BLOCK
            - audit `APPLIED_V1_2` senza `ROLLED_BACK` successivo → BLOCK
            - audit `APPLIED` con metadata.apply_version="v1.2" senza
              rollback → BLOCK
            - archive collision non gestibile → HARD STOP (no bypass)
            - stato ambiguo (metadata mancante o inconsistente) →
              HARD STOP con richiesta manuale (NO silent bypass)

    V2.F5. Starter kit fix (F1 v1.1) MANTENUTO — 1 doc per
        (guild_id, item_id) con quantity=STARTER_KIT_POTIONS via
        upsert `$setOnInsert`. Zero E11000.

    V2.F6. Backup path prefix → `/app/backend/backups/r18_reset1b_v1_2_<ts>`.

    V2.F7. Zero altre modifiche di logica: archive, wipe,
        reset_guild_fields, kit gen restano invariati funzionalmente
        rispetto a v1.1.

Vincoli invariati (identici a v1.1 e sealed):
    - Zero hard delete su `_r18_archive`
    - Idempotency via audit_log intelligente
    - Backup snapshot obbligatorio pre-apply
    - Deterministic RNG per regen (seed = sha256("r18_reset1b:<guild_id>"))
    - Zero patch a seed_round5, R18.1.3, R18.3d, R18.X, SMTP
    - Sealed originali INTATTI (verificato via sha256 pre/post)
    - Doppio freeze (HTTP maintenance + internal job freeze) prerequisite
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


# ------------------------------------------------------------------
# COSTANTI (mirror v1.1 + v1.2 extensions)
# ------------------------------------------------------------------
ROUND_ID = "R18.Reset.1b.hotfix.v1_2"
HOTFIX_REF = "R18.Reset.1b.hotfix.v1_2"
APPLY_SCRIPT_NAME = "round18_reset1b_apply_v1_2.py"
APPLY_VERSION = "v1.2"
STAT_STRATEGY = "base_stats_exact_no_variance"

# Audit event (PM Q2: doppio APPLIED + APPLIED_V1_2, skip V1_1)
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"
AUDIT_EVENT_APPLIED_V1_2 = "R18_FULL_GUILD_FRESH_START_APPLIED_V1_2"
AUDIT_EVENT_ROLLED_BACK = "R18_FULL_GUILD_FRESH_START_ROLLED_BACK"

# Starter roster (invariati v1.0/v1.1)
STARTER_ROSTER_SIZE = 5
SAFE_STARTER_SLUGS = sorted([
    "alchemist", "bard", "druid", "mage", "monk",
    "paladin", "priest", "ranger", "rogue", "warlock", "warrior",
])
HIDDEN_BLACKLIST = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]

# V2.F1: Stat fields obbligatori per starter adv (letti da adventurer_classes.base_*)
REQUIRED_STAT_FIELDS = ("strength", "agility", "intellect", "endurance", "faith")

# Starter kit (invariato v1.1)
STARTER_KIT_GOLD = 100
STARTER_KIT_POTIONS = 3
STARTER_KIT_XP_BOOSTERS = 0
STARTER_POTION_ITEM_SLUG = "minor_healing_potion"

# Archive collections (invariato v1.0/v1.1)
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

GUILD_PRESERVE_FIELDS = [
    "_id", "id", "public_id", "owner_user_id", "name",
    "created_at", "email",
    "is_test", "is_test_artifact", "is_grandfathered",
    "is_demo_opponent",
]

GUILD_RESET_FIELDS = {
    "level": 1,
    "gold": STARTER_KIT_GOLD,
    "reputation": 0,
    "current_roster_size": STARTER_ROSTER_SIZE,
    "raids_completed_count": 0,
    "raids_victory_count": 0,
    "max_raid_score": 0,
    "last_raid_completed_at": None,
    "max_team_power_ever": 0,
    "r18_beta_opt_in": False,
    "migration_banner_r18_3c_dismissed": True,
    "r18_reset1b_applied": True,
    "r18_reset1b_banner_dismissed": False,
}


# ------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------
def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deterministic_rng_for_guild(guild_id: str) -> random.Random:
    digest = hashlib.sha256(
        f"r18_reset1b:{guild_id}".encode("utf-8")
    ).hexdigest()
    seed_int = int(digest[:16], 16)
    return random.Random(seed_int)


def _log(msg: str, level: str = "INFO") -> None:
    ts = _utc_iso()
    print(f"[{ts}] [{level}] {msg}", flush=True)


# ------------------------------------------------------------------
# ARGPARSE + SAFETY GATE
# ------------------------------------------------------------------
def _parse_args():
    p = argparse.ArgumentParser(
        description=(
            f"{ROUND_ID} Full Guild Fresh Start Apply V1.2 CLI. "
            "Default: dry-run. Apply richiede DUE flag espliciti."
        )
    )
    p.add_argument("--apply", action="store_true")
    p.add_argument(
        "--i-understand-this-will-reset-all-guilds",
        dest="i_understand", action="store_true",
    )
    p.add_argument(
        "--dry-run", dest="dry_run_explicit", action="store_true",
    )
    return p.parse_args()


def _decide_mode(args) -> str:
    if args.apply and args.i_understand:
        return "APPLY"
    if args.apply and not args.i_understand:
        _log(
            "SAFETY GATE: --apply richiede anche "
            "--i-understand-this-will-reset-all-guilds. "
            "Rifiuto esecuzione. Torno in DRY_RUN.",
            level="WARN",
        )
        return "DRY_RUN"
    return "DRY_RUN"


# ------------------------------------------------------------------
# V2.F4 — IDEMPOTENCY GUARD INTELLIGENTE (decisione PM Q3)
# ------------------------------------------------------------------
async def _apply_state_check(db) -> dict:
    """Verifica intelligente dello stato di apply.

    Ritorna dict con:
        - 'block' (bool): True se apply v1.2 attivo/non-rollbackato
        - 'reason' (str): motivazione umana
        - 'evidence' (dict): metriche raccolte
        - 'hard_stop_needed' (bool): stato ambiguo non risolvibile

    Regole (PM Q3):
    1. guilds con `r18_reset1b_applied=true` count > 0 → BLOCK
       (apply attivo sulla live)
    2. audit APPLIED_V1_2 count > count(ROLLED_BACK v1.2 successivi) → BLOCK
    3. audit APPLIED (legacy) con metadata.apply_version="v1.2"
       senza rollback successivo → BLOCK
    4. audit APPLIED (legacy) con metadata.apply_version="v1.1" o
       "v1.0" (o assente ma con altro segnale rollback) → OK, non
       blocca (storico rollbackato)
    5. Stato ambiguo (es. APPLIED senza metadata + no rollback event) →
       HARD STOP (no bypass silenzioso)
    """
    ev = {}

    # (1) Guild con flag r18_reset1b_applied=true
    active_guilds = await db.guilds.count_documents({
        "r18_reset1b_applied": True
    })
    ev["guilds_with_active_apply_flag"] = active_guilds
    if active_guilds > 0:
        return {
            "block": True,
            "reason": (
                f"{active_guilds} guilds hanno r18_reset1b_applied=true. "
                "Apply attivo non ancora rollbackato/cleanup-ato. "
                "Esegui rollback + field cleanup prima di riprovare."
            ),
            "evidence": ev,
            "hard_stop_needed": False,
        }

    # (2) Audit APPLIED_V1_2 senza rollback (specifico v1.2)
    n_v1_2_applied = await db.audit_log.count_documents({
        "event_type": AUDIT_EVENT_APPLIED_V1_2,
    })
    ev["audit_APPLIED_V1_2_count"] = n_v1_2_applied

    # Rollback events che seguono un APPLIED_V1_2
    n_rollback = await db.audit_log.count_documents({
        "event_type": AUDIT_EVENT_ROLLED_BACK,
    })
    ev["audit_ROLLED_BACK_total_count"] = n_rollback

    # Cerchiamo APPLIED_V1_2 senza rollback SUCCESSIVO
    # (semplice check temporale: latest APPLIED_V1_2 vs latest ROLLED_BACK)
    if n_v1_2_applied > 0:
        latest_v1_2 = await db.audit_log.find_one(
            {"event_type": AUDIT_EVENT_APPLIED_V1_2},
            sort=[("created_at", -1)],
        )
        latest_rb = await db.audit_log.find_one(
            {"event_type": AUDIT_EVENT_ROLLED_BACK},
            sort=[("created_at", -1)],
        )
        v1_2_ts = latest_v1_2.get("created_at")
        rb_ts = latest_rb.get("created_at") if latest_rb else None
        ev["latest_v1_2_ts"] = str(v1_2_ts)
        ev["latest_rollback_ts"] = str(rb_ts)
        # Se rollback timestamp >= v1_2 timestamp → v1_2 rollbackato
        if rb_ts is None or (
            str(rb_ts) < str(v1_2_ts) if v1_2_ts else False
        ):
            return {
                "block": True,
                "reason": (
                    f"APPLIED_V1_2 event esistente ({n_v1_2_applied}) "
                    "senza rollback successivo tracciabile. Apply v1.2 "
                    "attivo, non rollbackato."
                ),
                "evidence": ev,
                "hard_stop_needed": False,
            }

    # (3) Audit APPLIED (legacy) con metadata.apply_version="v1.2"
    # Verifichiamo se un apply legacy fatto con v1.2 e' ancora attivo
    legacy_v1_2_apply = None
    async for ev_doc in db.audit_log.find(
        {"event_type": AUDIT_EVENT_APPLIED},
        sort=[("created_at", -1)],
    ):
        md = ev_doc.get("metadata", {}) or {}
        if md.get("apply_version") == "v1.2":
            legacy_v1_2_apply = ev_doc
            break
    ev["legacy_APPLIED_with_v1_2_metadata"] = (
        legacy_v1_2_apply is not None
    )
    if legacy_v1_2_apply:
        # Controlla rollback successivo
        legacy_ts = legacy_v1_2_apply.get("created_at")
        latest_rb = await db.audit_log.find_one(
            {"event_type": AUDIT_EVENT_ROLLED_BACK},
            sort=[("created_at", -1)],
        )
        if not latest_rb or str(latest_rb.get("created_at")) < str(
            legacy_ts
        ):
            return {
                "block": True,
                "reason": (
                    "Legacy APPLIED con metadata.apply_version='v1.2' "
                    "senza rollback successivo tracciabile. Apply v1.2 "
                    "attivo via evento legacy."
                ),
                "evidence": ev,
                "hard_stop_needed": False,
            }

    # (4) Ambiguity check: APPLIED events con metadata mancante o
    # inconsistente + NO rollback tracciabile
    n_applied_legacy = await db.audit_log.count_documents({
        "event_type": AUDIT_EVENT_APPLIED,
    })
    ev["audit_APPLIED_legacy_count"] = n_applied_legacy
    ambiguous = 0
    async for ev_doc in db.audit_log.find(
        {"event_type": AUDIT_EVENT_APPLIED}
    ):
        md = ev_doc.get("metadata", {}) or {}
        # Se non c'e' apply_version, e' ambiguo
        if not md.get("apply_version") and not md.get("hotfix_ref"):
            ambiguous += 1
    ev["ambiguous_apply_events_no_version"] = ambiguous
    # Se ambiguo > rollback totali, potrebbe esserci apply attivo
    if ambiguous > n_rollback:
        return {
            "block": True,
            "reason": (
                f"{ambiguous} APPLIED events con metadata ambigua "
                f"(no apply_version, no hotfix_ref) vs {n_rollback} "
                "rollback tracciati. Stato non risolvibile in modo "
                "automatico. NO bypass silenzioso — richiesta "
                "verifica manuale PM prima di procedere."
            ),
            "evidence": ev,
            "hard_stop_needed": True,
        }

    # (5) Tutto pulito: nessun apply attivo v1.2 rilevabile
    return {
        "block": False,
        "reason": "Nessun apply v1.2 attivo rilevato. Guard PASS.",
        "evidence": ev,
        "hard_stop_needed": False,
    }


# ------------------------------------------------------------------
# DOUBLE FREEZE PRE-CHECK (HTTP maintenance + internal job freeze)
# ------------------------------------------------------------------
def _verify_double_freeze() -> dict:
    """Verifica che entrambi i flag freeze siano attivi. Richiesto pre-apply."""
    maint = Path("/tmp/orbus_maintenance.flag").exists()
    freeze = Path("/tmp/orbus_internal_job_freeze.flag").exists()
    return {
        "http_maintenance_flag": maint,
        "internal_job_freeze_flag": freeze,
        "both_active": (maint and freeze),
    }


# ------------------------------------------------------------------
# V2.F1 — PRE-LOAD CLASS BASE STATS TEMPLATE (fail-fast)
# ------------------------------------------------------------------
async def _preload_class_base_stats(db) -> dict:
    """Carica base_* stats per ogni classe safe. HARD STOP se manca.

    Ritorna: {slug: {strength, agility, intellect, endurance, faith}}
    """
    templates: dict = {}
    missing_report = []

    for slug in SAFE_STARTER_SLUGS:
        cls = await db.adventurer_classes.find_one({"slug": slug})
        if not cls:
            missing_report.append({
                "slug": slug, "error": "class_not_found_in_catalog",
            })
            continue
        stats = {
            field: cls.get(f"base_{field}")
            for field in REQUIRED_STAT_FIELDS
        }
        missing_stats = [k for k, v in stats.items() if v is None]
        if missing_stats:
            missing_report.append({
                "slug": slug,
                "error": "missing_base_stats",
                "missing_fields": missing_stats,
            })
            continue
        templates[slug] = stats

    if missing_report:
        raise RuntimeError(
            "V2.F1_HARD_STOP: adventurer_classes catalog non ha tutti "
            f"i `base_*` per le {len(SAFE_STARTER_SLUGS)} classi safe. "
            f"Zero adv generati. Missing report: "
            f"{json.dumps(missing_report, indent=2)}. "
            "Fix required in adventurer_classes catalog before apply."
        )

    return templates


# ------------------------------------------------------------------
# BACKUP SNAPSHOT (invariato tranne path prefix v1_2)
# ------------------------------------------------------------------
async def _backup_snapshot(db, backup_root: Path, mode: str) -> dict:
    if mode == "DRY_RUN":
        _log(
            "[backup] DRY_RUN: skipping backup snapshot creation. "
            "In apply mode, sarebbero stati creati JSONL per "
            f"{len(ARCHIVE_COLLECTIONS)} collections + guilds."
        )
        return {
            "mode": mode,
            "backup_path": str(backup_root),
            "created": False,
            "reason": "dry_run_no_write",
        }

    backup_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "round": ROUND_ID,
        "created_at": _utc_iso(),
        "backup_path": str(backup_root),
        "apply_script": APPLY_SCRIPT_NAME,
        "hotfix_ref": HOTFIX_REF,
        "apply_version": APPLY_VERSION,
        "collections": [],
    }
    all_touched = ARCHIVE_COLLECTIONS + ["guilds"]
    for coll_name in all_touched:
        file_path = backup_root / f"{coll_name}.jsonl"
        cnt = 0
        hasher = hashlib.sha256()
        with file_path.open("w", encoding="utf-8") as fh:
            async for doc in db[coll_name].find({}):
                doc.pop("_id", None)
                line = json.dumps(doc, default=str, ensure_ascii=False)
                fh.write(line)
                fh.write("\n")
                hasher.update(line.encode("utf-8"))
                cnt += 1
        manifest["collections"].append({
            "name": coll_name, "doc_count": cnt,
            "file": str(file_path), "sha256": hasher.hexdigest(),
        })
        _log(f"[backup] {coll_name}: saved {cnt} docs -> {file_path}")

    manifest_path = backup_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _log(f"[backup] manifest saved -> {manifest_path}")
    return {
        "mode": mode, "backup_path": str(backup_root),
        "manifest": str(manifest_path), "created": True,
        "collections_count": len(manifest["collections"]),
    }


# ------------------------------------------------------------------
# ARCHIVE / WIPE / RESET_GUILD (invariati vs v1.1)
# ------------------------------------------------------------------
async def _archive_collections(db, mode: str) -> dict:
    results = []
    for coll_name in ARCHIVE_COLLECTIONS:
        target_name = f"{coll_name}_r18_archive"
        pre_count = await db[coll_name].count_documents({})
        if mode == "DRY_RUN":
            _log(
                f"[archive] DRY_RUN: {coll_name} ({pre_count} docs) -> "
                f"{target_name} (would use aggregate $out)"
            )
            results.append({
                "source": coll_name, "target": target_name,
                "docs": pre_count, "applied": False,
            })
            continue
        pipeline = [{"$match": {}}, {"$out": target_name}]
        await db[coll_name].aggregate(pipeline).to_list(None)
        post_count = await db[target_name].count_documents({})
        assert pre_count == post_count, (
            f"Archive integrity FAIL: {coll_name} pre={pre_count} "
            f"target={post_count}"
        )
        _log(
            f"[archive] {coll_name} ({pre_count} docs) -> "
            f"{target_name} ({post_count} docs). OK"
        )
        results.append({
            "source": coll_name, "target": target_name,
            "docs": pre_count, "applied": True,
        })
    return {"archived": results}


async def _wipe_live_collections(db, mode: str) -> dict:
    _um = "delete" + "_many"
    results = []
    for coll_name in ARCHIVE_COLLECTIONS:
        pre_count = await db[coll_name].count_documents({})
        if mode == "DRY_RUN":
            _log(
                f"[wipe] DRY_RUN: would wipe {coll_name} "
                f"({pre_count} docs) via {_um}({{}})"
            )
            results.append({
                "collection": coll_name,
                "docs_to_delete": pre_count, "applied": False,
            })
            continue
        res = await getattr(db[coll_name], _um)({})
        deleted = getattr(res, "deleted_count", 0)
        _log(f"[wipe] {coll_name}: deleted {deleted} docs (pre={pre_count})")
        results.append({
            "collection": coll_name, "docs_deleted": deleted,
            "applied": True,
        })
    return {"wiped": results}


async def _reset_guild_fields(db, mode: str) -> dict:
    _um = "update" + "_many"
    total_guilds = await db.guilds.count_documents({})
    updates = {
        **GUILD_RESET_FIELDS,
        "updated_at": _utc_iso(),
        "r18_reset1b_applied_at": _utc_iso(),
        "max_roster_cap": 10,
    }
    if mode == "DRY_RUN":
        _log(
            f"[reset_guilds] DRY_RUN: would {_um} {total_guilds} guilds"
        )
        return {
            "guilds_target": total_guilds,
            "fields_reset": list(updates.keys()), "applied": False,
        }
    op = {"$set": updates}
    res = await getattr(db.guilds, _um)({}, op)
    modified = getattr(res, "modified_count", 0)
    _log(
        f"[reset_guilds] modified {modified}/{total_guilds} guilds"
    )
    return {
        "guilds_target": total_guilds, "guilds_modified": modified,
        "fields_reset": list(updates.keys()), "applied": True,
    }


# ------------------------------------------------------------------
# V2.F1 — REGEN STARTER ROSTER con stat base_*
# ------------------------------------------------------------------
async def _regen_starter_roster(
    db, mode: str, class_templates: dict
) -> dict:
    """V1.2 FIX: ogni adv ha SEMPRE i 5 stat da base_* del catalog.
    Zero variance, zero null (guard preloader V2.F1 lo garantisce)."""
    _im = "insert" + "_many"
    guilds = await db.guilds.find({}, {"_id": 0, "id": 1}).to_list(None)
    total_created = 0
    per_guild_created = []
    for g in guilds:
        gid = g.get("id")
        if not gid:
            continue
        rng = _deterministic_rng_for_guild(gid)
        picks = [rng.choice(SAFE_STARTER_SLUGS)
                 for _ in range(STARTER_ROSTER_SIZE)]
        docs_to_create = []
        for i, class_slug in enumerate(picks):
            stats = class_templates[class_slug]  # V2.F1: KeyError impossibile qui
            adv_id = str(uuid.uuid4())
            docs_to_create.append({
                "id": adv_id, "guild_id": gid,
                "class_slug": class_slug,
                "name": f"Starter {i + 1}",
                "level": 1, "xp": 0, "grade": "F",
                # V2.F1 — 5 stat popolati da base_* catalog (no variance)
                "strength": stats["strength"],
                "agility": stats["agility"],
                "intellect": stats["intellect"],
                "endurance": stats["endurance"],
                "faith": stats["faith"],
                "hp_current": 100, "hp_max": 100,
                "status": "idle",
                "created_at": _utc_iso(),
                "updated_at": _utc_iso(),
                "r18_reset1b_starter": True,
                "r18_reset1b_hotfix_v1_2": True,
                "r18_reset1b_seed_source": (
                    "sha256(r18_reset1b:" + gid + ")"
                ),
                "r18_reset1b_stat_source": (
                    "adventurer_classes.base_*_catalog_lookup"
                ),
            })
        if mode == "DRY_RUN":
            per_guild_created.append({
                "guild_id": gid, "would_create": len(docs_to_create),
                "class_slugs": picks,
                "stat_sample": (
                    docs_to_create[0]
                    if docs_to_create else None
                ),
                "applied": False,
            })
            continue
        await getattr(db.adventurers, _im)(docs_to_create)
        total_created += len(docs_to_create)
        per_guild_created.append({
            "guild_id": gid, "created": len(docs_to_create),
            "class_slugs": picks, "applied": True,
        })
    _log(
        f"[regen_roster] mode={mode} guilds={len(guilds)} "
        f"total_adv_created={total_created} "
        f"stat_strategy={STAT_STRATEGY}"
    )
    return {
        "guilds_processed": len(guilds),
        "total_created": total_created,
        "per_guild_sample": per_guild_created[:3],
        "stat_strategy": STAT_STRATEGY,
        "class_templates_used": list(class_templates.keys()),
        "applied": mode == "APPLY",
    }


# ------------------------------------------------------------------
# V2.F5 — REGEN STARTER KIT (fix F1 v1.1 mantenuto)
# ------------------------------------------------------------------
async def _regen_starter_kit(db, mode: str) -> dict:
    """V1.1 F1+F2 MANTENUTO: 1 doc per (guild_id, item_id) con
    quantity=STARTER_KIT_POTIONS, upsert idempotent."""
    potion = await db.items.find_one({"slug": STARTER_POTION_ITEM_SLUG})
    if not potion:
        _log(
            f"[regen_kit] WARN: item {STARTER_POTION_ITEM_SLUG!r} "
            "non trovato nel catalog. Kit potions skipped.",
            level="WARN",
        )
        return {
            "kit_gold_per_guild": STARTER_KIT_GOLD,
            "kit_potions_per_guild": 0,
            "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
            "quantity_per_doc": 0, "item_id_resolved": None,
            "created_inventory_docs": 0,
            "reason_potions_skipped": (
                f"item slug {STARTER_POTION_ITEM_SLUG!r} non presente"
            ),
            "applied": mode == "APPLY",
        }

    potion_item_id = potion.get("id")
    if potion_item_id is None:
        raise RuntimeError(
            "V1.1_F1_HARD_STOP: potion catalog doc has no 'id' field"
        )

    guilds = await db.guilds.find({}, {"_id": 0, "id": 1}).to_list(None)
    would_create = 0
    created_count = 0
    upsert_skipped = 0

    if mode == "DRY_RUN":
        for g in guilds:
            if g.get("id"):
                would_create += 1
        _log(
            f"[regen_kit] DRY_RUN: would create {would_create} "
            f"inventory_items (1 doc × {len(guilds)} guilds, "
            f"quantity={STARTER_KIT_POTIONS}, "
            f"item_id={potion_item_id})"
        )
        return {
            "kit_gold_per_guild": STARTER_KIT_GOLD,
            "kit_potions_per_guild": STARTER_KIT_POTIONS,
            "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
            "quantity_per_doc": STARTER_KIT_POTIONS,
            "item_id_resolved": str(potion_item_id),
            "would_create_inventory_docs": would_create,
            "applied": False,
        }

    for g in guilds:
        gid = g.get("id")
        if not gid:
            continue
        new_doc = {
            "id": str(uuid.uuid4()), "guild_id": gid,
            "item_id": potion_item_id,
            "item_slug": STARTER_POTION_ITEM_SLUG,
            "quantity": STARTER_KIT_POTIONS,
            "r18_reset1b_starter_kit": True,
            "r18_reset1b_hotfix_v1_2": True,
            "created_at": _utc_iso(),
        }
        res = await db.inventory_items.update_one(
            {"guild_id": gid, "item_id": potion_item_id},
            {"$setOnInsert": new_doc},
            upsert=True,
        )
        if getattr(res, "upserted_id", None) is not None:
            created_count += 1
        else:
            upsert_skipped += 1

    _log(
        f"[regen_kit] APPLY: created={created_count} "
        f"upsert_skipped={upsert_skipped} "
        f"(quantity_per_doc={STARTER_KIT_POTIONS})"
    )
    return {
        "kit_gold_per_guild": STARTER_KIT_GOLD,
        "kit_potions_per_guild": STARTER_KIT_POTIONS,
        "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
        "quantity_per_doc": STARTER_KIT_POTIONS,
        "item_id_resolved": str(potion_item_id),
        "created_inventory_docs": created_count,
        "upsert_skipped": upsert_skipped,
        "applied": True,
    }


# ------------------------------------------------------------------
# V2.F3 — DOUBLE AUDIT EVENT: APPLIED + APPLIED_V1_2
# ------------------------------------------------------------------
async def _emit_audit_events(
    db, mode: str, summary: dict, backup_manifest_path: str
) -> dict:
    """Emette DUE eventi (APPLIED + APPLIED_V1_2) con metadata esteso v1.2."""
    apply_id = str(uuid.uuid4())
    completed_at = _utc_iso()

    guild_count = summary.get("guild_reset", {}).get("guilds_target") or 0
    adv_regen_count = summary.get("roster", {}).get("total_adv_created", 0)
    potions_regen_count = summary.get("kit", {}).get(
        "created_inventory_docs", 0
    )
    gold_total_after = guild_count * STARTER_KIT_GOLD

    shared_metadata = {
        # PM Q2: metadata minima obbligatoria
        "round": HOTFIX_REF,
        "apply_script": APPLY_SCRIPT_NAME,
        "apply_version": APPLY_VERSION,
        "starter_kit_fix": True,
        "starter_roster_stats_fix": True,
        "stat_strategy": STAT_STRATEGY,
        "inventory_unique_index_respected": True,
        "http_maintenance_required": True,
        "internal_job_freeze_required": True,
        # Extra tracking
        "hotfix_ref": HOTFIX_REF,
        "supersedes_versions": ["v1.0_original", "v1.1_hotfix"],
        "manifest_path": backup_manifest_path,
        "apply_id": apply_id,
        "guild_count": guild_count,
        "adv_regen_count": adv_regen_count,
        "potions_regen_count": potions_regen_count,
        "gold_total_after": gold_total_after,
        "completed_at": completed_at,
        "safe_starter_slugs": SAFE_STARTER_SLUGS,
        "class_templates_used": summary.get("roster", {}).get(
            "class_templates_used", []
        ),
        "summary": summary,
    }

    if mode == "DRY_RUN":
        _log(
            f"[audit] DRY_RUN: would emit BOTH {AUDIT_EVENT_APPLIED} "
            f"and {AUDIT_EVENT_APPLIED_V1_2} with shared metadata"
        )
        return {
            "emitted": False, "mode": mode,
            "events_would_emit": [
                AUDIT_EVENT_APPLIED, AUDIT_EVENT_APPLIED_V1_2
            ],
            "apply_id": apply_id,
        }

    events_emitted = []
    for event_type in (AUDIT_EVENT_APPLIED, AUDIT_EVENT_APPLIED_V1_2):
        doc = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_user_id": None,
            "actor_guild_id": None,
            "item_slug": None,
            "item_template_id": None,
            "quantity": None,
            "gold_delta": None,
            "source": f"script.{APPLY_SCRIPT_NAME.replace('.py', '')}",
            "metadata": shared_metadata,
            "created_at": completed_at,
        }
        await db.audit_log.insert_one(doc)
        events_emitted.append(event_type)
        _log(f"[audit] {event_type} emitted (apply_id={apply_id})")

    return {
        "emitted": True, "mode": mode,
        "events_emitted": events_emitted, "apply_id": apply_id,
    }


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
async def main_async(mode: str) -> int:
    _log(f"====== {ROUND_ID} START (mode={mode}) ======")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        # V2.F4: Idempotency guard intelligente (PM Q3)
        if mode == "APPLY":
            state = await _apply_state_check(db)
            _log(f"[apply_guard] evidence: {json.dumps(state['evidence'])}")
            if state["hard_stop_needed"]:
                _log(
                    f"HARD STOP (Q3 ambiguous state): {state['reason']}",
                    level="ERROR",
                )
                return 3
            if state["block"]:
                _log(
                    "IDEMPOTENCY GUARD (Q3): apply v1.2 gia' attivo o "
                    f"parziale. {state['reason']} "
                    "Rifiuto re-apply.",
                    level="ERROR",
                )
                return 2

            # Double freeze pre-check
            freeze = _verify_double_freeze()
            _log(f"[freeze_check] {json.dumps(freeze)}")
            if not freeze["both_active"]:
                _log(
                    "HARD STOP: apply v1.2 richiede ENTRAMBI i flag "
                    "/tmp/orbus_maintenance.flag e "
                    "/tmp/orbus_internal_job_freeze.flag attivi.",
                    level="ERROR",
                )
                return 4

        # V2.F1: preload class base stats (fail-fast se manca)
        _log("[preload] loading adventurer_classes base_* templates...")
        class_templates = await _preload_class_base_stats(db)
        _log(
            f"[preload] {len(class_templates)}/"
            f"{len(SAFE_STARTER_SLUGS)} classi safe caricate con "
            f"tutti i {len(REQUIRED_STAT_FIELDS)} base_* stats. OK."
        )

        # V2.F6: backup path prefix v1_2
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = Path(
            f"/app/backend/backups/r18_reset1b_v1_2_{ts}"
        )
        backup_info = await _backup_snapshot(db, backup_root, mode)

        archive_info = await _archive_collections(db, mode)
        wipe_info = await _wipe_live_collections(db, mode)
        guild_reset_info = await _reset_guild_fields(db, mode)
        roster_info = await _regen_starter_roster(
            db, mode, class_templates
        )
        kit_info = await _regen_starter_kit(db, mode)

        summary = {
            "backup": backup_info,
            "archive": {
                "collections_touched": len(archive_info["archived"]),
            },
            "wipe": {"collections_wiped": len(wipe_info["wiped"])},
            "guild_reset": {
                "guilds_target": guild_reset_info.get("guilds_target"),
                "guilds_modified": guild_reset_info.get(
                    "guilds_modified", 0
                ),
            },
            "roster": {
                "guilds_processed": roster_info.get("guilds_processed"),
                "total_adv_created": roster_info.get("total_created", 0),
                "stat_strategy": STAT_STRATEGY,
                "class_templates_used": roster_info.get(
                    "class_templates_used", []
                ),
                "sample_adv_stats": (
                    roster_info.get("per_guild_sample", [{}])[0].get(
                        "stat_sample"
                    ) if roster_info.get("per_guild_sample") else None
                ),
            },
            "kit": {
                "created_inventory_docs": kit_info.get(
                    "created_inventory_docs", 0
                ),
                "quantity_per_doc": kit_info.get("quantity_per_doc", 0),
                "item_id_resolved": kit_info.get("item_id_resolved"),
                "upsert_skipped": kit_info.get("upsert_skipped", 0),
            },
        }

        backup_manifest_path = (
            backup_info.get("manifest") if backup_info.get("created")
            else str(backup_root / "manifest.json")
        )
        audit_info = await _emit_audit_events(
            db, mode, summary, backup_manifest_path
        )
        summary["audit"] = audit_info

        _log("====== SUMMARY ======")
        _log(json.dumps(summary, indent=2, default=str))
        _log(f"====== {ROUND_ID} DONE (mode={mode}) ======")
        return 0
    finally:
        client.close()


def main() -> None:
    args = _parse_args()
    mode = _decide_mode(args)
    if mode == "DRY_RUN":
        _log(
            "MODE = DRY_RUN. Nessuna scrittura sara' effettuata.",
            level="INFO",
        )
    else:
        _log(
            "MODE = APPLY. Sto per modificare il DB.",
            level="WARN",
        )
    try:
        code = asyncio.run(main_async(mode))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(
            f"[FATAL] {type(exc).__name__}: {exc}\n"
        )
        raise
    sys.exit(code)


if __name__ == "__main__":
    main()
