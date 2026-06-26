"""Phase 16 — Consortiums routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user
from app.consortiums.services import (
    create_consortium,
    list_consortiums,
    get_consortium_detail,
    join_consortium,
    leave_consortium,
    my_consortium,
    consortium_activity,
)


router = APIRouter(prefix="/api/consortiums", tags=["consortiums"])


class CreateConsortiumPayload(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    tag: str | None = Field(default=None, max_length=6)
    description: str | None = Field(default=None, max_length=300)


@router.get("")
async def list_route(limit: int = Query(50, ge=1, le=100)):
    rows = await list_consortiums(db, limit=limit)
    return {"consortiums": rows, "count": len(rows)}


@router.post("", status_code=201)
async def create_route(
    payload: CreateConsortiumPayload,
    current_user: dict = Depends(get_current_user),
):
    out = await create_consortium(
        db,
        current_user=current_user,
        name=payload.name,
        tag=payload.tag,
        description=payload.description,
    )
    return out


@router.get("/me")
async def my_route(current_user: dict = Depends(get_current_user)):
    out = await my_consortium(db, current_user=current_user)
    return {"consortium": out}


@router.post("/leave")
async def leave_route(current_user: dict = Depends(get_current_user)):
    return await leave_consortium(db, current_user=current_user)


@router.get("/{consortium_id}")
async def detail_route(consortium_id: str):
    return await get_consortium_detail(db, consortium_id)


@router.post("/{consortium_id}/join")
async def join_route(
    consortium_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await join_consortium(db, current_user=current_user, cid=consortium_id)


@router.get("/{consortium_id}/activity")
async def activity_route(
    consortium_id: str,
    limit: int = Query(20, ge=1, le=50),
    lang: str = Query("it"),
):
    return await consortium_activity(db, consortium_id, limit=limit, lang=lang)


__all__ = ["router"]
