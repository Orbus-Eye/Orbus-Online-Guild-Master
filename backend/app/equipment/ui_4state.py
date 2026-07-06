"""
🔒 R18.4.followup — UI 4-State Item Compatibility Activation — CLOSED & SEALED
R18.4.followup CLOSED & SEALED
DO NOT MODIFY. SHA256 verified in /app/backend/tests/backend_r18_4_sealed_integrity_test.py

R18.4.followup Phase B — UI 4-state compatibility derivation helper.

Modulo READ-ONLY che deriva `compatibility_state` + `reason_code` per un pair
(adventurer, item) sulla base dei metadata R18.4 già applicati:
    - item.item_binding_policy ∈ {"hard", "soft", "universal"}
    - item.required_class_optional (per policy=hard)
    - item.recommended_classes / class_tags (per policy=soft)
    - adventurer.class_slug (legacy EN)

Governance:
    - Zero DB writes
    - Zero runtime enforcement change (no gate su equip)
    - Solo derivazione read-side per UI 4-state
    - Backward-compat con compatibility.py esistente (non lo modifica)

Enum locked B.SQ (Phase B PM decisions):
    compatibility_state: "blocked" | "not_recommended" | "recommended" | "universal"
    reason_code:         "universal_item" | "class_recommended"
                       | "class_mismatch_soft" | "class_mismatch_hard"
                       | "slot_missing"
"""
from __future__ import annotations

from typing import Any


VALID_COMPATIBILITY_STATES: frozenset[str] = frozenset({
    "blocked", "not_recommended", "recommended", "universal",
})

VALID_REASON_CODES: frozenset[str] = frozenset({
    "universal_item", "class_recommended",
    "class_mismatch_soft", "class_mismatch_hard", "slot_missing",
})


def _tags_lower(item: dict, field: str) -> set[str]:
    """Extract list-of-strings field lowercased. Returns empty set if missing."""
    raw = item.get(field) or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(x).strip().lower() for x in raw if x}


def derive_ui_4state(adventurer: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    """Deriva UI 4-state signals per (adventurer, item).

    Returns dict con:
        compatibility_state: str (enum locked)
        can_equip:           bool
        recommended_for_class: bool
        is_universal:        bool
        reason_code:         str (enum locked)
        item_binding_policy: str (raw pass-through)
        slot_type:           str | None (raw pass-through)

    Precedenza derivation (SQ6 + B.SQ):
        1. item_binding_policy == "universal" → universal state
        2. slot_type missing on equipable item_type → slot_missing edge case
        3. item_binding_policy == "hard":
           a. class matches (required_class_optional o class_tags o recommended)
              → recommended state
           b. class mismatch → blocked state
        4. item_binding_policy == "soft":
           a. class in recommended_classes/class_tags → recommended state
           b. else → not_recommended state
    """
    cls_slug = (
        adventurer.get("class_slug")
        or (adventurer.get("class_name") or "").lower()
        or ""
    )
    cls_slug = cls_slug.strip().lower()

    policy = (item.get("item_binding_policy") or "").strip().lower()
    slot_type = item.get("slot_type")
    item_type = (item.get("item_type") or "").strip().lower()
    equipable_types = {"weapon", "armor", "accessory", "shield"}

    is_universal_derived = (policy == "universal")

    # ── 1. Universal — highest priority ───────────────────────────────────
    if is_universal_derived:
        return {
            "compatibility_state": "universal",
            "can_equip": True,
            "recommended_for_class": True,
            "is_universal": True,
            "reason_code": "universal_item",
            "item_binding_policy": policy,
            "slot_type": slot_type,
        }

    # ── 2. Edge case: equipable item senza slot_type ─────────────────────
    if item_type in equipable_types and not slot_type:
        return {
            "compatibility_state": "blocked",
            "can_equip": False,
            "recommended_for_class": False,
            "is_universal": False,
            "reason_code": "slot_missing",
            "item_binding_policy": policy,
            "slot_type": slot_type,
        }

    # Extract class match hints
    required_class = (item.get("required_class_optional") or "").strip().lower()
    class_tags = _tags_lower(item, "class_tags")
    recommended_classes = _tags_lower(item, "recommended_classes")

    class_in_recommended = (
        cls_slug in class_tags or cls_slug in recommended_classes
    )

    # ── 3. Hard policy ─────────────────────────────────────────────────
    if policy == "hard":
        # a. Matches required_class OR in recommended/class_tags
        if required_class:
            matches = (cls_slug == required_class)
        else:
            matches = class_in_recommended
        if matches:
            return {
                "compatibility_state": "recommended",
                "can_equip": True,
                "recommended_for_class": True,
                "is_universal": False,
                "reason_code": "class_recommended",
                "item_binding_policy": policy,
                "slot_type": slot_type,
            }
        else:
            return {
                "compatibility_state": "blocked",
                "can_equip": False,
                "recommended_for_class": False,
                "is_universal": False,
                "reason_code": "class_mismatch_hard",
                "item_binding_policy": policy,
                "slot_type": slot_type,
            }

    # ── 4. Soft policy (default per catalog) ──────────────────────────
    if class_in_recommended:
        return {
            "compatibility_state": "recommended",
            "can_equip": True,
            "recommended_for_class": True,
            "is_universal": False,
            "reason_code": "class_recommended",
            "item_binding_policy": policy,
            "slot_type": slot_type,
        }
    return {
        "compatibility_state": "not_recommended",
        "can_equip": True,
        "recommended_for_class": False,
        "is_universal": False,
        "reason_code": "class_mismatch_soft",
        "item_binding_policy": policy,
        "slot_type": slot_type,
    }


__all__ = [
    "derive_ui_4state",
    "VALID_COMPATIBILITY_STATES",
    "VALID_REASON_CODES",
]
