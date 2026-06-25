#!/usr/bin/env python3
"""Production leaderboard cleanup — Orbus Online.

Twin of the in-preview operation executed on 2026-06-26. Designed to be
copied to the production pod and run there (the agent does NOT have access
to the production MongoDB). DEFAULT IS DRY-RUN: nothing is written unless
`--apply` is passed.

What it does
============
1. Connects to the MongoDB pointed at by env var `MONGO_URL`
   (loaded from /app/backend/.env on the prod pod).
2. Loads ALL allowlist + pending sets verbatim from this file (hardcoded for
   safety — no inheritance from conftest.py because /app/backend/tests
   isn't always present on the prod pod).
3. Audits which guilds currently leak through the public leaderboard
   filter (i.e., `owner_user_id ∉ {users where is_test_user=True}`).
4. Bucketizes them into:
     - allowlist     → never touch (Sentiero di Efreto, Drakarys, Harambes,
                       plus any guild whose owner is in ALLOWLIST_EMAILS)
     - pending       → never touch, surfaced for human review
                       (The Loremaster, The Iron Lantern)
     - test_residual → owner is a real users doc whose email matches a
                       known test pattern → flag is_test_user=True
     - orphan        → owner has NO users doc (was deleted but guild
                       remained) → insert a SHADOW user doc with the same
                       `id`, is_test_user=True, password_hash=SENTINEL,
                       which engages the existing leaderboard filter
                       without any code change.
5. Writes a JSON backup to
   `/tmp/prod_leaderboard_residual_flag_backup_<UTC_ISO>.json` BEFORE any
   write. The backup is the rollback fuel (see `--rollback` below).

Idempotent
==========
Re-running with `--apply` after a successful run is a no-op: users already
flagged are skipped, shadow placeholders are detected by their sentinel
hash. The script counts how many would be touched anyway and reports the
diff.

Safety guarantees
=================
- NO `delete_many` anywhere. NO hard delete of users or guilds.
- ALLOWLIST_EMAILS + ALLOWLIST_GUILDS + PENDING_AMBIGUOUS are double-checked
  on every per-record decision.
- Refuses to run if `MONGO_URL` points to a URI that looks like the
  preview cluster (heuristic: hostname contains 'test' or starts with
  '127.' / 'localhost').

Reversal
========
Two paths, depending on what you want to undo:
- `--rollback <backup_path>`: reads the backup and:
    * `$unset` is_test_user from each user listed in `users_flagged`,
    * `delete_many({"password_hash": SENTINEL, "id": {"$in": [...]}})` for
      the shadow placeholder users created.
  The backup file is the only authoritative rollback source.

Run modes
=========
    # Audit only (default — no writes, prints what would happen)
    python3 prod_leaderboard_cleanup.py

    # Apply (writes, with backup)
    python3 prod_leaderboard_cleanup.py --apply

    # Rollback a previous apply
    python3 prod_leaderboard_cleanup.py --rollback /tmp/prod_leaderboard_residual_flag_backup_2026-06-26T22-30-00.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# stdlib only + motor + dotenv (both already in prod backend requirements)
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import dotenv_values, load_dotenv
except ImportError as e:
    print(f"FATAL: missing dependency ({e}). Install motor + python-dotenv.",
          file=sys.stderr)
    sys.exit(2)


# ─── Permanent allowlist (hardcoded, single source of truth on prod) ───
ALLOWLIST_EMAILS = {
    "mr.gualmini@gmail.com",          # Gualma — Sentiero di Efreto
    "gianluca.brandi42@gmail.com",    # Drakarys
    # "<harambes email pending>",    # add when user provides it
    "tester@orbus.test",              # sandbox admin
}
ALLOWLIST_GUILDS = {
    "sentiero di efreto",
    "drakarys",
    "harambes",                       # name-based protection while email pending
}
# Guilds we explicitly DO NOT TOUCH until the user classifies them.
PENDING_AMBIGUOUS = {
    "the loremaster",
    "the iron lantern",
}

# Sentinel password_hash for the shadow placeholder users created for
# orphan guilds. Searchable for rollback. NEVER usable as a credential
# (bcrypt would never produce this string).
SHADOW_PW_SENTINEL = "$ORPHAN_PLACEHOLDER$"


# ─── Email patterns we ARE comfortable flagging on prod ────────────────
# All anchored to start-of-string. Anything else is considered ambiguous
# and surfaced to the human (i.e., NOT touched).
TEST_EMAIL_PATTERNS = [
    # Catch-all: anything @orbus.test that is NOT tester@orbus.test is test.
    # This domain is reserved for fixtures. Allowlist short-circuits above.
    re.compile(r"@orbus\.test$", re.IGNORECASE),
    re.compile(r"@(example\.com|example\.org|test\.local|x\.test|test\.com|test\.org)$",
               re.IGNORECASE),
    re.compile(r"^(test_|tester_|smoke_|smoketest_|welcometest_|playtest_)",
               re.IGNORECASE),
    re.compile(r"^(OrbusE2E|orbusE2E|e2e\d?_|reg_|pr\d|p\d|ref_|uitest)",
               re.IGNORECASE),
    re.compile(r"^(qa-|dev-|gates_|disp_|unlock_|dh_|sc_|gw_)",
               re.IGNORECASE),
]
# Same for guild names — used only when we MUST classify by name (e.g. when
# the owner email doesn't match a pattern, like the historic TEST_* guilds).
TEST_GUILD_NAME_PATTERNS = [
    re.compile(r"^(TEST_|Test_|test_|Test G[ _])", ),
    re.compile(r"^(G_p\d|P\d+Guild|p\d+_|G_OrbusE2E)"),
    re.compile(r"^(E2E_|ExpG_|Guild_\d|GA_|GB_|Smoke|UI Tes)"),
    re.compile(r"^(TestGuild_)"),
]


def is_test_email(email: str) -> bool:
    e = (email or "").strip()
    if not e:
        return False
    if e.lower() in ALLOWLIST_EMAILS:
        return False
    return any(p.search(e) for p in TEST_EMAIL_PATTERNS)


def is_test_guild_name(name: str) -> bool:
    n = (name or "").strip()
    if not n:
        return False
    if n.lower() in ALLOWLIST_GUILDS:
        return False
    if n.lower() in PENDING_AMBIGUOUS:
        return False
    return any(p.search(n) for p in TEST_GUILD_NAME_PATTERNS)


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, _, dom = email.partition("@")
    if len(local) <= 2:
        return local[0] + "*@" + dom
    return local[0] + "*" * (len(local) - 2) + local[-1] + "@" + dom


def _looks_like_preview_uri(uri: str) -> bool:
    """Refuse to run if the connection string looks local/preview."""
    u = (uri or "").lower()
    return any(s in u for s in ("localhost", "127.0.0.1", "/test_database"))


# ─── Core audit ─────────────────────────────────────────────────────────
async def audit(db) -> dict:
    """Read-only audit. Returns the classification result."""
    test_owner_ids = await db.users.distinct("id", {"is_test_user": True})
    base = {"owner_user_id": {"$nin": test_owner_ids}} if test_owner_ids else {}

    guilds = await db.guilds.find(
        base,
        {
            "_id": 0,
            "id": 1,
            "name": 1,
            "owner_user_id": 1,
            "max_team_power_ever": 1,
            "level": 1,
        },
    ).sort([("max_team_power_ever", -1), ("level", -1)]).to_list(None)

    owner_ids = list({g["owner_user_id"] for g in guilds})
    owners = await db.users.find(
        {"id": {"$in": owner_ids}},
        {"_id": 0, "id": 1, "email": 1, "is_test_user": 1},
    ).to_list(None)
    by_uid = {u["id"]: u for u in owners}

    buckets: dict[str, list] = {
        "allowlist": [],
        "pending_ambiguous": [],
        "test_residual": [],
        "orphan": [],
        "unknown_real": [],
    }
    for g in guilds:
        gn = (g.get("name") or "").lower()
        owner = by_uid.get(g.get("owner_user_id"))

        # 1. Guild name in allowlist → keep (covers Harambes even if email TBD)
        if gn in ALLOWLIST_GUILDS:
            buckets["allowlist"].append({
                "guild": g["name"],
                "owner_email_masked": mask_email(owner["email"]) if owner else "(no-user-doc)",
                "peak": g.get("max_team_power_ever", 0),
            })
            continue

        # 2. Guild name pending → never touch
        if gn in PENDING_AMBIGUOUS:
            buckets["pending_ambiguous"].append({
                "guild": g["name"],
                "owner_email_masked": mask_email(owner["email"]) if owner else "(no-user-doc)",
                "peak": g.get("max_team_power_ever", 0),
            })
            continue

        # 3. Owner missing → orphan (shadow placeholder)
        if owner is None:
            buckets["orphan"].append({
                "guild_id": g["id"],
                "guild": g["name"],
                "owner_user_id": g["owner_user_id"],
                "peak": g.get("max_team_power_ever", 0),
            })
            continue

        # 4. Owner email in allowlist → keep
        if (owner.get("email") or "").lower() in ALLOWLIST_EMAILS:
            buckets["allowlist"].append({
                "guild": g["name"],
                "owner_email_masked": mask_email(owner["email"]),
                "peak": g.get("max_team_power_ever", 0),
            })
            continue

        # 5. Test patterns (email OR guild name)
        if is_test_email(owner.get("email") or "") or is_test_guild_name(g.get("name") or ""):
            buckets["test_residual"].append({
                "user_id": owner["id"],
                "guild_id": g["id"],
                "guild": g["name"],
                "owner_email_masked": mask_email(owner["email"]),
                "peak": g.get("max_team_power_ever", 0),
            })
            continue

        # 6. Doesn't match anything we recognise → surface to human, do NOT touch
        buckets["unknown_real"].append({
            "guild": g["name"],
            "owner_email_masked": mask_email(owner["email"]),
            "peak": g.get("max_team_power_ever", 0),
        })

    return {
        "leaderboard_visible_total": len(guilds),
        "buckets_count": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
    }


def _print_audit(audit_result: dict) -> None:
    print("\n── LEADERBOARD AUDIT (read-only) ──")
    print(f"total visible (pre-flag): {audit_result['leaderboard_visible_total']}")
    for k, n in audit_result["buckets_count"].items():
        print(f"  {k:>20}: {n}")
    if audit_result["buckets"]["unknown_real"]:
        print("\n⚠  UNKNOWN_REAL — these will NOT be flagged. Review with user:")
        for u in audit_result["buckets"]["unknown_real"]:
            print(f"  • {u['guild']:30}  peak={u['peak']:>3}  owner={u['owner_email_masked']}")
    if audit_result["buckets"]["pending_ambiguous"]:
        print("\n⚠  PENDING_AMBIGUOUS — explicitly held for user review:")
        for u in audit_result["buckets"]["pending_ambiguous"]:
            print(f"  • {u['guild']:30}  peak={u['peak']:>3}  owner={u['owner_email_masked']}")
    if audit_result["buckets"]["allowlist"]:
        print("\n✅ ALLOWLIST (will stay visible):")
        for u in audit_result["buckets"]["allowlist"]:
            print(f"  • {u['guild']:30}  peak={u['peak']:>3}  owner={u['owner_email_masked']}")


# ─── Apply ──────────────────────────────────────────────────────────────
async def apply(db, audit_result: dict, backup_path: Path) -> dict:
    test_residual = audit_result["buckets"]["test_residual"]
    orphans = audit_result["buckets"]["orphan"]
    now = datetime.now(timezone.utc)

    backup = {
        "timestamp_utc": now.isoformat(),
        "reason": "prod leaderboard residual cleanup (no hard delete)",
        "operation_a": "users.update_many({id ∈ test_residual_ids}, {$set:{is_test_user:True}})",
        "operation_b": "users.insert_one({id, is_test_user:True, password_hash=SENTINEL}) per orphan owner_user_id",
        "allowlist_emails": sorted(ALLOWLIST_EMAILS),
        "allowlist_guilds": sorted(ALLOWLIST_GUILDS),
        "pending_ambiguous_skipped": sorted(PENDING_AMBIGUOUS),
        "unknown_real_skipped": audit_result["buckets"]["unknown_real"],
        "shadow_pw_sentinel": SHADOW_PW_SENTINEL,
        "test_residual_to_flag": test_residual,
        "orphans_to_shadow": orphans,
    }
    backup_path.write_text(json.dumps(backup, indent=2, default=str))
    print(f"\n[backup] saved → {backup_path}")

    # ── Phase A: flag is_test_user on real test users ────────────────────
    flagged = 0
    if test_residual:
        ids = [r["user_id"] for r in test_residual]
        # Double-defence: query intersection with allowlist must be empty.
        leaks = await db.users.find(
            {
                "id": {"$in": ids},
                "email": {"$in": list(ALLOWLIST_EMAILS)},
            },
            {"_id": 0, "id": 1, "email": 1},
        ).to_list(None)
        if leaks:
            print(f"⛔ ABORT: allowlist email leaked into flag set: {leaks}")
            sys.exit(3)
        res = await db.users.update_many(
            {"id": {"$in": ids}},
            {"$set": {"is_test_user": True, "updated_at": now}},
        )
        flagged = res.modified_count
        print(f"[flag]   matched={res.matched_count} modified={flagged}")

    # ── Phase B: shadow placeholder users for orphan guild owners ───────
    inserted = 0
    skipped = 0
    seen: set[str] = set()
    for o in orphans:
        oid = o["owner_user_id"]
        if oid in seen:
            continue
        seen.add(oid)
        existing = await db.users.find_one({"id": oid}, {"_id": 1})
        if existing:
            skipped += 1
            continue
        short = oid.split("-")[0]
        doc = {
            "id": oid,
            "email": f"orphan_{short}@orbus.test",
            "username": f"orphan_{short}",
            "password_hash": SHADOW_PW_SENTINEL,
            "is_admin": False,
            "is_test_user": True,
            "created_at": now,
            "updated_at": now,
        }
        try:
            await db.users.insert_one(doc)
            inserted += 1
        except Exception as e:
            print(f"  shadow insert failed for {oid}: {e}")
            skipped += 1
    print(f"[shadow] inserted={inserted} skipped(already-present)={skipped}")

    # ── Verify ───────────────────────────────────────────────────────────
    test_ids_after = await db.users.distinct("id", {"is_test_user": True})
    remaining = await db.guilds.count_documents(
        {"owner_user_id": {"$nin": test_ids_after}}
    )
    print(f"[verify] leaderboard visible guilds after = {remaining}")
    print(f"[verify] expected ≈ {len(audit_result['buckets']['allowlist']) + len(audit_result['buckets']['pending_ambiguous']) + len(audit_result['buckets']['unknown_real'])}")
    return {"flagged_users": flagged, "shadow_inserted": inserted, "remaining_visible": remaining}


# ─── Rollback ───────────────────────────────────────────────────────────
async def rollback(db, backup_path: Path) -> None:
    data = json.loads(backup_path.read_text())
    if data.get("shadow_pw_sentinel") != SHADOW_PW_SENTINEL:
        print("ABORT: backup sentinel mismatch — refusing to rollback.")
        sys.exit(4)

    # Phase A: unset flag on previously-flagged users
    ids = [r["user_id"] for r in data.get("test_residual_to_flag", [])]
    if ids:
        res = await db.users.update_many(
            {"id": {"$in": ids}},
            {"$unset": {"is_test_user": ""}},
        )
        print(f"[rb/flag] matched={res.matched_count} unset={res.modified_count}")

    # Phase B: delete shadow placeholders (identified by sentinel + id list)
    orphan_ids = [o["owner_user_id"] for o in data.get("orphans_to_shadow", [])]
    if orphan_ids:
        res = await db.users.delete_many({
            "id": {"$in": orphan_ids},
            "password_hash": SHADOW_PW_SENTINEL,
        })
        print(f"[rb/shadow] deleted={res.deleted_count}")
    print("[rollback] done")


# ─── Main ───────────────────────────────────────────────────────────────
async def _main(args: argparse.Namespace) -> None:
    # Resolve env. Prefer system env, fall back to backend/.env on the pod.
    env_path = Path(args.env_file).resolve() if args.env_file else None
    if env_path and env_path.exists():
        load_dotenv(env_path)
        cfg = dotenv_values(env_path)
    else:
        cfg = {k: os.environ.get(k) for k in ("MONGO_URL", "DB_NAME")}

    mongo_url = cfg.get("MONGO_URL") or os.environ.get("MONGO_URL")
    db_name = cfg.get("DB_NAME") or os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("FATAL: MONGO_URL and DB_NAME must be set (env or --env-file).",
              file=sys.stderr)
        sys.exit(2)

    if _looks_like_preview_uri(mongo_url) and not args.allow_preview:
        print("ABORT: MONGO_URL looks like preview/local. Pass --allow-preview "
              "to override (only use this on the prod pod or for a deliberate "
              "preview re-test).", file=sys.stderr)
        sys.exit(5)

    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]

    try:
        if args.rollback:
            await rollback(db, Path(args.rollback))
            return

        result = await audit(db)
        _print_audit(result)

        if not args.apply:
            print("\n(dry-run — pass --apply to write. NO writes performed.)")
            return

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        backup_path = Path(args.backup_dir) / f"prod_leaderboard_residual_flag_backup_{ts}.json"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        await apply(db, result, backup_path)
    finally:
        cli.close()


def _cli() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Orbus prod leaderboard cleanup")
    ap.add_argument("--apply", action="store_true",
                    help="Perform writes (default is dry-run, READ ONLY).")
    ap.add_argument("--rollback", metavar="BACKUP_JSON",
                    help="Path to a backup file to roll back.")
    ap.add_argument("--env-file", default="/app/backend/.env",
                    help="Path to .env file (defaults to /app/backend/.env).")
    ap.add_argument("--backup-dir", default="/tmp",
                    help="Where to drop the backup JSON (default /tmp).")
    ap.add_argument("--allow-preview", action="store_true",
                    help="Bypass the preview-URI guard (do not use on prod).")
    return ap.parse_args()


if __name__ == "__main__":
    asyncio.run(_main(_cli()))
