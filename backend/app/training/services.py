"""ROUND 6C — Training services: atomic apply_specialization flow.

The orchestrator below is intentionally linear (one path per failure mode,
no nested branches) so that the audit trail and Mongo writes are easy to
reason about. Every failure is a single `HTTPException` raise; every
success follows the exact same 5-step order:

    1. Pre-validate (404 / 422 sequence — all reads, no writes)
    2. Atomic gold debit ($inc … {gold: -cost} with `gold >= cost` filter)
    3. Generate signature_item (inventory row with bound_to_adventurer_id)
    4. Set adventurer.specialization (snapshot of modifiers locked in time)
    5. Best-effort audit log (never blocks the write)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.training.catalog import (
    MIN_ADVENTURER_LEVEL,
    SPEC_BY_SLUG,
    SPEC_SIGNATURE_ITEMS,
    apply_cost_for_training_level,
    tier_for_training_level,
)


SIGNATURE_BOUND_REASON = "specialization_signature"


async def _resolve_class_slug(db, adv: dict) -> str | None:
    """Return the canonical lowercase class slug for an adventurer.

    Real game-flow adventurers (recruitment + onboarding writes) only persist
    ``adventurer_class_id`` + ``class_name`` (capitalized display) on the doc,
    NOT ``class_slug``. The training catalog uses lowercase slugs as eligibility
    keys (`"warrior"`, `"paladin"`, …), so we MUST resolve via a lookup on
    `adventurer_classes` instead of trusting an embedded field.

    Resolution order (fail-soft, never raises):
      1. If `adv.class_slug` is already set (legacy data + test seeds + the
         recruitment generator preview path), use it as-is.
      2. Otherwise look up `adventurer_classes` by `adv.adventurer_class_id`
         and read `slug`.
      3. As a last resort lowercase `class_name` so we never block on a
         stale/missing FK (no row in the catalog).
    """
    cached = adv.get("class_slug")
    if isinstance(cached, str) and cached:
        return cached
    class_id = adv.get("adventurer_class_id")
    if class_id:
        row = await db.adventurer_classes.find_one(
            {"id": class_id}, {"_id": 0, "slug": 1},
        )
        if row and row.get("slug"):
            return row["slug"]
    name = adv.get("class_name")
    if isinstance(name, str) and name:
        return name.lower()
    return None


async def _get_training_level(db, guild_id: str) -> int:
    """Resolve the current `training_grounds` level for this guild."""
    row = await db.guild_structures.find_one(
        {"guild_id": guild_id},
        {"_id": 0, "structures.training_grounds": 1},
    )
    tg = (row or {}).get("structures", {}).get("training_grounds") or {}
    if not tg.get("is_unlocked"):
        return 0
    return int(tg.get("level", 0))


async def get_available_specs(db, *, guild_id: str) -> dict:
    """Public list of specs unlocked for this guild's training level.

    Returns the catalog filtered by tier + the apply cost so the UI doesn't
    duplicate gating logic.
    """
    tg_level = await _get_training_level(db, guild_id)
    tier = tier_for_training_level(tg_level)
    if tier is None:
        return {
            "training_grounds_level": 0,
            "tier": None,
            "apply_cost_gold": 0,
            "specs": [],
            "min_adventurer_level": MIN_ADVENTURER_LEVEL,
        }
    allowed = {"starter"} if tier == "starter" else {"starter", "full"}
    specs = [s for s in SPEC_BY_SLUG.values() if s["tier"] in allowed]
    return {
        "training_grounds_level": tg_level,
        "tier": tier,
        "apply_cost_gold": apply_cost_for_training_level(tg_level),
        "specs": specs,
        "min_adventurer_level": MIN_ADVENTURER_LEVEL,
    }


def _err(code: str, msg: str, *, status: int = 422, **extra: Any) -> HTTPException:
    """Build the structured-detail HTTPException the FE interceptor expects."""
    return HTTPException(
        status_code=status,
        detail={"code": code, "user_message": msg, **extra},
    )


async def apply_specialization(
    db,
    *,
    guild_id: str,
    actor_user_id: str,
    adventurer_id: str,
    spec_slug: str,
) -> dict:
    """Atomic apply orchestrator.

    Failure modes (all `HTTPException` with structured detail):
      • 404 if adventurer doesn't belong to the guild
      • 422 `training.locked` if training_grounds not unlocked
      • 422 `training.spec_unknown` if the spec slug isn't in catalog
      • 422 `training.spec_tier_locked` if spec tier > training level tier
      • 422 `training.class_not_eligible` if adv.class_slug not in spec.eligible
      • 422 `training.adventurer_level_too_low` if adv.level < 5
      • 422 `training.adventurer_already_specialized` if adv has spec set
      • 422 `training.adventurer_retired` if adv.is_retired
      • 402 `training.insufficient_gold` if guild gold < cost
    """
    spec = SPEC_BY_SLUG.get(spec_slug)
    if not spec:
        raise _err("training.spec_unknown", f"Specializzazione '{spec_slug}' non riconosciuta.")

    # 1) Pre-validate (all reads)
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        raise _err(
            "adventurer.not_found", "Avventuriero non trovato.", status=404,
            adventurer_id=adventurer_id,
        )
    if adv.get("is_retired") is True:
        raise _err("training.adventurer_retired",
                   "Non puoi specializzare un avventuriero congedato.")
    if adv.get("specialization"):
        raise _err(
            "training.adventurer_already_specialized",
            "Avventuriero già specializzato. In Round 6C il respec non è disponibile.",
            current_spec=adv["specialization"].get("slug"),
        )
    if int(adv.get("level", 1)) < MIN_ADVENTURER_LEVEL:
        raise _err(
            "training.adventurer_level_too_low",
            f"Serve livello minimo {MIN_ADVENTURER_LEVEL} (questo avventuriero è Lv{adv.get('level', 1)}).",
            min_level=MIN_ADVENTURER_LEVEL, current_level=adv.get("level", 1),
        )
    # Class eligibility — resolve via lookup so real game-flow advs
    # (which only persist `adventurer_class_id` + `class_name`, not
    # `class_slug`) are correctly matched against the catalog's lowercase
    # slug list. See `_resolve_class_slug` for fallback order.
    actual_class_slug = await _resolve_class_slug(db, adv)
    if actual_class_slug not in spec["eligible_classes"]:
        raise _err(
            "training.class_not_eligible",
            f"Classe '{adv.get('class_name')}' non compatibile con '{spec['name_it']}'.",
            eligible_classes=spec["eligible_classes"],
            actual_class=actual_class_slug,
        )

    # Training Grounds gating
    tg_level = await _get_training_level(db, guild_id)
    tier = tier_for_training_level(tg_level)
    if tier is None:
        raise _err("training.locked",
                   "Devi sbloccare il Campo di Addestramento per specializzare.")
    if spec["tier"] == "full" and tier != "full":
        raise _err(
            "training.spec_tier_locked",
            f"'{spec['name_it']}' richiede Training Grounds Lv3+.",
            spec_tier=spec["tier"], training_level=tg_level,
        )

    cost = apply_cost_for_training_level(tg_level)

    # 2) Atomic gold debit (idempotent guard via filter)
    debit_result = await db.guilds.update_one(
        {"id": guild_id, "gold": {"$gte": cost}},
        {"$inc": {"gold": -cost}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if debit_result.modified_count != 1:
        raise _err(
            "training.insufficient_gold",
            f"Servono {cost} oro per la specializzazione.",
            status=402, cost=cost,
        )

    # 3) Generate signature_item bound to the adventurer
    sig_template = SPEC_SIGNATURE_ITEMS.get(spec["signature_item_slug"])
    now_iso = datetime.now(timezone.utc).isoformat()
    inv_id = str(uuid.uuid4())
    signature_inv_row = {
        "id": inv_id,
        "instance_id": inv_id,
        "guild_id": guild_id,
        # `item_id` is the slug of the item template; the FE looks up item
        # data via the items catalog. Signature items are not in the items
        # collection — we embed the relevant display + power data here.
        "item_id": sig_template["slug"],
        "acquired_at": now_iso,
        "quantity": 1,
        # Round 4 forge fields (default-safe)
        "is_bound": True,  # guild-bound (cannot be sold)
        "refinement_level": 0,
        "enchants": [],
        "affixes": [],
        "reroll_count": 0,
        "disenchanted_at": None,
        # Round 6B.4 — adventurer-bound (cannot be equipped on others)
        "bound_to_adventurer_id": adventurer_id,
        "bound_reason": SIGNATURE_BOUND_REASON,
        "bound_at": now_iso,
        # ROUND 6C — embedded signature-item data so the FE can render without
        # a separate /api/items round-trip. The `power_score` is used by the
        # client-side preview when equipping.
        "signature": {
            "spec_slug": spec["slug"],
            "name_it": sig_template["name_it"],
            "name_en": sig_template["name_en"],
            "rarity": sig_template["rarity"],
            "slot": sig_template["slot"],
            "strength_bonus": sig_template.get("strength_bonus", 0),
            "agility_bonus": sig_template.get("agility_bonus", 0),
            "intellect_bonus": sig_template.get("intellect_bonus", 0),
            "endurance_bonus": sig_template.get("endurance_bonus", 0),
            "faith_bonus": sig_template.get("faith_bonus", 0),
            "power_score": sig_template["power_score"],
        },
    }
    await db.inventory_items.insert_one(signature_inv_row)

    # 4) Set adventurer.specialization (snapshot — modifiers locked in time
    # so future catalog rebalancing doesn't retroactively change live advs).
    spec_doc = {
        "slug": spec["slug"],
        "name_it": spec["name_it"],
        "name_en": spec["name_en"],
        "tier": spec["tier"],
        "applied_at": now_iso,
        "applied_at_level": int(adv.get("level", 1)),
        "signature_item_id": inv_id,
        "modifiers": dict(spec["modifiers"]),
        "applied_by_user_id": actor_user_id,
        "training_grounds_level_at_apply": tg_level,
    }
    await db.adventurers.update_one(
        {"id": adventurer_id, "guild_id": guild_id},
        {"$set": {"specialization": spec_doc, "updated_at": now_iso}},
    )

    # 5) Audit (best-effort, never raises)
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="specialization_applied",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            source="training.apply_specialization",
            related_entity_id=adventurer_id,
            metadata={
                "adventurer_id": adventurer_id,
                "spec_slug": spec["slug"],
                "tier": spec["tier"],
                "cost_gold": cost,
                "signature_item_id": inv_id,
                "training_grounds_level": tg_level,
            },
        )
        await write_audit(
            db,
            event_type="specialization_signature_item_created",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            source="training.apply_specialization",
            related_entity_id=inv_id,
            metadata={
                "adventurer_id": adventurer_id,
                "spec_slug": spec["slug"],
                "item_slug": sig_template["slug"],
                "rarity": sig_template["rarity"],
            },
        )
    except Exception:
        pass

    # ROUND 6D — contract progress (synergy 6C↔6D)
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(
            db, guild_id, "specializations_applied", 1,
        )
    except Exception:
        pass

    return {
        "adventurer_id": adventurer_id,
        "specialization": spec_doc,
        "signature_item": {**signature_inv_row, "_id": None},
        "gold_spent": cost,
    }


__all__ = [
    "SIGNATURE_BOUND_REASON",
    "apply_specialization",
    "get_available_specs",
]
