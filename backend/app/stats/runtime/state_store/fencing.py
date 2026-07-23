"""RT2-B-1A · Fencing token validation (pure logic, no I/O).

Il fencing token è un intero monotonic che aumenta ad OGNI nuova acquisizione
valida della lease (verdict PM B0Q02 + B0Q08). Il rinnovo (`renew_writer_lease`)
preserva il token corrente. La violazione del fencing è la difesa primaria
contro writer stale che tentano di mutare dopo essersi sospesi/partizionati.

Regole invarianti:
- Un writer con `fencing_token = X` NON può mutare se lo state document ha
  `fencing_token > X`.
- Ogni `reserve_writer` incrementa `fencing_token` di 1.
- `renew_writer_lease` NON incrementa `fencing_token`.
- Il clock applicativo NON è sufficiente a decidere validità della lease:
  la verifica passa SEMPRE attraverso la mutation atomica store-side.

Questo modulo esporta funzioni pure di supporto per gli adapter. Non fa I/O.
"""
from __future__ import annotations

from typing import Optional


def validate_fencing_match(expected: int, current: int) -> bool:
    """True se `expected == current`. False altrimenti (STALE_WRITER).

    Preconditions:
        entrambi interi ≥ 0.

    Returns:
        True su match. False su mismatch.
    """
    if not isinstance(expected, int) or not isinstance(current, int):
        return False
    if expected < 0 or current < 0:
        return False
    return expected == current


def next_fencing_token(current: Optional[int]) -> int:
    """Calcola il fencing_token successivo per una NUOVA acquisizione lease.

    - `current is None` → 1 (prima lease su documento appena creato).
    - `current >= 0` → `current + 1`.

    Non usato per renewal (che preserva il token corrente).
    """
    if current is None:
        return 1
    if not isinstance(current, int) or current < 0:
        raise ValueError(f"invalid current fencing_token: {current!r}")
    return current + 1


def validate_state_version_match(expected: int, current: int) -> bool:
    """True se `expected == current`. False altrimenti (STATE_VERSION_CONFLICT).

    Preconditions:
        entrambi interi ≥ 1 (initial state_version = 1 per B0Q04).
    """
    if not isinstance(expected, int) or not isinstance(current, int):
        return False
    if expected < 1 or current < 1:
        return False
    return expected == current


def next_state_version(current: int) -> int:
    """Incrementa `state_version` di 1 (monotonic invariant B0Q04)."""
    if not isinstance(current, int) or current < 1:
        raise ValueError(f"invalid current state_version: {current!r}")
    return current + 1
