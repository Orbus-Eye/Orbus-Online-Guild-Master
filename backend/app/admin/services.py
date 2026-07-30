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

from app.shared.rarity import CANONICAL_RARITIES


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


VALID_ROLES = ("Tank", "DPS", "Healer")
VALID_AFFECTED_STAT = ("strength", "agility", "intellect", "endurance", "faith", "xp_gain")
VALID_ITEM_TYPES = (
    "weapon", "armor", "legs", "helmet", "accessory",
    "back", "ring", "trinket", "consumable",
)
ITEM_TYPE_TO_SLOT = {
    "weapon": "weapon",
    "armor": "chest",
    "legs": "legs",
    "helmet": "head",
    "accessory": "accessory",
    "back": "back",
    "ring": "ring",
    "trinket": "trinket",
}
VALID_RARITIES = CANONICAL_RARITIES


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
    if "item_type" in payload:
        slot_type = ITEM_TYPE_TO_SLOT.get(base["item_type"])
        if slot_type:
            base["slot_type"] = slot_type
        else:
            base.pop("slot_type", None)
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


def _classify_user_for_flag(
    user: dict,
    guild: dict | None,
) -> tuple[str | None, str]:
    """ROUND 6B FASE C — per-user classification, extracted from
    `flag_test_users_aggressive`.

    Returns (action, reason) where:
      - action in {"flag", "skip_allowlist", "skip_already"}
      - reason is the audit-log reason string (only meaningful when
        action == "flag")
    """
    email_lower = (user.get("email") or "").lower().strip()
    gname_lower = (guild.get("name") or "").lower().strip() if guild else ""

    is_already = user.get("is_test_user") is True
    in_email_allowlist = email_lower in CLEANUP_ALLOWLIST_EMAILS
    in_guild_allowlist = bool(gname_lower) and gname_lower in CLEANUP_ALLOWLIST_GUILDS
    in_force_test = bool(gname_lower) and gname_lower in CLEANUP_TEST_GUILDS_FORCE

    # 0. TEST_GUILDS_FORCE override beats allowlist.
    if in_force_test:
        if is_already:
            return ("skip_already", "")
        return ("flag", "test_guilds_force")
    # 1. Allowlist (email OR guild) → keep
    if in_email_allowlist or in_guild_allowlist:
        return ("skip_allowlist", "")
    # 2. Already flagged → idempotent skip
    if is_already:
        return ("skip_already", "")
    # 3. Default: aggressive flag
    return ("flag", "no_allowlist_match")


async def _build_flag_plan(db) -> dict:
    """ROUND 6B FASE C — read-only phase: scan users+guilds and build the
    flag-or-skip plan. Pure (modulo DB reads) — no writes happen here.

    Returns a dict with keys: will_flag (list), allowlist_skipped (int),
    already_flagged (int), test_guilds_force (int), total_users (int).
    """
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
    allowlist_skipped = 0
    already_flagged = 0
    test_guilds_force_hits = 0

    for u in users:
        g = guild_by_owner.get(u.get("id"))
        action, reason = _classify_user_for_flag(u, g)
        if action == "flag":
            if reason == "test_guilds_force":
                test_guilds_force_hits += 1
            will_flag.append({
                "user_id": u["id"],
                "email_masked": _mask_email(u.get("email") or ""),
                "guild": g.get("name") if g else None,
                "reason": reason,
                "created_at": (g.get("created_at") if g else None),
            })
        elif action == "skip_allowlist":
            allowlist_skipped += 1
        elif action == "skip_already":
            already_flagged += 1

    return {
        "will_flag": will_flag,
        "allowlist_skipped": allowlist_skipped,
        "already_flagged": already_flagged,
        "test_guilds_force": test_guilds_force_hits,
        "total_users": len(users),
    }


async def _filter_allowlist_leaks(
    db,
    *,
    will_flag: list[dict],
) -> tuple[list[dict], int]:
    """ROUND 6B FASE C — defence-in-depth re-check on the actual write set.

    Returns (filtered_will_flag, leaked_count). Anything whose email is in
    CLEANUP_ALLOWLIST_EMAILS at apply-time is removed from the write set.
    """
    if not will_flag:
        return ([], 0)
    ids = [r["user_id"] for r in will_flag]
    leaks = await db.users.find(
        {"id": {"$in": ids}, "email": {"$in": list(CLEANUP_ALLOWLIST_EMAILS)}},
        {"_id": 0, "id": 1, "email": 1},
    ).to_list(None)
    if not leaks:
        return (will_flag, 0)
    leaked_ids = {r["id"] for r in leaks}
    filtered = [r for r in will_flag if r["user_id"] not in leaked_ids]
    return (filtered, len(leaked_ids))


async def _emit_flag_audit_batch(
    db,
    *,
    will_flag: list[dict],
    ids: list[str],
    now: datetime,
    mode: str,
    actor_admin_id: str | None,
) -> tuple[int, str | None]:
    """ROUND 6B FASE C — re-query the actually-modified rows and write one
    audit_log entry per flagged user. Best-effort: on insert failure, both
    return values are (0, None).
    """
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
    ts = int(now.timestamp())
    audit_rows = [
        {
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
        }
        for r in will_flag
        if r["user_id"] in modified_ids
    ]
    if not audit_rows:
        return (0, None)
    try:
        res = await db.audit_log.insert_many(audit_rows, ordered=False)
        return (len(res.inserted_ids), audit_rows[0]["id"])
    except Exception:
        return (0, None)


async def flag_test_users_aggressive(
    db,
    *,
    mode: str,
    actor_admin_id: str | None,
    sample_cap: int = 50,
) -> dict:
    """Aggressive bulk flag with CAS guard + audit. Read-only when
    `mode='dry_run'`. The double-gate (confirm_apply) is enforced at the
    router layer.

    ROUND 6B FASE C — body simplified (CC≈5, was CC≈39) by splitting into
    `_build_flag_plan`, `_filter_allowlist_leaks` and `_emit_flag_audit_batch`.
    """
    # Defence: this service NEVER calls `delete_*` on users/guilds. The
    # `_assert_no_destructive_op` helper is exposed for callers that need
    # to wrap arbitrary code paths; here, the absence of such calls is
    # the actual guarantee. We intentionally do NOT pre-invoke the helper
    # with destructive arguments (which would raise unconditionally).

    plan = await _build_flag_plan(db)
    will_flag: list[dict] = plan["will_flag"]

    response: dict = {
        "mode": mode,
        "total_users": plan["total_users"],
        "will_flag_count": len(will_flag),
        "allowlist_skipped": plan["allowlist_skipped"],
        "already_flagged": plan["already_flagged"],
        "test_guilds_force": plan["test_guilds_force"],
        "candidates": [
            {k: v for k, v in r.items() if k != "user_id"}
            for r in will_flag[:sample_cap]
        ],
    }

    if mode == "dry_run":
        return response

    # ── APPLY path ──────────────────────────────────────────────────────
    now = utc_now()
    applied_count = 0
    audit_entries_created = 0
    backup_doc_id: str | None = None

    if will_flag:
        will_flag, leaked_count = await _filter_allowlist_leaks(
            db, will_flag=will_flag,
        )
        if leaked_count:
            response["allowlist_skipped"] += leaked_count
            response["will_flag_count"] = len(will_flag)

        ids = [r["user_id"] for r in will_flag]
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

        if applied_count:
            audit_entries_created, backup_doc_id = await _emit_flag_audit_batch(
                db,
                will_flag=will_flag,
                ids=ids,
                now=now,
                mode=mode,
                actor_admin_id=actor_admin_id,
            )

    response["applied_count"] = applied_count
    response["audit_log_entries_created"] = audit_entries_created
    response["backup_doc_id"] = backup_doc_id
    return response
