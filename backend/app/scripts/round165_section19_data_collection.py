"""ROUND 16.5 P0 — Section 19 Data Collection (READ-ONLY).

Raccoglie i dati mancanti individuati nella sezione 19 del report R16.4:

1. Distribuzione avventurieri per livello (band lv 1-3, 4-6, 7-9, 10+).
2. Distribuzione Legendary items **equipaggiati** su avventurieri (per slug).
3. **ORPHANED LEGENDARIES**: avventurieri che indossano Legendary sotto
   il nuovo `min_level` applicato in R16.5 P0.

⚠️  NESSUN UNEQUIP AUTOMATICO. Lo script è read-only e usa i monkey-patch
delle write methods per garantirlo. L'utente decide il trattamento
(grandfathering vs forced-unequip) sulla base dei numeri estratti qui.

Output:
- /app/memory/round165_missing_data_section19.md
- /app/memory/round165_missing_data_section19.json

Usage:
    python /app/backend/app/scripts/round165_section19_data_collection.py \
        --read-only
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, "/app/backend")


# ═════════════════════════════════════════════════════════════════════
# 0. CLI safety — mandatory --read-only, forbidden hostile flags
# ═════════════════════════════════════════════════════════════════════


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, add_help=True)
    p.add_argument("--read-only", action="store_true", required=False,
                   help="MANDATORY safety flag.")
    for hostile in ("--apply", "--write", "--fix", "--unequip"):
        p.add_argument(hostile, action="store_true",
                       help="FORBIDDEN — script aborts if this is set.")
    return p.parse_args()


def _enforce_read_only(args: argparse.Namespace) -> None:
    if not args.read_only:
        sys.stderr.write("REFUSING: pass --read-only to run.\n")
        sys.exit(1)
    for hostile in ("apply", "write", "fix", "unequip"):
        if getattr(args, hostile, False):
            sys.stderr.write(
                f"REFUSING: hostile flag --{hostile} passed.\n"
            )
            sys.exit(1)
    print("=== SECTION 19 DATA COLLECTION — READ ONLY ===")


def _patch_write_methods_forbidden() -> None:
    import motor.motor_asyncio as _motor  # noqa: F401
    import pymongo.collection as _pc
    import pymongo.database as _pd

    def _raise_factory(name: str):
        def _raise(*args, **kwargs):
            raise RuntimeError(
                f"WRITE FORBIDDEN IN SECTION19 MODE (method: {name})"
            )
        return _raise

    forbidden = (
        "insert_one", "insert_many",
        "update_one", "update_many",
        "replace_one",
        "delete_one", "delete_many",
        "find_one_and_update", "find_one_and_replace",
        "find_one_and_delete",
        "bulk_write", "drop", "rename",
        "create_index", "create_indexes",
        "drop_index", "drop_indexes",
    )
    for cls in (_pc.Collection, _pd.Database):
        for m in forbidden:
            if hasattr(cls, m):
                setattr(cls, m, _raise_factory(f"{cls.__name__}.{m}"))


# ═════════════════════════════════════════════════════════════════════
# 1. DB
# ═════════════════════════════════════════════════════════════════════


def _connect_db():
    import os
    from dotenv import load_dotenv
    load_dotenv(Path("/app/backend/.env"))
    from pymongo import MongoClient
    url = os.environ.get("MONGO_URL")
    client = MongoClient(url)
    db = client["orbus_r16"]
    _ = db.list_collection_names()
    return client, db


# ═════════════════════════════════════════════════════════════════════
# 2. Data collection
# ═════════════════════════════════════════════════════════════════════


def _band_of(lvl: int) -> str:
    if lvl <= 3:
        return "lv1-3"
    if lvl <= 6:
        return "lv4-6"
    if lvl <= 9:
        return "lv7-9"
    return "lv10+"


def _adventurer_level_distribution(db) -> dict[str, Any]:
    bands = Counter()
    lvls: list[int] = []
    total = 0
    retired = 0
    for a in db.adventurers.find(
        {},
        {"_id": 0, "level": 1, "is_retired": 1},
    ):
        total += 1
        if a.get("is_retired"):
            retired += 1
            continue
        lvl = int(a.get("level") or 1)
        lvls.append(lvl)
        bands[_band_of(lvl)] += 1

    stats: dict[str, Any] = {"count_active": len(lvls), "count_retired": retired}
    if lvls:
        stats.update({
            "mean": round(statistics.mean(lvls), 2),
            "median": statistics.median(lvls),
            "min": min(lvls),
            "max": max(lvls),
            "p90": sorted(lvls)[int(len(lvls) * 0.9)] if len(lvls) > 10 else None,
        })
    return {
        "total_adventurers": total,
        "active": len(lvls),
        "retired": retired,
        "bands": dict(bands),
        "stats": stats,
    }


def _legendary_equipped_distribution(db) -> dict[str, Any]:
    """Conta ogni istanza di legendary attualmente EQUIPPATA su un avventuriero.

    Legge inventory_items con equipped_by set + slug in legendary catalog.
    Fallback: se il tuo schema usa un array `equipped_items` sull'avventuriero,
    conta anche quello.
    """
    # Catalog Legendary slugs
    leg_slugs = [
        it["slug"] for it in db.items.find(
            {"rarity": "Legendary"}, {"_id": 0, "slug": 1}
        )
    ]
    leg_set = set(leg_slugs)

    # PATH A: inventory_items with `equipped_by` field
    by_slug_A = Counter()
    equipped_pairs_A: list[dict] = []
    try:
        for inv in db.inventory_items.find(
            {"item_slug": {"$in": leg_slugs},
             "equipped_by": {"$exists": True, "$ne": None}},
            {"_id": 0, "item_slug": 1, "equipped_by": 1,
             "guild_id": 1, "owner_adventurer_id": 1},
        ):
            slug = inv.get("item_slug")
            by_slug_A[slug] += 1
            equipped_pairs_A.append({
                "item_slug": slug,
                "adventurer_id": inv.get("equipped_by")
                                 or inv.get("owner_adventurer_id"),
                "guild_id": inv.get("guild_id"),
            })
    except Exception:  # noqa: BLE001
        pass

    # PATH B: adventurer.equipped_items array (schema variant)
    by_slug_B = Counter()
    equipped_pairs_B: list[dict] = []
    for a in db.adventurers.find(
        {"$or": [
            {"equipped_items": {"$exists": True, "$ne": []}},
            {"equipment": {"$exists": True, "$ne": {}}},
        ]},
        {"_id": 0, "id": 1, "level": 1, "guild_id": 1,
         "equipped_items": 1, "equipment": 1},
    ):
        # Variant B1: list of slugs
        eq_list = a.get("equipped_items") or []
        for entry in eq_list:
            slug = entry.get("slug") if isinstance(entry, dict) else entry
            if slug in leg_set:
                by_slug_B[slug] += 1
                equipped_pairs_B.append({
                    "item_slug": slug,
                    "adventurer_id": a.get("id"),
                    "guild_id": a.get("guild_id"),
                    "adventurer_level": a.get("level"),
                })
        # Variant B2: dict {slot: slug}
        eq_dict = a.get("equipment") or {}
        if isinstance(eq_dict, dict):
            for slot, ref in eq_dict.items():
                if isinstance(ref, dict):
                    slug = ref.get("slug") or ref.get("item_slug")
                elif isinstance(ref, str):
                    slug = ref
                else:
                    slug = None
                if slug in leg_set:
                    by_slug_B[slug] += 1
                    equipped_pairs_B.append({
                        "item_slug": slug,
                        "adventurer_id": a.get("id"),
                        "guild_id": a.get("guild_id"),
                        "adventurer_level": a.get("level"),
                        "slot": slot,
                    })

    # Merge (prefer path with more data)
    if sum(by_slug_A.values()) >= sum(by_slug_B.values()):
        by_slug = dict(by_slug_A)
        pairs = equipped_pairs_A
        source = "inventory_items.equipped_by"
    else:
        by_slug = dict(by_slug_B)
        pairs = equipped_pairs_B
        source = "adventurers.equipped_items | adventurers.equipment"
    total_equipped = sum(by_slug.values())
    return {
        "source_used": source,
        "total_legendary_equipped": total_equipped,
        "by_item_slug": by_slug,
        "raw_pairs_sample": pairs[:50],  # cap sample for report size
        "raw_pairs_count": len(pairs),
    }


def _find_orphaned_legendaries(db) -> dict[str, Any]:
    """Trova le istanze di legendary equipaggiate da avventurieri il cui
    livello attuale è INFERIORE al nuovo `min_level` scritto dal P0.

    NON esegue nessun unequip. Ritorna solo la lista strutturata.
    """
    # Build slug → min_level (Legendary catalog post-apply)
    min_lvl_map = {
        it["slug"]: int(it.get("min_level") or 0)
        for it in db.items.find(
            {"rarity": "Legendary"},
            {"_id": 0, "slug": 1, "min_level": 1},
        )
    }
    leg_slugs = list(min_lvl_map.keys())

    orphans: list[dict] = []
    guilds_impacted: set[str] = set()
    adv_ids_impacted: set[str] = set()
    unique_items_impacted: Counter = Counter()

    # PATH A: inventory_items.equipped_by
    try:
        for inv in db.inventory_items.find(
            {"item_slug": {"$in": leg_slugs},
             "equipped_by": {"$exists": True, "$ne": None}},
            {"_id": 0, "item_slug": 1, "equipped_by": 1,
             "guild_id": 1, "id": 1},
        ):
            adv_id = inv.get("equipped_by")
            if not adv_id:
                continue
            adv = db.adventurers.find_one(
                {"id": adv_id},
                {"_id": 0, "id": 1, "name": 1, "level": 1, "guild_id": 1},
            )
            if not adv:
                continue
            adv_lvl = int(adv.get("level") or 1)
            required = min_lvl_map.get(inv["item_slug"], 0)
            if adv_lvl < required:
                orphans.append({
                    "item_slug": inv["item_slug"],
                    "required_min_level": required,
                    "adventurer_id": adv.get("id"),
                    "adventurer_name": adv.get("name"),
                    "adventurer_level": adv_lvl,
                    "gap_levels": required - adv_lvl,
                    "guild_id": inv.get("guild_id") or adv.get("guild_id"),
                    "inventory_item_id": inv.get("id"),
                    "source": "inventory_items.equipped_by",
                })
                guilds_impacted.add(orphans[-1]["guild_id"] or "?")
                adv_ids_impacted.add(orphans[-1]["adventurer_id"] or "?")
                unique_items_impacted[inv["item_slug"]] += 1
    except Exception:  # noqa: BLE001
        pass

    # PATH B: adventurer.equipped_items / equipment
    for a in db.adventurers.find(
        {"$or": [
            {"equipped_items": {"$exists": True, "$ne": []}},
            {"equipment": {"$exists": True, "$ne": {}}},
        ]},
        {"_id": 0, "id": 1, "name": 1, "level": 1, "guild_id": 1,
         "equipped_items": 1, "equipment": 1},
    ):
        adv_lvl = int(a.get("level") or 1)
        checked: list[tuple[str, Any]] = []
        for entry in (a.get("equipped_items") or []):
            slug = entry.get("slug") if isinstance(entry, dict) else entry
            checked.append((slug, entry))
        eq_dict = a.get("equipment") or {}
        if isinstance(eq_dict, dict):
            for slot, ref in eq_dict.items():
                if isinstance(ref, dict):
                    slug = ref.get("slug") or ref.get("item_slug")
                elif isinstance(ref, str):
                    slug = ref
                else:
                    slug = None
                checked.append((slug, {"slot": slot}))
        for slug, extra in checked:
            if slug in min_lvl_map:
                required = min_lvl_map[slug]
                if adv_lvl < required:
                    orphans.append({
                        "item_slug": slug,
                        "required_min_level": required,
                        "adventurer_id": a.get("id"),
                        "adventurer_name": a.get("name"),
                        "adventurer_level": adv_lvl,
                        "gap_levels": required - adv_lvl,
                        "guild_id": a.get("guild_id"),
                        "extra": extra,
                        "source": "adventurer.equipment",
                    })
                    guilds_impacted.add(a.get("guild_id") or "?")
                    adv_ids_impacted.add(a.get("id") or "?")
                    unique_items_impacted[slug] += 1

    return {
        "min_level_catalog": min_lvl_map,
        "total_orphans": len(orphans),
        "unique_adventurers_impacted": len(adv_ids_impacted),
        "unique_guilds_impacted": len(guilds_impacted),
        "unique_items_impacted": dict(unique_items_impacted),
        "orphans": orphans,
    }


def _render_md(data: dict) -> str:
    dist = data["adv_distribution"]
    leg = data["legendary_equipped"]
    orp = data["orphaned"]
    bands_str = "\n".join(
        f"- **{k}**: {v}" for k, v in sorted(dist["bands"].items())
    )
    by_slug_str = "\n".join(
        f"- `{k}`: {v} istanze"
        for k, v in sorted(
            leg["by_item_slug"].items(), key=lambda x: -x[1]
        )
    ) or "- (nessun Legendary attualmente equipaggiato)"

    if orp["orphans"]:
        orphan_rows = "\n".join(
            f"| `{o['item_slug']}` | lv{o['required_min_level']} | "
            f"`{o['adventurer_id']}` | {o.get('adventurer_name') or '?'} | "
            f"lv{o['adventurer_level']} | -{o['gap_levels']} | "
            f"`{o.get('guild_id') or '?'}` |"
            for o in orp["orphans"]
        )
        orphan_table = (
            "| item_slug | required min_lvl | adv_id | adv_name | "
            "adv_lvl | gap | guild_id |\n"
            "|---|---:|---|---|---:|---:|---|\n"
            + orphan_rows
        )
    else:
        orphan_table = "**Nessun orphan Legendary rilevato.** ✅"

    return f"""# Round 16.5 P0 — Section 19 Data Collection (READ-ONLY)

**Data generazione**: {data['meta']['run_at']}
**DB**: `{data['meta']['db_name']}`
**Script**: `/app/backend/app/scripts/round165_section19_data_collection.py`

> ⚠️  Questo report è **read-only**. Nessun unequip automatico eseguito.
> Le eventuali decisioni sui Legendary orfani sono elencate nel report
> finale `round165_p0_final_report.md`.

---

## 1. Distribuzione livelli avventurieri

- Totale avventurieri: **{dist['total_adventurers']}**
  (attivi: {dist['active']}, retired: {dist['retired']})
- Statistiche (attivi): {dist['stats']}

### Bande

{bands_str or '- (nessun dato)'}

---

## 2. Legendary equipaggiati (istanze)

- Fonte dati usata: `{leg['source_used']}`
- Totale istanze equipaggiate: **{leg['total_legendary_equipped']}**

{by_slug_str}

---

## 3. Orphaned Legendaries (adv sotto il nuovo `min_level`)

- Totale istanze orfane: **{orp['total_orphans']}**
- Avventurieri unici impattati: **{orp['unique_adventurers_impacted']}**
- Gilde uniche impattate: **{orp['unique_guilds_impacted']}**
- Item unici impattati: {orp['unique_items_impacted'] or '(nessuno)'}

### Tabella dettaglio

{orphan_table}

**Catalogo `min_level` di riferimento** (post-apply R16.5 P0):
```
{json.dumps(orp['min_level_catalog'], indent=2, sort_keys=True)}
```

---

## Note metodologiche

1. La distinzione tra fonti (inventory_items vs adventurer.equipment) è
   dovuta a due schemi possibili nel codebase. Lo script prova entrambi
   e usa il path con più dati.
2. `is_retired=True` esclude gli avventurieri in pensione dal conteggio
   attivo, ma NON dagli orphan check (non dovrebbero avere equip in ogni
   caso, ma li flagghiamo comunque per completezza).
3. Nessuna scrittura è stata eseguita sul DB. Le write methods di
   pymongo sono state monkey-patched all'avvio dello script.
"""


# ═════════════════════════════════════════════════════════════════════
# 3. MAIN
# ═════════════════════════════════════════════════════════════════════


def main() -> int:
    args = _parse_args()
    _enforce_read_only(args)
    _patch_write_methods_forbidden()

    t0 = time.time()
    client, db = _connect_db()
    print(f"[section19] connected to DB: {db.name}")

    adv_dist = _adventurer_level_distribution(db)
    leg_equipped = _legendary_equipped_distribution(db)
    orphaned = _find_orphaned_legendaries(db)

    elapsed = round(time.time() - t0, 3)
    meta = {
        "run_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "db_name": db.name,
        "elapsed_seconds": elapsed,
        "mode": "read-only",
    }
    data = {
        "meta": meta,
        "adv_distribution": adv_dist,
        "legendary_equipped": leg_equipped,
        "orphaned": orphaned,
    }

    md_path = Path("/app/memory/round165_missing_data_section19.md")
    json_path = Path("/app/memory/round165_missing_data_section19.json")
    md_path.write_text(_render_md(data))
    json_path.write_text(json.dumps(data, indent=2, default=str))

    print(f"[section19] adv_distribution bands: {adv_dist['bands']}")
    print(f"[section19] legendary equipped total: "
          f"{leg_equipped['total_legendary_equipped']}")
    print(f"[section19] orphaned legendaries: {orphaned['total_orphans']}")
    print(f"[section19] impacted adv={orphaned['unique_adventurers_impacted']} "
          f"guilds={orphaned['unique_guilds_impacted']}")
    print(f"[section19] md   : {md_path}")
    print(f"[section19] json : {json_path}")
    print(f"[section19] elapsed: {elapsed}s")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
