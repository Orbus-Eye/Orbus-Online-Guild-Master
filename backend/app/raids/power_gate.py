"""FASE 8B (2026-08-08) — Gate d'ingresso RAID a potere di squadra.

Allinea i raid alla filosofia dei dungeon (FASE 2.2/8A): l'accesso
dipende dal PWR combinato reale delle squadre, NON dal livello dei
singoli avventurieri. Il vecchio `enforce_min_adventurer_level` è
rimosso da start/preview; `min_adventurer_level` resta esposto come
fascia consigliata informativa.

I raid sono più severi dei dungeon: soglia al 75% del potere
consigliato (dungeon: 70%), su una curva già maggiorata del 15%
(RAID_CURVE, FASE 8A). Vedi memory/fase8_dungeon_difficulty_rebalance.md §5.
"""
from __future__ import annotations

import math

from fastapi import HTTPException

RAID_POWER_GATE_RATIO = 0.75


def raid_recommended_power(rd: dict) -> int:
    """Potere consigliato canonico del raid.

    1. RAID_CURVE (source of truth in codice, FASE 8A);
    2. fallback: `recommended_power_combined` del documento.
    """
    from app.shared.content_curve import RAID_CURVE
    canonical = RAID_CURVE.get(str(rd.get("slug") or ""))
    if canonical is not None:
        return int(canonical.recommended_power)
    return int(rd.get("recommended_power_combined") or 0)


def raid_required_team_power(rd: dict) -> int:
    """Soglia minima di potere combinato per entrare nel raid."""
    rec = max(1, raid_recommended_power(rd))
    return int(math.ceil(RAID_POWER_GATE_RATIO * rec))


def enforce_raid_min_power(team_power_combined: int, rd: dict, *,
                           source: str) -> None:
    """Raise 423 se il potere combinato è sotto la soglia del raid."""
    required = raid_required_team_power(rd)
    power = int(team_power_combined or 0)
    if power >= required:
        return
    import logging
    logging.getLogger("orbus.raids.power_gate").info(
        "raid_power_gate.blocked source=%s power=%d required=%d slug=%s",
        source, power, required, rd.get("slug") or "-",
    )
    raise HTTPException(
        status_code=423,
        detail={
            "code": "raid.power_too_low",
            "source": source,
            "team_power_combined": power,
            "required_team_power": required,
            "recommended_power": raid_recommended_power(rd),
            "raid_slug": rd.get("slug"),
            "user_message": (
                f"Le squadre hanno potere combinato {power}, ma per "
                f"questo raid servono almeno {required} (consigliato "
                f"{raid_recommended_power(rd)}). I raid perdonano meno "
                "dei dungeon: rinforza il roster prima di suonare la carica."
            ),
        },
    )


__all__ = [
    "RAID_POWER_GATE_RATIO",
    "raid_recommended_power",
    "raid_required_team_power",
    "enforce_raid_min_power",
]
