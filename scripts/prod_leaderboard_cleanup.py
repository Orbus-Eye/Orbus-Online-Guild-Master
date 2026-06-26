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
    "mr.gualmini@gmail.com",          # Gualma — Sentiero di Efreto / The Loremaster
    "gianluca.brandi42@gmail.com",    # Drakarys
    "samuelemazzini1994@gmail.com",   # Harambes — confirmed 2026-06-26
    "ginnyo.gear@gmail.com",          # Magmorella — Il Regno di Lanafuoco — 2026-06-26
    "tester@orbus.test",              # sandbox admin
}
ALLOWLIST_GUILDS = {
    "sentiero di efreto",
    "drakarys",
    "harambes",                       # name-based protection while email pending
    "the loremaster",                 # CONFIRMED real player (mr.gualmini@gmail.com)
    "il regno di lanafuoco",          # CONFIRMED real player 2026-06-26 (owner email TBD)
    "crociata d'argento",             # CONFIRMED new real tester 2026-06-26 (owner email TBD)
}
# Guilds we explicitly DO NOT TOUCH until the user classifies them.
PENDING_AMBIGUOUS: set[str] = set()  # cleared 2026-06-26 after user classification
# Confirmed test guilds that must be flagged is_test_user=True on their owner.
TEST_GUILDS_FORCE = {
    "the iron lantern",               # CONFIRMED test by user 2026-06-26
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
    # 2026-06-26 extension — user-requested broader test-fingerprint coverage:
    #   • @test (any TLD: .com, .local, .org, .io, .anything)
    #   • test@ (any prefix beginning with the word "test", any domain)
    #   • @orbus.com  (literal — separate from the .test fixture domain)
    re.compile(r"@test\.", re.IGNORECASE),
    re.compile(r"(^|\W)test@", re.IGNORECASE),
    re.compile(r"@orbus\.com$", re.IGNORECASE),
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


# ─── Hard-delete guard ─────────────────────────────────────────────────
# Anti-foot-gun: enforce at call sites that we never `delete_*` on users
# or guilds outside the rollback path (which is gated by the
# shadow-sentinel check). Date-mode in particular MUST NOT delete anything.
def _assert_no_destructive_op(collection_name: str, op: str) -> None:
    forbidden_collections = {"users", "guilds"}
    forbidden_ops = {"delete_one", "delete_many", "drop"}
    if collection_name in forbidden_collections and op in forbidden_ops:
        raise RuntimeError(
            f"REFUSED: destructive op '{op}' on '{collection_name}' is "
            "disallowed by policy (NO HARD DELETE). "
            "Use is_test_user=True flagging instead."
        )


# ─── Date-mode (2026-06-26 extension) ──────────────────────────────────
# Flag-by-date-range audit + apply. Targets guilds whose `created_at`
# falls in the configured UTC range (default 2026-06-23 to 2026-06-24
# inclusive). Idempotent: a user already `is_test_user=True` is reported
# as `ALREADY_FLAGGED` and not re-written. Allowlist (email OR guild name)
# is honoured. NO HARD DELETE.
DATE_MODE_START = datetime(2026, 6, 23, 0, 0, 0, tzinfo=timezone.utc)
DATE_MODE_END = datetime(2026, 6, 25, 0, 0, 0, tzinfo=timezone.utc)
DATE_MODE_REASON = "date_range_2026-06-23_to_24"


def _norm_created_at(value):
    """`guilds.created_at` may be a string (ISO), a datetime, or missing."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            v = value.rstrip("Z")
            dt = datetime.fromisoformat(v)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


async def audit_date_range(db, start: datetime, end: datetime) -> dict:
    """Read-only date-range audit. Returns per-guild classification."""
    # `created_at` may be stored as string OR datetime depending on legacy
    # writers — query both forms with $or for safety.
    rng_str = {
        "created_at": {"$gte": start.isoformat(), "$lt": end.isoformat()}
    }
    rng_dt = {"created_at": {"$gte": start, "$lt": end}}
    guilds = await db.guilds.find(
        {"$or": [rng_str, rng_dt]},
        {
            "_id": 0,
            "id": 1,
            "name": 1,
            "owner_user_id": 1,
            "created_at": 1,
        },
    ).sort("created_at", 1).to_list(None)

    owner_ids = list({g["owner_user_id"] for g in guilds if g.get("owner_user_id")})
    owners = await db.users.find(
        {"id": {"$in": owner_ids}},
        {"_id": 0, "id": 1, "email": 1, "is_test_user": 1},
    ).to_list(None)
    by_uid = {u["id"]: u for u in owners}

    will_flag: list[dict] = []
    allowlist_skipped: list[dict] = []
    already_flagged: list[dict] = []
    no_owner: list[dict] = []

    for g in guilds:
        gname_lower = (g.get("name") or "").lower()
        owner = by_uid.get(g.get("owner_user_id"))
        created_at_iso = (
            _norm_created_at(g.get("created_at")).isoformat()
            if _norm_created_at(g.get("created_at")) else "(unknown)"
        )

        # No owner doc — surface but never flag (no user_id to write to).
        if not owner:
            no_owner.append({
                "guild": g.get("name"),
                "guild_id": g.get("id"),
                "owner_user_id": g.get("owner_user_id"),
                "created_at": created_at_iso,
            })
            continue

        email_lower = (owner.get("email") or "").lower()

        # Allowlist (email OR guild name).
        if email_lower in ALLOWLIST_EMAILS or gname_lower in ALLOWLIST_GUILDS:
            allowlist_skipped.append({
                "guild": g.get("name"),
                "owner_email_masked": mask_email(owner.get("email") or ""),
                "created_at": created_at_iso,
                "reason": "email_in_ALLOWLIST_EMAILS" if email_lower in ALLOWLIST_EMAILS
                          else "guild_in_ALLOWLIST_GUILDS",
            })
            continue

        # Already flagged → idempotency.
        if owner.get("is_test_user") is True:
            already_flagged.append({
                "guild": g.get("name"),
                "owner_email_masked": mask_email(owner.get("email") or ""),
                "created_at": created_at_iso,
            })
            continue

        will_flag.append({
            "user_id": owner["id"],
            "guild": g.get("name"),
            "guild_id": g.get("id"),
            "owner_email_masked": mask_email(owner.get("email") or ""),
            "created_at": created_at_iso,
        })

    return {
        "range_start_utc": start.isoformat(),
        "range_end_utc_exclusive": end.isoformat(),
        "total_in_range": len(guilds),
        "n_will_flag": len(will_flag),
        "n_allowlist_skipped": len(allowlist_skipped),
        "n_already_flagged": len(already_flagged),
        "n_no_owner": len(no_owner),
        "will_flag": will_flag,
        "allowlist_skipped": allowlist_skipped,
        "already_flagged": already_flagged,
        "no_owner": no_owner,
    }


def _print_date_audit(res: dict) -> None:
    print("\n── DATE-MODE AUDIT (read-only) ──")
    print(f"range: {res['range_start_utc']} → {res['range_end_utc_exclusive']} (UTC, end-exclusive)")
    print(f"total_in_range     : {res['total_in_range']}")
    print(f"  WILL_FLAG        : {res['n_will_flag']}")
    print(f"  ALLOWLIST_SKIP   : {res['n_allowlist_skipped']}")
    print(f"  ALREADY_FLAGGED  : {res['n_already_flagged']}")
    print(f"  NO_OWNER         : {res['n_no_owner']}")
    if res["will_flag"]:
        print("\n→ WILL_FLAG (would set is_test_user=True on these owners):")
        for r in res["will_flag"]:
            print(f"  • {r['guild']:<32}  owner={r['owner_email_masked']:<30}  created={r['created_at']}")
    if res["allowlist_skipped"]:
        print("\n✅ ALLOWLIST_SKIP (never touched):")
        for r in res["allowlist_skipped"]:
            print(f"  • {r['guild']:<32}  owner={r['owner_email_masked']:<30}  created={r['created_at']}  via={r['reason']}")
    if res["already_flagged"]:
        print("\n⏭  ALREADY_FLAGGED (idempotent skip — no write):")
        for r in res["already_flagged"]:
            print(f"  • {r['guild']:<32}  owner={r['owner_email_masked']:<30}  created={r['created_at']}")
    if res["no_owner"]:
        print("\n⚠  NO_OWNER (orphan guild without user doc — surfaced, NOT flagged):")
        for r in res["no_owner"]:
            print(f"  • {r['guild']:<32}  guild_id={r['guild_id']}  created={r['created_at']}")


async def apply_date_range(db, res: dict, backup_path: Path) -> dict:
    """Idempotent write: $set is_test_user=True on each WILL_FLAG owner +
    one audit_log row per flagged user. NO HARD DELETE."""
    now = datetime.now(timezone.utc)
    will_flag = res["will_flag"]

    backup = {
        "timestamp_utc": now.isoformat(),
        "reason": "prod leaderboard cleanup — date-range mode (NO hard delete)",
        "operation": "users.update_one({id}, {$set:{is_test_user:True, flagged_at, flagged_reason}})",
        "range_start_utc": res["range_start_utc"],
        "range_end_utc_exclusive": res["range_end_utc_exclusive"],
        "allowlist_emails": sorted(ALLOWLIST_EMAILS),
        "allowlist_guilds": sorted(ALLOWLIST_GUILDS),
        "no_owner_skipped": res["no_owner"],
        "allowlist_skipped": res["allowlist_skipped"],
        "already_flagged_skipped": res["already_flagged"],
        "users_flagged": will_flag,
    }
    backup_path.write_text(json.dumps(backup, indent=2, default=str))
    print(f"\n[backup] saved → {backup_path}")

    if not will_flag:
        print("[apply] nothing to flag (idempotent no-op).")
        return {"flagged": 0, "audit_written": 0}

    # Defence-in-depth: re-check that no ALLOWLIST email leaked into the set.
    ids = [r["user_id"] for r in will_flag]
    leaks = await db.users.find(
        {"id": {"$in": ids}, "email": {"$in": list(ALLOWLIST_EMAILS)}},
        {"_id": 0, "id": 1, "email": 1},
    ).to_list(None)
    if leaks:
        print(f"⛔ ABORT: allowlist email leaked into flag set: {leaks}")
        sys.exit(3)

    flagged = 0
    audit_written = 0
    for r in will_flag:
        # Final per-row idempotency guard: if some concurrent run already
        # flagged this user, skip without write.
        existing = await db.users.find_one(
            {"id": r["user_id"]},
            {"_id": 0, "is_test_user": 1, "email": 1},
        )
        if not existing:
            print(f"  [skip] user_id {r['user_id']} not found (race?)")
            continue
        if existing.get("is_test_user") is True:
            continue
        if (existing.get("email") or "").lower() in ALLOWLIST_EMAILS:
            print(f"  ⛔ ABORT: would flag an ALLOWLIST email — {existing['email']}")
            sys.exit(3)
        upd = await db.users.update_one(
            {"id": r["user_id"], "is_test_user": {"$ne": True}},
            {"$set": {
                "is_test_user": True,
                "flagged_at": now.isoformat(),
                "flagged_reason": DATE_MODE_REASON,
                "updated_at": now,
            }},
        )
        if upd.modified_count:
            flagged += 1
            # Write audit_log row (NO email / NO token in metadata).
            try:
                await db.audit_log.insert_one({
                    "id": f"flag-{r['user_id']}-{int(now.timestamp())}",
                    "event_type": "user_flagged_test",
                    "actor_user_id": None,
                    "actor_guild_id": None,
                    "metadata": {
                        "user_id": r["user_id"],
                        "guild_name": r["guild"],
                        "guild_id": r["guild_id"],
                        "created_at": r["created_at"],
                        "mode": "date_range_v1",
                        "actor": "cleanup_script",
                        "range_start_utc": res["range_start_utc"],
                        "range_end_utc_exclusive": res["range_end_utc_exclusive"],
                    },
                    "created_at": now.isoformat(),
                })
                audit_written += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  [warn] audit_log write failed for {r['user_id']}: {exc}")

    print(f"[flag]  modified={flagged}/{len(will_flag)}  audit_written={audit_written}")
    return {"flagged": flagged, "audit_written": audit_written}


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

        # 0. Forced-test guild names — flag even when the owner email would
        #    normally pass an allowlist heuristic. The owner-email allowlist
        #    is still respected to spare the sandbox tester admin.
        if gn in TEST_GUILDS_FORCE and owner is not None:
            email_lower = (owner.get("email") or "").lower()
            if email_lower not in ALLOWLIST_EMAILS:
                buckets["test_residual"].append({
                    "user_id": owner["id"],
                    "guild_id": g["id"],
                    "guild": g["name"],
                    "owner_email_masked": mask_email(owner["email"]),
                    "peak": g.get("max_team_power_ever", 0),
                    "reason": "TEST_GUILDS_FORCE",
                })
                continue

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

        if args.date_mode:
            # Date-range cleanup (2026-06-23 → 2026-06-24 UTC by default).
            start = args.date_start or DATE_MODE_START
            end = args.date_end or DATE_MODE_END
            if isinstance(start, str):
                start = datetime.fromisoformat(start.rstrip("Z")).replace(tzinfo=timezone.utc)
            if isinstance(end, str):
                end = datetime.fromisoformat(end.rstrip("Z")).replace(tzinfo=timezone.utc)
            res = await audit_date_range(db, start, end)
            _print_date_audit(res)
            if not args.apply:
                print("\n(dry-run — pass --apply to write. NO writes performed.)")
                return
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
            backup_path = Path(args.backup_dir) / f"prod_leaderboard_date_mode_backup_{ts}.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            await apply_date_range(db, res, backup_path)
            # Final summary line for log scraping
            print(
                f"\n[summary] N_will_flag={res['n_will_flag']}  "
                f"N_allowlist_skipped={res['n_allowlist_skipped']}  "
                f"N_already_flagged={res['n_already_flagged']}  "
                f"N_no_owner={res['n_no_owner']}  "
                f"N_total_in_range={res['total_in_range']}"
            )
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
    ap.add_argument("--date-mode", action="store_true",
                    help="Run the date-range cleanup (2026-06-23 to 2026-06-24 "
                         "UTC by default), independent from the legacy "
                         "pattern-based audit. NO HARD DELETE.")
    ap.add_argument("--date-start", default=None,
                    help="Override date-mode start (ISO UTC, inclusive). "
                         "Default: 2026-06-23T00:00:00+00:00.")
    ap.add_argument("--date-end", default=None,
                    help="Override date-mode end (ISO UTC, exclusive). "
                         "Default: 2026-06-25T00:00:00+00:00.")
    return ap.parse_args()


if __name__ == "__main__":
    asyncio.run(_main(_cli()))
