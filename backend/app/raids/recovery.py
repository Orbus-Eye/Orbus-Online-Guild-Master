"""ROUND 16.1.1 Hotfix — Raid stuck recovery (idempotent).

Risolve raid che restano `status=in_progress` dopo `ends_at` perché
`POST /api/raids/{id}/complete` non è mai stato chiamato (è manuale,
nessuno scheduler globale lo invoca).

Strategia:
1. Atomic claim via `find_one_and_update` (CAS sullo status) — solo
   una concorrenza vince.
2. Replay deterministico della stessa logica di `complete_raid`
   (rng seeded by raid_id), così il raid recovered emette outcome
   identico a quello che il giocatore avrebbe ottenuto cliccando
   "Completa".
3. Reward applicate normalmente. Marker `recovered=True` +
   `recovery_reason` su `raids` per audit.
4. Squadra rilasciata (tutti gli `adventurer_id` partecipanti →
   `is_available=true`, `expedition_in_progress=false`).
5. Audit event `raid_recovered` scritto in `audit_log`.

Idempotenza: la CAS step (1) garantisce che chiamate ripetute non
duplichino reward/audit/release. Il replay deterministico garantisce
che dry-run e apply producano lo stesso outcome.
"""
from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.raids.contracts import raid_progression_rewards
from app.expeditions.services import _resolve_levelup

logger = logging.getLogger("orbus.raids.recovery")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _outcome_for_chances(rng: random.Random, chances: list[int]) -> tuple[str, list[bool]]:
    """Deterministic per-party rolls; mirrors raids/__init__.py."""
    rolls = [rng.randint(1, 100) <= int(c) for c in (chances or [])]
    succ = sum(1 for r in rolls if r)
    n = len(rolls) or 1
    if succ == n:
        outcome = "victory"
    elif succ == 0:
        outcome = "wipe"
    else:
        outcome = "partial"
    return outcome, rolls


def _outcome_multiplier(outcome: str) -> float:
    return {"victory": 1.0, "partial": 0.5, "wipe": 0.0}.get(outcome, 0.0)


async def _preview_recovery(db, raid: dict) -> dict:
    """Read-only preview of what `resolve_stuck_raid` would do.

    Same deterministic outcome as the actual recovery — no DB writes.
    """
    raid_id = raid["id"]
    rng = random.Random(raid_id)
    chances = raid.get("success_chance_per_party") or []
    outcome, party_rolls = _outcome_for_chances(rng, chances)
    multiplier = _outcome_multiplier(outcome)
    rd = await db.raid_dungeons.find_one(
        {"id": raid["raid_dungeon_id"]}, {"_id": 0}
    ) or {}
    from app.arfus_forge import bonus_pct as _arfus_bonus
    damage_bonus = await _arfus_bonus(
        raid["guild_id"], "combat_damage"
    )
    leader_xp_bonus = await _arfus_bonus(
        raid["guild_id"], "leader_experience"
    )
    gold = int(rd.get("base_gold_reward", 0) * multiplier)
    xp_per_member = int(
        rd.get("base_xp_per_member", 0)
        * multiplier
        * (1.0 + leader_xp_bonus / 100.0)
    )
    de_min = rd.get("guaranteed_dragon_essence_min", 1)
    de_max = rd.get("guaranteed_dragon_essence_max", 3)
    if outcome == "victory":
        de_count = rng.randint(de_min, de_max)
    elif outcome == "partial":
        de_count = max(0, de_min // 2)
    else:
        de_count = 0
    progression = raid_progression_rewards(
        raid.get("raid_dungeon_slug", ""),
        outcome,
    )
    members = await db.raid_participants.count_documents({"raid_id": raid_id})
    return {
        "raid_id": raid_id,
        "guild_id": raid.get("guild_id"),
        "raid_dungeon_slug": raid.get("raid_dungeon_slug"),
        "ends_at": raid.get("ends_at"),
        "members_blocked": int(members),
        "proposed_outcome": outcome,
        "proposed_gold": gold,
        "proposed_xp_per_member": xp_per_member,
        "proposed_dragon_essence": de_count,
        "proposed_progression_rewards": progression,
        "proposed_raid_score": int(
            int(raid.get("team_power_combined", 0))
            * multiplier
            * (1.0 + damage_bonus / 100.0)
        ),
    }


async def resolve_stuck_raid(
    db,
    raid_id: str,
    *,
    dry_run: bool = True,
    reason: str = "auto_recovery_stuck_after_ends_at",
) -> dict:
    """Resolve a single stuck raid idempotently.

    Returns one of:
      * `{"action": "skipped", "reason": "not_found"}`
      * `{"action": "skipped", "reason": "not_eligible"}` (already completed / not expired)
      * `{"action": "previewed", ...}` (dry_run=True)
      * `{"action": "resolved", ...}` (dry_run=False, success)
    """
    raid = await db.raids.find_one({"id": raid_id}, {"_id": 0})
    if not raid:
        return {"raid_id": raid_id, "action": "skipped", "reason": "not_found"}

    now = _utc_now()
    now_iso = now.isoformat()

    # Eligibility: must be in_progress AND ends_at already passed.
    if raid.get("status") != "in_progress":
        return {
            "raid_id": raid_id, "action": "skipped",
            "reason": f"already_{raid.get('status')}",
        }
    try:
        ends_at = datetime.fromisoformat(raid["ends_at"])
    except Exception:
        return {
            "raid_id": raid_id, "action": "skipped",
            "reason": "ends_at_invalid",
        }
    if now < ends_at:
        return {
            "raid_id": raid_id, "action": "skipped",
            "reason": "still_running",
        }

    if dry_run:
        preview = await _preview_recovery(db, raid)
        preview["action"] = "previewed"
        return preview

    # ── Atomic CAS claim ──────────────────────────────────────────
    # Only one concurrent caller can transition `in_progress` → `resolving`.
    # If the CAS fails, another worker (or a manual /complete call)
    # already resolved this raid — return skipped.
    claimed = await db.raids.find_one_and_update(
        {"id": raid_id, "status": "in_progress"},
        {"$set": {
            "status": "resolving",
            "resolution_started_at": now_iso,
            "updated_at": now_iso,
        }},
        projection={"_id": 0},
    )
    if not claimed:
        return {
            "raid_id": raid_id, "action": "skipped",
            "reason": "lost_race_to_claim",
        }

    # ── Deterministic outcome replay (mirrors complete_raid) ──────
    rng = random.Random(raid_id)
    outcome, party_rolls = _outcome_for_chances(
        rng, claimed.get("success_chance_per_party") or []
    )
    multiplier = _outcome_multiplier(outcome)
    rd = await db.raid_dungeons.find_one(
        {"id": claimed["raid_dungeon_id"]}, {"_id": 0}
    ) or {}
    from app.arfus_forge import bonus_pct as _arfus_bonus
    damage_bonus = await _arfus_bonus(
        claimed["guild_id"], "combat_damage"
    )
    leader_xp_bonus = await _arfus_bonus(
        claimed["guild_id"], "leader_experience"
    )
    gold = int(rd.get("base_gold_reward", 0) * multiplier)
    xp_per_member = int(
        rd.get("base_xp_per_member", 0)
        * multiplier
        * (1.0 + leader_xp_bonus / 100.0)
    )
    de_min = rd.get("guaranteed_dragon_essence_min", 1)
    de_max = rd.get("guaranteed_dragon_essence_max", 3)
    if outcome == "victory":
        de_count = rng.randint(de_min, de_max)
    elif outcome == "partial":
        de_count = max(0, de_min // 2)
    else:
        de_count = 0
    progression = raid_progression_rewards(
        claimed.get("raid_dungeon_slug", ""),
        outcome,
    )
    raid_score = int(
        int(claimed.get("team_power_combined", 0))
        * multiplier
        * (1.0 + damage_bonus / 100.0)
    )

    # ── Apply guild rewards (gold + counters) ─────────────────────
    await db.guilds.update_one(
        {"id": claimed["guild_id"]},
        {"$inc": {
            "gold": gold,
            "raid_tokens": progression["raid_tokens"],
            "legendary_fragments": progression["legendary_fragments"],
            "raids_completed_count": 1,
            "raids_victory_count": 1 if outcome == "victory" else 0,
        }, "$max": {"max_raid_score": raid_score},
         "$set": {
            "last_raid_completed_at": now_iso,
            "updated_at": now_iso,
        }},
    )

    # ── Per-participant XP + outcome flag ─────────────────────────
    participants = await db.raid_participants.find(
        {"raid_id": raid_id}, {"_id": 0}
    ).to_list(40)
    for p_doc in participants:
        idx = p_doc["party_idx"]
        survived = party_rolls[idx - 1] if idx - 1 < len(party_rolls) else False
        gained = xp_per_member if survived else 0
        await db.raid_participants.update_one(
            {"id": p_doc["id"]},
            {"$set": {
                "outcome": "survived" if survived else "fainted",
                "xp_gained": gained,
            }},
        )
        if gained:
            adv = await db.adventurers.find_one(
                {"id": p_doc["adventurer_id"], "guild_id": claimed["guild_id"]},
                {"_id": 0},
            )
            if adv:
                adv["experience"] = int(adv.get("experience", 0)) + gained
                _resolve_levelup(adv)
                await db.adventurers.update_one(
                    {"id": adv["id"], "guild_id": claimed["guild_id"]},
                    {"$set": {
                        "experience": adv["experience"],
                        "level": adv["level"],
                        "strength": adv["strength"],
                        "agility": adv["agility"],
                        "intellect": adv["intellect"],
                        "endurance": adv["endurance"],
                        "faith": adv["faith"],
                    }},
                )

    # ── Release adventurers (atomic, no double-release possible) ──
    all_adv_ids = [p["adventurer_id"] for p in participants]
    released_res = await db.adventurers.update_many(
        {"id": {"$in": all_adv_ids}},
        {"$set": {
            "is_available": True,
            "expedition_in_progress": False,
            "updated_at": now_iso,
        }},
    )

    # ── Dragon essence (additive insert into inventory_items) ─────
    if de_count > 0:
        de_item = await db.items.find_one({"slug": "dragon_essence"}, {"_id": 0})
        if de_item:
            existing = await db.inventory_items.find_one({
                "guild_id": claimed["guild_id"],
                "item_id": de_item["id"],
                "is_bound": {"$ne": True},
            })
            if existing:
                await db.inventory_items.update_one(
                    {"id": existing["id"]}, {"$inc": {"quantity": de_count}},
                )
            else:
                await db.inventory_items.insert_one({
                    "id": str(uuid.uuid4()),
                    "instance_id": str(uuid.uuid4()),
                    "guild_id": claimed["guild_id"],
                    "item_id": de_item["id"],
                    "quantity": de_count,
                    "refinement_level": 0,
                    "enchants": [],
                    "affixes": [],
                    "reroll_count": 0,
                    "is_bound": False,
                    "disenchanted_at": None,
                    "acquired_at": now_iso,
                    "source": "raid_reward_recovered",
                })

    # T6 authored pool uses its own deterministic seed and grant ledger, so a
    # recovery produces exactly the same item decision as normal completion.
    from app.raids.loot import grant_raid_item_reward

    raid_item_reward = await grant_raid_item_reward(
        db,
        guild_id=claimed["guild_id"],
        raid_id=raid_id,
        raid_slug=claimed.get("raid_dungeon_slug"),
        outcome=outcome,
    )

    # ── Mark raid as completed with `recovered` metadata ──────────
    parties_outcome = [
        {"party_idx": i + 1,
         "success": bool(party_rolls[i]) if i < len(party_rolls) else False,
         "success_chance": (claimed.get("success_chance_per_party") or [0])[i]
                            if i < len(claimed.get("success_chance_per_party") or [])
                            else 0}
        for i in range(len(claimed.get("success_chance_per_party") or []))
    ]
    rewards = {
        "gold_total": gold,
        "xp_per_member": xp_per_member,
        "dragon_essence_count": de_count,
        "item_reward": raid_item_reward,
        **progression,
    }
    await db.raid_reward_grants.update_one(
        {"raid_id": raid_id},
        {"$setOnInsert": {
            "id": str(uuid.uuid4()),
            "raid_id": raid_id,
            "guild_id": claimed["guild_id"],
            "raid_dungeon_slug": claimed.get("raid_dungeon_slug"),
            "outcome": outcome,
            "rewards": rewards,
            "source": "raid.recovery",
            "status": "applied",
            "created_at": now_iso,
        }},
        upsert=True,
    )
    await db.raids.update_one(
        {"id": raid_id},
        {"$set": {
            "status": "completed",
            "outcome": outcome,
            "completed_at": now_iso,
            "raid_score": raid_score,
            "parties_outcome": parties_outcome,
            "rewards": rewards,
            "recovered": True,
            "recovery_reason": reason,
            "recovery_completed_at": now_iso,
            "updated_at": now_iso,
        }},
    )
    from app.adventurers.career import record_career_activity_for_many

    await record_career_activity_for_many(
        db,
        guild_id=claimed["guild_id"],
        adventurer_ids=all_adv_ids,
        activity_kind="raid",
        activity_id=raid_id,
    )
    await db.raids.update_one(
        {"id": raid_id},
        {"$set": {"career_progress_recorded": True}},
    )
    # ── Audit emit (best-effort, never raises) ────────────────────
    audit_emitted = False
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="raid_recovered",
            actor_user_id=None,
            actor_guild_id=claimed["guild_id"],
            source="raids.recovery",
            related_entity_id=raid_id,
            metadata={
                "raid_dungeon_slug": claimed.get("raid_dungeon_slug"),
                "outcome": outcome,
                "raid_score": raid_score,
                "gold_total": gold,
                "xp_per_member": xp_per_member,
                "dragon_essence_count": de_count,
                "members_released": int(released_res.modified_count or 0),
                "recovered": True,
                "recovery_reason": reason,
            },
        )
        audit_emitted = True
    except Exception as exc:
        logger.warning("raid_recovery.audit_emit_failed raid=%s err=%s",
                       raid_id, exc)

    # ── Best-effort downstream hooks (mirror complete_raid) ───────
    try:
        from app.seasons.season_stats import increment_seasonal_stat
        if outcome in ("victory", "partial"):
            await increment_seasonal_stat(
                db, guild_id=claimed["guild_id"], field="raid_clears", delta=1,
                source="raid_recovered", source_collection="raids",
                source_id=raid_id, flag_key="season_stat_recorded_clear",
            )
        if raid_score > 0:
            await increment_seasonal_stat(
                db, guild_id=claimed["guild_id"], field="raid_score",
                delta=int(raid_score),
                source="raid_recovered", source_collection="raids",
                source_id=raid_id, flag_key="season_stat_recorded_score",
            )
    except Exception as exc:
        logger.warning("raid_recovery.season_stats_failed raid=%s err=%s",
                       raid_id, exc)

    # ROUND 16.5.3 P1 — Guild XP drip (Prestigio di Gilda). Best-effort,
    # idempotente su raid_id, cap 1/giorno. Mirror del complete_raid.
    try:
        from app.achievements.xp_hooks import on_raid_completed
        await on_raid_completed(
            db, claimed["guild_id"], raid_id=raid_id, outcome=outcome,
        )
    except Exception as exc:
        logger.warning("raid_recovery.xp_hook_failed raid=%s err=%s",
                       raid_id, exc)

    return {
        "raid_id": raid_id,
        "guild_id": claimed["guild_id"],
        "action": "resolved",
        "outcome": outcome,
        "rewards_applied": rewards,
        "members_released": int(released_res.modified_count or 0),
        "audit_emitted": audit_emitted,
        "raid_score": raid_score,
        "recovered": True,
        "recovery_reason": reason,
    }


async def find_stuck_raids_for_guild(db, guild_id: str) -> list[dict]:
    """Return raids stuck (in_progress + ends_at<=now) for a given guild.

    Cheap helper for the on-visit fallback hook.
    """
    now_iso = _utc_now().isoformat()
    cur = db.raids.find(
        {
            "guild_id": guild_id,
            "status": "in_progress",
            "ends_at": {"$lte": now_iso},
        },
        {"_id": 0, "id": 1},
    )
    return await cur.to_list(50)


from app.core.job_freeze import frozen_when_active as _frozen_when_active


@_frozen_when_active(
    "orbus.raids.auto_resolve_stuck_raids_for_guild", freeze_return_value=0,
)
async def auto_resolve_stuck_raids_for_guild(db, guild_id: str) -> int:
    """On-visit fallback hook. Resolves all stuck raids for one guild.

    Returns count of raids actually resolved (excluding already-completed).
    Best-effort: never raises — failures are logged.
    """
    resolved = 0
    try:
        stuck = await find_stuck_raids_for_guild(db, guild_id)
        for r in stuck:
            try:
                out = await resolve_stuck_raid(
                    db, r["id"], dry_run=False,
                    reason="on_visit_fallback",
                )
                if out.get("action") == "resolved":
                    resolved += 1
            except Exception as exc:
                logger.warning(
                    "raid_recovery.on_visit_failed raid=%s err=%s",
                    r.get("id"), exc,
                )
    except Exception as exc:
        logger.warning(
            "raid_recovery.on_visit_scan_failed guild=%s err=%s",
            guild_id, exc,
        )
    return resolved


__all__ = [
    "resolve_stuck_raid",
    "auto_resolve_stuck_raids_for_guild",
    "find_stuck_raids_for_guild",
]
