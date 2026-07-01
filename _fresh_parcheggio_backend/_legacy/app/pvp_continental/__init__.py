"""ROUND 16.3 Phase 7A — PvP continentale (asynchronous 1v1).

Cosmetic-only V0: no gold/XP/loot from PvP. Elo tracked for future 7B
leaderboard. Deterministic resolution seeded by battle_id.

Rules:
- Guild level gate ≥ 8
- Max 3 active challenges per guild
- 12h cooldown between challenges to same guild (anti-harassment)
- Bracket: ±200 Elo OR ±3 guild level
- Team snapshot at challenge time (no changes in-flight)
- New-player defensive buff +20% for guilds with <10 completed expeditions
- Applier Arfus filtered: only combat_damage/healing/defense/counter/
  team_morale/iron_will apply in PvP
- On-visit fallback for expired battles (no scheduler)
"""
from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.pvp_continental")

router = APIRouter(prefix="/api/pvp", tags=["pvp"])
admin_router = APIRouter(prefix="/api/admin/pvp", tags=["admin", "pvp"])

MIN_GUILD_LEVEL = 8
MAX_ACTIVE_CHALLENGES = 3
CHALLENGE_COOLDOWN_HOURS = 12
RESPOND_DEADLINE_HOURS = 24
AUTO_RESOLVE_HOURS = 48
DEFAULT_ELO = 1200
ELO_K_FACTOR = 32
ELO_MIN = 800
ELO_MAX = 2400
NEW_PLAYER_EXPEDITION_THRESHOLD = 10
NEW_PLAYER_BUFF = 0.20  # +20%
BRACKET_ELO_DELTA = 200
BRACKET_LEVEL_DELTA = 3
TEAM_SIZE = 5

# Arfus categories that ARE applied in PvP.
PVP_ARFUS_CATEGORIES = {
    "combat_damage", "combat_healing", "combat_defense",
    "counter_effectiveness", "team_morale", "iron_will",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _clamp_elo(v: int) -> int:
    return max(ELO_MIN, min(ELO_MAX, int(v)))


async def ensure_indexes():
    try:
        await db.pvp_battles.create_index(
            [("challenger_guild_id", 1), ("status", 1)])
        await db.pvp_battles.create_index(
            [("defender_guild_id", 1), ("status", 1)])
        await db.pvp_battles.create_index([("status", 1), ("resolves_at", 1)])
        await db.guild_pvp_stats.create_index("guild_id", unique=True)
        await db.pvp_challenge_cooldowns.create_index(
            [("challenger_id", 1), ("defender_id", 1)], unique=True)
    except Exception as exc:
        logger.debug("pvp indexes: %s", exc)


async def _emit_audit(event_type: str, actor_id: Optional[str],
                       guild_id: Optional[str], target_id: Optional[str],
                       metadata: dict) -> None:
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": event_type, "actor_id": actor_id,
            "actor_guild_id": guild_id, "target_id": target_id,
            "metadata": metadata,
            "created_at": _iso(_now()),
        })
    except Exception as exc:
        logger.warning("audit %s: %s", event_type, exc)


async def _get_stats(guild_id: str) -> dict:
    doc = await db.guild_pvp_stats.find_one(
        {"guild_id": guild_id}, {"_id": 0})
    if doc:
        return doc
    doc = {"guild_id": guild_id, "elo": DEFAULT_ELO,
             "wins": 0, "losses": 0, "draws": 0,
             "current_active_challenges": 0,
             "created_at": _iso(_now()), "updated_at": _iso(_now())}
    await db.guild_pvp_stats.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def _guild_continent(guild_id: str) -> Optional[str]:
    p = await db.guild_world_presence.find_one(
        {"guild_id": guild_id, "status": "active"},
        {"_id": 0, "continent_slug": 1})
    return p.get("continent_slug") if p else None


async def _completed_expedition_count(guild_id: str) -> int:
    return await db.expeditions.count_documents(
        {"guild_id": guild_id, "status": "completed"})


async def _pvp_arfus_bonus(guild_id: str, category: str) -> int:
    """Apply Arfus bonus only if category is PvP-relevant."""
    if category not in PVP_ARFUS_CATEGORIES:
        return 0
    try:
        from app.arfus_forge import bonus_pct
        return await bonus_pct(guild_id, category)
    except Exception:
        return 0


async def _team_snapshot(guild_id: str, adventurer_ids: list) -> list:
    if len(adventurer_ids) != TEAM_SIZE:
        raise HTTPException(400, f"team_must_be_{TEAM_SIZE}_adventurers")
    docs = await db.adventurers.find(
        {"guild_id": guild_id, "id": {"$in": adventurer_ids}},
        {"_id": 0}).to_list(TEAM_SIZE + 1)
    if len(docs) != TEAM_SIZE:
        raise HTTPException(400, "invalid_adventurer_ids")
    snap = []
    for a in docs:
        snap.append({"id": a["id"], "name": a.get("name"),
                      "class": a.get("class_slug") or a.get("class"),
                      "level": int(a.get("level", 1)),
                      "strength": int(a.get("strength", 5)),
                      "agility": int(a.get("agility", 5)),
                      "intellect": int(a.get("intellect", 5)),
                      "endurance": int(a.get("endurance", 5)),
                      "faith": int(a.get("faith", 5))})
    return snap


def _team_base_power(team: list) -> int:
    return sum(a["strength"] + a["agility"] + a["intellect"] +
                 a["endurance"] + a["faith"] + a["level"] * 3
                 for a in team)


async def _apply_pvp_bonuses(guild_id: str, base: int) -> tuple:
    """Return (adjusted_power, arfus_bonus_total_pct)."""
    total_pct = 0
    for cat in PVP_ARFUS_CATEGORIES:
        total_pct += await _pvp_arfus_bonus(guild_id, cat)
    adjusted = int(base * (1 + total_pct / 100.0))
    return adjusted, total_pct


def _elo_update(winner_elo: int, loser_elo: int, is_draw: bool = False) -> tuple:
    expected = 1.0 / (1.0 + 10 ** ((loser_elo - winner_elo) / 400.0))
    score = 0.5 if is_draw else 1.0
    delta = ELO_K_FACTOR * (score - expected)
    return _clamp_elo(round(winner_elo + delta)), _clamp_elo(round(loser_elo - delta))


def _generate_battle_log(battle_id: str, ch_guild_name: str,
                          def_guild_name: str, ch_team: list,
                          def_team: list, outcome: str) -> list:
    rng = random.Random(battle_id + "_narrative")
    log = [
        f"⚔️ {ch_guild_name} sfida {def_guild_name} in duello!",
    ]
    verbs_attack = ["carica", "attacca", "sferra un colpo su",
                     "lancia un incantesimo contro"]
    verbs_defense = ["para", "resiste all'attacco di", "controbatte"]
    verbs_heal = ["cura il team di", "risana",
                    "innalza il morale di"]
    for step in range(3):
        actor = rng.choice(ch_team + def_team)
        actor_guild = (ch_guild_name if actor in ch_team else def_guild_name)
        target_guild = (def_guild_name if actor in ch_team else ch_guild_name)
        action_kind = rng.choice(["attack", "defense", "heal"])
        if action_kind == "attack":
            v = rng.choice(verbs_attack)
            log.append(f"[{actor_guild}] {actor.get('name','Combattente')} "
                        f"{v} le linee di {target_guild}.")
        elif action_kind == "defense":
            v = rng.choice(verbs_defense)
            log.append(f"[{target_guild}] {v} {actor_guild} con determinazione.")
        else:
            v = rng.choice(verbs_heal)
            log.append(f"[{actor_guild}] {actor.get('name','Chierico')} "
                        f"{v} i propri alleati.")
    if outcome == "challenger_win":
        log.append(f"🏆 Vittoria per {ch_guild_name}!")
    elif outcome == "defender_win":
        log.append(f"🏆 Vittoria per {def_guild_name}!")
    elif outcome == "defender_forfeit":
        log.append(f"🏳️ {def_guild_name} non risponde in tempo. "
                    f"Vittoria automatica per {ch_guild_name}.")
    else:
        log.append("🤝 La battaglia si conclude in pareggio.")
    return log


def _mvp_from_team(team: list, battle_id: str) -> Optional[str]:
    if not team:
        return None
    rng = random.Random(battle_id + "_mvp")
    weighted = sorted(team,
                        key=lambda a: (a["strength"] + a["agility"] +
                                        a["intellect"] + a["endurance"] +
                                        a["faith"] + a["level"] * 3),
                        reverse=True)
    top3 = weighted[:3]
    return rng.choice(top3)["id"]


async def _resolve_battle(battle: dict) -> dict:
    """CAS-guarded resolver. Idempotent."""
    now_iso = _iso(_now())
    r = await db.pvp_battles.find_one_and_update(
        {"id": battle["id"],
         "status": {"$in": ["pending_response", "resolving"]},
         "resolution_started_at": None},
        {"$set": {"resolution_started_at": now_iso, "status": "resolving"}},
        return_document=True)
    if not r:
        cur = await db.pvp_battles.find_one({"id": battle["id"]}, {"_id": 0})
        return cur or battle
    battle = r
    ch_guild = await db.guilds.find_one(
        {"id": battle["challenger_guild_id"]},
        {"_id": 0, "name": 1})
    def_guild = await db.guilds.find_one(
        {"id": battle["defender_guild_id"]},
        {"_id": 0, "name": 1})
    ch_name = (ch_guild or {}).get("name", "Challenger")
    def_name = (def_guild or {}).get("name", "Defender")

    # Defender forfeit?
    if battle["defender_status"] == "pending":
        # Deadline passed → auto-forfeit path
        battle["defender_status"] = "timeout_defaulted"
        outcome = "defender_forfeit"
        ch_score = 100  # symbolic
        def_score = 0
    else:
        # Determine outcome via deterministic RNG
        rng = random.Random(battle["id"])
        ch_base = _team_base_power(battle["challenger_team"])
        def_base = _team_base_power(battle["defender_team"] or [])
        ch_adj, ch_bonus = await _apply_pvp_bonuses(
            battle["challenger_guild_id"], ch_base)
        def_adj, def_bonus = await _apply_pvp_bonuses(
            battle["defender_guild_id"], def_base)
        # New-player defensive buff on defender
        def_exp_count = await _completed_expedition_count(
            battle["defender_guild_id"])
        newplayer_buff = 0
        if def_exp_count < NEW_PLAYER_EXPEDITION_THRESHOLD:
            def_adj = int(def_adj * (1 + NEW_PLAYER_BUFF))
            newplayer_buff = int(NEW_PLAYER_BUFF * 100)
        ch_score = int(ch_adj * rng.uniform(0.9, 1.1))
        def_score = int(def_adj * rng.uniform(0.9, 1.1))
        if ch_score > def_score:
            outcome = "challenger_win"
        elif def_score > ch_score:
            outcome = "defender_win"
        else:
            outcome = "draw"

    # Elo update
    ch_stats = await _get_stats(battle["challenger_guild_id"])
    def_stats = await _get_stats(battle["defender_guild_id"])
    ch_elo_new, def_elo_new = ch_stats["elo"], def_stats["elo"]
    if outcome == "challenger_win" or outcome == "defender_forfeit":
        ch_elo_new, def_elo_new = _elo_update(ch_stats["elo"], def_stats["elo"])
        await db.guild_pvp_stats.update_one(
            {"guild_id": battle["challenger_guild_id"]},
            {"$set": {"elo": ch_elo_new, "updated_at": now_iso},
             "$inc": {"wins": 1, "current_active_challenges": -1}})
        await db.guild_pvp_stats.update_one(
            {"guild_id": battle["defender_guild_id"]},
            {"$set": {"elo": def_elo_new, "updated_at": now_iso},
             "$inc": {"losses": 1}})
    elif outcome == "defender_win":
        def_elo_new, ch_elo_new = _elo_update(def_stats["elo"], ch_stats["elo"])
        await db.guild_pvp_stats.update_one(
            {"guild_id": battle["defender_guild_id"]},
            {"$set": {"elo": def_elo_new, "updated_at": now_iso},
             "$inc": {"wins": 1}})
        await db.guild_pvp_stats.update_one(
            {"guild_id": battle["challenger_guild_id"]},
            {"$set": {"elo": ch_elo_new, "updated_at": now_iso},
             "$inc": {"losses": 1, "current_active_challenges": -1}})
    else:  # draw
        await db.guild_pvp_stats.update_one(
            {"guild_id": battle["challenger_guild_id"]},
            {"$set": {"updated_at": now_iso},
             "$inc": {"draws": 1, "current_active_challenges": -1}})
        await db.guild_pvp_stats.update_one(
            {"guild_id": battle["defender_guild_id"]},
            {"$set": {"updated_at": now_iso},
             "$inc": {"draws": 1}})

    # Battle log + MVP (based on winner team)
    if outcome == "defender_win":
        mvp = _mvp_from_team(battle["defender_team"] or [], battle["id"])
    else:
        mvp = _mvp_from_team(battle["challenger_team"], battle["id"])

    battle_log = _generate_battle_log(battle["id"], ch_name, def_name,
                                        battle["challenger_team"],
                                        battle["defender_team"] or [],
                                        outcome)

    r = await db.pvp_battles.find_one_and_update(
        {"id": battle["id"]},
        {"$set": {"status": "resolved",
                    "outcome": outcome,
                    "resolved_at": now_iso,
                    "battle_log": battle_log,
                    "mvp_adventurer_id": mvp,
                    "defender_status": battle["defender_status"],
                    "updated_at": now_iso}},
        return_document=True)

    await _emit_audit("PVP_BATTLE_RESOLVED", None,
                       battle["challenger_guild_id"], battle["id"],
                       {"outcome": outcome,
                        "defender_guild_id": battle["defender_guild_id"],
                        "mvp_adventurer_id": mvp})
    await _emit_audit("PVP_ELO_UPDATED", None,
                       battle["challenger_guild_id"], battle["id"],
                       {"ch_elo_before": ch_stats["elo"],
                        "ch_elo_after": ch_elo_new,
                        "def_elo_before": def_stats["elo"],
                        "def_elo_after": def_elo_new})
    r.pop("_id", None) if r else None
    return r or battle


async def _resolve_expired_for_guild(guild_id: str) -> int:
    now_iso = _iso(_now())
    q = {"$or": [{"challenger_guild_id": guild_id},
                 {"defender_guild_id": guild_id}],
         "status": "pending_response",
         "resolves_at": {"$lte": now_iso}}
    cur = db.pvp_battles.find(q, {"_id": 0})
    resolved = 0
    async for b in cur:
        try:
            await _resolve_battle(b)
            resolved += 1
        except Exception as exc:
            logger.warning("resolve %s: %s", b.get("id"), exc)
    return resolved


def _battle_public(b: dict) -> dict:
    d = {k: b.get(k) for k in (
        "id", "challenger_guild_id", "defender_guild_id",
        "continent_slug", "challenger_elo_snapshot",
        "defender_elo_snapshot", "challenger_team", "defender_team",
        "challenger_status", "defender_status", "status",
        "challenge_created_at", "response_deadline", "resolves_at",
        "resolved_at", "outcome", "battle_log", "mvp_adventurer_id")}
    return d


# ── Public routes ────────────────────────────────────────────────────
@router.get("/opponents")
async def list_opponents(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    if int(guild.get("level", 1)) < MIN_GUILD_LEVEL:
        return {"access": False,
                "requirement": f"guild_level_{MIN_GUILD_LEVEL}",
                "opponents": []}
    my_cont = await _guild_continent(guild["id"])
    if not my_cont:
        return {"access": True, "opponents": [],
                "note": "no_active_continent"}
    my_stats = await _get_stats(guild["id"])
    my_level = int(guild.get("level", 1))
    # Find guilds in same continent with active presence
    cont_docs = await db.guild_world_presence.find(
        {"continent_slug": my_cont, "status": "active"},
        {"_id": 0, "guild_id": 1}).to_list(500)
    opponents = []
    for p in cont_docs:
        gid = p["guild_id"]
        if gid == guild["id"]:
            continue
        g = await db.guilds.find_one({"id": gid},
                                       {"_id": 0, "id": 1, "name": 1,
                                        "level": 1})
        if not g or int(g.get("level", 1)) < MIN_GUILD_LEVEL:
            continue
        st = await _get_stats(gid)
        elo_diff = abs(st["elo"] - my_stats["elo"])
        lvl_diff = abs(int(g.get("level", 1)) - my_level)
        if elo_diff <= BRACKET_ELO_DELTA or lvl_diff <= BRACKET_LEVEL_DELTA:
            opponents.append({"guild_id": gid,
                                "guild_name": g["name"],
                                "guild_level": g.get("level"),
                                "elo": st["elo"],
                                "wins": st["wins"],
                                "losses": st["losses"]})
    return {"access": True, "my_elo": my_stats["elo"],
            "my_wins": my_stats["wins"], "my_losses": my_stats["losses"],
            "opponents": opponents}


@router.post("/challenge/{defender_guild_id}")
async def challenge(defender_guild_id: str, body: dict,
                     user: dict = Depends(get_current_user)):
    ch_guild = await user_guild_or_404(db, user["id"])
    if int(ch_guild.get("level", 1)) < MIN_GUILD_LEVEL:
        raise HTTPException(403, f"guild_level_below_required:{MIN_GUILD_LEVEL}")
    if ch_guild["id"] == defender_guild_id:
        raise HTTPException(400, "cannot_challenge_self")
    def_guild = await db.guilds.find_one({"id": defender_guild_id},
                                           {"_id": 0, "id": 1, "name": 1,
                                            "level": 1})
    if not def_guild:
        raise HTTPException(404, "defender_not_found")
    if int(def_guild.get("level", 1)) < MIN_GUILD_LEVEL:
        raise HTTPException(400, "defender_below_min_level")
    # Cross-continent block
    my_cont = await _guild_continent(ch_guild["id"])
    dc = await _guild_continent(defender_guild_id)
    if not my_cont or not dc:
        raise HTTPException(400, "missing_continent_presence")
    if my_cont != dc:
        raise HTTPException(400,
                            f"cross_continent_block:{my_cont}!={dc}")
    # Cooldown check
    now_iso = _iso(_now())
    cd = await db.pvp_challenge_cooldowns.find_one(
        {"challenger_id": ch_guild["id"],
         "defender_id": defender_guild_id,
         "cooldown_ends_at": {"$gt": now_iso}}, {"_id": 0})
    if cd:
        raise HTTPException(409,
                            f"challenge_cooldown_active:until={cd['cooldown_ends_at']}")
    # Max 3 active
    ch_stats = await _get_stats(ch_guild["id"])
    if int(ch_stats.get("current_active_challenges", 0)) >= MAX_ACTIVE_CHALLENGES:
        raise HTTPException(409, "max_active_challenges_reached")
    # Bracket check
    def_stats = await _get_stats(defender_guild_id)
    elo_diff = abs(ch_stats["elo"] - def_stats["elo"])
    lvl_diff = abs(int(ch_guild.get("level", 1)) - int(def_guild.get("level", 1)))
    if not (elo_diff <= BRACKET_ELO_DELTA or lvl_diff <= BRACKET_LEVEL_DELTA):
        raise HTTPException(400, "out_of_bracket")
    # Team snapshot
    adv_ids = list(body.get("adventurer_ids") or [])
    ch_team = await _team_snapshot(ch_guild["id"], adv_ids)
    now = _now()
    battle = {"id": str(uuid.uuid4()),
                "challenger_guild_id": ch_guild["id"],
                "defender_guild_id": defender_guild_id,
                "continent_slug": my_cont,
                "challenger_elo_snapshot": ch_stats["elo"],
                "defender_elo_snapshot": def_stats["elo"],
                "challenger_team": ch_team,
                "defender_team": None,
                "challenger_status": "committed",
                "defender_status": "pending",
                "status": "pending_response",
                "challenge_created_at": _iso(now),
                "response_deadline":
                    _iso(now + timedelta(hours=RESPOND_DEADLINE_HOURS)),
                "resolves_at":
                    _iso(now + timedelta(hours=AUTO_RESOLVE_HOURS)),
                "resolved_at": None, "resolution_started_at": None,
                "outcome": None, "battle_log": [],
                "mvp_adventurer_id": None,
                "audit_log_ids": [],
                "created_at": _iso(now), "updated_at": _iso(now)}
    await db.pvp_battles.insert_one(battle)
    await db.guild_pvp_stats.update_one(
        {"guild_id": ch_guild["id"]},
        {"$inc": {"current_active_challenges": 1},
         "$set": {"updated_at": _iso(now)}})
    # Cooldown record (upsert)
    await db.pvp_challenge_cooldowns.update_one(
        {"challenger_id": ch_guild["id"],
         "defender_id": defender_guild_id},
        {"$set": {"cooldown_ends_at":
                    _iso(now + timedelta(hours=CHALLENGE_COOLDOWN_HOURS))}},
        upsert=True)
    await _emit_audit("PVP_CHALLENGE_CREATED", user["id"], ch_guild["id"],
                       battle["id"],
                       {"defender_guild_id": defender_guild_id,
                        "team_size": len(ch_team)})
    battle.pop("_id", None)
    return {"status": "ok", "battle": _battle_public(battle)}


@router.post("/battles/{battle_id}/respond")
async def respond(battle_id: str, body: dict,
                    user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    b = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not b:
        raise HTTPException(404, "battle_not_found")
    if b["defender_guild_id"] != guild["id"]:
        raise HTTPException(403, "not_defender")
    if b["status"] != "pending_response" or b["defender_status"] != "pending":
        raise HTTPException(409, f"invalid_status:{b['status']}")
    adv_ids = list(body.get("adventurer_ids") or [])
    def_team = await _team_snapshot(guild["id"], adv_ids)
    now = _now()
    r = await db.pvp_battles.find_one_and_update(
        {"id": battle_id, "defender_status": "pending"},
        {"$set": {"defender_team": def_team,
                    "defender_status": "committed",
                    "resolves_at": _iso(now + timedelta(minutes=1)),
                    "updated_at": _iso(now)}},
        return_document=True)
    await _emit_audit("PVP_CHALLENGE_ACCEPTED", user["id"], guild["id"],
                       battle_id,
                       {"challenger_guild_id": b["challenger_guild_id"]})
    # Immediately trigger resolve
    resolved = await _resolve_battle(r)
    return {"status": "ok", "battle": _battle_public(resolved)}


@router.post("/battles/{battle_id}/decline")
async def decline(battle_id: str, user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    b = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not b:
        raise HTTPException(404, "battle_not_found")
    if b["defender_guild_id"] != guild["id"]:
        raise HTTPException(403, "not_defender")
    if b["status"] != "pending_response":
        raise HTTPException(409, f"invalid_status:{b['status']}")
    now_iso = _iso(_now())
    r = await db.pvp_battles.find_one_and_update(
        {"id": battle_id, "status": "pending_response"},
        {"$set": {"status": "declined",
                    "defender_status": "declined",
                    "resolved_at": now_iso, "updated_at": now_iso}},
        return_document=True)
    # Refund challenger active challenge counter
    await db.guild_pvp_stats.update_one(
        {"guild_id": b["challenger_guild_id"]},
        {"$inc": {"current_active_challenges": -1},
         "$set": {"updated_at": now_iso}})
    # Reset cooldown between these two guilds so challenger can retry
    await db.pvp_challenge_cooldowns.delete_one(
        {"challenger_id": b["challenger_guild_id"],
         "defender_id": guild["id"]})
    await _emit_audit("PVP_CHALLENGE_DECLINED", user["id"], guild["id"],
                       battle_id,
                       {"challenger_guild_id": b["challenger_guild_id"]})
    r.pop("_id", None) if r else None
    return {"status": "ok", "battle": _battle_public(r) if r else None}


@router.get("/battles/mine")
async def battles_mine(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    await _resolve_expired_for_guild(guild["id"])
    active = await db.pvp_battles.find(
        {"$or": [{"challenger_guild_id": guild["id"]},
                    {"defender_guild_id": guild["id"]}],
         "status": {"$in": ["pending_response", "resolving"]}},
        {"_id": 0}).sort("challenge_created_at", -1).to_list(20)
    recent = await db.pvp_battles.find(
        {"$or": [{"challenger_guild_id": guild["id"]},
                    {"defender_guild_id": guild["id"]}],
         "status": {"$in": ["resolved", "declined"]}},
        {"_id": 0}).sort("resolved_at", -1).to_list(20)
    return {"active": [_battle_public(b) for b in active],
            "recent": [_battle_public(b) for b in recent]}


@router.get("/battles/{battle_id}")
async def battle_detail(battle_id: str,
                          user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    b = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not b:
        raise HTTPException(404, "battle_not_found")
    if guild["id"] not in (b["challenger_guild_id"], b["defender_guild_id"]):
        raise HTTPException(403, "not_battle_member")
    return {"battle": _battle_public(b)}


# ── Admin ────────────────────────────────────────────────────────────
@admin_router.get("/stats")
async def admin_stats(admin: dict = Depends(get_admin_user)):
    pipe = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    by_status = await db.pvp_battles.aggregate(pipe).to_list(10)
    elo_pipe = [{"$bucket": {"groupBy": "$elo",
                              "boundaries": [800, 1000, 1200, 1400, 1600, 1800, 2400],
                              "default": "other",
                              "output": {"count": {"$sum": 1}}}}]
    elo_dist = await db.guild_pvp_stats.aggregate(elo_pipe).to_list(20)
    return {"battles_by_status": by_status, "elo_distribution": elo_dist}


import os as _os


@admin_router.post("/dev/force-resolve/{battle_id}")
async def admin_force_resolve(battle_id: str,
                                admin: dict = Depends(get_admin_user)):
    if (_os.environ.get("APP_ENV") or "development").lower() == "production":
        raise HTTPException(403, "disabled_in_production")
    b = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not b:
        raise HTTPException(404, "battle_not_found")
    if b["status"] not in ("pending_response", "resolving"):
        return {"status": "already_resolved", "battle": _battle_public(b)}
    past = _iso(_now() - timedelta(seconds=1))
    await db.pvp_battles.update_one(
        {"id": battle_id}, {"$set": {"resolves_at": past}})
    b["resolves_at"] = past
    resolved = await _resolve_battle(b)
    return {"status": "resolved", "battle": _battle_public(resolved)}


__all__ = ["router", "admin_router", "ensure_indexes",
             "_resolve_battle", "_resolve_expired_for_guild",
             "_elo_update", "_apply_pvp_bonuses",
             "_generate_battle_log", "_mvp_from_team",
             "PVP_ARFUS_CATEGORIES", "MIN_GUILD_LEVEL",
             "MAX_ACTIVE_CHALLENGES", "DEFAULT_ELO", "ELO_MIN", "ELO_MAX",
             "NEW_PLAYER_BUFF"]
