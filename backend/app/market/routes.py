"""Marketplace routes (Phase 14.8 — ROUND 3.C).

5 routes across 4 path-strings (+4 to OpenAPI paths count).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.market.services import (
    buy_listing,
    cancel_listing,
    create_listing,
    list_active_listings,
    list_my_listings,
)


router = APIRouter(prefix="/api/market", tags=["market"])


class CreateListingBody(BaseModel):
    item_slug: str = Field(..., min_length=1, max_length=120)
    quantity: int = Field(..., gt=0)
    price_per_unit: int = Field(..., gt=0)


class BuyListingBody(BaseModel):
    quantity: Optional[int] = Field(default=None, gt=0)


@router.get("/listings")
async def get_listings(
    item_type: Optional[str] = None,
    rarity: Optional[str] = None,
    level_max: Optional[int] = Query(default=None, ge=1, le=100),
    price_max: Optional[int] = Query(default=None, ge=0, le=10_000_000),
    name_contains: Optional[str] = Query(default=None, max_length=80),
    sort_by: str = Query(default="created_at"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=1000),
    lang: str = Query(default="it", pattern=r"^(it|en)$"),
):
    return await list_active_listings(
        db,
        item_type=item_type,
        rarity=rarity,
        level_max=level_max,
        price_max=price_max,
        name_contains=name_contains,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        lang=lang,
    )


@router.get("/listings/mine")
async def get_my_listings(
    lang: str = Query(default="it", pattern=r"^(it|en)$"),
    current_user: dict = Depends(get_current_user),
):
    return await list_my_listings(db, current_user["id"], lang=lang)


@router.post("/listings", status_code=201)
async def post_create_listing(
    body: CreateListingBody,
    lang: str = Query(default="it", pattern=r"^(it|en)$"),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await create_listing(
        db, current_user, guild,
        item_slug=body.item_slug,
        quantity=body.quantity,
        price_per_unit=body.price_per_unit,
        lang=lang,
    )


@router.delete("/listings/{listing_id}")
async def delete_listing(
    listing_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await cancel_listing(db, current_user, guild, listing_id)


@router.post("/listings/{listing_id}/buy")
async def post_buy_listing(
    listing_id: str,
    body: Optional[BuyListingBody] = None,
    lang: str = Query(default="it", pattern=r"^(it|en)$"),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    qty = body.quantity if body else None
    return await buy_listing(db, current_user, guild, listing_id, quantity=qty, lang=lang)


__all__ = ["router"]
