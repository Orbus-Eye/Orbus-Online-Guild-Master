"""RT2-B-2B-2-1 · Wiring feature-flag composition (6-conditions gate).

PM Message 170 §35 verbatim (`B2B2Q13`): the Drain runtime is guarded by a
COMPOSITE 6-conditions gate. All 6 must be simultaneously True for the Drain
path to execute any DB call, audit event, or state mutation.

Composition (verbatim):
    1. cdv_transient_state_enabled
    2. AND cdv_class_transitions_enabled
    3. AND cdv_drain_transitions_enabled
    4. AND authenticated user.is_test_user
    5. AND environment = localhost isolated
    6. AND Mongo target = allowlisted database

Flag Drain OFF (condition 3 False): **0 DB calls · 0 audit events · 0 mutations
(Drain path)**. Mark/Fragment paths already implemented are NOT disabled by the
sole Drain flag (surgical kill-switch).

This module exposes:
- `is_drain_gate_open(context)`: composite evaluation returning (bool, reason_code)
- `DrainGateContext`: dataclass describing gate inputs
- Utility gate reason codes for auditing.

PM normalization Message 170 §13: use `6-conditions gate` label. The term
"quintuple-gate" is DEPRECATED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from app.stats.runtime import feature_flags as _flags


# ═══════════════════════ Gate context ═══════════════════════
@dataclass(frozen=True)
class DrainGateContext:
    """Inputs to the 6-conditions composite gate.

    All fields SERVER-AUTHORITATIVE — never derivable from client headers/query/body.
    """

    is_test_user: bool  # trusted authenticated user.is_test_user
    environment_is_localhost_isolated: bool  # server-side environment inspection
    mongo_target_allowlisted: (
        bool  # target DB verified vs allowlist (orbus_r16_rt2b_test / *_it_*)
    )


@dataclass(frozen=True)
class EffectGateContext:
    """Server-authoritative inputs for the RT2-C-P2 five-condition gate."""

    is_test_user: bool
    environment_is_localhost_isolated: bool
    mongo_target_allowlisted: bool


# Reason codes emitted on gate rejection (audit correlation).
GATE_REASON_TRANSIENT_OFF: str = "TRANSIENT_STATE_DISABLED"
GATE_REASON_CLASS_OFF: str = "CLASS_TRANSITIONS_DISABLED"
GATE_REASON_DRAIN_OFF: str = "DRAIN_TRANSITIONS_DISABLED"
GATE_REASON_EFFECT_OFF: str = "ITEM_EFFECT_ENGINE_DISABLED"
GATE_REASON_TEST_USER: str = "TEST_USER_BOUNDARY_VIOLATION"
GATE_REASON_ENV: str = "ENVIRONMENT_NOT_LOCALHOST_ISOLATED"
GATE_REASON_DB: str = "DB_NOT_ALLOWLISTED"
GATE_REASON_OPEN: str = "GATE_OPEN"


def is_drain_gate_open(context: DrainGateContext) -> Tuple[bool, str]:
    """Evaluate the 6-conditions composite gate.

    Short-circuits on first failure. Reason codes are stable and audit-safe.

    Returns:
        (True, "GATE_OPEN") if all 6 conditions pass.
        (False, "<REASON_CODE>") on first failure.
    """
    # Condition 1: transient state master flag
    if not _flags.is_enabled("cdv_transient_state_enabled"):
        return False, GATE_REASON_TRANSIENT_OFF
    # Condition 2: class transitions flag (Mark/Fragment/Segment umbrella)
    if not _flags.is_enabled("cdv_class_transitions_enabled"):
        return False, GATE_REASON_CLASS_OFF
    # Condition 3: dedicated Drain flag (surgical kill-switch)
    if not _flags.is_enabled("cdv_drain_transitions_enabled"):
        return False, GATE_REASON_DRAIN_OFF
    # Condition 4: authenticated user.is_test_user
    if not context.is_test_user:
        return False, GATE_REASON_TEST_USER
    # Condition 5: environment = localhost isolated
    if not context.environment_is_localhost_isolated:
        return False, GATE_REASON_ENV
    # Condition 6: Mongo target = allowlisted database
    if not context.mongo_target_allowlisted:
        return False, GATE_REASON_DB
    return True, GATE_REASON_OPEN


def is_effect_gate_open(context: EffectGateContext) -> Tuple[bool, str]:
    """Evaluate the RT2-C-P2 five-condition effect integration gate.

    The generic engine is intentionally independent from CdV class/drain
    switches. CdV consumer hooks have their own reserved kill-switch and are
    not activated in P2.
    """

    if not _flags.is_enabled("cdv_transient_state_enabled"):
        return False, GATE_REASON_TRANSIENT_OFF
    if not _flags.is_enabled("item_effect_engine_enabled"):
        return False, GATE_REASON_EFFECT_OFF
    if context.is_test_user is not True:
        return False, GATE_REASON_TEST_USER
    if context.environment_is_localhost_isolated is not True:
        return False, GATE_REASON_ENV
    if context.mongo_target_allowlisted is not True:
        return False, GATE_REASON_DB
    return True, GATE_REASON_OPEN


def gate_snapshot() -> dict:
    """Diagnostic snapshot of the 3 flag conditions (not the runtime context).

    Runtime conditions 4-6 depend on request-scoped state and are NOT part of
    this snapshot. Only used for observability / test introspection.
    """
    return {
        "cdv_transient_state_enabled": _flags.is_enabled("cdv_transient_state_enabled"),
        "cdv_class_transitions_enabled": _flags.is_enabled(
            "cdv_class_transitions_enabled"
        ),
        "cdv_drain_transitions_enabled": _flags.is_enabled(
            "cdv_drain_transitions_enabled"
        ),
    }


def effect_gate_snapshot() -> dict:
    """Read-only snapshot of the two flag conditions in the effect gate."""

    return {
        "cdv_transient_state_enabled": _flags.is_enabled("cdv_transient_state_enabled"),
        "item_effect_engine_enabled": _flags.is_enabled("item_effect_engine_enabled"),
    }


__all__ = [
    "DrainGateContext",
    "EffectGateContext",
    "is_drain_gate_open",
    "is_effect_gate_open",
    "gate_snapshot",
    "effect_gate_snapshot",
    "GATE_REASON_TRANSIENT_OFF",
    "GATE_REASON_CLASS_OFF",
    "GATE_REASON_DRAIN_OFF",
    "GATE_REASON_EFFECT_OFF",
    "GATE_REASON_TEST_USER",
    "GATE_REASON_ENV",
    "GATE_REASON_DB",
    "GATE_REASON_OPEN",
]
