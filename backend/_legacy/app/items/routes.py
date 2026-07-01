"""Items routes (Phase 5.5c.2)."""
from fastapi import APIRouter

from app.core.database import db
from app.items.services import list_active_items


router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("")
async def list_items():
    return {"items": await list_active_items(db)}


__all__ = ["router"]
