"""RT2-A · Canonical IT ↔ runtime stat bridge.

Funzione pura, side-effect free. Nessuna dipendenza da DB o altre risorse.

Mappa i nomi italiani delle statistiche (documentazione player-facing e i18n)
verso i nomi runtime interni usati dai modelli adventurer / equipment nel codice
attuale. Sorgente di verità per le statistiche runtime attive nel gioco:

    strength, agility, intellect, endurance, faith

Deriva dalla catena `IS2-A` (LIVE_STATS_ATOMIC) via `app.core.stat_role_registry`
(unwired · read-only). Qui NON importiamo il registry runtime per evitare side
effects; le costanti sono replicate letteralmente e verificate a test-time.

Alias supportati (case-insensitive):
- Forza / Vigore / Potenza → strength
- Destrezza / Agilità / Agility → agility
- Intelligenza / Intelletto / Volontà → intellect
- Costituzione / Resistenza / Endurance → endurance
- Fede / Faith / Spirito → faith

Comportamento su chiave sconosciuta: solleva `StatBridgeError` (validation error).
NON logga né effettua chiamate esterne.
"""
from __future__ import annotations

from typing import Final

# ─── Constants (locked via IS2-A LIVE_STATS_ATOMIC) ────────────────────
RUNTIME_STATS: Final[tuple[str, ...]] = (
    "strength",
    "agility",
    "intellect",
    "endurance",
    "faith",
)

# Italian → runtime mapping (case-insensitive lookup via _normalize)
# Deriva dalle sezioni P2B-RT1 canonical bridge. Alias inclusivi per resilienza
# lato input; il target runtime resta la 5-tupla `RUNTIME_STATS`.
_IT_TO_RUNTIME_RAW: Final[dict[str, str]] = {
    # strength
    "forza": "strength",
    "vigore": "strength",
    "potenza": "strength",
    "strength": "strength",
    # agility
    "destrezza": "agility",
    "agilità": "agility",
    "agilita": "agility",
    "agility": "agility",
    # intellect
    "intelligenza": "intellect",
    "intelletto": "intellect",
    "volontà": "intellect",
    "volonta": "intellect",
    "saggezza": "intellect",
    "intellect": "intellect",
    # endurance
    "costituzione": "endurance",
    "resistenza": "endurance",
    "endurance": "endurance",
    # faith
    "fede": "faith",
    "spirito": "faith",
    "carisma": "faith",
    "faith": "faith",
}


class StatBridgeError(ValueError):
    """Sollevato su chiave statistica sconosciuta."""


def _normalize(name: str) -> str:
    return name.strip().lower()


def to_runtime(it_or_runtime_name: str) -> str:
    """Restituisce il nome runtime canonico dato un nome IT o runtime.

    :raises StatBridgeError: se la chiave non è mappata.
    """
    key = _normalize(it_or_runtime_name)
    try:
        return _IT_TO_RUNTIME_RAW[key]
    except KeyError as exc:
        raise StatBridgeError(
            f"unknown stat name: {it_or_runtime_name!r}"
        ) from exc


def is_runtime_stat(name: str) -> bool:
    """True se `name` è un nome runtime canonico."""
    return _normalize(name) in RUNTIME_STATS


def known_it_aliases() -> tuple[str, ...]:
    """Ritorna la tupla ordinata degli alias IT/runtime supportati.

    Utile per test di completezza e diagnostica. Puro.
    """
    return tuple(sorted(_IT_TO_RUNTIME_RAW.keys()))


__all__ = [
    "RUNTIME_STATS",
    "StatBridgeError",
    "to_runtime",
    "is_runtime_stat",
    "known_it_aliases",
]
