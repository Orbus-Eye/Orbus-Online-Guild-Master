"""ROUND 16.5.4c — ADJ-1 shared rarity canonicalizer.

Regola unica per la forma canonica delle rarità degli item nel catalog.
Storicamente convivevano forme miste (es. `Legendary` e `legendary`
sullo stesso schema), causando bug su filtri/sort case-sensitive.

La forma canonica è **Capitalized**:
  `Common`, `Uncommon`, `Rare`, `Epic`, `Legendary`, `Unique`.

Uso:
    from app.shared.rarity import canonicalize_rarity, CANONICAL_RARITIES

    canonicalize_rarity("legendary")  # → "Legendary"
    canonicalize_rarity("EPIC")       # → "Epic"
    canonicalize_rarity("  Rare  ")   # → "Rare"
    canonicalize_rarity(None)         # → None
    canonicalize_rarity("weird")      # → None (non canonical, lasciata al chiamante)

`canonicalize_rarity` **non solleva mai**. In caso di input non
riconoscibile ritorna None; il chiamante decide se rifiutare l'input
(seed/import path) o preservare il valore originale (read path).
"""
from __future__ import annotations

CANONICAL_RARITIES: tuple[str, ...] = (
    "Common", "Uncommon", "Rare", "Epic", "Legendary", "Unique",
)

_LOWER_TO_CANONICAL: dict[str, str] = {r.lower(): r for r in CANONICAL_RARITIES}


def canonicalize_rarity(value):
    """Normalizza `value` alla forma Capitalized canonica, o None."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    if not key:
        return None
    return _LOWER_TO_CANONICAL.get(key)


__all__ = ["canonicalize_rarity", "CANONICAL_RARITIES"]
