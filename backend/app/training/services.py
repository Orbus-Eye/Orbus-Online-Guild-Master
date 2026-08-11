"""FASE 9I — ADDESTRAMENTO: sessioni server-authoritative, solo XP.

Regole:
  * capacità 2 sessioni attive per gilda;
  * durata 1–24h, tempi decisi dal SERVER (mai dal timer del browser);
  * l'avventuriero in addestramento è occupato (is_available=False,
    status="training"): niente dungeon, raid o altre attività;
  * al termine (sweep lazy o visita alla pagina) riceve SOLO XP —
    niente oro, item o reagenti — con level-up via progressione
    condivisa; l'XP è FLAT: nessun moltiplicatore trait/consumabile,
    solo l'eventuale +50% recupero (sotto il benchmark di gilda),
    congelato all'avvio della sessione;
  * cancellazione: XP maturata per le ore INTERE trascorse, poi rilascio.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.training.catalog import (
    TRAINING_CAPACITY,
    TRAINING_CATCHUP_MULTIPLIER,
    TRAINING_MAX_HOURS,
    TRAINING_MIN_HOURS,
    catchup_benchmark_level,
    has_training_catchup,
    training_xp_for_session,
    training_xp_per_hour,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse(raw) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))


def _error(status: int, code: str, message: str, **extra) -> HTTPException:
    return HTTPException(status_code=status, detail={
        "code": code, "user_message": message, **extra,
    })


async def guild_benchmark_level(db, guild_id: str) -> int:
    levels = [
        row.get("level", 1)
        async for row in db.adventurers.find(
            {"guild_id": guild_id, "is_retired": {"$ne": True},
             "archived": {"$ne": True}},
            {"_id": 0, "level": 1},
        )
    ]
    return catchup_benchmark_level(levels)


async def _award_training_xp(db, session: dict, *, hours: float,
                             completed: bool) -> dict:
    """CAS sulla sessione, poi accredito XP + level-up + rilascio."""
    xp = training_xp_for_session(
        int(session.get("level_at_start") or 1),
        hours,
        catchup=bool(session.get("catchup_bonus")),
    )
    now_iso = _iso(_now())
    claimed = await db.training_sessions.find_one_and_update(
        {"id": session["id"], "status": "active"},
        {"$set": {
            "status": "completed" if completed else "cancelled",
            "xp_awarded": xp,
            "hours_effective": round(min(hours, session.get(
                "duration_hours", TRAINING_MAX_HOURS)), 2),
            "completed_at": now_iso,
        }},
    )
    if not claimed:
        # Un altro worker l'ha già chiusa: idempotenza garantita.
        return {"session_id": session["id"], "xp_awarded": 0,
                "already_resolved": True}

    adv = await db.adventurers.find_one(
        {"id": session["adventurer_id"]}, {"_id": 0},
    )
    if adv:
        # Level-up con la progressione condivisa (stessa curva runtime).
        from app.expeditions.services import _resolve_levelup
        adv["experience"] = int(adv.get("experience", 0)) + xp
        adv = _resolve_levelup(adv)
        await db.adventurers.update_one(
            {"id": adv["id"]},
            {"$set": {
                "experience": adv["experience"],
                "level": adv["level"],
                "strength": adv.get("strength"),
                "agility": adv.get("agility"),
                "intellect": adv.get("intellect"),
                "endurance": adv.get("endurance"),
                "faith": adv.get("faith"),
                "is_available": True,
                "status": "idle",
                "current_mission_id": None,
                "current_mission_type": None,
                "updated_at": now_iso,
            }},
        )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="training_session_completed",
            actor_guild_id=session.get("guild_id"),
            source="training.complete",
            related_entity_id=session.get("adventurer_id"),
            metadata={
                "session_id": session["id"],
                "xp_awarded": xp,
                "catchup_bonus": bool(session.get("catchup_bonus")),
                "completed": completed,
            },
        )
    except Exception:  # noqa: BLE001
        pass
    return {"session_id": session["id"], "xp_awarded": xp,
            "adventurer": adv, "already_resolved": False}


async def complete_due_training_sessions(db, guild_id: str) -> int:
    """Sweep lazy: chiude le sessioni scadute (idempotente, CAS)."""
    now = _now()
    done = 0
    async for session in db.training_sessions.find(
        {"guild_id": guild_id, "status": "active",
         "ends_at": {"$lte": _iso(now)}},
        {"_id": 0},
    ):
        result = await _award_training_xp(
            db, session,
            hours=float(session.get("duration_hours") or 0),
            completed=True,
        )
        if not result.get("already_resolved"):
            done += 1
    return done


async def training_overview(db, *, guild: dict) -> dict:
    """Stato della sala: sessioni attive, capacità, benchmark."""
    guild_id = guild["id"]
    await complete_due_training_sessions(db, guild_id)
    now = _now()
    active = await db.training_sessions.find(
        {"guild_id": guild_id, "status": "active"},
        {"_id": 0},
    ).sort("ends_at", 1).to_list(TRAINING_CAPACITY + 2)
    recent = await db.training_sessions.find(
        {"guild_id": guild_id, "status": {"$in": ["completed", "cancelled"]}},
        {"_id": 0},
    ).sort("completed_at", -1).limit(5).to_list(5)
    benchmark = await guild_benchmark_level(db, guild_id)
    sessions = []
    for row in active:
        ends_at = _parse(row["ends_at"])
        sessions.append({
            **row,
            "remaining_seconds": max(
                0, int((ends_at - now).total_seconds())
            ),
        })
    return {
        "capacity": {"used": len(active), "max": TRAINING_CAPACITY},
        "max_hours": TRAINING_MAX_HOURS,
        "min_hours": TRAINING_MIN_HOURS,
        "benchmark_level": benchmark,
        "catchup_multiplier": TRAINING_CATCHUP_MULTIPLIER,
        "sessions": sessions,
        "recent": recent,
    }


async def training_preview(db, *, guild: dict, adventurer_id: str) -> dict:
    """XP/h, bonus recupero e XP prevista per l'avventuriero scelto."""
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"],
         "is_retired": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "level": 1, "is_available": 1,
         "class_slug": 1},
    )
    if not adv:
        raise _error(404, "training.adventurer_not_found",
                     "Avventuriero non trovato.")
    level = int(adv.get("level") or 1)
    benchmark = await guild_benchmark_level(db, guild["id"])
    catchup = has_training_catchup(level, benchmark)
    rate = training_xp_per_hour(level)
    effective = int(math.floor(
        rate * (TRAINING_CATCHUP_MULTIPLIER if catchup else 1.0)
    ))
    return {
        "adventurer_id": adv["id"],
        "name": adv["name"],
        "level": level,
        "is_available": bool(adv.get("is_available", True)),
        "at_max_level": level >= ADVENTURER_MAX_LEVEL,
        "benchmark_level": benchmark,
        "catchup_bonus": catchup,
        "xp_per_hour_base": rate,
        "xp_per_hour_effective": effective,
        "xp_24h": training_xp_for_session(
            level, TRAINING_MAX_HOURS, catchup=catchup),
    }


async def start_training_session(
    db, *, guild: dict, actor_user_id: str,
    adventurer_id: str, duration_hours: int,
) -> dict:
    guild_id = guild["id"]
    await complete_due_training_sessions(db, guild_id)

    hours = int(duration_hours)
    if hours < TRAINING_MIN_HOURS or hours > TRAINING_MAX_HOURS:
        raise _error(
            422, "training.bad_duration",
            f"Durata non valida: da {TRAINING_MIN_HOURS} a "
            f"{TRAINING_MAX_HOURS} ore.",
        )

    active_count = await db.training_sessions.count_documents(
        {"guild_id": guild_id, "status": "active"},
    )
    if active_count >= TRAINING_CAPACITY:
        raise _error(
            409, "training.capacity_full",
            f"La sala di addestramento è piena "
            f"({active_count}/{TRAINING_CAPACITY}).",
        )

    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id,
         "is_retired": {"$ne": True}},
        {"_id": 0},
    )
    if not adv:
        raise _error(404, "training.adventurer_not_found",
                     "Avventuriero non trovato.")
    if not adv.get("class_slug"):
        raise _error(
            409, "training.classless",
            "Le reclute senza classe non possono addestrarsi: scegli "
            "prima una Sala di Classe.",
        )
    level = int(adv.get("level") or 1)
    if level >= ADVENTURER_MAX_LEVEL:
        raise _error(
            409, "training.max_level",
            "Questo avventuriero è già al livello massimo.",
        )

    benchmark = await guild_benchmark_level(db, guild_id)
    catchup = has_training_catchup(level, benchmark)
    now = _now()
    ends_at = now + timedelta(hours=hours)
    session = {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "adventurer_id": adventurer_id,
        "adventurer_name": adv.get("name"),
        "level_at_start": level,
        "duration_hours": hours,
        "started_at": _iso(now),
        "ends_at": _iso(ends_at),
        "xp_per_hour": training_xp_per_hour(level),
        "catchup_bonus": catchup,
        "catchup_multiplier": (
            TRAINING_CATCHUP_MULTIPLIER if catchup else 1.0
        ),
        "benchmark_level": benchmark,
        "expected_xp": training_xp_for_session(level, hours, catchup=catchup),
        "status": "active",
        "xp_awarded": 0,
        "created_at": _iso(now),
    }

    # Lock server-side dell'avventuriero: CAS su is_available.
    locked = await db.adventurers.find_one_and_update(
        {"id": adventurer_id, "guild_id": guild_id, "is_available": True},
        {"$set": {
            "is_available": False,
            "status": "training",
            "current_mission_id": session["id"],
            "current_mission_type": "training",
            "updated_at": _iso(now),
        }},
    )
    if not locked:
        raise _error(
            409, "training.adventurer_busy",
            "Questo avventuriero è già impegnato in un'altra attività.",
        )
    await db.training_sessions.insert_one(session)
    session.pop("_id", None)
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="training_session_started",
            actor_user_id=actor_user_id, actor_guild_id=guild_id,
            source="training.start", related_entity_id=adventurer_id,
            metadata={
                "session_id": session["id"],
                "duration_hours": hours,
                "catchup_bonus": catchup,
                "expected_xp": session["expected_xp"],
            },
        )
    except Exception:  # noqa: BLE001
        pass
    return {"session": session}


async def cancel_training_session(
    db, *, guild: dict, session_id: str,
) -> dict:
    session = await db.training_sessions.find_one(
        {"id": session_id, "guild_id": guild["id"]},
        {"_id": 0},
    )
    if not session:
        raise _error(404, "training.session_not_found",
                     "Sessione di addestramento non trovata.")
    if session.get("status") != "active":
        raise _error(409, "training.session_not_active",
                     "Questa sessione è già conclusa.")
    now = _now()
    ends_at = _parse(session["ends_at"])
    if ends_at <= now:
        # Già scaduta: completa normalmente.
        result = await _award_training_xp(
            db, session,
            hours=float(session.get("duration_hours") or 0),
            completed=True,
        )
        return {"cancelled": False, "completed": True, **result}
    elapsed_hours = math.floor(
        (now - _parse(session["started_at"])).total_seconds() / 3600
    )
    result = await _award_training_xp(
        db, session, hours=float(elapsed_hours), completed=False,
    )
    return {"cancelled": True, "completed": False,
            "hours_credited": elapsed_hours, **result}


__all__ = [
    "cancel_training_session",
    "complete_due_training_sessions",
    "guild_benchmark_level",
    "start_training_session",
    "training_overview",
    "training_preview",
]
