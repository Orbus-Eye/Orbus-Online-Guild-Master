"""FASE 8D (2026-08-08) — Raid a FASI (pilota: Veglia di Lunacaduta).

Un raid non è un dungeon più grosso: ha sezioni, un boss intermedio,
un evento rituale, un CHECKPOINT con scelta tattica e il boss finale.

Modello (ricalca le stanze dei dungeon, con differenze da raid):
  * le fasi avanzano AUTOMATICAMENTE (i raid durano ore): il timer
    `ends_at` rappresenta la fase corrente; la route /complete — già
    chiamata dal FE a timer scaduto — risolve la fase e arma la
    successiva;
  * l'unica pausa decisionale è il CHECKPOINT: scelta fra approccio
    prudente (+5 chance sulle fasi restanti) o assalto (−8, bottino
    maggiorato via outcome "victory" più probabile? no: fattore oro);
    deadline 24h → si sceglie la via prudente;
  * fallire una fase PRIMA del checkpoint = sconfitta (defeat);
    DOPO il checkpoint = ritirata con onore (partial): il checkpoint
    è un vero traguardo;
  * l'esito finale rientra nel flusso ricompense esistente
    (victory/partial/defeat → stessi reward, reagenti, item T6).

Risoluzione deterministica per fase: Random(f"{raid_id}:{idx}") —
replay-safe come il resto del modulo raid.

Flag: RAID_PHASES_ENABLED + RAID_PHASES_SLUGS.
"""
from __future__ import annotations

import random
from datetime import timedelta

RAID_PHASES_ENABLED = True
RAID_PHASES_SLUGS: frozenset[str] = frozenset({"moonfall-vigil"})

CHECKPOINT_DECISION_DEADLINE_SECONDS = 24 * 3600

# Modificatori di chance per tipo di fase (sul combined base).
PHASE_KIND_MODIFIER = {
    "approach": +5,
    "miniboss": -5,
    "checkpoint": 0,     # il checkpoint non si combatte
    "event": 0,
    "boss": -10,
}

CHECKPOINT_OPTIONS = (
    {
        "key": "rituale",
        "label_it": "Il Rituale di Purificazione",
        "description_it": (
            "Consacrare le armi al chiarore lunare: +5 alla riuscita "
            "delle fasi restanti."
        ),
        "chance_modifier": +5,
        "gold_factor": 1.0,
    },
    {
        "key": "assalto",
        "label_it": "L'Assalto Diretto",
        "description_it": (
            "Colpire prima che l'Araldo completi il rito: più rischio "
            "(−8), ma il santuario non farà in tempo a nascondere i "
            "suoi tesori (+25% oro)."
        ),
        "chance_modifier": -8,
        "gold_factor": 1.25,
    },
)

# Blueprint fasi del pilota. duration_share sul base_duration del raid.
PHASE_BLUEPRINTS: dict[str, list[dict]] = {
    "moonfall-vigil": [
        {
            "slug": "approccio", "name_it": "L'Approccio al Santuario",
            "kind": "approach", "duration_share": 0.15,
            "narrative_it": (
                "Quaranta gradini di pietra lunare, e ogni gradino "
                "canta sottovoce il nome di chi lo calpesta."
            ),
        },
        {
            "slug": "guardiani", "name_it": "I Guardiani della Veglia",
            "kind": "miniboss", "duration_share": 0.25,
            "narrative_it": (
                "Due colossi di marmo e luce: il boss intermedio della "
                "Veglia. Non dormono da tremila anni."
            ),
        },
        {
            "slug": "bivacco", "name_it": "Il Bivacco sotto la Luna",
            "kind": "checkpoint", "duration_share": 0.1,
            "narrative_it": (
                "Un momento di tregua. Da qui in poi, anche fallendo, "
                "nessuno tornerà a mani vuote: il checkpoint è vostro."
            ),
        },
        {
            "slug": "rito", "name_it": "Il Rito di Lunacaduta",
            "kind": "event", "duration_share": 0.2,
            "narrative_it": (
                "Il cielo si abbassa. La luna è TROPPO vicina, e il "
                "rito per farla cadere è già a metà."
            ),
        },
        {
            "slug": "araldo", "name_it": "L'Araldo della Luna Caduta",
            "kind": "boss", "duration_share": 0.3,
            "narrative_it": (
                "Indossa la luce lunare come un'armatura. Il boss "
                "finale della Veglia vi stava aspettando."
            ),
        },
    ],
}


def phases_mode_for_raid(rd: dict) -> bool:
    if not RAID_PHASES_ENABLED:
        return False
    return (rd.get("slug") or "").lower() in RAID_PHASES_SLUGS


def build_phases_snapshot(rd: dict, base_combined_chance: int) -> list[dict]:
    """Snapshot fasi congelato allo start (durate assolute + chance)."""
    slug = (rd.get("slug") or "").lower()
    blueprint = PHASE_BLUEPRINTS.get(slug) or []
    total_duration = int(rd.get("base_duration_seconds", 3600) or 3600)
    out = []
    for idx, phase in enumerate(blueprint):
        modifier = PHASE_KIND_MODIFIER.get(phase["kind"], 0)
        chance = max(5, min(100, int(base_combined_chance) + modifier))
        out.append({
            "idx": idx,
            "slug": phase["slug"],
            "name_it": phase["name_it"],
            "kind": phase["kind"],
            "narrative_it": phase["narrative_it"],
            "duration_seconds": max(
                30, int(round(total_duration * phase["duration_share"]))
            ),
            "chance": chance,
        })
    return out


def checkpoint_index(phases: list[dict]) -> int:
    """Indice della fase checkpoint (-1 se assente)."""
    for p in phases or []:
        if p.get("kind") == "checkpoint":
            return int(p.get("idx", -1))
    return -1


def phase_rng(raid_id: str, phase_idx: int) -> random.Random:
    """RNG deterministico per fase (replay-safe)."""
    return random.Random(f"{raid_id}:{phase_idx}")


def resolve_phase(phase: dict, raid_id: str,
                  bonus_modifier: int = 0) -> dict:
    """Risolve UNA fase (pure): checkpoint = sempre superato (non si
    combatte); altre fasi = roll deterministico vs chance ± bonus."""
    if phase.get("kind") == "checkpoint":
        return {"idx": phase["idx"], "slug": phase.get("slug"),
                "name_it": phase.get("name_it"), "kind": "checkpoint",
                "success": True, "roll": 0, "chance": 100}
    chance = max(5, min(100, int(phase.get("chance", 50)) + bonus_modifier))
    roll = phase_rng(raid_id, int(phase["idx"])).randint(1, 100)
    return {
        "idx": int(phase["idx"]),
        "slug": phase.get("slug"),
        "name_it": phase.get("name_it"),
        "kind": phase.get("kind"),
        "success": roll <= chance,
        "roll": roll,
        "chance": chance,
    }


def checkpoint_option(key: str) -> dict | None:
    for opt in CHECKPOINT_OPTIONS:
        if opt["key"] == key:
            return opt
    return None


__all__ = [
    "RAID_PHASES_ENABLED", "RAID_PHASES_SLUGS", "PHASE_BLUEPRINTS",
    "PHASE_KIND_MODIFIER", "CHECKPOINT_OPTIONS",
    "CHECKPOINT_DECISION_DEADLINE_SECONDS",
    "phases_mode_for_raid", "build_phases_snapshot", "checkpoint_index",
    "phase_rng", "resolve_phase", "checkpoint_option",
]
