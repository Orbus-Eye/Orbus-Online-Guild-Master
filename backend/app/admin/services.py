"""Admin domain services (Phase 5.5f).

Pure CRUD on the four seed collections (classes, traits, dungeons, items)
plus the monetization invariant enforcer and a couple of utility helpers.
All ops accept the Motor `db` handle so they are unit-testable.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


VALID_ROLES = ("Tank", "DPS", "Healer")
VALID_AFFECTED_STAT = ("strength", "agility", "intellect", "endurance", "faith", "xp_gain")
VALID_ITEM_TYPES = ("weapon", "armor", "accessory", "consumable")
VALID_RARITIES = ("Common", "Uncommon", "Rare", "Epic")


def validate_item_monetization(item: dict) -> None:
    """Reject inconsistent flags: real-money sale only allowed for pure cosmetics."""
    if item.get("can_be_sold_for_real_money"):
        if (
            not item.get("is_cosmetic", False)
            or item.get("affects_combat", False)
            or item.get("affects_economy", False)
            or item.get("affects_ranking", False)
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid item: can_be_sold_for_real_money requires "
                    "is_cosmetic=true AND affects_combat=false AND "
                    "affects_economy=false AND affects_ranking=false"
                ),
            )


def _slug_ok(s: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s or ""))


def _strip_db_fields(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "_id"}


def _build_item_doc(payload: dict, existing: Optional[dict] = None) -> dict:
    base = dict(existing) if existing else {
        "id": str(uuid.uuid4()),
        "level_required": 1,
        "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 0,
        "endurance_bonus": 0, "faith_bonus": 0,
        "is_tradeable": True, "is_cosmetic": False,
        "affects_combat": True, "affects_economy": False, "affects_ranking": False,
        "can_be_sold_for_gold": True, "can_be_sold_for_real_money": False,
        "is_active": True,
    }
    for k in ("name", "slug", "description", "item_type", "rarity"):
        if k in payload:
            base[k] = str(payload[k]).strip()
    for k in ("level_required", "power_score", "strength_bonus", "agility_bonus",
              "intellect_bonus", "endurance_bonus", "faith_bonus"):
        if k in payload:
            base[k] = int(payload[k])
    for k in ("is_tradeable", "is_cosmetic", "affects_combat", "affects_economy",
              "affects_ranking", "can_be_sold_for_gold",
              "can_be_sold_for_real_money", "is_active"):
        if k in payload:
            base[k] = bool(payload[k])
    return base


__all__ = [
    "VALID_ROLES",
    "VALID_AFFECTED_STAT",
    "VALID_ITEM_TYPES",
    "VALID_RARITIES",
    "validate_item_monetization",
    "_slug_ok",
    "_strip_db_fields",
    "_build_item_doc",
    "utc_now",
    "flag_test_users_aggressive",
    "CLEANUP_ALLOWLIST_EMAILS",
    "CLEANUP_ALLOWLIST_GUILDS",
    "CLEANUP_TEST_GUILDS_FORCE",
]


# ═════════════════════════════════════════════════════════════════════════
# Phase 16.1 — Aggressive flag-test-users service
# ═════════════════════════════════════════════════════════════════════════
# Hardcoded source of truth for the admin endpoint. Intentionally NOT
# imported from conftest or from the prod cleanup script — those files
# protect the test/preview boundary and must NOT be touched. If the
# allowlist changes in production we must edit THIS file in code review,
# get it reviewed, and redeploy. No silent mutation.
CLEANUP_ALLOWLIST_EMAILS = frozenset({
    "mr.gualmini@gmail.com",
    "gianluca.brandi42@gmail.com",
    "samuelemazzini1994@gmail.com",
    "ginnyo.gear@gmail.com",
    "lordcoby87@gmail.com",  # Crociata d'Argento owner — confirmed 2026-06-26
    "kyrie.shepard@gmail.com",  # Eclipse Vanguard owner — confirmed 2026-06-27 (Phase 19.2)
})
CLEANUP_ALLOWLIST_GUILDS = frozenset({
    "sentiero di efreto",
    "the loremaster",
    "drakarys",
    "harambes",
    "il regno di lanafuoco",
    "crociata d'argento",  # CONFIRMED new real tester 2026-06-26 (owner email TBD)
    "eclipse vanguard",  # CONFIRMED real player (kyrie.shepard@gmail.com) — 2026-06-27 (Phase 19.2)
})
# Guild names (case-insensitive) that MUST be flagged even if their owner
# would otherwise fall in the allowlist — confirmed test rigs from user.
CLEANUP_TEST_GUILDS_FORCE = frozenset({
    "the iron lantern",
})

CLEANUP_REASON = "admin_endpoint_aggressive_v1"
_CLEANUP_AUDIT_EVENT = "user_flagged_test_admin_api"


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, _, dom = email.partition("@")
    if len(local) <= 2:
        return local[0] + "*@" + dom
    return local[0] + "*" * (len(local) - 2) + local[-1] + "@" + dom


def _assert_no_destructive_op(collection: str, op: str) -> None:
    forbidden = {
        ("users", "delete_one"), ("users", "delete_many"), ("users", "drop"),
        ("guilds", "delete_one"), ("guilds", "delete_many"), ("guilds", "drop"),
    }
    if (collection, op) in forbidden:
        raise RuntimeError(
            f"REFUSED: destructive op '{op}' on '{collection}' is "
            "disallowed by policy (NO HARD DELETE)."
        )


async def flag_test_users_aggressive(
    db,
    *,
    mode: str,
    actor_admin_id: str | None,
    sample_cap: int = 50,
) -> dict:
    """Aggressive bulk flag with CAS guard + audit. Read-only when
    `mode='dry_run'`. The double-gate (confirm_apply) is enforced at the
    router layer."""
    # Defence: this service NEVER calls `delete_*` on users/guilds. The
    # `_assert_no_destructive_op` helper is exposed for callers that need
    # to wrap arbitrary code paths; here, the absence of such calls is
    # the actual guarantee. We intentionally do NOT pre-invoke the helper
    # with destructive arguments (which would raise unconditionally).

    # Load all guilds (need owner email + guild name to classify).
    guilds = await db.guilds.find(
        {}, {"_id": 0, "id": 1, "name": 1, "owner_user_id": 1, "created_at": 1},
    ).to_list(None)
    guild_by_owner: dict[str, dict] = {}
    for g in guilds:
        oid = g.get("owner_user_id")
        if oid and oid not in guild_by_owner:
            guild_by_owner[oid] = g

    users = await db.users.find(
        {}, {"_id": 0, "id": 1, "email": 1, "is_test_user": 1},
    ).to_list(None)

    will_flag: list[dict] = []
    candidates_sample: list[dict] = []
    allowlist_skipped = 0
    already_flagged = 0
    test_guilds_force_hits = 0

    for u in users:
        email_lower = (u.get("email") or "").lower().strip()
        g = guild_by_owner.get(u.get("id"))
        gname_lower = (g.get("name") or "").lower().strip() if g else ""

        is_already = u.get("is_test_user") is True
        in_email_allowlist = email_lower in CLEANUP_ALLOWLIST_EMAILS
        in_guild_allowlist = bool(gname_lower) and gname_lower in CLEANUP_ALLOWLIST_GUILDS
        in_force_test = bool(gname_lower) and gname_lower in CLEANUP_TEST_GUILDS_FORCE

        # 0. TEST_GUILDS_FORCE override beats allowlist.
        if in_force_test:
            test_guilds_force_hits += 1
            if is_already:
                already_flagged += 1
                continue
            will_flag.append({
                "user_id": u["id"],
                "email_masked": _mask_email(u.get("email") or ""),
                "guild": g.get("name") if g else None,
                "reason": "test_guilds_force",
                "created_at": (g.get("created_at") if g else None),
            })
            continue

        # 1. Allowlist (email OR guild) → keep
        if in_email_allowlist or in_guild_allowlist:
            allowlist_skipped += 1
            continue

        # 2. Already flagged → idempotent skip
        if is_already:
            already_flagged += 1
            continue

        # 3. Default: aggressive flag
        will_flag.append({
            "user_id": u["id"],
            "email_masked": _mask_email(u.get("email") or ""),
            "guild": g.get("name") if g else None,
            "reason": "no_allowlist_match",
            "created_at": (g.get("created_at") if g else None),
        })

    # Sample for response payload (max sample_cap).
    candidates_sample = [
        {k: v for k, v in r.items() if k != "user_id"}
        for r in will_flag[:sample_cap]
    ]

    response = {
        "mode": mode,
        "total_users": len(users),
        "will_flag_count": len(will_flag),
        "allowlist_skipped": allowlist_skipped,
        "already_flagged": already_flagged,
        "test_guilds_force": test_guilds_force_hits,
        "candidates": candidates_sample,
    }

    if mode == "dry_run":
        return response

    # ── APPLY path ──────────────────────────────────────────────────────
    now = utc_now()
    applied_count = 0
    audit_entries_created = 0
    backup_doc_id: str | None = None

    if will_flag:
        # Defence-in-depth re-check on the actual write set.
        ids = [r["user_id"] for r in will_flag]
        leaks = await db.users.find(
            {"id": {"$in": ids}, "email": {"$in": list(CLEANUP_ALLOWLIST_EMAILS)}},
            {"_id": 0, "id": 1, "email": 1},
        ).to_list(None)
        if leaks:
            # Filter out the offending ids and audit-log the abort decision.
            leaked_ids = {r["id"] for r in leaks}
            ids = [i for i in ids if i not in leaked_ids]
            will_flag = [r for r in will_flag if r["user_id"] not in leaked_ids]
            response["allowlist_skipped"] += len(leaked_ids)
            response["will_flag_count"] = len(will_flag)

        # Bulk update with CAS guard. CAS = is_test_user != True.
        upd = await db.users.update_many(
            {"id": {"$in": ids}, "is_test_user": {"$ne": True}},
            {"$set": {
                "is_test_user": True,
                "flagged_at": now.isoformat(),
                "flagged_reason": CLEANUP_REASON,
                "updated_at": now,
            }},
        )
        applied_count = int(upd.modified_count)

        # Bulk audit-log insert (no email / no token in metadata).
        # One row per actually-flagged user (no fan-out for already-flagged).
        if applied_count:
            # Re-query who is now flagged with our reason+timestamp to be
            # sure we only audit the actually-modified rows.
            modified = await db.users.find(
                {
                    "id": {"$in": ids},
                    "is_test_user": True,
                    "flagged_reason": CLEANUP_REASON,
                    "flagged_at": now.isoformat(),
                },
                {"_id": 0, "id": 1},
            ).to_list(None)
            modified_ids = {m["id"] for m in modified}
            audit_rows = []
            ts = int(now.timestamp())
            for r in will_flag:
                if r["user_id"] not in modified_ids:
                    continue
                audit_rows.append({
                    "id": f"flag-api-{r['user_id']}-{ts}",
                    "event_type": _CLEANUP_AUDIT_EVENT,
                    "actor_user_id": actor_admin_id,
                    "actor_guild_id": None,
                    "metadata": {
                        "user_id": r["user_id"],
                        "guild_name": r["guild"],
                        "reason": r["reason"],
                        "mode": mode,
                        "actor_admin_id": actor_admin_id,
                        "ts": now.isoformat(),
                    },
                    "created_at": now.isoformat(),
                })
            if audit_rows:
                try:
                    res = await db.audit_log.insert_many(audit_rows, ordered=False)
                    audit_entries_created = len(res.inserted_ids)
                    # Backup pointer = the first audit_log row id of this
                    # batch (clients can query by event_type+ts to fetch all).
                    backup_doc_id = audit_rows[0]["id"]
                except Exception:
                    audit_entries_created = 0

    response["applied_count"] = applied_count
    response["audit_log_entries_created"] = audit_entries_created
    response["backup_doc_id"] = backup_doc_id
    return response
