"""ROUND 16.3 Phase 8 V1 — Admin routes for stables (dev-gated)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.security import get_admin_user
from app.stables.models import AdminGrantMountPayload
from app.stables.services import admin_grant_mount


router = APIRouter(prefix="/api/admin/stables", tags=["admin", "stables"])


def _dev_gate() -> None:
    if (os.environ.get("APP_ENV") or "development").lower() == "production":
        raise HTTPException(
            status_code=403,
            detail={"code": "stables.dev_disabled_in_prod",
                    "user_message":
                    "L'admin grant dev è disabilitato in produzione."},
        )


@router.get("/catalog")
async def admin_catalog(admin: dict = Depends(get_admin_user)):
    mounts = await db.mount_catalog.find({}, {"_id": 0}).to_list(200)
    total_owners = {}
    for m in mounts:
        cnt = await db.guild_mount_ownership.count_documents(
            {"mount_slug": m["slug"]},
        )
        total_owners[m["slug"]] = cnt
    routes = await db.narrative_routes.find({}, {"_id": 0}).to_list(50)
    completions_total = await db.narrative_route_completions.count_documents({})
    return {
        "mounts": mounts,
        "owners_count_by_slug": total_owners,
        "narrative_routes": routes,
        "completions_total": completions_total,
    }


@router.post("/dev/grant-mount")
async def dev_grant_mount(payload: AdminGrantMountPayload,
                          admin: dict = Depends(get_admin_user)):
    _dev_gate()
    return await admin_grant_mount(db, payload.guild_id, payload.mount_slug)
