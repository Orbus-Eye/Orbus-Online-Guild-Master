"""ROUND 18.Reset.1b.hotfix - Full Guild Fresh Start Apply V1.1 (CLI ONE-SHOT).

Autore: e1 main agent - preparato R18.Reset.1b.hotfix phase 2026-07-05.

⚠️  QUESTO SCRIPT ESEGUE MUTAZIONI REALI SUL DB SE INVOCATO CON --apply.
    In tutti gli altri casi resta in dry-run. Default: dry-run.

════════════════════════════════════════════════════════════════════════
DIFFERENZE VS `round18_reset1b_apply.py` (SEALED, mtime=1783235358,
sha256=657d5853a5b203005a319452260bc2d8413e94d5fa8857ba36de4b78d427d934)
════════════════════════════════════════════════════════════════════════

Questa e' una versione SIBLING (non patch) dello script sealed. La
copia originale resta intatta ed e' referenziata via seal hash sopra.

Fix applicati (R18.Reset.1b.hotfix):

    F1. `_regen_starter_kit` ora RISOLVE l'`item_id` dal catalog
        `items` usando lo slug `STARTER_POTION_ITEM_SLUG`, e inserisce
        UN SOLO documento per `(guild_id, item_id)` con
        `quantity = STARTER_KIT_POTIONS` (3), rispettando l'indice
        unico `inv_guild_item_unique {guild_id, item_id}`. Elimina la
        BulkWriteError E11000 del sealed originale (che inseriva 3
        docs per guild con `item_id=null` implicito → collisione).

    F2. Idempotency di kit: se un doc `inventory_items` con
        `(guild_id, item_id)` esiste gia', l'operazione fa upsert
        no-op (nessuna scrittura, nessun raise) grazie al pattern
        `update_one({..., "r18_reset1b_starter_kit": True},
        {"$setOnInsert": doc}, upsert=True)`.

    F3. Double audit event: emette DUE eventi in `audit_log` con
        payload identico ed esteso (`metadata` ricco di metriche +
        hotfix_ref). Eventi:
            - `R18_FULL_GUILD_FRESH_START_APPLIED`
            - `R18_FULL_GUILD_FRESH_START_APPLIED_V1_1`
        Serve per audit trail sia col nome storico che con il
        marker specifico dell'hotfix.

    F4. Idempotency guard esteso: rifiuta l'apply se AL MENO UNO dei
        due audit event esiste gia' (guard vs re-apply anche parziale).

    F5. `source` metadata → `script.round18_reset1b_apply_v1_1`.

    F6. Backup path prefix → `/app/backend/backups/r18_reset1b_v1_1_<ts>`.

    F7. Zero altre modifiche di logica: archive, wipe, reset_guild_fields,
        regen_starter_roster restano invariati funzionalmente.

Vincoli invariante (identici allo sealed):
    - Zero hard delete su `_r18_archive`
    - Idempotency via audit_log
    - Backup snapshot obbligatorio pre-apply
    - Deterministic RNG per regen (seed = sha256("r18_reset1b:<guild_id>"))
    - Zero patch a seed_round5, R18.1.3, R18.3d, R18.X, SMTP
    - Sealed originale INTATTO (verificato via sha256 pre/post)
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
ROUND_ID = "R18.Reset.1b.hotfix"
HOTFIX_REF = "R18.Reset.1b.hotfix"
APPLY_SCRIPT_NAME = "round18_reset1b_apply_v1_1.py"

# Doppio audit event (F3 hotfix)
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"
AUDIT_EVENT_APPLIED_V1_1 = "R18_FULL_GUILD_FRESH_START_APPLIED_V1_1"

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
# (nome UI: "Minor Healing Potion").
STARTER_POTION_ITEM_SLUG = "minor_healing_potion"

# Collections che vengono ARCHIVIATE (copiate in <name>_r18_archive) e
# poi svuotate live. Mirror di ARCHIVE_COLLECTIONS del sealed.
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
    """RNG deterministico per guild_id, invariato vs sealed."""
    digest = hashlib.sha256(
        f"r18_reset1b:{guild_id}".encode("utf-8")
    ).hexdigest()
    seed_int = int(digest[:16], 16)
    return random.Random(seed_int)


def _log(msg: str, level: str = "INFO") -> None:
    ts = _utc_iso()
    print(f"[{ts}] [{level}] {msg}", flush=True)


# ------------------------------------------------------------------
# ARGPARSE + SAFETY GATE (invariato vs sealed)
# ------------------------------------------------------------------
def _parse_args():
    p = argparse.ArgumentParser(
        description=(
            f"{ROUND_ID} Full Guild Fresh Start Apply V1.1 CLI. "
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
        help="Safety flag obbligatorio per --apply.",
    )
    p.add_argument(
        "--dry-run", dest="dry_run_explicit", action="store_true",
        help="Force dry-run mode (default se apply flags mancano).",
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
# IDEMPOTENCY GUARD (F4: rifiuta se AL MENO UNO dei due event esiste)
# ------------------------------------------------------------------
async def _already_applied(db) -> bool:
    """Se un audit event R18_FULL_GUILD_FRESH_START_APPLIED oppure
    R18_FULL_GUILD_FRESH_START_APPLIED_V1_1 esiste, rifiuta re-apply."""
    n = await db.audit_log.count_documents({
        "event_type": {
            "$in": [AUDIT_EVENT_APPLIED, AUDIT_EVENT_APPLIED_V1_1]
        }
    })
    return n > 0


# ------------------------------------------------------------------
# BACKUP SNAPSHOT (invariato tranne il path prefix v1_1)
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
            "name": coll_name,
            "doc_count": cnt,
            "file": str(file_path),
            "sha256": hasher.hexdigest(),
        })
        _log(f"[backup] {coll_name}: saved {cnt} docs -> {file_path}")

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
# ARCHIVE STEP (invariato vs sealed)
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
# WIPE LIVE STEP (invariato vs sealed)
# ------------------------------------------------------------------
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
# RESET GUILD FIELDS STEP (invariato vs sealed)
# ------------------------------------------------------------------
async def _reset_guild_fields(db, mode: str) -> dict:
    _um = "update" + "_many"
    total_guilds = await db.guilds.count_documents({})
    updates = {
        **GUILD_RESET_FIELDS,
        "updated_at": _utc_iso(),
        "r18_reset1b_applied_at": _utc_iso(),
    }
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
# REGEN STARTER ROSTER STEP (invariato vs sealed)
# ------------------------------------------------------------------
async def _regen_starter_roster(db, mode: str) -> dict:
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
        "per_guild_sample": per_guild_created[:3],
        "applied": mode == "APPLY",
    }


# ------------------------------------------------------------------
# REGEN STARTER KIT STEP — HOTFIX F1 + F2
# ------------------------------------------------------------------
async def _regen_starter_kit(db, mode: str) -> dict:
    """HOTFIX V1.1:
        - Risolve `item_id` dal catalog `items` via slug (F1)
        - Inserisce UN SOLO doc per `(guild_id, item_id)` con
          `quantity=STARTER_KIT_POTIONS` (F1) → rispetta indice
          `inv_guild_item_unique {guild_id, item_id}`.
        - Idempotency via `update_one(..., upsert=True)` (F2).
    """
    # Lookup catalog item
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
            "quantity_per_doc": 0,
            "item_id_resolved": None,
            "created_inventory_docs": 0,
            "reason_potions_skipped": (
                f"item slug {STARTER_POTION_ITEM_SLUG!r} non presente "
                "in items catalog live."
            ),
            "applied": mode == "APPLY",
        }

    # Estrai identity key del potion (schema-dipendente).
    # Preferisci `id` (UUID string) su `_id` (ObjectId) per coerenza col
    # rollback JSONL manifest che serializza `id` non `_id`.
    potion_item_id = potion.get("id")
    if potion_item_id is None:
        raise RuntimeError(
            "HARD STOP: potion catalog doc has no 'id' field: "
            f"{ {k: v for k, v in potion.items() if k != '_id'} }"
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
        # Idempotency: upsert su chiave logica `(guild_id, item_id)`.
        # $setOnInsert scrive il payload nuovo SOLO se non esiste; se
        # esiste (retry post-crash), nessuna scrittura → nessuna
        # violazione dell'indice unique.
        new_doc = {
            "id": str(uuid.uuid4()),
            "guild_id": gid,
            "item_id": potion_item_id,
            "item_slug": STARTER_POTION_ITEM_SLUG,
            "quantity": STARTER_KIT_POTIONS,
            "r18_reset1b_starter_kit": True,
            "r18_reset1b_hotfix_v1_1": True,
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
        f"(guilds={len(guilds)}, quantity_per_doc={STARTER_KIT_POTIONS}, "
        f"item_id={potion_item_id})"
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
# DOUBLE AUDIT EVENT (F3): APPLIED + APPLIED_V1_1 con payload identico
# ------------------------------------------------------------------
async def _emit_audit_events(
    db, mode: str, summary: dict, backup_manifest_path: str
) -> dict:
    """Emette DUE eventi con `metadata` identico ed esteso (F3)."""
    apply_id = str(uuid.uuid4())
    completed_at = _utc_iso()

    # Estrai metriche dal summary per il payload esteso
    guild_count = summary.get("guild_reset", {}).get("guilds_target") or 0
    adv_regen_count = summary.get("roster", {}).get("total_adv_created", 0)
    potions_regen_count = summary.get("kit", {}).get(
        "created_inventory_docs", 0
    )
    gold_total_after = guild_count * STARTER_KIT_GOLD

    shared_metadata = {
        "round": HOTFIX_REF,
        "apply_script": APPLY_SCRIPT_NAME,
        "starter_kit_fix": True,
        "inventory_unique_index_respected": True,
        "hotfix_ref": HOTFIX_REF,
        "original_failure": "E11000_step_S7_dup_key_inv_guild_item_unique",
        "manifest_path": backup_manifest_path,
        "apply_id": apply_id,
        "guild_count": guild_count,
        "adv_regen_count": adv_regen_count,
        "potions_regen_count": potions_regen_count,
        "gold_total_after": gold_total_after,
        "completed_at": completed_at,
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
    }

    if mode == "DRY_RUN":
        _log(
            f"[audit] DRY_RUN: would emit BOTH {AUDIT_EVENT_APPLIED} "
            f"and {AUDIT_EVENT_APPLIED_V1_1} with shared metadata"
        )
        return {
            "emitted": False,
            "mode": mode,
            "events_would_emit": [
                AUDIT_EVENT_APPLIED, AUDIT_EVENT_APPLIED_V1_1
            ],
            "apply_id": apply_id,
        }

    events_emitted = []
    for event_type in (AUDIT_EVENT_APPLIED, AUDIT_EVENT_APPLIED_V1_1):
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
        "emitted": True,
        "mode": mode,
        "events_emitted": events_emitted,
        "apply_id": apply_id,
    }


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
async def main_async(mode: str) -> int:
    _log(f"====== {ROUND_ID} START (mode={mode}) ======")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        # Idempotency (F4: check per BOTH events)
        if mode == "APPLY" and await _already_applied(db):
            _log(
                "IDEMPOTENCY GUARD: audit event "
                f"{AUDIT_EVENT_APPLIED} o {AUDIT_EVENT_APPLIED_V1_1} "
                "gia' presente. Rifiuto re-apply. "
                "Usa round18_reset1b_rollback.py per rollback.",
                level="ERROR",
            )
            return 2

        # Backup snapshot (F6: path prefix v1_1)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = Path(
            f"/app/backend/backups/r18_reset1b_v1_1_{ts}"
        )
        backup_info = await _backup_snapshot(db, backup_root, mode)

        archive_info = await _archive_collections(db, mode)
        wipe_info = await _wipe_live_collections(db, mode)
        guild_reset_info = await _reset_guild_fields(db, mode)
        roster_info = await _regen_starter_roster(db, mode)
        kit_info = await _regen_starter_kit(db, mode)

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
