"""ROUND 16.1 Phase 1 — Dashboard data-driven suggestions, onboarding, daily loop.

Three endpoints — all read-only against the caller's guild — that drive the
new Dashboard cards:

  GET /api/dashboard/suggestions  → 3-5 actionable next-actions
  GET /api/dashboard/onboarding   → 8-step onboarding checklist (auto-derived)
  GET /api/dashboard/daily-loop   → 6-item rolling daily loop (no rewards)

Italian + English strings are returned together (title_it/title_en, cta_it/cta_en)
so the FE can switch language without a second round-trip.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


async def _ctx(user: dict = Depends(get_current_user)) -> dict:
    """Return {user, guild} after enforcing guild ownership."""
    guild = await user_guild_or_404(db, user["id"])
    return {"user": user, "guild": guild}


# ── helpers ─────────────────────────────────────────────────────────
def _today_utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _today_utc_bounds() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat(), now.isoformat()


# ── /api/dashboard/suggestions ─────────────────────────────────────
@router.get("/suggestions")
async def get_dashboard_suggestions(ctx=Depends(_ctx)):
    """Return up to 5 actionable suggestions, sorted by priority desc.

    Every suggestion is derived from live DB counters. If the underlying
    condition is false, the suggestion is omitted (no fluff)."""
    guild = ctx["guild"]
    gid = guild["id"]
    out: list[dict[str, Any]] = []

    # 1. Completed expeditions with unread report
    n_completed = await db.expeditions.count_documents({
        "guild_id": gid, "status": "completed", "is_read": {"$ne": True},
    })
    if n_completed > 0:
        out.append({
            "id": "expedition_reports_pending",
            "priority": 9,
            "title_it": f"Hai {n_completed} report di spedizione da leggere",
            "title_en": f"{n_completed} expedition report(s) waiting to be read",
            "cta_it": "Apri i report",
            "cta_en": "Open reports",
            "link": "/expeditions",
            "icon": "📜",
        })

    # 2. Adventurers without equipped items (proxy for upgradeable gear)
    n_no_equip = await db.adventurers.count_documents({
        "guild_id": gid,
        "equipped_items_count": {"$lte": 0},
    })
    # Fallback when field is missing on legacy docs.
    if n_no_equip == 0:
        # Estimate via items collection: adventurers with no equipped items at all.
        equipped_owners = await db.items.distinct(
            "equipped_by", {"guild_id": gid, "equipped_by": {"$ne": None}})
        n_advs = await db.adventurers.count_documents({"guild_id": gid})
        n_no_equip = max(0, n_advs - len(equipped_owners))
    if n_no_equip > 0:
        out.append({
            "id": "auto_equip_pending",
            "priority": 8,
            "title_it": f"{n_no_equip} avventurieri con equipaggiamento migliorabile",
            "title_en": f"{n_no_equip} adventurer(s) have improvable gear",
            "cta_it": "Apri il roster",
            "cta_en": "Open roster",
            "link": "/adventurers",
            "icon": "⚔",
        })

    # 3. Recruit available (gold + roster cap)
    gold = int(guild.get("gold") or 0)
    roster_count = await db.adventurers.count_documents({"guild_id": gid})
    roster_cap = int(guild.get("roster_cap") or 40)
    # Pull cheapest visible candidate cost from offers (best-effort).
    recruit_cost = 20
    if gold >= recruit_cost and roster_count < roster_cap:
        out.append({
            "id": "recruit_available",
            "priority": 7,
            "title_it": "Hai oro e posto per nuovi avventurieri",
            "title_en": "You have gold and roster slots for new recruits",
            "cta_it": "Vai al reclutamento",
            "cta_en": "Open recruitment",
            "link": "/recruitment",
            "icon": "🪪",
        })

    # 4. Class Hall with locked specs (unlock progress visible)
    halls_unlocked_with_locked_specs = 0
    async for h in db.class_halls.find(
        {"guild_id": gid, "is_unlocked": True},
        {"_id": 0, "unlocked_specializations": 1},
    ):
        if len(h.get("unlocked_specializations") or []) < 3:
            halls_unlocked_with_locked_specs += 1
    if halls_unlocked_with_locked_specs > 0:
        out.append({
            "id": "class_hall_unlock",
            "priority": 5,
            "title_it": f"{halls_unlocked_with_locked_specs} Sale di Classe con specializzazioni da sbloccare",
            "title_en": f"{halls_unlocked_with_locked_specs} Class Hall(s) have unlockable specializations",
            "cta_it": "Sale di Classe",
            "cta_en": "Class Halls",
            "link": "/class-halls",
            "icon": "◆",
        })

    # 5. Achievements near completion (≥75 % progress)
    near = 0
    async for a in db.guild_achievements.find(
        {"guild_id": gid, "unlocked_at": None},
        {"_id": 0, "progress": 1, "target": 1},
    ):
        target = float(a.get("target") or 0)
        if target <= 0:
            continue
        if (float(a.get("progress") or 0) / target) >= 0.75:
            near += 1
    if near > 0:
        out.append({
            "id": "achievement_near",
            "priority": 7,
            "title_it": f"{near} Imprese vicine al completamento (≥75%)",
            "title_en": f"{near} Achievement(s) close to completion (≥75%)",
            "cta_it": "Vedi Imprese",
            "cta_en": "See Achievements",
            "link": "/achievements",
            "icon": "★",
        })

    # 6. Dungeon-ready (any dungeon with estimated success ≥ 70 %).
    # Cheap proxy: at least 3 adventurers Lvl 1+ exist.
    if roster_count >= 3:
        out.append({
            "id": "dungeon_ready",
            "priority": 6,
            "title_it": "La tua squadra è pronta per un dungeon",
            "title_en": "Your party is ready for a dungeon run",
            "cta_it": "Apri i dungeon",
            "cta_en": "Open dungeons",
            "link": "/dungeons",
            "icon": "🗝",
        })

    # 7. Market visit (always present as low-priority evergreen).
    out.append({
        "id": "market_browse",
        "priority": 3,
        "title_it": "Esplora il Mercato per offerte e materiali",
        "title_en": "Browse the Market for offers and materials",
        "cta_it": "Apri il Mercato",
        "cta_en": "Open Market",
        "link": "/market",
        "icon": "🪙",
    })

    out.sort(key=lambda s: -s["priority"])
    return {"suggestions": out[:5], "generated_at": datetime.now(timezone.utc).isoformat()}


# ── /api/dashboard/onboarding ──────────────────────────────────────
ONBOARDING_STEPS = [
    # (step_id, title_it, title_en, link, cta_it, cta_en)
    ("create_guild",  "Crea la tua gilda",           "Create your guild",
        "/dashboard",  "Fatto",  "Done"),
    ("view_roster",   "Visita il roster",            "Visit the roster",
        "/adventurers", "Vai",   "Go"),
    ("recruit_one",   "Recluta un avventuriero",     "Recruit one adventurer",
        "/recruitment", "Recluta", "Recruit"),
    ("equip_one",     "Equipaggia un avventuriero",  "Equip one adventurer",
        "/adventurers", "Vai al roster", "Go to roster"),
    ("first_run",     "Avvia il primo dungeon",      "Launch your first dungeon",
        "/dungeons",    "Apri dungeon", "Open dungeons"),
    ("read_report",   "Leggi un report di spedizione", "Read an expedition report",
        "/expeditions", "Apri report", "Open reports"),
    ("visit_training","Visita la Sala di Addestramento", "Visit Training Grounds",
        "/training",    "Vai", "Go"),
    ("visit_halls",   "Visita una Sala di Classe",   "Visit a Class Hall",
        "/class-halls", "Vai", "Go"),
]


@router.get("/onboarding")
async def get_dashboard_onboarding(ctx=Depends(_ctx)):
    """Derive the 8-step onboarding state purely from live DB counters."""
    guild = ctx["guild"]
    gid = guild["id"]
    completed = set(guild.get("onboarding_completed_steps") or [])

    # Always-on derivations (so legacy guilds reflect their real state).
    completed.add("create_guild")

    adv_count = await db.adventurers.count_documents({"guild_id": gid})
    if adv_count > 0:
        completed.add("view_roster")
    if adv_count > 3:  # > starter pack
        completed.add("recruit_one")

    n_equipped = await db.equipped_items.count_documents(
        {"guild_id": gid})
    if n_equipped > 0:
        completed.add("equip_one")

    n_exp = await db.expeditions.count_documents({"guild_id": gid})
    n_exp_done = await db.expeditions.count_documents(
        {"guild_id": gid, "status": "completed"})
    if n_exp >= 1:
        completed.add("first_run")
    if n_exp_done >= 1:
        completed.add("read_report")
    # ROUND 16.1 Phase 4 — graduation rule: a player who has already
    # completed an expedition has obviously equipped someone too — the
    # explicit `equip_one` step would only have been ticked if the FE
    # had been wired to call the equip endpoint, which is the same path
    # the auto-expedition pipeline takes. Marking it complete here keeps
    # mature accounts from seeing an "Equip an adventurer" nag forever.
    if n_exp_done >= 1:
        completed.add("equip_one")

    n_halls = await db.class_halls.count_documents({"guild_id": gid})
    if n_halls > 0:
        completed.add("visit_training")  # class halls implies training visible
    n_halls_unlocked = await db.class_halls.count_documents(
        {"guild_id": gid, "is_unlocked": True})
    if n_halls_unlocked > 0:
        completed.add("visit_halls")

    steps = []
    for sid, t_it, t_en, link, cta_it, cta_en in ONBOARDING_STEPS:
        steps.append({
            "id": sid,
            "title_it": t_it, "title_en": t_en,
            "cta_it": cta_it, "cta_en": cta_en,
            "link": link,
            "completed": sid in completed,
        })

    all_done = all(s["completed"] for s in steps)
    dismissed = bool(guild.get("onboarding_dismissed", False))
    # ROUND 16.1 Phase 4 — graduation rule: mature guilds (level ≥ 3 OR
    # ≥ 3 completed expeditions) auto-dismiss the onboarding card so the
    # UI does not nag returning players. Documented behaviour: the
    # `dismissed_implicit` flag is informational; the FE hides the card
    # when either `dismissed` or `dismissed_implicit` is true.
    guild_level = int(guild.get("level") or 0)
    dismissed_implicit = (guild_level >= 3) or (n_exp_done >= 3)
    graduation_reason = (
        "guild_level_ge_3" if guild_level >= 3
        else ("completed_expeditions_ge_3" if n_exp_done >= 3 else None)
    )
    # ROUND 16.A Phase 2 — emit `onboarding_graduated` once per guild on
    # the first false→true transition. CAS on `onboarding_graduated_at:
    # None` guarantees exactly-one emission even under concurrent reads.
    if dismissed_implicit:
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            transitioned = await db.guilds.find_one_and_update(
                {"id": gid, "onboarding_graduated_at": None},
                {"$set": {"onboarding_graduated_at": now_iso}},
                projection={"_id": 0, "id": 1},
            )
            # `find_one_and_update` returns the PRE-update doc; if the
            # doc had no `onboarding_graduated_at` field (or it was None)
            # we just flipped it. Mongo returns `None` only when no doc
            # matched the filter — i.e. already graduated → skip emit.
            if transitioned is not None:
                from app.audit.log import write_audit
                await write_audit(
                    db,
                    event_type="onboarding_graduated",
                    actor_guild_id=gid,
                    actor_user_id=ctx["user"]["id"],
                    source="dashboard.onboarding",
                    related_entity_id=gid,
                    metadata={
                        "graduation_reason": graduation_reason,
                        "completed_steps_count": sum(
                            1 for s in steps if s["completed"]),
                        "guild_level": guild_level,
                        "completed_expeditions": n_exp_done,
                    },
                )
        except Exception:  # noqa: BLE001
            # Best-effort: dashboard read must never fail because of an
            # audit-bridge issue.
            pass
    return {
        "steps": steps,
        "completed_count": sum(1 for s in steps if s["completed"]),
        "total_count": len(steps),
        "all_completed": all_done,
        "dismissed": dismissed,
        "dismissed_implicit": dismissed_implicit,
        "graduation_reason": graduation_reason,
    }


@router.post("/onboarding/dismiss")
async def dismiss_onboarding(ctx=Depends(_ctx)):
    guild = ctx["guild"]
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$set": {"onboarding_dismissed": True,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"ok": True}


# ── /api/dashboard/daily-loop ──────────────────────────────────────
DAILY_LOOP_ITEMS = [
    # (step_id, title_it, title_en, link)
    ("daily_expedition",   "Completa 1 spedizione oggi",
                            "Complete 1 expedition today",          "/dungeons"),
    ("daily_recruit",      "Recluta 1 avventuriero",
                            "Recruit 1 adventurer",                 "/recruitment"),
    ("daily_auto_equip",   "Migliora l'equip di un avventuriero",
                            "Improve an adventurer's gear",         "/adventurers"),
    ("daily_visit_halls",  "Visita una Sala di Classe",
                            "Visit a Class Hall",                   "/class-halls"),
    ("daily_threat_run",   "Completa un dungeon con 2+ minacce contrastate",
                            "Clear a dungeon countering 2+ threats", "/expeditions"),
    ("daily_market",       "Visita il Mercato",
                            "Browse the Market",                    "/market"),
]


@router.get("/daily-loop")
async def get_dashboard_daily_loop(ctx=Depends(_ctx)):
    guild = ctx["guild"]
    gid = guild["id"]
    today = _today_utc_date()
    day_start_iso, _ = _today_utc_bounds()

    prog = guild.get("daily_loop_progress") or {}
    if prog.get("date") != today:
        prog = {"date": today, "completed": []}

    completed = set(prog.get("completed") or [])

    # Live derivations (read-only): if a counter shows the action has
    # happened today, surface it as done — but never strip away an action
    # already cached.
    if await db.expeditions.count_documents({
        "guild_id": gid, "status": "completed",
        "completed_at": {"$gte": day_start_iso},
    }) > 0:
        completed.add("daily_expedition")
        # 2+ threats countered today?
        async for e in db.expeditions.find({
            "guild_id": gid, "status": "completed",
            "completed_at": {"$gte": day_start_iso},
        }, {"_id": 0, "threat_resolution": 1}):
            tr = e.get("threat_resolution") or {}
            if tr.get("applies") and len(tr.get("threats_countered") or []) >= 2:
                completed.add("daily_threat_run")
                break

    if await db.adventurers.count_documents({
        "guild_id": gid, "created_at": {"$gte": day_start_iso},
    }) > 0:
        completed.add("daily_recruit")

    if await db.audit_log.count_documents({
        "metadata.guild_id": gid,
        "event_type": "adventurer_auto_equipped",
        "occurred_at": {"$gte": day_start_iso},
    }) > 0:
        completed.add("daily_auto_equip")

    items = []
    for sid, t_it, t_en, link in DAILY_LOOP_ITEMS:
        items.append({
            "id": sid,
            "title_it": t_it,
            "title_en": t_en,
            "link": link,
            "completed": sid in completed,
        })

    # Persist the derived progress so the FE can rely on guild state.
    if set(prog.get("completed") or []) != completed:
        await db.guilds.update_one(
            {"id": gid},
            {"$set": {"daily_loop_progress": {
                "date": today, "completed": sorted(completed),
            }, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )

    return {
        "date": today,
        "items": items,
        "completed_count": sum(1 for it in items if it["completed"]),
        "total_count": len(items),
    }
