"""ROUND 16.5.4b — ADJ-2 Legendary min-level backfill.

Fixes the six Legendary equippables seeded with
`required_adventurer_level: 1`, which bypass the R16.5 level gate.

Whitelist (slug → target required_adventurer_level):
    legendary_sword_alveora   → 9
    legendary_staff_efreto    → 9
    legendary_armor_ambash    → 8
    legendary_ring_velur      → 8
    legendary_amulet_nathos   → 8
    legendary_cape_aveol      → 8

Contract:
  * dry-run by default. `--apply` required to write.
  * Only two fields are touched: `required_adventurer_level` + `updated_at`.
  * Any slug not in the whitelist is left untouched. Anything unexpected
    goes into `unresolved` list of the report.
  * Pre-change snapshot saved to `/app/memory/round1654b_adj2_snapshot.json`
    with SHA256 checksum.
  * Idempotent: second `--apply` results in zero writes.
  * Emits audit event `LEGENDARY_LEVEL_GATE_BACKFILL_APPLIED`.

Usage:
    python -m app.scripts.round1654b_seed_integrity --dry-run
    python -m app.scripts.round1654b_seed_integrity --apply
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

# ── Whitelist — approved target levels (STEP 2 spec) ─────────────────────
TARGET_LEVELS: dict[str, int] = {
    "legendary_sword_alveora": 9,
    "legendary_staff_efreto": 9,
    "legendary_armor_ambash": 8,
    "legendary_ring_velur": 8,
    "legendary_amulet_nathos": 8,
    "legendary_cape_aveol": 8,
}

SNAPSHOT_PATH = Path("/app/memory/round1654b_adj2_snapshot.json")
AUDIT_EVENT = "LEGENDARY_LEVEL_GATE_BACKFILL_APPLIED"


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _load_current(db) -> list[dict]:
    slugs = sorted(TARGET_LEVELS.keys())
    rows = await db.items.find(
        {"slug": {"$in": slugs}},
        {"_id": 0, "id": 1, "slug": 1,
         "required_adventurer_level": 1, "rarity": 1, "item_type": 1},
    ).sort([("slug", 1)]).to_list(len(slugs))
    return rows


def _plan_diff(rows: list[dict]) -> tuple[list[dict], list[str], list[dict]]:
    """Return (plan, missing_slugs, noop_items).

    - plan: items whose `required_adventurer_level` needs update.
    - missing_slugs: whitelisted slugs not found in DB (surface as
      unresolved).
    - noop_items: whitelisted slugs already at or above target.
    """
    plan: list[dict] = []
    noop: list[dict] = []
    found_slugs = {r["slug"] for r in rows}
    for r in rows:
        slug = r["slug"]
        target = TARGET_LEVELS[slug]
        old = int(r.get("required_adventurer_level", 1) or 1)
        if old == target:
            noop.append({"slug": slug, "current": old, "target": target,
                         "reason": "already_at_target"})
        elif old > target:
            # Never downgrade. Log as noop with warning.
            noop.append({"slug": slug, "current": old, "target": target,
                         "reason": "current_above_target_no_downgrade"})
        else:
            plan.append({
                "slug": slug,
                "id": r.get("id"),
                "rarity": r.get("rarity"),
                "item_type": r.get("item_type"),
                "old_required_level": old,
                "new_required_level": target,
                "delta": target - old,
            })
    missing = sorted(set(TARGET_LEVELS.keys()) - found_slugs)
    return plan, missing, noop


def _print_preview(plan: list[dict], missing: list[str],
                   noop: list[dict]) -> None:
    print("\n" + "=" * 72)
    print("  R16.5.4b ADJ-2 Legendary min-level backfill — PREVIEW")
    print("=" * 72)
    if plan:
        print(f"\n  Item da aggiornare ({len(plan)}):")
        print(f"    {'slug':<30} {'old':>4}  →  {'new':>4}  Δ")
        print(f"    {'-'*30} {'-'*4}     {'-'*4}  {'-'*2}")
        for p in plan:
            print(f"    {p['slug']:<30} {p['old_required_level']:>4}  →  "
                  f"{p['new_required_level']:>4}  {p['delta']:+d}")
    else:
        print("\n  Nessun item da aggiornare (idempotenza OK).")
    if noop:
        print(f"\n  Noop ({len(noop)}) — già al target o oltre:")
        for n in noop:
            print(f"    {n['slug']:<30} current={n['current']} "
                  f"target={n['target']} ({n['reason']})")
    if missing:
        print(f"\n  ⚠ Whitelist slug NON trovati nel DB ({len(missing)}):")
        for s in missing:
            print(f"    - {s}")
    print("=" * 72)


async def _write_snapshot(rows: list[dict], plan: list[dict]) -> dict:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": _utc_iso_now(),
        "round": "16.5.4b",
        "purpose": "ADJ-2 Legendary min-level pre-change snapshot",
        "whitelist": TARGET_LEVELS,
        "before": rows,
        "planned_updates": plan,
    }
    payload_json = json.dumps(payload, indent=2, sort_keys=True,
                              ensure_ascii=False, default=str)
    checksum = _sha256(payload_json)
    SNAPSHOT_PATH.write_text(payload_json, encoding="utf-8")
    return {"path": str(SNAPSHOT_PATH), "sha256": checksum,
            "bytes": len(payload_json)}


async def _apply(db, plan: list[dict]) -> list[dict]:
    """Apply the plan atomically per-item. Returns actually-modified rows."""
    applied: list[dict] = []
    ts = _utc_iso_now()
    for p in plan:
        # Whitelist enforcement: assert slug is in TARGET_LEVELS and target
        # matches (defensive; the plan is already whitelisted upstream).
        if p["slug"] not in TARGET_LEVELS:
            continue
        if p["new_required_level"] != TARGET_LEVELS[p["slug"]]:
            continue
        res = await db.items.update_one(
            {"slug": p["slug"],
             "required_adventurer_level": p["old_required_level"]},
            {"$set": {
                "required_adventurer_level": p["new_required_level"],
                "updated_at": ts,
            }},
        )
        if res.modified_count == 1:
            applied.append(p)
    return applied


async def _write_audit(db, applied: list[dict], snapshot_info: dict,
                       dry_run: bool) -> None:
    try:
        await db.audit_log.insert_one({
            "event_type": AUDIT_EVENT,
            "occurred_at": _utc_iso_now(),
            "source": "scripts.round1654b_seed_integrity",
            "dry_run": dry_run,
            "applied_count": len(applied),
            "applied_slugs": [a["slug"] for a in applied],
            "snapshot": snapshot_info,
        })
    except Exception as exc:  # noqa: BLE001
        # Best-effort audit; never fail the migration on audit write.
        print(f"  ⚠ audit_log insert failed ({type(exc).__name__}): {exc}")


async def run(dry_run: bool = True) -> dict:
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        rows = await _load_current(db)
        plan, missing, noop = _plan_diff(rows)
        _print_preview(plan, missing, noop)
        snapshot_info = await _write_snapshot(rows, plan)
        print(f"\n  Snapshot: {snapshot_info['path']}")
        print(f"  SHA256:   {snapshot_info['sha256']}")
        applied: list[dict] = []
        if dry_run:
            print("\n  DRY-RUN: nessuna scrittura eseguita. "
                  "Usa --apply per applicare.")
        else:
            print(f"\n  APPLY: aggiorno {len(plan)} item…")
            applied = await _apply(db, plan)
            print(f"  ✔ Aggiornati: {len(applied)} item.")
        await _write_audit(db, applied, snapshot_info, dry_run)
        return {
            "mode": "dry-run" if dry_run else "apply",
            "plan": plan,
            "missing": missing,
            "noop": noop,
            "applied": applied,
            "snapshot": snapshot_info,
        }
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R16.5.4b ADJ-2 Legendary min-level backfill",
    )
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true", default=True,
                     help="Preview only (default).")
    grp.add_argument("--apply", action="store_true", default=False,
                     help="Actually apply the whitelist backfill.")
    args = parser.parse_args()
    dry = not args.apply
    asyncio.run(run(dry_run=dry))
    return 0


if __name__ == "__main__":
    sys.exit(main())
