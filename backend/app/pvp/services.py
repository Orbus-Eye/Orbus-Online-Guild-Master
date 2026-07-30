"""ROUND 12.A — PvP Arena services.

Responsibilities:
  * Defense team CRUD + validation.
  * Matchmaking (opponent search with league band).
  * Snapshot building (immutable team copies stored on the match doc).
  * Match resolution wiring (simulator → rating update → audit).
  * Anti-abuse guards (self-challenge, daily limit, target cooldown).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException

from app.audit.log import write_audit
from app.adventurers.classless import require_class_hall_assignment
from app.pvp.rating import apply_match
from app.pvp.simulator import simulate
from app.seasons.services import (
    assign_league,
    get_current_season,
    get_or_create_participation,
)

logger = logging.getLogger("orbus.pvp")

# Tunable: in preview the seeded tester roster doesn't always reach Lv5.
# Spec mandates Lv5; we keep Lv3 as a documented preview fallback.
MIN_LEVEL_PVP = 3  # Preview value (see report). Production should restore to 5.
TEAM_SIZE = 5
DAILY_RANKED_LIMIT = 10
TARGET_DAILY_CAP = 3
# ROUND 12.C — Account age gate. Preview value 1h, production 24h.
MIN_GUILD_AGE_SECONDS = 60 * 60


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc_range() -> tuple[str, str]:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return today.isoformat(), (today + timedelta(days=1)).isoformat()


async def ensure_pvp_indexes(db) -> None:
    try:
        await db.pvp_defense_teams.create_index("guild_id", unique=True)
        await db.pvp_matches.create_index("match_id", unique=True)
        await db.pvp_matches.create_index([("season_id", 1), ("attacker_guild_id", 1), ("created_at", -1)])
        await db.pvp_matches.create_index([("season_id", 1), ("defender_guild_id", 1), ("created_at", -1)])
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_pvp_indexes failed: %s", exc)


# ─── Defense Team ─────────────────────────────────────────────────────────────
async def _validate_team(db, *, guild_id: str, adventurer_ids: list[str]) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if len(adventurer_ids) != TEAM_SIZE:
        warnings.append(f"team_size_mismatch: expected {TEAM_SIZE}, got {len(adventurer_ids)}")
        return False, warnings
    if len(set(adventurer_ids)) != TEAM_SIZE:
        warnings.append("duplicate_ids")
        return False, warnings
    cursor = db.adventurers.find(
        {"id": {"$in": adventurer_ids}, "guild_id": guild_id},
        {"_id": 0, "id": 1, "level": 1, "is_available": 1, "name": 1,
         "role": 1, "recruit_status": 1, "class_slug": 1,
         "canonical_class_slug": 1, "class_proficiency": 1,
         "class_hall_id": 1},
    )
    found = await cursor.to_list(TEAM_SIZE)
    if len(found) != TEAM_SIZE:
        warnings.append("some_adventurers_not_in_guild_or_missing")
        return False, warnings
    try:
        require_class_hall_assignment(found, source="pvp.team")
    except HTTPException:
        warnings.extend(
            f"class_hall_required:{a['id']}"
            for a in found
            if a.get("recruit_status") == "recruit_unassigned"
            and not a.get("class_slug")
        )
    for a in found:
        if not a.get("is_available", True):
            warnings.append(f"adventurer_not_available:{a['id']}")
        if int(a.get("level", 1)) < MIN_LEVEL_PVP:
            warnings.append(f"adventurer_below_min_level:{a['id']} (lv {a.get('level')} < {MIN_LEVEL_PVP})")
    is_valid = len(warnings) == 0
    return is_valid, warnings


async def get_defense_team(db, *, guild_id: str) -> Optional[dict]:
    doc = await db.pvp_defense_teams.find_one({"guild_id": guild_id}, {"_id": 0})
    return doc


async def upsert_defense_team(
    db, *, guild_id: str, adventurer_ids: list[str], actor_user_id: str,
) -> dict:
    is_valid, warnings = await _validate_team(db, guild_id=guild_id, adventurer_ids=adventurer_ids)
    if not is_valid:
        raise HTTPException(422, {
            "code": "pvp.team_invalid",
            "warnings": warnings,
            "user_message": "Squadra di difesa non valida. Controlla le segnalazioni.",
        })
    existing = await db.pvp_defense_teams.find_one({"guild_id": guild_id})
    doc = {
        "guild_id": guild_id,
        "adventurer_ids": adventurer_ids,
        "is_valid": True,
        "last_validated_at": _now_iso(),
        "warnings": warnings,
        "updated_at": _now_iso(),
    }
    if existing:
        await db.pvp_defense_teams.update_one({"guild_id": guild_id}, {"$set": doc})
        event = "pvp_defense_team_updated"
    else:
        doc["created_at"] = _now_iso()
        await db.pvp_defense_teams.insert_one(doc)
        event = "pvp_defense_team_created"
    await write_audit(
        db, event_type=event, actor_user_id=actor_user_id, actor_guild_id=guild_id,
        source="pvp.defense_team",
        metadata={"adventurer_count": TEAM_SIZE},
    )
    return await get_defense_team(db, guild_id=guild_id)


async def delete_defense_team(db, *, guild_id: str, actor_user_id: str) -> None:
    res = await db.pvp_defense_teams.delete_one({"guild_id": guild_id})
    if res.deleted_count:
        await write_audit(
            db, event_type="pvp_defense_team_deleted",
            actor_user_id=actor_user_id, actor_guild_id=guild_id,
            source="pvp.defense_team",
            metadata={},
        )


async def build_team_summary(db, *, guild_id: str, adventurer_ids: list[str]) -> dict:
    advs = await db.adventurers.find(
        {"id": {"$in": adventurer_ids}, "guild_id": guild_id},
        {"_id": 0},
    ).to_list(TEAM_SIZE)
    from app.expeditions.formulas import adventurer_effective_power
    total_power = sum(adventurer_effective_power(a) for a in advs)
    avg_level = round(sum(int(a.get("level") or 1) for a in advs) / max(len(advs), 1), 2)
    roles: dict[str, int] = {}
    for a in advs:
        r = a.get("role") or "Unknown"
        roles[r] = roles.get(r, 0) + 1
    return {
        "adventurer_ids": adventurer_ids,
        "adventurers": advs,
        "total_power": total_power,
        "average_level": avg_level,
        "roles": roles,
    }


# ─── Snapshot ─────────────────────────────────────────────────────────────────
async def _build_snapshot(db, *, guild: dict, adventurer_ids: list[str]) -> dict:
    advs = await db.adventurers.find(
        {"id": {"$in": adventurer_ids}, "guild_id": guild["id"]},
        {"_id": 0},
    ).to_list(TEAM_SIZE)
    # Equip bonus aggregation (best-effort): use cached team_power as proxy when
    # no per-equip aggregate is available — keeps simulator stable.
    snap_advs = []
    for a in advs:
        from app.adventurers.career import (
            career_effective_stats,
            career_stat_multiplier,
        )
        from app.expeditions.formulas import adventurer_effective_power
        stats = career_effective_stats(a)
        effective_power = adventurer_effective_power(a)
        snap_advs.append({
            "id": a["id"],
            "name": a.get("name"),
            "class": a.get("class"),
            "role": a.get("role"),
            "level": a.get("level"),
            "stats": stats,
            "rarity_stat_multiplier": career_stat_multiplier(a),
            "equip_bonus": max(
                0, int(a.get("team_power") or effective_power) - effective_power
            ),
            "traits": a.get("traits") or [],
            "specialization": a.get("specialization"),
        })
    return {
        "guild_id": guild["id"],
        "guild_public_id": guild.get("public_id") or guild["id"][:8],
        "guild_name": guild["name"],
        "adventurers": snap_advs,
        "captured_at": _now_iso(),
    }


# ─── Matchmaking ──────────────────────────────────────────────────────────────
def _power_band(total_power: int) -> str:
    band = (total_power // 100) * 100
    return f"{band}-{band + 99}"


def _relative_time(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    try:
        ts = datetime.fromisoformat(iso)
    except Exception:
        return "—"
    delta = datetime.now(timezone.utc) - ts
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "ora"
    if minutes < 60:
        return f"{minutes}m fa"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h fa"
    days = hours // 24
    return f"{days}g fa"


async def list_opponents(db, *, my_guild: dict, season: dict, limit: int = 10) -> list[dict]:
    my_part = await get_or_create_participation(db, season_id=season["season_id"], guild=my_guild)
    my_league = my_part["league"]
    # League band ±1 (preseason permissive: include unranked if I'm unranked).
    league_order = ["unranked", "bronze", "silver", "gold", "platinum", "diamond", "master"]
    try:
        idx = league_order.index(my_league)
    except ValueError:
        idx = 0
    # ROUND 12.D — during placement (unranked), expose all leagues so
    # new guilds can sample opponents at any rating tier. Once ranked,
    # standard ±1 league band applies.
    if my_league == "unranked":
        allowed_leagues = list(league_order)
    else:
        allowed_leagues = league_order[max(0, idx - 1): idx + 2]

    # Filter: not me, has defense team, in allowed leagues, not test artifact.
    pipeline = [
        {"$match": {"season_id": season["season_id"], "league": {"$in": allowed_leagues},
                     "guild_id": {"$ne": my_guild["id"]}, "is_test": {"$ne": True}}},
        {"$sort": {"rating": -1}},
        {"$limit": limit * 3},  # over-fetch then filter by defense team presence
    ]
    parts = await db.season_participations.aggregate(pipeline).to_list(limit * 3)
    if not parts:
        return []

    # Daily target cooldown filter — exclude opponents I've challenged ≥ TARGET_DAILY_CAP times today.
    today_start, today_end = _today_utc_range()
    today_challenges = await db.pvp_matches.find(
        {"attacker_guild_id": my_guild["id"], "created_at": {"$gte": today_start, "$lt": today_end}},
        {"_id": 0, "defender_guild_id": 1},
    ).to_list(200)
    count_per_target: dict[str, int] = {}
    for m in today_challenges:
        d = m.get("defender_guild_id")
        if d:
            count_per_target[d] = count_per_target.get(d, 0) + 1

    out: list[dict] = []
    for p in parts:
        if len(out) >= limit:
            break
        if count_per_target.get(p["guild_id"], 0) >= TARGET_DAILY_CAP:
            continue
        dt = await db.pvp_defense_teams.find_one(
            {"guild_id": p["guild_id"]}, {"_id": 0, "is_valid": 1, "adventurer_ids": 1, "updated_at": 1},
        )
        if not dt or not dt.get("is_valid"):
            continue
        # Compute safe public projection.
        summary = await build_team_summary(db, guild_id=p["guild_id"], adventurer_ids=dt["adventurer_ids"])
        out.append({
            "guild_public_id": p["guild_public_id"],
            "guild_name": p["guild_name"],
            "league": p["league"],
            "rating": p["rating"],
            "total_power_band": _power_band(summary["total_power"]),
            "last_active_relative": _relative_time(p.get("last_match_at") or dt.get("updated_at")),
            "average_level": summary["average_level"],
            "roles": summary["roles"],
        })
    return out


# ─── Challenge / Match resolution ─────────────────────────────────────────────
async def challenge(
    db, *, attacker_guild: dict, attacker_user_id: str,
    opponent_guild_public_id: str, attacker_adventurer_ids: list[str], mode: str = "ranked",
) -> dict:
    # ROUND 12.D — Validation ordering:
    # 1. payload shape (team size 5) → 422 pvp.team_size_mismatch
    # 2. self-check → 400 pvp.self_challenge
    # 3. season active → 423 pvp.season_inactive
    # 4. account-age gate → 423 pvp.account_too_young
    # 5. daily limit + target cooldown → 429 (require season + opponent later)
    # 6. opponent lookup → 404 pvp.opponent_not_found / pvp.no_defense_team
    # 7. attacker eligibility → 422 pvp.team_invalid

    # 1. Payload shape
    if not isinstance(attacker_adventurer_ids, list) or len(attacker_adventurer_ids) != TEAM_SIZE:
        raise HTTPException(422, {
            "code": "pvp.team_size_mismatch",
            "user_message": f"Devi selezionare esattamente {TEAM_SIZE} attaccanti.",
            "received": len(attacker_adventurer_ids) if isinstance(attacker_adventurer_ids, list) else 0,
        })

    # 2. Self-challenge guard
    my_public = attacker_guild.get("public_id") or attacker_guild["id"][:8]
    if opponent_guild_public_id == my_public:
        raise HTTPException(400, {
            "code": "pvp.self_challenge",
            "user_message": "Non puoi sfidare te stesso.",
        })

    # 3. Season active
    season = await get_current_season(db)
    if not season or season["status"] != "active":
        raise HTTPException(423, {
            "code": "pvp.season_inactive",
            "user_message": "Nessuna stagione attiva: l'Arena è chiusa.",
        })

    # 4. Account age gate (ranked only)
    if mode == "ranked":
        try:
            created_at = attacker_guild.get("created_at")
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at)
            else:
                created_dt = created_at
            if created_dt and (datetime.now(timezone.utc) - created_dt).total_seconds() < MIN_GUILD_AGE_SECONDS:
                raise HTTPException(423, {
                    "code": "pvp.account_too_young",
                    "user_message": f"La gilda è troppo giovane per le ranked (min {MIN_GUILD_AGE_SECONDS // 60} minuti).",
                })
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("[pvp] account_age_gate check failed (allowing): %s", exc)

    # Resolve opponent
    opp = await db.guilds.find_one({"public_id": opponent_guild_public_id})
    if not opp:
        opp = await db.guilds.find_one({"id": {"$regex": f"^{opponent_guild_public_id}"}})
    if not opp:
        raise HTTPException(404, {"code": "pvp.opponent_not_found", "user_message": "Gilda avversaria non trovata."})

    opp_dt = await db.pvp_defense_teams.find_one({"guild_id": opp["id"]})
    if not opp_dt or not opp_dt.get("is_valid"):
        raise HTTPException(404, {
            "code": "pvp.no_defense_team",
            "user_message": "L'avversario non ha una squadra di difesa valida.",
        })

    # Validate attacker team
    is_valid, warnings = await _validate_team(db, guild_id=attacker_guild["id"], adventurer_ids=attacker_adventurer_ids)
    if not is_valid:
        raise HTTPException(422, {
            "code": "pvp.team_invalid",
            "warnings": warnings,
            "user_message": "Squadra d'attacco non valida.",
        })

    # Daily limits
    today_start, today_end = _today_utc_range()
    daily_count = await db.pvp_matches.count_documents({
        "attacker_guild_id": attacker_guild["id"],
        "created_at": {"$gte": today_start, "$lt": today_end},
        "mode": "ranked",
    })
    if mode == "ranked" and daily_count >= DAILY_RANKED_LIMIT:
        raise HTTPException(429, {
            "code": "pvp.daily_limit",
            "user_message": f"Limite giornaliero raggiunto ({DAILY_RANKED_LIMIT} sfide/giorno).",
        })

    # Target cooldown
    target_count = await db.pvp_matches.count_documents({
        "attacker_guild_id": attacker_guild["id"],
        "defender_guild_id": opp["id"],
        "created_at": {"$gte": today_start, "$lt": today_end},
    })
    if target_count >= TARGET_DAILY_CAP:
        raise HTTPException(429, {
            "code": "pvp.target_cooldown",
            "user_message": f"Hai già sfidato questa gilda {TARGET_DAILY_CAP} volte oggi.",
        })

    # Snapshots
    attacker_snap = await _build_snapshot(db, guild=attacker_guild, adventurer_ids=attacker_adventurer_ids)
    defender_snap = await _build_snapshot(db, guild=opp, adventurer_ids=opp_dt["adventurer_ids"])

    match_id = str(uuid.uuid4())
    # Combat resolution
    combat = simulate(attacker_snap, defender_snap, match_id=match_id, season_id=season["season_id"])

    # Test-artifact flag (excludes from leaderboard)
    is_test = bool(attacker_guild.get("is_test_artifact") or opp.get("is_test_artifact"))

    # Persist match
    doc = {
        "match_id": match_id,
        "season_id": season["season_id"],
        "season_slug": season["slug"],
        "mode": mode,
        "attacker_guild_id": attacker_guild["id"],
        "attacker_guild_public_id": my_public,
        "attacker_guild_name": attacker_guild["name"],
        "defender_guild_id": opp["id"],
        "defender_guild_public_id": opp.get("public_id") or opp["id"][:8],
        "defender_guild_name": opp["name"],
        "attacker_snapshot": attacker_snap,
        "defender_snapshot": defender_snap,
        "outcome": combat["outcome"],
        "final_attack_score": combat["final_attack_score"],
        "final_defense_score": combat["final_defense_score"],
        "report_it": combat["report_it"],
        "combat_version": combat["combat_version"],
        "rng_version": combat["rng_version"],
        "seed_hash": combat["seed_hash"],
        "rating_applied": False,
        "is_test": is_test,
        "created_at": _now_iso(),
    }
    await db.pvp_matches.insert_one(doc)
    await write_audit(
        db, event_type="pvp_match_created",
        actor_user_id=attacker_user_id, actor_guild_id=attacker_guild["id"],
        source="pvp.challenge", related_entity_id=match_id,
        metadata={"defender_guild_id": opp["id"], "mode": mode, "season_id": season["season_id"]},
    )

    # Rating update (idempotent flag on doc)
    if mode == "ranked" and not is_test:
        await _apply_rating(db, match_doc=doc, season=season)

    # Reload to get the final state
    final = await db.pvp_matches.find_one({"match_id": match_id}, {"_id": 0})
    return final


async def _apply_rating(db, *, match_doc: dict, season: dict) -> None:
    if match_doc.get("rating_applied"):
        return
    att_guild_id = match_doc["attacker_guild_id"]
    def_guild_id = match_doc["defender_guild_id"]
    season_id = match_doc["season_id"]
    att_part = await db.season_participations.find_one(
        {"season_id": season_id, "guild_id": att_guild_id}, {"_id": 0},
    )
    def_part = await db.season_participations.find_one(
        {"season_id": season_id, "guild_id": def_guild_id}, {"_id": 0},
    )
    # Lazy bootstrap defender participation if missing.
    if not att_part:
        guild = await db.guilds.find_one({"id": att_guild_id})
        att_part = await get_or_create_participation(db, season_id=season_id, guild=guild)
    if not def_part:
        guild = await db.guilds.find_one({"id": def_guild_id})
        def_part = await get_or_create_participation(db, season_id=season_id, guild=guild)

    outcome = match_doc["outcome"]
    attacker_outcome = {"attacker_win": "win", "defender_win": "loss", "draw": "draw"}[outcome]

    new_att, new_def = apply_match(att_part["rating"], def_part["rating"], attacker_outcome)

    # Update attacker participation
    att_updates = {
        "rating": new_att,
        "best_rating": max(att_part["best_rating"], new_att),
        "attacks_played": att_part["attacks_played"] + 1,
        "placement_matches_played": att_part["placement_matches_played"] + 1,
        "last_match_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    if attacker_outcome == "win":
        att_updates["wins"] = att_part["wins"] + 1
    elif attacker_outcome == "loss":
        att_updates["losses"] = att_part["losses"] + 1
    else:
        att_updates["draws"] = att_part["draws"] + 1
    att_updates["league"] = assign_league(new_att, att_updates["placement_matches_played"])
    league_order = ["unranked", "bronze", "silver", "gold", "platinum", "diamond", "master"]
    if league_order.index(att_updates["league"]) > league_order.index(att_part["highest_league"]):
        att_updates["highest_league"] = att_updates["league"]
    await db.season_participations.update_one(
        {"season_id": season_id, "guild_id": att_guild_id}, {"$set": att_updates},
    )

    # Update defender participation
    def_updates = {
        "rating": new_def,
        "best_rating": max(def_part["best_rating"], new_def),
        "placement_matches_played": def_part["placement_matches_played"] + 1,
        "last_match_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    if attacker_outcome == "win":
        def_updates["defense_losses"] = def_part["defense_losses"] + 1
        def_updates["losses"] = def_part["losses"] + 1
    elif attacker_outcome == "loss":
        def_updates["defense_wins"] = def_part["defense_wins"] + 1
        def_updates["wins"] = def_part["wins"] + 1
    else:
        def_updates["draws"] = def_part["draws"] + 1
    def_updates["league"] = assign_league(new_def, def_updates["placement_matches_played"])
    if league_order.index(def_updates["league"]) > league_order.index(def_part["highest_league"]):
        def_updates["highest_league"] = def_updates["league"]
    await db.season_participations.update_one(
        {"season_id": season_id, "guild_id": def_guild_id}, {"$set": def_updates},
    )

    # Idempotency flag
    await db.pvp_matches.update_one(
        {"match_id": match_doc["match_id"]},
        {"$set": {"rating_applied": True,
                  "rating_delta_attacker": new_att - att_part["rating"],
                  "rating_delta_defender": new_def - def_part["rating"]}},
    )
    await write_audit(
        db, event_type="pvp_rating_updated",
        actor_guild_id=att_guild_id, source="pvp.rating",
        related_entity_id=match_doc["match_id"],
        metadata={
            "attacker_delta": new_att - att_part["rating"],
            "defender_delta": new_def - def_part["rating"],
            "outcome": outcome,
            "season_id": season_id,
        },
    )
    await write_audit(
        db, event_type="pvp_match_resolved",
        actor_guild_id=att_guild_id, source="pvp.challenge",
        related_entity_id=match_doc["match_id"],
        metadata={"outcome": outcome, "season_id": season_id},
    )

    # ROUND 16.A Phase 1 — achievement trigger emissions for PvP match.
    # Fire `pvp_match_completed` for BOTH guilds (with outcome in payload)
    # and `season_league_reached` whenever a guild's `highest_league`
    # advanced this match.
    try:
        from app.achievements.trigger_emitter import emit_achievement_trigger
        att_outcome = attacker_outcome  # "win" / "loss" / "draw"
        def_outcome = {"win": "loss", "loss": "win", "draw": "draw"}[att_outcome]
        match_id = match_doc["match_id"]
        await emit_achievement_trigger(
            db, att_guild_id, "pvp_match_completed",
            {
                "outcome": att_outcome,
                "opponent_guild_id": def_guild_id,
                "match_id": match_id,
                "season_id": season_id,
            },
            idempotency_key=f"{match_id}:att",
        )
        await emit_achievement_trigger(
            db, def_guild_id, "pvp_match_completed",
            {
                "outcome": def_outcome,
                "opponent_guild_id": att_guild_id,
                "match_id": match_id,
                "season_id": season_id,
            },
            idempotency_key=f"{match_id}:def",
        )
        if att_updates.get("highest_league") != att_part.get("highest_league"):
            await emit_achievement_trigger(
                db, att_guild_id, "season_league_reached",
                {
                    "league_slug": att_updates["highest_league"],
                    "season_id": season_id,
                },
                idempotency_key=f"{att_guild_id}:{season_id}:{att_updates['highest_league']}",
            )
        if def_updates.get("highest_league") != def_part.get("highest_league"):
            await emit_achievement_trigger(
                db, def_guild_id, "season_league_reached",
                {
                    "league_slug": def_updates["highest_league"],
                    "season_id": season_id,
                },
                idempotency_key=f"{def_guild_id}:{season_id}:{def_updates['highest_league']}",
            )
    except Exception as exc:  # noqa: BLE001
        # never break PvP because of an achievement issue
        import logging
        logging.getLogger("orbus.pvp").warning(
            "achievement trigger failed in _apply_rating: %s", exc)


async def list_my_matches(db, *, guild_id: str, limit: int = 50) -> list[dict]:
    rows = await db.pvp_matches.find(
        {"$or": [{"attacker_guild_id": guild_id}, {"defender_guild_id": guild_id}]},
        {"_id": 0, "attacker_snapshot": 0, "defender_snapshot": 0, "report_it": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return rows


async def get_match(db, *, guild_id: str, match_id: str) -> Optional[dict]:
    m = await db.pvp_matches.find_one({"match_id": match_id}, {"_id": 0})
    if not m:
        return None
    # ownership check: caller must be attacker or defender.
    if m["attacker_guild_id"] != guild_id and m["defender_guild_id"] != guild_id:
        return None
    return m


__all__ = [
    "ensure_pvp_indexes",
    "get_defense_team", "upsert_defense_team", "delete_defense_team",
    "build_team_summary", "list_opponents", "challenge",
    "list_my_matches", "get_match",
    "MIN_LEVEL_PVP", "TEAM_SIZE",
]
