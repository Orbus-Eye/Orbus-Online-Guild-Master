"""Phase 14.8 (ROUND 3.C) — Marketplace / Auction House.

Endpoints implemented (4 path-strings, 5 HTTP routes):
  - GET    /api/market/listings              → public listings with filters
  - POST   /api/market/listings              → create a listing (lock inventory)
  - DELETE /api/market/listings/{listing_id} → cancel own listing (refund stock)
  - POST   /api/market/listings/{listing_id}/buy → atomic purchase
  - GET    /api/market/listings/mine         → seller-side own listings

Atomicity (no Mongo transactions on the stand-alone preview cluster):
We use a sequence of conditional updates that double as locks. Each step
either succeeds with `modified_count == 1` and proceeds, or fails and
triggers a manual revert of the prior $inc / $set operations. At worst
the system returns to the pre-call state (no item duplication, no gold
leak).

Privacy: GET responses NEVER expose `seller_user_id` or `buyer_user_id`,
only the guild_name snapshot captured at listing/purchase time.

Tax / fee: a single MARKET_FEE_PCT (configurable constant) applied on
the seller proceeds. Buyer pays full price, seller receives
price * (1 - fee/100). The platform fee is currently a sink (gold
removed from circulation) — by design, mirrors Round 3.B/3.D
mechanics. It is documented in the public listing response.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from app.audit.log import write_audit
from app.items.services import item_public


logger = logging.getLogger("orbus.market")

MARKET_FEE_PCT = 5  # 5% fee on seller proceeds; buyer pays full price
LISTING_STATUS_ACTIVE = "active"
LISTING_STATUS_SOLD = "sold"
LISTING_STATUS_CANCELLED = "cancelled"
LISTING_STATUS_EXPIRED = "expired"

_VALID_SORT = {"price_asc", "price_desc", "level", "created_at"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _localized_name(item: dict, lang: str = "it") -> str:
    if lang == "en":
        return (
            item.get("display_name_en")
            or item.get("name")
            or item.get("slug", "")
        )
    return (
        item.get("display_name_it")
        or item.get("name")
        or item.get("slug", "")
    )


async def _equipped_count(db, guild_id: str, item_id: str) -> int:
    return await db.equipped_items.count_documents(
        {"guild_id": guild_id, "item_id": item_id}
    )


async def _available_qty(db, guild_id: str, item_id: str) -> tuple[int, dict]:
    """Return (available, inventory_row). Available = quantity - equipped - market_locked."""
    row = await db.inventory_items.find_one(
        {"guild_id": guild_id, "item_id": item_id}, {"_id": 0}
    )
    if not row:
        return 0, {}
    eq = await _equipped_count(db, guild_id, item_id)
    locked = int(row.get("market_locked_qty", 0))
    available = max(
        0, int(row.get("quantity", 0)) - eq - locked
    )
    return available, row


def listing_public(listing: dict, *, lang: str = "it", include_buyer: bool = False) -> dict:
    name = (
        listing.get("item_display_name_en") if lang == "en"
        else listing.get("item_display_name_it")
    ) or listing.get("item_slug", "")
    out = {
        "id": listing["id"],
        "item": {
            "slug": listing["item_slug"],
            "name": name,
            "rarity": listing.get("item_rarity"),
            "item_type": listing.get("item_type"),
            "level_required": int(listing.get("item_level_required", 1)),
        },
        "quantity": int(listing.get("quantity", 0)),
        "price_per_unit": int(listing.get("price_per_unit", 0)),
        "total_price": int(listing.get("price_per_unit", 0)) * int(listing.get("quantity", 0)),
        "fee_percentage": int(listing.get("fee_percentage", MARKET_FEE_PCT)),
        "status": listing.get("status", LISTING_STATUS_ACTIVE),
        "created_at": listing.get("created_at"),
        "seller": {
            "guild_name": listing.get("seller_guild_name"),
            # ROUND 6B.3 Wave 3 — FIX BUG 1: expose seller_user_id (NOT PII —
            # internal UUID, never email/username) so the FE can compute
            # `isOwn` and visibly disable the Buy button on the player's own
            # listings, instead of relying on a backend 4xx after click.
            "user_id": listing["seller_user_id"],
        },
    }
    if include_buyer and listing.get("buyer_guild_name"):
        out["buyer"] = {"guild_name": listing.get("buyer_guild_name")}
    if listing.get("sold_at"):
        out["sold_at"] = listing["sold_at"]
    return out


async def ensure_market_indexes(db) -> None:
    """Idempotent index creation. Called from lifespan."""
    try:
        await db.market_listings.create_index(
            [("id", 1)], unique=True, name="market_listings_id_unique"
        )
        await db.market_listings.create_index(
            [("status", 1), ("item_slug", 1), ("created_at", -1)],
            name="market_listings_status_slug_created_idx",
        )
        await db.market_listings.create_index(
            [("seller_user_id", 1), ("status", 1), ("created_at", -1)],
            name="market_listings_seller_status_idx",
        )
        await db.market_listings.create_index(
            [("status", 1), ("price_per_unit", 1)],
            name="market_listings_status_price_idx",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_market_indexes failed: %s", exc)


# ─── Public read endpoints ──────────────────────────────────────────────


async def list_active_listings(
    db,
    *,
    item_type: Optional[str] = None,
    rarity: Optional[str] = None,
    level_max: Optional[int] = None,
    price_max: Optional[int] = None,
    name_contains: Optional[str] = None,
    sort_by: str = "created_at",
    limit: int = 50,
    offset: int = 0,
    lang: str = "it",
) -> dict:
    if sort_by not in _VALID_SORT:
        raise HTTPException(status_code=400, detail=f"sort_by must be in {sorted(_VALID_SORT)}")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be in [1, 100]")
    if offset < 0 or offset > 1000:
        raise HTTPException(status_code=400, detail="offset must be in [0, 1000]")

    q: dict = {"status": LISTING_STATUS_ACTIVE, "is_test": {"$ne": True}}
    if item_type:
        q["item_type"] = item_type
    if rarity:
        q["item_rarity"] = rarity
    if level_max is not None:
        q["item_level_required"] = {"$lte": int(level_max)}
    if price_max is not None:
        q["price_per_unit"] = {"$lte": int(price_max)}
    if name_contains:
        # Search across both localized snapshots (case-insensitive)
        rx = {"$regex": name_contains, "$options": "i"}
        q["$or"] = [
            {"item_display_name_it": rx},
            {"item_display_name_en": rx},
            {"item_slug": rx},
        ]

    sort_spec = {
        "price_asc":   [("price_per_unit", 1), ("created_at", -1)],
        "price_desc":  [("price_per_unit", -1), ("created_at", -1)],
        "level":       [("item_level_required", 1), ("price_per_unit", 1)],
        "created_at":  [("created_at", -1)],
    }[sort_by]

    total = await db.market_listings.count_documents(q)
    rows = await (
        db.market_listings.find(q, {"_id": 0})
        .sort(sort_spec)
        .skip(offset)
        .limit(limit)
        .to_list(limit)
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "listings": [listing_public(r, lang=lang) for r in rows],
    }


async def list_my_listings(
    db, user_id: str, *, lang: str = "it", limit: int = 100
) -> dict:
    rows = await (
        db.market_listings.find(
            {"seller_user_id": user_id}, {"_id": 0}
        )
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )
    return {
        "listings": [listing_public(r, lang=lang, include_buyer=True) for r in rows],
    }


# ─── Create listing ─────────────────────────────────────────────────────


async def create_listing(
    db,
    user: dict,
    guild: dict,
    *,
    item_slug: str,
    quantity: int,
    price_per_unit: int,
    lang: str = "it",
) -> dict:
    if not isinstance(quantity, int) or quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be a positive integer")
    if not isinstance(price_per_unit, int) or price_per_unit <= 0:
        raise HTTPException(status_code=400, detail="price_per_unit must be a positive integer")

    item = await db.items.find_one(
        {"slug": item_slug, "is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.get("is_tradeable") is False:
        raise HTTPException(status_code=400, detail="Item is not tradeable")
    if item.get("can_be_sold_for_gold") is False:
        raise HTTPException(status_code=400, detail="Item cannot be sold for gold")

    available, row = await _available_qty(db, guild["id"], item["id"])
    if available < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough available quantity (have {available}, want {quantity})",
        )

    # 🔒 ROUND 4 BoE GUARD (Q8 LOCKED): a refined / enchanted / rerolled
    # inventory row cannot be listed on the marketplace. Reject 422 with a
    # clear, i18n-friendly detail string.
    bound_row = await db.inventory_items.find_one(
        {
            "guild_id": guild["id"],
            "item_id": item["id"],
            "is_bound": True,
            "disenchanted_at": None,
        },
        {"_id": 0, "id": 1, "instance_id": 1},
    )
    if bound_row:
        raise HTTPException(
            status_code=422,
            detail="market.bound_item_not_sellable",  # frontend resolves via i18n
        )

    # ROUND 6B.4 Task 2 — adventurer-bound guard.
    # Items bound to a specific adventurer can never be listed on the auction.
    adv_bound_row = await db.inventory_items.find_one(
        {
            "guild_id": guild["id"],
            "item_id": item["id"],
            "bound_to_adventurer_id": {"$ne": None},
        },
        {"_id": 0, "id": 1, "bound_to_adventurer_id": 1},
    )
    if adv_bound_row:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "auction.bound_to_adventurer_not_listable",
                "source": "market.create_listing",
                "bound_to_adventurer_id": adv_bound_row.get("bound_to_adventurer_id"),
                "user_message": (
                    "Questo oggetto è legato a un avventuriero e non può "
                    "essere messo all'asta."
                ),
            },
        )

    # 1) Conditional lock: atomically increase market_locked_qty as long
    #    as quantity - equipped - market_locked - requested >= 0.
    #    We approximate equipped count once (race window: a parallel
    #    equip would reduce available; the lock-check below is the
    #    primary defence).
    eq = await _equipped_count(db, guild["id"], item["id"])
    res = await db.inventory_items.update_one(
        {
            "guild_id": guild["id"],
            "item_id": item["id"],
            # invariant: existing quantity covers equipped + already-locked + new lock
            "$expr": {
                "$gte": [
                    {"$subtract": ["$quantity", {"$add": [eq, {"$ifNull": ["$market_locked_qty", 0]}]}]},
                    quantity,
                ]
            },
        },
        {"$inc": {"market_locked_qty": quantity}},
    )
    if res.modified_count != 1:
        raise HTTPException(
            status_code=409,
            detail="Inventory changed during listing — try again",
        )

    # 2) Insert listing doc
    now = _utc_now()
    listing_id = str(uuid.uuid4())
    doc = {
        "id": listing_id,
        "seller_user_id": user["id"],
        "seller_guild_id": guild["id"],
        "seller_guild_name": guild["name"],
        "item_slug": item["slug"],
        "item_template_id": item["id"],
        "item_display_name_it": item.get("display_name_it") or item.get("name"),
        "item_display_name_en": item.get("display_name_en") or item.get("name"),
        "item_rarity": item.get("rarity"),
        "item_type": item.get("item_type"),
        "item_level_required": int(item.get("level_required", 1)),
        "quantity": int(quantity),
        "price_per_unit": int(price_per_unit),
        "status": LISTING_STATUS_ACTIVE,
        "created_at": now.isoformat(),
        "sold_at": None,
        "buyer_user_id": None,
        "buyer_guild_id": None,
        "buyer_guild_name": None,
        "fee_percentage": MARKET_FEE_PCT,
        "metadata": {},
        "is_test": False,
    }
    try:
        await db.market_listings.insert_one(doc)
    except Exception:  # revert inventory lock
        await db.inventory_items.update_one(
            {"guild_id": guild["id"], "item_id": item["id"]},
            {"$inc": {"market_locked_qty": -quantity}},
        )
        raise HTTPException(status_code=500, detail="Failed to persist listing")

    # 3) Best-effort audit
    try:
        await write_audit(
            db, event_type="market_listing_created",
            actor_user_id=user["id"], actor_guild_id=guild["id"],
            item_slug=item["slug"], item_template_id=item["id"],
            quantity=int(quantity),
            source="market",
            related_entity_id=listing_id,
            metadata={"price_per_unit": int(price_per_unit)},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit write failed in create_listing: %s", exc)

    # Phase 14.1 — weekly quest progress (best-effort, non-critical)
    try:
        from app.quests.services import increment_weekly_progress
        await increment_weekly_progress(
            db, guild["id"], "market_listings_created", 1
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("weekly quest hook failed in create_listing: %s", exc)
    # ROUND 6D — contract progress for the SELLER (listing created)
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(
            db, guild["id"], "market_listings_created", 1,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("contract hook failed in create_listing: %s", exc)
    # ROUND 6E — auction_listings_created (alias counter; gated by auction_house at generation time)
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(
            db, guild["id"], "auction_listings_created", 1,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("auction contract hook failed in create_listing: %s", exc)

    total_price = int(price_per_unit) * int(quantity)
    fee = total_price * MARKET_FEE_PCT // 100
    return {
        "success": True,
        "listing_id": listing_id,
        "item": {
            "slug": item["slug"],
            "name": _localized_name(item, lang),
            "rarity": item.get("rarity"),
        },
        "quantity": int(quantity),
        "price_per_unit": int(price_per_unit),
        "total_price": total_price,
        "fee_estimate": fee,
        "seller_proceeds_estimate": total_price - fee,
    }


# ─── Cancel listing ─────────────────────────────────────────────────────


async def cancel_listing(db, user: dict, guild: dict, listing_id: str) -> dict:
    listing = await db.market_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["seller_user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the seller can cancel this listing")
    if listing["status"] != LISTING_STATUS_ACTIVE:
        raise HTTPException(
            status_code=400, detail=f"Listing is not active (status={listing['status']})"
        )

    qty = int(listing.get("quantity", 0))

    # 1) Flip status atomically — guard on still active
    res = await db.market_listings.update_one(
        {"id": listing_id, "status": LISTING_STATUS_ACTIVE},
        {
            "$set": {
                "status": LISTING_STATUS_CANCELLED,
                "updated_at": _utc_now().isoformat(),
            }
        },
    )
    if res.modified_count != 1:
        raise HTTPException(
            status_code=409, detail="Listing status changed during cancel — try again"
        )

    # 2) Release reserved inventory
    await db.inventory_items.update_one(
        {"guild_id": guild["id"], "item_id": listing["item_template_id"]},
        {"$inc": {"market_locked_qty": -qty}},
    )

    # 3) Audit
    try:
        await write_audit(
            db, event_type="market_listing_cancelled",
            actor_user_id=user["id"], actor_guild_id=guild["id"],
            item_slug=listing["item_slug"],
            item_template_id=listing["item_template_id"],
            quantity=qty,
            source="market", related_entity_id=listing_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit write failed in cancel_listing: %s", exc)

    return {"success": True, "listing_id": listing_id, "item_restored_quantity": qty}


# ─── Buy ────────────────────────────────────────────────────────────────


async def buy_listing(
    db, buyer_user: dict, buyer_guild: dict, listing_id: str,
    *, quantity: Optional[int] = None, lang: str = "it",
) -> dict:
    listing = await db.market_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["status"] != LISTING_STATUS_ACTIVE:
        raise HTTPException(
            status_code=409, detail=f"Listing not available (status={listing['status']})"
        )
    if listing["seller_user_id"] == buyer_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot buy your own listing")

    listing_qty = int(listing["quantity"])
    qty = listing_qty if quantity is None else int(quantity)
    if qty <= 0 or qty > listing_qty:
        raise HTTPException(
            status_code=400,
            detail=f"quantity must be in [1, {listing_qty}]",
        )

    price = int(listing["price_per_unit"])
    total_cost = price * qty
    fee_pct = int(listing.get("fee_percentage", MARKET_FEE_PCT))
    fee = total_cost * fee_pct // 100
    seller_proceeds = total_cost - fee

    # ─── Step 1: atomically lock the listing slice ───
    # If qty == remaining, flip to sold + capture buyer. Otherwise decrement quantity.
    flips_to_sold = (qty == listing_qty)
    now_iso = _utc_now().isoformat()
    if flips_to_sold:
        res = await db.market_listings.update_one(
            {
                "id": listing_id,
                "status": LISTING_STATUS_ACTIVE,
                "quantity": {"$gte": qty},
            },
            {
                "$set": {
                    "status": LISTING_STATUS_SOLD,
                    "sold_at": now_iso,
                    "buyer_user_id": buyer_user["id"],
                    "buyer_guild_id": buyer_guild["id"],
                    "buyer_guild_name": buyer_guild["name"],
                    "updated_at": now_iso,
                },
                "$inc": {"quantity": -qty},
            },
        )
    else:
        res = await db.market_listings.update_one(
            {
                "id": listing_id,
                "status": LISTING_STATUS_ACTIVE,
                "quantity": {"$gte": qty},
            },
            {
                "$inc": {"quantity": -qty},
                "$set": {"updated_at": now_iso},
            },
        )
    if res.modified_count != 1:
        raise HTTPException(
            status_code=409, detail="Listing changed during purchase — try again"
        )

    async def _revert_listing():
        if flips_to_sold:
            await db.market_listings.update_one(
                {"id": listing_id},
                {
                    "$set": {
                        "status": LISTING_STATUS_ACTIVE,
                        "sold_at": None,
                        "buyer_user_id": None,
                        "buyer_guild_id": None,
                        "buyer_guild_name": None,
                    },
                    "$inc": {"quantity": qty},
                },
            )
        else:
            await db.market_listings.update_one(
                {"id": listing_id}, {"$inc": {"quantity": qty}}
            )

    # ─── Step 2: decrement buyer gold (conditional) ───
    gold_res = await db.guilds.update_one(
        {"id": buyer_guild["id"], "gold": {"$gte": total_cost}},
        {"$inc": {"gold": -total_cost}, "$set": {"updated_at": now_iso}},
    )
    if gold_res.modified_count != 1:
        await _revert_listing()
        raise HTTPException(status_code=409, detail="Not enough gold")

    # ─── Step 3: credit seller gold (unconditional) ───
    try:
        await db.guilds.update_one(
            {"id": listing["seller_guild_id"]},
            {"$inc": {"gold": seller_proceeds}, "$set": {"updated_at": now_iso}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("buy: seller credit failed (%s) — reverting", exc)
        await db.guilds.update_one(
            {"id": buyer_guild["id"]},
            {"$inc": {"gold": total_cost}},
        )
        await _revert_listing()
        raise HTTPException(status_code=500, detail="Internal market error — purchase reverted")

    # ─── Step 4: decrement seller inventory (quantity + market_locked_qty) ───
    try:
        await db.inventory_items.update_one(
            {"guild_id": listing["seller_guild_id"], "item_id": listing["item_template_id"]},
            {"$inc": {"quantity": -qty, "market_locked_qty": -qty}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("buy: seller inv dec failed (%s) — reverting", exc)
        await db.guilds.update_one(
            {"id": listing["seller_guild_id"]},
            {"$inc": {"gold": -seller_proceeds}},
        )
        await db.guilds.update_one(
            {"id": buyer_guild["id"]},
            {"$inc": {"gold": total_cost}},
        )
        await _revert_listing()
        raise HTTPException(status_code=500, detail="Internal market error — purchase reverted")

    # ─── Step 5: upsert buyer inventory ───
    try:
        await db.inventory_items.update_one(
            {"guild_id": buyer_guild["id"], "item_id": listing["item_template_id"]},
            {
                "$inc": {"quantity": qty},
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "guild_id": buyer_guild["id"],
                    "item_id": listing["item_template_id"],
                    "acquired_at": now_iso,
                    "source": "market",
                    "bind_state": "unbound",
                },
            },
            upsert=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("buy: buyer inv credit failed (%s) — reverting", exc)
        await db.inventory_items.update_one(
            {"guild_id": listing["seller_guild_id"], "item_id": listing["item_template_id"]},
            {"$inc": {"quantity": qty, "market_locked_qty": qty}},
        )
        await db.guilds.update_one(
            {"id": listing["seller_guild_id"]},
            {"$inc": {"gold": -seller_proceeds}},
        )
        await db.guilds.update_one(
            {"id": buyer_guild["id"]},
            {"$inc": {"gold": total_cost}},
        )
        await _revert_listing()
        raise HTTPException(status_code=500, detail="Internal market error — purchase reverted")

    # ─── Step 6: audit log ───
    try:
        await write_audit(
            db, event_type="market_purchase_completed",
            actor_user_id=buyer_user["id"], actor_guild_id=buyer_guild["id"],
            item_slug=listing["item_slug"], item_template_id=listing["item_template_id"],
            quantity=qty,
            source="market", related_entity_id=listing_id,
            metadata={
                "seller_guild_id": listing["seller_guild_id"],
                "price_per_unit": price,
                "fee": fee,
            },
        )
        await write_audit(
            db, event_type="gold_debited",
            actor_user_id=buyer_user["id"], actor_guild_id=buyer_guild["id"],
            gold_delta=-total_cost,
            source="market", related_entity_id=listing_id,
        )
        await write_audit(
            db, event_type="gold_credited",
            actor_guild_id=listing["seller_guild_id"],
            gold_delta=seller_proceeds,
            source="market", related_entity_id=listing_id,
        )
        await write_audit(
            db, event_type="loot_awarded",
            actor_user_id=buyer_user["id"], actor_guild_id=buyer_guild["id"],
            item_slug=listing["item_slug"], item_template_id=listing["item_template_id"],
            quantity=qty,
            source="market", related_entity_id=listing_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit write failed in buy_listing: %s", exc)

    # Phase 14.1 — weekly quest progress (best-effort, non-critical).
    # Track market_purchases for the BUYER only (1 quest tick per purchase
    # event, not per unit, to avoid grindy bot patterns).
    try:
        from app.quests.services import increment_weekly_progress
        await increment_weekly_progress(
            db, buyer_guild["id"], "market_purchases", 1
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("weekly quest hook failed in buy_listing: %s", exc)
    # ROUND 6D — contract progress on the SELLER (market_sales_count)
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(
            db, listing["seller_guild_id"], "market_sales_count", 1,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("contract hook failed in buy_listing: %s", exc)

    # Fetch buyer's remaining gold for the response
    buyer_after = await db.guilds.find_one(
        {"id": buyer_guild["id"]}, {"_id": 0, "gold": 1}
    )
    return {
        "success": True,
        "listing_id": listing_id,
        "item_received": {
            "slug": listing["item_slug"],
            "name": (listing.get("item_display_name_en") if lang == "en"
                     else listing.get("item_display_name_it")) or listing["item_slug"],
            "rarity": listing.get("item_rarity"),
            "quantity": qty,
        },
        "gold_spent": total_cost,
        "remaining_gold": int(buyer_after.get("gold", 0)) if buyer_after else 0,
        "listing_status": LISTING_STATUS_SOLD if flips_to_sold else LISTING_STATUS_ACTIVE,
    }


# Item public projection (used by sellable-items helper in the frontend)
__all__ = [
    "MARKET_FEE_PCT",
    "ensure_market_indexes",
    "list_active_listings",
    "list_my_listings",
    "create_listing",
    "cancel_listing",
    "buy_listing",
    "listing_public",
    "item_public",  # re-export for completeness
]
