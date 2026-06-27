"""Phase 16 — Server Chronicle (public activity feed).

Read-only digest derived from the existing `audit_log`. Designed to give
the game an "online feel" without exposing sensitive data.

Privacy rules (CRITICAL — enforced here, NOT at the audit-log layer):
- ❌ NEVER expose email, user_id, _id, refresh/access tokens.
- ✅ Expose `guild_name` snapshot only (resolved from audit_log.actor_guild_id).
- ❌ Drop rows where the actor guild's owner is a test user (`users.is_test_user=True`).
- ❌ Drop rows where the guild name starts with `Test` (case-insensitive) or
  matches the `@orbus.test` test-pattern at the owner level.
- ❌ Drop rows where event_type is not in the public allowlist.
- ❌ Drop rows older than 7 days (UX freshness cap).

Whitelist of public event_types:
  - market_listing_created
  - market_purchase_completed
  - item_crafted          (only Uncommon+ rarity)
  - loot_awarded          (only Uncommon+ rarity)
  - streak_reward_claimed (only tier 7 — milestone)
  - weekly_quest_claimed
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("orbus.chronicle")

PUBLIC_EVENTS = frozenset({
    "market_listing_created",
    "market_purchase_completed",
    "item_crafted",
    "loot_awarded",
    "streak_reward_claimed",
    "weekly_quest_claimed",
})

# Event types that only surface if the item rarity is Uncommon+.
RARITY_GATED = frozenset({"item_crafted", "loot_awarded"})
RARITY_ALLOW = frozenset({"Uncommon", "Rare", "Epic", "Legendary"})

# Streak: only D7 (the cycle milestone) is interesting public news.
STREAK_PUBLIC_TIERS = frozenset({7})

_TEST_GUILD_NAME_RE = re.compile(r"^test", re.IGNORECASE)
# Defensive secondary filter: matches the auto-generated guild names left
# behind by older backend test runs (e.g. "G 7becbd44", "G_p15_abc123").
_TEST_GUILD_PATTERN_RE = re.compile(
    r"^(g[_\s][0-9a-f]{6,}|testguild|tg_|p\d+_[0-9a-f]+)",
    re.IGNORECASE,
)
_LOOKBACK_DAYS = 7


def _is_public_event(row: dict) -> bool:
    et = row.get("event_type")
    if et not in PUBLIC_EVENTS:
        return False
    md = row.get("metadata") or {}
    if et == "streak_reward_claimed":
        tier = int(md.get("tier", 0) or 0)
        return tier in STREAK_PUBLIC_TIERS
    return True


async def _enrich_guild_names(db, guild_ids: list[str]) -> dict[str, dict]:
    """Resolve {guild_id: {name, owner_user_id}}. Empty rows allowed."""
    if not guild_ids:
        return {}
    rows = await db.guilds.find(
        {"id": {"$in": list(set(guild_ids))}},
        {"_id": 0, "id": 1, "name": 1, "owner_user_id": 1},
    ).to_list(500)
    return {r["id"]: {"name": r.get("name", ""), "owner_user_id": r.get("owner_user_id")} for r in rows}


async def _test_user_ids(db, owner_user_ids: list[str]) -> set[str]:
    """Return the subset of owner_user_ids that should be treated as test
    accounts. We consider an owner a test account if EITHER:
      - `users.is_test_user=True`, OR
      - email matches the test-domain regex `@orbus.test$` /
        `(^|.+)test@` / `@.+\.test$` (defensive: catches unflagged users
        from older imports).
    """
    if not owner_user_ids:
        return set()
    rows = await db.users.find(
        {
            "id": {"$in": list(set(owner_user_ids))},
            "$or": [
                {"is_test_user": True},
                {"email": {"$regex": r"@orbus\.test$", "$options": "i"}},
                {"email": {"$regex": r"@.+\.test$", "$options": "i"}},
                {"email": {"$regex": r"^test@|.+test@", "$options": "i"}},
                {"email": {"$regex": r"@test\.", "$options": "i"}},
            ],
        },
        {"_id": 0, "id": 1},
    ).to_list(500)
    return {r["id"] for r in rows}


async def _enrich_item_rarity(db, item_ids: list[str]) -> dict[str, str]:
    if not item_ids:
        return {}
    rows = await db.items.find(
        {"id": {"$in": list(set(item_ids))}},
        {"_id": 0, "id": 1, "rarity": 1, "display_name_it": 1, "display_name_en": 1, "name": 1},
    ).to_list(500)
    return {r["id"]: r for r in rows}


def _localized_item_name(item: dict, lang: str) -> str:
    if lang == "en":
        return item.get("display_name_en") or item.get("name") or ""
    return item.get("display_name_it") or item.get("name") or ""


def _format_event(row: dict, guild_name: str, item: dict | None, lang: str) -> dict:
    et = row["event_type"]
    md = row.get("metadata") or {}
    item_name = _localized_item_name(item, lang) if item else None
    qty = int(row.get("quantity") or 0)
    if et == "market_listing_created":
        kind = "market_listed"
        text_it = f"{guild_name} ha messo in vendita {item_name or '?'} ×{qty}"
        text_en = f"{guild_name} listed {item_name or '?'} ×{qty} on the market"
    elif et == "market_purchase_completed":
        kind = "market_bought"
        text_it = f"{guild_name} ha acquistato {item_name or '?'} ×{qty} al mercato"
        text_en = f"{guild_name} bought {item_name or '?'} ×{qty} on the market"
    elif et == "item_crafted":
        kind = "crafted"
        text_it = f"{guild_name} ha creato {item_name or '?'}"
        text_en = f"{guild_name} crafted {item_name or '?'}"
    elif et == "loot_awarded":
        kind = "loot"
        text_it = f"{guild_name} ha trovato {item_name or '?'}"
        text_en = f"{guild_name} found {item_name or '?'}"
    elif et == "streak_reward_claimed":
        kind = "streak_milestone"
        tier = int(md.get("tier", 0))
        text_it = f"{guild_name} ha raggiunto un traguardo streak (Giorno {tier})"
        text_en = f"{guild_name} reached a streak milestone (Day {tier})"
    elif et == "weekly_quest_claimed":
        kind = "weekly_done"
        slug = md.get("slug", "")
        text_it = f"{guild_name} ha completato una missione settimanale ({slug})"
        text_en = f"{guild_name} completed a weekly quest ({slug})"
    else:  # defensive (already filtered)
        return None  # type: ignore[return-value]
    return {
        "id": row.get("id"),
        "kind": kind,
        "guild_name": guild_name,
        "item_name": item_name,
        "text": text_it if lang != "en" else text_en,
        "created_at": row.get("created_at"),
    }


async def list_chronicle(
    db, *, limit: int = 20, lang: str = "it"
) -> dict:
    """Return at most `limit` (cap 50) public events from the last 7 days,
    sanitized and i18n-formatted."""
    limit = max(1, min(int(limit or 20), 50))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)).isoformat()
    # Over-fetch to allow for post-filter loss (test guilds / rarity gating).
    raw = await db.audit_log.find(
        {
            "event_type": {"$in": list(PUBLIC_EVENTS)},
            "created_at": {"$gte": cutoff},
            "actor_guild_id": {"$ne": None},
        },
        {"_id": 0},
    ).sort("created_at", -1).limit(limit * 4).to_list(limit * 4)

    if not raw:
        return {"events": []}

    # Enrich guilds + flag test owners.
    guild_ids = [r["actor_guild_id"] for r in raw if r.get("actor_guild_id")]
    guild_map = await _enrich_guild_names(db, guild_ids)
    test_owner_ids = await _test_user_ids(
        db,
        [g["owner_user_id"] for g in guild_map.values() if g.get("owner_user_id")],
    )
    # Enrich item rarity (and localized name) for rarity-gated events.
    item_ids = [r["item_template_id"] for r in raw if r.get("item_template_id")]
    item_map = await _enrich_item_rarity(db, item_ids)

    out: list[dict] = []
    for row in raw:
        if not _is_public_event(row):
            continue
        g = guild_map.get(row.get("actor_guild_id"))
        if not g:
            continue
        gname = g.get("name", "")
        if not gname:
            continue
        if _TEST_GUILD_NAME_RE.match(gname) or _TEST_GUILD_PATTERN_RE.match(gname):
            continue
        if g.get("owner_user_id") in test_owner_ids:
            continue
        item = item_map.get(row.get("item_template_id"))
        if row["event_type"] in RARITY_GATED:
            if not item or (item.get("rarity") not in RARITY_ALLOW):
                continue
        formatted = _format_event(row, gname, item, lang)
        if not formatted:
            continue
        out.append(formatted)
        if len(out) >= limit:
            break
    return {"events": out}


__all__ = ["list_chronicle", "PUBLIC_EVENTS"]
