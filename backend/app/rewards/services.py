"""ROUND 12.C — Seasonal cosmetic rewards.

Hard constraint: ONLY cosmetic reward types are allowed.
The whitelist `COSMETIC_REWARD_TYPES` is enforced at insert + grant time;
any reward referencing power/economy/competitive fields raises 400.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from app.audit.log import write_audit

logger = logging.getLogger("orbus.rewards")

COSMETIC_REWARD_TYPES = frozenset({
    "title", "badge", "frame", "banner", "league_icon",
    "hall_of_fame", "chat_flair", "cosmetic",
})

# Field-level guard: any reward whose name/description hints at competitive
# value (gold, xp, power, item, boost…) is hard-blocked.
_FORBIDDEN_FIELDS = frozenset({
    "gold", "xp", "exp", "power", "item", "stat", "boost",
    "ticket", "premium", "currency", "buff",
})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_cosmetic(payload: dict) -> None:
    rt = payload.get("reward_type")
    if rt not in COSMETIC_REWARD_TYPES:
        raise HTTPException(400, {
            "code": "reward.non_cosmetic_forbidden",
            "user_message": f"Tipo reward '{rt}' non è cosmetico. Whitelist: {sorted(COSMETIC_REWARD_TYPES)}.",
        })
    if not payload.get("cosmetic_only", True):
        raise HTTPException(400, {
            "code": "reward.cosmetic_only_required",
            "user_message": "cosmetic_only deve essere True.",
        })
    # Forbidden field sweep
    lowered = " ".join([
        str(payload.get("name_it") or ""),
        str(payload.get("name_en") or ""),
        str(payload.get("description_it") or ""),
    ]).lower()
    for kw in _FORBIDDEN_FIELDS:
        if kw in lowered:
            raise HTTPException(400, {
                "code": "reward.non_cosmetic_forbidden",
                "user_message": f"Il reward contiene un termine non cosmetico vietato: '{kw}'.",
            })


async def ensure_reward_indexes(db) -> None:
    try:
        await db.season_rewards.create_index("reward_id", unique=True)
        await db.season_rewards.create_index([("season_id", 1), ("reward_type", 1)])
        await db.granted_rewards.create_index(
            [("season_id", 1), ("guild_id", 1), ("reward_id", 1)], unique=True,
        )
        await db.granted_rewards.create_index([("season_id", 1), ("guild_id", 1)])
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_reward_indexes failed: %s", exc)


async def list_rewards(db, season_id: str) -> list[dict]:
    rows = await db.season_rewards.find(
        {"season_id": season_id}, {"_id": 0},
    ).sort("created_at", 1).to_list(200)
    return rows


async def insert_reward(db, payload: dict, *, actor_user_id: Optional[str] = None) -> dict:
    _validate_cosmetic(payload)
    doc = {
        "reward_id": payload.get("reward_id") or str(uuid.uuid4()),
        "season_id": payload["season_id"],
        "reward_type": payload["reward_type"],
        "name_it": payload["name_it"],
        "name_en": payload.get("name_en") or payload["name_it"],
        "description_it": payload.get("description_it", ""),
        "description_en": payload.get("description_en", payload.get("description_it", "")),
        "criteria": payload.get("criteria") or {},
        "cosmetic_only": True,
        "is_test": bool(payload.get("is_test", False)),
        "created_at": _now(),
    }
    await db.season_rewards.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


async def grant_rewards(
    db, *, season_id: str, actor_user_id: str, reason: str, dry_run: bool = False,
) -> dict:
    """Grant all defined rewards to every eligible participant.

    Criteria are documented per reward; for the preseason the rules are
    intentionally permissive (every active participant gets the
    "Veterano della Preseason" title). Future seasons will lock criteria
    to placement/league/wins thresholds.

    Idempotent: replays no-op thanks to the unique index on
    (season_id, guild_id, reward_id) and pre-check on `granted_rewards`.
    """
    season = await db.seasons.find_one({"season_id": season_id})
    if not season:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    rewards = await list_rewards(db, season_id)
    if not rewards:
        return {"ok": True, "granted": 0, "skipped": 0, "dry_run": dry_run,
                "reason": "no_rewards_defined"}
    parts = await db.season_participations.find(
        {"season_id": season_id, "is_test": {"$ne": True}}, {"_id": 0},
    ).to_list(10_000)

    granted, skipped = 0, 0
    for p in parts:
        for r in rewards:
            existing = await db.granted_rewards.find_one({
                "season_id": season_id, "guild_id": p["guild_id"], "reward_id": r["reward_id"],
            })
            if existing:
                skipped += 1
                continue
            if dry_run:
                granted += 1
                continue
            try:
                await db.granted_rewards.insert_one({
                    "season_id": season_id,
                    "guild_id": p["guild_id"],
                    "guild_public_id": p["guild_public_id"],
                    "reward_id": r["reward_id"],
                    "reward_type": r["reward_type"],
                    "name_it": r["name_it"],
                    "granted_at": _now(),
                    "granted_by": actor_user_id,
                    "reason": reason,
                })
                granted += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("grant_rewards skip dup: %s", exc)
                skipped += 1

    if not dry_run:
        await write_audit(
            db, event_type="season_rewards_granted", actor_user_id=actor_user_id,
            source="rewards.grant",
            metadata={"season_id": season_id, "granted": granted, "skipped": skipped, "reason": reason},
        )
    return {"ok": True, "granted": granted, "skipped": skipped, "dry_run": dry_run,
            "season_id": season_id, "rewards_count": len(rewards),
            "participants_count": len(parts)}


__all__ = [
    "COSMETIC_REWARD_TYPES",
    "ensure_reward_indexes",
    "list_rewards", "insert_reward", "grant_rewards",
]
