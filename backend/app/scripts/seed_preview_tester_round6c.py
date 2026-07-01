"""ROUND 6C — Preview validation seed for the hardcoded tester account.

This script unblocks E2E manual validation of the Training Grounds feature on
the **preview environment only** by:

  1. Forcing Training Grounds Lv1 on the tester's guild (no gold debit — this
     is a seed, not a purchase).
  2. Promoting up to 4 adventurers (one per spec-eligible class family) from
     their current level to Lv5, so the tester can immediately exercise the
     full apply-spec flow (Lv ≥ 5 gate).
  3. (Optional) Promoting one Berserker to Lv5 to let the tester exercise the
     `training.spec_tier_locked` rejection path against a starter-tier
     Training Grounds.

Hard rules (DO NOT relax):
  • Whitelist HARDCODED to ``tester@orbus.test``. Any other email aborts
    the script with a defensive ``AssertionError`` before any DB write.
  • Idempotent — a second ``--apply`` run is a no-op:
        - skips the structure update if Training Grounds is already
          unlocked at ``level >= 1``;
        - skips an adventurer promotion if they are already at level >= 5.
  • Dry-run by default. Pass ``--apply`` to actually mutate.
  • NO hard deletes anywhere. NO modifications to chronicle, market,
    auction, leaderboard, or any other guild's data.
  • Emits the audit events ``guild_structure_seeded`` and
    ``adventurer_seeded`` with ``reason="round6c_validation_seed"``.
  • Writes a JSON audit/backup file at
    ``/app/memory/round6c_preview_seed_<UTC_TIMESTAMP>.json`` on apply.

Run from the backend container:

    python -m app.scripts.seed_preview_tester_round6c           # dry-run
    python -m app.scripts.seed_preview_tester_round6c --apply   # mutate
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Defensive whitelist ────────────────────────────────────────────────
# Hardcoded — the script refuses to operate on any other account. This is a
# defense-in-depth check on top of the dry-run default.
TESTER_EMAIL = "tester@orbus.test"
SEED_REASON = "round6c_validation_seed"
SCRIPT_SOURCE = "scripts.seed_preview_tester_round6c"
MEMORY_DIR = Path("/app/memory")

# ─── Target promotion plan ──────────────────────────────────────────────
# Ordered list of class-family priorities. We promote ONE adventurer per row,
# picking the first non-retired one whose `class_name` matches any slug in
# the row's class list. Each row maps to one tier-starter specialization to
# document *why* this class is in the list (not used at runtime).
PROMOTION_PLAN: tuple[dict, ...] = (
    {"label": "tank",     "classes": ("Paladin", "Warrior"),  "spec_hint": "spec_difensore"},
    {"label": "rogue",    "classes": ("Rogue", "Ranger"),     "spec_hint": "spec_furtivo"},
    {"label": "healer",   "classes": ("Priest", "Druid"),     "spec_hint": "spec_guaritore"},
    {"label": "support",  "classes": ("Bard",),               "spec_hint": "spec_bardo"},
)
# Optional probe for the tier-locked rejection path. We promote a Berserker
# to Lv5 so the tester can try applying a full-tier spec against a
# starter-tier Training Grounds (expected 422 `training.spec_tier_locked`).
OPTIONAL_PROBE: dict = {
    "label": "tier_locked_probe",
    "classes": ("Berserker",),
    "spec_hint": "spec_furia",
}
TARGET_LEVEL = 5
TARGET_STRUCTURE = "training_grounds"
TARGET_STRUCTURE_LEVEL = 1


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _resolve_tester(db) -> tuple[dict, dict]:
    """Return (user, guild) for the hardcoded tester, or raise."""
    user = await db.users.find_one(
        {"email": TESTER_EMAIL},
        {"_id": 0, "id": 1, "email": 1, "username": 1},
    )
    assert user is not None, (
        f"Whitelisted tester {TESTER_EMAIL!r} not found — aborting before any mutation."
    )
    assert user["email"] == TESTER_EMAIL, (
        f"Defensive guard: resolved email {user['email']!r} != whitelist {TESTER_EMAIL!r}."
    )
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]},
        {"_id": 0, "id": 1, "name": 1, "owner_user_id": 1},
    )
    assert guild is not None, f"Tester {TESTER_EMAIL!r} has no guild — aborting."
    return user, guild


async def _plan_structure(db, guild_id: str) -> dict:
    """Decide whether the training_grounds structure needs an update."""
    doc = await db.guild_structures.find_one(
        {"guild_id": guild_id},
        {"_id": 0, f"structures.{TARGET_STRUCTURE}": 1},
    )
    current = (
        ((doc or {}).get("structures") or {}).get(TARGET_STRUCTURE)
        or {"level": 0, "is_unlocked": False, "acquired_via": "default"}
    )
    needs_update = not (current.get("is_unlocked") and (current.get("level") or 0) >= TARGET_STRUCTURE_LEVEL)
    return {
        "structure_slug": TARGET_STRUCTURE,
        "current": current,
        "target_level": TARGET_STRUCTURE_LEVEL,
        "needs_update": needs_update,
    }


async def _plan_promotions(db, guild_id: str) -> list[dict]:
    """For each plan row, decide the right action with strict idempotency.

    Order of checks per row:
      1. **Idempotency short-circuit** — if ANY non-retired adventurer in
         the row's class family is already at ``level >= TARGET_LEVEL``,
         the row is marked ``already_satisfied`` and skipped, even if
         other family members are still at Lv1. This guarantees the
         second ``--apply`` run is a true no-op.
      2. Otherwise pick the highest-level non-retired candidate below the
         target and promote them.
      3. If no candidate exists at all, mark ``skipped_no_candidate``.
    """
    out: list[dict] = []
    # Track ids already picked in this same run so two rows don't promote
    # the same adventurer (e.g. if two plan rows shared a class slug).
    picked_ids: set[str] = set()
    for row in (*PROMOTION_PLAN, OPTIONAL_PROBE):
        # 1) IDEMPOTENCY GUARD — if the family already has a satisfied
        # member, do NOT promote a second one on subsequent runs.
        satisfied = await db.adventurers.find_one(
            {
                "guild_id": guild_id,
                "is_retired": {"$ne": True},
                "class_name": {"$in": list(row["classes"])},
                "level": {"$gte": TARGET_LEVEL},
            },
            {"_id": 0, "id": 1, "name": 1, "class_name": 1, "level": 1},
        )
        if satisfied:
            out.append({
                "plan_label": row["label"],
                "classes": list(row["classes"]),
                "spec_hint": row["spec_hint"],
                "optional": row is OPTIONAL_PROBE,
                "action": "already_satisfied",
                "adventurer": satisfied,
            })
            continue

        # 2) Pick a candidate below the target level.
        match = await db.adventurers.find_one(
            {
                "guild_id": guild_id,
                "is_retired": {"$ne": True},
                "class_name": {"$in": list(row["classes"])},
                "id": {"$nin": list(picked_ids)},
                "level": {"$lt": TARGET_LEVEL},
            },
            {"_id": 0, "id": 1, "name": 1, "class_name": 1, "level": 1},
            sort=[("level", -1), ("created_at", 1)],
        )
        if match is None:
            # 3) No-candidate fallthrough (family extinct or all retired).
            out.append({
                "plan_label": row["label"],
                "classes": list(row["classes"]),
                "spec_hint": row["spec_hint"],
                "optional": row is OPTIONAL_PROBE,
                "action": "skipped_no_candidate",
                "adventurer": None,
            })
            continue
        picked_ids.add(match["id"])
        out.append({
            "plan_label": row["label"],
            "classes": list(row["classes"]),
            "spec_hint": row["spec_hint"],
            "optional": row is OPTIONAL_PROBE,
            "action": "promote",
            "adventurer": match,
            "from_level": match.get("level", 1),
            "to_level": TARGET_LEVEL,
        })
    return out


async def _apply_structure(db, *, user_id: str, guild_id: str, plan: dict) -> None:
    now_iso = _utc_iso()
    await db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            f"structures.{TARGET_STRUCTURE}.is_unlocked": True,
            f"structures.{TARGET_STRUCTURE}.level": TARGET_STRUCTURE_LEVEL,
            f"structures.{TARGET_STRUCTURE}.acquired_via": "seed_round6c_validation",
            f"structures.{TARGET_STRUCTURE}.purchased_at": now_iso,
            f"structures.{TARGET_STRUCTURE}.upgraded_at": now_iso,
        }},
    )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="guild_structure_seeded",
            actor_user_id=user_id,
            actor_guild_id=guild_id,
            source=SCRIPT_SOURCE,
            related_entity_id=guild_id,
            metadata={
                "reason": SEED_REASON,
                "structure_slug": TARGET_STRUCTURE,
                "from": plan["current"],
                "to": {"is_unlocked": True, "level": TARGET_STRUCTURE_LEVEL},
            },
        )
    except Exception:  # noqa: BLE001
        pass


async def _apply_promotion(db, *, user_id: str, guild_id: str, entry: dict) -> None:
    adv = entry["adventurer"]
    now_iso = _utc_iso()
    await db.adventurers.update_one(
        {"id": adv["id"]},
        {"$set": {
            "level": TARGET_LEVEL,
            "experience": 0,
            "updated_at": now_iso,
        }},
    )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="adventurer_seeded",
            actor_user_id=user_id,
            actor_guild_id=guild_id,
            source=SCRIPT_SOURCE,
            related_entity_id=adv["id"],
            metadata={
                "reason": SEED_REASON,
                "plan_label": entry["plan_label"],
                "class_name": adv.get("class_name"),
                "from_level": entry["from_level"],
                "to_level": entry["to_level"],
                "optional": entry.get("optional", False),
            },
        )
    except Exception:  # noqa: BLE001
        pass


async def _write_backup_file(payload: dict) -> str:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = MEMORY_DIR / f"round6c_preview_seed_{ts}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return str(path)


async def _seed(*, apply: bool) -> dict:
    # Lazy import to keep `--help` fast and avoid side-effects.
    from app.core.database import db

    user, guild = await _resolve_tester(db)
    structure_plan = await _plan_structure(db, guild["id"])
    promotions = await _plan_promotions(db, guild["id"])

    report = {
        "mode": "apply" if apply else "dry",
        "ran_at": _utc_iso(),
        "tester": {"email": TESTER_EMAIL, "user_id": user["id"]},
        "guild": {"id": guild["id"], "name": guild["name"]},
        "structure": structure_plan,
        "promotions": promotions,
        "applied": {"structure": False, "adventurers": []},
    }

    if not apply:
        return report

    if structure_plan["needs_update"]:
        await _apply_structure(db, user_id=user["id"], guild_id=guild["id"], plan=structure_plan)
        report["applied"]["structure"] = True

    for entry in promotions:
        if entry["action"] == "promote":
            await _apply_promotion(db, user_id=user["id"], guild_id=guild["id"], entry=entry)
            report["applied"]["adventurers"].append({
                "id": entry["adventurer"]["id"],
                "name": entry["adventurer"]["name"],
                "class_name": entry["adventurer"]["class_name"],
                "from_level": entry["from_level"],
                "to_level": entry["to_level"],
                "plan_label": entry["plan_label"],
                "optional": entry.get("optional", False),
            })

    report["backup_file"] = await _write_backup_file(report)
    return report


async def _amain() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually mutate the DB. Default = dry-run.",
    )
    args = parser.parse_args()

    result = await _seed(apply=args.apply)
    print("ROUND 6C — Preview tester seed report:")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_amain()))
