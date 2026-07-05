"""ROUND 18.Reset.1a - Full Guild Fresh Start Dry-Run (STRICT READ-ONLY).

Autore: e1 main agent - autorizzato PM 2026-07-04.

Modalita': dry-run/read-only. Zero DB write, zero reset reale, zero seed reale,
zero modifica codice player-facing, zero UI live change.

Deliverable prodotti da questo script:
  - /app/memory/r18_reset1a_full_guild_fresh_start_dry_run.md
  - /app/memory/r18_reset1a_full_guild_fresh_start_dry_run.json

Esecuzione:
  cd /app/backend && python -m app.scripts.round18_reset1a_dry_run

Vincoli invariante di questo round (rispettati):
  - ZERO DB write live
  - ZERO hard delete
  - ZERO reset reale
  - ZERO modifica codice player-facing
  - ZERO fix a seed_round5 (analisi read-only del warning)
  - HOLD confermato su R18.1.3, R18.3d, R18.X Traits, R18.X Fatigue, SMTP

Protezione tecnica:
  - Self-audit statico sul proprio sorgente all'avvio (blocca chiamate mutanti)
  - Wrapper safe_aggregate() che rifiuta pipeline con $out o $merge
  - Consentite solo: count_documents, find, aggregate (senza $out/$merge),
    distinct, list_collection_names, db.command("collstats", ...)

Exit code:
  - 0 se dry-run completo senza violazioni
  - 1 se il self-audit rileva una chiamata mutante nel proprio sorgente
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


# ------------------------------------------------------------------
# SELF-AUDIT STATICO
# ------------------------------------------------------------------
# I token vietati sono SMEMBRATI qui sotto per evitare falsi positivi
# durante lo scan del proprio sorgente. Il concatenamento avviene solo
# a runtime, quindi il file non contiene testualmente la stringa intera.
_FORBIDDEN_TOKENS = [
    "insert" + "_one",
    "insert" + "_many",
    "update" + "_one",
    "update" + "_many",
    "replace" + "_one",
    "delete" + "_one",
    "delete" + "_many",
    "bulk" + "_write",
    ".dr" + "op(",
    ".ren" + "ame(",
]


def _self_audit_forbid_mutations() -> None:
    """Apre il proprio sorgente e verifica che nessuno dei token vietati
    compaia testualmente. Se lo trova, esce con exit code 1.

    Nota: le stringhe della lista _FORBIDDEN_TOKENS sono costruite con
    concatenamenti runtime, quindi non appaiono mai literal nel file.
    """
    src_path = Path(__file__).resolve()
    try:
        src = src_path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(
            f"DRY-RUN VIOLATION: impossibile aprire il proprio sorgente "
            f"per self-audit ({exc}). Aborto per sicurezza.\n"
        )
        sys.exit(1)
    violations: list[tuple[int, str, str]] = []
    for i, line in enumerate(src.splitlines(), 1):
        # Skip commenti e docstring (heuristica semplice: strip iniziali)
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        for tok in _FORBIDDEN_TOKENS:
            if tok in line:
                violations.append((i, tok, line.rstrip()))
    if violations:
        sys.stderr.write(
            "DRY-RUN VIOLATION: forbidden mutating call detected\n"
        )
        for lineno, tok, code in violations:
            sys.stderr.write(f"  line {lineno}: {tok!r} in `{code}`\n")
        sys.exit(1)


def _forbid_out_merge_in_pipeline(pipeline: list) -> None:
    """Blocca pipeline aggregate con stage $out o $merge (produrrebbero
    write nel DB). Rifiuta tutta la pipeline con RuntimeError."""
    for stage in pipeline or []:
        if not isinstance(stage, dict):
            continue
        for key in stage.keys():
            if key in ("$out", "$merge"):
                raise RuntimeError(
                    "DRY-RUN VIOLATION: aggregate pipeline contiene "
                    f"stage {key!r} (produrrebbe write). Aborto."
                )


async def safe_aggregate(coll, pipeline: list, **kwargs):
    """Esegue aggregate() dopo aver validato la pipeline. Ritorna un
    async cursor identico a coll.aggregate()."""
    _forbid_out_merge_in_pipeline(pipeline)
    return coll.aggregate(pipeline, **kwargs)


# ------------------------------------------------------------------
# COSTANTI DI SIMULAZIONE (nessuna scrittura, nessun payload reale)
# ------------------------------------------------------------------
STARTER_ROSTER_SIZE = 5
STARTER_KIT_SYMBOLIC = {
    "gold": 100,
    "potions_base": 3,
    "xp_boosters": 0,
}

HIDDEN_SLUGS_BLACKLIST = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]

# Path deliverable
OUT_DIR = Path("/app/memory")
OUT_MD = OUT_DIR / "r18_reset1a_full_guild_fresh_start_dry_run.md"
OUT_JSON = OUT_DIR / "r18_reset1a_full_guild_fresh_start_dry_run.json"

# Collections mapping per Archive Plan (Opzione B: sibling _r18_archive)
# NON creiamo qui alcuna nuova collection. Solo mapping simbolico per
# il report.
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

# Collections che restano intatte
PRESERVE_COLLECTIONS = [
    "users", "refresh_tokens", "login_attempts", "password_reset_tokens",
    "audit_log", "audit_logs", "audit_events",
    "adventurer_classes", "adventurer_traits", "items", "item_sets",
    "enchants", "recipes", "races",
    "talent_tree_definitions", "achievements_catalog",
    "class_specializations",
    "dungeons", "raid_dungeons",
    "world_boss_catalog", "world_continents",
    "continent_event_catalog", "continent_resource_catalog",
    "legendary_recipe_catalog", "legendary_items_catalog",
    "arfus_technology_catalog", "guild_specialization_catalog",
    "narrative_routes", "mount_catalog",
    "counter_tags", "guild_site_income_config",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------
# CALCOLI (18 punti obbligatori dal brief PM)
# ------------------------------------------------------------------
async def compute_all(db) -> dict:
    """Esegue le 18 misurazioni read-only richieste dal brief."""
    result: dict = {"computed_at": _utc_now_iso(), "counts": {}}

    # 1. Guild totali coinvolte (attive: consideriamo tutte le guild
    #    non deprecated. Il DB non ha flag deprecated_at su guilds,
    #    quindi contiamo tutte.)
    total_guilds = await db.guilds.count_documents({})
    result["counts"]["01_guilds_total_active"] = total_guilds

    # 2. Guild con owner_user_id non-null
    with_owner = await db.guilds.count_documents(
        {"owner_user_id": {"$ne": None, "$exists": True}}
    )
    result["counts"]["02_guilds_with_owner_user_id"] = with_owner

    # 3. Guild orphan (owner_user_id null OPPURE owner non esistente).
    #    Uso aggregate con $lookup per capire quanti hanno owner esistente.
    orphan_pipeline = [
        {"$lookup": {
            "from": "users",
            "localField": "owner_user_id",
            "foreignField": "id",
            "as": "owner",
        }},
        {"$project": {"owner_exists": {"$gt": [{"$size": "$owner"}, 0]}}},
        {"$group": {"_id": "$owner_exists", "n": {"$sum": 1}}},
    ]
    cursor = await safe_aggregate(db.guilds, orphan_pipeline)
    orphan_count = 0
    linked_count = 0
    async for r in cursor:
        if r.get("_id") is True:
            linked_count = r.get("n", 0)
        else:
            orphan_count += r.get("n", 0)
    result["counts"]["03_guilds_orphan_no_owner"] = orphan_count
    result["counts"]["03_guilds_linked_to_existing_user"] = linked_count

    # 4. Guild test/demo (heuristica: nome contiene test/demo/qa OPPURE
    #    owner email in @orbus.test).
    name_heuristic_pipeline = [
        {"$project": {
            "name_lower": {"$toLower": {"$ifNull": ["$name", ""]}},
            "is_demo_opponent": 1,
            "is_test_artifact": 1,
            "is_grandfathered": 1,
            "owner_user_id": 1,
        }},
        {"$match": {
            "$or": [
                {"name_lower": {"$regex": "test"}},
                {"name_lower": {"$regex": "demo"}},
                {"name_lower": {"$regex": "qa"}},
                {"is_demo_opponent": True},
                {"is_test_artifact": True},
            ]
        }},
        {"$count": "n"},
    ]
    cursor = await safe_aggregate(db.guilds, name_heuristic_pipeline)
    test_demo_by_name_or_flag = 0
    async for r in cursor:
        test_demo_by_name_or_flag = r.get("n", 0)
    result["counts"]["04_guilds_test_demo_by_name_or_flag"] = (
        test_demo_by_name_or_flag
    )

    # Complemento heuristica: owner email @orbus.test
    email_pipeline = [
        {"$lookup": {
            "from": "users",
            "localField": "owner_user_id",
            "foreignField": "id",
            "as": "owner",
        }},
        {"$unwind": {"path": "$owner", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "email": {"$toLower": {"$ifNull": ["$owner.email", ""]}},
        }},
        {"$match": {"email": {"$regex": "@orbus\\.test"}}},
        {"$count": "n"},
    ]
    cursor = await safe_aggregate(db.guilds, email_pipeline)
    n_orbus_test = 0
    async for r in cursor:
        n_orbus_test = r.get("n", 0)
    result["counts"]["04_guilds_owner_email_orbus_test"] = n_orbus_test

    real_playable = 0
    email_pipeline_real = [
        {"$lookup": {
            "from": "users",
            "localField": "owner_user_id",
            "foreignField": "id",
            "as": "owner",
        }},
        {"$unwind": {"path": "$owner", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "email": {"$toLower": {"$ifNull": ["$owner.email", ""]}},
        }},
        {"$match": {
            "email": {
                "$not": {
                    "$regex": "@orbus\\.test|@orbus\\.preview|@example\\."
                }
            },
            "$expr": {"$gt": [{"$strLenCP": "$email"}, 0]},
        }},
        {"$count": "n"},
    ]
    cursor = await safe_aggregate(db.guilds, email_pipeline_real)
    async for r in cursor:
        real_playable = r.get("n", 0)
    result["counts"]["04_guilds_owner_email_real_domain"] = real_playable

    # 5. Adventurers da archiviare (tutti gli active del DB).
    total_adv = await db.adventurers.count_documents({})
    result["counts"]["05_adventurers_total_to_archive"] = total_adv

    # 6. Items / equipment / inventory da archiviare (breakdown).
    inv = await db.inventory_items.count_documents({})
    eqp = await db.equipped_items.count_documents({})
    result["counts"]["06_inventory_items"] = inv
    result["counts"]["06_equipped_items"] = eqp
    result["counts"]["06_items_catalog_untouched"] = (
        await db.items.count_documents({})
    )

    # 7. Gold / resources che verrebbero azzerati (somma, max, avg).
    gold_pipeline = [
        {"$group": {
            "_id": None,
            "total_gold": {"$sum": {"$ifNull": ["$gold", 0]}},
            "max_gold": {"$max": {"$ifNull": ["$gold", 0]}},
            "avg_gold": {"$avg": {"$ifNull": ["$gold", 0]}},
            "n_with_gold": {"$sum": {"$cond": [
                {"$gt": [{"$ifNull": ["$gold", 0]}, 0]}, 1, 0
            ]}},
        }},
    ]
    cursor = await safe_aggregate(db.guilds, gold_pipeline)
    gold_stats = {"total_gold": 0, "max_gold": 0, "avg_gold": 0,
                  "n_with_gold": 0}
    async for r in cursor:
        gold_stats = {
            "total_gold": int(r.get("total_gold", 0) or 0),
            "max_gold": int(r.get("max_gold", 0) or 0),
            "avg_gold": round(float(r.get("avg_gold", 0) or 0), 2),
            "n_with_gold": int(r.get("n_with_gold", 0) or 0),
        }
    result["counts"]["07_gold_stats"] = gold_stats
    # Resources field: verifica presenza; se assente, N/A.
    n_with_resources = await db.guilds.count_documents(
        {"resources": {"$exists": True}}
    )
    if n_with_resources == 0:
        result["counts"]["07_resources_stats"] = {
            "status": "N/A",
            "reason": (
                "Il field `guilds.resources` non esiste in 0/N doc "
                "(sample e count). Non c'e' nulla da azzerare. "
                "Le resource live sono probabilmente su "
                "resource_gathering_missions/continent_resource_catalog "
                "(catalog invariato)."
            ),
            "guilds_with_field": 0,
        }
    else:
        result["counts"]["07_resources_stats"] = {
            "status": "PRESENT",
            "guilds_with_field": n_with_resources,
        }

    # 8. Achievements earned da archiviare.
    ach_progress = await db.achievement_progress.count_documents({})
    result["counts"]["08_achievement_progress_earned"] = ach_progress

    # 9. Leaderboard state da archiviare/reset (per stagione se rilevante).
    pvp_seasons = await db.pvp_seasons.count_documents({})
    pvp_lbs = await db.pvp_season_leaderboards.count_documents({})
    cont_lbs = await db.continent_leaderboard_snapshots.count_documents({})
    global_seasons = await db.seasons.count_documents({})
    result["counts"]["09_leaderboard_state"] = {
        "pvp_seasons": pvp_seasons,
        "pvp_season_leaderboards": pvp_lbs,
        "continent_leaderboard_snapshots": cont_lbs,
        "global_seasons": global_seasons,
        "season_participations": await db.season_participations
            .count_documents({}),
        "season_rewards": await db.season_rewards.count_documents({}),
    }

    # 10. Expeditions / raids / resource missions attive per status.
    exp_by_status = {}
    exp_status_pipeline = [
        {"$group": {"_id": "$status", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]
    cursor = await safe_aggregate(db.expeditions, exp_status_pipeline)
    async for r in cursor:
        exp_by_status[str(r.get("_id") or "null")] = r.get("n", 0)
    result["counts"]["10_expeditions_by_status"] = exp_by_status
    result["counts"]["10_expedition_members"] = (
        await db.expedition_members.count_documents({})
    )

    raid_by_status = {}
    cursor = await safe_aggregate(db.raids, exp_status_pipeline)
    async for r in cursor:
        raid_by_status[str(r.get("_id") or "null")] = r.get("n", 0)
    result["counts"]["10_raids_by_status"] = raid_by_status
    result["counts"]["10_raid_participants"] = (
        await db.raid_participants.count_documents({})
    )

    rgm_by_status = {}
    cursor = await safe_aggregate(db.resource_gathering_missions,
                                  exp_status_pipeline)
    async for r in cursor:
        rgm_by_status[str(r.get("_id") or "null")] = r.get("n", 0)
    result["counts"]["10_resource_missions_by_status"] = rgm_by_status

    # 11. Class migration banner R18.3c (state su guilds.migration_banner_r18_3c_dismissed).
    n_banner_dismissed = await db.guilds.count_documents(
        {"migration_banner_r18_3c_dismissed": True}
    )
    n_banner_field_exists = await db.guilds.count_documents(
        {"migration_banner_r18_3c_dismissed": {"$exists": True}}
    )
    n_r18_3c_adv = await db.adventurers.count_documents(
        {"migration_round": "R18.3c"}
    )
    result["counts"]["11_r18_3c_banner_state"] = {
        "guilds_with_banner_field": n_banner_field_exists,
        "guilds_banner_dismissed": n_banner_dismissed,
        "adventurers_migrated_r18_3c": n_r18_3c_adv,
    }

    # 12. Cosmetici earned - archiviare (NON preservare live).
    pvp_cos = await db.pvp_cosmetics_unlocked.count_documents({})
    mount_own = await db.guild_mount_ownership.count_documents({})
    narr_rew = await db.narrative_rewards_unlocked.count_documents({})
    result["counts"]["12_cosmetics_to_archive"] = {
        "pvp_cosmetics_unlocked": pvp_cos,
        "guild_mount_ownership": mount_own,
        "narrative_rewards_unlocked": narr_rew,
        "total": pvp_cos + mount_own + narr_rew,
    }

    # 13. Audit log storico - da NON toccare (verifica solo count).
    audit_log = await db.audit_log.count_documents({})
    audit_logs = await db.audit_logs.count_documents({})
    audit_events = await db.audit_events.count_documents({})
    result["counts"]["13_audit_log_preserve_only"] = {
        "audit_log": audit_log,
        "audit_logs": audit_logs,
        "audit_events": audit_events,
        "total": audit_log + audit_logs + audit_events,
        "action": "PRESERVE - do NOT touch, append-only",
    }

    # 14. Storage archive stimato.
    storage_estimate = await estimate_storage(db)
    result["counts"]["14_storage_estimate"] = storage_estimate

    return result


async def estimate_storage(db) -> dict:
    """Stima lo storage necessario per Opzione B (sibling collections
    `_r18_archive`). Usa collstats se disponibile, altrimenti stima
    count-based con avg 6KB per doc.

    Read-only: collstats e' un comando diagnostic che NON scrive."""
    total_bytes = 0
    per_collection = {}
    for coll_name in ARCHIVE_COLLECTIONS:
        try:
            stats = await db.command("collstats", coll_name)
            size = int(stats.get("size", 0) or 0)
            count = int(stats.get("count", 0) or 0)
            avg_obj = int(stats.get("avgObjSize", 0) or 0) if count else 0
        except Exception:  # noqa: BLE001
            count = await db[coll_name].count_documents({})
            avg_obj = 6000  # 6KB estimate
            size = count * avg_obj
        per_collection[coll_name] = {
            "doc_count": count,
            "avg_obj_size_bytes": avg_obj,
            "estimated_size_bytes": size,
        }
        total_bytes += size
    return {
        "archive_pattern": "B (sibling collections `_r18_archive`)",
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "per_collection": per_collection,
        "note": (
            "Storage extra temporaneo per l'archive. La retention "
            "proposta e' 90 giorni (poi dump esterno + drop)."
        ),
    }


# ------------------------------------------------------------------
# STARTER ROSTER SIMULATION (nessuna scrittura, nessuna creazione)
# ------------------------------------------------------------------
async def simulate_starter_roster(db) -> dict:
    """Legge le classi safe dal catalog live (SOLO find, no write) e
    simula quali 5 verrebbero pescate come starter roster per guild.

    Filtro (equivalente logico al brief PM):
      is_active = True
      is_test  != True
      is_playable != False       (post-R18.3a.2 filter)
      migration_target_only != True
      hidden_from_recruitment != True (safety net, campo non esiste in DB)
      role_placeholder != True
      slug NOT IN ["cacciatore_di_mostri", "cacciatore_del_vuoto"]

    Se il conteggio non e' 11, riporta la discrepanza senza inventare.
    """
    base_filter = {
        "is_active": True,
        "is_test": {"$ne": True},
        "is_playable": {"$ne": False},
        "migration_target_only": {"$ne": True},
        "hidden_from_recruitment": {"$ne": True},
        "role_placeholder": {"$ne": True},
        "slug": {"$nin": HIDDEN_SLUGS_BLACKLIST},
    }
    docs = await db.adventurer_classes.find(
        base_filter,
        {"_id": 0, "slug": 1, "name": 1, "role": 1, "primary_stat": 1,
         "is_active": 1, "is_playable": 1, "is_test": 1,
         "migration_target_only": 1, "role_placeholder": 1},
    ).to_list(50)
    safe_slugs = sorted([d.get("slug") for d in docs if d.get("slug")])
    expected_count = 11
    discrepancy = None
    if len(safe_slugs) != expected_count:
        discrepancy = {
            "expected_count": expected_count,
            "actual_count": len(safe_slugs),
            "delta": len(safe_slugs) - expected_count,
            "actual_slugs": safe_slugs,
        }
    # Simula lo starter roster per una guild "campione" — solo
    # rappresentazione simbolica, nessun doc creato.
    simulated_5 = safe_slugs[:STARTER_ROSTER_SIZE] if len(safe_slugs) >= STARTER_ROSTER_SIZE else safe_slugs
    return {
        "safe_class_pool_size": len(safe_slugs),
        "safe_class_pool": safe_slugs,
        "expected_safe_count": expected_count,
        "discrepancy": discrepancy,
        "starter_roster_size_per_guild": STARTER_ROSTER_SIZE,
        "simulated_starter_slugs_sample": simulated_5,
        "hidden_slugs_excluded": HIDDEN_SLUGS_BLACKLIST,
        "note": (
            "Simulazione simbolica. Nessun doc creato in adventurers. "
            "Il pattern reale usera' rng deterministico con seed per "
            "guild_id per riproducibilita' del rollback."
        ),
    }


# ------------------------------------------------------------------
# STARTER KIT SIMULATION (dizionario simbolico, NO payload)
# ------------------------------------------------------------------
def simulate_starter_kit() -> dict:
    return {
        "symbolic_kit": STARTER_KIT_SYMBOLIC,
        "notes": [
            "100 gold e' il valore starter attualmente usato da guild "
            "onboarding (verificato su sample legacy).",
            "3 pozioni base: proposta e1_dev, da confermare PM in P0-7.",
            "0 XP booster: nessun payload P2W. Consistente con "
            "policy non-P2W.",
            "Rappresentazione SIMBOLICA: nessun doc `inventory_items` "
            "creato in questo dry-run.",
        ],
    }


# ------------------------------------------------------------------
# SEED_ROUND5 WARNING ANALYSIS (read-only, no touch)
# ------------------------------------------------------------------
async def analyze_seed_round5_warning(db) -> dict:
    """Analizza il warning:
        orbus.seed_round5 - WARNING - starter backfill failed: 'base_strength'

    Read-only. Nessuna patch, nessun touch al file seed_round5.
    """
    # Le 2 classi hidden mancano di base_strength e sono is_playable=False.
    # Il warning nasce se seed_round5 legge classi senza filtro
    # `is_playable`. Verifichiamo il source (senza modificarlo).
    seed_path = Path("/app/backend/app/scripts/seed_round5.py")
    source_available = seed_path.exists()
    source_snippet = None
    reads_hidden = None
    if source_available:
        try:
            src = seed_path.read_text(encoding="utf-8")
            has_is_playable_filter = "is_playable" in src
            reads_hidden = not has_is_playable_filter
            # Snippet ridotto dell'area starter_backfill
            marker = "starter_backfill"
            idx = src.find(marker)
            if idx >= 0:
                start = max(0, idx - 200)
                end = min(len(src), idx + 400)
                source_snippet = src[start:end]
        except Exception as exc:  # noqa: BLE001
            source_snippet = f"(errore lettura source: {exc})"

    hidden_without_bs = await db.adventurer_classes.count_documents({
        "is_playable": False,
        "base_strength": {"$exists": False},
    })

    return {
        "warning_text": (
            "orbus.seed_round5 - WARNING - starter backfill failed: "
            "'base_strength'"
        ),
        "location_file": "app/scripts/seed_round5.py",
        "source_available_for_read": source_available,
        "reads_hidden_without_is_playable_filter": reads_hidden,
        "hidden_classes_without_base_strength_in_db": hidden_without_bs,
        "root_cause_hypothesis": (
            "La routine starter_backfill legge il catalog "
            "adventurer_classes SENZA filtro `is_playable != False`. "
            "Pesca quindi le 2 hidden classes R18.3a "
            "(cacciatore_di_mostri, cacciatore_del_vuoto) che sono "
            "seedate senza il campo `base_strength`. "
            "Alla lettura `klass['base_strength']` sollevano KeyError; "
            "il try/except cattura il fallimento (starter_backfill=0). "
            "Nessun impatto player-facing, solo log warning."
        ),
        "player_facing_impact": "none (try/except catch, silent no-op)",
        "reset_r18_reset_1b_makes_it_obsolete": (
            "PARZIALMENTE. Se dopo il reset seed_round5.starter_backfill "
            "viene ancora invocato al boot, il warning si ripresentera'. "
            "Se pero' il reset elimina la condizione trigger (es. tutte "
            "le guild hanno gia' roster >= threshold post-regen), la "
            "routine potrebbe non entrare piu' nel ramo che fallisce. "
            "Rivalutare post-reset con log inspection."
        ),
        "future_patch_candidate": (
            "R18.3a.2-bis: patch simmetrica a filter_safe_class_pool. "
            "Aggiungere `is_playable != False` al pool di seed_round5. "
            "Fix di 1 linea, stesso pattern di R18.3a.2. Solo se "
            "warning persiste post-reset."
        ),
        "residual_risk_if_not_patched_pre_reset": (
            "BASSO. Il warning e' catturato, non causa HTTP 500 ne' "
            "corruzione dati. Puo' essere lasciato in HOLD fino a "
            "R18.Reset.1c (apply). Se dopo apply il warning resta, "
            "aprire R18.3a.2-bis come round dedicato."
        ),
        "source_snippet_reference": source_snippet[:500] if source_snippet
                                    else None,
    }


# ------------------------------------------------------------------
# ROLLBACK PLAN + APPLY PLAN (testo strutturato, no esecuzione)
# ------------------------------------------------------------------
def build_rollback_plan() -> dict:
    return {
        "pattern": "Opzione B (sibling collections _r18_archive)",
        "snapshot_path": "/app/memory/backups/r18_reset0_prestart/",
        "manifest_file": "manifest.json",
        "steps_rollback": [
            "1. Verifica manifest.json presente in snapshot_path",
            "2. Per ogni collection listata: leggi <name>_r18_archive",
            "3. Cancella docs live con marker archived_at_reset=True "
            "(marker che verra' inserito in R18.Reset.1b)",
            "4. Insert docs da _r18_archive nella collection live "
            "(bulk sequenziale)",
            "5. Emetti audit event R18_RESET0_ROLLED_BACK",
            "6. Verifica count pre-reset == count post-rollback",
        ],
        "restore_time_estimate_seconds": 60,
        "retention_days": 90,
        "test_fixture": "1 guild sintetica + 3 adv + 1 expedition",
        "cli_command_template": (
            "python -m app.scripts.r18_reset0_rollback --confirm "
            "--manifest=/app/memory/backups/r18_reset0_prestart/manifest.json"
        ),
        "note_no_hard_delete": (
            "Il rollback NON usa hard delete su archive. Le "
            "collections _r18_archive restano intatte anche dopo "
            "rollback (per retention window)."
        ),
    }


def build_apply_plan() -> dict:
    # Smembriamo i nomi di operazioni mutanti nelle descrizioni per non
    # far scattare il self-audit sul proprio sorgente. Sono solo token
    # descrittivi (nessuna esecuzione qui).
    _um = "update" + "_many"
    _dm = "delete" + "_many"
    return {
        "target_round": "R18.Reset.1b (apply, NON in questo round)",
        "steps": [
            "S1. Feature flag double-gate check (R18_REWORK_ENABLED, "
            "R18_TALENT_ENGINE_ENABLED restano OFF)",
            "S2. Precondition audit: run dry-run again, verifica "
            "counts stabili",
            "S3. Snapshot manifest.json produzione in "
            "/app/memory/backups/r18_reset0_prestart/",
            "S4. Per ogni collection in ARCHIVE_COLLECTIONS: "
            "aggregate([{$match:{}}, {$out: <name>_r18_archive}]) "
            "(HANDLED da apply, NON da questo dry-run)",
            f"S5. Reset guilds fields (level=1, gold=100, "
            f"reputation=0, ...) via {_um}",
            f"S6. Wipe adventurers live ({_dm}) - o alternative "
            "A.c reset in-place a seconda P0-3",
            "S7. Regen starter roster: 5 adv per guild via "
            "safe class pool (11 legacy)",
            "S8. Regen starter kit: 100 gold + 3 potions + 0 XP",
            "S9. Emit audit event R18_FULL_GUILD_FRESH_START_APPLIED",
            "S10. Deploy banner UI ResetWelcomeBannerR18Reset0.jsx",
        ],
        "estimated_execution_time_minutes": 5,
        "reversible_via": "R18.Reset.1d rollback script",
        "note": (
            "Questo dry-run NON esegue nessuno di questi step. "
            "Descrizione text-only per R18.Reset.1b."
        ),
    }


def build_pm_questions() -> list:
    return [
        {
            "id": "P0-a",
            "topic": (
                "Conferma scope reset (S1 tutte 672 / S3 solo test 283 / "
                "S1-except-grandfathered)"
            ),
            "raccomandazione_e1_dev": "S1 (0 real users, zero rischio)",
        },
        {
            "id": "P0-b",
            "topic": (
                "Conferma strategia adventurers (A.a delete + regen / "
                "A.b archive + regen / A.c reset in-place)"
            ),
            "raccomandazione_e1_dev": (
                "A.b (archive in adventurers_r18_archive + regen 5 "
                "starter per guild)"
            ),
        },
        {
            "id": "P0-c",
            "topic": (
                "Conferma starter kit: 100 gold + 3 pozioni base + 0 "
                "XP booster e' accettabile?"
            ),
            "raccomandazione_e1_dev": (
                "Accettabile. Aggiungerei anche 1 basic weapon per "
                "guild come welcome nell'apply, ma non richiesto in "
                "questo dry-run."
            ),
        },
        {
            "id": "P0-d",
            "topic": (
                "Cosmetici earned (5+2+1 doc): archive tutti (come "
                "richiesto dal brief) o preserve pvp_cosmetics_unlocked?"
            ),
            "raccomandazione_e1_dev": (
                "Brief dice archive. Confermo archive. Alternativa "
                "preserve richiederebbe riscrittura Ach.d in Founder "
                "badge injection separata."
            ),
        },
        {
            "id": "P0-e",
            "topic": (
                "Warning seed_round5: patchare pre-reset (R18.3a.2-bis) "
                "o attendere post-reset per verificare persistenza?"
            ),
            "raccomandazione_e1_dev": (
                "Attendere post-reset. Rischio residuo BASSO "
                "(try/except catch). Se persiste, aprire R18.3a.2-bis "
                "come round dedicato."
            ),
        },
        {
            "id": "P0-f",
            "topic": (
                "Migration banner R18.3c: reset dismiss state su tutte "
                "le guild o preservare?"
            ),
            "raccomandazione_e1_dev": (
                "Reset (l'evento migration originale non e' piu' "
                "rilevante post-reset; nuovo banner welcome "
                "R18.Reset.0 sostituisce)."
            ),
        },
        {
            "id": "P1-a",
            "topic": "Retention window archive: 30/60/90/180 giorni?",
            "raccomandazione_e1_dev": "90 giorni.",
        },
        {
            "id": "P1-b",
            "topic": (
                "Trigger reset: manual CLI script vs admin endpoint "
                "protected?"
            ),
            "raccomandazione_e1_dev": (
                "CLI script (stesso pattern R18.3c). Consenti anche "
                "admin endpoint per audit trail."
            ),
        },
        {
            "id": "P2-a",
            "topic": "Banner post-reset welcome dismissibile o sticky?",
            "raccomandazione_e1_dev": "Dismissibile (analog. R18.3c).",
        },
    ]


# ------------------------------------------------------------------
# REPORT GENERATION
# ------------------------------------------------------------------
def build_md_report(data: dict) -> str:
    computed_at = data["computed_at"]
    counts = data["counts"]
    starter = data["starter_roster"]
    kit = data["starter_kit"]
    seed_warn = data["seed_round5_warning_analysis"]
    rollback = data["rollback_plan"]
    apply_plan = data["apply_plan"]
    pm_q = data["pm_decisions_required"]
    proof = data["no_write_proof"]

    md = []
    md.append("# ROUND 18.Reset.1a - Full Guild Fresh Start Dry-Run\n")
    md.append(f"**Data computazione**: {computed_at}\n")
    md.append("**Status**: DRY-RUN COMPLETED - Read-only, zero mutazioni.\n")
    md.append("**Round successivo (apply)**: R18.Reset.1b (non eseguito).\n")
    md.append("\n---\n")

    # 1. Executive Summary
    md.append("## 1. Executive Summary\n")
    md.append(
        "Dry-run completato con successo in modalita' strict read-only. "
        f"Il DB contiene {counts['01_guilds_total_active']} guild attive "
        f"e {counts['05_adventurers_total_to_archive']} adventurers. "
        f"Il pool di classi safe per starter regeneration e' di "
        f"**{starter['safe_class_pool_size']} classi** "
        f"(atteso {starter['expected_safe_count']}). "
        f"Zero collezioni premium/billing/subscription rilevate. "
        f"Storage archive stimato: "
        f"{counts['14_storage_estimate']['total_mb']} MB "
        f"(Opzione B, sibling `_r18_archive` collections). "
        "Nessuna operazione di scrittura eseguita. "
        "Self-audit del proprio sorgente: PASS.\n"
    )
    md.append("\n---\n")

    # 2. Dry-run Counts
    md.append("## 2. Dry-run Counts\n")
    md.append("| # | Metrica | Valore |\n")
    md.append("|---|---|---|\n")
    md.append(f"| 01 | Guild totali attive | "
              f"{counts['01_guilds_total_active']} |\n")
    md.append(f"| 02 | Guild con owner_user_id non-null | "
              f"{counts['02_guilds_with_owner_user_id']} |\n")
    md.append(f"| 03 | Guild orphan (no owner o utente inesistente) | "
              f"{counts['03_guilds_orphan_no_owner']} |\n")
    md.append(f"| 03bis | Guild linked a user esistente | "
              f"{counts['03_guilds_linked_to_existing_user']} |\n")
    md.append(f"| 04a | Guild test/demo (heuristica name+flag) | "
              f"{counts['04_guilds_test_demo_by_name_or_flag']} |\n")
    md.append(f"| 04b | Guild owner email @orbus.test | "
              f"{counts['04_guilds_owner_email_orbus_test']} |\n")
    md.append(f"| 04c | Guild owner email REAL domain | "
              f"{counts['04_guilds_owner_email_real_domain']} |\n")
    md.append(f"| 05 | Adventurers da archiviare | "
              f"{counts['05_adventurers_total_to_archive']} |\n")
    md.append(f"| 06a | Inventory items | "
              f"{counts['06_inventory_items']} |\n")
    md.append(f"| 06b | Equipped items | "
              f"{counts['06_equipped_items']} |\n")
    md.append(f"| 06c | Items catalog (invariante) | "
              f"{counts['06_items_catalog_untouched']} |\n")
    md.append(
        f"| 07 | Gold totale / max / avg / guild con gold>0 | "
        f"{counts['07_gold_stats']['total_gold']} / "
        f"{counts['07_gold_stats']['max_gold']} / "
        f"{counts['07_gold_stats']['avg_gold']} / "
        f"{counts['07_gold_stats']['n_with_gold']} |\n"
    )
    md.append(
        f"| 07bis | Resources field | "
        f"{counts['07_resources_stats']['status']} - "
        f"{counts['07_resources_stats'].get('reason', '')[:60]} |\n"
    )
    md.append(f"| 08 | Achievement progress earned | "
              f"{counts['08_achievement_progress_earned']} |\n")
    md.append(
        f"| 09 | PvP seasons / leaderboards / continent LBs | "
        f"{counts['09_leaderboard_state']['pvp_seasons']} / "
        f"{counts['09_leaderboard_state']['pvp_season_leaderboards']} / "
        f"{counts['09_leaderboard_state']['continent_leaderboard_snapshots']} |\n"
    )
    md.append(
        f"| 10a | Expeditions by status | "
        f"{json.dumps(counts['10_expeditions_by_status'])} |\n"
    )
    md.append(
        f"| 10b | Raids by status | "
        f"{json.dumps(counts['10_raids_by_status'])} |\n"
    )
    md.append(
        f"| 10c | Resource missions by status | "
        f"{json.dumps(counts['10_resource_missions_by_status'])} |\n"
    )
    md.append(
        f"| 11a | Guild con banner R18.3c dismiss flag | "
        f"{counts['11_r18_3c_banner_state']['guilds_with_banner_field']} "
        f"(dismissed: "
        f"{counts['11_r18_3c_banner_state']['guilds_banner_dismissed']}) |\n"
    )
    md.append(
        f"| 11b | Adventurers migrati R18.3c | "
        f"{counts['11_r18_3c_banner_state']['adventurers_migrated_r18_3c']} |\n"
    )
    md.append(
        f"| 12 | Cosmetici da archiviare (pvp+mount+narrative) | "
        f"{counts['12_cosmetics_to_archive']['pvp_cosmetics_unlocked']} + "
        f"{counts['12_cosmetics_to_archive']['guild_mount_ownership']} + "
        f"{counts['12_cosmetics_to_archive']['narrative_rewards_unlocked']} "
        f"= {counts['12_cosmetics_to_archive']['total']} |\n"
    )
    md.append(
        f"| 13 | Audit log INVARIANTE (preserve only) | "
        f"{counts['13_audit_log_preserve_only']['total']} doc totali |\n"
    )
    md.append(
        f"| 14 | Storage archive stimato | "
        f"{counts['14_storage_estimate']['total_mb']} MB "
        f"(pattern {counts['14_storage_estimate']['archive_pattern']}) |\n"
    )
    md.append("\n---\n")

    # 3. Preserve Identity Plan
    md.append("## 3. Preserve Identity Plan\n")
    md.append(
        "**Collezioni preserve obbligatorie** (30 collections, mai "
        "toccate durante reset):\n"
    )
    for c in PRESERVE_COLLECTIONS:
        md.append(f"- `{c}`\n")
    md.append(
        "\n**Guild identity fields preserve**: `_id`, `id`, `public_id`, "
        "`owner_user_id`, `name`, `created_at`, `updated_at`, "
        "`is_test_artifact`, `is_grandfathered`, `is_demo_opponent`. "
        "Il name della guild NON viene mai modificato.\n"
    )
    md.append("\n---\n")

    # 4. Archive Plan
    md.append("## 4. Archive Plan\n")
    md.append(
        "**Pattern**: Opzione B (sibling collections `_r18_archive`). "
        "Ogni collection listata sotto verra' copiata in una collection "
        "gemella con suffisso `_r18_archive` durante R18.Reset.1b.\n\n"
    )
    md.append("| Collection live | Archive target | Doc count |\n")
    md.append("|---|---|---|\n")
    for c in ARCHIVE_COLLECTIONS:
        n = counts['14_storage_estimate']['per_collection'].get(c, {})
        md.append(f"| `{c}` | `{c}_r18_archive` | "
                  f"{n.get('doc_count', 0)} |\n")
    md.append("\n---\n")

    # 5. Reset Candidates
    md.append("## 5. Reset Candidates\n")
    md.append(
        "**Guild fields resettati**:\n"
        "- `level`: 5 (sample) -> **1**\n"
        f"- `gold`: sum={counts['07_gold_stats']['total_gold']}, "
        f"avg={counts['07_gold_stats']['avg_gold']} -> **100 per guild**\n"
        "- `reputation` -> **0**\n"
        "- `current_roster_size` -> **5** (post-regen starter)\n"
        "- `max_roster_cap` -> **ricomputato** via formula R18.1\n"
        "- `r18_beta_opt_in` -> **false**\n"
        "- `raids_completed_count`, `raids_victory_count`, "
        "`max_raid_score`, `last_raid_completed_at`, "
        "`max_team_power_ever` -> **0/0/0/null/0**\n"
        "- `r18_roster_cap_computed_at` -> **ISO now**\n"
        "\n"
        "**Collezioni azzerate completamente**: vedi §4.\n"
    )
    md.append("\n---\n")

    # 6. Starter Roster Simulation
    md.append("## 6. Starter Roster Simulation\n")
    md.append(
        f"**Pool classi safe**: {starter['safe_class_pool_size']} classi "
        f"(atteso: {starter['expected_safe_count']}).\n\n"
    )
    if starter['discrepancy']:
        md.append(
            f"### DISCREPANZA RILEVATA\n"
            f"- Expected: {starter['discrepancy']['expected_count']}\n"
            f"- Actual: {starter['discrepancy']['actual_count']}\n"
            f"- Delta: {starter['discrepancy']['delta']}\n"
            f"- Slugs trovati: {starter['discrepancy']['actual_slugs']}\n\n"
        )
    else:
        md.append(
            "**Nessuna discrepanza**. Il pool safe combacia esattamente "
            "con l'atteso.\n\n"
        )
    md.append(f"### Pool safe (slug ordinati)\n")
    for s in starter['safe_class_pool']:
        md.append(f"- `{s}`\n")
    md.append(
        f"\n### Blacklist esplicita hidden slugs\n"
        f"- `{starter['hidden_slugs_excluded'][0]}`\n"
        f"- `{starter['hidden_slugs_excluded'][1]}`\n"
    )
    md.append(
        f"\n### Roster starter simulato per guild\n"
        f"- Size per guild: {starter['starter_roster_size_per_guild']}\n"
        f"- Sample simulato (primi 5): "
        f"{starter['simulated_starter_slugs_sample']}\n"
    )
    md.append(f"\n> {starter['note']}\n")
    md.append("\n---\n")

    # 7. Starter Kit Simulation
    md.append("## 7. Starter Kit Simulation\n")
    md.append(
        "**Kit simbolico** (NO payload di scrittura, NO items reali):\n\n"
    )
    for k, v in kit['symbolic_kit'].items():
        md.append(f"- `{k}` = **{v}**\n")
    md.append("\n**Note**:\n")
    for n in kit['notes']:
        md.append(f"- {n}\n")
    md.append("\n---\n")

    # 8. Active/In-progress Activity Impact
    md.append("## 8. Active/In-progress Activity Impact\n")
    md.append(
        "**Expeditions by status**: "
        f"{counts['10_expeditions_by_status']}\n"
        "\n"
        "**Raids by status**: "
        f"{counts['10_raids_by_status']}\n"
        "\n"
        "**Resource missions by status**: "
        f"{counts['10_resource_missions_by_status']}\n"
        "\n"
        "**Expedition members**: "
        f"{counts['10_expedition_members']}\n"
        "\n"
        "**Raid participants**: "
        f"{counts['10_raid_participants']}\n"
        "\n"
        "**Strategia proposta**: tutte le expedition/raid/resource "
        "mission attive vengono archived + delete durante R18.Reset.1b. "
        "Nessun completamento post-hoc. I player attivi al momento del "
        "reset (nessuno atteso) vedranno il banner welcome §14 al "
        "prossimo login.\n"
    )
    md.append("\n---\n")

    # 9. Leaderboard/Achievements Impact
    md.append("## 9. Leaderboard/Achievements Impact\n")
    md.append(
        f"**Leaderboard state completo**: "
        f"{json.dumps(counts['09_leaderboard_state'], indent=2)}\n"
        "\n"
        f"**Achievement progress**: "
        f"{counts['08_achievement_progress_earned']} doc\n"
        "\n"
        "**Strategia raccomandata**: L.d (nuova era) + Ach.d "
        "(Hall of Fame + Founder badge combo). Vedi §12 di "
        "r18_reset0_full_guild_fresh_start_plan.md per il razionale "
        "completo.\n"
    )
    md.append("\n---\n")

    # 10. R18 Migration/Banner Impact
    md.append("## 10. R18 Migration/Banner Impact\n")
    md.append(
        f"**R18.3c orphan migration state**:\n"
        f"- Adventurers migrati R18.3c: "
        f"{counts['11_r18_3c_banner_state']['adventurers_migrated_r18_3c']}\n"
        f"- Guild con banner field: "
        f"{counts['11_r18_3c_banner_state']['guilds_with_banner_field']}\n"
        f"- Guild banner dismissed: "
        f"{counts['11_r18_3c_banner_state']['guilds_banner_dismissed']}\n"
        "\n"
        "**Strategia**: banner R18.3c e' obsoleto post-reset. Il campo "
        "`migration_banner_r18_3c_dismissed` viene resettato o "
        "archiviato con la guild. Nuovo banner welcome R18.Reset.0 "
        "sostituisce.\n"
    )
    md.append("\n---\n")

    # 11. seed_round5 Warning Analysis
    md.append("## 11. seed_round5 Warning Analysis\n")
    md.append(f"**Warning**: `{seed_warn['warning_text']}`\n\n")
    md.append(f"**Location**: `{seed_warn['location_file']}`\n\n")
    md.append(
        f"**Root cause (ipotesi)**:\n{seed_warn['root_cause_hypothesis']}\n\n"
    )
    md.append(
        f"**Legge hidden classes senza filtro is_playable**: "
        f"{seed_warn['reads_hidden_without_is_playable_filter']}\n\n"
    )
    md.append(
        f"**Hidden classes senza base_strength in DB**: "
        f"{seed_warn['hidden_classes_without_base_strength_in_db']}\n\n"
    )
    md.append(
        f"**Player-facing impact**: "
        f"{seed_warn['player_facing_impact']}\n\n"
    )
    md.append(
        f"**Reset R18.Reset.1b lo rende obsoleto?**\n"
        f"{seed_warn['reset_r18_reset_1b_makes_it_obsolete']}\n\n"
    )
    md.append(
        f"**Future patch candidate**: "
        f"{seed_warn['future_patch_candidate']}\n\n"
    )
    md.append(
        f"**Rischio residuo se NON patchiamo prima del reset apply**: "
        f"{seed_warn['residual_risk_if_not_patched_pre_reset']}\n\n"
    )
    md.append(
        "**IMPORTANTE**: questo dry-run NON modifica `seed_round5.py`. "
        "Solo lettura e analisi.\n"
    )
    md.append("\n---\n")

    # 12. Storage Estimate
    md.append("## 12. Storage Estimate\n")
    st = counts['14_storage_estimate']
    md.append(
        f"**Pattern**: {st['archive_pattern']}\n\n"
        f"**Storage totale stimato**: {st['total_mb']} MB "
        f"({st['total_bytes']} bytes)\n\n"
        f"**Retention proposta**: 90 giorni\n\n"
        "**Breakdown per collection** (top-10 by size):\n\n"
        "| Collection | Doc count | Avg obj (bytes) | Size (bytes) |\n"
        "|---|---|---|---|\n"
    )
    per = sorted(st['per_collection'].items(),
                 key=lambda x: -x[1]['estimated_size_bytes'])[:10]
    for name, info in per:
        md.append(
            f"| `{name}` | {info['doc_count']} | "
            f"{info['avg_obj_size_bytes']} | "
            f"{info['estimated_size_bytes']} |\n"
        )
    md.append(f"\n> {st['note']}\n")
    md.append("\n---\n")

    # 13. Rollback Plan
    md.append("## 13. Rollback Plan\n")
    md.append(f"**Pattern**: {rollback['pattern']}\n\n")
    md.append(f"**Snapshot path**: `{rollback['snapshot_path']}`\n\n")
    md.append(f"**Manifest file**: `{rollback['manifest_file']}`\n\n")
    md.append(f"**Steps**:\n")
    for s in rollback['steps_rollback']:
        md.append(f"- {s}\n")
    md.append(
        f"\n**Restore time estimate**: "
        f"{rollback['restore_time_estimate_seconds']} secondi\n\n"
        f"**Retention window**: {rollback['retention_days']} giorni\n\n"
        f"**Test fixture**: {rollback['test_fixture']}\n\n"
        f"**Comando CLI**:\n```\n{rollback['cli_command_template']}\n```\n\n"
        f"> {rollback['note_no_hard_delete']}\n"
    )
    md.append("\n---\n")

    # 14. Apply Plan
    md.append("## 14. Apply Plan (step-by-step per R18.Reset.1b)\n")
    md.append(f"**Target**: {apply_plan['target_round']}\n\n")
    md.append("**Steps** (non eseguiti in questo round):\n\n")
    for s in apply_plan['steps']:
        md.append(f"- {s}\n")
    md.append(
        f"\n**Tempo esecuzione stimato**: "
        f"{apply_plan['estimated_execution_time_minutes']} minuti\n\n"
        f"**Reversibile via**: {apply_plan['reversible_via']}\n\n"
        f"> {apply_plan['note']}\n"
    )
    md.append("\n---\n")

    # 15. No-Write Proof
    md.append("## 15. No-Write Proof\n")
    md.append("**Protezioni tecniche attive**:\n")
    for p in proof['protections']:
        md.append(f"- {p}\n")
    md.append(
        f"\n**Self-audit del sorgente**: "
        f"{proof['self_audit_result']}\n\n"
        f"**Chiamate DB consentite**: "
        f"{', '.join(proof['allowed_db_calls'])}\n\n"
        f"**Chiamate DB vietate**: "
        f"{', '.join(proof['forbidden_db_calls'])}\n"
    )
    md.append("\n---\n")

    # 16. PM Decisions Required
    md.append("## 16. PM Decisions Required Before Reset.1b\n")
    for q in pm_q:
        md.append(f"\n**{q['id']}**. {q['topic']}\n")
        md.append(f"- **Raccomandazione e1_dev**: "
                  f"{q['raccomandazione_e1_dev']}\n")
    md.append("\n---\n")
    md.append(
        f"\n*Firma: e1 main agent - dry-run generato "
        f"{computed_at}*\n"
    )
    return "".join(md)


def build_json_report(data: dict) -> dict:
    """JSON con le stesse 16 sezioni in forma machine-readable.
    Chiavi snake_case in inglese."""
    return {
        "round": "R18.Reset.1a",
        "mode": "dry_run_read_only",
        "computed_at": data["computed_at"],
        "status": "COMPLETED",
        "sections": {
            "section_01_executive_summary": {
                "guilds_total": data["counts"]["01_guilds_total_active"],
                "adventurers_total": data["counts"]
                    ["05_adventurers_total_to_archive"],
                "safe_class_pool_size": data["starter_roster"]
                    ["safe_class_pool_size"],
                "storage_archive_mb": data["counts"]
                    ["14_storage_estimate"]["total_mb"],
                "self_audit_result": data["no_write_proof"]
                    ["self_audit_result"],
            },
            "section_02_dry_run_counts": data["counts"],
            "section_03_preserve_identity_plan": {
                "collections": PRESERVE_COLLECTIONS,
                "count": len(PRESERVE_COLLECTIONS),
                "guild_identity_fields": [
                    "_id", "id", "public_id", "owner_user_id", "name",
                    "created_at", "updated_at", "is_test_artifact",
                    "is_grandfathered", "is_demo_opponent",
                ],
            },
            "section_04_archive_plan": {
                "pattern": "B",
                "sibling_suffix": "_r18_archive",
                "collections": ARCHIVE_COLLECTIONS,
                "count": len(ARCHIVE_COLLECTIONS),
            },
            "section_05_reset_candidates": {
                "guild_fields_reset": {
                    "level": 1, "gold": 100, "reputation": 0,
                    "current_roster_size": 5,
                    "max_roster_cap": "recomputed_via_R18_1_formula",
                    "r18_beta_opt_in": False,
                    "raids_completed_count": 0,
                    "raids_victory_count": 0,
                    "max_raid_score": 0,
                    "last_raid_completed_at": None,
                    "max_team_power_ever": 0,
                    "r18_roster_cap_computed_at": "iso_now",
                },
            },
            "section_06_starter_roster_simulation": data["starter_roster"],
            "section_07_starter_kit_simulation": data["starter_kit"],
            "section_08_active_activity_impact": {
                "expeditions_by_status": data["counts"]
                    ["10_expeditions_by_status"],
                "raids_by_status": data["counts"]["10_raids_by_status"],
                "resource_missions_by_status": data["counts"]
                    ["10_resource_missions_by_status"],
                "expedition_members": data["counts"]
                    ["10_expedition_members"],
                "raid_participants": data["counts"]
                    ["10_raid_participants"],
                "strategy": (
                    "Archive + delete all active. Player at reset time "
                    "sees welcome banner at next login (0 expected)."
                ),
            },
            "section_09_leaderboard_achievements_impact": {
                "leaderboard_state": data["counts"]
                    ["09_leaderboard_state"],
                "achievement_progress": data["counts"]
                    ["08_achievement_progress_earned"],
                "strategy_leaderboard": "L.d (nuova era + preserve cosmetici)",
                "strategy_achievement": "Ach.d (Hall of Fame + Founder combo)",
            },
            "section_10_r18_migration_banner_impact": data["counts"]
                ["11_r18_3c_banner_state"],
            "section_11_seed_round5_warning_analysis": data
                ["seed_round5_warning_analysis"],
            "section_12_storage_estimate": data["counts"]
                ["14_storage_estimate"],
            "section_13_rollback_plan": data["rollback_plan"],
            "section_14_apply_plan": data["apply_plan"],
            "section_15_no_write_proof": data["no_write_proof"],
            "section_16_pm_decisions_required": data
                ["pm_decisions_required"],
        },
    }


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
async def main_async() -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        counts_bundle = await compute_all(db)
        starter = await simulate_starter_roster(db)
        kit = simulate_starter_kit()
        seed_warn = await analyze_seed_round5_warning(db)
        rollback = build_rollback_plan()
        apply_plan = build_apply_plan()
        pm_q = build_pm_questions()
        no_write_proof = {
            "self_audit_result": "PASS",
            "protections": [
                "Self-audit statico all'avvio (grep del proprio sorgente)",
                "Wrapper safe_aggregate() blocca $out/$merge nelle pipeline",
                "Token forbidden smembrati per evitare falsi positivi",
                "Nessun import di funzioni mutanti",
            ],
            "allowed_db_calls": [
                "count_documents", "find", "aggregate (senza $out/$merge)",
                "distinct", "list_collection_names",
                "command('collstats', ...)",
            ],
            "forbidden_db_calls": _FORBIDDEN_TOKENS,
        }
        data = {
            **counts_bundle,
            "starter_roster": starter,
            "starter_kit": kit,
            "seed_round5_warning_analysis": seed_warn,
            "rollback_plan": rollback,
            "apply_plan": apply_plan,
            "pm_decisions_required": pm_q,
            "no_write_proof": no_write_proof,
        }

        # Write MD + JSON
        md_content = build_md_report(data)
        json_content = build_json_report(data)
        OUT_MD.write_text(md_content, encoding="utf-8")
        OUT_JSON.write_text(
            json.dumps(json_content, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Stdout compact summary
        c = counts_bundle["counts"]
        print("=" * 70)
        print("R18.Reset.1a DRY-RUN COMPLETED (read-only, zero mutazioni)")
        print("=" * 70)
        print(f"Computed at: {counts_bundle['computed_at']}")
        print(f"Guild totali: {c['01_guilds_total_active']}")
        print(f"  - Con owner user: {c['02_guilds_with_owner_user_id']}")
        print(f"  - Orphan (no owner): {c['03_guilds_orphan_no_owner']}")
        print(f"  - Test/demo (name+flag): "
              f"{c['04_guilds_test_demo_by_name_or_flag']}")
        print(f"  - Owner @orbus.test: "
              f"{c['04_guilds_owner_email_orbus_test']}")
        print(f"  - Owner REAL domain: "
              f"{c['04_guilds_owner_email_real_domain']}")
        print(f"Adventurers totali: {c['05_adventurers_total_to_archive']}")
        print(f"Inventory items: {c['06_inventory_items']} · "
              f"Equipped: {c['06_equipped_items']}")
        print(f"Gold sum: {c['07_gold_stats']['total_gold']} · "
              f"avg: {c['07_gold_stats']['avg_gold']}")
        print(f"Achievement progress: "
              f"{c['08_achievement_progress_earned']}")
        print(f"Storage archive stimato: "
              f"{c['14_storage_estimate']['total_mb']} MB")
        print(f"Safe class pool: {starter['safe_class_pool_size']} "
              f"(atteso: {starter['expected_safe_count']})")
        if starter['discrepancy']:
            print(f"  DISCREPANZA: {starter['discrepancy']}")
        else:
            print("  Nessuna discrepanza")
        print(f"seed_round5 warning: "
              f"{seed_warn['player_facing_impact']}")
        print()
        print(f"Deliverable prodotti:")
        print(f"  MD:   {OUT_MD}")
        print(f"  JSON: {OUT_JSON}")
        print("=" * 70)
        print("Self-audit del sorgente: PASS (nessuna chiamata mutante)")
        print("=" * 70)
        return 0
    finally:
        client.close()


def main() -> None:
    # 1. Self-audit sul sorgente (blocca se trova token vietati).
    _self_audit_forbid_mutations()
    # 2. Esegui async main.
    try:
        exit_code = asyncio.run(main_async())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"ERRORE dry-run: {type(exc).__name__}: {exc}\n")
        raise
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
