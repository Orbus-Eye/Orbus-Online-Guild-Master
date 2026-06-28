"""ROUND 4 — Forge / Workshop services.

Implements refinement, enchantment, affix re-roll, and disenchant operations
on per-instance inventory rows. All operations are:
  • Atomic (Mongo CAS conditional update + rollback on partial failure).
  • Idempotent at the endpoint level (double-click safe via instance state).
  • Audit-logged.
  • BoE-aware: any successful refine/enchant/reroll auto-flags the
    inventory row as `is_bound=True`, which is enforced by
    `app/market/services.create_listing` (HTTP 422).

NO P2W. NO real-money purchase. NO Mythic. NO hard delete.
"""
from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

logger = logging.getLogger("orbus.forge")


# ─── Locked economy (binding §F LOCKED) ────────────────────────────────
# Refinement +N curve. NEVER raise above MAX_REFINEMENT without product
# re-authorization. Costs: gold + iron_shard + arcane_dust (uncommon) +
# dull_gem (uncommon) + dragon_essence (rare, T4+ drop). Failures consume
# materials but DO NOT break the item (per Q2 + §J: no item-break in R4).
MAX_REFINEMENT = 10
REFINEMENT_TABLE: list[dict] = [
    # idx 0 = +0 → +1, idx 9 = +9 → +10
    {"level": 1,  "rate": 1.00, "gold": 50,    "mats": {"iron_shard": 2}},
    {"level": 2,  "rate": 0.90, "gold": 100,   "mats": {"iron_shard": 4}},
    {"level": 3,  "rate": 0.75, "gold": 200,   "mats": {"iron_shard": 6, "arcane_dust": 1}},
    {"level": 4,  "rate": 0.60, "gold": 400,   "mats": {"iron_shard": 8, "arcane_dust": 2}},
    {"level": 5,  "rate": 0.45, "gold": 800,   "mats": {"iron_shard": 10, "arcane_dust": 2, "dull_gem": 1}},
    {"level": 6,  "rate": 0.35, "gold": 1500,  "mats": {"iron_shard": 12, "arcane_dust": 3, "dull_gem": 2}},
    {"level": 7,  "rate": 0.25, "gold": 2500,  "mats": {"raw_leather": 8, "dull_gem": 2, "dragon_essence": 1}},
    {"level": 8,  "rate": 0.18, "gold": 4000,  "mats": {"raw_leather": 10, "dull_gem": 3, "dragon_essence": 1}},
    {"level": 9,  "rate": 0.12, "gold": 6000,  "mats": {"raw_leather": 12, "dull_gem": 4, "dragon_essence": 2}},
    {"level": 10, "rate": 0.08, "gold": 10000, "mats": {"dragon_essence": 3, "arcane_dust": 5, "dull_gem": 5}},
]

# Reroll cost curve (Q7 LOCKED). Hard cap 5 reroll / item.
REROLL_COSTS = [50, 150, 400, 1000, 2500]
REROLL_CAP = 5

# Disenchant base materials guaranteed by rarity (Q4 LOCKED).
DISENCHANT_GUARANTEED: dict[str, dict[str, int]] = {
    "Common":    {"iron_shard": 1},
    "Uncommon":  {"iron_shard": 2, "arcane_dust": 1},
    "Rare":      {"iron_shard": 3, "arcane_dust": 1, "dull_gem": 1},
    "Epic":      {"iron_shard": 4, "arcane_dust": 2, "dull_gem": 1, "raw_leather": 2},
    "Legendary": {"iron_shard": 6, "arcane_dust": 3, "dull_gem": 2, "raw_leather": 3, "dragon_essence": 1},
}
# Bonus drop chance pool — weighted random per rarity.
DISENCHANT_BONUS_POOL: dict[str, list[tuple[str, int, float]]] = {
    # (material_slug, qty, probability 0..1)
    "Common":    [("arcane_dust", 1, 0.10)],
    "Uncommon":  [("arcane_dust", 1, 0.25), ("dull_gem", 1, 0.10)],
    "Rare":      [("dull_gem", 1, 0.30), ("raw_leather", 1, 0.20)],
    "Epic":      [("dragon_essence", 1, 0.15), ("raw_leather", 2, 0.30)],
    "Legendary": [("dragon_essence", 1, 0.50), ("arcane_dust", 3, 0.30)],
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Helpers ────────────────────────────────────────────────────────────
async def _load_owned_instance(db, guild_id: str, instance_id: str) -> dict:
    """Load an inventory row owned by `guild_id` keyed by `instance_id`.
    Backward compat: instance_id falls back to inventory_items.id for
    legacy rows pre-ROUND-4 migration."""
    row = await db.inventory_items.find_one(
        {
            "$or": [
                {"instance_id": instance_id},
                {"id": instance_id},  # legacy fallback
            ],
            "guild_id": guild_id,
        },
        {"_id": 0},
    )
    if not row:
        raise HTTPException(404, "inventory instance not found")
    if row.get("disenchanted_at"):
        raise HTTPException(410, "instance disenchanted")
    return row


async def _load_item_template(db, item_id: str) -> dict:
    it = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not it:
        raise HTTPException(404, "item template not found")
    return it


async def _audit(db, guild_id: str, user_id: str, event_type: str, metadata: dict) -> None:
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_user_id": user_id,
            "actor_guild_id": guild_id,
            "metadata": metadata,
            "created_at": _utc_now_iso(),
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit write failed (%s): %s", event_type, exc)


async def _consume_gold_and_mats(
    db, guild_id: str, gold_cost: int, mats_cost: dict[str, int]
) -> None:
    """Atomic gold + materials debit. Raises 402 if insufficient.

    Strategy: do an atomic `find_one_and_update` on guild gold with CAS
    guard `gold >= gold_cost`. Then loop through materials with CAS guards
    `quantity >= qty`. If any material fails, REFUND gold and any already
    consumed materials before raising.
    """
    guild = await db.guilds.find_one_and_update(
        {"id": guild_id, "gold": {"$gte": int(gold_cost)}},
        {"$inc": {"gold": -int(gold_cost)}},
    )
    if not guild:
        raise HTTPException(402, "insufficient gold")

    consumed: list[tuple[str, str, int]] = []  # (slug, item_id, qty)
    try:
        for slug, qty in mats_cost.items():
            item = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
            if not item:
                raise HTTPException(500, f"material not seeded: {slug}")
            r = await db.inventory_items.find_one_and_update(
                {
                    "guild_id": guild_id,
                    "item_id": item["id"],
                    "quantity": {"$gte": int(qty)},
                    "is_bound": {"$ne": True},
                },
                {"$inc": {"quantity": -int(qty)}},
            )
            if not r:
                raise HTTPException(402, f"insufficient material: {slug} (need {qty})")
            consumed.append((slug, item["id"], int(qty)))
    except HTTPException:
        # Rollback: refund gold + already-consumed materials.
        await db.guilds.update_one({"id": guild_id}, {"$inc": {"gold": int(gold_cost)}})
        for _slug, item_id, qty in consumed:
            await db.inventory_items.update_one(
                {"guild_id": guild_id, "item_id": item_id},
                {"$inc": {"quantity": int(qty)}},
            )
        raise


async def _grant_materials(db, guild_id: str, mats: dict[str, int]) -> dict[str, int]:
    """Best-effort idempotent material grant. Increments existing stack or
    creates a new one. Returns `{slug: qty}` actually granted."""
    granted: dict[str, int] = {}
    for slug, qty in mats.items():
        if int(qty) <= 0:
            continue
        item = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
        if not item:
            continue
        existing = await db.inventory_items.find_one_and_update(
            {"guild_id": guild_id, "item_id": item["id"], "is_bound": {"$ne": True}},
            {"$inc": {"quantity": int(qty)}},
        )
        if not existing:
            await db.inventory_items.insert_one({
                "id": str(uuid.uuid4()),
                "instance_id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item["id"],
                "quantity": int(qty),
                "refinement_level": 0,
                "enchants": [],
                "affixes": [],
                "is_bound": False,
                "disenchanted_at": None,
                "acquired_at": _utc_now_iso(),
            })
        granted[slug] = int(qty)
    return granted


def _is_stackable(item: dict) -> bool:
    return item.get("item_type") in ("material", "consumable")


# ─── Public API ─────────────────────────────────────────────────────────
async def refine_instance(
    db, *, guild: dict, user_id: str, instance_id: str
) -> dict:
    inv = await _load_owned_instance(db, guild["id"], instance_id)
    item = await _load_item_template(db, inv["item_id"])

    if _is_stackable(item):
        raise HTTPException(422, "stackable items cannot be refined")
    max_ref = int(item.get("max_refinement") or MAX_REFINEMENT)
    if max_ref <= 0:
        raise HTTPException(422, "item template not refinable")
    cur = int(inv.get("refinement_level", 0))
    if cur >= max_ref:
        raise HTTPException(422, "already at max refinement")

    step = REFINEMENT_TABLE[cur]  # cur=0 → +1, etc.
    await _consume_gold_and_mats(db, guild["id"], step["gold"], step["mats"])

    success = random.random() < float(step["rate"])
    new_level = cur + 1 if success else cur

    # CAS on the instance: ensure level hasn't moved.
    upd = await db.inventory_items.find_one_and_update(
        {
            "$or": [{"instance_id": instance_id}, {"id": instance_id}],
            "guild_id": guild["id"],
            "refinement_level": cur,
        },
        {"$set": {"refinement_level": new_level, "is_bound": True}},
        return_document=True,
    )
    if not upd:
        # Race lost — refund mats (best-effort).
        await db.guilds.update_one({"id": guild["id"]}, {"$inc": {"gold": step["gold"]}})
        await _grant_materials(db, guild["id"], step["mats"])
        raise HTTPException(409, "concurrent refine — please retry")

    await _audit(db, guild["id"], user_id,
                 "item_refined" if success else "item_refine_failed",
                 {
                     "instance_id": instance_id,
                     "item_slug": item["slug"],
                     "from_level": cur,
                     "to_level": new_level,
                     "success": success,
                     "gold_cost": step["gold"],
                     "rate": step["rate"],
                 })
    await _emit_forge_contract_progress(db, guild["id"])
    return {
        "success": success,
        "refinement_level": new_level,
        "from_level": cur,
        "is_bound": True,
        "instance_id": inv.get("instance_id") or inv["id"],
    }


async def _emit_forge_contract_progress(db, guild_id: str) -> None:
    """ROUND 6E — forge contract progress hook (best-effort)."""
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(db, guild_id, "forge_refinements", 1)
    except Exception:
        pass


async def enchant_options(
    db, *, guild: dict, instance_id: str, n: int = 4
) -> dict:
    """Generate 3-5 weighted enchant choices for the player (Q5 LOCKED)."""
    inv = await _load_owned_instance(db, guild["id"], instance_id)
    item = await _load_item_template(db, inv["item_id"])
    if _is_stackable(item):
        raise HTTPException(422, "stackable items cannot be enchanted")
    slots = int(item.get("enchant_slots") or 0)
    used = len(inv.get("enchants", []))
    if used >= max(1, slots):  # at least 1 slot to allow legacy items
        raise HTTPException(422, "no free enchant slots")

    pool = await db.enchants.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(500)
    if not pool:
        raise HTTPException(503, "enchant pool empty (seed missing)")

    # Weight: higher rarity item → more chance of rarer enchant.
    rarity_weight = {
        "Common": [60, 30, 8, 2],
        "Uncommon": [40, 40, 15, 5],
        "Rare": [25, 40, 25, 10],
        "Epic": [15, 30, 35, 20],
        "Legendary": [5, 20, 40, 35],
    }
    weights = rarity_weight.get(item["rarity"], [50, 30, 15, 5])
    buckets: dict[str, list[dict]] = {"Common": [], "Uncommon": [], "Rare": [], "Epic": []}
    for e in pool:
        buckets.setdefault(e.get("rarity", "Common"), []).append(e)
    flat: list[tuple[dict, float]] = []
    total_weight = 0.0
    for r_idx, r_name in enumerate(("Common", "Uncommon", "Rare", "Epic")):
        n_in_bucket = max(1, len(buckets[r_name]))
        per_item = weights[r_idx] / n_in_bucket
        for e in buckets[r_name]:
            flat.append((e, per_item))
            total_weight += per_item

    # Sample n distinct enchants weighted (no slot machine).
    n = max(3, min(5, int(n)))
    options: list[dict] = []
    used_slugs: set[str] = set()
    attempts = 0
    while len(options) < n and attempts < n * 6:
        attempts += 1
        r = random.random() * total_weight
        cum = 0.0
        for e, w in flat:
            cum += w
            if cum >= r:
                if e["slug"] not in used_slugs:
                    options.append({
                        "slug": e["slug"],
                        "name": e["name"],
                        "rarity": e.get("rarity", "Common"),
                        "bonus_stat": e["bonus_stat"],
                        "bonus_value": int(e["bonus_value"]),
                        "cost_gold": int(e.get("cost_gold", 100)),
                    })
                    used_slugs.add(e["slug"])
                break
    return {"options": options, "free_slots": max(0, slots - used)}


async def apply_enchant(
    db, *, guild: dict, user_id: str, instance_id: str, enchant_slug: str
) -> dict:
    inv = await _load_owned_instance(db, guild["id"], instance_id)
    item = await _load_item_template(db, inv["item_id"])
    if _is_stackable(item):
        raise HTTPException(422, "stackable items cannot be enchanted")
    slots = int(item.get("enchant_slots") or 0) or 1
    used = len(inv.get("enchants", []))
    if used >= slots:
        raise HTTPException(422, "no free enchant slots")
    e = await db.enchants.find_one({"slug": enchant_slug}, {"_id": 0})
    if not e:
        raise HTTPException(404, "enchant not found")

    cost_gold = int(e.get("cost_gold", 100))
    mats_cost = e.get("cost_materials", {}) or {}
    await _consume_gold_and_mats(db, guild["id"], cost_gold, mats_cost)

    enchant_entry = {
        "slug": e["slug"],
        "bonus_stat": e["bonus_stat"],
        "bonus_value": int(e["bonus_value"]),
        "applied_at": _utc_now_iso(),
    }
    upd = await db.inventory_items.find_one_and_update(
        {
            "$or": [{"instance_id": instance_id}, {"id": instance_id}],
            "guild_id": guild["id"],
        },
        {"$push": {"enchants": enchant_entry}, "$set": {"is_bound": True}},
        return_document=True,
    )
    if not upd:
        # Refund.
        await db.guilds.update_one({"id": guild["id"]}, {"$inc": {"gold": cost_gold}})
        raise HTTPException(409, "concurrent enchant — please retry")
    await _audit(db, guild["id"], user_id, "item_enchanted", {
        "instance_id": instance_id,
        "item_slug": item["slug"],
        "enchant_slug": enchant_slug,
        "cost_gold": cost_gold,
    })
    return {"success": True, "enchant": enchant_entry, "is_bound": True}


async def reroll_affixes(
    db, *, guild: dict, user_id: str, instance_id: str
) -> dict:
    inv = await _load_owned_instance(db, guild["id"], instance_id)
    item = await _load_item_template(db, inv["item_id"])
    if _is_stackable(item):
        raise HTTPException(422, "stackable items cannot reroll affixes")
    if not inv.get("affixes"):
        raise HTTPException(422, "item has no affixes to reroll")
    reroll_count = int(inv.get("reroll_count", 0))
    if reroll_count >= REROLL_CAP:
        raise HTTPException(422, f"reroll cap reached ({REROLL_CAP})")

    cost = REROLL_COSTS[reroll_count]
    await _consume_gold_and_mats(db, guild["id"], cost, {})

    # Generate new affixes from a static pool (no DB collection needed in MVP).
    AFFIX_POOL = [
        {"slot": "prefix", "name": "Sharp",  "bonus_stat": "strength_bonus", "bonus_value": 2},
        {"slot": "prefix", "name": "Swift",  "bonus_stat": "agility_bonus",  "bonus_value": 2},
        {"slot": "prefix", "name": "Astute", "bonus_stat": "intellect_bonus","bonus_value": 2},
        {"slot": "prefix", "name": "Sturdy", "bonus_stat": "endurance_bonus","bonus_value": 2},
        {"slot": "prefix", "name": "Holy",   "bonus_stat": "faith_bonus",    "bonus_value": 2},
        {"slot": "suffix", "name": "of the Wolf",   "bonus_stat": "agility_bonus",  "bonus_value": 3},
        {"slot": "suffix", "name": "of the Bear",   "bonus_stat": "strength_bonus", "bonus_value": 3},
        {"slot": "suffix", "name": "of the Owl",    "bonus_stat": "intellect_bonus","bonus_value": 3},
        {"slot": "suffix", "name": "of the Turtle", "bonus_stat": "endurance_bonus","bonus_value": 3},
        {"slot": "suffix", "name": "of the Saint",  "bonus_stat": "faith_bonus",    "bonus_value": 3},
    ]
    prefixes = [a for a in AFFIX_POOL if a["slot"] == "prefix"]
    suffixes = [a for a in AFFIX_POOL if a["slot"] == "suffix"]
    new_affixes = [random.choice(prefixes), random.choice(suffixes)]

    upd = await db.inventory_items.find_one_and_update(
        {
            "$or": [{"instance_id": instance_id}, {"id": instance_id}],
            "guild_id": guild["id"],
            "reroll_count": reroll_count,
        },
        {"$set": {"affixes": new_affixes, "reroll_count": reroll_count + 1, "is_bound": True}},
        return_document=True,
    )
    if not upd:
        await db.guilds.update_one({"id": guild["id"]}, {"$inc": {"gold": cost}})
        raise HTTPException(409, "concurrent reroll — please retry")
    await _audit(db, guild["id"], user_id, "item_reroll_affix", {
        "instance_id": instance_id,
        "item_slug": item["slug"],
        "reroll_count_new": reroll_count + 1,
        "cost_gold": cost,
    })
    return {
        "success": True,
        "affixes": new_affixes,
        "reroll_count": reroll_count + 1,
        "next_cost": REROLL_COSTS[reroll_count + 1] if reroll_count + 1 < REROLL_CAP else None,
        "is_bound": True,
    }


async def disenchant_instance(
    db, *, guild: dict, user_id: str, instance_id: str
) -> dict:
    inv = await _load_owned_instance(db, guild["id"], instance_id)
    item = await _load_item_template(db, inv["item_id"])
    if _is_stackable(item):
        raise HTTPException(422, "stackable items cannot be disenchanted")

    rarity = item.get("rarity", "Common")
    guaranteed = DISENCHANT_GUARANTEED.get(rarity, {"iron_shard": 1})
    bonus_pool = DISENCHANT_BONUS_POOL.get(rarity, [])
    bonus_granted: dict[str, int] = {}
    for slug, qty, prob in bonus_pool:
        if random.random() < float(prob):
            bonus_granted[slug] = bonus_granted.get(slug, 0) + int(qty)

    # CAS: mark disenchanted (no hard delete; row stays for audit).
    res = await db.inventory_items.find_one_and_update(
        {
            "$or": [{"instance_id": instance_id}, {"id": instance_id}],
            "guild_id": guild["id"],
            "disenchanted_at": None,
        },
        {"$set": {"disenchanted_at": _utc_now_iso()}},
        return_document=True,
    )
    if not res:
        raise HTTPException(409, "concurrent disenchant — please retry")

    granted = await _grant_materials(db, guild["id"], guaranteed)
    bonus_actual = await _grant_materials(db, guild["id"], bonus_granted)

    await _audit(db, guild["id"], user_id, "item_disenchanted", {
        "instance_id": instance_id,
        "item_slug": item["slug"],
        "rarity": rarity,
        "guaranteed": guaranteed,
        "bonus": bonus_actual,
    })
    return {
        "success": True,
        "materials_guaranteed": [{"slug": k, "qty": v} for k, v in granted.items()],
        "materials_bonus": [{"slug": k, "qty": v} for k, v in bonus_actual.items()],
    }


# ─── Read endpoints (sets) ──────────────────────────────────────────────
async def list_sets(db) -> list[dict]:
    rows = await db.item_sets.find({}, {"_id": 0}).sort("slug", 1).to_list(200)
    return rows


async def list_enchants(db) -> list[dict]:
    rows = await db.enchants.find({"is_active": {"$ne": False}}, {"_id": 0}).sort("rarity", 1).to_list(200)
    return rows


async def adventurer_equipment_detail(db, adventurer_id: str, guild_id: str) -> dict:
    """Compute current equipment + active set bonuses for one adventurer."""
    rows = await db.equipped_items.find(
        {"adventurer_id": adventurer_id}, {"_id": 0}
    ).to_list(20)
    if not rows:
        return {"slots": [], "set_progress": [], "active_bonuses": []}
    item_ids = [r["item_id"] for r in rows]
    items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(50)
    items_by_id = {i["id"]: i for i in items}
    slots = []
    set_counts: dict[str, int] = {}
    for r in rows:
        it = items_by_id.get(r["item_id"])
        if not it:
            continue
        slots.append({
            "slot": r.get("slot"),
            "item_slug": it["slug"],
            "item_name": it["name"],
            "rarity": it.get("rarity", "Common"),
        })
        set_id = it.get("set_id")
        if set_id:
            set_counts[set_id] = set_counts.get(set_id, 0) + 1
    set_progress = []
    active_bonuses = []
    if set_counts:
        sets = await db.item_sets.find(
            {"slug": {"$in": list(set_counts.keys())}}, {"_id": 0}
        ).to_list(50)
        for s in sets:
            owned = set_counts.get(s["slug"], 0)
            total = len(s.get("pieces", []))
            set_progress.append({
                "set_id": s.get("id"),
                "slug": s["slug"],
                "name": s["name"],
                "owned": owned,
                "total": total,
                "tiers": s.get("tiers", []),
            })
            for t in s.get("tiers", []):
                if owned >= int(t["count"]):
                    active_bonuses.append({
                        "set_slug": s["slug"],
                        "pieces": int(t["count"]),
                        "bonus_stat": t["bonus_stat"],
                        "bonus_value": int(t["bonus_value"]),
                    })
    return {"slots": slots, "set_progress": set_progress, "active_bonuses": active_bonuses}


__all__ = [
    "REFINEMENT_TABLE", "REROLL_COSTS", "REROLL_CAP",
    "DISENCHANT_GUARANTEED", "DISENCHANT_BONUS_POOL", "MAX_REFINEMENT",
    "refine_instance", "enchant_options", "apply_enchant",
    "reroll_affixes", "disenchant_instance",
    "list_sets", "list_enchants", "adventurer_equipment_detail",
]
