"""ROUND 16.5.4c — Test-seed 2 avventurieri (Warlock + Alchemist) sulla
gilda di `tester@orbus.test` per permettere il test E2E browser
`e1_tester` sull'Auto-Equip con le classi post-ADJ-3.

Guard-rail (applicati staticamente):
  * Solo owner=`tester@orbus.test`. Se il lookup restituisce user diverso,
    lo script fallisce.
  * Solo `db.adventurers` (insert) e `db.inventory_items` (insert).
  * Marker `is_test_seed=True` + `test_seed_source="round1654c_e2e"`.
  * Snapshot pre-seed dell'intero roster del tester in
    `/app/memory/round1654c_test_seed_snapshot.json`.
  * Audit event `TEST_ADVENTURER_SEEDED` per ogni doc inserito.
  * NO delete. NO $set su doc esistenti. NO modifica a drop/reward/PvP.
  * Idempotenza: se un Warlock/Alchemist con marker `test_seed_source`
    esiste già → riusa senza creare duplicati.

Uso:
    python -m app.scripts.round1654c_test_seed_adventurers --apply
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

from motor.motor_asyncio import AsyncIOMotorClient

TESTER_EMAIL = "tester@orbus.test"
TEST_SEED_SOURCE = "round1654c_e2e"
SNAPSHOT_PATH = Path("/app/memory/round1654c_test_seed_snapshot.json")
AUDIT_EVENT = "TEST_ADVENTURER_SEEDED"

# Item slugs from ADJ-3 seed pack — Common Lv1 sono i più permissivi
# per il tester (nessun level gate blocca).
INVENTORY_BY_CLASS = {
    "warlock": [
        "warlock_apprentice_tome",
        "warlock_novice_robe",
        "warlock_cursed_pendant",
    ],
    "alchemist": [
        "alchemist_apprentice_flask",
        "alchemist_apron",
        "alchemist_reagent_pouch",
    ],
}


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _load_tester(db) -> tuple[dict, dict]:
    user = await db.users.find_one({"email": TESTER_EMAIL})
    if not user:
        raise RuntimeError(f"user {TESTER_EMAIL} non trovato")
    guild = await db.guilds.find_one({"owner_user_id": user["id"]})
    if not guild:
        raise RuntimeError(f"guild non trovata per {TESTER_EMAIL}")
    return user, guild


async def _load_class(db, slug: str) -> dict:
    cls = await db.adventurer_classes.find_one({"slug": slug})
    if not cls:
        raise RuntimeError(f"class {slug} non nel catalog")
    return cls


async def _existing_test_seed_adv(db, guild_id: str, class_slug: str):
    return await db.adventurers.find_one({
        "guild_id": guild_id,
        "class_slug": class_slug,
        "test_seed_source": TEST_SEED_SOURCE,
    })


def _build_adventurer_doc(guild_id: str, klass: dict, *,
                          adv_name: str, level: int = 5) -> dict:
    now = _utc_iso_now()
    # Stats coerenti con la classe (usa i base_* del catalog).
    stats = {}
    for stat in ("strength", "agility", "intellect",
                 "endurance", "faith"):
        stats[stat] = int(klass.get(f"base_{stat}", 10) or 10)
    doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": adv_name,
        "adventurer_class_id": klass["id"],
        "class_name": klass["name"],
        "class_slug": klass["slug"],
        "class_role": klass.get("role", "DPS"),
        "rarity": "Common",
        "level": level,
        "experience": 0,
        **stats,
        "stamina": 100,
        "morale": 100,
        "is_available": True,
        "is_retired": False,
        "traits": [],
        "is_starter": False,
        "is_test_seed": True,
        "test_seed_source": TEST_SEED_SOURCE,
        "created_at": now,
        "updated_at": now,
    }
    return doc


async def _seed_inventory(db, guild_id: str, item_slug: str) -> str | None:
    """Insert 1 inventory row for the item; skip se già presente in inv."""
    item = await db.items.find_one({"slug": item_slug})
    if not item:
        print(f"  [warn] item {item_slug} non trovato nel catalog, skip")
        return None
    exists = await db.inventory_items.find_one({
        "guild_id": guild_id, "item_id": item["id"],
    })
    if exists:
        print(f"  [reuse] inv già presente per {item_slug} "
              f"(inv_id={exists['id']})")
        return exists["id"]
    inv_id = str(uuid.uuid4())
    await db.inventory_items.insert_one({
        "id": inv_id,
        "guild_id": guild_id,
        "item_id": item["id"],
        "quantity": 1,
        "reserved_qty": 0,
        "is_active": True,
        "is_bound": False,
        "created_at": _utc_iso_now(),
    })
    print(f"  [seed] inv {item_slug} → inv_id={inv_id}")
    return inv_id


async def _audit(db, adv_doc: dict) -> None:
    try:
        await db.audit_events.insert_one({
            "event_type": AUDIT_EVENT,
            "actor_user_id": None,
            "actor_guild_id": adv_doc["guild_id"],
            "related_entity_id": adv_doc["id"],
            "source": "script.round1654c_test_seed_adventurers",
            "occurred_at": _utc_iso_now(),
            "metadata": {
                "adventurer_id": adv_doc["id"],
                "name": adv_doc["name"],
                "class_slug": adv_doc["class_slug"],
                "level": adv_doc["level"],
                "test_seed_source": TEST_SEED_SOURCE,
            },
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit emit failed: {exc}", file=sys.stderr)


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL o DB_NAME mancante", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print(f"[mode] {'DRY-RUN' if dry_run else 'APPLY'} · db={db_name}")

    user, guild = await _load_tester(db)
    print(f"[tester] {user['email']} · guild={guild['name']!r} "
          f"({guild['id']})")

    # Guard: rifiuta se l'account non è tester@orbus.test.
    if user.get("email") != TESTER_EMAIL:
        print(f"[FAIL] guard: user email ({user.get('email')!r}) diversa "
              f"da {TESTER_EMAIL!r}")
        return 3

    # Snapshot pre-seed (roster completo tester)
    roster_before = await db.adventurers.find(
        {"guild_id": guild["id"]},
        {"_id": 0, "id": 1, "name": 1, "class_slug": 1,
         "class_name": 1, "level": 1, "is_test_seed": 1,
         "test_seed_source": 1},
    ).to_list(length=None)
    snapshot = {
        "generated_at": _utc_iso_now(),
        "tester_email": TESTER_EMAIL,
        "guild_id": guild["id"],
        "guild_name": guild["name"],
        "roster_count_before": len(roster_before),
        "roster_before": roster_before,
    }
    if not dry_run:
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, default=str)
            + "\n", encoding="utf-8",
        )
        print(f"[snapshot] {SNAPSHOT_PATH} "
              f"(roster_before={len(roster_before)})")

    results: dict[str, dict] = {}

    for class_slug, name in (("warlock", "Test-Warlock-R1654c"),
                             ("alchemist", "Test-Alchemist-R1654c")):
        print(f"\n=== {class_slug} ===")
        existing = await _existing_test_seed_adv(
            db, guild["id"], class_slug,
        )
        if existing:
            print(f"  [reuse] adventurer già presente "
                  f"(id={existing['id']}, name={existing['name']!r})")
            adv_doc = existing
        else:
            klass = await _load_class(db, class_slug)
            adv_doc = _build_adventurer_doc(
                guild["id"], klass, adv_name=name, level=5,
            )
            print(f"  [plan] insert adventurer id={adv_doc['id']} "
                  f"name={adv_doc['name']!r} lv={adv_doc['level']}")
            if not dry_run:
                await db.adventurers.insert_one(dict(adv_doc))
                await _audit(db, adv_doc)

        # Inventory
        inv_seeded = []
        for item_slug in INVENTORY_BY_CLASS[class_slug]:
            if dry_run:
                print(f"  [plan] inv {item_slug}")
                inv_seeded.append(item_slug)
                continue
            inv_id = await _seed_inventory(db, guild["id"], item_slug)
            if inv_id:
                inv_seeded.append(item_slug)

        results[class_slug] = {
            "adventurer_id": adv_doc["id"],
            "name": adv_doc["name"],
            "level": adv_doc["level"],
            "class_slug": class_slug,
            "inventory_seeded": inv_seeded,
        }

    print("\n=== SUMMARY ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    if dry_run:
        print("\n[dry-run] nessuna scrittura. Rieseguire con --apply.")

    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__ or "")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true", default=True)
    grp.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    rc = asyncio.run(run(dry_run=not args.apply_))
    sys.exit(rc)


if __name__ == "__main__":
    main()
