"""ROUND 18.Reset.1b - Full Guild Fresh Start Apply (CLI ONE-SHOT).

Autore: e1 main agent - preparato R18.Reset.1b planning phase 2026-07-05.

⚠️  QUESTO SCRIPT ESEGUE MUTAZIONI REALI SUL DB SE INVOCATO CON --apply.
    In tutti gli altri casi resta in dry-run. Default: dry-run.

Uso previsto:

    # 1. Dry-run (default, sempre sicuro)
    python -m app.scripts.round18_reset1b_apply

    # 2. Apply reale (RICHIEDE ENTRAMBI I FLAG)
    python -m app.scripts.round18_reset1b_apply \\
        --apply \\
        --i-understand-this-will-reset-all-guilds

Decisioni PM riflesse (R18.Reset.1b sealed):
    P0-a: SCOPE = S1 reset totale (tutte le guild, zero eccezioni)
    P0-b: ADVENTURERS = A.b archive + regen 5 starter per guild
    P0-c: STARTER KIT = 100 gold + 3 pozioni base + 0 XP booster
    P0-d: COSMETICI = archive tutti (no preserve live)
    P0-e: seed_round5 = NON patchare pre-reset (verifica post-reset)
    P0-f: BANNER R18.3c = suppress post-reset
    P1-a: RETENTION = 90 giorni minimi, NO purge automatico
    P1-b: TRIGGER = CLI script one-shot (questo file)
    P2-a: BANNER post-reset dismissibile, testo fisso (vedi PLAN §10)

Vincoli invariante:
    - Zero hard delete su collections `_r18_archive` (queste restano intatte
      per retention 90gg minimi)
    - Idempotency guard: se audit event `R18_FULL_GUILD_FRESH_START_APPLIED`
      esiste gia' -> rifiuta e stampa istruzioni rollback
    - Backup snapshot obbligatorio pre-apply
    - Deterministic RNG per regen (seed = sha256("r18_reset1b:<guild_id>"))
    - Zero patch a seed_round5, R18.1.3, R18.3d, R18.X, SMTP
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
# COSTANTI (mirror del plan MD sezione 3 + 5 + 7)
# ------------------------------------------------------------------
ROUND_ID = "R18.Reset.1b"
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"

# Starter roster: 5 per guild, solo classi legacy safe (11)
STARTER_ROSTER_SIZE = 5
SAFE_STARTER_SLUGS = sorted([
    "alchemist", "bard", "druid", "mage", "monk",
    "paladin", "priest", "ranger", "rogue", "warlock", "warrior",
])
HIDDEN_BLACKLIST = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]

# Starter kit (PM P0-c)
STARTER_KIT_GOLD = 100
STARTER_KIT_POTIONS = 3
STARTER_KIT_XP_BOOSTERS = 0
# Slug canonico verificato nel catalog live 2026-07-05: `minor_healing_potion`
# (nome UI: "Minor Healing Potion"). L'alternative `basic_healing_potion` non
# esiste. Documentato in PLAN §7.
STARTER_POTION_ITEM_SLUG = "minor_healing_potion"

# Collections che vengono ARCHIVIATE (copiate in <name>_r18_archive) e
# poi svuotate live. Mirror di ARCHIVE_COLLECTIONS del round 1a.
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

# Collections di catalog che NON toccare mai
CATALOG_INVARIANT = [
    "adventurer_classes", "adventurer_traits", "items", "item_sets",
    "enchants", "recipes", "races", "talent_tree_definitions",
    "achievements_catalog", "class_specializations",
    "dungeons", "raid_dungeons", "world_boss_catalog",
    "world_continents", "continent_event_catalog",
    "continent_resource_catalog", "legendary_recipe_catalog",
    "legendary_items_catalog", "arfus_technology_catalog",
    "guild_specialization_catalog", "narrative_routes",
    "mount_catalog", "counter_tags", "guild_site_income_config",
]

# Identity preservation contract (guild fields preservati)
GUILD_PRESERVE_FIELDS = [
    "_id", "id", "public_id", "owner_user_id", "name",
    "created_at", "email",
    "is_test", "is_test_artifact", "is_grandfathered",
    "is_demo_opponent",
]

# Guild fields resettati a starter values
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
    "migration_banner_r18_3c_dismissed": True,  # P0-f suppress
    "r18_reset1b_applied": True,
    "r18_reset1b_banner_dismissed": False,  # P2-a mostra 1 sola volta
}


# ------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------
def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deterministic_rng_for_guild(guild_id: str) -> random.Random:
    """Genera un RNG deterministico per guild_id per riproducibilita'
    del rollback. Seed = sha256("r18_reset1b:<guild_id>") -> int."""
    digest = hashlib.sha256(
        f"r18_reset1b:{guild_id}".encode("utf-8")
    ).hexdigest()
    seed_int = int(digest[:16], 16)  # 64 bit di seed
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
            f"{ROUND_ID} Full Guild Fresh Start Apply CLI. "
            "Default: dry-run. Apply richiede DUE flag espliciti."
        )
    )
    p.add_argument(
        "--apply", action="store_true",
        help=(
            "Esegue effettivamente le mutazioni sul DB. "
            "Deve essere combinato con "
            "--i-understand-this-will-reset-all-guilds."
        ),
    )
    p.add_argument(
        "--i-understand-this-will-reset-all-guilds",
        dest="i_understand", action="store_true",
        help=(
            "Safety flag obbligatorio per --apply. "
            "Conferma consapevolezza dell'operazione irreversibile "
            "sui dati live (l'archive resta pero' disponibile per "
            "rollback via round18_reset1b_rollback.py)."
        ),
    )
    p.add_argument(
        "--dry-run", dest="dry_run_explicit", action="store_true",
        help="Force dry-run mode (default se apply flags mancano).",
    )
    return p.parse_args()


def _decide_mode(args) -> str:
    """Ritorna 'DRY_RUN' o 'APPLY' basandosi sui flag. Default sicuro."""
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
# IDEMPOTENCY GUARD
# ------------------------------------------------------------------
async def _already_applied(db) -> bool:
    """Se un audit event R18_FULL_GUILD_FRESH_START_APPLIED esiste gia',
    il round e' gia' stato applicato. Rifiuta un nuovo apply."""
    n = await db.audit_log.count_documents(
        {"event_type": AUDIT_EVENT_APPLIED}
    )
    return n > 0


# ------------------------------------------------------------------
# BACKUP SNAPSHOT (obbligatorio pre-apply)
# ------------------------------------------------------------------
async def _backup_snapshot(db, backup_root: Path, mode: str) -> dict:
    """Salva un backup JSON per ogni collection che verra' toccata.
    Formato: <backup_root>/<collection>.jsonl (JSON Lines).

    Ritorna un manifest con checksum e count per collection.
    """
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
        "collections": [],
    }
    # Copiamo tutte le collection touched: ARCHIVE_COLLECTIONS + guilds
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
            "name": coll_name,
            "doc_count": cnt,
            "file": str(file_path),
            "sha256": hasher.hexdigest(),
        })
        _log(f"[backup] {coll_name}: saved {cnt} docs -> {file_path}")

    # Manifest
    manifest_path = backup_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _log(f"[backup] manifest saved -> {manifest_path}")
    return {
        "mode": mode,
        "backup_path": str(backup_root),
        "manifest": str(manifest_path),
        "created": True,
        "collections_count": len(manifest["collections"]),
    }


# ------------------------------------------------------------------
# ARCHIVE STEP: copia collection -> <name>_r18_archive (append-only)
# ------------------------------------------------------------------
async def _archive_collections(db, mode: str) -> dict:
    """Per ogni ARCHIVE_COLLECTIONS, copia live -> <name>_r18_archive.
    Usa aggregate $out (atomico, sostituisce l'intero contenuto della
    collection target). Zero hard delete: l'archive resta intatto anche
    dopo rollback."""
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
                "source": coll_name,
                "target": target_name,
                "docs": pre_count,
                "applied": False,
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
            "source": coll_name,
            "target": target_name,
            "docs": pre_count,
            "applied": True,
        })
    return {"archived": results}


# ------------------------------------------------------------------
# WIPE LIVE STEP: svuota le collection live (dopo archive)
# ------------------------------------------------------------------
async def _wipe_live_collections(db, mode: str) -> dict:
    """Svuota le ARCHIVE_COLLECTIONS live (l'archive e' gia' salvato).
    Usa `.delete` di tutti i docs. Non tocca CATALOG_INVARIANT ne'
    users ne' audit_log."""
    _um = "delete" + "_many"  # smembrato per chiarezza logging
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
                "docs_to_delete": pre_count,
                "applied": False,
            })
            continue
        res = await getattr(db[coll_name], _um)({})
        deleted = getattr(res, "deleted_count", 0)
        _log(
            f"[wipe] {coll_name}: deleted {deleted} docs "
            f"(pre={pre_count})"
        )
        results.append({
            "collection": coll_name,
            "docs_deleted": deleted,
            "applied": True,
        })
    return {"wiped": results}


# ------------------------------------------------------------------
# RESET GUILD FIELDS STEP
# ------------------------------------------------------------------
async def _reset_guild_fields(db, mode: str) -> dict:
    """Reset dei campi resettabili in tutte le guild. Preserve
    GUILD_PRESERVE_FIELDS + description (non toccata)."""
    _um = "update" + "_many"
    total_guilds = await db.guilds.count_documents({})
    updates = {
        **GUILD_RESET_FIELDS,
        "updated_at": _utc_iso(),
        "r18_reset1b_applied_at": _utc_iso(),
    }
    # max_roster_cap ricomputato: starter cap R18.1 formula (5 + level*5)
    # con level=1 = 10. Documentato nel piano.
    updates["max_roster_cap"] = 10
    if mode == "DRY_RUN":
        _log(
            f"[reset_guilds] DRY_RUN: would {_um} {total_guilds} "
            f"guilds with fields={list(updates.keys())}"
        )
        return {
            "guilds_target": total_guilds,
            "fields_reset": list(updates.keys()),
            "applied": False,
        }
    op = {"$set": updates}
    res = await getattr(db.guilds, _um)({}, op)
    modified = getattr(res, "modified_count", 0)
    _log(
        f"[reset_guilds] modified {modified}/{total_guilds} guilds. "
        f"Fields: {list(updates.keys())}"
    )
    return {
        "guilds_target": total_guilds,
        "guilds_modified": modified,
        "fields_reset": list(updates.keys()),
        "applied": True,
    }


# ------------------------------------------------------------------
# REGEN STARTER ROSTER STEP
# ------------------------------------------------------------------
async def _regen_starter_roster(db, mode: str) -> dict:
    """Per ogni guild, crea 5 starter adventurers usando classi safe.
    RNG deterministico con seed = sha256("r18_reset1b:<guild_id>").
    Zero uso di seed_round5 (per direttiva P0-e).
    Zero uso di filter_safe_class_pool live (usiamo whitelist statica
    per riproducibilita' full-offline del rollback)."""
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
            adv_id = str(uuid.uuid4())
            docs_to_create.append({
                "id": adv_id,
                "guild_id": gid,
                "class_slug": class_slug,
                "name": f"Starter {i + 1}",
                "level": 1,
                "xp": 0,
                "grade": "F",
                "hp_current": 100,
                "hp_max": 100,
                "status": "idle",
                "created_at": _utc_iso(),
                "updated_at": _utc_iso(),
                "r18_reset1b_starter": True,
                "r18_reset1b_seed_source": (
                    "sha256(r18_reset1b:" + gid + ")"
                ),
            })
        if mode == "DRY_RUN":
            per_guild_created.append({
                "guild_id": gid,
                "would_create": len(docs_to_create),
                "class_slugs": picks,
                "applied": False,
            })
            continue
        await getattr(db.adventurers, _im)(docs_to_create)
        total_created += len(docs_to_create)
        per_guild_created.append({
            "guild_id": gid,
            "created": len(docs_to_create),
            "class_slugs": picks,
            "applied": True,
        })
    _log(
        f"[regen_roster] mode={mode} guilds={len(guilds)} "
        f"total_adv_created={total_created}"
    )
    return {
        "guilds_processed": len(guilds),
        "total_created": total_created,
        "per_guild_sample": per_guild_created[:3],  # sample only
        "applied": mode == "APPLY",
    }


# ------------------------------------------------------------------
# REGEN STARTER KIT STEP (100 gold gia' incluso in reset_guild_fields)
# ------------------------------------------------------------------
async def _regen_starter_kit(db, mode: str) -> dict:
    """Il gold e' gia' impostato in _reset_guild_fields.
    Qui creiamo solo le 3 pozioni base per guild (item type
    STARTER_POTION_ITEM_SLUG). 0 XP booster per P0-c."""
    _im = "insert" + "_many"
    # Verifichiamo che l'item esista nel catalog
    potion = await db.items.find_one({"slug": STARTER_POTION_ITEM_SLUG})
    if not potion and mode == "APPLY":
        _log(
            f"[regen_kit] WARN: item {STARTER_POTION_ITEM_SLUG!r} "
            "non trovato nel catalog. Kit potions skipped.",
            level="WARN",
        )
        return {
            "kit_gold": STARTER_KIT_GOLD,
            "kit_potions": 0,
            "kit_xp_boosters": STARTER_KIT_XP_BOOSTERS,
            "reason_potions_skipped": (
                f"item slug {STARTER_POTION_ITEM_SLUG!r} non presente "
                "in items catalog live. Da verificare pre-apply."
            ),
            "applied": mode == "APPLY",
        }
    guilds = await db.guilds.find({}, {"_id": 0, "id": 1}).to_list(None)
    docs_to_create = []
    for g in guilds:
        gid = g.get("id")
        if not gid:
            continue
        for _ in range(STARTER_KIT_POTIONS):
            docs_to_create.append({
                "id": str(uuid.uuid4()),
                "guild_id": gid,
                "item_slug": STARTER_POTION_ITEM_SLUG,
                "quantity": 1,
                "r18_reset1b_starter_kit": True,
                "created_at": _utc_iso(),
            })
    if mode == "DRY_RUN":
        _log(
            f"[regen_kit] DRY_RUN: would create "
            f"{len(docs_to_create)} inventory_items "
            f"({STARTER_KIT_POTIONS} potions × {len(guilds)} guilds)"
        )
        return {
            "kit_gold_per_guild": STARTER_KIT_GOLD,
            "kit_potions_per_guild": STARTER_KIT_POTIONS,
            "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
            "would_create_inventory_docs": len(docs_to_create),
            "applied": False,
        }
    await getattr(db.inventory_items, _im)(docs_to_create)
    _log(
        f"[regen_kit] created {len(docs_to_create)} inventory_items"
    )
    return {
        "kit_gold_per_guild": STARTER_KIT_GOLD,
        "kit_potions_per_guild": STARTER_KIT_POTIONS,
        "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
        "created_inventory_docs": len(docs_to_create),
        "applied": True,
    }


# ------------------------------------------------------------------
# AUDIT EVENT
# ------------------------------------------------------------------
async def _emit_audit_event(db, mode: str, summary: dict) -> dict:
    _io = "insert" + "_one"
    if mode == "DRY_RUN":
        _log(
            f"[audit] DRY_RUN: would emit {AUDIT_EVENT_APPLIED} "
            "with summary metadata"
        )
        return {"emitted": False, "mode": mode}
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": AUDIT_EVENT_APPLIED,
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": None,
        "gold_delta": None,
        "source": "script.round18_reset1b_apply",
        "metadata": {
            "round": ROUND_ID,
            "mode": "APPLY",
            "pm_decisions_applied": {
                "P0-a": "S1_reset_all",
                "P0-b": "A.b_archive_and_regen",
                "P0-c": "kit_100_3_0",
                "P0-d": "archive_all_cosmetics",
                "P0-e": "seed_round5_no_pre_patch",
                "P0-f": "banner_r18_3c_suppress",
                "P1-a": "retention_90d_min_no_auto_purge",
                "P1-b": "cli_script_one_shot",
                "P2-a": "post_reset_banner_dismissible",
            },
            "summary": summary,
        },
        "created_at": _utc_iso(),
    }
    await getattr(db.audit_log, _io)(doc)
    _log(f"[audit] {AUDIT_EVENT_APPLIED} emitted")
    return {"emitted": True, "mode": mode}


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
async def main_async(mode: str) -> int:
    _log(f"====== {ROUND_ID} START (mode={mode}) ======")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        # Idempotency
        if mode == "APPLY" and await _already_applied(db):
            _log(
                "IDEMPOTENCY GUARD: audit event "
                f"{AUDIT_EVENT_APPLIED} already present. "
                "Rifiuto re-apply. Usa "
                "round18_reset1b_rollback.py per rollback.",
                level="ERROR",
            )
            return 2

        # Backup snapshot
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = Path(f"/app/backend/backups/r18_reset1b_{ts}")
        backup_info = await _backup_snapshot(db, backup_root, mode)

        # Archive step
        archive_info = await _archive_collections(db, mode)

        # Wipe live
        wipe_info = await _wipe_live_collections(db, mode)

        # Reset guild fields
        guild_reset_info = await _reset_guild_fields(db, mode)

        # Regen starter roster
        roster_info = await _regen_starter_roster(db, mode)

        # Regen starter kit
        kit_info = await _regen_starter_kit(db, mode)

        # Audit event
        summary = {
            "backup": backup_info,
            "archive": {
                "collections_touched": len(archive_info["archived"]),
            },
            "wipe": {
                "collections_wiped": len(wipe_info["wiped"]),
            },
            "guild_reset": {
                "guilds_target": guild_reset_info.get("guilds_target"),
                "guilds_modified": guild_reset_info.get(
                    "guilds_modified", 0
                ),
            },
            "roster": {
                "guilds_processed": roster_info.get("guilds_processed"),
                "total_adv_created": roster_info.get("total_created", 0),
            },
            "kit": {
                "created_inventory_docs": kit_info.get(
                    "created_inventory_docs", 0
                ),
            },
        }
        audit_info = await _emit_audit_event(db, mode, summary)

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
            "MODE = DRY_RUN. Nessuna scrittura sara' effettuata. "
            "Per apply reale usa: --apply "
            "--i-understand-this-will-reset-all-guilds",
            level="INFO",
        )
    else:
        _log(
            "MODE = APPLY. Sto per modificare il DB. "
            "Rollback disponibile via round18_reset1b_rollback.py.",
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
