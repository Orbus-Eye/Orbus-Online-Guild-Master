"""
Phase 14.3-b — flag the 16 ambiguous users with is_test_user=True.

Idempotent. Re-runs are no-ops (matched count stays at 16, modified count
drops to 0). Additive backup written to /app/memory/db_ambiguous_flag_backup.json.

NOT TOUCHED:
  - any user outside the ambiguous classification
  - allowlist email (`mr.gualmini@gmail.com`) — double-guard in $ne clause
  - guilds, adventurers, expeditions, equipped_items, inventory_items, etc.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = ROOT / "backend" / ".env"
BACKUP_PATH = ROOT / "memory" / "db_ambiguous_flag_backup.json"

ALLOWLIST_EMAIL = "mr.gualmini@gmail.com"

# Same classifier as the previous cleanup script — kept inline so this
# file is standalone and recoverable.
_DENY_CONTAINS = (
    "@orbus.test", "tester@", "+smoke", "+smoketest", "+welcometest",
    "+secrettest", "+pwd", "+e2e", "@example.com", "@example.org",
    "@test.local",
)
_DENY_STARTS = ("smoke", "smoketest", "welcometest", "secrettest", "pytest", "qa-", "dev-")
_AMBIG_DOMAINS = ("@x.test", "@test.com", "@test.org")


def classify(email: str) -> str:
    e = (email or "").strip().lower()
    if e == ALLOWLIST_EMAIL.lower():
        return "allowlist"
    if any(s in e for s in _DENY_CONTAINS):
        return "denylist"
    local = e.split("@", 1)[0]
    if any(local.startswith(s) for s in _DENY_STARTS):
        return "denylist"
    if any(d in e for d in _AMBIG_DOMAINS):
        return "ambiguous"
    return "real"


def mask(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, _, dom = email.partition("@")
    if len(local) <= 2:
        masked = local[0] + "*"
    else:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked}@{dom}"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    try:
        from bson import ObjectId
        if isinstance(obj, ObjectId):
            return str(obj)
    except Exception:
        pass
    return str(obj)


async def main():
    env = dotenv_values(str(BACKEND_ENV))
    cli = AsyncIOMotorClient(env["MONGO_URL"])
    db = cli[env["DB_NAME"]]

    users_all = await db.users.find({}).to_list(None)
    ambig_users = [u for u in users_all if classify(u.get("email", "")) == "ambiguous"]
    ambig_ids = [u["id"] for u in ambig_users]

    print(f"[scope] ambiguous_users_identified={len(ambig_ids)}  (expected 16)")
    assert ALLOWLIST_EMAIL.lower() not in {u["email"].lower() for u in ambig_users}, \
        "ALLOWLIST EMAIL leaked into ambiguous list"

    # Pre-state snapshot
    pre_flagged_count = await db.users.count_documents({"is_test_user": True})
    pre_ambig_already_flagged = sum(1 for u in ambig_users if u.get("is_test_user"))

    # Additive backup BEFORE write
    backup = {
        "backup_created_at": utcnow_iso(),
        "phase": "14.3-b",
        "operation": "flag_ambiguous_users_is_test_user_true",
        "ambiguous_user_ids": ambig_ids,
        "ambiguous_users_snapshot": ambig_users,
        "pre_state": {
            "users_total": len(users_all),
            "users_flagged_is_test_user": pre_flagged_count,
            "ambiguous_already_flagged": pre_ambig_already_flagged,
        },
    }
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_PATH.write_text(json.dumps(backup, default=_json_default, indent=2))
    size_kb = BACKUP_PATH.stat().st_size / 1024
    print(f"[backup] wrote {BACKUP_PATH} ({size_kb:.1f} KB)")

    # The write — double-guard with $ne on allowlist email.
    result = await db.users.update_many(
        {
            "id": {"$in": ambig_ids},
            "email": {"$ne": ALLOWLIST_EMAIL},
        },
        {"$set": {"is_test_user": True, "test_flagged_at": utcnow_iso()}},
    )
    print(f"[flag] matched={result.matched_count} modified={result.modified_count}")

    # Post-state verification
    post_flagged_count = await db.users.count_documents({"is_test_user": True})
    allow_doc = await db.users.find_one({"email": ALLOWLIST_EMAIL}, {"is_test_user": 1})
    assert allow_doc is not None, "ABORT: allowlist user disappeared"
    assert not allow_doc.get("is_test_user"), "ABORT: allowlist user got flagged"

    ambig_all_flagged = await db.users.count_documents(
        {"id": {"$in": ambig_ids}, "is_test_user": True}
    )

    sentiero = await db.guilds.find_one({"name": "Sentiero di Efreto"}, {"id": 1})

    summary = {
        "ambiguous_identified": len(ambig_ids),
        "matched_by_update": result.matched_count,
        "modified_by_update": result.modified_count,
        "ambiguous_with_flag_after": ambig_all_flagged,
        "users_total": await db.users.count_documents({}),
        "users_flagged_before": pre_flagged_count,
        "users_flagged_after": post_flagged_count,
        "ambiguous_already_flagged_before": pre_ambig_already_flagged,
        "allowlist_user_present": True,
        "allowlist_user_is_test_user": False,
        "sentiero_present": bool(sentiero),
        "backup_file": str(BACKUP_PATH),
        "sample_ambiguous_emails_masked": [mask(u["email"]) for u in ambig_users[:5]],
    }
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    cli.close()


if __name__ == "__main__":
    asyncio.run(main())
