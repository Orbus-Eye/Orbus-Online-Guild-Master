"""ROUND 5 Phase 18 — Solo Raid module.

A single-player raid is a 20-adventurer expedition split across 4 parties of 5.
No PvP, no Consortium, no cooperative play. Locked decisions live in
`/app/memory/ROUND_5_BRIEF.md` (§I + §M).

Public surface (router mounted in `app_factory`):
  • GET    /api/raids/catalog            → list of 3 raid_dungeons with gate
  • POST   /api/raids/preview            → success chance & combined power preview
  • POST   /api/raids/start              → create raid, mark 20 advs busy, 15min cooldown
  • POST   /api/raids/{raid_id}/complete → server-driven outcome + rewards + audit
  • GET    /api/raids                    → guild raid history
  • GET    /api/raids/{raid_id}          → raid report

Everything else (schema, formulas, report shape) is inline to keep the module
self-contained and minimise cross-file coupling for the audit/code review.
"""
from __future__ import annotations

import random as _legacy_random  # Round 11.4d — kept for any module-level seed only
import secrets
random = secrets.SystemRandom()  # PvP-ready: crypto-grade RNG
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.territory.cap_guard import over_cap_dep
from app.territory.guards import require_unlocked
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.audit.log import write_audit


router = APIRouter(prefix="/api/raids", tags=["raids"])


# Locked constants from brief
RAID_COOLDOWN_SECONDS = 15 * 60       # §I.7
REQUIRED_PARTY_COUNT = 4
REQUIRED_PARTY_SIZE = 5
REQUIRED_ROSTER = REQUIRED_PARTY_COUNT * REQUIRED_PARTY_SIZE  # 20


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def raid_dungeon_public(d: dict) -> dict:
    # ROUND 11.3 TASK A — derive min_adventurer_level from explicit field
    # if present, else from `tier` (1→8, 2→12, 3→15). Avoids a circular
    # import via late binding.
    from app.expeditions.level_gate import legacy_min_level_for_raid
    from app.content.lore_meta import raid_lore_meta
    meta = raid_lore_meta(d.get("slug", ""))
    return {
        "id": d["id"],
        "slug": d["slug"],
        "name": d["name"],
        "name_it": d.get("name_it") or meta.get("name_it") or d["name"],
        "description": d.get("description"),
        "description_it": d.get("description_it"),
        "tier": d.get("tier", 1),
        "recommended_power_combined": d["recommended_power_combined"],
        "min_roster_size": d.get("min_roster_size", REQUIRED_ROSTER),
        "required_party_count": d.get("required_party_count", REQUIRED_PARTY_COUNT),
        "required_party_size": d.get("required_party_size", REQUIRED_PARTY_SIZE),
        "party_focus_hints": d.get("party_focus_hints", []),
        "base_duration_seconds": d["base_duration_seconds"],
        "base_gold_reward": d["base_gold_reward"],
        "base_xp_per_member": d["base_xp_per_member"],
        "guaranteed_dragon_essence_min": d.get("guaranteed_dragon_essence_min", 1),
        "guaranteed_dragon_essence_max": d.get("guaranteed_dragon_essence_max", 3),
        "gate": d.get("gate") or {},
        "min_adventurer_level": legacy_min_level_for_raid(d),
        # ROUND 13a — Lore meta (additive, PII-safe).
        "lore_theme": d.get("lore_theme") or meta.get("lore_theme"),
        "content_family": d.get("content_family") or meta.get("content_family") or "baseline",
        "emotional_tone": d.get("emotional_tone") or meta.get("emotional_tone"),
        "boss_name": d.get("boss_name") or meta.get("boss_name"),
        "narrative_hook": d.get("narrative_hook") or meta.get("narrative_hook"),
        "spoiler_level": d.get("spoiler_level") or meta.get("spoiler_level") or "public",
        "is_new": meta.get("is_new", False),
        "is_void_undead": meta.get("is_void_undead", False),
        "lore_reviewed": bool(d.get("lore_reviewed", False)),
    }


def raid_public(r: dict) -> dict:
    # ROUND 16.5.1 B.4 — countdown server-side (evita drift client)
    remaining = None
    status = r.get("status")
    ends_at = r.get("ends_at")
    if status in ("in_progress",) and ends_at:
        try:
            end_dt = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            remaining = max(0, int((end_dt - now_dt).total_seconds()))
        except Exception:
            remaining = None
    return {
        "id": r["id"],
        "guild_id": r["guild_id"],
        "raid_dungeon_slug": r["raid_dungeon_slug"],
        "status": status,
        "outcome": r.get("outcome"),
        "team_power_combined": r["team_power_combined"],
        "recommended_power_combined": r["recommended_power_combined"],
        "success_chance_combined": r["success_chance_combined"],
        "success_chance_per_party": r.get("success_chance_per_party", []),
        "raid_score": r.get("raid_score", 0),
        "started_at": r["started_at"],
        "ends_at": ends_at,
        "completed_at": r.get("completed_at"),
        "duration_seconds": r.get("duration_seconds"),
        "remaining_seconds": remaining,
        "rewards": r.get("rewards"),
        "parties_outcome": r.get("parties_outcome", []),
    }


# ────────────────────────────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────────────────────────────
class PartyIn(BaseModel):
    party_idx: int = Field(..., ge=1, le=4)
    adventurer_ids: List[str] = Field(..., min_length=5, max_length=5)


class RaidPreviewIn(BaseModel):
    raid_slug: str
    parties: List[PartyIn] = Field(..., min_length=4, max_length=4)


class RaidStartIn(BaseModel):
    raid_slug: str
    parties: List[PartyIn] = Field(..., min_length=4, max_length=4)


# ────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────
async def _resolve_raid_dungeon(slug: str) -> dict:
    rd = await db.raid_dungeons.find_one({"slug": slug, "is_active": True}, {"_id": 0})
    if not rd:
        raise HTTPException(status_code=404, detail="raid_dungeon_not_found")
    return rd


async def _validate_parties_and_advs(guild: dict, parties: List[PartyIn]) -> List[dict]:
    """Returns the 20 adventurer docs (in order party1..party4)."""
    # 1. Party indices must be {1,2,3,4} exactly
    idxs = sorted([p.party_idx for p in parties])
    if idxs != [1, 2, 3, 4]:
        raise HTTPException(status_code=422, detail="raids.parties_invalid_indices")
    # 2. No duplicate adv across all 4 parties
    all_ids = [aid for p in parties for aid in p.adventurer_ids]
    if len(set(all_ids)) != REQUIRED_ROSTER:
        raise HTTPException(status_code=422, detail="raids.duplicate_adventurer")
    # 3. All advs must belong to guild + be available
    adv_docs = await db.adventurers.find(
        {"id": {"$in": all_ids}, "guild_id": guild["id"]}, {"_id": 0}
    ).to_list(50)
    if len(adv_docs) != REQUIRED_ROSTER:
        raise HTTPException(status_code=422, detail="raids.adventurers_not_owned_or_missing")
    # ROUND 6B.3 Wave 1.5 — explicit retired check (423 with structured detail).
    retired_ids = [a["id"] for a in adv_docs if a.get("is_retired") is True]
    if retired_ids:
        raise HTTPException(
            status_code=423,
            detail={
                "code": "adventurers.retired_in_set",
                "source": "raid.start",
                "retired_adventurer_ids": retired_ids,
                "count": len(retired_ids),
                "user_message": (
                    f"La selezione include {len(retired_ids)} avventurier"
                    f"{'i' if len(retired_ids) > 1 else 'o'} congedat"
                    f"{'i' if len(retired_ids) > 1 else 'o'}. Rimuovili dalla selezione."
                ),
            },
        )
    busy = [a for a in adv_docs if a.get("is_available") is False or a.get("expedition_in_progress")]
    if busy:
        raise HTTPException(status_code=422, detail="raids.adventurer_busy")
    # Build order-preserving list following parties order
    by_id = {a["id"]: a for a in adv_docs}
    ordered = []
    for p in sorted(parties, key=lambda x: x.party_idx):
        for aid in p.adventurer_ids:
            ordered.append(by_id[aid])
    return ordered


def _adv_power(a: dict) -> int:
    base = (
        int(a.get("strength", 0)) + int(a.get("agility", 0))
        + int(a.get("intellect", 0)) + int(a.get("endurance", 0))
        + int(a.get("faith", 0))
    )
    return base + int(a.get("level", 1)) * 2


def _party_power(adv_docs: List[dict]) -> int:
    """Phase 6+ formula plus role-comp bonus identical to expeditions."""
    base = sum(_adv_power(a) for a in adv_docs)
    roles = {a.get("class_role") for a in adv_docs}
    bonus = 0
    if "Tank" in roles:
        bonus += 5
    if "Healer" in roles:
        bonus += 5
    if "DPS" in roles:
        bonus += 5
    if {"Tank", "Healer", "DPS"}.issubset(roles):
        bonus += 10
    return base + bonus


def _success_chance(party_power: int, party_rec: int) -> int:
    # Same lineal-clamp formula as expeditions, per-party
    return max(5, min(95, 50 + (party_power - party_rec)))


def _combined_success_chance(total_power: int, total_rec: int) -> int:
    # Slightly gentler curve for the combined view: /4 dampens the swing
    return max(5, min(95, 40 + (total_power - total_rec) // 4))


def _compute_preview(rd: dict, parties_docs: List[List[dict]]) -> dict:
    party_rec = rd["recommended_power_combined"] // 4
    powers = [_party_power(party) for party in parties_docs]
    chances = [_success_chance(p, party_rec) for p in powers]
    total = sum(powers)
    return {
        "team_power_combined": total,
        "recommended_power_combined": rd["recommended_power_combined"],
        "success_chance_per_party": chances,
        "success_chance_combined": _combined_success_chance(total, rd["recommended_power_combined"]),
        "party_powers": powers,
    }


def _outcome_for_chances(rng: random.Random, chances: List[int]) -> tuple[str, List[bool]]:
    rolls = [rng.randint(1, 100) <= c for c in chances]
    succ = sum(rolls)
    if succ == 4:
        return "victory", rolls
    if succ in (2, 3):
        return "partial", rolls
    return "wipe", rolls


def _outcome_multiplier(outcome: str) -> float:
    return {"victory": 1.0, "partial": 0.5, "wipe": 0.1}[outcome]


# ────────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────────
@router.get("/catalog")
async def list_catalog(current_user: dict = Depends(get_current_user)):
    """List 3 raid_dungeons with the guild's gate eligibility evaluated."""
    guild = await user_guild_or_404(db, current_user["id"])
    raid_dungeons = await db.raid_dungeons.find(
        {"is_active": True}, {"_id": 0}
    ).sort("tier", 1).to_list(20)

    adv_count = await db.adventurers.count_documents({"guild_id": guild["id"]})
    peak = int(guild.get("max_team_power_ever", 0))

    out = []
    for rd in raid_dungeons:
        gate = rd.get("gate") or {}
        unlocked = True
        gate_reason = None
        if adv_count < gate.get("min_roster_size", REQUIRED_ROSTER):
            unlocked = False
            gate_reason = "roster_too_small"
        elif gate.get("min_max_team_power_ever") and peak < gate["min_max_team_power_ever"]:
            unlocked = False
            gate_reason = "max_team_power_too_low"
        pub = raid_dungeon_public(rd)
        pub["unlocked"] = unlocked
        pub["gate_reason"] = gate_reason
        pub["guild_roster_count"] = adv_count
        pub["guild_max_team_power_ever"] = peak
        out.append(pub)

    # Cooldown status
    last_completed = guild.get("last_raid_completed_at")
    cooldown_remaining = 0
    if last_completed:
        try:
            lc = datetime.fromisoformat(last_completed)
        except Exception:
            lc = _utc_now() - timedelta(days=1)
        cooldown_remaining = max(
            0, RAID_COOLDOWN_SECONDS - int((_utc_now() - lc).total_seconds())
        )
    return {
        "raid_dungeons": out,
        "cooldown_seconds_remaining": cooldown_remaining,
        "cooldown_total_seconds": RAID_COOLDOWN_SECONDS,
    }


@router.post("/preview")
async def preview_raid(payload: RaidPreviewIn, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    rd = await _resolve_raid_dungeon(payload.raid_slug)
    advs_ordered = await _validate_parties_and_advs(guild, payload.parties)
    # ROUND 11.3 TASK A — level gate (also on preview so FE blocks early).
    from app.expeditions.level_gate import (
        enforce_min_adventurer_level,
        legacy_min_level_for_raid,
    )
    enforce_min_adventurer_level(
        advs_ordered, legacy_min_level_for_raid(rd), source="raid.preview",
    )
    parties_docs = [advs_ordered[i * 5:(i + 1) * 5] for i in range(4)]
    p = _compute_preview(rd, parties_docs)
    return {
        "raid_slug": payload.raid_slug,
        **p,
        "base_duration_seconds": rd["base_duration_seconds"],
        "base_gold_reward": rd["base_gold_reward"],
        "base_xp_per_member": rd["base_xp_per_member"],
        "guaranteed_dragon_essence_min": rd.get("guaranteed_dragon_essence_min", 1),
        "guaranteed_dragon_essence_max": rd.get("guaranteed_dragon_essence_max", 3),
    }


@router.post(
    "/start",
    status_code=201,
    dependencies=[
        Depends(require_unlocked("raid.start.t1")),
        Depends(over_cap_dep("raid.start")),
    ],
)
async def start_raid(payload: RaidStartIn, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    rd = await _resolve_raid_dungeon(payload.raid_slug)

    # Cooldown
    last_completed = guild.get("last_raid_completed_at")
    if last_completed:
        try:
            lc = datetime.fromisoformat(last_completed)
            remaining = RAID_COOLDOWN_SECONDS - int((_utc_now() - lc).total_seconds())
            if remaining > 0:
                raise HTTPException(
                    status_code=422,
                    detail="raids.cooldown_active",
                )
        except ValueError:
            pass

    # No concurrent raid in progress
    in_progress = await db.raids.find_one(
        {"guild_id": guild["id"], "status": "in_progress"}, {"_id": 0, "id": 1}
    )
    if in_progress:
        raise HTTPException(status_code=422, detail="raids.already_in_progress")

    advs_ordered = await _validate_parties_and_advs(guild, payload.parties)

    # ROUND 11.3 TASK A — level gate before commit. Mirrors expedition.dispatch.
    from app.expeditions.level_gate import (
        enforce_min_adventurer_level,
        legacy_min_level_for_raid,
    )
    enforce_min_adventurer_level(
        advs_ordered, legacy_min_level_for_raid(rd), source="raid.start",
    )

    parties_docs = [advs_ordered[i * 5:(i + 1) * 5] for i in range(4)]
    p = _compute_preview(rd, parties_docs)

    raid_id = str(uuid.uuid4())
    now = _utc_now()
    ends_at = now + timedelta(seconds=rd["base_duration_seconds"])
    raid_doc = {
        "id": raid_id,
        "guild_id": guild["id"],
        "raid_dungeon_id": rd["id"],
        "raid_dungeon_slug": rd["slug"],
        "status": "in_progress",
        "outcome": None,
        "team_power_combined": p["team_power_combined"],
        "recommended_power_combined": rd["recommended_power_combined"],
        "success_chance_per_party": p["success_chance_per_party"],
        "success_chance_combined": p["success_chance_combined"],
        "raid_score": 0,
        "started_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "completed_at": None,
        "duration_seconds": rd["base_duration_seconds"],
        "rewards": None,
        "parties_outcome": [],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.raids.insert_one(raid_doc)

    # Insert raid_participants & flag advs busy (best-effort atomic-ish)
    parts = []
    for party_idx, party in enumerate(parties_docs, start=1):
        for a in party:
            parts.append({
                "id": str(uuid.uuid4()),
                "raid_id": raid_id,
                "guild_id": guild["id"],
                "adventurer_id": a["id"],
                "party_idx": party_idx,
                "role_snapshot": a.get("class_role"),
                "class_snapshot": a.get("class_name"),
                "level_snapshot": a.get("level", 1),
                "total_power_snapshot": _adv_power(a),
                "outcome": None,
                "xp_gained": 0,
                "created_at": now.isoformat(),
            })
    if parts:
        await db.raid_participants.insert_many(parts, ordered=False)

    all_adv_ids = [a["id"] for a in advs_ordered]
    await db.adventurers.update_many(
        {"id": {"$in": all_adv_ids}},
        {"$set": {"is_available": False, "expedition_in_progress": True, "updated_at": now.isoformat()}},
    )

    # Audit
    try:
        await write_audit(
            db, event_type="raid_started", actor_user_id=current_user["id"],
            actor_guild_id=guild["id"], source="raids.start",
            related_entity_id=raid_id,
            metadata={
                "raid_dungeon_slug": rd["slug"],
                "team_power_combined": p["team_power_combined"],
                "success_chance_combined": p["success_chance_combined"],
            },
        )
    except Exception:
        pass

    return {"raid": raid_public(raid_doc)}


@router.post("/{raid_id}/complete")
async def complete_raid(raid_id: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    raid = await db.raids.find_one({"id": raid_id, "guild_id": guild["id"]}, {"_id": 0})
    if not raid:
        raise HTTPException(status_code=404, detail="raid_not_found")
    if raid["status"] == "completed":
        return {"raid": raid_public(raid)}

    # Time-gated: must wait until ends_at
    try:
        ends_at = datetime.fromisoformat(raid["ends_at"])
    except Exception:
        ends_at = _utc_now() - timedelta(seconds=1)
    if _utc_now() < ends_at:
        raise HTTPException(status_code=422, detail="raids.not_ended_yet")

    rng = random.Random(raid_id)  # deterministic per raid for replay safety
    outcome, party_rolls = _outcome_for_chances(rng, raid["success_chance_per_party"])
    multiplier = _outcome_multiplier(outcome)

    rd = await db.raid_dungeons.find_one({"id": raid["raid_dungeon_id"]}, {"_id": 0})
    # ROUND 16.3 Phase 5B — Arfus passive bonuses (0 if none active).
    from app.arfus_forge import bonus_pct as _arfus_bonus
    _dmg_bonus = await _arfus_bonus(guild["id"], "combat_damage")
    _leader_xp_bonus = await _arfus_bonus(guild["id"], "leader_experience")
    gold = int(rd["base_gold_reward"] * multiplier)
    xp_per_member = int(rd["base_xp_per_member"] * multiplier
                        * (1.0 + _leader_xp_bonus / 100.0))

    # dragon_essence: guaranteed range, scaled by outcome
    de_min = rd.get("guaranteed_dragon_essence_min", 1)
    de_max = rd.get("guaranteed_dragon_essence_max", 3)
    if outcome == "victory":
        de_count = rng.randint(de_min, de_max)
    elif outcome == "partial":
        de_count = max(0, de_min // 2)
    else:
        de_count = 0

    # Apply rewards
    now = _utc_now()
    raid_score = int(raid["team_power_combined"] * multiplier
                     * (1.0 + _dmg_bonus / 100.0))
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$inc": {
            "gold": gold,
            "raids_completed_count": 1,
            "raids_victory_count": 1 if outcome == "victory" else 0,
        }, "$max": {"max_raid_score": raid_score},
         "$set": {
            "last_raid_completed_at": now.isoformat(),
            "updated_at": now.isoformat(),
         }},
    )

    # XP & survived flag per participant
    participants = await db.raid_participants.find({"raid_id": raid_id}, {"_id": 0}).to_list(40)
    for p_doc in participants:
        idx = p_doc["party_idx"]
        survived = party_rolls[idx - 1]
        gained = xp_per_member if survived else 0
        await db.raid_participants.update_one(
            {"id": p_doc["id"]},
            {"$set": {"outcome": "survived" if survived else "fainted", "xp_gained": gained}},
        )
        if gained:
            await db.adventurers.update_one(
                {"id": p_doc["adventurer_id"]},
                {"$inc": {"experience": gained}},
            )
    # Release advs
    all_adv_ids = [p["adventurer_id"] for p in participants]
    await db.adventurers.update_many(
        {"id": {"$in": all_adv_ids}},
        {"$set": {"is_available": True, "expedition_in_progress": False, "updated_at": now.isoformat()}},
    )

    # dragon_essence to guild inventory (additive insert into inventory_items)
    if de_count > 0:
        de_item = await db.items.find_one({"slug": "dragon_essence"}, {"_id": 0})
        if de_item:
            existing = await db.inventory_items.find_one(
                {"guild_id": guild["id"], "item_id": de_item["id"], "is_bound": {"$ne": True}}
            )
            if existing:
                await db.inventory_items.update_one(
                    {"id": existing["id"]}, {"$inc": {"quantity": de_count}},
                )
            else:
                await db.inventory_items.insert_one({
                    "id": str(uuid.uuid4()),
                    "instance_id": str(uuid.uuid4()),
                    "guild_id": guild["id"],
                    "item_id": de_item["id"],
                    "quantity": de_count,
                    "refinement_level": 0,
                    "enchants": [],
                    "affixes": [],
                    "reroll_count": 0,
                    "is_bound": False,
                    "disenchanted_at": None,
                    "acquired_at": now.isoformat(),
                    "source": "raid_reward",
                })

    # Persist raid completion
    parties_outcome = [
        {"party_idx": i + 1, "success": bool(party_rolls[i]),
         "success_chance": raid["success_chance_per_party"][i]}
        for i in range(4)
    ]
    rewards = {
        "gold_total": gold,
        "xp_per_member": xp_per_member,
        "dragon_essence_count": de_count,
    }
    await db.raids.update_one(
        {"id": raid_id},
        {"$set": {
            "status": "completed",
            "outcome": outcome,
            "completed_at": now.isoformat(),
            "raid_score": raid_score,
            "parties_outcome": parties_outcome,
            "rewards": rewards,
            "updated_at": now.isoformat(),
        }},
    )

    raid["status"] = "completed"
    raid["outcome"] = outcome
    raid["completed_at"] = now.isoformat()
    raid["raid_score"] = raid_score
    raid["parties_outcome"] = parties_outcome
    raid["rewards"] = rewards

    # ROUND 15 Phase 3 — achievement trigger for raid completion (best-effort).
    # Trigger only on victory/partial; wipes do not count for `raid_completed`.
    try:
        from app.achievements.engine import evaluate_achievements
        if outcome in ("victory", "partial"):
            await evaluate_achievements(
                guild["id"], "raid_completed",
                {"raid_id": raid_id, "outcome": outcome,
                 "raid_dungeon_id": raid["raid_dungeon_id"]},
                db=db,
            )
    except Exception:
        pass

    # ROUND 13b — seasonal raid stats (idempotent via raids.id + flag CAS).
    # Only victory/partial count toward `raid_clears`; `raid_score` always
    # adds the actual score computed above (0 if wipe → no-op).
    try:
        from app.seasons.season_stats import increment_seasonal_stat
        if outcome in ("victory", "partial"):
            await increment_seasonal_stat(
                db, guild_id=guild["id"], field="raid_clears", delta=1,
                source="raid_complete", source_collection="raids",
                source_id=raid_id, flag_key="season_stat_recorded_clear",
            )
        if raid_score > 0:
            await increment_seasonal_stat(
                db, guild_id=guild["id"], field="raid_score", delta=int(raid_score),
                source="raid_complete", source_collection="raids",
                source_id=raid_id, flag_key="season_stat_recorded_score",
            )
    except Exception:
        pass

    try:
        await write_audit(
            db, event_type="raid_completed", actor_user_id=current_user["id"],
            actor_guild_id=guild["id"], source="raids.complete",
            related_entity_id=raid_id,
            metadata={
                "raid_dungeon_slug": raid["raid_dungeon_slug"],
                "outcome": outcome,
                "raid_score": raid_score,
                "gold_total": gold,
                "xp_per_member": xp_per_member,
                "dragon_essence_count": de_count,
            },
        )
    except Exception:
        pass

    # Phase 19 — weekly quest progress hook (best-effort, never raises).
    # Only fires when outcome != "wipe". raids_completed always bumps;
    # raids_t2plus_success additionally requires tier>=2 AND outcome in
    # {"victory","partial"}. Gated by 20-adv roster (`/api/raids/start` already
    # enforces `roster_too_small`), so guilds <20 advs cannot trigger this.
    if outcome != "wipe":
        try:
            from app.quests.services import increment_weekly_progress
            tier = int(rd.get("tier", 1) or 1)
            await increment_weekly_progress(db, guild["id"], "raids_completed", 1)
            if tier >= 2 and outcome in ("victory", "partial"):
                await increment_weekly_progress(db, guild["id"], "raids_t2plus_success", 1)
            # ROUND 6E — contract progress (raids_completed)
            try:
                from app.contracts.services import increment_contract_progress
                await increment_contract_progress(
                    db, guild["id"], "raids_completed", 1,
                )
            except Exception:
                pass
            try:
                await write_audit(
                    db, event_type="weekly_quest_raid_progressed",
                    actor_user_id=current_user["id"], actor_guild_id=guild["id"],
                    source="raids.complete",
                    related_entity_id=raid_id,
                    metadata={
                        "raid_dungeon_slug": raid["raid_dungeon_slug"],
                        "tier": tier,
                        "outcome": outcome,
                    },
                )
            except Exception:
                pass
        except Exception:
            pass

    return {"raid": raid_public(raid)}


@router.get("")
async def list_raids(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    # ROUND 16.1.1 hotfix — on-visit fallback: auto-resolve any stuck raid
    # (status=in_progress, ends_at<=now) for this guild before returning the
    # list. Best-effort, never raises.
    try:
        from app.raids.recovery import auto_resolve_stuck_raids_for_guild
        await auto_resolve_stuck_raids_for_guild(db, guild["id"])
    except Exception:
        pass
    cursor = db.raids.find(
        {"guild_id": guild["id"]}, {"_id": 0},
    ).sort("created_at", -1).limit(30)
    rows = await cursor.to_list(30)
    return {"raids": [raid_public(r) for r in rows]}


# ══════════════════════════════════════════════════════════════════════
# ROUND 16.5.1 B.3 — Dashboard "Ultimo raid" + replay preview
# ══════════════════════════════════════════════════════════════════════

@router.get("/last")
async def get_last_raid(current_user: dict = Depends(get_current_user)):
    """Ritorna l'ultimo raid completato dell'utente + participants +
    disponibilità squadra per replay (best-effort).

    Se non esistono raid completati → 404 `no_completed_raid`.
    Nessun `remaining_seconds` calcolato (raid già chiuso)."""
    guild = await user_guild_or_404(db, current_user["id"])
    # Best-effort on-visit fallback
    try:
        from app.raids.recovery import auto_resolve_stuck_raids_for_guild
        await auto_resolve_stuck_raids_for_guild(db, guild["id"])
    except Exception:
        pass
    raid = await db.raids.find_one(
        {"guild_id": guild["id"], "status": "completed"},
        {"_id": 0},
        sort=[("completed_at", -1), ("created_at", -1)],
    )
    if not raid:
        raise HTTPException(status_code=404, detail="no_completed_raid")
    parts = await db.raid_participants.find(
        {"raid_id": raid["id"]}, {"_id": 0},
    ).to_list(40)
    return {
        "raid": raid_public(raid),
        "participants": [
            {"id": p["id"], "adventurer_id": p["adventurer_id"],
             "party_idx": p["party_idx"],
             "role_snapshot": p.get("role_snapshot")}
            for p in parts
        ],
    }


class RaidReplayPreviewIn(BaseModel):
    raid_slug: str
    squad_ids: List[str] = Field(..., min_length=20, max_length=20)


@router.post("/replay-preview")
async def raid_replay_preview(body: RaidReplayPreviewIn,
                              current_user: dict = Depends(get_current_user)):
    """Verifica se la stessa squadra può ripetere lo stesso raid_slug.

    Ritorna:
      - `raid_available`: bool (raid_dungeon esiste e is_active)
      - `all_adventurers_owned`: bool
      - `all_adventurers_available`: bool (nessuno busy/retired)
      - `unavailable_adventurers`: list di {id, name, reason}
      - `missing_adventurers`: list di id non trovati
    NON avvia niente. NON modifica nulla."""
    guild = await user_guild_or_404(db, current_user["id"])
    # Raid dungeon lookup
    rd = await db.raid_dungeons.find_one(
        {"slug": body.raid_slug, "is_active": True}, {"_id": 0},
    )
    raid_available = bool(rd)
    # Adventurers lookup
    advs = await db.adventurers.find(
        {"id": {"$in": body.squad_ids},
         "guild_id": guild["id"]},
        {"_id": 0, "id": 1, "name": 1, "level": 1,
         "is_available": 1, "is_retired": 1, "retired": 1},
    ).to_list(30)
    found_ids = {a["id"] for a in advs}
    missing = [aid for aid in body.squad_ids if aid not in found_ids]
    unavailable = []
    for a in advs:
        reasons = []
        if a.get("is_retired") or a.get("retired"):
            reasons.append("retired")
        if a.get("is_available") is False:
            reasons.append("busy")
        if reasons:
            unavailable.append({
                "id": a["id"], "name": a.get("name", "?"),
                "reasons": reasons,
            })
    return {
        "raid_available": raid_available,
        "all_adventurers_owned": len(missing) == 0,
        "all_adventurers_available": len(unavailable) == 0
                                     and len(missing) == 0,
        "unavailable_adventurers": unavailable,
        "missing_adventurers": missing,
        "raid_dungeon": raid_dungeon_public(rd) if rd else None,
    }


@router.get("/{raid_id}")
async def get_raid(raid_id: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    # ROUND 16.1.1 hotfix — on-visit fallback for the specific raid.
    try:
        from app.raids.recovery import resolve_stuck_raid
        await resolve_stuck_raid(
            db, raid_id, dry_run=False, reason="on_visit_fallback_detail",
        )
    except Exception:
        pass
    raid = await db.raids.find_one({"id": raid_id, "guild_id": guild["id"]}, {"_id": 0})
    if not raid:
        raise HTTPException(status_code=404, detail="raid_not_found")
    parts = await db.raid_participants.find({"raid_id": raid_id}, {"_id": 0}).to_list(40)
    # attach light-weight participants info
    return {
        "raid": raid_public(raid),
        "participants": [
            {
                "id": p["id"],
                "raid_id": p["raid_id"],
                "adventurer_id": p["adventurer_id"],
                "party_idx": p["party_idx"],
                "role_snapshot": p.get("role_snapshot"),
                "class_snapshot": p.get("class_snapshot"),
                "level_snapshot": p.get("level_snapshot"),
                "outcome": p.get("outcome"),
                "xp_gained": p.get("xp_gained", 0),
            }
            for p in parts
        ],
    }


__all__ = ["router"]
