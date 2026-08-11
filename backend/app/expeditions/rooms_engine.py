"""FASE 5 (2026-08-08) — Motore delle spedizioni a stanze.

Stati e flusso: memory/fase5_design_dungeon_stanze.md §2.
Il doc expedition resta `status="in_progress"` per tutta la run (lock
gruppo/liste invariati); il sub-stato vive in `room_state`. Un solo
timer (`completes_at`): stanza corrente oppure deadline della scelta
(oltre → auto-continue). Il finalize passa dal claim CAS
`in_progress → completing` e riusa `apply_expedition_completion`
(stessa economia del legacy).

Idempotenza risoluzione stanza: l'update è un CAS su
(id, status, room_state, current_room_idx) — se un altro worker ha già
risolto, l'update non matcha e si esce senza effetti. La risoluzione
NON tocca l'inventario (tutto matura in `carried_*` fino al finalize).
"""
from __future__ import annotations

import secrets
from datetime import timedelta

from fastapi import HTTPException

from app.dungeons.rooms import (
    DECISION_DEADLINE_SECONDS,
    REST_CHANCE_BONUS,
    REST_DURATION_FACTOR,
    apply_salvage,
)

_rng = secrets.SystemRandom()


def _now():
    from app.expeditions.services import utc_now
    return utc_now()


# ── Risoluzione stanza dovuta (chiamata dalla lazy sweep) ────────────────

async def advance_due_rooms_expedition(db, exp_id: str) -> None:
    """Gestisce un doc a stanze con `completes_at` scaduto."""
    exp = await db.expeditions.find_one(
        {"id": exp_id, "status": "in_progress", "mode": "rooms"},
        {"_id": 0},
    )
    if not exp:
        return
    state = exp.get("room_state")
    if state == "awaiting_choice":
        # Deadline scaduta → auto-continue (mai run bloccate).
        await _start_next_room(db, exp, rest=False, auto=True)
        return
    if state == "in_room":
        await _resolve_current_room(db, exp)


async def _resolve_current_room(db, exp: dict) -> None:
    rooms = exp.get("rooms_snapshot") or []
    idx = int(exp.get("current_room_idx", 0))
    if idx >= len(rooms):
        return  # doc corrotto: lascialo alla ricognizione manuale
    room = rooms[idx]
    chance = min(100, int(room["chance"]) + int(exp.get("rest_bonus_next", 0)))
    roll = _rng.randint(1, 100)
    success = roll <= chance
    now = _now()
    room_result = {
        "idx": idx,
        "slug": room.get("slug"),
        "name_it": room.get("name_it"),
        "kind": room.get("kind"),
        "success": success,
        "roll": roll,
        "chance": chance,
        "gold": int(room.get("gold", 0)) if success else 0,
        "xp": int(room.get("xp", 0)) if success else 0,
        "loot_count": 0,
        "resolved_at": now.isoformat(),
    }

    if not success:
        # Sconfitta in stanza → ritirata forzata (salvage 25%/40%).
        await _finalize_rooms(db, exp, outcome="failed",
                              last_room_result=room_result)
        return

    # Loot solo nelle stanze has_loot; nessun side-effect inventario qui.
    room_loot: list[str] = []
    if room.get("has_loot"):
        from app.expeditions.loot_tables import roll_loot_for_dungeon
        dungeon = await db.dungeons.find_one(
            {"id": exp["dungeon_id"]}, {"_id": 0},
        )
        if dungeon:
            room_loot = await roll_loot_for_dungeon(db, dungeon, True)
    room_result["loot_count"] = len(room_loot)

    is_last = idx >= len(rooms) - 1
    if is_last:
        await _finalize_rooms(db, exp, outcome="completed",
                              last_room_result=room_result,
                              last_room_loot=room_loot)
        return

    # Successo intermedio → attesa scelta (deadline 24h → auto-continue).
    deadline = now + timedelta(seconds=DECISION_DEADLINE_SECONDS)
    update = {
        "$set": {
            "room_state": "awaiting_choice",
            "completes_at": deadline.isoformat(),
            "rest_bonus_next": 0,
            "updated_at": now.isoformat(),
        },
        "$inc": {
            "carried_gold": room_result["gold"],
            "carried_xp": room_result["xp"],
        },
        "$push": {
            "room_results": room_result,
            **({"carried_loot_ids": {"$each": room_loot}} if room_loot else {}),
        },
    }
    await db.expeditions.update_one(
        {
            "id": exp["id"], "status": "in_progress",
            "room_state": "in_room", "current_room_idx": idx,
        },
        update,
    )


async def _start_next_room(db, exp: dict, *, rest: bool, auto: bool,
                           route: str | None = None) -> bool:
    """awaiting_choice → in_room sulla prossima stanza. True se applicato.

    FASE 8C — se la prossima entry è un BIVIO serve la scelta del
    percorso (`route`); in auto-continue (deadline scaduta) si prende
    la prima opzione (la via "sicura" per convenzione autoriale).
    """
    from app.dungeons.rooms import resolve_fork

    rooms = list(exp.get("rooms_snapshot") or [])
    idx = int(exp.get("current_room_idx", 0))
    next_idx = idx + 1
    if next_idx >= len(rooms):
        return False

    snapshot_update: dict | None = None
    # Risolvi eventuali bivi consecutivi (le opzioni-scorciatoia possono
    # teoricamente esporre un altro bivio; in auto si sceglie sempre la
    # prima opzione).
    while next_idx < len(rooms) and rooms[next_idx].get("type") == "fork":
        fork = rooms[next_idx]
        chosen = route if route else (
            fork["options"][0]["key"] if auto or not route else None
        )
        if not chosen:
            raise HTTPException(status_code=422, detail={
                "code": "rooms.route_required",
                "fork_id": fork.get("fork_id"),
                "options": [
                    {"key": o["key"], "label_it": o["label_it"],
                     "description_it": o.get("description_it", "")}
                    for o in fork.get("options", [])
                ],
                "user_message": (
                    "Il percorso si biforca: scegli quale via prendere."
                ),
            })
        resolved = resolve_fork(rooms, next_idx, chosen)
        if resolved is None:
            raise HTTPException(status_code=422, detail={
                "code": "rooms.invalid_route",
                "user_message": "Percorso non valido per questo bivio.",
            })
        rooms = resolved
        snapshot_update = {"rooms_snapshot": rooms}
        route = None  # la scelta vale per UN bivio

    if next_idx >= len(rooms):
        return False

    now = _now()
    duration = int(rooms[next_idx]["duration_seconds"])
    if rest:
        duration = int(round(duration * REST_DURATION_FACTOR))
    res = await db.expeditions.update_one(
        {
            "id": exp["id"], "status": "in_progress",
            "room_state": "awaiting_choice", "current_room_idx": idx,
        },
        {"$set": {
            **(snapshot_update or {}),
            "current_room_idx": next_idx,
            "room_state": "in_room",
            # FASE 9P — timestamp autoritativi della stanza corrente
            # (durata EFFETTIVA: il riposo la allunga del 25%).
            "room_started_at": now.isoformat(),
            "room_duration_seconds": int(duration),
            "completes_at": (now + timedelta(seconds=duration)).isoformat(),
            "rest_bonus_next": REST_CHANCE_BONUS if rest else 0,
            "auto_continued": bool(auto),
            "updated_at": now.isoformat(),
        }},
    )
    return res.modified_count == 1


# ── Azione del giocatore ─────────────────────────────────────────────────

VALID_ACTIONS = ("continue", "rest_and_continue", "escape")


async def advance_rooms_action(db, guild: dict, expedition_id: str,
                               action: str, route: str | None = None) -> dict:
    """POST /api/expeditions/{id}/advance — scelta dopo una stanza.

    FASE 8C — `route` seleziona l'opzione quando la prossima entry è
    un bivio (obbligatoria in quel caso per continue/rest)."""
    if action not in VALID_ACTIONS:
        raise HTTPException(status_code=422, detail={
            "code": "rooms.invalid_action",
            "user_message": "Azione non valida.",
        })
    exp = await db.expeditions.find_one(
        {"id": expedition_id, "guild_id": guild["id"]}, {"_id": 0},
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Spedizione non trovata")
    if exp.get("mode") != "rooms" or exp.get("status") != "in_progress":
        raise HTTPException(status_code=409, detail={
            "code": "rooms.not_active",
            "user_message": "Questa spedizione non è in corso a stanze.",
        })
    if exp.get("room_state") != "awaiting_choice":
        raise HTTPException(status_code=409, detail={
            "code": "rooms.not_awaiting_choice",
            "user_message": (
                "Il gruppo è ancora impegnato nella stanza: aspetta che "
                "la stanza si concluda."
            ),
        })

    if action == "escape":
        await _finalize_rooms(db, exp, outcome="escaped")
    else:
        applied = await _start_next_room(
            db, exp, rest=(action == "rest_and_continue"), auto=False,
            route=route,
        )
        if not applied:
            raise HTTPException(status_code=409, detail={
                "code": "rooms.conflict",
                "user_message": "La situazione è cambiata: ricarica la pagina.",
            })

    from app.expeditions.services import expedition_public
    fresh = await db.expeditions.find_one(
        {"id": expedition_id}, {"_id": 0},
    )
    return {"expedition": expedition_public(fresh)}


# ── Finalize (unica via d'uscita: completed / escaped / failed) ─────────

_OUTCOME_SUMMARY = {
    "completed": "Success",
    "failed": "Failed",
    "escaped": "Escaped",
}


def _result_log_it(outcome: str, dungeon_name: str,
                   rooms_done: int, rooms_total: int) -> str:
    if outcome == "completed":
        return (
            f"Il gruppo ha ripulito {dungeon_name} stanza dopo stanza "
            f"({rooms_total}/{rooms_total}) ed è tornato vittorioso."
        )
    if outcome == "escaped":
        return (
            f"Il gruppo è fuggito da {dungeon_name} dopo "
            f"{rooms_done}/{rooms_total} stanze, portando in salvo metà "
            "del bottino. L'esperienza dell'impresa incompiuta è perduta."
        )
    return (
        f"Il gruppo è stato travolto in {dungeon_name} "
        f"({rooms_done}/{rooms_total} stanze superate) e si è ritirato "
        "con quel poco che è riuscito a salvare."
    )


async def _finalize_rooms(db, exp: dict, *, outcome: str,
                          last_room_result: dict | None = None,
                          last_room_loot: list | None = None) -> None:
    # Claim CAS identico al legacy: un solo finalize può vincere.
    from pymongo import ReturnDocument
    claimed = await db.expeditions.find_one_and_update(
        {"id": exp["id"], "status": "in_progress"},
        {"$set": {"status": "completing"}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        return

    dungeon = await db.dungeons.find_one(
        {"id": claimed["dungeon_id"]}, {"_id": 0},
    )
    members = await db.expedition_members.find(
        {"expedition_id": claimed["id"]}, {"_id": 0},
    ).to_list(50)

    room_results = list(claimed.get("room_results") or [])
    carried_gold = int(claimed.get("carried_gold", 0))
    carried_xp = int(claimed.get("carried_xp", 0))
    carried_loot = list(claimed.get("carried_loot_ids") or [])
    if last_room_result:
        room_results.append(last_room_result)
        carried_gold += int(last_room_result.get("gold", 0))
        carried_xp += int(last_room_result.get("xp", 0))
    if last_room_loot:
        carried_loot.extend(last_room_loot)

    success = outcome == "completed"

    # Salvage per esito (fuga 50%, sconfitta 25%/40%, completamento 100%
    # + bonus XP finale). Vedi design §4.
    gold_reward, kept_loot, xp_per_member = apply_salvage(
        carried_gold, carried_loot, carried_xp, outcome, rng=_rng,
    )

    # Solo a COMPLETAMENTO: Overpower sugli item, reagente del dungeon,
    # Pietra della Conoscenza. Finire i dungeon deve contare.
    overpower_extra_count = 0
    materials_found: list[dict] = []
    if success and dungeon:
        loot_multiplier = float(
            claimed.get("overpower_loot_multiplier") or 1.0
        )
        if loot_multiplier > 1.0 and kept_loot:
            extra_exact = (loot_multiplier - 1.0) * len(kept_loot)
            extra_count = int(extra_exact)
            if _rng.random() < (extra_exact - extra_count):
                extra_count += 1
            if extra_count > 0:
                kept_loot = kept_loot + [
                    _rng.choice(kept_loot) for _ in range(extra_count)
                ]
                overpower_extra_count = extra_count
        from app.expeditions.material_drop_tables import (
            roll_materials_for_dungeon,
        )
        materials_found = await roll_materials_for_dungeon(
            db, dungeon, True,
        )
        # FASE 9J — stessa policy del path legacy (helper condiviso).
        from app.expeditions.knowledge_stone import (
            maybe_roll_knowledge_stone,
        )
        stone_id = await maybe_roll_knowledge_stone(
            db, success=True, rng=_rng,
        )
        if stone_id:
            kept_loot = kept_loot + [stone_id]

    rooms_total = len(claimed.get("rooms_snapshot") or [])
    rooms_done = sum(1 for r in room_results if r.get("success"))
    result_log = _result_log_it(
        outcome, (dungeon or {}).get("name", "il dungeon"),
        rooms_done, rooms_total,
    )

    from app.expeditions.services import apply_expedition_completion
    await apply_expedition_completion(
        db, claimed=claimed, dungeon=dungeon or {}, members=members,
        success=success, gold_reward=gold_reward,
        xp_per_member=xp_per_member, loot_ids=kept_loot,
        materials_found=materials_found,
        result_summary=_OUTCOME_SUMMARY[outcome],
        result_log=result_log,
        extra_set={
            "room_state": outcome,
            "room_results": room_results,
            "carried_gold": carried_gold,
            "carried_xp": carried_xp,
            "carried_loot_ids": [],
            "rooms_outcome": outcome,
            "overpower_extra_loot_count": overpower_extra_count,
            "final_score": None,
        },
    )


__all__ = [
    "VALID_ACTIONS",
    "advance_due_rooms_expedition",
    "advance_rooms_action",
]
