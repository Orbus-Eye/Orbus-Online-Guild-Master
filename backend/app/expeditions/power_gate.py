"""FASE 2.2 (2026-08-08) — Gate d'ingresso dungeon a POTERE del gruppo.

Sostituisce il level-gate (`enforce_min_adventurer_level`) sui dungeon:
l'accesso non dipende più dal livello dei singoli avventurieri ma dal
potere totale della squadra che entra. Vedi
memory/fase2_design_bilanciamento.md §5.

Regola: team_power ≥ ⌈POWER_GATE_RATIO × recommended_power⌉ (60%),
che sulla curva logistica equivale a ~14% di probabilità: la run
azzardata resta possibile, quella assurda no.

Error contract (HTTP 423 — Locked, stessa famiglia del vecchio gate):

    {
        "code": "team.power_too_low",
        "source": "<expedition.dispatch|expedition.preview>",
        "team_power": <int>,
        "required_team_power": <int>,
        "recommended_power": <int>,
        "user_message": "…in italiano…"
    }

I raid NON usano questo modulo (mantengono i loro gate attuali).
"""
from __future__ import annotations

import math

from fastapi import HTTPException

from app.shared.constants import POWER_GATE_RATIO


def required_team_power_for(dungeon: dict) -> int:
    """Soglia minima di potere squadra per entrare nel dungeon."""
    rec = max(1, int(dungeon.get("recommended_power") or 1))
    return int(math.ceil(POWER_GATE_RATIO * rec))


def enforce_min_team_power(
    team_power: int,
    dungeon: dict,
    *,
    source: str,
) -> None:
    """Raise 423 se il potere squadra è sotto la soglia del dungeon."""
    required = required_team_power_for(dungeon)
    power = int(team_power or 0)
    if power >= required:
        return
    import logging
    logging.getLogger("orbus.power_gate").info(
        "power_gate.blocked source=%s team_power=%d required=%d slug=%s",
        source, power, required, dungeon.get("slug") or "-",
    )
    raise HTTPException(
        status_code=423,
        detail={
            "code": "team.power_too_low",
            "source": source,
            "team_power": power,
            "required_team_power": required,
            "recommended_power": int(dungeon.get("recommended_power") or 0),
            "dungeon_slug": dungeon.get("slug"),
            "user_message": (
                f"La squadra ha potere {power}, ma per entrare servono "
                f"almeno {required} (il dungeon consiglia "
                f"{int(dungeon.get('recommended_power') or 0)}). "
                "Potenzia gli avventurieri o migliora l'equipaggiamento."
            ),
        },
    )


__all__ = ["required_team_power_for", "enforce_min_team_power"]
