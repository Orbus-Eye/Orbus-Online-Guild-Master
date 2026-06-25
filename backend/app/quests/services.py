"""Phase 14 — Daily Quests service.

Three fixed quests per day, reset at UTC midnight, reward is gold only.

Data model (nested on `guilds`):
  daily_quest_state = {
    window_start_utc: "YYYY-MM-DD",  # date string, UTC
    quests: {
      expedition_complete: {progress: int, claimed: bool},
      recruit:             {progress: int, claimed: bool},
      equip:               {progress: int, claimed: bool},
    }
  }

Concurrency:
  * progress is bumped via `$inc` (atomic on Mongo)
  * claim uses find_one_and_update CAS gating on
    `progress >= threshold AND claimed == false` so the second concurrent
    claim sees no-match and gets 409
  * lazy reset on read AND on increment: if the stored window predates
    today (UTC), a single conditional update rewrites the doc.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument


# Quest catalog (Phase 14 MVP, gold-only rewards).
QUEST_DEFINITIONS: dict[str, dict] = {
    "expedition_complete": {"threshold": 1, "reward_gold": 10},
    "recruit": {"threshold": 1, "reward_gold": 5},
    "equip": {"threshold": 1, "reward_gold": 5},
}
QUEST_IDS = tuple(QUEST_DEFINITIONS.keys())


def _today_utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _empty_state() -> dict:
    return {
        "window_start_utc": _today_utc_date(),
        "quests": {
            qid: {"progress": 0, "claimed": False} for qid in QUEST_IDS
        },
    }


async def _ensure_state_fresh(db, guild_id: str) -> dict:
    """Lazy reset: if no state OR window predates today UTC, reset.
    Returns the up-to-date state dict (state is also persisted in guild doc).
    """
    today = _today_utc_date()
    guild = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "daily_quest_state": 1}
    )
    state = (guild or {}).get("daily_quest_state")
    if not state or state.get("window_start_utc") != today:
        fresh = _empty_state()
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"daily_quest_state": fresh}}
        )
        return fresh
    # Defensive: backfill any missing quest key (in case catalog grew)
    quests = dict(state.get("quests", {}))
    changed = False
    for qid in QUEST_IDS:
        if qid not in quests:
            quests[qid] = {"progress": 0, "claimed": False}
            changed = True
    if changed:
        state["quests"] = quests
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": {"daily_quest_state": state}}
        )
    return state


async def get_today_quests(db, guild_id: str) -> dict:
    """Return the public payload consumed by the frontend card."""
    state = await _ensure_state_fresh(db, guild_id)
    quests = []
    for qid, defn in QUEST_DEFINITIONS.items():
        s = state["quests"].get(qid, {"progress": 0, "claimed": False})
        progress = int(s.get("progress", 0))
        claimed = bool(s.get("claimed", False))
        completed = progress >= defn["threshold"]
        quests.append({
            "id": qid,
            "threshold": defn["threshold"],
            "progress": progress,
            "reward_gold": defn["reward_gold"],
            "claimed": claimed,
            "completed": completed,
            "can_claim": (completed and not claimed),
        })
    # Next reset = tomorrow 00:00 UTC
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    tomorrow = tomorrow + timedelta(days=1)
    return {
        "window_start_utc": state["window_start_utc"],
        "next_reset_at": tomorrow.isoformat(),
        "quests": quests,
    }


async def increment_quest_progress(db, guild_id: str, quest_id: str, amount: int = 1) -> None:
    """Best-effort atomic progress bump.

    Called from expedition completion, recruit, equip lifecycle. Never raises
    — quest tracking failures must NOT abort the parent business operation.
    """
    if quest_id not in QUEST_DEFINITIONS:
        return
    try:
        today = _today_utc_date()
        # Try to bump if state is for today; if not, reset+bump in two steps.
        res = await db.guilds.update_one(
            {"id": guild_id, "daily_quest_state.window_start_utc": today},
            {"$inc": {f"daily_quest_state.quests.{quest_id}.progress": amount}},
        )
        if res.matched_count == 0:
            # Stale or missing window — ensure + retry once.
            await _ensure_state_fresh(db, guild_id)
            await db.guilds.update_one(
                {"id": guild_id, "daily_quest_state.window_start_utc": today},
                {"$inc": {f"daily_quest_state.quests.{quest_id}.progress": amount}},
            )
    except Exception:
        # Swallow — quest tracking is non-critical
        pass


async def claim_quest(db, guild_id: str, quest_id: str) -> dict:
    """Atomic claim: requires progress >= threshold AND not yet claimed.
    Returns updated quest snapshot + new guild gold."""
    if quest_id not in QUEST_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Unknown quest")
    # Ensure the daily window is current first
    await _ensure_state_fresh(db, guild_id)
    today = _today_utc_date()
    defn = QUEST_DEFINITIONS[quest_id]
    threshold = defn["threshold"]
    reward = defn["reward_gold"]

    # Atomic CAS: only flip claimed=true if progress is enough AND not yet claimed
    updated = await db.guilds.find_one_and_update(
        {
            "id": guild_id,
            "daily_quest_state.window_start_utc": today,
            f"daily_quest_state.quests.{quest_id}.claimed": False,
            f"daily_quest_state.quests.{quest_id}.progress": {"$gte": threshold},
        },
        {
            "$set": {f"daily_quest_state.quests.{quest_id}.claimed": True},
            "$inc": {"gold": reward},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        # Distinguish "not completed yet" vs "already claimed"
        cur = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "daily_quest_state": 1})
        s = (cur or {}).get("daily_quest_state", {}).get("quests", {}).get(quest_id, {})
        if bool(s.get("claimed", False)):
            raise HTTPException(status_code=409, detail="Quest already claimed today")
        raise HTTPException(status_code=422, detail="Quest not completed yet")

    quest_state = updated["daily_quest_state"]["quests"][quest_id]
    return {
        "quest": {
            "id": quest_id,
            "threshold": threshold,
            "progress": int(quest_state.get("progress", 0)),
            "reward_gold": reward,
            "claimed": True,
            "completed": True,
            "can_claim": False,
        },
        "guild_gold": int(updated.get("gold", 0)),
        "reward_gold_granted": reward,
    }


__all__ = [
    "QUEST_DEFINITIONS",
    "QUEST_IDS",
    "get_today_quests",
    "increment_quest_progress",
    "claim_quest",
]
