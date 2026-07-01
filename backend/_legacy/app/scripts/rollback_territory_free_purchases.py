"""ROUND 6B.3 — Rollback script for territory structures bought/upgraded
via the (now-fixed) atomicity bug.

Scope (confirmed by user, "Opzione A"):
  - Rollback ONLY structures where:
      - level > 0
      - acquired_via ∈ {"default", "purchase", None}  (NOT migration*)
      - expected_cost.gold > 0
      - 0 audit rows OR sum(|gold_delta|) == 0
  - migration / migration_legacy structures are intentional Round 6B.1
    pre-fills and MUST NOT be touched.

Behaviour:
  --dry-run  (default) : print plan + write backup JSON, no DB writes
  --apply              : write backup, perform reset, idempotent on re-run

Safety:
  - Hard SAFE_ACQUIRED_VIA assert in `_classify_for_rollback` aborts the
    whole run if a "migration" structure accidentally enters the candidate set.
  - No hard deletes (users / guilds / adventurers / items / listings / raids
    / expeditions / reports remain untouched).
  - Dormitory cap downgrades: roster is NEVER deleted. A flag
    `roster_over_capacity = true` is set on the guild instead.
  - Audit event `guild_structure_rollback_free_purchase` is written for
    every reset (one per (guild, slug) pair).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.territory.costs import UPGRADE_COSTS

logger = logging.getLogger("orbus.rollback_territory_free")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# Hard safety: any acquired_via not in this set raises BEFORE any write.
SAFE_ACQUIRED_VIA = {"default", "purchase", None}
EXCLUDED_ACQUIRED_VIA = {"migration", "migration_legacy"}

ROLLBACK_AUDIT_EVENT = "guild_structure_rollback_free_purchase"
BACKUP_DIR = Path("/app/memory")


def _expected_cost_gold(slug: str, target_level: int) -> int:
    """Sum gold cost from L=1..target_level for `slug` (skips legacy-only Nones)."""
    table = UPGRADE_COSTS.get(slug) or []
    total = 0
    for L in range(1, target_level + 1):
        row = table[L] if L < len(table) else None
        if row is None:
            continue
        total += int(row.get("gold") or 0)
    return total


async def _paid_gold(db, guild_id: str, slug: str) -> int:
    """Sum |gold_delta| across audit rows for (guild, slug) so we can
    classify whether the structure was paid or not."""
    rows = await db.audit_log.find(
        {
            "actor_guild_id": guild_id,
            "event_type": {"$in": ["guild_structure_purchased",
                                    "guild_structure_upgraded"]},
            "metadata.structure_slug": slug,
        },
        {"_id": 0, "gold_delta": 1},
    ).to_list(200)
    return sum(abs(int(r.get("gold_delta") or 0)) for r in rows)


def _classify_for_rollback(
    *, slug: str, current_level: int, acquired_via: Optional[str],
    expected_gold: int, paid_gold: int,
) -> Optional[dict]:
    """Return rollback action `{action, new_level, reason}` or None if no
    rollback applies. RAISES if a migration row leaks into the scope."""
    if current_level <= 0:
        return None
    if expected_gold <= 0:
        return None  # starter cost=0 — not in scope
    # SAFETY ASSERT — should never fire because the caller filters,
    # but defence-in-depth ensures we abort on logic bugs.
    assert acquired_via in SAFE_ACQUIRED_VIA, (
        f"REFUSING to rollback non-safe acquired_via='{acquired_via}' "
        f"for slug='{slug}'. This usually means a migration structure "
        f"leaked into the candidate set — investigate."
    )
    if paid_gold == 0:
        return {"action": "reset_to_zero", "new_level": 0,
                "reason": "free_purchase",
                "expected_cost_gold": expected_gold,
                "paid_cost_gold": 0}
    if paid_gold < expected_gold:
        # Find the highest level whose cumulative cost ≤ paid_gold.
        cum = 0
        new_lv = 0
        for L in range(1, current_level + 1):
            row = (UPGRADE_COSTS.get(slug) or [])[L] if L < len(UPGRADE_COSTS.get(slug) or []) else None
            if row is None:
                continue
            cum += int(row.get("gold") or 0)
            if cum <= paid_gold:
                new_lv = L
            else:
                break
        return {"action": "reset_to_paid_level", "new_level": new_lv,
                "reason": "partial_free_purchase",
                "expected_cost_gold": expected_gold,
                "paid_cost_gold": paid_gold}
    return None  # paid >= expected → keep as is


async def _build_plan(db) -> dict:
    """Scan all guild_structures docs and build a list of rollback actions."""
    plan_actions: list[dict] = []
    skipped_migration = 0
    skipped_paid = 0
    skipped_other_acquired_via: Counter = Counter()
    affected_guilds: set[str] = set()

    async for gs in db.guild_structures.find({}, {"_id": 0}):
        guild_id = gs["guild_id"]
        for slug, st in (gs.get("structures") or {}).items():
            lvl = int(st.get("level") or 0)
            if lvl <= 0:
                continue
            acq = st.get("acquired_via")
            if acq in EXCLUDED_ACQUIRED_VIA:
                skipped_migration += 1
                continue
            # SCOPE LOCK — Option A: rollback ONLY structures whose
            # acquired_via ∈ SAFE_ACQUIRED_VIA. Any other value (e.g.
            # `test_setup`, `rolled_back`, future tags) is intentionally
            # out of scope: not migration, not user purchase. Skip with
            # a counter so the report shows them.
            if acq not in SAFE_ACQUIRED_VIA:
                skipped_other_acquired_via[str(acq)] += 1
                continue
            expected = _expected_cost_gold(slug, lvl)
            if expected <= 0:
                continue  # starter
            paid = await _paid_gold(db, guild_id, slug)
            action = _classify_for_rollback(
                slug=slug, current_level=lvl,
                acquired_via=acq, expected_gold=expected, paid_gold=paid,
            )
            if action is None:
                skipped_paid += 1
                continue
            plan_actions.append({
                "guild_id": guild_id,
                "structure_slug": slug,
                "old_level": lvl,
                **action,
                "acquired_via": acq,
            })
            affected_guilds.add(guild_id)
    return {
        "actions": plan_actions,
        "skipped_migration": skipped_migration,
        "skipped_paid": skipped_paid,
        "skipped_other_acquired_via": dict(skipped_other_acquired_via),
        "affected_guild_ids": affected_guilds,
    }


async def _write_backup(db, *, plan: dict, ts: str) -> Path:
    """Snapshot guild_structures + audit_log for every affected guild before
    we touch a single row. Path is printed so the operator can verify the
    file exists before granting --apply."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    out = BACKUP_DIR / f"territory_free_purchase_rollback_backup_{ts}.json"
    snapshot = []
    for guild_id in plan["affected_guild_ids"]:
        gs = await db.guild_structures.find_one({"guild_id": guild_id}, {"_id": 0})
        guild = await db.guilds.find_one({"id": guild_id},
                                         {"_id": 0, "id": 1, "name": 1, "gold": 1})
        events = await db.audit_log.find(
            {"actor_guild_id": guild_id,
             "event_type": {"$in": ["guild_structure_purchased",
                                     "guild_structure_upgraded"]}},
            {"_id": 0},
        ).to_list(200)
        snapshot.append({
            "guild_id": guild_id,
            "guild_public_name": (guild or {}).get("name"),
            "gold_snapshot": (guild or {}).get("gold"),
            "structures_snapshot": (gs or {}).get("structures"),
            "audit_events_snapshot": events,
        })
    out.write_text(json.dumps({
        "generated_at_utc": ts,
        "guilds_count": len(snapshot),
        "guilds": snapshot,
    }, indent=2, default=str))
    return out


async def _apply_one(db, action: dict, *, ts: str) -> bool:
    """Apply one rollback action. Idempotent: returns True if a write
    happened, False if the structure was already at the target level."""
    guild_id = action["guild_id"]
    slug = action["structure_slug"]
    new_lv = int(action["new_level"])

    # Idempotency check: read current level. If already at new_lv, skip.
    gs = await db.guild_structures.find_one({"guild_id": guild_id},
                                             {"_id": 0, "structures": 1})
    cur = ((gs or {}).get("structures") or {}).get(slug, {})
    cur_lv = int(cur.get("level") or 0)
    if cur_lv == new_lv:
        return False

    update_path = f"structures.{slug}"
    if new_lv == 0:
        new_struct = {
            "level": 0,
            "is_unlocked": False,
            "purchased_at": None,
            "upgraded_at": None,
            "acquired_via": "rolled_back",
        }
    else:
        new_struct = {
            "level": new_lv,
            "is_unlocked": True,
            "purchased_at": cur.get("purchased_at"),
            "upgraded_at": ts,
            "acquired_via": "rolled_back",
        }
    await db.guild_structures.update_one(
        {"guild_id": guild_id, f"{update_path}.level": cur_lv},
        {"$set": {update_path: new_struct, "updated_at": ts}},
    )

    # Dormitory special case: roster may now be over cap.
    if slug == "dormitories":
        try:
            from app.territory.structures import dormitory_cap_for_level
            new_cap = dormitory_cap_for_level(new_lv)
            roster = await db.adventurers.count_documents(
                {"guild_id": guild_id, "is_retired": {"$ne": True}},
            )
            if roster > new_cap:
                await db.guilds.update_one(
                    {"id": guild_id},
                    {"$set": {"roster_over_capacity": True,
                              "roster_over_capacity_set_at": ts}},
                )
        except Exception as exc:
            logger.warning("dormitory over-cap flag failed for guild=%s: %s",
                           guild_id, exc)

    # Audit event — write a single row per rollback.
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": ROLLBACK_AUDIT_EVENT,
            "actor_user_id": None,
            "actor_guild_id": guild_id,
            "item_slug": None,
            "item_template_id": None,
            "quantity": None,
            "gold_delta": None,
            "source": "scripts.rollback_territory_free_purchases",
            "related_entity_id": None,
            "metadata": {
                "structure_slug": slug,
                "old_level": cur_lv,
                "new_level": new_lv,
                "reason": action["reason"],
                "expected_cost": action["expected_cost_gold"],
                "paid_cost": action["paid_cost_gold"],
                "rollback_timestamp": ts,
            },
            "created_at": ts,
        })
    except Exception as exc:
        logger.warning("audit insert failed for rollback (%s, %s): %s",
                       guild_id, slug, exc)
    return True


async def _entity_counts(db) -> dict:
    """Snapshot count of every collection we promise NOT to hard-delete."""
    cols = ["users", "guilds", "adventurers", "items",
            "inventory_items", "market_listings", "auction_listings",
            "raids", "expeditions", "expedition_reports", "guild_structures"]
    out = {}
    for c in cols:
        try:
            out[c] = await db[c].count_documents({})
        except Exception:
            out[c] = -1
    return out


async def run(*, apply: bool) -> dict:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    iso_ts = datetime.now(timezone.utc).isoformat()

    counts_before = await _entity_counts(db)
    plan = await _build_plan(db)
    backup_path = await _write_backup(db, plan=plan, ts=ts)

    by_slug = Counter((a["structure_slug"], a["old_level"], a["new_level"])
                      for a in plan["actions"])
    by_slug_serialised = {f"{slug}|{old}|{new}": cnt
                           for (slug, old, new), cnt in by_slug.items()}
    by_reason = Counter(a["reason"] for a in plan["actions"])

    if not apply:
        cli.close()
        return {
            "mode": "dry_run",
            "actions_count": len(plan["actions"]),
            "by_slug_old_new": by_slug_serialised,
            "by_reason": dict(by_reason),
            "skipped_migration": plan["skipped_migration"],
            "skipped_paid": plan["skipped_paid"],
            "skipped_other_acquired_via": plan["skipped_other_acquired_via"],
            "affected_guilds": len(plan["affected_guild_ids"]),
            "backup_file": str(backup_path),
            "entity_counts_before": counts_before,
        }

    # APPLY path
    applied = 0
    noop_idempotent = 0
    for action in plan["actions"]:
        did_write = await _apply_one(db, action, ts=iso_ts)
        if did_write:
            applied += 1
        else:
            noop_idempotent += 1

    counts_after = await _entity_counts(db)
    cli.close()
    return {
        "mode": "apply",
        "actions_count": len(plan["actions"]),
        "applied": applied,
        "noop_idempotent": noop_idempotent,
        "by_slug_old_new": by_slug_serialised,
        "by_reason": dict(by_reason),
        "skipped_migration": plan["skipped_migration"],
        "skipped_paid": plan["skipped_paid"],
        "skipped_other_acquired_via": plan["skipped_other_acquired_via"],
        "affected_guilds": len(plan["affected_guild_ids"]),
        "backup_file": str(backup_path),
        "entity_counts_before": counts_before,
        "entity_counts_after": counts_after,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true",
                   help="Actually perform writes. Default is dry-run.")
    args = p.parse_args()
    result = asyncio.run(run(apply=args.apply))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
