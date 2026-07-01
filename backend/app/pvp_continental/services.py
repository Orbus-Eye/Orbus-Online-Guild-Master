"""ROUND 16.3 Phase 7A — PvP Continental services.

Business logic for challenge creation / response / decline / listings.
Ownership + gate + cooldown + bracket + team-availability checks.
Snapshots stats at commit time (no change in corsa).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException

from app.audit.log import write_audit
from app.pvp_continental.resolver import (
    ELO_DEFAULT,
    _get_or_init_stats,
)


logger = logging.getLogger("orbus.pvp_continental")


GUILD_LEVEL_GATE: int = 8
MAX_ACTIVE_CHALLENGES: int = 3
COOLDOWN_HOURS: int = 12
COOLDOWN_REFUND_HOURS_ON_DECLINE: int = 6
RESPONSE_WINDOW_HOURS: int = 24
RESOLVE_WINDOW_HOURS_FROM_CHALLENGE: int = 48
RESOLVE_WINDOW_HOURS_FROM_RESPOND: int = 24

BRACKET_ELO_RANGE: int = 200
BRACKET_LEVEL_RANGE: int = 3
DEFAULT_TEAM_SIZE: int = 5


# ── Helpers ─────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


async def _guild_of_user(db, user_id: str) -> dict:
    g = await db.guilds.find_one({"owner_user_id": user_id}, {"_id": 0})
    if not g:
        raise HTTPException(404, detail={"code": "pvp.no_guild"})
    return g


async def _continent_of_guild(db, guild_id: str) -> str | None:
    p = await db.guild_world_presence.find_one(
        {"guild_id": guild_id, "status": "active"},
        {"_id": 0, "continent_slug": 1},
    )
    return p.get("continent_slug") if p else None


def _require_level_gate(guild: dict) -> None:
    if int(guild.get("level") or 0) < GUILD_LEVEL_GATE:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "pvp.level_gate",
                "required_level": GUILD_LEVEL_GATE,
                "current_level": int(guild.get("level") or 0),
                "user_message": (
                    f"Il PvP Continentale richiede la gilda al Livello "
                    f"{GUILD_LEVEL_GATE}."
                ),
            },
        )


async def _adventurers_owned(
    db, guild_id: str, adv_ids: list[str],
) -> list[dict]:
    docs = await db.adventurers.find(
        {"id": {"$in": adv_ids}, "guild_id": guild_id},
        {"_id": 0},
    ).to_list(len(adv_ids))
    if len(docs) != len(adv_ids):
        raise HTTPException(
            status_code=400,
            detail={"code": "pvp.team_ownership",
                    "user_message":
                    "Uno o più avventurieri non appartengono alla tua gilda."},
        )
    for a in docs:
        if a.get("is_available") is False:
            raise HTTPException(
                status_code=409,
                detail={"code": "pvp.team_unavailable",
                        "adventurer_id": a["id"],
                        "user_message":
                        f"{a.get('name','Un avventuriero')} non è disponibile."},
            )
    return docs


def _snapshot_adventurer(adv: dict, guild_id: str) -> dict:
    return {
        "id": adv["id"],
        "guild_id": guild_id,
        "name": adv.get("name", "?"),
        "class_slug": adv.get("class_slug"),
        "specialization_slug": adv.get("specialization_slug"),
        "level_snapshot": int(adv.get("level") or 1),
        "strength_snapshot": int(adv.get("strength") or 0),
        "agility_snapshot": int(adv.get("agility") or 0),
        "intellect_snapshot": int(adv.get("intellect") or 0),
        "endurance_snapshot": int(adv.get("endurance") or 0),
        "faith_snapshot": int(adv.get("faith") or 0),
        "role_snapshot": adv.get("role"),
    }


async def _reserve_team(db, battle_id: str, adv_ids: list[str]) -> None:
    """Atomic CAS reserve — marks all 5 as unavailable in one shot.

    If any doc has moved to `is_available=false` between the ownership
    check and now, `modified_count` will be < len(adv_ids) and we abort
    (raising 409). Callers should not proceed past this function.
    """
    now = _now()
    res = await db.adventurers.update_many(
        {"id": {"$in": adv_ids}, "is_available": True},
        {"$set": {"is_available": False,
                   "on_pvp_battle_id": battle_id,
                   "updated_at": now}},
    )
    if res.modified_count != len(adv_ids):
        # Best-effort revert of whatever we did lock (idempotent)
        await db.adventurers.update_many(
            {"id": {"$in": adv_ids}, "on_pvp_battle_id": battle_id},
            {"$set": {"is_available": True,
                       "on_pvp_battle_id": None,
                       "updated_at": now}},
        )
        raise HTTPException(
            status_code=409,
            detail={"code": "pvp.team_race",
                    "user_message":
                    "Uno degli avventurieri è stato impegnato altrove."},
        )


async def _check_cooldown(
    db, challenger_id: str, defender_id: str,
) -> None:
    now_iso = _iso(_now())
    doc = await db.pvp_challenge_cooldowns.find_one(
        {"challenger_id": challenger_id, "defender_id": defender_id},
        {"_id": 0, "cooldown_ends_at": 1},
    )
    if doc and doc.get("cooldown_ends_at") and doc["cooldown_ends_at"] > now_iso:
        raise HTTPException(
            status_code=409,
            detail={"code": "pvp.cooldown",
                    "cooldown_ends_at": doc["cooldown_ends_at"],
                    "user_message":
                    "Devi attendere prima di sfidare di nuovo questa gilda."},
        )


async def _upsert_cooldown(
    db, challenger_id: str, defender_id: str, hours: int,
) -> None:
    ends = _iso(_now() + timedelta(hours=hours))
    await db.pvp_challenge_cooldowns.update_one(
        {"challenger_id": challenger_id, "defender_id": defender_id},
        {"$set": {"cooldown_ends_at": ends,
                   "challenger_id": challenger_id,
                   "defender_id": defender_id}},
        upsert=True,
    )


async def _shrink_cooldown(
    db, challenger_id: str, defender_id: str, hours: int,
) -> None:
    """Reduce a live cooldown by `hours`. If it becomes past, delete."""
    doc = await db.pvp_challenge_cooldowns.find_one(
        {"challenger_id": challenger_id, "defender_id": defender_id},
        {"_id": 0, "cooldown_ends_at": 1},
    )
    if not doc or not doc.get("cooldown_ends_at"):
        return
    try:
        current = datetime.fromisoformat(doc["cooldown_ends_at"])
    except Exception:
        return
    new = current - timedelta(hours=hours)
    if new <= _now():
        await db.pvp_challenge_cooldowns.delete_one(
            {"challenger_id": challenger_id, "defender_id": defender_id},
        )
    else:
        await db.pvp_challenge_cooldowns.update_one(
            {"challenger_id": challenger_id, "defender_id": defender_id},
            {"$set": {"cooldown_ends_at": _iso(new)}},
        )


# ── Public services ─────────────────────────────────────────────────


async def list_opponents(db, guild: dict) -> list[dict]:
    """Return opponents in the same continent within the bracket."""
    _require_level_gate(guild)
    continent = await _continent_of_guild(db, guild["id"])
    if not continent:
        raise HTTPException(
            status_code=409,
            detail={"code": "pvp.no_continent",
                    "user_message":
                    "Devi essere presente in un continente per accedere al PvP."},
        )
    my_stats = await _get_or_init_stats(db, guild["id"])
    my_elo = int(my_stats.get("elo") or ELO_DEFAULT)
    my_level = int(guild.get("level") or 1)

    peers = await db.guild_world_presence.find(
        {"continent_slug": continent, "status": "active",
         "guild_id": {"$ne": guild["id"]}},
        {"_id": 0, "guild_id": 1},
    ).to_list(500)
    gids = [p["guild_id"] for p in peers]
    if not gids:
        return []

    gdocs = await db.guilds.find(
        {"id": {"$in": gids}},
        {"_id": 0, "id": 1, "name": 1, "level": 1},
    ).to_list(500)

    stat_docs = await db.guild_pvp_stats.find(
        {"guild_id": {"$in": gids}}, {"_id": 0},
    ).to_list(500)
    stat_map = {s["guild_id"]: s for s in stat_docs}

    now_iso = _iso(_now())
    cds = await db.pvp_challenge_cooldowns.find(
        {"challenger_id": guild["id"], "defender_id": {"$in": gids},
         "cooldown_ends_at": {"$gt": now_iso}},
        {"_id": 0, "defender_id": 1},
    ).to_list(500)
    cd_set = {c["defender_id"] for c in cds}

    out: list[dict] = []
    for g in gdocs:
        gid = g["id"]
        if gid in cd_set:
            continue
        s = stat_map.get(gid, {})
        elo = int(s.get("elo") or ELO_DEFAULT)
        lvl = int(g.get("level") or 1)
        if lvl < GUILD_LEVEL_GATE:
            continue
        elo_ok = abs(elo - my_elo) <= BRACKET_ELO_RANGE
        lvl_ok = abs(lvl - my_level) <= BRACKET_LEVEL_RANGE
        if not (elo_ok or lvl_ok):
            continue
        out.append({
            "guild_id": gid,
            "guild_name": g.get("name", "?"),
            "elo": elo,
            "guild_level": lvl,
            "wins": int(s.get("wins") or 0),
            "losses": int(s.get("losses") or 0),
            "draws": int(s.get("draws") or 0),
        })
    out.sort(key=lambda r: (abs(r["elo"] - my_elo), r["guild_name"]))
    return out


async def create_challenge(
    db, *, challenger_guild: dict, defender_guild_id: str,
    adventurer_ids: list[str],
) -> dict:
    _require_level_gate(challenger_guild)

    if defender_guild_id == challenger_guild["id"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "pvp.self_challenge",
                    "user_message": "Non puoi sfidare la tua gilda."},
        )
    defender = await db.guilds.find_one(
        {"id": defender_guild_id}, {"_id": 0},
    )
    if not defender:
        raise HTTPException(
            status_code=404,
            detail={"code": "pvp.defender_not_found"},
        )
    _require_level_gate(defender)

    # Continent check
    my_c = await _continent_of_guild(db, challenger_guild["id"])
    def_c = await _continent_of_guild(db, defender_guild_id)
    if not my_c or my_c != def_c:
        raise HTTPException(
            status_code=409,
            detail={"code": "pvp.cross_continent",
                    "user_message":
                    "Puoi sfidare solo gilde del tuo continente."},
        )

    # Bracket check
    my_stats = await _get_or_init_stats(db, challenger_guild["id"])
    def_stats = await _get_or_init_stats(db, defender_guild_id)
    my_elo = int(my_stats["elo"])
    def_elo = int(def_stats["elo"])
    my_level = int(challenger_guild.get("level") or 1)
    def_level = int(defender.get("level") or 1)
    if (abs(my_elo - def_elo) > BRACKET_ELO_RANGE
            and abs(my_level - def_level) > BRACKET_LEVEL_RANGE):
        raise HTTPException(
            status_code=409,
            detail={"code": "pvp.out_of_bracket",
                    "user_message":
                    "La gilda selezionata è fuori dal tuo bracket."},
        )

    # Cooldown check
    await _check_cooldown(db, challenger_guild["id"], defender_guild_id)

    # Max active challenges (challenger side only)
    active = int(my_stats.get("current_active_challenges") or 0)
    if active >= MAX_ACTIVE_CHALLENGES:
        raise HTTPException(
            status_code=409,
            detail={"code": "pvp.max_active_challenges",
                    "current": active, "max": MAX_ACTIVE_CHALLENGES,
                    "user_message":
                    "Hai già 3 sfide attive. Attendi che si risolvano."},
        )

    # Team ownership + availability + snapshot
    if len(set(adventurer_ids)) != DEFAULT_TEAM_SIZE:
        raise HTTPException(
            status_code=400,
            detail={"code": "pvp.team_size",
                    "user_message":
                    "Servono esattamente 5 avventurieri unici."},
        )
    advs = await _adventurers_owned(db, challenger_guild["id"], adventurer_ids)

    battle_id = str(uuid.uuid4())
    challenge_created_at = _now()
    response_deadline = challenge_created_at + timedelta(
        hours=RESPONSE_WINDOW_HOURS,
    )
    resolves_at_initial = challenge_created_at + timedelta(
        hours=RESOLVE_WINDOW_HOURS_FROM_CHALLENGE,
    )

    await _reserve_team(db, battle_id, adventurer_ids)

    snapshot = [_snapshot_adventurer(a, challenger_guild["id"]) for a in advs]

    doc = {
        "id": battle_id,
        "challenger_guild_id": challenger_guild["id"],
        "defender_guild_id": defender_guild_id,
        "continent_slug": my_c,
        "challenger_elo_snapshot": my_elo,
        "defender_elo_snapshot": def_elo,
        "challenger_team": snapshot,
        "defender_team": [],
        "challenger_status": "committed",
        "defender_status": "pending",
        "status": "pending_response",
        "challenge_created_at": _iso(challenge_created_at),
        "response_deadline": _iso(response_deadline),
        "resolves_at": _iso(resolves_at_initial),
        "resolved_at": None,
        "resolution_started_at": None,
        "outcome": None,
        "battle_log": [],
        "mvp_adventurer_id": None,
        "audit_log_ids": [],
    }
    await db.pvp_battles.insert_one(doc)
    # Bump challenger active count
    await db.guild_pvp_stats.update_one(
        {"guild_id": challenger_guild["id"]},
        {"$inc": {"current_active_challenges": 1}},
        upsert=True,
    )
    await _upsert_cooldown(
        db, challenger_guild["id"], defender_guild_id, COOLDOWN_HOURS,
    )
    await write_audit(
        db, event_type="PVP_CHALLENGE_CREATED",
        actor_user_id=None, actor_guild_id=challenger_guild["id"],
        source="pvp_continental.services",
        metadata={"battle_id": battle_id,
                  "defender_guild_id": defender_guild_id,
                  "continent_slug": my_c},
    )
    return {"battle": _serialize(doc)}


async def respond_to_challenge(
    db, *, defender_guild: dict, battle_id: str,
    adventurer_ids: list[str],
) -> dict:
    battle = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(404, detail={"code": "pvp.battle_not_found"})
    if battle["defender_guild_id"] != defender_guild["id"]:
        raise HTTPException(403, detail={"code": "pvp.not_defender"})
    if battle["status"] != "pending_response":
        raise HTTPException(
            409, detail={"code": "pvp.wrong_status",
                          "current": battle["status"]},
        )
    now = _now()
    now_iso = _iso(now)
    if battle.get("response_deadline") and battle["response_deadline"] <= now_iso:
        raise HTTPException(
            409, detail={"code": "pvp.deadline_expired"},
        )
    if len(set(adventurer_ids)) != DEFAULT_TEAM_SIZE:
        raise HTTPException(
            400, detail={"code": "pvp.team_size"},
        )
    advs = await _adventurers_owned(
        db, defender_guild["id"], adventurer_ids,
    )
    await _reserve_team(db, battle_id, adventurer_ids)
    snapshot = [_snapshot_adventurer(a, defender_guild["id"]) for a in advs]
    resolves_at = now + timedelta(hours=RESOLVE_WINDOW_HOURS_FROM_RESPOND)
    cas = await db.pvp_battles.update_one(
        {"id": battle_id, "status": "pending_response",
         "defender_status": "pending"},
        {"$set": {
            "defender_team": snapshot,
            "defender_status": "committed",
            "status": "resolving",
            "resolves_at": _iso(resolves_at),
        }},
    )
    if cas.modified_count == 0:
        # revert team reservation
        await db.adventurers.update_many(
            {"id": {"$in": adventurer_ids},
             "on_pvp_battle_id": battle_id},
            {"$set": {"is_available": True,
                       "on_pvp_battle_id": None,
                       "updated_at": now}},
        )
        raise HTTPException(
            409, detail={"code": "pvp.race_lost"},
        )
    await write_audit(
        db, event_type="PVP_CHALLENGE_ACCEPTED",
        actor_user_id=None, actor_guild_id=defender_guild["id"],
        source="pvp_continental.services",
        metadata={"battle_id": battle_id},
    )
    updated = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    return {"battle": _serialize(updated)}


async def decline_challenge(
    db, *, defender_guild: dict, battle_id: str,
) -> dict:
    battle = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(404, detail={"code": "pvp.battle_not_found"})
    if battle["defender_guild_id"] != defender_guild["id"]:
        raise HTTPException(403, detail={"code": "pvp.not_defender"})
    if battle["status"] != "pending_response":
        raise HTTPException(
            409, detail={"code": "pvp.wrong_status",
                          "current": battle["status"]},
        )
    now = _now()
    now_iso = _iso(now)
    if battle.get("response_deadline") and battle["response_deadline"] <= now_iso:
        raise HTTPException(
            409, detail={"code": "pvp.deadline_expired"},
        )
    cas = await db.pvp_battles.update_one(
        {"id": battle_id, "status": "pending_response"},
        {"$set": {
            "status": "declined",
            "defender_status": "declined",
            "resolved_at": now_iso,
        }},
    )
    if cas.modified_count == 0:
        raise HTTPException(409, detail={"code": "pvp.race_lost"})
    # Release challenger team (defender never committed)
    await db.adventurers.update_many(
        {"on_pvp_battle_id": battle_id},
        {"$set": {"is_available": True,
                   "on_pvp_battle_id": None,
                   "updated_at": now}},
    )
    # Refund cooldown 6h to challenger
    await _shrink_cooldown(
        db, battle["challenger_guild_id"], defender_guild["id"],
        COOLDOWN_REFUND_HOURS_ON_DECLINE,
    )
    # Decrement active challenges counter for challenger
    await db.guild_pvp_stats.update_one(
        {"guild_id": battle["challenger_guild_id"]},
        {"$inc": {"current_active_challenges": -1}},
    )
    await write_audit(
        db, event_type="PVP_CHALLENGE_DECLINED",
        actor_user_id=None, actor_guild_id=defender_guild["id"],
        source="pvp_continental.services",
        metadata={"battle_id": battle_id},
    )
    updated = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    return {"battle": _serialize(updated)}


def _serialize(battle: dict) -> dict:
    """Public projection (removes internal-only fields)."""
    out = dict(battle)
    out.pop("audit_log_ids", None)
    return out


async def list_battles_mine(db, guild: dict) -> dict:
    """Active battles + last 20 resolved. Triggers on-visit fallback."""
    from app.pvp_continental.resolver import auto_resolve_stuck_battles_for_guild
    try:
        await auto_resolve_stuck_battles_for_guild(db, guild["id"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("on_visit fallback failed guild=%s: %s",
                        guild["id"], exc)

    q_active = {
        "$or": [{"challenger_guild_id": guild["id"]},
                {"defender_guild_id": guild["id"]}],
        "status": {"$in": ["pending_response", "resolving"]},
    }
    active = await db.pvp_battles.find(q_active, {"_id": 0}).sort(
        "challenge_created_at", -1,
    ).to_list(50)

    q_history = {
        "$or": [{"challenger_guild_id": guild["id"]},
                {"defender_guild_id": guild["id"]}],
        "status": {"$in": ["resolved", "expired", "declined"]},
    }
    history = await db.pvp_battles.find(q_history, {"_id": 0}).sort(
        "resolved_at", -1,
    ).to_list(20)

    return {
        "active": [_serialize(b) for b in active],
        "history": [_serialize(b) for b in history],
    }


async def get_battle_detail(
    db, *, guild: dict, battle_id: str,
) -> dict:
    battle = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(404, detail={"code": "pvp.battle_not_found"})
    if guild["id"] not in (
        battle["challenger_guild_id"], battle["defender_guild_id"],
    ):
        raise HTTPException(403, detail={"code": "pvp.not_participant"})
    return {"battle": _serialize(battle)}
