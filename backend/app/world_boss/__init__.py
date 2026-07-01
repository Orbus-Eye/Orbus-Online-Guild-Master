"""ROUND 16.3 Phase 1 — World Boss V1 Alveora.

Compact single-file module for the World Boss subsystem:
- Idempotent seed (catalog + counter_mind_control counter)
- Models, services, resolution, recovery, routes.
- On-visit fallback + CAS-protected resolution (lesson learned R16.1.1).
- 3-phase narrative, threat/counter reuse via local THREAT_COUNTER_MAP.

Public: `router`, `seed_world_boss_catalog`, `try_resolve_expired_events_for_guild`,
`resolve_stuck_world_boss_event`.
"""
from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.world_boss")

router = APIRouter(prefix="/api/world-boss", tags=["world-boss"])
admin_router = APIRouter(prefix="/api/admin/world-boss", tags=["admin", "world-boss"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── Threat → Counter map (local; append-only respect to R16.0 seeds) ─
THREAT_COUNTER_MAP: dict[str, list[str]] = {
    "void": ["counter_void"],
    "curse": ["counter_curse", "counter_undead"],
    "mind_control": ["counter_mind_control"],
    "boss": ["counter_boss"],
    "magic_barrier": ["counter_magic_barrier", "counter_spell", "counter_void"],
    "puppet_minions": ["counter_minion"],
    "moon_phase": [],  # phase mechanic, no direct counter in V1
}

ALVEORA_SLUG = "alveora_moon_puppeteer"


# ── SEED ──────────────────────────────────────────────────────────────
async def seed_world_boss_catalog() -> dict:
    """Idempotent seed: catalog Alveora + `counter_mind_control` counter."""
    # 1) counter_mind_control (append-only to R16.0 counter catalog)
    await db.counter_tags.update_one(
        {"slug": "counter_mind_control"},
        {"$setOnInsert": {
            "slug": "counter_mind_control",
            "name_it": "Anti-Controllo Mentale",
            "name_en": "Anti-Mind-Control",
            "threats_countered": ["mind_control"],
            "created_at": _utc_now().isoformat(),
        }},
        upsert=True,
    )
    # 2) Alveora catalog
    alveora = {
        "slug": ALVEORA_SLUG,
        "name_it": "Alveora, la Burattinaia della Luna",
        "name_en": "Alveora, the Moon Puppeteer",
        "description_it": (
            "Alveora è una minaccia lunare legata al Vuoto e a Ergolat. "
            "Usa fili mentali, burattini, maschere, carillon e Obelischi "
            "del Vuoto per piegare le menti degli avventurieri e "
            "trasformarli in marionette danzanti sotto la Luna Morta."
        ),
        "description_en": (
            "Alveora is a lunar threat bound to the Void and Ergolat. "
            "She uses mental strings, puppets, masks, music boxes and "
            "Void Obelisks to bend the minds of adventurers into "
            "dancing marionettes under the Dead Moon."
        ),
        "theme_tags": ["luna_morta", "fili_del_vuoto", "burattini",
                       "obelischi", "sinfonia_dei_fili", "controllo_mentale"],
        "phases": [
            {"n": 1, "name_it": "I Fili si Tendono",
             "name_en": "The Threads Tighten",
             "threats": ["void", "curse", "boss"],
             "hp_threshold": 1.0},
            {"n": 2, "name_it": "La Sinfonia dei Fili",
             "name_en": "The Symphony of Threads",
             "threats": ["void", "curse", "mind_control",
                         "puppet_minions", "magic_barrier"],
             "hp_threshold": 0.66},
            {"n": 3, "name_it": "Il Sorriso della Luna Morta",
             "name_en": "The Smile of the Dead Moon",
             "threats": ["void", "curse", "mind_control", "puppet_minions",
                         "magic_barrier", "boss", "moon_phase"],
             "hp_threshold": 0.33},
        ],
        "total_hp_default": 1_000_000,
        "duration_hours_default": 72,
        "reward_currencies": ["filo_lunare_spezzato",
                              "frammento_obelisco_vuoto",
                              "eco_della_luna_morta"],
        "reward_gold_pool_default": 50_000,
        "is_active": True,
    }
    await db.world_boss_catalog.update_one(
        {"slug": ALVEORA_SLUG},
        {"$setOnInsert": {**alveora,
                          "created_at": _utc_now().isoformat()}},
        upsert=True,
    )
    # 3) Event currencies as items
    now_iso = _utc_now().isoformat()
    for slug, name_it, name_en in [
        ("filo_lunare_spezzato", "Filo Lunare Spezzato", "Broken Moon Thread"),
        ("frammento_obelisco_vuoto", "Frammento di Obelisco del Vuoto",
         "Void Obelisk Fragment"),
        ("eco_della_luna_morta", "Eco della Luna Morta", "Echo of the Dead Moon"),
    ]:
        await db.items.update_one(
            {"slug": slug},
            {"$setOnInsert": {
                "id": str(uuid.uuid4()),
                "slug": slug,
                "name": name_it, "name_it": name_it, "name_en": name_en,
                "item_type": "material_event",
                "rarity": "epic",
                "is_tradeable": True,
                "is_cosmetic": False,
                "affects_combat": False,
                "affects_economy": False,
                "can_be_sold_for_real_money": False,
                "description_it": f"Currency evento World Boss.",
                "description_en": f"World Boss event currency.",
                "created_at": now_iso,
            }},
            upsert=True,
        )
    return {"status": "ok"}


# ── EVENT LIFECYCLE ────────────────────────────────────────────────────
async def _current_phase_for_hp_ratio(catalog: dict, ratio: float) -> int:
    """ratio = current_hp / total_hp. Returns phase number (1..3)."""
    phases = sorted(catalog.get("phases", []), key=lambda p: -p["hp_threshold"])
    current = 1
    for p in phases:
        if ratio <= p["hp_threshold"]:
            current = max(current, p["n"])
    return current


def _event_public(ev: dict) -> dict:
    """Strip internal fields, ensure JSON-safe."""
    out = {k: v for k, v in ev.items() if not k.startswith("_")}
    out.pop("_id", None)
    return out


async def _emit_audit(event_type: str, actor_guild_id: Optional[str],
                      related_entity_id: str, metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type=event_type, actor_user_id=None,
            actor_guild_id=actor_guild_id, source="world_boss",
            related_entity_id=related_entity_id, metadata=metadata,
        )
    except Exception as exc:
        logger.warning("world_boss.audit_emit_failed event=%s err=%s",
                       event_type, exc)


# ── RESOLUTION + RECOVERY ─────────────────────────────────────────────
async def resolve_stuck_world_boss_event(
    event_id: str, *, dry_run: bool = True,
    reason: str = "on_visit_fallback",
) -> dict:
    """Idempotent resolver. CAS lock on status=active + ends_at passed.

    Returns action: `resolved`, `skipped`, `previewed`.
    """
    ev = await db.world_boss_events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        return {"event_id": event_id, "action": "skipped",
                "reason": "not_found"}
    if ev.get("status") not in ("active", "scheduled"):
        return {"event_id": event_id, "action": "skipped",
                "reason": f"already_{ev.get('status')}"}
    try:
        ends_at = datetime.fromisoformat(ev["ends_at"])
    except Exception:
        return {"event_id": event_id, "action": "skipped",
                "reason": "ends_at_invalid"}
    now = _utc_now()
    if now < ends_at:
        return {"event_id": event_id, "action": "skipped",
                "reason": "still_running"}

    if dry_run:
        return {
            "event_id": event_id,
            "guild_scope": ev.get("continent_scope", "global"),
            "current_hp": ev.get("current_hp"),
            "total_hp": ev.get("total_hp"),
            "action": "previewed",
            "proposed_outcome": ("completed" if ev.get("current_hp", 1) <= 0
                                 else "failed"),
        }

    # CAS claim
    now_iso = now.isoformat()
    claimed = await db.world_boss_events.find_one_and_update(
        {"id": event_id, "status": {"$in": ["active", "scheduled"]}},
        {"$set": {"status": "resolving",
                  "resolution_started_at": now_iso,
                  "updated_at": now_iso}},
        projection={"_id": 0},
    )
    if not claimed:
        return {"event_id": event_id, "action": "skipped",
                "reason": "lost_race_to_claim"}

    outcome = "completed" if claimed.get("current_hp", 1) <= 0 else "failed"

    # Release all adventurers still bound to this event
    released = await db.adventurers.update_many(
        {"current_world_boss_event_id": event_id},
        {"$set": {"is_available": True,
                  "expedition_in_progress": False,
                  "current_world_boss_event_id": None,
                  "updated_at": now_iso}},
    )

    # Grant rewards ONCE (CAS on reward_granted flag)
    if outcome == "completed":
        await _grant_rewards_idempotent(event_id, reason=reason)

    # Finalize event status
    await db.world_boss_events.update_one(
        {"id": event_id},
        {"$set": {"status": outcome,
                  "resolved_at": now_iso,
                  "recovered": True,
                  "recovery_reason": reason,
                  "updated_at": now_iso}},
    )

    await _emit_audit(
        "WORLD_BOSS_EVENT_RESOLVED", actor_guild_id=None,
        related_entity_id=event_id,
        metadata={"outcome": outcome, "recovered": True, "reason": reason,
                  "adv_released": int(released.modified_count or 0)},
    )
    await _emit_audit(
        "WORLD_BOSS_TEAM_RELEASED", actor_guild_id=None,
        related_entity_id=event_id,
        metadata={"adv_released": int(released.modified_count or 0)},
    )

    return {"event_id": event_id, "action": "resolved",
            "outcome": outcome,
            "adv_released": int(released.modified_count or 0),
            "recovered": True, "recovery_reason": reason}


async def _grant_rewards_idempotent(event_id: str, *, reason: str) -> dict:
    """Distribute rewards to participants. Guarded by per-guild CAS flag."""
    now_iso = _utc_now().isoformat()
    catalog = await db.world_boss_catalog.find_one(
        {"slug": (await db.world_boss_events.find_one(
            {"id": event_id}, {"boss_slug": 1}))["boss_slug"]}, {"_id": 0},
    )
    # Ranking = participants sorted by total contribution
    parts = await db.world_boss_participants.find(
        {"event_id": event_id}, {"_id": 0},
    ).to_list(500)
    parts.sort(key=lambda p: -p.get("total_contribution", 0))
    granted = 0
    for rank_idx, part in enumerate(parts):
        # CAS: only grant if not already granted
        cas = await db.world_boss_participants.update_one(
            {"id": part["id"], "reward_granted": {"$ne": True}},
            {"$set": {"reward_granted": True,
                      "reward_granted_at": now_iso,
                      "reward_rank": rank_idx + 1}},
        )
        if cas.modified_count == 0:
            continue  # already granted
        # Build reward payload
        rank = rank_idx + 1
        if rank <= 10 and part.get("total_contribution", 0) > 0:
            rewards = {"filo_lunare_spezzato": 3,
                       "frammento_obelisco_vuoto": 2,
                       "eco_della_luna_morta": 1,
                       "gold": max(500, catalog.get("reward_gold_pool_default", 50000) // max(1, len(parts)) * 2)}
        elif part.get("total_contribution", 0) > 0:
            rewards = {"filo_lunare_spezzato": 1, "gold": 200}
        else:
            rewards = {"eco_della_luna_morta": 1, "gold": 50}
        # Persist reward row (audit-friendly)
        await db.world_boss_rewards.insert_one({
            "id": str(uuid.uuid4()),
            "event_id": event_id,
            "guild_id": part["guild_id"],
            "rank": rank,
            "contribution": part.get("total_contribution", 0),
            "rewards": rewards,
            "granted_at": now_iso,
            "reason": reason,
        })
        # Apply gold to guild
        if rewards.get("gold", 0) > 0:
            await db.guilds.update_one(
                {"id": part["guild_id"]},
                {"$inc": {"gold": int(rewards["gold"])}},
            )
        # Apply currency items to inventory (idempotent-add pattern)
        for slug, qty in rewards.items():
            if slug == "gold":
                continue
            item = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
            if not item:
                continue
            existing = await db.inventory_items.find_one({
                "guild_id": part["guild_id"], "item_id": item["id"],
                "is_bound": {"$ne": True},
            })
            if existing:
                await db.inventory_items.update_one(
                    {"id": existing["id"]}, {"$inc": {"quantity": qty}},
                )
            else:
                await db.inventory_items.insert_one({
                    "id": str(uuid.uuid4()),
                    "instance_id": str(uuid.uuid4()),
                    "guild_id": part["guild_id"],
                    "item_id": item["id"],
                    "quantity": qty,
                    "refinement_level": 0,
                    "enchants": [], "affixes": [], "reroll_count": 0,
                    "is_bound": False,
                    "disenchanted_at": None,
                    "acquired_at": now_iso,
                    "source": "world_boss_reward",
                })
        await _emit_audit(
            "WORLD_BOSS_REWARD_GRANTED", actor_guild_id=part["guild_id"],
            related_entity_id=event_id,
            metadata={"rank": rank, "rewards": rewards},
        )
        granted += 1
    return {"granted": granted}


async def try_resolve_expired_events_for_guild(guild_id: str) -> int:
    """Best-effort on-visit fallback.

    Resolves ANY active+expired event AND any event the guild participates in.
    Union approach avoids missing globally-active events even when the guild
    already has participation history in other events.
    """
    now_iso = _utc_now().isoformat()
    resolved = 0
    try:
        # 1) All globally-expired active events
        global_expired = await db.world_boss_events.find(
            {"status": "active", "ends_at": {"$lte": now_iso}},
            {"_id": 0, "id": 1},
        ).to_list(50)
        ev_ids: set[str] = {e["id"] for e in global_expired}
        # 2) Events the guild participates in (may be already expired)
        parts = await db.world_boss_participants.find(
            {"guild_id": guild_id}, {"_id": 0, "event_id": 1},
        ).to_list(100)
        ev_ids.update(p["event_id"] for p in parts)
        for eid in ev_ids:
            try:
                out = await resolve_stuck_world_boss_event(
                    eid, dry_run=False, reason="on_visit_fallback",
                )
                if out.get("action") == "resolved":
                    resolved += 1
            except Exception as exc:
                logger.warning("world_boss.on_visit_failed ev=%s err=%s",
                               eid, exc)
    except Exception as exc:
        logger.warning("world_boss.on_visit_scan_failed guild=%s err=%s",
                       guild_id, exc)
    return resolved


# ── PYDANTIC BODIES ───────────────────────────────────────────────────
class CreateEventBody(BaseModel):
    boss_slug: str = Field(default=ALVEORA_SLUG)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    total_hp_override: Optional[int] = None


class SendTeamBody(BaseModel):
    adventurer_ids: list[str] = Field(min_length=1, max_length=3)


# ── PUBLIC ROUTES ─────────────────────────────────────────────────────
@router.get("/active")
async def list_active(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    try:
        await try_resolve_expired_events_for_guild(guild["id"])
    except Exception:
        pass
    rows = await db.world_boss_events.find(
        {"status": {"$in": ["scheduled", "active"]}}, {"_id": 0},
    ).sort("starts_at", -1).limit(20).to_list(20)
    return {"events": [_event_public(r) for r in rows]}


@router.get("/events/{event_id}")
async def get_event(event_id: str,
                    current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    try:
        await resolve_stuck_world_boss_event(
            event_id, dry_run=False, reason="on_visit_fallback_detail",
        )
    except Exception:
        pass
    ev = await db.world_boss_events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(404, "event_not_found")
    catalog = await db.world_boss_catalog.find_one(
        {"slug": ev["boss_slug"]}, {"_id": 0},
    )
    part = await db.world_boss_participants.find_one(
        {"event_id": event_id, "guild_id": guild["id"]}, {"_id": 0},
    )
    contribs = await db.world_boss_contributions.find(
        {"event_id": event_id, "guild_id": guild["id"]}, {"_id": 0},
    ).sort("created_at", -1).to_list(50)
    return {
        "event": _event_public(ev),
        "catalog": catalog,
        "guild_participation": part,
        "guild_contributions": contribs,
    }


@router.post("/events/{event_id}/join")
async def join_event(event_id: str,
                     current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    ev = await db.world_boss_events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(404, "event_not_found")
    if ev["status"] not in ("scheduled", "active"):
        raise HTTPException(409, "event_not_joinable")
    now_iso = _utc_now().isoformat()
    # Idempotent join
    existing = await db.world_boss_participants.find_one(
        {"event_id": event_id, "guild_id": guild["id"]}, {"_id": 0},
    )
    if existing:
        return {"participant": _event_public(existing), "already_joined": True}
    part_id = str(uuid.uuid4())
    doc = {
        "id": part_id, "event_id": event_id, "guild_id": guild["id"],
        "joined_at": now_iso, "total_contribution": 0,
        "teams_sent": 0, "reward_granted": False,
    }
    await db.world_boss_participants.insert_one(doc)
    doc.pop("_id", None)  # insert_one mutates doc adding _id ObjectId
    await _emit_audit("WORLD_BOSS_JOINED", actor_guild_id=guild["id"],
                      related_entity_id=event_id,
                      metadata={"guild_id": guild["id"]})
    return {"participant": doc, "already_joined": False}


@router.post("/events/{event_id}/send-team")
async def send_team(event_id: str, body: SendTeamBody,
                    current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    ev = await db.world_boss_events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(404, "event_not_found")
    if ev["status"] != "active":
        raise HTTPException(409, "event_not_active")
    # Verify participation
    part = await db.world_boss_participants.find_one(
        {"event_id": event_id, "guild_id": guild["id"]}, {"_id": 0},
    )
    if not part:
        raise HTTPException(400, "not_joined")
    # Verify adventurers ownership + availability
    advs = await db.adventurers.find(
        {"id": {"$in": body.adventurer_ids}, "guild_id": guild["id"]},
        {"_id": 0},
    ).to_list(3)
    if len(advs) != len(body.adventurer_ids):
        raise HTTPException(400, "adventurers_ownership_or_unavailable")
    for a in advs:
        if not a.get("is_available", True) or a.get("expedition_in_progress"):
            raise HTTPException(409, f"adventurer_busy:{a['id']}")

    # Contribution formula
    base_power = sum(int(a.get("power", 0) or a.get("total_power", 100))
                     for a in advs)
    counter_slugs: set[str] = set()
    for a in advs:
        for cslug in (a.get("counter_tags") or []):
            counter_slugs.add(cslug)
        for cslug in ((a.get("class_data") or {}).get("counter_tags") or []):
            counter_slugs.add(cslug)
    # Match threats vs available counters
    matched = 0
    for threat in ev.get("threats", []):
        available = THREAT_COUNTER_MAP.get(threat, [])
        if any(c in counter_slugs for c in available):
            matched += 1
    counter_bonus = matched * 0.15
    phase_mult = 1.0 + max(0, ev.get("phase", 1) - 1) * 0.2
    # ROUND 16.3 Phase 5B — Arfus combat_damage bonus (0 if none active).
    from app.arfus_forge import bonus_pct as _arfus_bonus
    _dmg_bonus = await _arfus_bonus(guild["id"], "combat_damage")
    contribution = int(base_power * (1 + counter_bonus) * phase_mult
                       * (1.0 + _dmg_bonus / 100.0))

    now_iso = _utc_now().isoformat()
    contrib_id = str(uuid.uuid4())
    # Snapshot members
    members_snap = [{"id": a["id"], "name": a.get("name"),
                     "class_slug": a.get("class_slug"),
                     "power_at_send": int(a.get("power", 0)
                                          or a.get("total_power", 100))}
                    for a in advs]
    await db.world_boss_contributions.insert_one({
        "id": contrib_id, "event_id": event_id, "guild_id": guild["id"],
        "members": members_snap, "base_power": base_power,
        "counter_bonus": counter_bonus, "phase_multiplier": phase_mult,
        "contribution": contribution, "matched_threats": matched,
        "created_at": now_iso,
    })
    # Update participant total
    await db.world_boss_participants.update_one(
        {"id": part["id"]},
        {"$inc": {"total_contribution": contribution, "teams_sent": 1},
         "$set": {"updated_at": now_iso}},
    )
    # Update event HP + phase
    new_ev = await db.world_boss_events.find_one_and_update(
        {"id": event_id},
        {"$inc": {"current_hp": -contribution},
         "$set": {"updated_at": now_iso}},
        return_document=True, projection={"_id": 0},
    )
    if new_ev:
        total_hp = max(1, new_ev.get("total_hp", 1))
        ratio = max(0.0, new_ev.get("current_hp", 0) / total_hp)
        catalog = await db.world_boss_catalog.find_one(
            {"slug": new_ev["boss_slug"]}, {"_id": 0},
        )
        new_phase = await _current_phase_for_hp_ratio(catalog, ratio)
        if new_phase != new_ev.get("phase"):
            await db.world_boss_events.update_one(
                {"id": event_id}, {"$set": {"phase": new_phase}},
            )
        # If HP reached 0 → immediate completion (skip timer)
        if new_ev.get("current_hp", 1) <= 0:
            await resolve_stuck_world_boss_event(
                event_id, dry_run=False, reason="hp_zero_completion",
            )
    # Mark adventurers as engaged
    await db.adventurers.update_many(
        {"id": {"$in": body.adventurer_ids}},
        {"$set": {"is_available": False,
                  "expedition_in_progress": True,
                  "current_world_boss_event_id": event_id,
                  "updated_at": now_iso}},
    )
    await _emit_audit(
        "WORLD_BOSS_CONTRIBUTION_RECORDED", actor_guild_id=guild["id"],
        related_entity_id=event_id,
        metadata={"contribution": contribution, "matched": matched},
    )
    # Achievement triggers (best-effort)
    try:
        from app.achievements.trigger_emitter import emit_achievement_trigger
        await emit_achievement_trigger(
            db, event_name="world_boss_participated",
            guild_id=guild["id"],
            idempotency_key=f"wb_participated:{guild['id']}:{event_id}",
            payload={"event_id": event_id, "contribution": contribution},
        )
    except Exception as exc:
        logger.debug("achievement emit skipped: %s", exc)
    return {"contribution": contribution, "matched_threats": matched,
            "phase": (new_ev or ev).get("phase", 1),
            "current_hp": (new_ev or ev).get("current_hp", 0)}


@router.get("/events/{event_id}/ranking")
async def get_ranking(event_id: str,
                      current_user: dict = Depends(get_current_user)):
    parts = await db.world_boss_participants.find(
        {"event_id": event_id}, {"_id": 0},
    ).sort("total_contribution", -1).limit(20).to_list(20)
    # Attach guild names
    gids = [p["guild_id"] for p in parts]
    gmap = {g["id"]: g["name"] for g in await db.guilds.find(
        {"id": {"$in": gids}}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)}
    return {"ranking": [
        {"rank": i + 1, "guild_id": p["guild_id"],
         "guild_name": gmap.get(p["guild_id"], "?"),
         "contribution": p.get("total_contribution", 0),
         "teams_sent": p.get("teams_sent", 0)}
        for i, p in enumerate(parts)
    ]}


@router.get("/events/{event_id}/report")
async def get_report(event_id: str,
                     current_user: dict = Depends(get_current_user)):
    ev = await db.world_boss_events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(404, "event_not_found")
    if ev["status"] not in ("completed", "failed"):
        raise HTTPException(409, "event_not_finalized")
    guild = await user_guild_or_404(db, current_user["id"])
    reward = await db.world_boss_rewards.find_one(
        {"event_id": event_id, "guild_id": guild["id"]}, {"_id": 0},
    )
    return {"event": _event_public(ev), "reward": reward}


# ── ADMIN ROUTES ──────────────────────────────────────────────────────
@admin_router.post("/events")
async def admin_create_event(body: CreateEventBody,
                             admin: dict = Depends(get_admin_user)):
    catalog = await db.world_boss_catalog.find_one(
        {"slug": body.boss_slug}, {"_id": 0},
    )
    if not catalog:
        raise HTTPException(404, "boss_not_found")
    now = _utc_now()
    starts_at = body.starts_at or now.isoformat()
    duration_h = catalog.get("duration_hours_default", 72)
    ends_at = body.ends_at or (now + timedelta(hours=duration_h)).isoformat()
    total_hp = body.total_hp_override or catalog.get("total_hp_default", 1_000_000)
    ev_id = str(uuid.uuid4())
    doc = {
        "id": ev_id, "boss_slug": body.boss_slug,
        "name_it": catalog["name_it"], "name_en": catalog["name_en"],
        "status": "scheduled",
        "starts_at": starts_at, "ends_at": ends_at,
        "total_hp": total_hp, "current_hp": total_hp,
        "phase": 1, "server_progress": 0.0,
        "threats": catalog["phases"][0]["threats"],
        "continent_scope": "global",
        "created_at": now.isoformat(),
        "resolved_at": None, "resolution_started_at": None,
        "recovered": False,
    }
    await db.world_boss_events.insert_one(doc)
    await _emit_audit("WORLD_BOSS_EVENT_CREATED", None, ev_id,
                      {"boss_slug": body.boss_slug, "total_hp": total_hp})
    return {"event": _event_public(doc)}


@admin_router.post("/events/{event_id}/start")
async def admin_start_event(event_id: str,
                            admin: dict = Depends(get_admin_user)):
    from pymongo import ReturnDocument
    now_iso = _utc_now().isoformat()
    r = await db.world_boss_events.find_one_and_update(
        {"id": event_id, "status": "scheduled"},
        {"$set": {"status": "active", "starts_at": now_iso,
                  "updated_at": now_iso}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not r:
        raise HTTPException(409, "event_not_scheduled_or_missing")
    await _emit_audit("WORLD_BOSS_EVENT_STARTED", None, event_id,
                      {"started_at": now_iso})
    return {"event": _event_public(r)}


@admin_router.post("/events/{event_id}/resolve")
async def admin_resolve_event(event_id: str,
                              admin: dict = Depends(get_admin_user)):
    # Force expiry: set ends_at to now, then invoke resolver
    now_iso = _utc_now().isoformat()
    await db.world_boss_events.update_one(
        {"id": event_id, "status": {"$in": ["active", "scheduled"]}},
        {"$set": {"ends_at": now_iso, "updated_at": now_iso}},
    )
    out = await resolve_stuck_world_boss_event(
        event_id, dry_run=False, reason="admin_force_resolve",
    )
    return out


@admin_router.post("/events/{event_id}/recover")
async def admin_recover_event(event_id: str,
                              admin: dict = Depends(get_admin_user)):
    return await resolve_stuck_world_boss_event(
        event_id, dry_run=False, reason="admin_force_recovery",
    )


__all__ = ["router", "admin_router", "seed_world_boss_catalog",
           "try_resolve_expired_events_for_guild",
           "resolve_stuck_world_boss_event",
           "ALVEORA_SLUG", "THREAT_COUNTER_MAP"]
