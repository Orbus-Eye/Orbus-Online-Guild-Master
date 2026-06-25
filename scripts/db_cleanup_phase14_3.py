"""
DB cleanup — Phase 14.3 (authorized by user message 2026-06-25).

Performs, in order:
  1. Snapshot + JSON backup → /app/memory/db_pre_cleanup_backup.json
  2. Flag denylist users with is_test_user=True (reversible $unset)
  3. (no schema change here — the leaderboard patch is applied separately
      to services.py and is independent of this script)
  4. Delete orphan guilds (owner_user_id not in users.id) + cascade
  5. Emit ambiguous users list → /app/memory/db_ambiguous_users.md
  6. Print structured summary

NOT TOUCHED:
  - denylist users themselves (only flagged, never deleted)
  - 16 ambiguous users (left untouched, just listed)
  - allowlist: mr.gualmini@gmail.com + guild "Sentiero di Efreto"
  - seeds: adventurer_classes, adventurer_traits, dungeons, items

Idempotent: re-running yields no-op (orphans already gone, flags already
set, ambiguous list regenerated).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = ROOT / "backend" / ".env"
BACKUP_PATH = ROOT / "memory" / "db_pre_cleanup_backup.json"
AMBIGUOUS_LIST_PATH = ROOT / "memory" / "db_ambiguous_users.md"

ALLOWLIST_EMAIL = "mr.gualmini@gmail.com"
ALLOWLIST_GUILD_NAMES = {"Sentiero di Efreto"}

# ── Permanent allowlist (Phase 14.5-hotfix, 2026-06-25) ─────────────────────
# Single source of truth for accounts/guilds that NO cleanup, conftest sweep,
# or denylist operation is ever allowed to touch. Kept as plain sets so
# callers can do `email.lower() in ALLOWLIST_EMAILS` and
# `name.lower() in ALLOWLIST_GUILDS_LOWER`.
ALLOWLIST_EMAILS = {
    "mr.gualmini@gmail.com",
    "gianluca.brandi42@gmail.com",
    # Harambes owner email PENDING (real prod player). Name-based protection
    # on the guild "harambes" is in place below until the user provides the
    # email.
}
ALLOWLIST_GUILDS_LOWER = {
    "sentiero di efreto",
    "drakarys",
    "harambes",  # real prod player (owner email pending)
}

# Denylist patterns (case-insensitive, on .lower() of email)
_DENY_CONTAINS = (
    "@orbus.test",
    "tester@",
    "+smoke",
    "+smoketest",
    "+welcometest",
    "+secrettest",
    "+pwd",
    "+e2e",
    "@example.com",
    "@example.org",
    "@test.local",
)
_DENY_STARTS = (
    "smoke",
    "smoketest",
    "welcometest",
    "secrettest",
    "pytest",
    "qa-",
    "dev-",
)
# Ambiguous: matched only when NOT a denylist match.
_AMBIG_DOMAINS = ("@x.test", "@test.com", "@test.org")


def classify(email: str) -> str:
    e = (email or "").strip().lower()
    # Hardcoded permanent allowlist — never touch these emails.
    if e in ALLOWLIST_EMAILS:
        return "allowlist"
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

    # ─────────────────────────────────────────────────────────────────
    # STEP 0 — snapshot users / classify
    # ─────────────────────────────────────────────────────────────────
    users_all = await db.users.find({}).to_list(None)
    living_user_ids = {u["id"] for u in users_all}

    by_class: dict[str, list[dict]] = {"allowlist": [], "denylist": [], "ambiguous": [], "real": []}
    for u in users_all:
        by_class[classify(u.get("email", ""))].append(u)

    deny_ids = {u["id"] for u in by_class["denylist"]}
    ambig_ids = {u["id"] for u in by_class["ambiguous"]}

    # Sanity guards
    allow_users = [u for u in by_class["allowlist"] if u.get("email", "").lower() == ALLOWLIST_EMAIL.lower()]
    assert len(allow_users) == 1, f"Allowlist user not unique: {len(allow_users)}"
    assert ALLOWLIST_EMAIL.lower() not in {u["email"].lower() for u in by_class["denylist"]}, \
        "ALLOWLIST EMAIL leaked into denylist!"

    totals_before = {
        "users": len(users_all),
        "guilds": await db.guilds.count_documents({}),
        "adventurers": await db.adventurers.count_documents({}),
        "inventory_items": await db.inventory_items.count_documents({}),
        "equipped_items": await db.equipped_items.count_documents({}),
        "expeditions": await db.expeditions.count_documents({}),
        "expedition_members": await db.expedition_members.count_documents({}),
        "recruitment_offers": await db.recruitment_offers.count_documents({}),
        "classification": {k: len(v) for k, v in by_class.items()},
    }
    print(f"[snapshot] {totals_before}")

    # ─────────────────────────────────────────────────────────────────
    # STEP 1 — identify guilds
    # ─────────────────────────────────────────────────────────────────
    guilds_all_min = await db.guilds.find({}, {"id": 1, "name": 1, "owner_user_id": 1}).to_list(None)
    orphan_guild_ids = [g["id"] for g in guilds_all_min if g["owner_user_id"] not in living_user_ids]
    deny_owned_guild_ids = [g["id"] for g in guilds_all_min if g["owner_user_id"] in deny_ids]

    # Allowlist sanity: ensure 'Sentiero di Efreto' belongs to allowlist user, and is
    # NEVER classified as orphan or deny-owned.
    allow_uid = allow_users[0]["id"]
    allow_guilds = [g for g in guilds_all_min if g["owner_user_id"] == allow_uid]
    assert any(g["name"] in ALLOWLIST_GUILD_NAMES for g in allow_guilds), \
        f"Allowlist guild 'Sentiero di Efreto' not found for {ALLOWLIST_EMAIL}"
    for g in allow_guilds:
        assert g["id"] not in orphan_guild_ids, "Allowlist guild flagged as orphan!"
        assert g["id"] not in deny_owned_guild_ids, "Allowlist guild flagged as deny-owned!"

    print(f"[scope] orphan_guilds={len(orphan_guild_ids)} deny_owned_guilds={len(deny_owned_guild_ids)}")

    # ─────────────────────────────────────────────────────────────────
    # STEP 2 — full backup BEFORE any write
    # ─────────────────────────────────────────────────────────────────
    backup = {
        "backup_created_at": utcnow_iso(),
        "schema_version": 1,
        "totals_before": totals_before,
        "denylist_users": by_class["denylist"],
        "ambiguous_users_snapshot": by_class["ambiguous"],
        "allowlist_user": by_class["allowlist"],
        "guilds_owned_by_denylist": [g for g in await db.guilds.find({"owner_user_id": {"$in": list(deny_ids)}}).to_list(None)],
        "orphan_guilds": [g for g in await db.guilds.find({"id": {"$in": orphan_guild_ids}}).to_list(None)],
        "adventurers_in_orphans": await db.adventurers.find({"guild_id": {"$in": orphan_guild_ids}}).to_list(None),
        "inventory_items_in_orphans": await db.inventory_items.find({"guild_id": {"$in": orphan_guild_ids}}).to_list(None),
        "equipped_items_in_orphans": await db.equipped_items.find({"guild_id": {"$in": orphan_guild_ids}}).to_list(None),
        "expeditions_in_orphans": await db.expeditions.find({"guild_id": {"$in": orphan_guild_ids}}).to_list(None),
        "recruitment_offers_in_orphans": await db.recruitment_offers.find({"guild_id": {"$in": orphan_guild_ids}}).to_list(None),
    }
    # expedition_members cascade by expedition_id
    orphan_exp_ids = [e["id"] for e in backup["expeditions_in_orphans"]]
    backup["expedition_members_in_orphans"] = await db.expedition_members.find(
        {"expedition_id": {"$in": orphan_exp_ids}}
    ).to_list(None) if orphan_exp_ids else []

    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_PATH.write_text(json.dumps(backup, default=_json_default, indent=2))
    size_kb = BACKUP_PATH.stat().st_size / 1024
    print(f"[backup] wrote {BACKUP_PATH} ({size_kb:.1f} KB)")

    # ─────────────────────────────────────────────────────────────────
    # STEP 3 — set is_test_user=True on denylist (idempotent)
    # ─────────────────────────────────────────────────────────────────
    # Explicit safety: never include allowlist email.
    deny_ids_list = list(deny_ids)
    flag_result = await db.users.update_many(
        {
            "id": {"$in": deny_ids_list},
            "email": {"$ne": ALLOWLIST_EMAIL},  # double-guard
        },
        {"$set": {"is_test_user": True, "test_flagged_at": utcnow_iso()}},
    )
    print(f"[flag] matched={flag_result.matched_count} modified={flag_result.modified_count}")

    # Verify allowlist NOT flagged
    allow_doc = await db.users.find_one({"email": ALLOWLIST_EMAIL}, {"is_test_user": 1})
    assert not allow_doc.get("is_test_user"), "ALLOWLIST got flagged — ABORT"

    # Verify ambiguous NOT flagged
    ambig_flagged = await db.users.count_documents({"id": {"$in": list(ambig_ids)}, "is_test_user": True})
    assert ambig_flagged == 0, f"{ambig_flagged} ambiguous users got flagged — ABORT"

    # ─────────────────────────────────────────────────────────────────
    # STEP 4 — delete orphan guilds + cascade
    # ─────────────────────────────────────────────────────────────────
    cascade_counts = {}
    if orphan_guild_ids:
        # Final guard: ensure allowlist guild NOT in this list.
        for g in allow_guilds:
            assert g["id"] not in orphan_guild_ids, "ABORT: allowlist guild in delete list"

        r = await db.adventurers.delete_many({"guild_id": {"$in": orphan_guild_ids}})
        cascade_counts["adventurers"] = r.deleted_count
        r = await db.inventory_items.delete_many({"guild_id": {"$in": orphan_guild_ids}})
        cascade_counts["inventory_items"] = r.deleted_count
        r = await db.equipped_items.delete_many({"guild_id": {"$in": orphan_guild_ids}})
        cascade_counts["equipped_items"] = r.deleted_count
        if orphan_exp_ids:
            r = await db.expedition_members.delete_many({"expedition_id": {"$in": orphan_exp_ids}})
            cascade_counts["expedition_members"] = r.deleted_count
        else:
            cascade_counts["expedition_members"] = 0
        r = await db.expeditions.delete_many({"guild_id": {"$in": orphan_guild_ids}})
        cascade_counts["expeditions"] = r.deleted_count
        r = await db.recruitment_offers.delete_many({"guild_id": {"$in": orphan_guild_ids}})
        cascade_counts["recruitment_offers"] = r.deleted_count
        r = await db.guilds.delete_many({"id": {"$in": orphan_guild_ids}})
        cascade_counts["guilds"] = r.deleted_count
    else:
        cascade_counts = {k: 0 for k in (
            "adventurers", "inventory_items", "equipped_items",
            "expedition_members", "expeditions", "recruitment_offers", "guilds"
        )}
    print(f"[cascade] {cascade_counts}")

    # ─────────────────────────────────────────────────────────────────
    # STEP 5 — emit ambiguous users list (masked, read-only review)
    # ─────────────────────────────────────────────────────────────────
    md_lines = [
        "# Ambiguous Users — Manual Review",
        f"**Generated:** {utcnow_iso()}",
        f"**Count:** {len(by_class['ambiguous'])}",
        "",
        "These accounts match neither the allowlist nor the denylist patterns.",
        "They were NOT flagged with `is_test_user` and were NOT deleted. The",
        "operator must decide individually. Emails are masked.",
        "",
        "| # | Email | Guild | Adv. | Exp. | Created | Last login |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for i, u in enumerate(sorted(by_class["ambiguous"], key=lambda x: x.get("email", "")), 1):
        uid = u["id"]
        g = await db.guilds.find_one({"owner_user_id": uid}, {"name": 1, "id": 1})
        adv_n = await db.adventurers.count_documents({"guild_id": g["id"]}) if g else 0
        exp_n = await db.expeditions.count_documents({"guild_id": g["id"]}) if g else 0
        last_login = u.get("last_login_at") or "—"
        if isinstance(last_login, datetime):
            last_login = last_login.isoformat()
        created = u.get("created_at")
        if isinstance(created, datetime):
            created = created.isoformat()
        md_lines.append(
            f"| {i} | `{mask(u.get('email',''))}` | "
            f"{g['name'] if g else '—'} | {adv_n} | {exp_n} | "
            f"{created or '—'} | {last_login} |"
        )
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("*No write performed on these users. Awaiting human review.*")
    AMBIGUOUS_LIST_PATH.write_text("\n".join(md_lines))
    print(f"[ambig] wrote {AMBIGUOUS_LIST_PATH}")

    # ─────────────────────────────────────────────────────────────────
    # STEP 6 — verification (DO NOT print sensitive fields)
    # ─────────────────────────────────────────────────────────────────
    totals_after = {
        "users": await db.users.count_documents({}),
        "guilds": await db.guilds.count_documents({}),
        "orphan_guilds_remaining": 0,
        "adventurers": await db.adventurers.count_documents({}),
        "inventory_items": await db.inventory_items.count_documents({}),
        "equipped_items": await db.equipped_items.count_documents({}),
        "expeditions": await db.expeditions.count_documents({}),
        "expedition_members": await db.expedition_members.count_documents({}),
        "recruitment_offers": await db.recruitment_offers.count_documents({}),
        "is_test_user_true": await db.users.count_documents({"is_test_user": True}),
    }
    # recompute orphan count
    living_ids_now = {u async for u in db.users.find({}, {"id": 1})}
    living_ids_now = {u["id"] for u in await db.users.find({}, {"id": 1}).to_list(None)}
    orphan_after = await db.guilds.count_documents({"owner_user_id": {"$nin": list(living_ids_now)}})
    totals_after["orphan_guilds_remaining"] = orphan_after

    # Allowlist final guard
    allow_doc = await db.users.find_one({"email": ALLOWLIST_EMAIL})
    sentiero = await db.guilds.find_one({"name": "Sentiero di Efreto"}, {"id": 1, "owner_user_id": 1})
    assert allow_doc is not None, "ALLOWLIST USER MISSING — ABORT"
    assert sentiero is not None, "ALLOWLIST GUILD MISSING — ABORT"
    assert sentiero["owner_user_id"] == allow_doc["id"], "ALLOWLIST GUILD OWNERSHIP MISMATCH"
    print(f"[verify] {totals_after}")
    print(f"[verify] allowlist preserved: user_id={allow_doc['id'][:8]}… guild_id={sentiero['id'][:8]}…")

    print("\n=== SUMMARY ===")
    print(json.dumps({
        "totals_before": totals_before,
        "totals_after": totals_after,
        "cascade_counts": cascade_counts,
        "users_flagged_is_test_user": flag_result.modified_count,
        "denylist_total": len(by_class["denylist"]),
        "ambiguous_total": len(by_class["ambiguous"]),
        "allowlist_total": len(by_class["allowlist"]),
        "backup_file": str(BACKUP_PATH),
        "backup_size_bytes": BACKUP_PATH.stat().st_size,
        "ambiguous_review_file": str(AMBIGUOUS_LIST_PATH),
    }, indent=2, default=_json_default))

    cli.close()


if __name__ == "__main__":
    asyncio.run(main())
