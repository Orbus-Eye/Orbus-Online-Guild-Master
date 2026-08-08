"""ROUND 16.5.4b — Auto-Equip class-aware, stat-aware, level-gated.

Given an adventurer, scans guild inventory and equips the best
compatible item per slot, honouring:
  * `check_equip_compatibility` (block → exclude, warning → penalty ×0.5)
  * `resolve_item_required_level` (item under-level → exclude)
  * class primary/secondary stat weighting from `adventurer_classes`
  * deterministic tie-break (fitness DESC, power_score DESC, id ASC)

Fitness formula (single source of truth):
    fitness = PRIMARY_WEIGHT   * item[f"{primary}_bonus"]
            + SECONDARY_WEIGHT * sum(item[f"{s}_bonus"] for s in secondaries)
            + POWER_WEIGHT     * item.power_score
            + STAT_TAG_BONUS   if primary in item.stat_tags else 0
    warning verdict → fitness *= WARNING_PENALTY

Item stat schema (canonical, verified in R16.5.4b audit):
  * strength_bonus, agility_bonus, intellect_bonus,
    endurance_bonus, faith_bonus, power_score  (all int)
  * class primary_stat values are: strength|agility|intellect|
    endurance|faith  (from adventurer_classes catalog). The pattern
    `f"{primary}_bonus"` resolves directly to the matching item field.
    No mapping table required.

Idempotency: a second invocation with the same inventory state yields
zero swaps (the newly-equipped item becomes the current best).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException

from app.audit.log import write_audit
from app.equipment.compatibility import check_equip_compatibility
from app.equipment.level_gate import resolve_item_required_level
from app.equipment.services import equip_item_service, unequip_item_service
from app.expeditions.formulas import item_equip_power
from app.shared.constants import EQUIPMENT_SLOTS, SLOT_TO_ITEM_TYPE

logger = logging.getLogger("orbus.equipment.auto_equip")

# ── Scoring weights (tunable, per R16.5.4b STEP 1 spec approval) ─────────
PRIMARY_WEIGHT = 3.0
SECONDARY_WEIGHT = 1.5
POWER_WEIGHT = 1.0
STAT_TAG_BONUS = 2.0
# ROUND 16.5.4b REOPEN #2 (2026-07-02) — PM decision Q2-b(iii): Auto-Equip
# SKIPS warning-severity items entirely (no penalty fallback). Only "ok"
# candidates enter the ranking. Manual equip is UNCHANGED. See sezione
# 19 di round1654b_final_report.md.
# (Legacy `WARNING_PENALTY = 0.5` constant removed — no longer applied.)


def _extract_it_message(http_exc: HTTPException, slot_it: str,
                       *, fallback: str) -> str:
    """ROUND 16.5.4c ADJ-3.c — estrai messaggio IT pulito da HTTPException.

    Contract dei service Orbus: `detail` è tipicamente
    `{"code": "...", "user_message": "…in italiano…"}`. Ritorna quel
    messaggio se disponibile, altrimenti `fallback`. NON stringifica mai
    `type(exc).__name__` — quel comportamento leakava "HTTPException"
    nel report del player (bug del REOPEN #2 R16.5.4b).
    """
    detail = getattr(http_exc, "detail", None)
    if isinstance(detail, dict):
        user_msg = detail.get("user_message") or detail.get("message")
        if user_msg and isinstance(user_msg, str):
            return f"{slot_it}: {user_msg}"
    elif isinstance(detail, str) and detail.strip():
        return f"{slot_it}: {detail.strip()}"
    return fallback


def _stat_bonus(item: dict, stat_name: str) -> int:
    """Read the canonical `{stat}_bonus` int field. Missing / null → 0.

    NOTE: `adventurer_classes.primary_stat` values are already lowercase
    canonical stat names (strength / agility / intellect / endurance /
    faith). The item schema mirrors those names verbatim with a `_bonus`
    suffix, so no translation table is needed.
    """
    return int(item.get(f"{stat_name}_bonus", 0) or 0)


def _compute_fitness(
    item: dict, primary: str, secondaries: list[str]
) -> float:
    primary_score = _stat_bonus(item, primary) * PRIMARY_WEIGHT
    secondary_score = sum(
        _stat_bonus(item, s) for s in (secondaries or [])
    ) * SECONDARY_WEIGHT
    power_score_v = int(item.get("power_score", 0) or 0) * POWER_WEIGHT
    stat_tags = item.get("stat_tags") or []
    tag_bonus = STAT_TAG_BONUS if primary in stat_tags else 0.0
    return float(primary_score + secondary_score + power_score_v + tag_bonus)


def _stat_delta(
    old_item: dict | None, new_item: dict, primary: str,
) -> dict[str, int]:
    """Compute per-stat delta between two items using canonical bonus fields.

    Includes only non-zero deltas. Always includes `power` (from
    `power_score`) when it differs — this is what the FE displays as
    "+X Power".
    """
    out: dict[str, int] = {}
    stat_keys = (
        "strength", "agility", "intellect", "endurance", "faith",
    )
    old = old_item or {}
    for k in stat_keys:
        d = _stat_bonus(new_item, k) - _stat_bonus(old, k)
        if d:
            out[k] = d
    power_delta = (
        int(new_item.get("power_score", 0) or 0)
        - int(old.get("power_score", 0) or 0)
    )
    if power_delta:
        out["power"] = power_delta
    # Order: primary first (best FE readability), then others alphabetical.
    ordered: dict[str, int] = {}
    if primary in out:
        ordered[primary] = out.pop(primary)
    for k in sorted(out.keys()):
        ordered[k] = out[k]
    return ordered


def _format_stat_delta(delta: dict[str, int]) -> str:
    """Compact stat delta rendering: '+5 Int, +2 End, +8 Power'."""
    if not delta:
        return ""
    labels = {
        "strength": "Str", "agility": "Agi", "intellect": "Int",
        "endurance": "End", "faith": "Faith", "power": "Power",
    }
    parts = []
    for k, v in delta.items():
        sign = "+" if v > 0 else ""
        parts.append(f"{sign}{v} {labels.get(k, k.capitalize())}")
    return ", ".join(parts)


async def _load_class_meta(db, class_slug: Optional[str]) -> dict:
    if not class_slug:
        return {"primary_stat": "strength", "secondary_stats": [],
                "display_name_it": None}
    doc = await db.adventurer_classes.find_one(
        {"slug": class_slug},
        {"_id": 0, "slug": 1, "primary_stat": 1, "secondary_stats": 1,
         "display_name_it": 1, "name": 1},
    )
    if not doc:
        return {"primary_stat": "strength", "secondary_stats": [],
                "display_name_it": None}
    return doc


def _resolve_class_slug(adv: dict) -> Optional[str]:
    """Resolve the class slug from an adventurer document.

    Legacy adventurers were seeded with `class_name` (Title-cased,
    e.g. "Warrior") only; the `class_slug` field was added in R16.0
    but only ~6% of the 2000+ existing documents were backfilled.

    Mirrors the fallback used by `check_equip_compatibility` so the
    auto-equip class-aware scoring works on the same population that
    the compatibility validator already handles correctly.
    """
    slug = (adv.get("class_slug") or "").strip().lower()
    if slug:
        return slug
    name = (adv.get("class_name") or adv.get("class") or "").strip().lower()
    return name or None


# ── Italian noun agreement per slot for narrative messages ──────────────
_SLOT_GRAMMAR_IT: dict[str, dict[str, str]] = {
    "weapon":    {"noun": "Arma",       "past_part": "equipaggiata",   "art": "un'"},
    "chest":     {"noun": "Corazza",    "past_part": "equipaggiata",   "art": "una "},
    "legs":      {"noun": "Gambe",      "past_part": "equipaggiate",   "art": "delle "},
    "head":      {"noun": "Elmo",       "past_part": "equipaggiato",   "art": "un "},
    "accessory": {"noun": "Accessorio", "past_part": "equipaggiato",   "art": "un "},
    "back":      {"noun": "Schiena",    "past_part": "equipaggiata",   "art": "la "},
    "ring_1":    {"noun": "Anello I",   "past_part": "equipaggiato",   "art": "un "},
    "ring_2":    {"noun": "Anello II",  "past_part": "equipaggiato",   "art": "un "},
    "trinket_1": {"noun": "Monile I",   "past_part": "equipaggiato",   "art": "un "},
    "trinket_2": {"noun": "Monile II",  "past_part": "equipaggiato",   "art": "un "},
}


def _slot_grammar_it(slot: str) -> dict[str, str]:
    return _SLOT_GRAMMAR_IT.get(
        slot,
        {"noun": slot.capitalize(), "past_part": "equipaggiato",
         "art": "un "},
    )


# Italian class labels used when the adventurer_classes doc lacks a
# `display_name_it` (defensive fallback; class catalog is fully
# localised as of R16.0).
_CLASS_LABELS_IT: dict[str, str] = {
    "warrior": "Guerriero", "mage": "Mago", "priest": "Sacerdote",
    "rogue": "Ladro", "ranger": "Ranger", "paladin": "Paladino",
    "berserker": "Berserker", "druid": "Druido",
    "necromancer": "Negromante", "monk": "Monaco", "bard": "Bardo",
    "assassin": "Assassino", "warlock": "Occultista",
    "alchemist": "Alchimista",
}


def _class_it_label(cls_meta: dict) -> str:
    """Human-readable Italian class label used in narrative reasons.

    ROUND 16.5.4c REOPEN #3 — Precedenza: mappa canonica
    `_CLASS_LABELS_IT[slug]` (single source of truth) → `display_name_it`
    del catalog → `name` (fallback). Il PM ha deciso `warlock → Occultista`
    (era `Stregone`); la mappa `_CLASS_LABELS_IT` è la sede canonica per
    questi override, indipendentemente da `adventurer_classes.name`.
    """
    slug = (cls_meta.get("slug") or "").strip().lower()
    if slug and slug in _CLASS_LABELS_IT:
        return _CLASS_LABELS_IT[slug]
    return (
        cls_meta.get("display_name_it")
        or cls_meta.get("name")
        or ""
    )


async def auto_equip_adventurer(
    db, *, guild: dict, adventurer_id: str,
    actor_user_id: Optional[str],
) -> dict[str, Any]:
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"]},
        {"_id": 0, "id": 1, "name": 1, "level": 1, "class_slug": 1,
         "class_name": 1, "specialization_slug": 1},
    )
    if not adv:
        raise HTTPException(404, {
            "code": "auto_equip.adventurer_not_found",
            "user_message": "Avventuriero non trovato in questa gilda.",
        })

    cls_meta = await _load_class_meta(db, _resolve_class_slug(adv))
    primary = cls_meta.get("primary_stat") or "strength"
    secondaries = cls_meta.get("secondary_stats") or []
    class_it = _class_it_label(cls_meta)
    adv_level = int(adv.get("level") or 1)

    # Current equipment snapshot per slot.
    eq_docs = await db.equipped_items.find(
        {"guild_id": guild["id"], "adventurer_id": adv["id"]},
        {"_id": 0, "slot": 1, "item_id": 1},
    ).sort([("slot", 1)]).to_list(20)
    current_by_slot: dict[str, dict] = {}
    for e in eq_docs:
        item = await db.items.find_one({"id": e["item_id"]}, {"_id": 0})
        if item:
            current_by_slot[e["slot"]] = item

    # Inventory pool (NOT bound to other adventurers). Deterministic sort.
    inv_rows = await db.inventory_items.find(
        {"guild_id": guild["id"], "is_active": {"$ne": False}},
        {"_id": 0, "item_id": 1, "is_bound": 1,
         "bound_to_adventurer_id": 1},
    ).sort([("item_id", 1)]).to_list(2000)
    item_ids = sorted({r["item_id"] for r in inv_rows
                       if not r.get("is_bound") or
                       r.get("bound_to_adventurer_id") == adv["id"]})
    if not item_ids:
        items_pool: list[dict] = []
    else:
        items_pool = await db.items.find(
            {"id": {"$in": item_ids}, "is_active": {"$ne": False}},
            {"_id": 0},
        ).sort([("id", 1)]).to_list(len(item_ids))

    equipped_summary: list[dict] = []
    replaced_summary: list[dict] = []
    unchanged: list[str] = []
    warnings: list[str] = []
    reasons: list[dict] = []
    unchanged_slots_detail: list[dict] = []
    score_before = sum(item_equip_power(i)
                       for i in current_by_slot.values())

    def _slot_label(slot: str) -> tuple[str, str]:
        return {
            "weapon": ("Arma", "Weapon"),
            "chest": ("Corazza", "Chest"),
            "legs": ("Gambe", "Legs"),
            "head": ("Elmo", "Head"),
            "accessory": ("Accessorio", "Accessory"),
            "back": ("Schiena", "Back"),
            "ring_1": ("Anello I", "Ring I"),
            "ring_2": ("Anello II", "Ring II"),
            "trinket_1": ("Monile I", "Trinket I"),
            "trinket_2": ("Monile II", "Trinket II"),
        }.get(slot, (slot, slot))

    for slot in EQUIPMENT_SLOTS:
        slot_it, slot_en = _slot_label(slot)
        grammar_it = _slot_grammar_it(slot)
        expected_type = SLOT_TO_ITEM_TYPE[slot]
        # Candidates: matching item_type + level gate + compat == "ok".
        # ROUND 16.5.4b REOPEN #2 — PM decision Q2-b(iii): warning-severity
        # items are SKIPPED (previously they entered the pool with a ×0.5
        # penalty). This prevents Auto-Equip from putting off-class weapons
        # (e.g. Frostfang Claymore on a Druid) when the inventory lacks
        # class-fit items. Manual equip is UNCHANGED (still allowed with
        # a warning UX).
        candidates: list[tuple[float, dict]] = []
        off_class_seen = 0  # matching type + level, rejected by class compat
        for it in items_pool:
            if it.get("item_type") != expected_type:
                continue
            # ROUND 16.5.4b — use the shared R11.3 level gate helper.
            # Legacy fields `required_level` / `level_requirement` do NOT
            # exist in the item schema; using them here (the pre-fix
            # behaviour) meant the auto-equip skipped every level gate.
            req_lv = resolve_item_required_level(it)
            if req_lv > adv_level:
                continue
            verdict = check_equip_compatibility(adv, it)
            severity = verdict.get("severity") or "ok"
            if severity in ("block", "warning"):
                # Class-fit rejected. Track it so we can differentiate the
                # empty state ("nothing at all" vs "only off-class here").
                off_class_seen += 1
                continue
            fit = _compute_fitness(it, primary, secondaries)
            candidates.append((fit, it))
        if not candidates:
            warnings.append(f"{slot}: nessun item compatibile disponibile")
            unchanged.append(slot)
            # ROUND 16.5.4b REOPEN #2 — Empty state differenziato:
            #   - se `off_class_seen == 0` → inventario proprio vuoto per il tipo
            #   - se `off_class_seen > 0`  → item trovati ma tutti off-class
            noun_it = grammar_it.get("noun") or slot_it
            noun_it_lower = noun_it.lower()
            if off_class_seen == 0:
                reason_it = (
                    f"Nessuna {noun_it_lower} adatta a {class_it} "
                    f"Lv{adv_level} trovata in inventario. Completa "
                    f"spedizioni, raid o missioni per trovare "
                    f"equipaggiamento compatibile."
                )
                reason_en = (
                    f"{slot_en}: no compatible item in inventory. "
                    f"Complete expeditions, raids or contracts to loot one."
                )
            else:
                reason_it = (
                    f"Oggetti trovati, ma nessuno adatto alla classe "
                    f"{class_it} per lo slot {noun_it_lower}."
                )
                reason_en = (
                    f"{slot_en}: items found in inventory, but none is "
                    f"class-compatible for this adventurer."
                )
            unchanged_slots_detail.append({
                "slot": slot,
                "reason_it": reason_it,
                "reason_en": reason_en,
                "off_class_seen": off_class_seen,
            })
            continue
        # ROUND 16.5.4b — deterministic tie-break: fitness DESC,
        # power_score DESC, id ASC. Python's sort is stable; the tuple
        # key gives a total order.
        candidates.sort(key=lambda pair: (
            -pair[0],
            -int(pair[1].get("power_score", 0) or 0),
            str(pair[1].get("id", "")),
        ))
        best_fit, best_item = candidates[0]
        current = current_by_slot.get(slot)
        current_fit = (
            _compute_fitness(current, primary, secondaries)
            if current else -1.0
        )
        if current and best_item.get("id") == current.get("id"):
            unchanged.append(slot)
            unchanged_slots_detail.append({
                "slot": slot,
                "reason_it": (
                    f"{slot_it}: l'oggetto attualmente equipaggiato è "
                    f"già il migliore."
                ),
                "reason_en": (
                    f"{slot_en}: the currently equipped item is already "
                    f"the best."
                ),
            })
            continue
        if best_fit <= current_fit:
            unchanged.append(slot)
            unchanged_slots_detail.append({
                "slot": slot,
                "reason_it": (
                    f"{slot_it}: nessun oggetto migliore disponibile "
                    f"in inventario."
                ),
                "reason_en": (
                    f"{slot_en}: no better item available in inventory."
                ),
            })
            continue
        # Swap: unequip current then equip new.
        if current:
            try:
                await unequip_item_service(db, guild, adv["id"], slot)
            except HTTPException as http_exc:
                # ROUND 16.5.4c ADJ-3.c — business error dal service: usa
                # il `user_message` italiano strutturato se disponibile,
                # altrimenti un fallback IT amichevole. NON stringificare
                # mai "HTTPException" nel warning player-facing.
                warnings.append(_extract_it_message(
                    http_exc, slot_it,
                    fallback=f"{slot_it}: impossibile rimuovere "
                             f"l'oggetto attuale in questo momento."
                ))
                logger.warning(
                    "auto_equip: unequip failed adv=%s slot=%s http=%s",
                    adv["id"], slot, http_exc.status_code,
                )
                continue
            except Exception as exc:  # noqa: BLE001
                # Errore tecnico imprevisto — solo log, no dettaglio nel report.
                logger.exception(
                    "auto_equip: unequip crashed adv=%s slot=%s",
                    adv["id"], slot,
                )
                warnings.append(
                    f"{slot_it}: impossibile rimuovere l'oggetto attuale "
                    f"in questo momento."
                )
                continue
        try:
            await equip_item_service(
                db, guild, adv["id"], best_item["id"], slot,
            )
        except HTTPException as http_exc:
            warnings.append(_extract_it_message(
                http_exc, slot_it,
                fallback=f"{slot_it}: impossibile equipaggiare l'oggetto "
                         f"scelto in questo momento."
            ))
            logger.warning(
                "auto_equip: equip failed adv=%s slot=%s item=%s http=%s",
                adv["id"], slot, best_item.get("id"), http_exc.status_code,
            )
            continue
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "auto_equip: equip crashed adv=%s slot=%s item=%s",
                adv["id"], slot, best_item.get("id"),
            )
            warnings.append(
                f"{slot_it}: impossibile equipaggiare l'oggetto scelto "
                f"in questo momento."
            )
            continue
        # ROUND 16.5.4b — stat delta from canonical *_bonus fields.
        stat_delta = _stat_delta(current, best_item, primary)
        primary_gain = int(stat_delta.get(primary, 0))
        item_score_before = (
            item_equip_power(current) if current else 0
        )
        item_score_after = item_equip_power(best_item)
        # Bilingual narrative reason (Italian: "arcane_focus
        # equipaggiato: +5 Int, +2 End, migliore per Mago.")
        new_name = (
            best_item.get("display_name_it")
            or best_item.get("name")
            or best_item.get("slug")
        )
        new_name_en = (
            best_item.get("display_name_en")
            or best_item.get("name")
            or best_item.get("slug")
        )
        stat_str_it = _format_stat_delta(stat_delta)
        class_suffix_it = f", migliore per {class_it}." if class_it else "."
        class_suffix_en = (
            f", better for {cls_meta.get('name') or ''}."
            if cls_meta.get("name") else "."
        )
        if current:
            old_name = (
                current.get("display_name_it")
                or current.get("name")
                or current.get("slug")
            )
            old_name_en = (
                current.get("display_name_en")
                or current.get("name")
                or current.get("slug")
            )
            r_it = (
                f"{slot_it} sostituit{'a' if grammar_it['past_part']=='equipaggiata' else 'o'}: «{old_name}» → «{new_name}»"
                + (f" ({stat_str_it})" if stat_str_it else "")
                + class_suffix_it
            )
            r_en = (
                f"{slot_en} replaced: \"{old_name_en}\" → \"{new_name_en}\""
                + class_suffix_en
            )
            replaced_summary.append({
                "slot": slot,
                "old_item_slug": current.get("slug"),
                "new_item_slug": best_item.get("slug"),
                "fitness_delta": round(best_fit - current_fit, 2),
                "score_before": item_score_before,
                "score_after": item_score_after,
                "stat_delta": stat_delta,
            })
        else:
            r_it = (
                f"{slot_it} {grammar_it['past_part']}: «{new_name}»"
                + (f" ({stat_str_it})" if stat_str_it else "")
                + class_suffix_it
            )
            r_en = (
                f"{slot_en} equipped: \"{new_name_en}\""
                + class_suffix_en
            )
            equipped_summary.append({
                "slot": slot,
                "item_slug": best_item.get("slug"),
                "item_name": new_name,
                "fitness": round(best_fit, 2),
                "score_before": item_score_before,
                "score_after": item_score_after,
                "stat_delta": stat_delta,
            })
        reasons.append({
            "slot": slot,
            "old_item_slug": (current or {}).get("slug"),
            "new_item_slug": best_item.get("slug"),
            "old_item_name": (current or {}).get("name"),
            "new_item_name": best_item.get("name"),
            "stat_delta": stat_delta,
            "primary_stat": primary,
            "primary_gain": primary_gain,
            "score_before": item_score_before,
            "score_after": item_score_after,
            "reason_it": r_it,
            "reason_en": r_en,
        })

    score_after_rows = await db.equipped_items.find(
        {"guild_id": guild["id"], "adventurer_id": adv["id"]},
        {"_id": 0, "item_id": 1},
    ).sort([("slot", 1)]).to_list(20)
    after_items = await db.items.find(
        {"id": {"$in": [r["item_id"] for r in score_after_rows]}},
        {"_id": 0},
    ).sort([("id", 1)]).to_list(20)
    score_after = sum(item_equip_power(i) for i in after_items)

    swaps_count = len(equipped_summary) + len(replaced_summary)
    await write_audit(
        db, event_type="adventurer_auto_equipped",
        actor_user_id=actor_user_id, actor_guild_id=guild["id"],
        source="equipment.auto_equip",
        related_entity_id=adv["id"],
        metadata={
            "adventurer_id": adv["id"],
            "swaps_count": swaps_count,
            "score_delta": score_after - score_before,
        },
    )

    return {
        "adventurer_id": adv["id"],
        "adventurer_name": adv.get("name"),
        "equipped": equipped_summary,
        "replaced": replaced_summary,
        "unchanged_slots": unchanged,
        "unchanged_slots_detail": unchanged_slots_detail,
        "reasons": reasons,
        "primary_stat": primary,
        "secondary_stats": list(secondaries),
        "warnings": warnings,
        "warnings_it": warnings,
        "warnings_en": [
            ("No compatible item in inventory."
             if "nessun item compatibile" in w else w)
            for w in warnings
        ],
        "score_before": int(score_before),
        "score_after": int(score_after),
        "score_delta": int(score_after - score_before),
        "swaps_count": swaps_count,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["auto_equip_adventurer"]
