"""FASE 9 — Package del registry canonico delle classi."""
from app.classes.registry import (  # noqa: F401
    CANONICAL_ROLES,
    CLASS_REGISTRY,
    CLASS_ROLE_DPS,
    CLASS_ROLE_HEALER,
    CLASS_ROLE_TANK,
    ClassDefinition,
    LEGACY_CLASS_SLUG_ALIASES,
    ROLE_LABEL_IT,
    canonical_class_slug,
    class_role_for,
    member_role,
    normalize_role_value,
    registry_entry,
    role_counts,
    role_focus_stats,
)
