"""ROUND 6E — Preview validation seed for the hardcoded tester account.

Extends the Round 6C bootstrap by preparing the tester guild for the
**Respec happy path** end-to-end:

  1. Bump ``training_grounds`` from any prior level to **Lv3** (Full Hybrid
     tier unlocked → all 14 specs become reachable in the catalog response).
  2. Provision **one** non-specialized Warrior at Lv >= 5 ready for an
     immediate Apply Spec flow followed by a Respec to a Full Hybrid (e.g.
     Furia or Maestro di Armi). If no eligible Warrior exists, the script
     promotes the highest-level unspecialized Warrior to Lv5.

Hard rules (DO NOT relax):
  • Whitelist HARDCODED to ``tester@orbus.test``. Defensive assertion
    aborts the run before any mutation if a different email is resolved.
  • Idempotent — a second ``--apply`` run is a no-op:
      - skips the structure update if Training Grounds is already at
        ``level >= 3`` and ``is_unlocked``;
      - skips the adventurer slot if any non-retired, non-specialized
        Warrior at Lv >= 5 already exists on the tester's guild.
  • Dry-run by default. Pass ``--apply`` to mutate.
  • NO hard deletes. NO modifications to chronicle, market, audit history,
    or any other guild's data.
  • Emits the audit events ``guild_structure_seeded`` (existing 6C type)
    and ``adventurer_seeded`` (existing 6C type) with
    ``reason="round6e_validation_seed"`` to keep the allowlist surface
    unchanged.
  • Writes a JSON backup at
    ``/app/memory/round6e_preview_seed_<UTC_TIMESTAMP>.json`` on apply.

Run from the backend container:

    python -m app.scripts.seed_preview_tester_round6e           # dry-run
    python -m app.scripts.seed_preview_tester_round6e --apply   # mutate
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Defensive whitelist ────────────────────────────────────────────────
TESTER_EMAIL = "tester@orbus.test"
SEED_REASON = "round6e_validation_seed"
SCRIPT_SOURCE = "scripts.seed_preview_tester_round6e"
MEMORY_DIR = Path("/app/memory")

# ─── Target state ───────────────────────────────────────────────────────
TARGET_STRUCTURE = "training_grounds"
TARGET_STRUCTURE_LEVEL = 3  # ROUND 6E — Full Hybrid tier unlocked
TARGET_ADV_LEVEL = 5        # ≥ MIN_ADVENTURER_LEVEL gate
WARRIOR_CLASSES = ("Warrior", "Paladin")  # spec-eligible for hybrids


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _resolve_tester(db) -> tuple[dict, dict]:
    user = await db.users.find_one(
        {"email": TESTER_EMAIL},
        {"_id": 0, "id": 1, "email": 1, "username": 1},
    )
    assert user is not None, (
        f"Whitelisted tester {TESTER_EMAIL!r} not found — aborting before any mutation."
    )
    assert user["email"] == TESTER_EMAIL, (
        f"Defensive guard: resolved email {user['email']!r} != "
        f"whitelist {TESTER_EMAIL!r}."
    )
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]},
        {"_id": 0, "id": 1, "name": 1, "owner_user_id": 1},
    )
    assert guild is not None, f"Tester {TESTER_EMAIL!r} has no guild — aborting."
    return user, guild


async def _plan_structure(db, guild_id: str) -> dict:
    """Bump training_grounds to Lv3 (Full Hybrid tier) if not already there."""
    doc = await db.guild_structures.find_one(
        {"guild_id": guild_id},
        {"_id": 0, f"structures.{TARGET_STRUCTURE}": 1},
    )
    current = (
        ((doc or {}).get("structures") or {}).get(TARGET_STRUCTURE)
        or {"level": 0, "is_unlocked": False, "acquired_via": "default"}
    )
    needs_update = not (
        current.get("is_unlocked")
        and (current.get("level") or 0) >= TARGET_STRUCTURE_LEVEL
    )
    return {
        "structure_slug": TARGET_STRUCTURE,
        "current": current,
        "target_level": TARGET_STRUCTURE_LEVEL,
        "needs_update": needs_update,
    }


async def _plan_warrior_slot(db, guild_id: str) -> dict:
    """Locate or promote a Warrior-family Lv≥5 unspecialized adventurer.

    Idempotency: if any non-retired Warrior on the guild is already
    Lv≥5 AND has no ``specialization.slug`` set, the slot is considered
    already-satisfied and no mutation is planned.
    """
    # 1) Idempotency short-circuit — slot already prepared?
    satisfied = await db.adventurers.find_one(
        {
            "guild_id": guild_id,
            "is_retired": {"$ne": True},
            "class_name": {"$in": list(WARRIOR_CLASSES)},
            "level": {"$gte": TARGET_ADV_LEVEL},
            "$or": [
                {"specialization": {"$exists": False}},
                {"specialization": None},
                {"specialization.slug": {"$in": [None, ""]}},
                {"specialization.slug": {"$exists": False}},
            ],
        },
        {"_id": 0, "id": 1, "name": 1, "class_name": 1, "level": 1,
         "specialization": 1},
    )
    if satisfied:
        return {
            "action": "already_satisfied",
            "adventurer": satisfied,
            "classes": list(WARRIOR_CLASSES),
        }

    # 2) Pick the highest-level unspecialized Warrior below the target.
    match = await db.adventurers.find_one(
        {
            "guild_id": guild_id,
            "is_retired": {"$ne": True},
            "class_name": {"$in": list(WARRIOR_CLASSES)},
            "level": {"$lt": TARGET_ADV_LEVEL},
            "$or": [
                {"specialization": {"$exists": False}},
                {"specialization": None},
                {"specialization.slug": {"$in": [None, ""]}},
                {"specialization.slug": {"$exists": False}},
            ],
        },
        {"_id": 0, "id": 1, "name": 1, "class_name": 1, "level": 1},
        sort=[("level", -1), ("created_at", 1)],
    )
    if match is None:
        return {
            "action": "skipped_no_candidate",
            "adventurer": None,
            "classes": list(WARRIOR_CLASSES),
        }
    return {
        "action": "promote",
        "adventurer": match,
        "classes": list(WARRIOR_CLASSES),
        "from_level": match.get("level", 1),
        "to_level": TARGET_ADV_LEVEL,
    }


async def _apply_structure(db, *, user_id: str, guild_id: str, plan: dict) -> None:
    now_iso = _utc_iso()
    await db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            f"structures.{TARGET_STRUCTURE}.is_unlocked": True,
            f"structures.{TARGET_STRUCTURE}.level": TARGET_STRUCTURE_LEVEL,
            f"structures.{TARGET_STRUCTURE}.acquired_via": "seed_round6e_validation",
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


async def _apply_warrior_promotion(db, *, user_id: str, guild_id: str,
                                   entry: dict) -> None:
    adv = entry["adventurer"]
    now_iso = _utc_iso()
    await db.adventurers.update_one(
        {"id": adv["id"]},
        {"$set": {
            "level": TARGET_ADV_LEVEL,
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
                "plan_label": "warrior_respec_target",
                "class_name": adv.get("class_name"),
                "from_level": entry["from_level"],
                "to_level": entry["to_level"],
            },
        )
    except Exception:  # noqa: BLE001
        pass


async def _write_backup_file(payload: dict) -> str:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = MEMORY_DIR / f"round6e_preview_seed_{ts}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return str(path)


async def _seed(*, apply: bool) -> dict:
    from app.core.database import db

    user, guild = await _resolve_tester(db)
    structure_plan = await _plan_structure(db, guild["id"])
    warrior_slot = await _plan_warrior_slot(db, guild["id"])

    report = {
        "mode": "apply" if apply else "dry",
        "ran_at": _utc_iso(),
        "tester": {"email": TESTER_EMAIL, "user_id": user["id"]},
        "guild": {"id": guild["id"], "name": guild["name"]},
        "structure": structure_plan,
        "warrior_slot": warrior_slot,
        "applied": {"structure": False, "warrior_slot": None},
    }

    if not apply:
        return report

    if structure_plan["needs_update"]:
        await _apply_structure(
            db, user_id=user["id"], guild_id=guild["id"], plan=structure_plan,
        )
        report["applied"]["structure"] = True

    if warrior_slot["action"] == "promote":
        await _apply_warrior_promotion(
            db, user_id=user["id"], guild_id=guild["id"], entry=warrior_slot,
        )
        report["applied"]["warrior_slot"] = {
            "id": warrior_slot["adventurer"]["id"],
            "name": warrior_slot["adventurer"]["name"],
            "class_name": warrior_slot["adventurer"]["class_name"],
            "from_level": warrior_slot["from_level"],
            "to_level": warrior_slot["to_level"],
        }

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
    print("ROUND 6E — Preview tester seed report:")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_amain()))
