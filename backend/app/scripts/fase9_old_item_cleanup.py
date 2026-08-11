#!/usr/bin/env python3
"""FASE 9M — Eliminazione definitiva degli item legacy build/spec.

I vecchi item costruiti intorno a specializzazioni e build:
  * interferivano con l'Auto-Equip;
  * risultavano equipaggiabili in condizioni sbagliate;
  * causavano problemi all'ingresso nelle istanze.

Questo script li identifica CHIRURGICAMENTE (mai cancellazione cieca),
produce un report dry-run e applica la pulizia solo con --apply.

Cosa identifica (AUDIT):
  1. catalog item legacy (db.items):
     a. item firma di specializzazione (slug spec_signature_* o
        is_signature=true);
     b. item con specialization_unlocks non vuoto E fuori dai cataloghi
        canonici correnti (T6 + kit Hall + set raid + seed IT + fase3);
     c. item con campi build (build_path_*) — se il loro slug È nei
        cataloghi correnti vengono SANATI ($unset dei campi build/spec),
        altrimenti sono legacy pieni;
  2. inventory instance (db.inventory_items) che puntano agli item legacy;
  3. equipped_items che li indossano (con reserved_qty da riconciliare);
  4. reservation (inventory_items.reserved_qty) incoerenti;
  5. listing di mercato/asta che li offrono;
  6. ricette (db.recipes) che li producono o li richiedono;
  7. loot table dei dungeon (db.dungeons.loot_table) che li contengono;
  8. riferimenti Class Hall / Collection Book (claim storici: SOLO report);
  9. campi spec sugli avventurieri (specialization*, signature_item_id)
     e sulle Sale (unlocked_specializations, righe hall legacy inglesi)
     + collection class_specializations.

La migration (--apply, IDEMPOTENTE e FAIL-CLOSED):
  1. disequipaggia gli item legacy (delete equipped_items);
  2. riconcilia le reservation (reserved_qty -= pezzi rilasciati, >= 0);
  3. rimuove le inventory instance legacy;
  4. rimuove le catalog entry legacy (is_active=false + is_legacy_removed
     -> gli id restano risolvibili per i report storici, ma NESSUN
     sistema li vede piu': Auto-Equip/loot/craft filtrano is_active);
  5. sana gli item correnti ($unset build_path_*/specialization_unlocks);
  6. annulla listing di mercato/asta legacy (status cancelled);
  7. rimuove gli item legacy dalle loot table dei dungeon;
  8. disattiva le ricette che producono item legacy;
  9. $unset dei campi spec su adventurers, pulizia class_halls
     (unlocked_specializations + righe legacy) e drop
     class_specializations;
 10. VERIFICA finale: 0 equipped orfani, 0 inventory orfane, 0 campi
     spec residui, 0 item legacy attivi — se una verifica fallisce lo
     script esce con codice != 0 (fail-closed).

Uso:
    python -m app.scripts.fase9_old_item_cleanup            # dry-run
    python -m app.scripts.fase9_old_item_cleanup --apply    # applica

MAI eseguito automaticamente. Con APP_ENV=production serve anche
--confirm-production (decisione esplicita dell'owner).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

LEGACY_ENGLISH_CLASS_SLUGS = {
    "warrior", "rogue", "mage", "priest", "ranger", "paladin", "druid",
    "monk", "bard", "warlock", "alchemist", "berserker", "assassin",
    "necromancer",
}

SPEC_FIELDS_ON_ADVENTURER = (
    "specialization", "specialization_slug", "specialization_respec_count",
    "specialization_applied_at", "specialization_respec_last_at",
    "signature_item_id",
)

BUILD_FIELDS_ON_ITEM = (
    "build_path_id", "build_path_name_it", "build_path_description_it",
    "build_path_item_tags",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_slugs() -> set[str]:
    """Slug degli item nei cataloghi canonici CORRENTI (post-FASE 9)."""
    from app.items.final_catalog import FINAL_ITEM_CATALOG
    from app.raids.class_sets import RAID_CLASS_SET_ITEMS
    from app.seeds.seed_fase3_reagenti_consumabili import (
        NEW_CONSUMABLES,
        NEW_MATERIALS,
    )
    from app.seeds.seed_items_it import ITALIAN_ITEM_SEED
    slugs = {row["slug"] for row in FINAL_ITEM_CATALOG}
    slugs |= {row["slug"] for row in RAID_CLASS_SET_ITEMS}
    slugs |= {row["slug"] for row in NEW_CONSUMABLES}
    slugs |= {row["slug"] for row in NEW_MATERIALS}
    slugs |= {row.get("slug") for row in ITALIAN_ITEM_SEED if row.get("slug")}
    return slugs


async def audit(db) -> dict:
    canonical = _canonical_slugs()

    legacy_ids: set[str] = set()
    legacy_rows: list[dict] = []
    heal_rows: list[dict] = []

    async for item in db.items.find(
        {}, {"_id": 0, "id": 1, "slug": 1, "name": 1, "is_active": 1,
             "is_signature": 1, "specialization_unlocks": 1,
             "build_path_id": 1, "is_legacy_removed": 1},
    ):
        slug = str(item.get("slug") or "")
        item_id = item.get("id")
        is_signature = bool(item.get("is_signature")) or slug.startswith(
            "spec_signature_"
        )
        has_spec_unlocks = bool(item.get("specialization_unlocks"))
        has_build_fields = item.get("build_path_id") is not None
        in_canonical = slug in canonical

        if is_signature or (
            (has_spec_unlocks or has_build_fields) and not in_canonical
        ):
            legacy_ids.add(item_id)
            legacy_rows.append({
                "id": item_id, "slug": slug, "name": item.get("name"),
                "reason": (
                    "spec_signature" if is_signature
                    else "spec_locked_off_catalog" if has_spec_unlocks
                    else "build_item_off_catalog"
                ),
                "already_removed": bool(item.get("is_legacy_removed")),
            })
        elif in_canonical and (has_spec_unlocks or has_build_fields):
            heal_rows.append({"id": item_id, "slug": slug})

    legacy_id_list = list(legacy_ids)

    equipped = await db.equipped_items.find(
        {"item_id": {"$in": legacy_id_list}},
        {"_id": 0, "id": 1, "item_id": 1, "adventurer_id": 1, "guild_id": 1},
    ).to_list(100000)
    inventory = await db.inventory_items.find(
        {"item_id": {"$in": legacy_id_list}},
        {"_id": 0, "id": 1, "item_id": 1, "guild_id": 1, "quantity": 1,
         "reserved_qty": 1},
    ).to_list(100000)
    market = await db.market_listings.find(
        {"item_id": {"$in": legacy_id_list},
         "status": {"$nin": ["cancelled", "sold"]}},
        {"_id": 0, "id": 1, "item_id": 1, "guild_id": 1, "status": 1},
    ).to_list(100000)
    try:
        auction = await db.auction_listings.find(
            {"item_id": {"$in": legacy_id_list},
             "status": {"$nin": ["cancelled", "sold", "expired"]}},
            {"_id": 0, "id": 1, "item_id": 1, "status": 1},
        ).to_list(100000)
    except Exception:  # noqa: BLE001
        auction = []
    recipes = await db.recipes.find(
        {"$or": [
            {"output_item_id": {"$in": legacy_id_list}},
            {"result_item_id": {"$in": legacy_id_list}},
        ], "is_active": {"$ne": False}},
        {"_id": 0, "id": 1, "slug": 1},
    ).to_list(10000)
    dungeons_with_legacy_loot = []
    async for d in db.dungeons.find(
        {}, {"_id": 0, "id": 1, "slug": 1, "loot_table": 1},
    ):
        table = d.get("loot_table") or []
        hit = [
            row for row in table
            if (row.get("item_id") in legacy_ids
                or row.get("id") in legacy_ids)
        ]
        if hit:
            dungeons_with_legacy_loot.append(
                {"slug": d.get("slug"), "count": len(hit)}
            )
    hall_track_claims = await db.class_hall_item_claims.count_documents(
        {"item_id": {"$in": legacy_id_list}},
    ) if "class_hall_item_claims" in await db.list_collection_names() else 0

    adventurers_with_spec = await db.adventurers.count_documents({
        "$or": [{field: {"$exists": True, "$nin": [None, 0]}}
                for field in SPEC_FIELDS_ON_ADVENTURER],
    })
    halls_with_specs = await db.class_halls.count_documents(
        {"unlocked_specializations": {"$exists": True}},
    )
    legacy_hall_rows = await db.class_halls.count_documents(
        {"class_slug": {"$in": list(LEGACY_ENGLISH_CLASS_SLUGS)}},
    )
    spec_collection_docs = (
        await db.class_specializations.count_documents({})
        if "class_specializations" in await db.list_collection_names()
        else 0
    )

    return {
        "generated_at": _now_iso(),
        "canonical_catalog_slugs": len(canonical),
        "legacy_catalog_items": legacy_rows,
        "legacy_catalog_count": len(legacy_rows),
        "healable_catalog_items": heal_rows,
        "healable_catalog_count": len(heal_rows),
        "equipped_legacy": equipped,
        "equipped_legacy_count": len(equipped),
        "inventory_legacy": inventory,
        "inventory_legacy_count": len(inventory),
        "market_listings_legacy_count": len(market),
        "market_listings_legacy": market,
        "auction_listings_legacy_count": len(auction),
        "recipes_producing_legacy_count": len(recipes),
        "recipes_producing_legacy": recipes,
        "dungeon_loot_tables_with_legacy": dungeons_with_legacy_loot,
        "class_hall_track_claims_on_legacy": hall_track_claims,
        "adventurers_with_spec_fields": adventurers_with_spec,
        "class_halls_with_unlocked_specs_field": halls_with_specs,
        "class_hall_legacy_rows": legacy_hall_rows,
        "class_specializations_docs": spec_collection_docs,
        "_legacy_ids": legacy_id_list,
    }


async def apply_cleanup(db, report: dict) -> dict:
    legacy_ids = report["_legacy_ids"]
    now = _now_iso()
    result: dict = {"applied_at": now}

    # 1-2. Disequipaggia + riconcilia reservation.
    released: dict[tuple[str, str], int] = {}
    for row in report["equipped_legacy"]:
        key = (row.get("guild_id"), row.get("item_id"))
        released[key] = released.get(key, 0) + 1
    unequipped = await db.equipped_items.delete_many(
        {"item_id": {"$in": legacy_ids}},
    )
    result["unequipped"] = int(unequipped.deleted_count)
    fixed_reservations = 0
    for (guild_id, item_id), count in released.items():
        inv = await db.inventory_items.find_one(
            {"guild_id": guild_id, "item_id": item_id},
            {"_id": 0, "reserved_qty": 1},
        )
        if inv is None:
            continue
        reserved = max(0, int(inv.get("reserved_qty") or 0) - count)
        await db.inventory_items.update_one(
            {"guild_id": guild_id, "item_id": item_id},
            {"$set": {"reserved_qty": reserved, "updated_at": now}},
        )
        fixed_reservations += 1
    result["reservations_reconciled"] = fixed_reservations

    # 3. Inventory instance legacy.
    removed_inventory = await db.inventory_items.delete_many(
        {"item_id": {"$in": legacy_ids}},
    )
    result["inventory_removed"] = int(removed_inventory.deleted_count)

    # 4. Catalog legacy: disattivati e marcati (id risolvibili nei report
    #    storici, ma invisibili a Auto-Equip/loot/craft che filtrano
    #    is_active=True).
    removed_catalog = await db.items.update_many(
        {"id": {"$in": legacy_ids}},
        {"$set": {"is_active": False, "is_legacy_removed": True,
                  "legacy_removed_at": now, "updated_at": now}},
    )
    result["catalog_deactivated"] = int(removed_catalog.modified_count)

    # 5. Sana gli item correnti (via campi build/spec).
    healed = await db.items.update_many(
        {"$or": [
            {"specialization_unlocks": {"$exists": True}},
            {"build_path_id": {"$exists": True}},
        ], "is_legacy_removed": {"$ne": True}},
        {"$unset": {
            "specialization_unlocks": "",
            **{field: "" for field in BUILD_FIELDS_ON_ITEM},
        }, "$set": {"updated_at": now}},
    )
    result["catalog_healed"] = int(healed.modified_count)

    # 6. Listing di mercato/asta legacy.
    market_cancelled = await db.market_listings.update_many(
        {"item_id": {"$in": legacy_ids},
         "status": {"$nin": ["cancelled", "sold"]}},
        {"$set": {"status": "cancelled",
                  "cancelled_reason": "fase9_legacy_item",
                  "updated_at": now}},
    )
    result["market_listings_cancelled"] = int(market_cancelled.modified_count)
    try:
        auction_cancelled = await db.auction_listings.update_many(
            {"item_id": {"$in": legacy_ids},
             "status": {"$nin": ["cancelled", "sold", "expired"]}},
            {"$set": {"status": "cancelled",
                      "cancelled_reason": "fase9_legacy_item",
                      "updated_at": now}},
        )
        result["auction_listings_cancelled"] = int(
            auction_cancelled.modified_count
        )
    except Exception:  # noqa: BLE001
        result["auction_listings_cancelled"] = 0

    # 7. Loot table dei dungeon.
    loot_cleaned = 0
    async for d in db.dungeons.find(
        {}, {"_id": 0, "id": 1, "loot_table": 1},
    ):
        table = d.get("loot_table") or []
        kept = [
            row for row in table
            if row.get("item_id") not in set(legacy_ids)
            and row.get("id") not in set(legacy_ids)
        ]
        if len(kept) != len(table):
            await db.dungeons.update_one(
                {"id": d["id"]},
                {"$set": {"loot_table": kept, "updated_at": now}},
            )
            loot_cleaned += 1
    result["dungeon_loot_tables_cleaned"] = loot_cleaned

    # 8. Ricette che producono item legacy.
    recipes_off = await db.recipes.update_many(
        {"$or": [
            {"output_item_id": {"$in": legacy_ids}},
            {"result_item_id": {"$in": legacy_ids}},
        ]},
        {"$set": {"is_active": False,
                  "deactivated_reason": "fase9_legacy_item",
                  "updated_at": now}},
    )
    result["recipes_deactivated"] = int(recipes_off.modified_count)

    # 9. Campi spec su avventurieri, Sale e collection dedicata.
    adv_unset = await db.adventurers.update_many(
        {"$or": [{field: {"$exists": True}}
                 for field in SPEC_FIELDS_ON_ADVENTURER]},
        {"$unset": {field: "" for field in SPEC_FIELDS_ON_ADVENTURER}},
    )
    result["adventurers_spec_fields_cleared"] = int(adv_unset.modified_count)
    halls_unset = await db.class_halls.update_many(
        {"unlocked_specializations": {"$exists": True}},
        {"$unset": {"unlocked_specializations": ""}},
    )
    result["class_halls_specs_cleared"] = int(halls_unset.modified_count)
    legacy_halls = await db.class_halls.delete_many(
        {"class_slug": {"$in": list(LEGACY_ENGLISH_CLASS_SLUGS)}},
    )
    result["class_hall_legacy_rows_removed"] = int(legacy_halls.deleted_count)
    if "class_specializations" in await db.list_collection_names():
        await db.class_specializations.drop()
        result["class_specializations_dropped"] = True
    else:
        result["class_specializations_dropped"] = False

    # Audit trail (best-effort).
    try:
        await db.audit_log.insert_one({
            "event_type": "fase9_item_cleanup_applied",
            "occurred_at": now,
            "source": "scripts.fase9_old_item_cleanup",
            "metadata": {k: v for k, v in result.items()
                         if isinstance(v, (int, bool, str))},
        })
    except Exception:  # noqa: BLE001
        pass
    return result


async def verify(db) -> dict:
    """Verifica post-migration (fail-closed: ok=False → exit code 1)."""
    active_item_ids = set(await db.items.distinct("id", {"is_active": True}))
    equipped_orphans = 0
    async for row in db.equipped_items.find({}, {"_id": 0, "item_id": 1}):
        if row.get("item_id") not in active_item_ids:
            equipped_orphans += 1
    inventory_orphans = 0
    async for row in db.inventory_items.find(
        {"quantity": {"$gt": 0}}, {"_id": 0, "item_id": 1},
    ):
        if row.get("item_id") not in active_item_ids:
            inventory_orphans += 1
    legacy_active = await db.items.count_documents({
        "is_active": True,
        "$or": [
            {"is_signature": True},
            {"slug": {"$regex": "^spec_signature_"}},
            {"specialization_unlocks": {"$exists": True, "$ne": []}},
            {"build_path_id": {"$exists": True}},
        ],
    })
    adventurers_with_spec = await db.adventurers.count_documents({
        "$or": [{field: {"$exists": True}}
                for field in SPEC_FIELDS_ON_ADVENTURER],
    })
    halls_with_specs = await db.class_halls.count_documents(
        {"unlocked_specializations": {"$exists": True}},
    )
    legacy_hall_rows = await db.class_halls.count_documents(
        {"class_slug": {"$in": list(LEGACY_ENGLISH_CLASS_SLUGS)}},
    )
    checks = {
        "equipped_orphans": equipped_orphans,
        "inventory_orphans": inventory_orphans,
        "legacy_items_active": legacy_active,
        "adventurers_with_spec_fields": adventurers_with_spec,
        "class_halls_with_unlocked_specs": halls_with_specs,
        "class_hall_legacy_rows": legacy_hall_rows,
    }
    checks["ok"] = all(v == 0 for v in checks.values())
    return checks


async def run(apply: bool, confirm_production: bool) -> int:
    app_env = os.environ.get("APP_ENV", "development")
    if apply and app_env == "production" and not confirm_production:
        print("ERRORE: APP_ENV=production richiede anche "
              "--confirm-production (decisione esplicita dell'owner).",
              file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    report = await audit(db)
    public_report = {k: v for k, v in report.items() if k != "_legacy_ids"}
    print("═══ FASE 9M — AUDIT ITEM LEGACY (dry-run) ═══")
    print(json.dumps(public_report, ensure_ascii=False, indent=2,
                     default=str)[:12000])

    out_dir = Path(__file__).resolve().parents[3] / "memory"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    mode = "apply" if apply else "dryrun"
    out_path = out_dir / f"fase9_item_cleanup_{mode}_{stamp}.json"

    if not apply:
        out_path.write_text(
            json.dumps(public_report, ensure_ascii=False, indent=2,
                       default=str),
            encoding="utf-8",
        )
        print(f"\nDRY-RUN: nessuna scrittura. Report: {out_path}")
        print("Per applicare: --apply")
        return 0

    applied = await apply_cleanup(db, report)
    checks = await verify(db)
    payload = {"audit": public_report, "applied": applied,
               "verification": checks}
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print("\n═══ APPLICATO ═══")
    print(json.dumps(applied, ensure_ascii=False, indent=2))
    print("\n═══ VERIFICA ═══")
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    print(f"\nReport completo: {out_path}")
    if not checks["ok"]:
        print("VERIFICA FALLITA — indagare prima di procedere.",
              file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="applica la pulizia (default: dry-run)")
    parser.add_argument("--confirm-production", action="store_true",
                        help="richiesto in aggiunta con APP_ENV=production")
    args = parser.parse_args()
    return asyncio.run(run(args.apply, args.confirm_production))


if __name__ == "__main__":
    raise SystemExit(main())
