"""FASE 5 + 8C (2026-08-08) — Dungeon a stanze: motore puro.

Le stanze sono AUTORATE in codice (`rooms_blueprints.py`, come
DUNGEON_LORE): niente migrazioni DB. FASE 8C: il sistema copre TUTTI i
dungeon canonici (22; training-yard resta single-block: tutorial day-1
con la logica starter-fallback) e introduce i BIVI (fork): scelte di
percorso con conseguenze leggibili — via sicura (+5 chance) vs via
ricca (−8/−10 chance, stanza tesoro/boss opzionale), scorciatoie.

`ROOMS_MODE_ENABLED` spegne tutto all'istante.
Tutte le funzioni qui sono PURE (nessun I/O) → unit-testabili.
Design: memory/fase5_design_dungeon_stanze.md + fase8 report.
"""
from __future__ import annotations

from app.dungeons.rooms_blueprints import ROOM_BLUEPRINTS

# ── Feature flag ─────────────────────────────────────────────────────────
ROOMS_MODE_ENABLED = True
# FASE 8C — "pilota" storico ora = tutti gli slug con blueprint autorato.
ROOMS_PILOT_SLUGS: frozenset[str] = frozenset(ROOM_BLUEPRINTS.keys())

# Modificatori di probabilità per tipo di stanza (vs chance base Fase 2).
ROOM_CHANCE_MODIFIER: dict[str, int] = {
    "guard": 0,
    "ambient": 5,
    "treasure": 5,
    "boss": -10,
}

# Riposo: +chance alla stanza successiva, +25% durata della stanza.
REST_CHANCE_BONUS = 8
REST_DURATION_FACTOR = 1.25

# FASE 10H — spedizione AUTOMATICA: durata totale del percorso ×1.20.
AUTO_DURATION_FACTOR = 1.20

# Deadline della scelta: oltre → auto-continue (mai run bloccate).
DECISION_DEADLINE_SECONDS = 24 * 3600

# Frazioni di salvataggio per esito (oro / prob. per item / XP maturata).
SALVAGE = {
    "completed": {"gold": 1.0, "items": 1.0, "xp": 1.0},
    "escaped": {"gold": 0.5, "items": 0.5, "xp": 0.5},
    "failed": {"gold": 0.25, "items": 0.25, "xp": 0.4},
}
COMPLETION_XP_BONUS = 0.25  # +25% XP al completamento (premio vs fuga)


# Generatore di fallback per slug senza blueprint autorato
# (contenuti futuri): stanze per difficoltà, boss finale.
_FALLBACK_ROOM_COUNT = {1: 3, 2: 4, 3: 5, 4: 5}


def _fallback_blueprint(dungeon: dict) -> list[dict]:
    difficulty = int(dungeon.get("difficulty", 1) or 1)
    count = _FALLBACK_ROOM_COUNT.get(difficulty, 3)
    kinds = ["guard", "ambient", "treasure", "guard", "ambient"][: count - 1]
    rooms: list[dict] = []
    share = round(1.0 / count, 4)
    for i, kind in enumerate(kinds):
        rooms.append({
            "slug": f"stanza-{i + 1}", "name_it": f"Stanza {i + 1}",
            "kind": kind, "duration_share": share, "gold_share": share,
            "xp_share": share, "has_loot": kind == "treasure",
            "narrative_it": "Il gruppo avanza con cautela.",
        })
    rest = round(1.0 - share * (count - 1), 4)
    rooms.append({
        "slug": "boss", "name_it": "L'Ultima Sala",
        "kind": "boss", "duration_share": rest, "gold_share": rest,
        "xp_share": rest, "has_loot": True,
        "narrative_it": "Il padrone del dungeon attende.",
    })
    return rooms


def rooms_mode_for_dungeon(dungeon: dict) -> bool:
    """True se questo dungeon parte in modalità stanze (pilota + flag)."""
    if not ROOMS_MODE_ENABLED:
        return False
    return (dungeon.get("slug") or "").lower() in ROOMS_PILOT_SLUGS


def _materialize_room(room: dict, dungeon: dict, base_chance: int,
                      extra_modifier: int = 0) -> dict:
    """Room di blueprint → room di snapshot con valori assoluti."""
    total_duration = int(dungeon.get("base_duration_seconds", 60) or 60)
    total_gold = int(dungeon.get("base_gold_reward", 0) or 0)
    total_xp = int(dungeon.get("base_xp_reward", 0) or 0)
    modifier = ROOM_CHANCE_MODIFIER.get(room["kind"], 0) + extra_modifier
    chance = max(5, min(100, int(base_chance) + modifier))
    return {
        "type": "room",
        "slug": room["slug"],
        "name_it": room["name_it"],
        "kind": room["kind"],
        "narrative_it": room.get("narrative_it", ""),
        "has_loot": bool(room.get("has_loot")),
        "duration_seconds": max(
            10, int(round(total_duration * room["duration_share"]))
        ),
        "gold": int(round(total_gold * room["gold_share"])),
        "xp": int(round(total_xp * room["xp_share"])),
        "chance": chance,
    }


def build_rooms_snapshot(dungeon: dict, base_chance: int) -> list[dict]:
    """Costruisce lo snapshot congelato al dispatch (stanze + bivi).

    FASE 8C — le entry possono essere stanze (`type: room`) o bivi
    (`type: fork`): il bivio contiene le opzioni con le RISPETTIVE
    stanze già materializzate (valori assoluti + chance con il
    modificatore dell'opzione); alla scelta il bivio viene sostituito
    dalle stanze dell'opzione (`resolve_fork`).
    """
    slug = (dungeon.get("slug") or "").lower()
    blueprint = ROOM_BLUEPRINTS.get(slug) or _fallback_blueprint(dungeon)
    out: list[dict] = []
    for entry in blueprint:
        if entry.get("type") == "fork":
            out.append({
                "type": "fork",
                "idx": len(out),
                "fork_id": entry["fork_id"],
                "prompt_it": entry.get("prompt_it", ""),
                "options": [
                    {
                        "key": opt["key"],
                        "label_it": opt["label_it"],
                        "description_it": opt.get("description_it", ""),
                        "rooms": [
                            _materialize_room(
                                r, dungeon, base_chance,
                                int(opt.get("chance_modifier", 0)),
                            )
                            for r in opt.get("rooms", [])
                        ],
                    }
                    for opt in entry["options"]
                ],
            })
        else:
            room = _materialize_room(entry, dungeon, base_chance)
            room["idx"] = len(out)
            out.append(room)
    return out


def resolve_fork(snapshot: list[dict], fork_pos: int,
                 option_key: str) -> list[dict] | None:
    """Sostituisce il bivio in `fork_pos` con le stanze dell'opzione.

    Ritorna il NUOVO snapshot reindicizzato, o None se posizione/opzione
    non validi. Le entry precedenti non cambiano posizione (i
    room_results già registrati restano coerenti).
    """
    if fork_pos < 0 or fork_pos >= len(snapshot):
        return None
    fork = snapshot[fork_pos]
    if fork.get("type") != "fork":
        return None
    option = next(
        (o for o in fork.get("options", []) if o.get("key") == option_key),
        None,
    )
    if option is None:
        return None
    new_snapshot = (
        list(snapshot[:fork_pos])
        + [dict(r) for r in option.get("rooms", [])]
        + list(snapshot[fork_pos + 1:])
    )
    for i, entry in enumerate(new_snapshot):
        entry["idx"] = i
    return new_snapshot


def iter_paths(slug: str) -> list[list[dict]]:
    """Tutti i percorsi completi (una scelta per bivio) di un blueprint.

    Per i test di coerenza economica (le share di ogni percorso devono
    sommare ≈ 1.0) e di struttura (boss finale su ogni percorso).
    """
    blueprint = ROOM_BLUEPRINTS.get(slug)
    if not blueprint:
        return []
    paths: list[list[dict]] = [[]]
    for entry in blueprint:
        if entry.get("type") == "fork":
            new_paths = []
            for path in paths:
                for opt in entry["options"]:
                    new_paths.append(path + list(opt.get("rooms", [])))
            paths = new_paths
        else:
            paths = [path + [entry] for path in paths]
    return paths


def build_auto_route_snapshot(
    stored_route: list[dict],
    *,
    stored_base_chance: int,
    base_chance: int,
) -> list[dict]:
    """FASE 10G-J — snapshot per la run AUTOMATICA: replay del percorso
    completato manualmente (lineare, bivi già risolti), MAI branch nuovi.

    - stessa sequenza di stanze del clear manuale;
    - chance ricalcolata per la squadra ATTUALE preservando il
      modificatore per-stanza congelato nel clear
      (chance_manuale − base_chance_manuale);
    - durata di OGNI stanza ×1.20 (totale = tempo normale ×1.20).
    """
    out: list[dict] = []
    for room in stored_route:
        if room.get("type") != "room":
            continue  # difensivo: un fork non risolto non viene replayato
        modifier = int(room.get("chance", stored_base_chance)) - int(
            stored_base_chance
        )
        new_room = dict(room)
        new_room["idx"] = len(out)
        new_room["chance"] = max(5, min(100, int(base_chance) + modifier))
        new_room["duration_seconds"] = max(
            10,
            int(round(
                int(room.get("duration_seconds", 10))
                * AUTO_DURATION_FACTOR
            )),
        )
        out.append(new_room)
    return out


def auto_route_duration_seconds(stored_route: list[dict]) -> int:
    """Durata totale della run automatica: somma stanze ×1.20."""
    total = sum(
        int(r.get("duration_seconds", 0))
        for r in stored_route
        if r.get("type") == "room"
    )
    return int(round(total * AUTO_DURATION_FACTOR))


def apply_salvage(carried_gold: int, carried_loot_ids: list[str],
                  carried_xp: int, outcome: str, *, rng) -> tuple[int, list[str], int]:
    """Applica le frazioni di salvataggio dell'esito (J.21).

    Ritorna (gold, loot_ids_tenuti, xp). Gli item sono tenuti
    INDIVIDUALMENTE con probabilità pari alla frazione (selezione
    casuale, come da richiesta).
    """
    frac = SALVAGE.get(outcome) or SALVAGE["failed"]
    gold = int(round(int(carried_gold or 0) * frac["gold"]))
    if frac["items"] >= 1.0:
        kept = list(carried_loot_ids or [])
    else:
        kept = [i for i in (carried_loot_ids or [])
                if rng.random() < frac["items"]]
    xp = int(round(int(carried_xp or 0) * frac["xp"]))
    if outcome == "completed":
        xp = int(round(xp * (1.0 + COMPLETION_XP_BONUS)))
    return gold, kept, xp


__all__ = [
    "ROOMS_MODE_ENABLED",
    "ROOMS_PILOT_SLUGS",
    "ROOM_BLUEPRINTS",
    "ROOM_CHANCE_MODIFIER",
    "REST_CHANCE_BONUS",
    "REST_DURATION_FACTOR",
    "AUTO_DURATION_FACTOR",
    "DECISION_DEADLINE_SECONDS",
    "SALVAGE",
    "COMPLETION_XP_BONUS",
    "rooms_mode_for_dungeon",
    "build_rooms_snapshot",
    "build_auto_route_snapshot",
    "auto_route_duration_seconds",
    "resolve_fork",
    "iter_paths",
    "apply_salvage",
]
