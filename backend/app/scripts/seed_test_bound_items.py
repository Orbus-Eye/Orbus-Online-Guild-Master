"""ROUND 6B.4 Task 2 — Dev-only seed for adventurer-bound inventory items.

Binds a single existing inventory row of every `@orbus.test` user to their
first non-retired adventurer, with `bound_reason="dev_seed_round_6b4"`. This
lets us exercise the four bound guards (equip, market, auction, retire) on
the preview environment without waiting for Round 6C/6D sources.

Hard rules (do NOT relax):
  • Only touches users whose email ends with `@orbus.test`
  • Idempotent: skips users whose first inventory row is already bound
  • NEVER hard-deletes anything
  • Dry-run by default; pass `--apply` to actually mutate
  • Emits an audit event `bound_to_adventurer_dev_seed` for traceability

Run from the backend container:
    python -m app.scripts.seed_test_bound_items          # dry-run
    python -m app.scripts.seed_test_bound_items --apply  # mutate
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone


TEST_EMAIL_SUFFIX = "@orbus.test"
BOUND_REASON = "dev_seed_round_6b4"


async def _seed(*, apply: bool) -> dict:
    # Lazy import to keep `--help` fast and avoid side-effects.
    from app.core.database import db

    users = await db.users.find(
        {"email": {"$regex": f"{TEST_EMAIL_SUFFIX}$", "$options": "i"}},
        {"_id": 0, "id": 1, "email": 1},
    ).to_list(500)

    if not users:
        return {"users_scanned": 0, "bound_now": 0, "already_bound": 0,
                "skipped_no_adv": 0, "skipped_no_inv": 0, "mode": "dry" if not apply else "apply"}

    bound_now = 0
    already_bound = 0
    skipped_no_adv = 0
    skipped_no_inv = 0

    for u in users:
        # 1) Find the user's guild
        guild = await db.guilds.find_one(
            {"owner_user_id": u["id"]}, {"_id": 0, "id": 1, "name": 1},
        )
        if not guild:
            skipped_no_adv += 1
            continue

        # 2) First non-retired adventurer
        adv = await db.adventurers.find_one(
            {"guild_id": guild["id"], "is_retired": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1},
        )
        if not adv:
            skipped_no_adv += 1
            continue

        # 3) Idempotency gate — skip the user if ANY inventory row is already
        # bound to this adventurer. We only bind ONE row per user, never more.
        existing_bound = await db.inventory_items.find_one(
            {
                "guild_id": guild["id"],
                "bound_to_adventurer_id": {"$ne": None},
            },
            {"_id": 0, "id": 1},
        )
        if existing_bound:
            already_bound += 1
            continue

        # 4) Find a row that isn't yet adventurer-bound
        candidate = await db.inventory_items.find_one(
            {
                "guild_id": guild["id"],
                "$or": [
                    {"bound_to_adventurer_id": None},
                    {"bound_to_adventurer_id": {"$exists": False}},
                ],
            },
            {"_id": 0, "id": 1, "item_id": 1},
        )
        if not candidate:
            skipped_no_inv += 1
            continue

        if apply:
            now_iso = datetime.now(timezone.utc).isoformat()
            await db.inventory_items.update_one(
                {"id": candidate["id"]},
                {"$set": {
                    "bound_to_adventurer_id": adv["id"],
                    "bound_reason": BOUND_REASON,
                    "bound_at": now_iso,
                }},
            )
            # Best-effort audit (event type not in enum on purpose — dev tool).
            try:
                from app.audit.log import write_audit
                await write_audit(
                    db,
                    event_type="bound_to_adventurer_dev_seed",
                    actor_user_id=u["id"],
                    actor_guild_id=guild["id"],
                    source="scripts.seed_test_bound_items",
                    related_entity_id=adv["id"],
                    metadata={
                        "inventory_id": candidate["id"],
                        "item_id": candidate.get("item_id"),
                        "adventurer_name": adv.get("name"),
                        "user_email": u.get("email"),
                    },
                )
            except Exception:
                # Audit dropped silently — write_audit already logs internally.
                pass
        bound_now += 1

    return {
        "users_scanned": len(users),
        "bound_now": bound_now,
        "already_bound": already_bound,
        "skipped_no_adv": skipped_no_adv,
        "skipped_no_inv": skipped_no_inv,
        "mode": "apply" if apply else "dry",
    }


async def _amain() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Actually mutate the DB. Default = dry-run.")
    args = parser.parse_args()

    result = await _seed(apply=args.apply)
    print("ROUND 6B.4 — Dev bound-item seed result:")
    for k, v in result.items():
        print(f"  {k:>22}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_amain()))
