"""ROUND 15 — Fase 2 / Task A: Equipment compatibility validator.
   ROUND 16.0 — Fase 2 / Task 2.3: Validator v2 — base class + specialization.

Server-authoritative compatibility check between an item and an
adventurer's class. Three severity levels:

    "block"   → hard incompatibility (mage in heavy plate, signature
                belonging to another class, etc.). The equip endpoint
                MUST return HTTP 400.
    "warning" → equippable but inefficient (e.g. rogue with a 2-handed
                weapon that lacks a stealth/finesse tag). The equip
                succeeds and the response carries `warning_it`.
    "ok"      → no issues.

Rules are data-driven from `items.*_tags` populated by
`round15_seed_item_tags.py` and `adventurer_classes.role_tags /
allowed_armor_tags / allowed_weapon_tags / preferred_item_tags`.

This module is intentionally a *pure function* — no DB access. The
caller (equip_item_service) loads the class document once and hands it
to the checker. Pure helpers stay trivial to unit-test.
"""

from __future__ import annotations

from app.adventurers.classless import is_explicit_classless_recruit

# Heavy-armour blacklist by class slug. These classes CAN NEVER equip
# heavy armour even if the seed tag map drifts — defence in depth.
# Round 16.0: includes the new `warlock` (caster) base class.
# Legacy `necromancer` kept for back-compat reads only (post-migration
# no adventurer carries that slug anymore).
NO_HEAVY_ARMOR_CLASSES = frozenset(
    {
        "mage",
        "necromancer",
        "priest",
        "druid",
        "bard",
        "warlock",
    }
)

# Arcane-weapon (staff/wand/grimoire) blacklist for non-caster classes.
# Legacy `berserker` / `assassin` kept for back-compat reads only.
NO_ARCANE_WEAPON_CLASSES = frozenset(
    {
        "warrior",
        "paladin",
        "berserker",
        "rogue",
        "ranger",
        "assassin",
        "monk",
    }
)

ARCANE_WEAPON_TAGS = frozenset({"staff", "wand", "arcane", "grimoire", "tome"})


def _tags(item: dict, field: str) -> list[str]:
    """Safe list-of-lower-string extractor; tolerates None / missing."""
    raw = item.get(field) or []
    return [str(t).lower() for t in raw if t]


def check_equip_compatibility(adventurer: dict, item: dict) -> dict:
    """Decide if an adventurer can wear an item.

    Args:
        adventurer: dict from `adventurers` collection (must carry
            `class_slug` or `class_name`; optionally `specialization_slug`).
        item: dict from `items` collection. Optional new field
            `specialization_unlocks: list[str]` is consulted when the
            base class is NOT in `class_tags`/`recommended_classes`.

    Returns:
        {
          "allowed": bool,
          "severity": "ok"|"warning"|"block",
          "reason_it": str,
          "reason_code": str,
        }
    """
    cls_slug = (
        adventurer.get("class_slug")
        or (adventurer.get("class_name") or "").lower()
        or ""
    )
    cls_slug = cls_slug.strip().lower()

    weapon_tags = set(_tags(item, "weapon_tags"))
    armor_tags = set(_tags(item, "armor_tags"))
    class_tags = set(_tags(item, "class_tags"))
    recommended = set(_tags(item, "recommended_classes"))
    is_universal = bool(item.get("is_universal"))
    required_class = (item.get("required_class_optional") or "").strip().lower()

    # ── 1. Hard requirement: signature / class-locked item ───────────────
    if required_class and required_class != cls_slug:
        return {
            "allowed": False,
            "severity": "block",
            "reason_code": "class_locked",
            "reason_it": (
                f"Questo oggetto è esclusivo della classe '{required_class}'. "
                f"Non può essere equipaggiato da un {cls_slug or 'altro'}."
            ),
        }

    # A newly recruited adventurer has no combat discipline until the
    # player explicitly chooses a Class Hall.  Only genuinely universal
    # trinkets and non-specialised utility categories may pass this layer.
    if is_explicit_classless_recruit(adventurer):
        utility_types = {"consumable", "material", "cosmetic"}
        item_type = (item.get("item_type") or "").strip().lower()
        if is_universal or item_type in utility_types:
            return {
                "allowed": True,
                "severity": "ok",
                "reason_code": "universal_classless",
                "reason_it": "Utilizzabile anche prima di scegliere una Sala di Classe.",
            }
        return {
            "allowed": False,
            "severity": "block",
            "reason_code": "class_required",
            "reason_it": (
                "Scegli prima una Sala di Classe: questa recluta non ha ancora "
                "la disciplina necessaria per equipaggiare l'oggetto."
            ),
        }

    # Universal accessories skip every other check.
    if is_universal:
        return {
            "allowed": True,
            "severity": "ok",
            "reason_code": "universal",
            "reason_it": "Accessorio universale.",
        }

    # ── 2. Heavy armour blacklist ───────────────────────────────────────
    if "heavy" in armor_tags and cls_slug in NO_HEAVY_ARMOR_CLASSES:
        return {
            "allowed": False,
            "severity": "block",
            "reason_code": "heavy_armor_forbidden",
            "reason_it": (
                "Questa classe non può indossare armatura pesante: "
                "la mobilità e la canalizzazione magica vengono compromesse."
            ),
        }

    # ── 3. Arcane weapon blacklist ──────────────────────────────────────
    if (weapon_tags & ARCANE_WEAPON_TAGS) and cls_slug in NO_ARCANE_WEAPON_CLASSES:
        return {
            "allowed": False,
            "severity": "block",
            "reason_code": "arcane_weapon_forbidden",
            "reason_it": (
                "Questa classe non sa canalizzare l'energia arcana attraverso "
                "uno strumento di questo tipo."
            ),
        }

    # FASE 9C — il ramo `specialization_unlocks` non esiste più: le
    # specializzazioni sono state rimosse. Un item legacy che ancora
    # dichiara spec_unlocks viene trattato coi soli check di classe
    # (e verrà ripulito dalla migration 9M).

    # ── 4. Soft warning: not in recommended_classes / class_tags ────────
    if recommended and cls_slug not in recommended:
        return {
            "allowed": True,
            "severity": "warning",
            "reason_code": "not_recommended_class",
            "reason_it": (
                "Equipaggiabile ma poco efficiente per questa classe. "
                "I bonus non sono allineati alla statistica primaria."
            ),
        }
    if class_tags and cls_slug not in class_tags:
        return {
            "allowed": True,
            "severity": "warning",
            "reason_code": "off_class_tags",
            "reason_it": (
                "Oggetto pensato per altre classi: i bonus non corrispondono "
                "al ruolo attuale dell'avventuriero."
            ),
        }

    # ── 5. All clear ────────────────────────────────────────────────────
    return {
        "allowed": True,
        "severity": "ok",
        "reason_code": "ok",
        "reason_it": "",
    }


__all__ = [
    "check_equip_compatibility",
    "NO_HEAVY_ARMOR_CLASSES",
    "NO_ARCANE_WEAPON_CLASSES",
    "ARCANE_WEAPON_TAGS",
]
