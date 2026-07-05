"""R18.3d — Phase B3 · Apply Metadata (append-only SAFE fields).

Correzione Q10.b applicata: registry ora ha 27 classi canoniche + legacy
separate. L'apply scope opera SOLO sull'intersezione:

    canonical_classes ∩ live_catalog (via `exists_in_live_db=true`)

Legacy live classes sono documentate ma NON toccate (guard esplicito).

SIBLING SCRIPT — NOT SEALED YET. Sealing è B5 gate (PM approval).

Fields applied via `$set` (append-only):
    * role_display_it
    * class_role_tags
    * design_primary_stat_it
    * design_secondary_stats_it
    * stat_role_registry_source_round

BLOCKED fields (guard hard-stop, fail-fast):
    primary_stat, secondary_stats, role, base_strength, base_agility,
    base_intellect, base_endurance, base_faith, is_playable, is_active,
    is_canonical

Legacy live hard-stop: qualsiasi slug in `legacy_live_slugs_hard_stop`
del registry provoca un rifiuto immediato (exit 22).

CLI:
    python -m app.scripts.round18_3d_apply_metadata --dry-run        # default
    python -m app.scripts.round18_3d_apply_metadata --apply \\
        --i-understand-this-will-write-metadata

Exit codes:
    0   OK (dry-run or apply successful)
    20  registry file missing / invalid
    21  guard hard-stop triggered (BLOCKED field in payload)
    22  legacy live slug leaked into apply plan
    30  --apply without ack flag
    31  backup path failure
    40  DB error

Author: e1_dev (R18.3d Phase B3, corr. Q10.b)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

REGISTRY_PATH = Path("/app/memory/r18_3d_stat_role_mapping_registry.json")
BACKUP_DIR_BASE = Path("/app/backend/backups")

SAFE_FIELDS = {
    "role_display_it",
    "class_role_tags",
    "design_primary_stat_it",
    "design_secondary_stats_it",
    "stat_role_registry_source_round",
}

BLOCKED_FIELDS = {
    "primary_stat",
    "secondary_stats",
    "role",
    "base_strength",
    "base_agility",
    "base_intellect",
    "base_endurance",
    "base_faith",
    "is_playable",
    "is_active",
    "is_canonical",
    "VALID_ROLES",
}

SOURCE_ROUND_TAG = "R18.3d Phase B"


class GuardHardStop(RuntimeError):
    """Raised when payload attempts to touch a BLOCKED field."""


class LegacyLiveLeak(RuntimeError):
    """Raised when apply plan includes a legacy live slug."""


def _guard_payload(payload: dict[str, Any]) -> None:
    for k in payload:
        if k in BLOCKED_FIELDS:
            raise GuardHardStop(
                f"BLOCKED field in payload: {k!r}. Refusing apply."
            )


def _build_payload_for(entry: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "role_display_it": entry.get("role_display_it"),
        "class_role_tags": entry.get("class_role_tags") or [],
        "design_primary_stat_it": entry.get("design_primary_stat_it"),
        "design_secondary_stats_it": entry.get("design_secondary_stats_it") or [],
        "stat_role_registry_source_round": SOURCE_ROUND_TAG,
    }
    return payload


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        print(f"ERROR: registry missing at {REGISTRY_PATH}")
        sys.exit(20)
    try:
        return json.loads(REGISTRY_PATH.read_bytes())
    except json.JSONDecodeError as exc:
        print(f"ERROR: registry not valid JSON: {exc}")
        sys.exit(20)


def _plan_apply(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Build apply plan for canonical classes that exist in live DB.
    Legacy live classes are NEVER included in the plan (guard).
    """
    scope = registry.get("safe_metadata_fields_apply_scope") or {}
    eligible = set(scope.get("eligible_apply_slugs") or [])
    legacy_hardstop = set(scope.get("legacy_live_slugs_hard_stop") or [])

    plan: list[dict[str, Any]] = []
    for entry in registry.get("canonical_classes", []):
        slug = entry.get("slug")
        if not slug:
            continue
        if slug in legacy_hardstop:
            # canonical slugs should never overlap with legacy hardstop;
            # if this ever happens, fail fast
            raise LegacyLiveLeak(
                f"canonical slug {slug!r} appears in legacy_live_slugs_hard_stop"
            )
        if not entry.get("exists_in_live_db"):
            continue
        if eligible and slug not in eligible:
            continue
        payload = _build_payload_for(entry)
        _guard_payload(payload)
        plan.append({"slug": slug, "payload": payload})

    # Belt & suspenders: verify no legacy slug ends up in plan.
    plan_slugs = {p["slug"] for p in plan}
    leaks = plan_slugs & legacy_hardstop
    if leaks:
        raise LegacyLiveLeak(
            f"legacy slugs leaked into apply plan: {sorted(leaks)}"
        )
    return plan


async def _snapshot_pre_apply(db, slugs: list[str], backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_file = backup_dir / f"adventurer_classes_pre_apply_{ts}.jsonl"
    docs = await db.adventurer_classes.find(
        {"slug": {"$in": slugs}}
    ).to_list(None)
    with snapshot_file.open("w") as f:
        for d in docs:
            d.pop("_id", None)
            f.write(json.dumps(d, default=str) + "\n")
    return snapshot_file


async def _apply_all(db, plan: list[dict[str, Any]]) -> dict[str, int]:
    modified = 0
    skipped_no_doc = 0
    for item in plan:
        _guard_payload(item["payload"])
        res = await db.adventurer_classes.update_one(
            {"slug": item["slug"]},
            {"$set": item["payload"]},
        )
        if res.matched_count == 0:
            skipped_no_doc += 1
        else:
            modified += 1
    return {"modified": modified, "skipped_no_doc": skipped_no_doc}


async def _emit_audit(db, plan_count: int, apply_id: str) -> None:
    now = datetime.now(timezone.utc)
    doc = {
        "id": f"r18_3d_metadata_{apply_id}",
        "event_type": "R18_3D_METADATA_APPLIED",
        "actor_user_id": None,
        "actor_guild_id": None,
        "metadata": {
            "apply_id": apply_id,
            "fields_added": sorted(SAFE_FIELDS),
            "class_count": plan_count,
            "source_round": SOURCE_ROUND_TAG,
            "correction_applied": "Q10.b canonical=27",
        },
        "created_at": now.isoformat(),
    }
    try:
        await db.audit_log.insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: audit emit failed: {exc}")


async def _main_async(args: argparse.Namespace) -> int:
    registry = _load_registry()

    print("── R18.3d Phase B3 · Apply Metadata (Q10.b canonical=27) ──")
    print(f"registry: {REGISTRY_PATH}")
    print(f"mode:     {'APPLY' if args.apply else 'DRY_RUN'}")
    meta = registry.get("meta") or {}
    print(f"canonical_classes={meta.get('canonical_classes')} "
          f"live_catalog={meta.get('live_catalog_classes')} "
          f"canonical_live={meta.get('canonical_live_count')} "
          f"legacy_live={meta.get('legacy_live_classes_count')} "
          f"design_only={meta.get('design_only_classes_count')}")

    try:
        plan = _plan_apply(registry)
    except GuardHardStop as exc:
        print(f"GUARD HARD-STOP: {exc}")
        return 21
    except LegacyLiveLeak as exc:
        print(f"LEGACY LIVE LEAK: {exc}")
        return 22

    print(f"plan: {len(plan)} canonical class(es) eligible "
          f"(intersezione canonical ∩ live_catalog)")
    for it in plan:
        print(f"  · {it['slug']}: {sorted(it['payload'].keys())}")

    if not args.apply:
        print()
        print("DRY_RUN complete. No DB writes performed. exit=0")
        return 0

    if not args.i_understand:
        print(
            "ERROR: --apply requires --i-understand-this-will-write-metadata"
        )
        return 30

    env = dotenv_values("/app/backend/.env")
    client = AsyncIOMotorClient(env["MONGO_URL"])
    db = client[env["DB_NAME"]]

    apply_id = uuid.uuid4().hex
    backup_dir = BACKUP_DIR_BASE / f"r18_3d_metadata_{apply_id}"
    try:
        snap = await _snapshot_pre_apply(
            db, [it["slug"] for it in plan], backup_dir
        )
        print(f"backup snapshot: {snap}")
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: backup snapshot failed: {exc}")
        return 31

    try:
        result = await _apply_all(db, plan)
    except GuardHardStop as exc:
        print(f"GUARD HARD-STOP (during apply): {exc}")
        return 21
    except LegacyLiveLeak as exc:
        print(f"LEGACY LIVE LEAK (during apply): {exc}")
        return 22
    except Exception as exc:  # noqa: BLE001
        print(f"DB ERROR: {exc}")
        return 40

    await _emit_audit(db, len(plan), apply_id)

    print()
    print(f"APPLY done. modified={result['modified']} "
          f"skipped_no_doc={result['skipped_no_doc']}")
    print(f"apply_id={apply_id}")
    client.close()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R18.3d Phase B3 metadata apply (SAFE, canonical∩live)",
    )
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", default=False)
    parser.add_argument(
        "--i-understand-this-will-write-metadata",
        dest="i_understand",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False
    exit_code = asyncio.run(_main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
