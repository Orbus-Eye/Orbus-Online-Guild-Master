"""Expedition HTTP routes (Phase 5.5e + ROUND 6B.3 Wave 1.5 over-cap guard).

Route order matters: `/last-completed` and `/replay-last` are registered
BEFORE the `/{expedition_id}` catch-all so FastAPI doesn't capture the
literal segments as a UUID parameter.
"""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.expeditions.preview import preview_expedition
from app.expeditions.preview_schema import ExpeditionPreviewIn
from app.expeditions.schemas import ExpeditionCreateIn
from app.expeditions.services import (
    get_expedition as svc_get_expedition,
    get_last_completed,
    list_expeditions,
    replay_last,
    start_expedition,
)
from app.guilds.services import user_guild_or_404
from app.territory.cap_guard import over_cap_dep


router = APIRouter(prefix="/api/expeditions", tags=["expeditions"])


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(over_cap_dep("expedition.create"))],
)
async def start_expedition_route(
    payload: ExpeditionCreateIn,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    result = await start_expedition(db, guild, payload)
    # ROUND 17.1 P0.3 — funnel event FIRST_EXPEDITION_STARTED.
    is_first_start = False
    try:
        from app.audit.first_events import emit_first_event
        is_first_start = await emit_first_event(
            db, event_type="FIRST_EXPEDITION_STARTED",
            guild_id=guild["id"], user_id=current_user["id"],
            extra={"dungeon_id": payload.dungeon_id if hasattr(payload, "dungeon_id") else None},
        )
    except Exception:  # noqa: BLE001
        pass
    # ROUND 17.1b P1.1 — surface milestone flag for client-side toast.
    if isinstance(result, dict):
        result.setdefault("milestones", {})
        result["milestones"]["is_first_expedition_started"] = bool(is_first_start)
    return result


@router.post("/preview")
async def preview_expedition_route(
    payload: ExpeditionPreviewIn,
    current_user: dict = Depends(get_current_user),
):
    """Phase 14.3-c — read-only preview: success chance, injury risk,
    expected reward, modifiers list. NEVER writes to DB.
    Wave 1.5 — intentionally NOT gated by over-cap; the FE shows a warning
    banner using the cap_state from the dashboard widget."""
    guild = await user_guild_or_404(db, current_user["id"])
    # ROUND 17.1 P0.3 — funnel event FIRST_EXPEDITION_PREVIEWED.
    try:
        from app.audit.first_events import emit_first_event
        await emit_first_event(
            db, event_type="FIRST_EXPEDITION_PREVIEWED",
            guild_id=guild["id"], user_id=current_user["id"],
        )
    except Exception:  # noqa: BLE001
        pass
    return await preview_expedition(
        db, guild, payload.dungeon_id, payload.adventurer_ids
    )


@router.get("/last-completed")
async def get_last_completed_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_last_completed(db, guild)


@router.post(
    "/replay-last",
    status_code=201,
    dependencies=[Depends(over_cap_dep("expedition.replay"))],
)
async def replay_last_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await replay_last(db, guild)


@router.get("")
async def list_expeditions_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    # ROUND 17.1 P0.3 — funnel event FIRST_DUNGEON_VIEWED.
    try:
        from app.audit.first_events import emit_first_event
        await emit_first_event(
            db, event_type="FIRST_DUNGEON_VIEWED",
            guild_id=guild["id"], user_id=current_user["id"],
        )
    except Exception:  # noqa: BLE001
        pass
    return await list_expeditions(db, guild)


@router.get("/{expedition_id}")
async def get_expedition_route(
    expedition_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    result = await svc_get_expedition(db, expedition_id, guild)
    # ROUND 17.1 P0.3 — funnel event FIRST_REPORT_OPENED (best-effort;
    # emesso solo se la spedizione è completed, per evitare che una
    # navigation su in-progress conti come "report opened").
    try:
        # result payload wraps as { expedition, members, loot_items, ... }
        exp_doc = (result or {}).get("expedition") if isinstance(result, dict) else None
        exp_status = (exp_doc or {}).get("status") if exp_doc else None
        if exp_status in ("completed", "success", "failed", "Success", "Failed"):
            from app.audit.first_events import emit_first_event
            await emit_first_event(
                db, event_type="FIRST_REPORT_OPENED",
                guild_id=guild["id"], user_id=current_user["id"],
                extra={"expedition_id": expedition_id},
            )
    except Exception:  # noqa: BLE001
        pass
    return result


__all__ = ["router"]
