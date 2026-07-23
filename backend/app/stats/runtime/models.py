"""RT2-A · Effective-stat result model + Loadout snapshot (immutable).

Modelli in-memory a vita breve. NON persistenti (no DB). NON esposti dall'API
pubblica. Costruiti tramite `runtime_evaluator.evaluate_runtime_stats(...)`.

Regole (P0Q02 verbatim):
- Snapshot immutable dopo `__init__`.
- NON salvato come stato persistente del personaggio.
- NON aggiornato da equip/unequip successivi.
- Può esistere nel contesto runtime già usato dalla spedizione.
- Se serve nuova persistenza cross-request → STOP `PERSISTENCE_BASELINE_CONFLICT`.

Snapshot version costante: `1` (bump solo su schema-breaking change ratificato PM).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping

SNAPSHOT_VERSION: int = 1


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EffectiveStatResult:
    """Risultato del calcolo statistica RT2-A (side-effect free).

    Campi obbligatori per contract §2 item 6:
      - nominal_stats: dict runtime_stat → int (pre soft-cap)
      - effective_stats: dict runtime_stat → Decimal (post soft-cap, precisione 4)
      - soft_cap_applied: True se soft cap Int è scattato
      - soft_cap_delta: Decimal = nominal_intelligence - effective_intelligence (>=0)
      - evaluation_duration_ns: int
      - reason_code: str (diagnostica)
    """

    nominal_stats: dict[str, int]
    effective_stats: dict[str, Decimal]
    soft_cap_applied: bool
    soft_cap_delta: Decimal
    evaluation_duration_ns: int
    reason_code: str


@dataclass(frozen=True)
class LoadoutSnapshot:
    """Snapshot immutabile del loadout all'avvio spedizione.

    Campi minimi (P0Q02 §20.3 verbatim). NON persistente cross-request.
    """

    adventurer_id: str
    expedition_id: str
    base_stats: dict[str, int]
    equipment_derived_flat_stats: dict[str, int]
    permanent_modifiers: dict[str, int]
    temporary_modifiers_at_start: dict[str, int]
    nominal_stats: dict[str, int]
    effective_stats: dict[str, Decimal]
    soft_cap_result: bool
    source_item_blueprint_list: tuple[str, ...]
    snapshot_version: int = SNAPSHOT_VERSION
    created_at: str = field(default_factory=_utc_now_iso)

    def to_diagnostic_dict(self) -> dict[str, Any]:
        """Rappresentazione diagnostica del snapshot (audit/debug only).

        NON esporre al client. Loadout NON inclusa in forma completa: solo
        blueprint IDs e stat aggregate.
        """
        return {
            "adventurer_id": self.adventurer_id,
            "expedition_id": self.expedition_id,
            "snapshot_version": self.snapshot_version,
            "soft_cap_result": self.soft_cap_result,
            "created_at": self.created_at,
            "nominal_intelligence": int(self.nominal_stats.get("intellect", 0)),
            "effective_intelligence": float(
                self.effective_stats.get("intellect", Decimal(0))
            ),
            "blueprint_count": len(self.source_item_blueprint_list),
        }


__all__ = [
    "SNAPSHOT_VERSION",
    "EffectiveStatResult",
    "LoadoutSnapshot",
]
