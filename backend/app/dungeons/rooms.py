"""FASE 5 (2026-08-08) — Dungeon a stanze: blueprint e helper puri.

Le stanze sono AUTORATE in codice (come DUNGEON_LORE): niente migrazioni
DB. Il rollout è a pilota dietro flag: solo gli slug in
`ROOMS_PILOT_SLUGS` partono in modalità stanze; `ROOMS_MODE_ENABLED`
spegne tutto all'istante.

Tutte le funzioni qui sono PURE (nessun I/O) → unit-testabili.
Design completo: memory/fase5_design_dungeon_stanze.md
"""
from __future__ import annotations

# ── Feature flag & pilota ────────────────────────────────────────────────
ROOMS_MODE_ENABLED = True
ROOMS_PILOT_SLUGS: frozenset[str] = frozenset({
    "sewer-nest",       # tutorial 3p — onboarding al nuovo flusso
    "goblin-warrens",   # 5p base — pilota della linea principale
})

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

# Deadline della scelta: oltre → auto-continue (mai run bloccate).
DECISION_DEADLINE_SECONDS = 24 * 3600

# Frazioni di salvataggio per esito (oro / prob. per item / XP maturata).
SALVAGE = {
    "completed": {"gold": 1.0, "items": 1.0, "xp": 1.0},
    "escaped": {"gold": 0.5, "items": 0.5, "xp": 0.5},
    "failed": {"gold": 0.25, "items": 0.25, "xp": 0.4},
}
COMPLETION_XP_BONUS = 0.25  # +25% XP al completamento (premio vs fuga)


# ── Blueprint autorati (piloti) ──────────────────────────────────────────
# Campi: slug, name_it, kind, duration_share, gold_share, xp_share,
#        has_loot, narrative_it. Le share sommano a 1.0.
ROOM_BLUEPRINTS: dict[str, list[dict]] = {
    "sewer-nest": [
        {
            "slug": "cunicoli", "name_it": "I Cunicoli Allagati",
            "kind": "ambient", "duration_share": 0.3, "gold_share": 0.2,
            "xp_share": 0.3, "has_loot": False,
            "narrative_it": (
                "L'acqua putrida arriva alle ginocchia. Tra i tubi "
                "rotti qualcosa si muove nell'oscurità."
            ),
        },
        {
            "slug": "covo-ratti", "name_it": "Il Covo dei Ratti",
            "kind": "guard", "duration_share": 0.3, "gold_share": 0.3,
            "xp_share": 0.3, "has_loot": True,
            "narrative_it": (
                "Un tappeto di code e denti. I ratti giganti difendono "
                "il loro tesoro di rifiuti… e di monete perdute."
            ),
        },
        {
            "slug": "madre-nido", "name_it": "La Madre del Nido",
            "kind": "boss", "duration_share": 0.4, "gold_share": 0.5,
            "xp_share": 0.4, "has_loot": True,
            "narrative_it": (
                "Grande quanto un cavallo, cieca e furiosa: la Madre "
                "del Nido non lascerà passare nessuno."
            ),
        },
    ],
    "goblin-warrens": [
        {
            "slug": "posto-guardia", "name_it": "Il Posto di Guardia",
            "kind": "guard", "duration_share": 0.25, "gold_share": 0.2,
            "xp_share": 0.25, "has_loot": False,
            "narrative_it": (
                "Due sentinelle goblin sonnecchiano accanto a un gong "
                "d'allarme. Meglio non farlo suonare."
            ),
        },
        {
            "slug": "trappole", "name_it": "Il Corridoio delle Trappole",
            "kind": "ambient", "duration_share": 0.2, "gold_share": 0.15,
            "xp_share": 0.2, "has_loot": False,
            "narrative_it": (
                "Fili tesi, buche puntellate, secchi di pece sospesi: "
                "l'ingegneria goblin nel suo peggio."
            ),
        },
        {
            "slug": "sala-bottino", "name_it": "La Sala del Bottino",
            "kind": "treasure", "duration_share": 0.25, "gold_share": 0.3,
            "xp_share": 0.25, "has_loot": True,
            "narrative_it": (
                "Casse rubate alle carovane, ancora sigillate. I goblin "
                "non hanno capito quanto valgono."
            ),
        },
        {
            "slug": "re-goblin", "name_it": "La Corte del Re Goblin",
            "kind": "boss", "duration_share": 0.3, "gold_share": 0.35,
            "xp_share": 0.3, "has_loot": True,
            "narrative_it": (
                "Su un trono di ossa e lamiere siede il Re Goblin, con "
                "una corona rubata troppo grande per la sua testa."
            ),
        },
    ],
}

# Generatore di fallback per slug pilota senza blueprint autorato
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


def build_rooms_snapshot(dungeon: dict, base_chance: int) -> list[dict]:
    """Costruisce lo snapshot stanze congelato al dispatch.

    Ogni stanza riceve: durata assoluta, oro/XP assoluti (dalle share)
    e la probabilità di successo (chance base ± modificatore tipo,
    clamp [5, 100]).
    """
    slug = (dungeon.get("slug") or "").lower()
    blueprint = ROOM_BLUEPRINTS.get(slug) or _fallback_blueprint(dungeon)
    total_duration = int(dungeon.get("base_duration_seconds", 60) or 60)
    total_gold = int(dungeon.get("base_gold_reward", 0) or 0)
    total_xp = int(dungeon.get("base_xp_reward", 0) or 0)
    out = []
    for idx, room in enumerate(blueprint):
        modifier = ROOM_CHANCE_MODIFIER.get(room["kind"], 0)
        chance = max(5, min(100, int(base_chance) + modifier))
        out.append({
            "idx": idx,
            "slug": room["slug"],
            "name_it": room["name_it"],
            "kind": room["kind"],
            "narrative_it": room["narrative_it"],
            "has_loot": bool(room["has_loot"]),
            "duration_seconds": max(
                10, int(round(total_duration * room["duration_share"]))
            ),
            "gold": int(round(total_gold * room["gold_share"])),
            "xp": int(round(total_xp * room["xp_share"])),
            "chance": chance,
        })
    return out


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
    "DECISION_DEADLINE_SECONDS",
    "SALVAGE",
    "COMPLETION_XP_BONUS",
    "rooms_mode_for_dungeon",
    "build_rooms_snapshot",
    "apply_salvage",
]
