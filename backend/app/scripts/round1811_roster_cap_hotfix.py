"""ROUND 18.1.1 — Roster Cap Canonical Formula Hotfix.

Fix additivo/idempotente. Corregge il campo source-of-truth per calcolare
`max_roster_cap` sulle guilds.

**Decisione PM (sigillata):**
    effective_level = max(guild.level or 0, guild.guild_level or 0, 1)
    max_roster_cap  = min(50, 10 + effective_level * 2)

La formula precedente (`guild_level or level or 1`) picchiava su
`guild_level` quando presente, ignorando `level` più alto. Effetto: guilds
reali con `level > guild_level` (es. `la lanterna di ferro` lvl=15/gl=6)
vedevano cap troppo basso (22) → falso grandfathering.

Scope:
  * Solo Block F di R18.1 (roster cap), tutto il resto invariato
  * Solo update dove `max_roster_cap` cambia effettivamente
  * `is_grandfathered` ricalcolato con nuova formula
  * `r18_roster_cap_recomputed_at` marker aggiunto per traceability
  * Idempotent: secondo apply = 0 modifiche
  * Feature flag `R18_REWORK_ENABLED` OFF preservato

Uso:
    python -m app.scripts.round1811_roster_cap_hotfix --dry-run
    python -m app.scripts.round1811_roster_cap_hotfix --apply
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _effective_level(guild: dict) -> int:
    return max(int(guild.get("level") or 0),
               int(guild.get("guild_level") or 0), 1)


def _new_cap(guild: dict) -> tuple[int, int]:
    eff = _effective_level(guild)
    return min(50, 10 + eff * 2), eff


async def _emit_audit(db, count: int, changes: list[dict]) -> None:
    """One audit_log event summarizing the hotfix run."""
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": "R18_ROSTER_CAP_RECOMPUTED",
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": count,
        "gold_delta": None,
        "source": "script.round1811_roster_cap_hotfix",
        "related_entity_id": None,
        "metadata": {
            "round": "R18.1.1",
            "hotfix": "canonical_roster_level_formula",
            "formula": "min(50, 10 + max(level, guild_level, 1) * 2)",
            "guilds_updated": count,
            # keep top 20 diffs for traceability
            "top_diffs": changes[:20],
        },
        "created_at": _utc_iso(),
    }
    await db.audit_log.insert_one(doc)


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2

    # Safety: feature flag must stay OFF
    flag = os.environ.get("R18_REWORK_ENABLED", "false").strip().lower()
    if flag not in ("false", "0", "no", ""):
        print(f"[FAIL] R18_REWORK_ENABLED='{flag}' must be OFF", file=sys.stderr)
        return 3

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name} · round=R18.1.1 roster-cap-hotfix")

    # Scan diff
    diffs: list[dict] = []
    grandfathered_before = 0
    grandfathered_after = 0
    total = 0
    async for g in db.guilds.find(
        {},
        {"_id": 0, "id": 1, "name": 1, "level": 1, "guild_level": 1,
         "max_roster_cap": 1, "current_roster_size": 1,
         "is_grandfathered": 1},
    ):
        total += 1
        curr_cap = g.get("max_roster_cap")
        roster = int(g.get("current_roster_size") or 0)
        new_cap, eff = _new_cap(g)
        new_gf = roster > new_cap
        if g.get("is_grandfathered"):
            grandfathered_before += 1
        if new_gf:
            grandfathered_after += 1
        cap_changed = curr_cap != new_cap
        gf_changed = bool(g.get("is_grandfathered")) != new_gf
        if cap_changed or gf_changed:
            diffs.append({
                "guild_id": g["id"],
                "name": g.get("name", "?"),
                "level": g.get("level"),
                "guild_level": g.get("guild_level"),
                "effective_level": eff,
                "cap_before": curr_cap,
                "cap_after": new_cap,
                "roster": roster,
                "gf_before": bool(g.get("is_grandfathered")),
                "gf_after": new_gf,
            })

    print(f"\n[scan] total_guilds={total}  cap_or_gf_changes={len(diffs)}")
    print(f"[scan] grandfathered before={grandfathered_before}  after={grandfathered_after}")
    if diffs:
        print("\n[scan] top changes:")
        for d in sorted(diffs, key=lambda x: (x["cap_after"] - (x["cap_before"] or 0)), reverse=True)[:10]:
            print(f"  · {d['name'][:35]:35}  L={d['level']} GL={d['guild_level']} "
                  f"eff={d['effective_level']}  cap {d['cap_before']} → {d['cap_after']}  "
                  f"roster={d['roster']}  gf {d['gf_before']}→{d['gf_after']}")

    if dry_run:
        print("\n[dry-run] Re-run --apply per scrivere.")
        return 0

    # APPLY: only touched docs
    updated = 0
    for d in diffs:
        r = await db.guilds.update_one(
            {"id": d["guild_id"]},
            {"$set": {
                "max_roster_cap": d["cap_after"],
                "is_grandfathered": d["gf_after"],
                "r18_roster_cap_recomputed_at": _utc_iso(),
                "r18_effective_level": d["effective_level"],
            }},
        )
        if r.modified_count > 0:
            updated += 1
    print(f"\n[apply] guilds updated: {updated}/{len(diffs)}")

    # Idempotency-safe audit: emit ONLY if we actually updated something
    # (otherwise re-runs would spam audit_log with no-op events)
    if updated > 0:
        await _emit_audit(db, updated, diffs)
        print("[audit] R18_ROSTER_CAP_RECOMPUTED emitted to audit_log")

    # Post-verify
    n_r18_type = await db.audit_log.count_documents(
        {"event_type": "R18_ROSTER_CAP_RECOMPUTED"}
    )
    print(f"[verify] audit_log R18_ROSTER_CAP_RECOMPUTED total: {n_r18_type}")
    return 0


def _parse_args():
    p = argparse.ArgumentParser(description=__doc__ or "")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    sys.exit(asyncio.run(run(dry_run=not args.apply_)))


if __name__ == "__main__":
    main()
