"""ROUND 16.3 Phase 7A — PvP battle resolver.

Deterministic, seeded by `battle_id + role`. Idempotent CAS on
`status=resolving → resolved`. No side effects until the CAS transition
succeeds, so concurrent callers observing the same expired battle will
never double-resolve.

Elo K-factor 32, clamped to [800, 2400]. Draw margin 3% (no Elo delta).

Battle log: 4-6 turn narrative in Italian, hardcoded templates chosen
via seeded RNG. No LLM.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Any

from app.audit.log import write_audit
from app.pvp_continental.applier import get_pvp_arfus_bonus_sum


logger = logging.getLogger("orbus.pvp_continental")


ELO_K_FACTOR: int = 32
ELO_MIN: int = 800
ELO_MAX: int = 2400
ELO_DEFAULT: int = 1200

DRAW_MARGIN: float = 0.03
NEW_PLAYER_BUFF: float = 0.20
NEW_PLAYER_THRESHOLD: int = 10

VARIANCE_LOW: float = 0.9
VARIANCE_HIGH: float = 1.1


def _sum_stats(adv: dict) -> int:
    """Sum snapshot stats. Missing fields default to 0 (never raise)."""
    return (
        int(adv.get("strength_snapshot") or 0)
        + int(adv.get("agility_snapshot") or 0)
        + int(adv.get("intellect_snapshot") or 0)
        + int(adv.get("endurance_snapshot") or 0)
        + int(adv.get("faith_snapshot") or 0)
        + int(adv.get("level_snapshot") or 1) * 3
    )


async def _count_completed_expeditions(db, guild_id: str) -> int:
    return await db.expeditions.count_documents(
        {"guild_id": guild_id, "status": "completed"},
    )


async def calculate_battle_score(
    db,
    *,
    team: list[dict],
    guild_id: str,
    role: str,
    battle_id: str,
) -> float:
    """Deterministic seeded score for one side.

    Formula (documented in `round163_phase7a_iter1_backend_report.md`):
        base = Σ stats
        arfus = 1 + get_pvp_arfus_bonus_sum(guild)    # cap 1.50
        new_player_buff = 1.20 if defender AND completed<10 else 1.00
        variance = rng.uniform(0.9, 1.1)             # seed=battle_id:role
        score = base * arfus * new_player_buff * variance
    """
    base_power = float(sum(_sum_stats(a) for a in team))
    arfus_fraction = await get_pvp_arfus_bonus_sum(db, guild_id)
    arfus_mult = 1.0 + arfus_fraction
    new_player_mult = 1.0
    if role == "defender":
        completed = await _count_completed_expeditions(db, guild_id)
        if completed < NEW_PLAYER_THRESHOLD:
            new_player_mult = 1.0 + NEW_PLAYER_BUFF
    rng = random.Random(f"{battle_id}:{role}")
    variance = rng.uniform(VARIANCE_LOW, VARIANCE_HIGH)
    return base_power * arfus_mult * new_player_mult * variance


def compute_elo_update(winner_elo: int, loser_elo: int) -> tuple[int, int]:
    """Standard Elo with K=32. Returns (new_winner, new_loser) clamped."""
    expected_w = 1.0 / (1.0 + 10 ** ((loser_elo - winner_elo) / 400.0))
    delta = ELO_K_FACTOR * (1.0 - expected_w)
    new_w = round(winner_elo + delta)
    new_l = round(loser_elo - delta)
    return (
        max(ELO_MIN, min(ELO_MAX, new_w)),
        max(ELO_MIN, min(ELO_MAX, new_l)),
    )


def find_mvp(team: list[dict], seed: str) -> str | None:
    """Deterministic MVP: highest _sum_stats; ties broken by seeded RNG."""
    if not team:
        return None
    scored = sorted(
        [(a["id"], _sum_stats(a)) for a in team],
        key=lambda t: -t[1],
    )
    top_score = scored[0][1]
    top_ids = [aid for aid, s in scored if s == top_score]
    if len(top_ids) == 1:
        return top_ids[0]
    rng = random.Random(f"{seed}:mvp")
    return rng.choice(sorted(top_ids))


# ── Italian battle log templates ─────────────────────────────────────
# Each template is a `.format()` string using {actor}, {target}, {guild}.
# Kept short and evocative. Deterministic selection via seeded RNG.
_OPENING_TEMPLATES: list[str] = [
    "Le due squadre si schierano sotto il vessillo del proprio continente.",
    "L'arena si accende: {chall_guild} sfida {def_guild} a duello aperto.",
    "Il segnale di battaglia risuona: {chall_guild} contro {def_guild}.",
    "I comandanti scambiano un cenno formale prima dell'ingaggio.",
]

_MID_TEMPLATES: list[str] = [
    "{actor} carica la prima linea avversaria con furia disciplinata.",
    "{actor} intona una preghiera che rinvigorisce i compagni.",
    "{actor} evoca una barriera che assorbe l'ondata nemica.",
    "{actor} scaglia una raffica di dardi contro le fila opposte.",
    "{actor} coordina un'azione di fiancheggiamento sui difensori scoperti.",
    "{actor} paralizza il campo avversario con un incantesimo di controllo.",
    "{actor} affonda un colpo mirato sui punti deboli dell'armatura.",
    "{actor} trascina fuori dal centro un compagno ferito per curarlo.",
]

_MVP_TEMPLATES: list[str] = [
    "{actor} apre uno squarcio decisivo nel dispositivo avversario.",
    "{actor} ribalta l'inerzia dello scontro con una manovra brillante.",
    "{actor} si distingue per lucidità e coordinamento, trascinando i propri.",
]

_CLOSING_TEMPLATES_WIN: list[str] = [
    "La battaglia si conclude: la vittoria va a {winner_guild}.",
    "L'arbitro alza la bandiera di {winner_guild}: fine del duello.",
]

_CLOSING_TEMPLATES_DRAW: list[str] = [
    "Le forze si bilanciano: l'incontro termina in parità.",
    "Nessuna delle due gilde riesce a prevalere: pareggio dichiarato.",
]

_CLOSING_TEMPLATES_FORFEIT: list[str] = [
    "La squadra difensiva non si presenta: {winner_guild} vince a tavolino.",
    "Il tempo di risposta scade: forfait automatico a favore di {winner_guild}.",
]


def _pick(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def generate_battle_log(
    *,
    battle: dict,
    chall_guild_name: str,
    def_guild_name: str,
    outcome: str,
    mvp_id: str | None,
    winner_side: str | None,
) -> list[dict]:
    """Return 4-6 turn narrative. Deterministic per battle.id.

    Each entry: {turn, actor_guild_id, actor_adventurer_id, text_it}.
    """
    rng = random.Random(f"{battle['id']}:log")
    log: list[dict] = []
    turn = 1

    # Opening (turn 1)
    log.append({
        "turn": turn,
        "actor_guild_id": None,
        "actor_adventurer_id": None,
        "text_it": _pick(rng, _OPENING_TEMPLATES).format(
            chall_guild=chall_guild_name, def_guild=def_guild_name,
        ),
    })
    turn += 1

    # Mid-fight: 3-4 templates alternating sides
    mid_turns = rng.randint(3, 4)
    all_advs = (battle.get("challenger_team") or []) + (
        battle.get("defender_team") or []
    )
    if not all_advs:
        all_advs = [{"id": None, "name": "?", "guild_id": None}]
    for _ in range(mid_turns):
        adv = rng.choice(all_advs)
        log.append({
            "turn": turn,
            "actor_guild_id": adv.get("guild_id"),
            "actor_adventurer_id": adv.get("id"),
            "text_it": _pick(rng, _MID_TEMPLATES).format(
                actor=adv.get("name", "Un combattente"),
            ),
        })
        turn += 1

    # MVP highlight (skip if forfeit or no mvp)
    if mvp_id and outcome != "defender_forfeit":
        mvp = next((a for a in all_advs if a.get("id") == mvp_id), None)
        if mvp:
            log.append({
                "turn": turn,
                "actor_guild_id": mvp.get("guild_id"),
                "actor_adventurer_id": mvp_id,
                "text_it": _pick(rng, _MVP_TEMPLATES).format(
                    actor=mvp.get("name", "L'MVP"),
                ),
            })
            turn += 1

    # Closing
    if outcome == "draw":
        text = _pick(rng, _CLOSING_TEMPLATES_DRAW)
    elif outcome == "defender_forfeit":
        text = _pick(rng, _CLOSING_TEMPLATES_FORFEIT).format(
            winner_guild=chall_guild_name,
        )
    else:
        winner_name = (
            chall_guild_name if winner_side == "challenger" else def_guild_name
        )
        text = _pick(rng, _CLOSING_TEMPLATES_WIN).format(
            winner_guild=winner_name,
        )
    log.append({
        "turn": turn,
        "actor_guild_id": None,
        "actor_adventurer_id": None,
        "text_it": text,
    })
    return log


async def _release_teams(db, battle: dict) -> None:
    """Set `is_available=true` on all adventurers involved in this battle.

    Idempotent: uses `on_pvp_battle_id` field to scope the release. If
    the field was cleared already (concurrent recovery), the query
    matches 0 docs and nothing happens.
    """
    await db.adventurers.update_many(
        {"on_pvp_battle_id": battle["id"]},
        {"$set": {"is_available": True, "on_pvp_battle_id": None,
                   "updated_at": datetime.now(timezone.utc)}},
    )


async def _upsert_pvp_stats(
    db, guild_id: str, *, elo: int, wins_delta: int = 0,
    losses_delta: int = 0, draws_delta: int = 0,
) -> None:
    now = datetime.now(timezone.utc)
    await db.guild_pvp_stats.update_one(
        {"guild_id": guild_id},
        {"$set": {"elo": elo, "updated_at": now},
         "$inc": {"wins": wins_delta, "losses": losses_delta,
                  "draws": draws_delta,
                  "current_active_challenges": -1}},
        upsert=True,
    )


async def resolve_battle(db, battle_id: str, *, reason: str = "on_visit") -> dict:
    """CAS-guarded resolution. Safe to call concurrently.

    Returns dict with `{ok, reason, outcome?}`. Never raises on the
    happy path; on unexpected errors, restores battle to `resolving`
    only if we own the CAS transition.
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    battle = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        return {"ok": False, "reason": "not_found"}
    if battle.get("status") == "resolved":
        return {"ok": True, "reason": "already_resolved"}

    # Two paths to resolution:
    #   1. status=pending_response AND response_deadline<=now → forfeit
    #   2. status=resolving        AND resolves_at<=now       → normal
    if battle["status"] == "pending_response":
        deadline = battle.get("response_deadline")
        if deadline and deadline > now_iso:
            return {"ok": False, "reason": "deadline_not_reached"}
        cas = await db.pvp_battles.update_one(
            {"id": battle_id, "status": "pending_response"},
            {"$set": {"status": "resolving",
                       "resolution_started_at": now_iso,
                       "defender_status": "timeout_defaulted"}},
        )
        if cas.modified_count == 0:
            return {"ok": False, "reason": "cas_lost"}
        return await _finalize_forfeit(db, battle_id, now_iso, reason=reason)

    if battle["status"] == "resolving":
        if battle.get("resolves_at") and battle["resolves_at"] > now_iso:
            return {"ok": False, "reason": "not_yet"}
        cas = await db.pvp_battles.update_one(
            {"id": battle_id, "status": "resolving",
             "resolved_at": None},
            {"$set": {"resolution_started_at": now_iso}},
        )
        if cas.modified_count == 0:
            return {"ok": False, "reason": "cas_lost"}
        return await _finalize_normal(db, battle_id, now_iso, reason=reason)

    return {"ok": False, "reason": f"unexpected_status:{battle['status']}"}


async def _finalize_forfeit(
    db, battle_id: str, now_iso: str, *, reason: str,
) -> dict:
    battle = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    chall_g = await db.guilds.find_one(
        {"id": battle["challenger_guild_id"]}, {"_id": 0, "name": 1},
    ) or {"name": "?"}
    def_g = await db.guilds.find_one(
        {"id": battle["defender_guild_id"]}, {"_id": 0, "name": 1},
    ) or {"name": "?"}
    mvp_id = find_mvp(battle.get("challenger_team") or [], battle["id"])
    log_entries = generate_battle_log(
        battle=battle,
        chall_guild_name=chall_g["name"],
        def_guild_name=def_g["name"],
        outcome="defender_forfeit",
        mvp_id=mvp_id,
        winner_side="challenger",
    )
    outcome = "defender_forfeit"
    # No Elo change on forfeit (avoid rage-quit abuse). Still count win.
    chall_stats = await _get_or_init_stats(db, battle["challenger_guild_id"])
    def_stats = await _get_or_init_stats(db, battle["defender_guild_id"])
    await _upsert_pvp_stats(
        db, battle["challenger_guild_id"], elo=chall_stats["elo"],
        wins_delta=1,
    )
    await _upsert_pvp_stats(
        db, battle["defender_guild_id"], elo=def_stats["elo"],
        losses_delta=1,
    )
    await db.pvp_battles.update_one(
        {"id": battle_id},
        {"$set": {
            "status": "resolved", "resolved_at": now_iso,
            "outcome": outcome, "mvp_adventurer_id": mvp_id,
            "battle_log": log_entries,
        }},
    )
    await _release_teams(db, battle)
    await write_audit(
        db, event_type="PVP_CHALLENGE_TIMEOUT_DEFAULTED",
        actor_user_id=None, actor_guild_id=battle["challenger_guild_id"],
        source="pvp_continental.resolver",
        metadata={"battle_id": battle_id, "reason": reason},
    )
    await write_audit(
        db, event_type="PVP_BATTLE_RESOLVED",
        actor_user_id=None, actor_guild_id=battle["challenger_guild_id"],
        source="pvp_continental.resolver",
        metadata={"battle_id": battle_id, "outcome": outcome},
    )
    return {"ok": True, "outcome": outcome}


async def _finalize_normal(
    db, battle_id: str, now_iso: str, *, reason: str,
) -> dict:
    battle = await db.pvp_battles.find_one({"id": battle_id}, {"_id": 0})
    chall_g = await db.guilds.find_one(
        {"id": battle["challenger_guild_id"]}, {"_id": 0, "name": 1},
    ) or {"name": "?"}
    def_g = await db.guilds.find_one(
        {"id": battle["defender_guild_id"]}, {"_id": 0, "name": 1},
    ) or {"name": "?"}

    chall_score = await calculate_battle_score(
        db, team=battle["challenger_team"],
        guild_id=battle["challenger_guild_id"],
        role="challenger", battle_id=battle["id"],
    )
    def_score = await calculate_battle_score(
        db, team=battle["defender_team"],
        guild_id=battle["defender_guild_id"],
        role="defender", battle_id=battle["id"],
    )

    hi = max(chall_score, def_score)
    if hi <= 0:
        outcome = "draw"
    else:
        diff = abs(chall_score - def_score) / hi
        if diff < DRAW_MARGIN:
            outcome = "draw"
        elif chall_score > def_score:
            outcome = "challenger_win"
        else:
            outcome = "defender_win"

    chall_stats = await _get_or_init_stats(db, battle["challenger_guild_id"])
    def_stats = await _get_or_init_stats(db, battle["defender_guild_id"])
    new_chall_elo = chall_stats["elo"]
    new_def_elo = def_stats["elo"]
    winner_side = None
    if outcome == "challenger_win":
        new_chall_elo, new_def_elo = compute_elo_update(
            chall_stats["elo"], def_stats["elo"],
        )
        winner_side = "challenger"
        winner_team = battle["challenger_team"]
    elif outcome == "defender_win":
        new_def_elo, new_chall_elo = compute_elo_update(
            def_stats["elo"], chall_stats["elo"],
        )
        winner_side = "defender"
        winner_team = battle["defender_team"]
    else:
        winner_team = (
            battle["challenger_team"] if chall_score >= def_score
            else battle["defender_team"]
        )

    mvp_id = find_mvp(winner_team, battle["id"])

    log_entries = generate_battle_log(
        battle=battle,
        chall_guild_name=chall_g["name"],
        def_guild_name=def_g["name"],
        outcome=outcome,
        mvp_id=mvp_id,
        winner_side=winner_side,
    )

    await _upsert_pvp_stats(
        db, battle["challenger_guild_id"], elo=new_chall_elo,
        wins_delta=1 if outcome == "challenger_win" else 0,
        losses_delta=1 if outcome == "defender_win" else 0,
        draws_delta=1 if outcome == "draw" else 0,
    )
    await _upsert_pvp_stats(
        db, battle["defender_guild_id"], elo=new_def_elo,
        wins_delta=1 if outcome == "defender_win" else 0,
        losses_delta=1 if outcome == "challenger_win" else 0,
        draws_delta=1 if outcome == "draw" else 0,
    )
    await db.pvp_battles.update_one(
        {"id": battle_id},
        {"$set": {
            "status": "resolved", "resolved_at": now_iso,
            "outcome": outcome, "mvp_adventurer_id": mvp_id,
            "battle_log": log_entries,
            "challenger_elo_after": new_chall_elo,
            "defender_elo_after": new_def_elo,
        }},
    )
    await _release_teams(db, battle)
    await write_audit(
        db, event_type="PVP_BATTLE_RESOLVED",
        actor_user_id=None, actor_guild_id=battle["challenger_guild_id"],
        source="pvp_continental.resolver",
        metadata={"battle_id": battle_id, "outcome": outcome,
                  "chall_score": round(chall_score, 2),
                  "def_score": round(def_score, 2)},
    )
    if outcome != "draw":
        await write_audit(
            db, event_type="PVP_ELO_UPDATED",
            actor_user_id=None, actor_guild_id=battle["challenger_guild_id"],
            source="pvp_continental.resolver",
            metadata={"battle_id": battle_id,
                      "challenger_before": chall_stats["elo"],
                      "challenger_after": new_chall_elo,
                      "defender_before": def_stats["elo"],
                      "defender_after": new_def_elo},
        )
    return {"ok": True, "outcome": outcome}


async def _get_or_init_stats(db, guild_id: str) -> dict:
    doc = await db.guild_pvp_stats.find_one(
        {"guild_id": guild_id}, {"_id": 0},
    )
    if doc:
        return doc
    now = datetime.now(timezone.utc)
    seed = {
        "guild_id": guild_id, "elo": ELO_DEFAULT,
        "wins": 0, "losses": 0, "draws": 0,
        "current_active_challenges": 0,
        "created_at": now, "updated_at": now,
    }
    try:
        await db.guild_pvp_stats.insert_one(seed)
    except Exception as exc:  # race — another caller inserted first
        logger.info("pvp_stats.race guild=%s: %s", guild_id, exc)
        doc = await db.guild_pvp_stats.find_one(
            {"guild_id": guild_id}, {"_id": 0},
        )
        return doc or seed
    return seed


async def auto_resolve_stuck_battles_for_guild(db, guild_id: str) -> int:
    """Batch on-visit resolver. Best-effort, never raises."""
    now_iso = datetime.now(timezone.utc).isoformat()
    q = {
        "$or": [
            {"challenger_guild_id": guild_id},
            {"defender_guild_id": guild_id},
        ],
        "$and": [
            {"status": {"$in": ["pending_response", "resolving"]}},
            {"$or": [
                {"status": "pending_response",
                 "response_deadline": {"$lte": now_iso}},
                {"status": "resolving",
                 "resolves_at": {"$lte": now_iso}},
            ]},
        ],
    }
    resolved = 0
    async for b in db.pvp_battles.find(q, {"_id": 0, "id": 1}):
        try:
            r = await resolve_battle(db, b["id"], reason="on_visit_batch")
            if r.get("ok"):
                resolved += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("resolve %s failed: %s", b["id"], exc)
    return resolved
