"""R18.3d — Stat/Role Mapping Registry loader (READ-ONLY, UNWIRED).

═══════════════════════════════════════════════════════════════════════
UNWIRED MODULE — DO NOT IMPORT FROM RUNTIME CODE PATHS WITHOUT NEW PM GO
═══════════════════════════════════════════════════════════════════════

Purpose (per PM Q4 Phase B decision):
  Registry `/app/memory/r18_3d_stat_role_mapping_registry.json` is a
  DOCUMENTAL + ADMIN-INTROSPECTION resource. `adventurer_classes` remains
  the source-of-truth for runtime primary_stat/role/base_*.

  This module exposes a read-only loader for the registry file. It is
  intentionally NOT imported anywhere at runtime (auto-equip, xp_modifier,
  combat resolvers, recruitment, sorting, matchmaking must NOT depend on
  this module).

  Only test suites and future admin endpoints (post R18.3d.v2 PM GO) may
  import from this module.

Design constraints (PM Phase B lock):
  * No mutation API — only load & introspect
  * No import from any orbus runtime module (avoid side-effects)
  * fail-fast validation ONLY when explicitly invoked (via
    `validate_registry_or_raise()`); startup path stays untouched
  * `get_stat_role_mapping()` is UNWIRED — callers must be new admin
    endpoints or tests, never combat/equip/xp code paths

Author: e1_dev (R18.3d Phase B, 2026-07-05)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

REGISTRY_PATH = Path("/app/memory/r18_3d_stat_role_mapping_registry.json")

# Locked values from PM Phase B decisions.
LIVE_STATS_ATOMIC = ("strength", "agility", "intellect", "endurance", "faith")
LIVE_ROLES_ATOMIC = ("Tank", "DPS", "Healer")
DESIGN_STAT_MAPPING_6_TO_5 = {
    "Forza": "strength",
    "Destrezza": "agility",
    "Costituzione": "endurance",
    "Intelligenza": "intellect",
    "Saggezza": "intellect",
    "Carisma": "faith",
}

# Fields authorized for future admin metadata apply (Phase B3).
SAFE_METADATA_FIELDS = (
    "role_display_it",
    "class_role_tags",
    "design_primary_stat_it",
    "design_secondary_stats_it",
    "stat_role_registry_source_round",
)

# Fields the registry MUST NEVER be used to overwrite in the DB.
BLOCKED_RUNTIME_FIELDS = (
    "primary_stat",
    "secondary_stats",
    "role",
    "base_strength",
    "base_agility",
    "base_intellect",
    "base_endurance",
    "base_faith",
    "is_playable",
    "is_active",
    "is_canonical",
)


class RegistryValidationError(RuntimeError):
    """Raised when the registry file is missing, malformed, or violates
    the PM Phase B contract."""


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Load the registry JSON as a plain dict. Raises RegistryValidationError
    if the file is missing or JSON-invalid.

    NOTE: this function is READ-ONLY. It never writes to disk or DB.
    """
    if not path.exists():
        raise RegistryValidationError(f"registry missing at {path}")
    try:
        raw = path.read_bytes()
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RegistryValidationError(
            f"registry not valid JSON at {path}: {exc}"
        ) from exc


def compute_registry_sha256(path: Path = REGISTRY_PATH) -> str:
    """Compute the SHA256 of the registry file for audit trail."""
    if not path.exists():
        raise RegistryValidationError(f"registry missing at {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_registry_or_raise(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Structural validation. Invoke ONLY from tests or from an
    admin-triggered introspection endpoint — NEVER from startup path.

    Checks:
      * top-level keys present
      * stat_system.live_stats_5_atomic matches LIVE_STATS_ATOMIC
      * role_system.live_roles_atomic matches LIVE_ROLES_ATOMIC
      * design_stat_mapping_6_to_5_LOCKED matches DESIGN_STAT_MAPPING_6_TO_5
      * live_classes_18 present (list) with class_slug keys
      * canonical_design_only_16 present (list)
      * safe_metadata_fields_apply_scope.fields_to_apply_via_set is a
        subset of SAFE_METADATA_FIELDS
      * blocked_fields_never_touch matches BLOCKED_RUNTIME_FIELDS or is
        a strict superset
    """
    reg = load_registry(path)

    required = [
        "meta",
        "stat_mapping_6_to_5",
        "role_system",
        "canonical_classes",
        "legacy_live_classes",
        "excluded_manifest_entries",
        "safe_metadata_fields_apply_scope",
    ]
    for k in required:
        if k not in reg:
            raise RegistryValidationError(f"registry missing top-level key: {k}")

    stats = tuple(reg["role_system"].get("live_roles_atomic") or ())
    if stats != LIVE_ROLES_ATOMIC:
        raise RegistryValidationError(
            f"live_roles_atomic mismatch: {stats} vs {LIVE_ROLES_ATOMIC}"
        )

    mapping_raw = reg.get("stat_mapping_6_to_5") or {}
    for design_it, live_expected in DESIGN_STAT_MAPPING_6_TO_5.items():
        got = (mapping_raw.get(design_it) or {}).get("live")
        if got != live_expected:
            raise RegistryValidationError(
                f"design_stat_mapping mismatch for {design_it}: {got} vs {live_expected}"
            )

    if not isinstance(reg["canonical_classes"], list) or len(reg["canonical_classes"]) != 27:
        raise RegistryValidationError(
            f"canonical_classes must be a list of exactly 27 entries, "
            f"got {len(reg['canonical_classes'])}"
        )

    if not isinstance(reg["legacy_live_classes"], list):
        raise RegistryValidationError("legacy_live_classes must be a list")

    scope = reg["safe_metadata_fields_apply_scope"]
    fields = tuple(scope.get("fields_to_apply_via_set") or ())
    for f in fields:
        if f not in SAFE_METADATA_FIELDS:
            raise RegistryValidationError(
                f"fields_to_apply_via_set contains non-SAFE field: {f}"
            )

    blocked = set(scope.get("blocked_fields_never_touch") or ())
    for f in BLOCKED_RUNTIME_FIELDS:
        if f not in blocked:
            raise RegistryValidationError(
                f"blocked_fields_never_touch missing runtime-critical field: {f}"
            )

    return reg


def get_stat_role_mapping(
    class_slug: str, path: Path = REGISTRY_PATH
) -> Optional[dict[str, Any]]:
    """UNWIRED helper — return the canonical registry entry for a given
    canonical `class_slug`, or None if not present. Callers: ONLY tests
    or admin endpoints.

    DO NOT invoke from auto-equip, xp_modifier, combat, sorting, recruitment,
    or matchmaking code paths. If a runtime consumer needs stat/role data,
    it MUST read from `adventurer_classes` collection (source-of-truth).
    """
    reg = load_registry(path)
    for entry in reg.get("canonical_classes", []):
        if entry.get("slug") == class_slug:
            return entry
    return None


__all__ = [
    "LIVE_STATS_ATOMIC",
    "LIVE_ROLES_ATOMIC",
    "DESIGN_STAT_MAPPING_6_TO_5",
    "SAFE_METADATA_FIELDS",
    "BLOCKED_RUNTIME_FIELDS",
    "RegistryValidationError",
    "load_registry",
    "compute_registry_sha256",
    "validate_registry_or_raise",
    "get_stat_role_mapping",
]
