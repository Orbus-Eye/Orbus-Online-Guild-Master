"""14-point DB verification for R18.Reset.1b.hotfix.v1_3 REAL APPLY."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

CURRENT_APPLY_ID_V1_3 = "3e1e6462-694b-49d4-8e60-0045460c58d0"
STAT_KEYS = ["strength", "agility", "intellect", "endurance", "faith"]
POTION_ITEM_ID = "fd5cbdef-3146-483c-b1fd-217b4da0a59d"
SAFE_CLASSES = ["alchemist", "bard", "druid", "mage", "monk", "paladin",
                "priest", "ranger", "rogue", "warlock", "warrior"]
BACKUP_ROOT_V1_3_PREPATCH = Path("/tmp/orbus_v1_3_prepatch_backup_root.txt").read_text().strip()


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    checks = []

    def rec(idx, name, status, expected, actual, extra=None):
        e = {"check": idx, "name": name, "status": status,
             "expected": expected, "actual": actual}
        if extra is not None:
            e["extra"] = extra
        checks.append(e)

    # 1. Target patchato = 3360
    patched = await db.adventurers.count_documents({
        "r18_reset1b_hotfix_v1_3": True,
        "r18_reset1b_hotfix_v1_3_apply_id": CURRENT_APPLY_ID_V1_3,
    })
    rec(1, "target_patched_count", "PASS" if patched == 3360 else "FAIL", 3360, patched)

    # 2. adventurer_class_id presente + non-null su 3360
    v1_2_targets = await db.adventurers.count_documents({"r18_reset1b_hotfix_v1_2": True})
    valid_class_id = await db.adventurers.count_documents({
        "r18_reset1b_hotfix_v1_2": True,
        "adventurer_class_id": {"$exists": True, "$ne": None, "$type": "string"},
    })
    rec(2, "adventurer_class_id_present_nonnull",
        "PASS" if valid_class_id == 3360 else "FAIL", 3360, valid_class_id,
        extra={"total_v1_2_targets": v1_2_targets})

    # 3. experience presente su 3360
    exp_present = await db.adventurers.count_documents({
        "r18_reset1b_hotfix_v1_2": True,
        "experience": {"$exists": True},
    })
    exp_zero = await db.adventurers.count_documents({
        "r18_reset1b_hotfix_v1_2": True,
        "experience": 0,
    })
    rec(3, "experience_present_all",
        "PASS" if exp_present == 3360 and exp_zero == 3360 else "FAIL",
        {"present": 3360, "value_zero": 3360},
        {"present": exp_present, "value_zero": exp_zero})

    # 4. is_available=true on 3360
    is_avail_true = await db.adventurers.count_documents({
        "r18_reset1b_hotfix_v1_2": True,
        "is_available": True,
    })
    rec(4, "is_available_true_all", "PASS" if is_avail_true == 3360 else "FAIL", 3360, is_avail_true)

    # 5. no missing runtime-critical fields
    # (adventurer_public hard-access keys: id, guild_id, name, adventurer_class_id,
    # strength, agility, intellect, endurance, faith, created_at)
    RUNTIME_HARD_KEYS = ["id", "guild_id", "name", "adventurer_class_id",
                         "strength", "agility", "intellect", "endurance", "faith", "created_at"]
    missing_by_field = {}
    for k in RUNTIME_HARD_KEYS:
        c = await db.adventurers.count_documents({
            "r18_reset1b_hotfix_v1_2": True,
            k: {"$exists": False},
        })
        missing_by_field[k] = c
    all_zero = all(v == 0 for v in missing_by_field.values())
    rec(5, "no_missing_runtime_critical_keys",
        "PASS" if all_zero else "FAIL", "all zero", missing_by_field)

    # 6. mapping class_slug → adventurer_class_id = 11/11
    slug_id_map = {}
    for slug in SAFE_CLASSES:
        cat = await db.adventurer_classes.find_one({"slug": slug})
        cat_id = cat.get("id") if cat else None
        # count docs with this slug and this class_id
        matched = await db.adventurers.count_documents({
            "r18_reset1b_hotfix_v1_2": True,
            "class_slug": slug,
            "adventurer_class_id": cat_id,
        })
        expected_count = await db.adventurers.count_documents({
            "r18_reset1b_hotfix_v1_2": True,
            "class_slug": slug,
        })
        slug_id_map[slug] = {"cat_id": cat_id, "matched": matched, "expected": expected_count}
    all_mapped = all(m["matched"] == m["expected"] for m in slug_id_map.values())
    rec(6, "class_slug_to_class_id_mapping_11_11",
        "PASS" if all_mapped else "FAIL", "11/11 matched", slug_id_map)

    # 7. stats invariance
    stats_null_or_missing = 0
    for k in STAT_KEYS:
        c = await db.adventurers.count_documents({
            "r18_reset1b_hotfix_v1_2": True,
            "$or": [{k: {"$exists": False}}, {k: None}],
        })
        stats_null_or_missing += c
    rec(7, "stats_invariance_v1_2", "PASS" if stats_null_or_missing == 0 else "FAIL",
        0, stats_null_or_missing)

    # 8. gold total = 67200
    gold_total = 0
    async for d in db.guilds.aggregate([
        {"$group": {"_id": None, "t": {"$sum": "$gold"}}}
    ]):
        gold_total = int(d.get("t") or 0)
    rec(8, "gold_total_67200", "PASS" if gold_total == 67200 else "FAIL", 67200, gold_total)

    # 9. inventory kit = 672 doc
    kit_count = await db.inventory_items.count_documents({"item_id": POTION_ITEM_ID})
    rec(9, "inventory_kit_672_docs", "PASS" if kit_count == 672 else "FAIL", 672, kit_count)

    # 10. total quantity minor_healing_potion = 2016
    qty_total = 0
    async for d in db.inventory_items.aggregate([
        {"$match": {"item_id": POTION_ITEM_ID}},
        {"$group": {"_id": None, "t": {"$sum": "$quantity"}}}
    ]):
        qty_total = int(d.get("t") or 0)
    rec(10, "potion_total_qty_2016", "PASS" if qty_total == 2016 else "FAIL", 2016, qty_total)

    # 11. audit R18_STARTER_ROSTER_HOTFIX_APPLIED (1 record for current apply_id)
    ev_generic_query = {"event_type": "R18_STARTER_ROSTER_HOTFIX_APPLIED",
                        "metadata.apply_id": CURRENT_APPLY_ID_V1_3}
    ev_generic_count = await db.audit_log.count_documents(ev_generic_query)
    ev_generic_docs = await db.audit_log.find(
        ev_generic_query,
        {"_id": 0, "event_type": 1, "created_at": 1, "source": 1, "metadata": 1}
    ).to_list(length=3)
    rec(11, "audit_generic_applied_v1_3", "PASS" if ev_generic_count == 1 else "FAIL",
        1, ev_generic_count, extra={"sample": ev_generic_docs})

    # 12. audit R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3 (1 record)
    ev_v13_query = {"event_type": "R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3",
                    "metadata.apply_id": CURRENT_APPLY_ID_V1_3}
    ev_v13_count = await db.audit_log.count_documents(ev_v13_query)
    ev_v13_docs = await db.audit_log.find(
        ev_v13_query,
        {"_id": 0, "event_type": 1, "created_at": 1, "source": 1, "metadata": 1}
    ).to_list(length=3)
    rec(12, "audit_specific_applied_v1_3", "PASS" if ev_v13_count == 1 else "FAIL",
        1, ev_v13_count, extra={"sample": ev_v13_docs})

    # 13. no hard delete — archive collections unchanged
    archive_expected = {
        "adventurers_r18_archive": 3415,
        "inventory_items_r18_archive": 111,
        "expeditions_r18_archive": 17,
        "raids_r18_archive": 1,
    }
    archive_actual = {}
    all_ok = True
    for coll, exp in archive_expected.items():
        c = await db[coll].count_documents({})
        archive_actual[coll] = c
        if c != exp:
            all_ok = False
    # Also verify total live adventurers unchanged from post-v1.2
    live_advs = await db.adventurers.count_documents({})
    if live_advs != 3360:
        all_ok = False
    rec(13, "no_hard_delete_archive_intact",
        "PASS" if all_ok else "FAIL",
        {**archive_expected, "adventurers_live": 3360},
        {**archive_actual, "adventurers_live": live_advs})

    # 14. fresh backup pre-v1.3 sha256 still valid
    manifest_path = Path(BACKUP_ROOT_V1_3_PREPATCH) / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    mismatches = []
    for entry in manifest.get("collections", []):
        expected = entry["sha256"]
        fpath = Path(entry["file"])
        if not fpath.exists():
            fpath = manifest_path.parent / Path(entry["file"]).name
        h = hashlib.sha256()
        with fpath.open("rb") as f:
            for line in f:
                h.update(line.rstrip(b"\n"))
        if h.hexdigest() != expected:
            mismatches.append(entry.get("name"))
    rec(14, "prepatch_backup_sha256_intact",
        "PASS" if not mismatches else "FAIL", "no mismatch",
        {"mismatches": mismatches, "files_checked": len(manifest.get("collections", []))})

    # ── output ──
    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = total - passed
    print("=" * 78)
    print("R18.Reset.1b.hotfix.v1_3 REAL APPLY — 14-Point DB Verification")
    print("=" * 78)
    for c in checks:
        m = "✓" if c["status"] == "PASS" else "✗"
        print(f"[{m}] {c['check']:>2}. {c['name']:<40} {c['status']}")
    print("-" * 78)
    print(f"TOTAL: {passed}/{total} PASSED — verdict={'ALL_PASS' if failed == 0 else 'FAIL'}")
    if failed:
        print()
        print("FAIL DETAILS:")
        for c in checks:
            if c["status"] != "PASS":
                print(f"  {c['check']}. {c['name']}: expected={c['expected']} actual={c['actual']}")

    out = {
        "generated_at": "2026-07-05T14:59:00Z",
        "apply_id_v1_3": CURRENT_APPLY_ID_V1_3,
        "checks": checks,
        "summary": {"total": total, "passed": passed, "failed": failed,
                    "verdict": "ALL_PASS" if failed == 0 else "FAIL"},
    }
    Path("/app/memory/r18_reset1b_hotfix_v1_3_db_verification.json").write_text(
        json.dumps(out, indent=2, default=str))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
