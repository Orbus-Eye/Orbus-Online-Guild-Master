"""Phase 19.4b — Shop services (NPC system shop).

ROUND 13c — Materials triplicato + refresh ogni 2 ore.
  • Bucket di rotazione 2-ore (hour // 2 * 2) invece di reset giornaliero 04:00 UTC.
  • Candidate pool esteso (5 → 9 materiali Common/Uncommon/Rare lite).
  • Stock max triplicato per Common, raddoppiato per Uncommon (Rare invariato).
  • DAILY_OFFER_COUNT 6 → 18 (cap a `len(CANDIDATE_OFFERS)` = 9, mostra tutti i candidati per bucket).
  • Determinismo per bucket via sha256(bucket_key).
  • NO Legendary, NO P2W, NO premium.

Design originale:
  • Pool of ~12 candidate items (Common/Uncommon materials + consumables).
    NEVER Legendary, NEVER forge endgame, NEVER P2W.
  • Deterministic pick of N offers via hashlib seed (bucket_key).
  • Buy price = base_price (anchored to rarity × level); sell price = 40% buy
    (anti-exploit gap).
  • Atomic ops with manual rollback (same pattern as auction).
  • Audit log: shop_system_purchase / shop_system_sale.
  • Rate limit: 10 transactions / 10s per user (lighter than chat as
    purchases are slower).
  • Max quantity per transaction: 99.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException

from app.audit.log import write_audit


logger = logging.getLogger("orbus.shop")

# ROUND 13c — 2-hour bucket instead of daily reset.
BUCKET_HOURS = 2
# DAILY_RESET_HOUR_UTC kept as legacy constant (no longer drives rotation but
# referenced by an old test). Logical reset window is now BUCKET_HOURS.
DAILY_RESET_HOUR_UTC = 4
# Show all candidates per bucket (cap = len(CANDIDATE_OFFERS)).
DAILY_OFFER_COUNT = 18
MAX_TX_QUANTITY = 99
SELL_PRICE_MULTIPLIER = 0.4  # sell to system = 40% of buy_price (anti-exploit)
RATE_LIMIT_COUNT = 10
RATE_LIMIT_WINDOW_S = 10


# ─── Candidate pool (hardcoded — never grows without code review) ─────────
# ROUND 13c — stock_max triplicato per Common, raddoppiato per Uncommon,
# invariato per Rare (no flooding endgame economy).
CANDIDATE_OFFERS: list[dict] = [
    # Common materials (×3 stock vs legacy)
    {"slug": "iron_shard",          "buy_price": 8,  "max_quantity": 75, "rarity": "Common"},
    {"slug": "raw_leather",         "buy_price": 6,  "max_quantity": 90, "rarity": "Common"},
    {"slug": "healing_herb",        "buy_price": 5,  "max_quantity": 90, "rarity": "Common"},
    # Common consumables (×3 stock vs legacy)
    {"slug": "minor_healing_potion","buy_price": 12, "max_quantity": 60, "rarity": "Common"},
    {"slug": "travel_ration",       "buy_price": 4,  "max_quantity": 120, "rarity": "Common"},
    # Uncommon materials (×2 stock vs legacy)
    {"slug": "arcane_dust",         "buy_price": 22, "max_quantity": 24, "rarity": "Uncommon"},
    {"slug": "dull_gem",            "buy_price": 18, "max_quantity": 30, "rarity": "Uncommon"},
    {"slug": "lesser_arcane_dust",  "buy_price": 28, "max_quantity": 20, "rarity": "Uncommon"},
    # Rare crafting material (low stock, gated by price)
    {"slug": "greater_arcane_dust", "buy_price": 95, "max_quantity": 4,  "rarity": "Rare"},
]


# ─── Date / cutoff helpers ────────────────────────────────────────────────
def _shop_bucket_key(now: Optional[datetime] = None) -> str:
    """ROUND 13c — Deterministic 2-hour bucket key.

    Format: ``YYYY-MM-DDTHH`` where HH is rounded down to the nearest 2h
    (00, 02, 04, …, 22). Two requests in the same bucket → same rotation.
    """
    now = now or datetime.now(timezone.utc)
    hour_bucket = (now.hour // BUCKET_HOURS) * BUCKET_HOURS
    return f"{now.strftime('%Y-%m-%d')}T{hour_bucket:02d}"


def _shop_day_key(now: Optional[datetime] = None) -> str:
    """Backwards-compat alias for legacy callers/tests. Returns the 2-hour
    bucket key (renamed for clarity in ROUND 13c).
    """
    return _shop_bucket_key(now)


def _next_reset_at(now: Optional[datetime] = None) -> datetime:
    """Compute the start of the *next* 2-hour bucket (ISO timestamp).

    Used by FE for the live countdown "Prossimo refresh tra Xh Ym".
    """
    now = now or datetime.now(timezone.utc)
    cur_bucket_hour = (now.hour // BUCKET_HOURS) * BUCKET_HOURS
    cur_bucket_start = now.replace(
        hour=cur_bucket_hour, minute=0, second=0, microsecond=0
    )
    return cur_bucket_start + timedelta(hours=BUCKET_HOURS)


def _daily_offers_pick(day_key: str) -> list[dict]:
    """Deterministic pick of N offers for a given bucket key.

    Uses sha256(bucket_key) as a stable seed → same offers all bucket,
    different rotation each bucket. No randomness, no external state.

    ROUND 13c: since `DAILY_OFFER_COUNT` (18) >= `len(CANDIDATE_OFFERS)`
    (9), every bucket exposes all candidates. The sha256 shuffle controls
    *order* only — useful for UX freshness.
    """
    digest = hashlib.sha256(day_key.encode()).digest()
    indices = list(range(len(CANDIDATE_OFFERS)))
    indices.sort(key=lambda i: digest[i % len(digest)])
    cap = min(DAILY_OFFER_COUNT, len(CANDIDATE_OFFERS))
    return [CANDIDATE_OFFERS[i] for i in indices[:cap]]


# ─── Index bootstrap ──────────────────────────────────────────────────────
async def ensure_shop_indexes(db) -> None:
    await db.shop_daily_offers.create_index(
        [("day_key", 1), ("offer_id", 1)],
        name="shop_day_offer_idx", unique=True,
    )
    await db.shop_daily_offers.create_index("day_key", name="shop_day_idx")


# ─── Daily offer seed (idempotent, called on each GET) ────────────────────
async def get_or_seed_daily_offers(db) -> list[dict]:
    """Return current-bucket offers, seeding them if missing. Idempotent.

    ROUND 13c: bucket rotation 2h, allows materials with `is_active`
    missing (defaults True) for legacy seed compatibility (Round 6B.3
    materials never had `is_active` set).
    """
    day_key = _shop_bucket_key()
    rows = await db.shop_daily_offers.find(
        {"day_key": day_key}, {"_id": 0}
    ).to_list(50)
    if rows:
        return rows
    # Seed this bucket's offers
    picks = _daily_offers_pick(day_key)
    docs = []
    for pick in picks:
        # ROUND 13c — accept materials with `is_active` missing (default True).
        item = await db.items.find_one(
            {"slug": pick["slug"], "is_active": {"$ne": False},
             "is_test": {"$ne": True}},
            {"_id": 0, "id": 1, "slug": 1, "name": 1, "rarity": 1,
             "item_type": 1, "level_required": 1, "display_name_it": 1,
             "display_name_en": 1, "is_tradeable": 1, "is_premium": 1,
             "is_cosmetic_real_money": 1},
        )
        if not item or item.get("is_tradeable") is False:
            continue
        if item.get("is_premium") or item.get("is_cosmetic_real_money"):
            continue
        docs.append({
            "offer_id": f"{day_key}_{pick['slug']}",
            "day_key": day_key,
            "item_slug": item["slug"],
            "item_template_id": item["id"],
            "item_name_it": item.get("display_name_it") or item.get("name"),
            "item_name_en": item.get("display_name_en") or item.get("name"),
            "rarity": item.get("rarity", "Common"),
            "item_type": item.get("item_type", "material"),
            "level_required": int(item.get("level_required", 1)),
            "buy_price": int(pick["buy_price"]),
            "max_quantity": int(pick["max_quantity"]),
            "stock_remaining": int(pick["max_quantity"]),
        })
    if docs:
        try:
            await db.shop_daily_offers.insert_many(docs, ordered=False)
            # ROUND 13c — audit rotation event (best-effort).
            try:
                await write_audit(
                    db, event_type="market_rotation_refreshed",
                    source="shop.bucket_seed",
                    metadata={"bucket_key": day_key, "offer_count": len(docs)},
                )
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            # Another concurrent call seeded — fetch and continue.
            logger.info("shop seed race: %s", exc)
        rows = await db.shop_daily_offers.find(
            {"day_key": day_key}, {"_id": 0}
        ).to_list(50)
    return rows


def offer_public(o: dict) -> dict:
    """Project a daily offer to its public shape."""
    return {
        "offer_id": o["offer_id"],
        "item": {
            "slug": o["item_slug"],
            "name": o.get("item_name_it") or o.get("item_name_en") or o["item_slug"],
            "rarity": o.get("rarity", "Common"),
            "item_type": o.get("item_type", "material"),
            "level_required": int(o.get("level_required", 1)),
        },
        "buy_price": int(o["buy_price"]),
        "sell_price": int(round(int(o["buy_price"]) * SELL_PRICE_MULTIPLIER)),
        "stock_remaining": int(o.get("stock_remaining", 0)),
        "max_quantity": int(o.get("max_quantity", 0)),
    }


# ─── Rate limit ───────────────────────────────────────────────────────────
async def _check_rate_limit(db, user_id: str) -> None:
    cutoff_iso = (
        datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_WINDOW_S)
    ).isoformat()
    recent = await db.audit_log.count_documents({
        "actor_user_id": user_id,
        "event_type": {"$in": ["shop_system_purchase", "shop_system_sale"]},
        "created_at": {"$gt": cutoff_iso},
    })
    if recent >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="shop.rate_limited")


# ─── Buy ──────────────────────────────────────────────────────────────────
async def buy_from_shop(
    db, *, current_user: dict, guild: dict, offer_id: str, quantity: int
) -> dict:
    if not isinstance(quantity, int) or quantity < 1:
        raise HTTPException(status_code=422, detail="shop.invalid_quantity")
    if quantity > MAX_TX_QUANTITY:
        raise HTTPException(status_code=422, detail="shop.quantity_too_high")

    offer = await db.shop_daily_offers.find_one(
        {"offer_id": offer_id, "day_key": _shop_day_key()}, {"_id": 0}
    )
    if not offer:
        # Either non-existent or expired (different day_key)
        any_offer = await db.shop_daily_offers.find_one({"offer_id": offer_id}, {"_id": 0, "day_key": 1})
        if any_offer:
            raise HTTPException(status_code=410, detail="shop.offer_expired")
        raise HTTPException(status_code=404, detail="shop.offer_not_found")

    if int(offer.get("stock_remaining", 0)) < quantity:
        raise HTTPException(status_code=409, detail="shop.out_of_stock")

    total_cost = int(offer["buy_price"]) * quantity
    if int(guild.get("gold", 0)) < total_cost:
        raise HTTPException(status_code=402, detail="shop.insufficient_gold")

    await _check_rate_limit(db, current_user["id"])

    # 1) Atomic conditional stock decrement
    res = await db.shop_daily_offers.update_one(
        {"offer_id": offer_id, "day_key": _shop_day_key(),
         "stock_remaining": {"$gte": quantity}},
        {"$inc": {"stock_remaining": -quantity}},
    )
    if res.modified_count != 1:
        raise HTTPException(status_code=409, detail="shop.race_lost")

    # 2) Atomic conditional gold debit
    res = await db.guilds.update_one(
        {"id": guild["id"], "gold": {"$gte": total_cost}},
        {"$inc": {"gold": -total_cost}},
    )
    if res.modified_count != 1:
        # Rollback stock
        await db.shop_daily_offers.update_one(
            {"offer_id": offer_id}, {"$inc": {"stock_remaining": quantity}}
        )
        raise HTTPException(status_code=402, detail="shop.insufficient_gold")

    # 3) Upsert inventory (same pattern as expedition loot post-P19.2 fix)
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        await db.inventory_items.update_one(
            {"guild_id": guild["id"], "item_id": offer["item_template_id"]},
            {
                "$inc": {"quantity": quantity},
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "instance_id": str(uuid.uuid4()),
                    "guild_id": guild["id"],
                    "item_id": offer["item_template_id"],
                    "acquired_at": now_iso,
                    "source": "shop",
                    "is_bound": False,
                    "disenchanted_at": None,
                    "refinement_level": 0,
                    "enchants": [],
                    "affixes": [],
                    "reroll_count": 0,
                },
            },
            upsert=True,
        )
    except Exception as exc:
        # Rollback gold + stock
        await db.guilds.update_one({"id": guild["id"]}, {"$inc": {"gold": total_cost}})
        await db.shop_daily_offers.update_one(
            {"offer_id": offer_id}, {"$inc": {"stock_remaining": quantity}}
        )
        logger.exception("shop buy inventory upsert failed: %s", exc)
        raise HTTPException(status_code=500, detail="shop.internal_error")

    # 4) Audit log (best-effort)
    await write_audit(
        db, event_type="shop_system_purchase",
        actor_user_id=current_user["id"], actor_guild_id=guild["id"],
        item_slug=offer["item_slug"], item_template_id=offer["item_template_id"],
        quantity=quantity, gold_delta=-total_cost,
        source="shop", related_entity_id=offer_id,
    )

    # 5) Return refreshed guild gold + offer
    updated_offer = await db.shop_daily_offers.find_one(
        {"offer_id": offer_id}, {"_id": 0}
    )
    updated_guild = await db.guilds.find_one({"id": guild["id"]}, {"_id": 0, "gold": 1})
    return {
        "success": True,
        "offer": offer_public(updated_offer),
        "quantity": quantity,
        "gold_spent": total_cost,
        "guild_gold": int(updated_guild["gold"]),
    }


# ─── Sell ─────────────────────────────────────────────────────────────────
SELLABLE_REASONS = {
    "bound": "shop.sell.bound",
    "equipped": "shop.sell.equipped",
    "listed": "shop.sell.listed",
    "not_tradeable": "shop.sell.not_tradeable",
    "no_stock": "shop.sell.no_stock",
}


async def _resolve_sell_price_for_item(item: dict) -> int:
    """Best-effort sell price: 40% of any candidate-pool match; fallback
    to a tier formula (rarity × level)."""
    for c in CANDIDATE_OFFERS:
        if c["slug"] == item["slug"]:
            return int(round(int(c["buy_price"]) * SELL_PRICE_MULTIPLIER))
    rarity_mult = {"Common": 4, "Uncommon": 10, "Rare": 25, "Epic": 60, "Legendary": 0}
    mult = rarity_mult.get(item.get("rarity", "Common"), 4)
    if mult == 0:
        return 0  # legendary → not sellable
    return max(1, int(round(mult * int(item.get("level_required", 1)) * SELL_PRICE_MULTIPLIER)))


async def sell_to_shop(
    db, *, current_user: dict, guild: dict, instance_id: str, quantity: int
) -> dict:
    if not isinstance(quantity, int) or quantity < 1:
        raise HTTPException(status_code=422, detail="shop.invalid_quantity")
    if quantity > MAX_TX_QUANTITY:
        raise HTTPException(status_code=422, detail="shop.quantity_too_high")

    # Find inventory row (by instance_id OR fall back to internal id)
    row = await db.inventory_items.find_one(
        {"$or": [{"instance_id": instance_id}, {"id": instance_id}],
         "guild_id": guild["id"]},
        {"_id": 0},
    )
    if not row:
        raise HTTPException(status_code=404, detail="shop.item_not_found")

    # Eligibility checks (preserve detail strings for i18n)
    if row.get("is_bound") is True:
        from app.core.bound_errors import raise_market_not_sellable
        raise_market_not_sellable(
            source="shop.sell_to_shop",
            bound_to_adventurer_id=row.get("bound_to_adventurer_id"),
        )

    # ROUND 6B.4 Task 2 — adventurer-bound guard for NPC shop sale.
    if row.get("bound_to_adventurer_id"):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "market.bound_to_adventurer_not_sellable",
                "source": "shop.sell_to_shop",
                "bound_to_adventurer_id": row.get("bound_to_adventurer_id"),
                "user_message": (
                    "Questo oggetto è legato a un avventuriero e non può "
                    "essere venduto al mercante."
                ),
            },
        )

    item = await db.items.find_one(
        {"id": row["item_id"]}, {"_id": 0},
    )
    if not item:
        raise HTTPException(status_code=404, detail="shop.item_template_not_found")
    if item.get("is_tradeable") is False or item.get("can_be_sold_for_gold") is False:
        raise HTTPException(status_code=409, detail=SELLABLE_REASONS["not_tradeable"])

    # Equipped / listed checks
    eq_count = await db.equipped_items.count_documents(
        {"guild_id": guild["id"], "item_id": row["item_id"]}
    )
    locked = int(row.get("market_locked_qty", 0))
    total = int(row.get("quantity", 0))
    available = max(0, total - eq_count - locked)
    if available < quantity:
        # Differentiate the message
        if eq_count > 0 and (total - eq_count) < quantity:
            raise HTTPException(status_code=409, detail=SELLABLE_REASONS["equipped"])
        if locked > 0:
            raise HTTPException(status_code=409, detail=SELLABLE_REASONS["listed"])
        raise HTTPException(status_code=409, detail=SELLABLE_REASONS["no_stock"])

    await _check_rate_limit(db, current_user["id"])

    # Compute sell price (per unit)
    unit_price = await _resolve_sell_price_for_item(item)
    if unit_price <= 0:
        raise HTTPException(status_code=409, detail=SELLABLE_REASONS["not_tradeable"])
    total_proceeds = unit_price * quantity

    # 1) Atomic inventory decrement
    res = await db.inventory_items.update_one(
        {"id": row["id"], "quantity": {"$gte": quantity}},
        {"$inc": {"quantity": -quantity}},
    )
    if res.modified_count != 1:
        raise HTTPException(status_code=409, detail="shop.race_lost")

    # 2) Credit gold
    try:
        await db.guilds.update_one(
            {"id": guild["id"]}, {"$inc": {"gold": total_proceeds}}
        )
    except Exception as exc:
        # Rollback inventory
        await db.inventory_items.update_one(
            {"id": row["id"]}, {"$inc": {"quantity": quantity}}
        )
        logger.exception("shop sell gold credit failed: %s", exc)
        raise HTTPException(status_code=500, detail="shop.internal_error")

    # 3) Audit log
    await write_audit(
        db, event_type="shop_system_sale",
        actor_user_id=current_user["id"], actor_guild_id=guild["id"],
        item_slug=item["slug"], item_template_id=item["id"],
        quantity=quantity, gold_delta=total_proceeds,
        source="shop", related_entity_id=row["id"],
    )

    updated_guild = await db.guilds.find_one({"id": guild["id"]}, {"_id": 0, "gold": 1})
    return {
        "success": True,
        "item_sold": {
            "slug": item["slug"],
            "name": item.get("display_name_it") or item.get("name"),
            "rarity": item.get("rarity"),
        },
        "quantity": quantity,
        "unit_price": unit_price,
        "gold_earned": total_proceeds,
        "guild_gold": int(updated_guild["gold"]),
    }


__all__ = [
    "ensure_shop_indexes",
    "get_or_seed_daily_offers",
    "offer_public",
    "buy_from_shop",
    "sell_to_shop",
    "_next_reset_at",
    "_shop_day_key",
    "SELL_PRICE_MULTIPLIER",
    "MAX_TX_QUANTITY",
    "RATE_LIMIT_COUNT",
]
