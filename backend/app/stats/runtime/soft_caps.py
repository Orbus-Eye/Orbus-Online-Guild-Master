"""RT2-A · Intelligence soft-cap function.

Funzione pura `effective_intelligence(x)` conforme al verdetto RT1/P0Q10:

- se `x <= 100` → `x`
- se `x >  100` → `100 + (x - 100) * 0.5`

Precisione interna: 4 decimali (Decimal per determinismo).
Rounding intermedio: NONE (nessuno).
Display esposto dall'API pubblica di questo modulo: 1 decimale.
Final derived-power rounding (esterno al modulo): ROUND_HALF_UP.

Casi boundary OBBLIGATORI (verificati nel test suite):
    99  → 99.0
    100 → 100.0
    101 → 100.5
    105 → 102.5
    200 → 150.0

Gestione input:
- input `None` → treat as zero
- input negativo → clamp a 0 (regola RT2-A "negative final nominal stat → 0")
- input non numerico → `SoftCapError` (validation error)
"""
from __future__ import annotations

from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import Union

INTELLIGENCE_SOFT_CAP: int = 100
POST_CAP_EFFECTIVE_RETURN: Decimal = Decimal("0.5")
INTERNAL_PRECISION_DECIMALS: int = 4
DISPLAY_PRECISION_DECIMALS: int = 1

# Isola contesto Decimal locale (thread-safe: getcontext() è thread-local).
# Non alteriamo globale del processo per non impattare altri moduli.
_QUANTIZE_INTERNAL = Decimal(10) ** -INTERNAL_PRECISION_DECIMALS
_QUANTIZE_DISPLAY = Decimal(10) ** -DISPLAY_PRECISION_DECIMALS


class SoftCapError(ValueError):
    """Sollevato su input non numerico."""


NumericIn = Union[int, float, Decimal, str, None]


def _to_decimal(x: NumericIn) -> Decimal:
    if x is None:
        return Decimal(0)
    if isinstance(x, Decimal):
        return x
    try:
        return Decimal(str(x))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise SoftCapError(f"non-numeric input: {x!r}") from exc


def effective_intelligence(x: NumericIn) -> Decimal:
    """Ritorna il valore Intelligence effettivo post-soft-cap.

    Ritorna Decimal con precisione interna 4 decimali. Il chiamante può
    quantizzare per display via `format_display(...)`. Puro, deterministic.

    :raises SoftCapError: se `x` non è numerico.
    """
    d = _to_decimal(x)
    if d < Decimal(0):
        d = Decimal(0)  # clamp negative → 0 (RT2-A rule)
    cap = Decimal(INTELLIGENCE_SOFT_CAP)
    if d <= cap:
        result = d
    else:
        surplus = d - cap
        result = cap + surplus * POST_CAP_EFFECTIVE_RETURN
    # internal precision 4 decimals, no intermediate rounding beyond quantize
    return result.quantize(_QUANTIZE_INTERNAL, rounding=ROUND_HALF_UP)


def format_display(value: Decimal) -> str:
    """Formatta un valore effective per display (1 decimale, ROUND_HALF_UP)."""
    q = value.quantize(_QUANTIZE_DISPLAY, rounding=ROUND_HALF_UP)
    return f"{q:.1f}"


def soft_cap_applied(nominal: NumericIn) -> bool:
    """True se il nominal supera il soft cap."""
    return _to_decimal(nominal) > Decimal(INTELLIGENCE_SOFT_CAP)


def soft_cap_delta(nominal: NumericIn) -> Decimal:
    """Ritorna `nominal - effective` (>=0). Utile per diagnostica."""
    nom_d = _to_decimal(nominal)
    if nom_d < Decimal(0):
        nom_d = Decimal(0)
    eff = effective_intelligence(nom_d)
    return (nom_d - eff).quantize(_QUANTIZE_INTERNAL, rounding=ROUND_HALF_UP)


__all__ = [
    "INTELLIGENCE_SOFT_CAP",
    "POST_CAP_EFFECTIVE_RETURN",
    "INTERNAL_PRECISION_DECIMALS",
    "DISPLAY_PRECISION_DECIMALS",
    "SoftCapError",
    "effective_intelligence",
    "format_display",
    "soft_cap_applied",
    "soft_cap_delta",
]
