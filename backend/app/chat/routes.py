"""Phase 19.3 — Chat routes. All endpoints require JWT bearer."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.chat.services import (
    fetch_consortium,
    fetch_global,
    send_message,
    MESSAGE_MAX_LEN,
)
from app.core.database import db
from app.core.security import get_current_user
from app.territory.guards import require_unlocked


router = APIRouter(prefix="/api/chat", tags=["chat"])


class SendMessageIn(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=MESSAGE_MAX_LEN)


# ─── Global ───────────────────────────────────────────────────────────────
@router.get("/global")
async def get_global(
    after: Optional[str] = Query(None, description="ISO timestamp; only messages after this"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    msgs = await fetch_global(db, current_user=current_user, after_iso=after, limit=limit)
    return {"channel_type": "global", "messages": msgs, "count": len(msgs)}


@router.post("/global", status_code=201, dependencies=[Depends(require_unlocked("chat.global"))])
async def post_global(
    payload: SendMessageIn,
    current_user: dict = Depends(get_current_user),
):
    msg = await send_message(
        db,
        current_user=current_user,
        channel_type="global",
        consortium_id=None,
        raw_text=payload.message_text,
    )
    return {"message": msg}


# ─── Consortium ───────────────────────────────────────────────────────────
@router.get("/consortium/{consortium_id}")
async def get_consortium(
    consortium_id: str,
    after: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    msgs = await fetch_consortium(
        db,
        current_user=current_user,
        consortium_id=consortium_id,
        after_iso=after,
        limit=limit,
    )
    return {
        "channel_type": "consortium",
        "consortium_id": consortium_id,
        "messages": msgs,
        "count": len(msgs),
    }


@router.post("/consortium/{consortium_id}", status_code=201, dependencies=[Depends(require_unlocked("chat.consortium"))])
async def post_consortium(
    consortium_id: str,
    payload: SendMessageIn,
    current_user: dict = Depends(get_current_user),
):
    msg = await send_message(
        db,
        current_user=current_user,
        channel_type="consortium",
        consortium_id=consortium_id,
        raw_text=payload.message_text,
    )
    return {"message": msg}


__all__ = ["router"]
