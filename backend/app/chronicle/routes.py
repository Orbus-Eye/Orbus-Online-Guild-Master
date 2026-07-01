"""Phase 16 — Server Chronicle routes (public, no auth required)."""
from fastapi import APIRouter, Query

from app.core.database import db
from app.chronicle.services import list_chronicle


router = APIRouter(prefix="/api/chronicle", tags=["chronicle"])


@router.get("")
async def chronicle_list(
    limit: int = Query(20, ge=1, le=50),
    lang: str = Query("it"),
):
    return await list_chronicle(db, limit=limit, lang=lang)


__all__ = ["router"]
