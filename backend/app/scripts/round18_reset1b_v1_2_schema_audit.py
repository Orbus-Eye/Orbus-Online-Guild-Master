"""
R18.Reset.1b.hotfix.v1_2 — POST-APPLY SCHEMA AUDIT (READ-ONLY).

Compara schema pre-apply (backup JSONL fresh 20260705T134230Z) vs
schema post-apply (live DB) sui 3360 adventurers rigenerati.
Verifica anche mapping class_slug → adventurer_classes.id.

READ-ONLY: nessuna scrittura DB, nessun tocco sigilli.
"""
from __future__ import annotations

import asyncio
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

PRE_APPLY_JSONL = "/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z/adventurers.jsonl"
SAFE_CLASSES = ["alchemist", "bard", "druid", "mage", "monk", "paladin",
                "priest", "ranger", "rogue", "warlock", "warrior"]
STAT_KEYS = ["strength", "agility", "intellect", "endurance", "faith"]
BASE_STAT_KEYS = ["base_strength", "base_agility", "base_intellect", "base_endurance", "base_faith"]

OUT_JSON = "/app/memory/r18_reset1b_v1_2_post_apply_schema_audit.json"


def _type(v) -> str:
    if v is None:
        return "null"
    return type(v).__name__


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    now_iso = datetime.now(timezone.utc).isoformat()

    # ── PRE-APPLY ANALYSIS (JSONL) ──
    pre_field_presence: Counter[str] = Counter()  # non-null count
    pre_field_exists: Counter[str] = Counter()   # exists at all (incl. null)
    pre_field_null: Counter[str] = Counter()
    pre_field_type_by_field: dict[str, Counter[str]] = defaultdict(Counter)
    pre_sample_doc = None
    pre_total = 0
    with open(PRE_APPLY_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            pre_total += 1
            if pre_sample_doc is None:
                # pick a doc that has adventurer_class_id populated for reference
                if d.get("adventurer_class_id"):
                    pre_sample_doc = d
            for k, v in d.items():
                pre_field_exists[k] += 1
                if v is None:
                    pre_field_null[k] += 1
                else:
                    pre_field_presence[k] += 1
                    pre_field_type_by_field[k][_type(v)] += 1
        # fallback if no doc with adventurer_class_id found in first pass
        if pre_sample_doc is None:
            with open(PRE_APPLY_JSONL) as g:
                for line in g:
                    d = json.loads(line)
                    if d.get("adventurer_class_id"):
                        pre_sample_doc = d
                        break

    # ── POST-APPLY LIVE DB ANALYSIS ──
    post_field_presence: Counter[str] = Counter()
    post_field_exists: Counter[str] = Counter()
    post_field_null: Counter[str] = Counter()
    post_field_type_by_field: dict[str, Counter[str]] = defaultdict(Counter)
    post_sample_doc = None
    post_total = 0
    async for d in db.adventurers.find({}):
        d.pop("_id", None)
        post_total += 1
        if post_sample_doc is None:
            post_sample_doc = d
        for k, v in d.items():
            post_field_exists[k] += 1
            if v is None:
                post_field_null[k] += 1
            else:
                post_field_presence[k] += 1
                post_field_type_by_field[k][_type(v)] += 1

    # ── SCHEMA DIFF ──
    all_fields = sorted(set(pre_field_exists.keys()) | set(post_field_exists.keys()))
    schema_diff = []
    for f in all_fields:
        pe = pre_field_exists.get(f, 0)
        pv = pre_field_presence.get(f, 0)  # non-null pre
        pn = pre_field_null.get(f, 0)
        pe_pct = round(100 * pe / pre_total, 2) if pre_total else 0
        pv_pct = round(100 * pv / pre_total, 2) if pre_total else 0

        ppe = post_field_exists.get(f, 0)
        ppv = post_field_presence.get(f, 0)
        ppn = post_field_null.get(f, 0)
        ppe_pct = round(100 * ppe / post_total, 2) if post_total else 0
        ppv_pct = round(100 * ppv / post_total, 2) if post_total else 0

        type_pre = dict(pre_field_type_by_field.get(f) or {})
        type_post = dict(post_field_type_by_field.get(f) or {})

        # classify
        status = "OK"
        notes = []
        if ppe == 0 and pe > 0:
            status = "MISSING_POST"
            notes.append(f"field lost 100% post-apply (was in {pe_pct}% pre)")
        elif ppv == 0 and pv > 0:
            status = "NULLIFIED_POST"
            notes.append(f"non-null pre={pv_pct}%, now 0% non-null (all null or missing)")
        elif ppv_pct < pv_pct - 5:
            status = "DEGRADED_COVERAGE"
            notes.append(f"non-null coverage dropped {pv_pct}% → {ppv_pct}%")
        elif type_pre and type_post and set(type_pre.keys()) != set(type_post.keys()):
            status = "TYPE_MISMATCH"
            notes.append(f"types differ: pre={list(type_pre.keys())} post={list(type_post.keys())}")

        schema_diff.append({
            "field": f,
            "pre_exists_pct": pe_pct,
            "pre_nonnull_pct": pv_pct,
            "post_exists_pct": ppe_pct,
            "post_nonnull_pct": ppv_pct,
            "type_pre": type_pre,
            "type_post": type_post,
            "status": status,
            "notes": "; ".join(notes),
        })

    # ── CATALOG MAPPING: class_slug → adventurer_class_id ──
    # try common collection names
    class_mapping = {"queries_attempted": [], "mapping_by_slug": {}, "collection_used": None,
                     "total_docs_in_catalog": 0, "safe_classes_mapped": 0, "safe_classes_unmapped": [],
                     "duplicates_by_slug": {}}
    candidate_collections = ["adventurer_classes", "adventurer_class_catalog", "classes",
                              "adventurer_class", "class_catalog"]
    for cname in candidate_collections:
        try:
            cnt = await db[cname].count_documents({})
        except Exception as e:
            class_mapping["queries_attempted"].append({"collection": cname, "error": str(e)})
            continue
        class_mapping["queries_attempted"].append({"collection": cname, "count": cnt})
        if cnt > 0 and class_mapping["collection_used"] is None:
            class_mapping["collection_used"] = cname
            class_mapping["total_docs_in_catalog"] = cnt

    if class_mapping["collection_used"]:
        coll = class_mapping["collection_used"]
        # collect docs
        by_slug: dict[str, list] = defaultdict(list)
        first_doc = None
        async for doc in db[coll].find({}):
            doc.pop("_id", None)
            if first_doc is None:
                first_doc = doc
            slug = doc.get("slug") or doc.get("class_slug") or doc.get("name")
            if slug:
                by_slug[slug].append({
                    "id": doc.get("id") or doc.get("class_id") or doc.get("_id_str") or doc.get("adventurer_class_id"),
                    "slug": slug,
                    "base_strength": doc.get("base_strength"),
                    "base_agility": doc.get("base_agility"),
                    "base_intellect": doc.get("base_intellect"),
                    "base_endurance": doc.get("base_endurance"),
                    "base_faith": doc.get("base_faith"),
                    "is_hidden": doc.get("is_hidden"),
                    "raw_keys": sorted(doc.keys()),
                })
        class_mapping["catalog_sample_doc"] = first_doc
        for safe in SAFE_CLASSES:
            matches = by_slug.get(safe, [])
            if not matches:
                class_mapping["mapping_by_slug"][safe] = {"found": False, "candidates": 0}
                class_mapping["safe_classes_unmapped"].append(safe)
            else:
                unique_ids = {m["id"] for m in matches}
                base_stats_ok = all(
                    all(m.get(bk) is not None for bk in BASE_STAT_KEYS) for m in matches
                )
                if len(matches) > 1:
                    class_mapping["duplicates_by_slug"][safe] = len(matches)
                class_mapping["mapping_by_slug"][safe] = {
                    "found": True,
                    "candidates": len(matches),
                    "id": matches[0]["id"],
                    "id_unique_across_matches": len(unique_ids) == 1,
                    "base_stats_populated": base_stats_ok,
                    "base_stats": {k: matches[0].get(k) for k in BASE_STAT_KEYS},
                    "is_hidden": matches[0].get("is_hidden"),
                }
                if matches[0]["id"]:
                    class_mapping["safe_classes_mapped"] += 1
                else:
                    class_mapping["safe_classes_unmapped"].append(safe + "(no_id)")

    # ── STATIC CODE ANALYSIS ──
    code_refs = {
        "adventurer_public_required_fields": [],
        "adventurer_base_power_required_fields": [],
        "files_grepped": [],
    }
    svc_path = Path("/app/backend/app/adventurers/services.py")
    if svc_path.exists():
        code_refs["files_grepped"].append(str(svc_path))
        src = svc_path.read_text()
        # attempt to isolate adventurer_public function via naive parsing
        for func_name, target in [("adventurer_public", "adventurer_public_required_fields"),
                                   ("adventurer_base_power", "adventurer_base_power_required_fields")]:
            marker = f"def {func_name}("
            idx = src.find(marker)
            if idx < 0:
                code_refs[target] = ["<function not found>"]
                continue
            # take next ~150 lines
            snippet = src[idx: idx + 6000]
            # find doc[...] access patterns
            import re
            keys = re.findall(r'doc\[[\'"](\w+)[\'"]\]', snippet)
            keys_get = re.findall(r'doc\.get\([\'"](\w+)[\'"]', snippet)
            code_refs[target] = {
                "hard_access_via_doc[key]": sorted(set(keys)),
                "soft_access_via_doc.get()": sorted(set(keys_get)),
            }

    # ── SIDE-BY-SIDE SAMPLE ──
    side_by_side = {
        "pre_apply_sample": pre_sample_doc,
        "post_apply_sample": post_sample_doc,
    }

    # ── CLASSIFY MISSING FIELDS ──
    missing_universally = [d["field"] for d in schema_diff
                           if d["status"] in ("MISSING_POST", "NULLIFIED_POST")]
    missing_hard_used = set()
    if isinstance(code_refs["adventurer_public_required_fields"], dict):
        missing_hard_used.update(code_refs["adventurer_public_required_fields"].get("hard_access_via_doc[key]", []))
    if isinstance(code_refs["adventurer_base_power_required_fields"], dict):
        missing_hard_used.update(code_refs["adventurer_base_power_required_fields"].get("hard_access_via_doc[key]", []))
    runtime_critical = [m for m in missing_universally if m in missing_hard_used]
    non_critical = [m for m in missing_universally if m not in missing_hard_used]

    # ── FRESH BACKUP MANIFEST CHECK ──
    import hashlib
    fresh_manifest_path = Path("/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z/manifest.json")
    fresh_manifest_status = {"path": str(fresh_manifest_path), "exists": fresh_manifest_path.exists(),
                              "files_verified": 0, "mismatches": []}
    if fresh_manifest_path.exists():
        m = json.loads(fresh_manifest_path.read_text())
        for entry in m.get("collections", []):
            expected = entry.get("sha256")
            fpath = Path(entry.get("file") or "")
            if not fpath.exists():
                fpath = fresh_manifest_path.parent / Path(entry.get("file", "")).name
            if not fpath.exists() or not expected:
                fresh_manifest_status["mismatches"].append({"file": entry.get("name"), "error": "missing"})
                continue
            h = hashlib.sha256()
            with fpath.open("rb") as f:
                for line in f:
                    h.update(line.rstrip(b"\n"))
            actual = h.hexdigest()
            if actual != expected:
                fresh_manifest_status["mismatches"].append({"file": entry.get("name"), "expected": expected, "actual": actual})
            fresh_manifest_status["files_verified"] += 1

    result = {
        "generated_at": now_iso,
        "apply_id_v1_2": "5815c73c-dae7-447c-ac3c-70455d3099a3",
        "pre_apply_backup": PRE_APPLY_JSONL,
        "pre_apply_total_docs": pre_total,
        "post_apply_total_docs": post_total,
        "side_by_side_sample": side_by_side,
        "schema_diff": schema_diff,
        "missing_fields_summary": {
            "missing_universally_count": len(missing_universally),
            "missing_universally": missing_universally,
            "runtime_critical_count": len(runtime_critical),
            "runtime_critical": runtime_critical,
            "non_critical_count": len(non_critical),
            "non_critical": non_critical,
        },
        "class_mapping": class_mapping,
        "code_refs": code_refs,
        "fresh_backup_manifest": fresh_manifest_status,
    }

    Path(OUT_JSON).write_text(json.dumps(result, indent=2, default=str))
    print(f"Audit JSON written -> {OUT_JSON}")
    print()
    print("=== SUMMARY ===")
    print(f"pre_total={pre_total} post_total={post_total}")
    print(f"missing_universally={len(missing_universally)} → {missing_universally}")
    print(f"runtime_critical={len(runtime_critical)} → {runtime_critical}")
    print(f"non_critical={len(non_critical)} → {non_critical}")
    print(f"catalog collection used: {class_mapping['collection_used']} "
          f"(total={class_mapping['total_docs_in_catalog']})")
    print(f"safe classes mapped: {class_mapping['safe_classes_mapped']}/11")
    print(f"unmapped: {class_mapping['safe_classes_unmapped']}")
    print(f"duplicates by slug: {class_mapping['duplicates_by_slug']}")
    print(f"fresh backup manifest: files_verified={fresh_manifest_status['files_verified']} "
          f"mismatches={len(fresh_manifest_status['mismatches'])}")


if __name__ == "__main__":
    asyncio.run(main())
