"""Items routes (Phase 5.5c.2)."""
from fastapi import APIRouter

from app.core.database import db
from app.items.services import get_catalog_contract_status, list_active_items


router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("")
async def list_items():
    return {"items": await list_active_items(db)}


@router.get("/catalog-contract")
async def catalog_contract():
    """Public, read-only progress toward the canonical 1500-item catalog."""
    return await get_catalog_contract_status(db)


__all__ = ["router"]
