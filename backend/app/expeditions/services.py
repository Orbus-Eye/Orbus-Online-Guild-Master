"""Expedition orchestration services (Phase 5.5e).

Hosts the full lifecycle:
- `_dispatch_expedition`: shared logic for both fresh start and replay.
- `_evaluate_dungeon_gate`: sticky soft-progression gate (Phase 7/8).
- `complete_due_expeditions` / `_complete_one_expedition`: lazy completion
  sweep with atomic claim, idempotent.
- `_check_replay_eligibility` / `_find_last_completed_expedition`: replay flow.
- `_resolve_levelup`: per-class stat picker on XP threshold loops.

All async helpers accept the Motor `db` handle as first positional arg so the
module remains import-safe (no implicit global db).
"""
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.expeditions.formulas import (
    adventurer_base_power as _adventurer_unit_power,
    adventurer_effective_power as _adventurer_effective_power,
    build_equipment_delta as _build_equipment_delta,
    compute_success_chance,
    compute_team_power,
    sum_xp_percent,
)
from app.expeditions.loot_tables import roll_loot_for_dungeon
from app.equipment.services import (
    _empty_slot_map,
    _item_summary_for_snapshot,
    _load_equipment_for_adventurer,
    _load_equipment_for_guild,
)
from app.items.services import item_public
from app.shared.constants import XP_THRESHOLD_PER_LEVEL


# Phase 5.6: cryptographically-secure RNG. Distributions unchanged vs `random.*`.
_rng = secrets.SystemRandom()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Public serializers ───────────────────────────────────────────────────────
def member_public(m: dict) -> dict:
    return {
        "id": m["id"],
        "expedition_id": m["expedition_id"],
        "adventurer_id": m["adventurer_id"],
        "name_snapshot": m["name_snapshot"],
        "class_name_snapshot": m["class_name_snapshot"],
        "role_snapshot": m["role_snapshot"],
        "level_snapshot": m["level_snapshot"],
        "strength_snapshot": m["strength_snapshot"],
        "agility_snapshot": m["agility_snapshot"],
        "intellect_snapshot": m["intellect_snapshot"],
        "endurance_snapshot": m["endurance_snapshot"],
        "faith_snapshot": m["faith_snapshot"],
        # Phase 6 — equipment at the moment of departure (immutable snapshot)
        "equipment_snapshot": m.get("equipment_snapshot", []),
        "equipment_power_snapshot": int(m.get("equipment_power_snapshot", 0)),
        # Phase 13 — traits at dispatch (immutable snapshot for determinism)
        "traits_snapshot": m.get("traits_snapshot", []),
        "total_power_snapshot": int(
            m.get("total_power_snapshot")
            if m.get("total_power_snapshot") is not None
            else (
                int(m["strength_snapshot"])
                + int(m["agility_snapshot"])
                + int(m["intellect_snapshot"])
                + int(m["endurance_snapshot"])
                + int(m["faith_snapshot"])
                + int(m.get("level_snapshot", 1)) * 2
                + int(m.get("equipment_power_snapshot", 0))
            )
        ),
    }


def expedition_public(e: dict) -> dict:
    out = {
        "id": e["id"],
        "guild_id": e["guild_id"],
        "dungeon_id": e["dungeon_id"],
        "dungeon_name": e.get("dungeon_name", ""),
        "status": e["status"],
        "started_at": e.get("started_at"),
        "completes_at": e.get("completes_at"),
        "completed_at": e.get("completed_at"),
        "team_power": e.get("team_power", 0),
        "success_chance": e.get("success_chance", 0),
        # Phase 7: equipment delta snapshot (immutable after start)
        "base_team_power": e.get("base_team_power", e.get("team_power", 0)),
        "equipment_power_bonus": int(e.get("equipment_power_bonus", 0)),
        "final_team_power": e.get("final_team_power", e.get("team_power", 0)),
        "success_chance_without_equipment": e.get(
            "success_chance_without_equipment", e.get("success_chance", 0)
        ),
        "success_chance_with_equipment": e.get(
            "success_chance_with_equipment", e.get("success_chance", 0)
        ),
        "equipment_delta_text": e.get("equipment_delta_text"),
        "final_score": e.get("final_score"),
        "result_summary": e.get("result_summary"),
        "result_log": e.get("result_log"),
        "gold_reward": e.get("gold_reward", 0),
        "xp_reward": e.get("xp_reward", 0),
        "loot_item_ids": e.get("loot_item_ids", []),
        # Phase 8: marks the run as a "Replay Last Run" dispatch (UI label).
        "is_replay": bool(e.get("is_replay", False)),
        "created_at": e["created_at"],
        "updated_at": e.get("updated_at", e["created_at"]),
    }
    if out["status"] == "in_progress" and out["completes_at"]:
        try:
            ca = datetime.fromisoformat(out["completes_at"])
            remaining = int((ca - utc_now()).total_seconds())
            out["seconds_remaining"] = max(0, remaining)
        except Exception:
            out["seconds_remaining"] = 0
    return out


# ─── Dungeon gating (sticky soft progression) ─────────────────────────────────
async def _evaluate_dungeon_gate(
    db, dungeon: dict, guild: dict
) -> tuple[bool, Optional[str]]:
    """Returns (unlocked, unlock_reason). Reason is None when unlocked.

    - Goblin Warrens: always unlocked (Phase 7 invariant).
    - Shadow Crypts: guild.level >= 1 AND adventurer_count >= 3 (Phase 7 invariant).
    - Dragon's Hoard: guild.level >= 2 OR peak_team_power_ever >= 65
      OR best-3 current team total_power >= 65 (Phase 8 sticky semantics).
    - All other dungeons: data-driven via `dungeon.gate` dict (Phase 11.2).
    """
    slug = dungeon.get("slug")
    if slug == "shadow-crypts":
        adv_count = await db.adventurers.count_documents({"guild_id": guild["id"]})
        if int(guild.get("level", 1)) >= 1 and adv_count >= 3:
            return True, None
        return False, "Requires guild level 1 and at least 3 adventurers"
    if slug == "dragons-hoard":
        if int(guild.get("level", 1)) >= 2:
            return True, None
        if int(guild.get("max_team_power_ever", 0)) >= 65:
            return True, None
        advs = await db.adventurers.find(
            {"guild_id": guild["id"]}, {"_id": 0}
        ).to_list(200)
        if advs:
            eq_map = await _load_equipment_for_guild(db, guild["id"])
            powers = []
            for a in advs:
                _slots, eq_p = eq_map.get(a["id"], (_empty_slot_map(), 0))
                powers.append(_adventurer_unit_power(a) + eq_p)
            powers.sort(reverse=True)
            best3 = sum(powers[:3])
            if best3 >= 65:
                return True, None
        return (
            False,
            "Requires guild level 2, team power \u2265 65, or peak team power ever \u2265 65",
        )
    # Phase 11.2: Goblin Warrens always unlocked; all other Phase-10 dungeons
    # delegate to the data-driven evaluator using their seed `gate` dict.
    if slug == "goblin-warrens":
        return True, None
    from app.dungeons.gates import evaluate_data_driven_gate

    return await evaluate_data_driven_gate(db, dungeon, guild)


# ─── Level-up resolver ────────────────────────────────────────────────────────
CLASS_LEVELUP_STAT = {
    "Warrior": lambda: _rng.choice(["strength", "endurance"]),
    "Rogue": lambda: "agility",
    "Mage": lambda: "intellect",
    "Priest": lambda: "faith",
    "Ranger": lambda: _rng.choice(["agility", "strength"]),
}


def _resolve_levelup(adv: dict) -> dict:
    """Apply level-up loop in-place on a dict. Returns the updated dict."""
    while adv["experience"] >= adv["level"] * XP_THRESHOLD_PER_LEVEL:
        threshold = adv["level"] * XP_THRESHOLD_PER_LEVEL
        adv["experience"] -= threshold
        adv["level"] += 1
        picker = CLASS_LEVELUP_STAT.get(adv.get("class_name", ""))
        stat = picker() if picker else "strength"
        adv[stat] = adv.get(stat, 0) + 1
    return adv


def _build_result_log(dungeon_name: str, member_names: list, success: bool) -> str:
    names = ", ".join(member_names) if member_names else "Your party"
    if success:
        return (
            f"Your party of {names} entered the {dungeon_name} at dawn. "
            f"After hours of careful work, they cleared the main chamber and returned "
            f"with what they could carry. The expedition was successful."
        )
    return (
        f"Your party pushed too deep into the {dungeon_name}. "
        f"A hidden ambush split the formation, and the group was forced to retreat. "
        f"The expedition failed, but the survivors returned with valuable experience."
    )


# ─── Lazy completion sweep ────────────────────────────────────────────────────
async def _complete_one_expedition(db, exp_id: str) -> None:
    """Atomically claim and finalize a single due expedition. Idempotent."""
    claimed = await db.expeditions.find_one_and_update(
        {"id": exp_id, "status": "in_progress"},
        {"$set": {"status": "completing"}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        return  # already completed by a concurrent caller

    dungeon = await db.dungeons.find_one({"id": claimed["dungeon_id"]}, {"_id": 0})
    if not dungeon:
        # Defensive fallback — should never happen
        await db.expeditions.update_one(
            {"id": exp_id},
            {
                "$set": {
                    "status": "failed",
                    "result_summary": "Failed",
                    "result_log": "Dungeon data unavailable.",
                    "completed_at": utc_now().isoformat(),
                }
            },
        )
        return

    members = await db.expedition_members.find(
        {"expedition_id": exp_id}, {"_id": 0}
    ).to_list(50)

    final_score = _rng.randint(1, 100)
    success = final_score <= claimed["success_chance"]
    now = utc_now()

    # Phase 7: weighted, per-dungeon loot table (Common-only on failure)
    loot_ids = await roll_loot_for_dungeon(db, dungeon, success)

    if success:
        gold_reward = dungeon["base_gold_reward"]
        xp_per_member = dungeon["base_xp_reward"]
    else:
        gold_reward = round(dungeon["base_gold_reward"] * 0.25)
        xp_per_member = round(dungeon["base_xp_reward"] * 0.4)

    # Apply rewards to guild gold
    await db.guilds.update_one(
        {"id": claimed["guild_id"]},
        {"$inc": {"gold": gold_reward}, "$set": {"updated_at": now.isoformat()}},
    )

    # Apply XP + free adventurers, with level-up loop.
    # Phase 13 — XP per member is scaled by the member's traits_snapshot
    # xp_gain percent modifiers (additive stacking, then applied once).
    for m in members:
        adv = await db.adventurers.find_one(
            {"id": m["adventurer_id"], "guild_id": claimed["guild_id"]}, {"_id": 0}
        )
        if not adv:
            continue
        traits_snap = m.get("traits_snapshot") or []
        xp_pct = sum_xp_percent(traits_snap)
        member_xp = int(round(int(xp_per_member) * (1.0 + xp_pct / 100.0)))
        adv["experience"] = int(adv.get("experience", 0)) + member_xp
        adv = _resolve_levelup(adv)
        adv["is_available"] = True
        adv["updated_at"] = now.isoformat()
        await db.adventurers.update_one(
            {"id": m["adventurer_id"]},
            {
                "$set": {
                    "experience": adv["experience"],
                    "level": adv["level"],
                    "strength": adv["strength"],
                    "agility": adv["agility"],
                    "intellect": adv["intellect"],
                    "endurance": adv["endurance"],
                    "faith": adv["faith"],
                    "is_available": True,
                    "updated_at": now.isoformat(),
                }
            },
        )

    # Apply loot to inventory (upsert quantity)
    for item_id in loot_ids:
        await db.inventory_items.update_one(
            {"guild_id": claimed["guild_id"], "item_id": item_id},
            {
                "$inc": {"quantity": 1},
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "guild_id": claimed["guild_id"],
                    "item_id": item_id,
                    "acquired_at": now.isoformat(),
                },
            },
            upsert=True,
        )

    member_names = [m["name_snapshot"] for m in members]
    result_summary = "Success" if success else "Failed"
    result_log = _build_result_log(dungeon["name"], member_names, success)

    await db.expeditions.update_one(
        {"id": exp_id},
        {
            "$set": {
                "status": "completed",
                "completed_at": now.isoformat(),
                "final_score": final_score,
                "gold_reward": gold_reward,
                "xp_reward": xp_per_member,
                "loot_item_ids": loot_ids,
                "result_summary": result_summary,
                "result_log": result_log,
                "updated_at": now.isoformat(),
            }
        },
    )

    # Phase 14 — daily quest progress (best-effort, non-critical)
    try:
        from app.quests.services import increment_quest_progress
        await increment_quest_progress(db, claimed["guild_id"], "expedition_complete")
    except Exception:
        pass


async def complete_due_expeditions(db, guild_id: str) -> int:
    """Lazy sweep: complete any in_progress expedition whose completes_at <= now."""
    now_iso = utc_now().isoformat()
    due = await db.expeditions.find(
        {
            "guild_id": guild_id,
            "status": "in_progress",
            "completes_at": {"$lte": now_iso},
        },
        {"_id": 0, "id": 1},
    ).to_list(100)
    for d in due:
        await _complete_one_expedition(db, d["id"])
    return len(due)


# ─── Replay flow ──────────────────────────────────────────────────────────────
async def _find_last_completed_expedition(db, guild_id: str) -> Optional[dict]:
    """Return the most recently completed (or failed) expedition for a guild,
    or None if none exist. Triggers a lazy completion sweep first.
    """
    await complete_due_expeditions(db, guild_id)
    return await db.expeditions.find_one(
        {
            "guild_id": guild_id,
            "status": "completed",
            "result_summary": {"$in": ["Success", "Failed"]},
        },
        {"_id": 0},
        sort=[("completed_at", -1)],
    )


async def _check_replay_eligibility(
    db, guild: dict, last_exp: dict
) -> tuple[bool, Optional[str], list[str], Optional[dict]]:
    """Return (can_replay, reason, adventurer_ids, dungeon)."""
    dungeon = await db.dungeons.find_one(
        {"id": last_exp["dungeon_id"]}, {"_id": 0}
    )
    if not dungeon or not dungeon.get("is_active", True):
        return False, "Dungeon is no longer available", [], None
    unlocked, unlock_reason = await _evaluate_dungeon_gate(db, dungeon, guild)
    if not unlocked:
        return False, f"Dungeon locked: {unlock_reason}", [], dungeon

    members = await db.expedition_members.find(
        {"expedition_id": last_exp["id"]},
        {"_id": 0, "adventurer_id": 1, "name_snapshot": 1},
    ).to_list(50)
    if not members:
        return False, "Original expedition has no member records", [], dungeon
    if len(members) != int(dungeon.get("required_team_size", len(members))):
        return False, "Team size mismatch with dungeon requirements", [], dungeon

    adv_ids = [m["adventurer_id"] for m in members]

    for m in members:
        adv = await db.adventurers.find_one(
            {"id": m["adventurer_id"], "guild_id": guild["id"]}, {"_id": 0}
        )
        if not adv:
            return (
                False,
                f"Adventurer {m['name_snapshot']} is no longer in your guild",
                adv_ids,
                dungeon,
            )
        if not adv.get("is_available", True):
            return (
                False,
                f"Adventurer {adv['name']} is currently in another expedition",
                adv_ids,
                dungeon,
            )

    return True, None, adv_ids, dungeon


# ─── Main dispatcher (start + replay share this) ──────────────────────────────
async def _dispatch_expedition(
    db,
    *,
    guild: dict,
    dungeon_id: str,
    adventurer_ids: list[str],
    is_replay: bool = False,
) -> dict:
    """Validates + snapshots + persists a fresh expedition document.

    Shared by `POST /api/expeditions` and `POST /api/expeditions/replay-last`.
    Bumps `guild.max_team_power_ever` via an atomic `$max` Mongo update.
    """
    dungeon = await db.dungeons.find_one(
        {"id": dungeon_id, "is_active": True}, {"_id": 0}
    )
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon not found")

    # Phase 7: enforce soft progression gate
    unlocked, unlock_reason = await _evaluate_dungeon_gate(db, dungeon, guild)
    if not unlocked:
        raise HTTPException(
            status_code=403, detail=f"Dungeon locked: {unlock_reason}"
        )

    # Validate team composition
    ids = adventurer_ids
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=400, detail="Duplicate adventurer in team")
    if len(ids) != dungeon["required_team_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"This dungeon requires exactly {dungeon['required_team_size']} adventurers",
        )

    members_live = []
    for aid in ids:
        adv = await db.adventurers.find_one(
            {"id": aid, "guild_id": guild["id"]}, {"_id": 0}
        )
        if not adv:
            raise HTTPException(
                status_code=404,
                detail=f"Adventurer {aid} not found in your guild",
            )
        if not adv.get("is_available", True):
            raise HTTPException(
                status_code=400,
                detail=f"Adventurer {adv['name']} is not available",
            )
        members_live.append(adv)

    # Phase 6: load equipment for each member; snapshot is frozen at departure.
    # Phase 13: also snapshot the active traits so completion can resolve
    # xp_gain modifiers deterministically even if the trait pool changes.
    members_for_power: list[dict] = []
    equipment_by_adv: dict[str, dict] = {}
    traits_by_adv: dict[str, list] = {}
    for adv in members_live:
        slots, eq_power, raw = await _load_equipment_for_adventurer(db, adv["id"])
        snapshot = [_item_summary_for_snapshot(r["row"], r["item"]) for r in raw]
        # Phase 13 — use effective (trait-modified) power as base
        base = _adventurer_effective_power(adv)
        traits_snapshot = list(adv.get("traits") or [])
        traits_by_adv[adv["id"]] = traits_snapshot
        equipment_by_adv[adv["id"]] = {
            "equipment_snapshot": snapshot,
            "equipment_power_snapshot": eq_power,
            "total_power_snapshot": base + eq_power,
        }
        members_for_power.append(
            {
                **adv,
                "total_power_snapshot": base + eq_power,
                "equipment_power_snapshot": eq_power,
            }
        )

    team_power = compute_team_power(members_for_power)
    success_chance = compute_success_chance(team_power, dungeon["recommended_power"])

    # Phase 7: equipment delta (frozen at start)
    delta = _build_equipment_delta(
        members_for_power, dungeon, team_power, success_chance
    )

    now = utc_now()
    completes_at = now + timedelta(seconds=dungeon["base_duration_seconds"])
    exp_id = str(uuid.uuid4())
    exp_doc = {
        "id": exp_id,
        "guild_id": guild["id"],
        "dungeon_id": dungeon["id"],
        "dungeon_name": dungeon["name"],
        "status": "in_progress",
        "started_at": now.isoformat(),
        "completes_at": completes_at.isoformat(),
        "completed_at": None,
        "team_power": team_power,
        "success_chance": success_chance,
        # Phase 7 delta snapshot
        "base_team_power": delta["base_team_power"],
        "equipment_power_bonus": delta["equipment_power_bonus"],
        "final_team_power": delta["final_team_power"],
        "success_chance_without_equipment": delta["success_chance_without_equipment"],
        "success_chance_with_equipment": delta["success_chance_with_equipment"],
        "equipment_delta_text": delta["equipment_delta_text"],
        "final_score": None,
        "result_summary": None,
        "result_log": None,
        "gold_reward": 0,
        "xp_reward": 0,
        "loot_item_ids": [],
        # Phase 8: mark replay expeditions so the FE can label them differently.
        "is_replay": bool(is_replay),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.expeditions.insert_one(exp_doc)

    members_docs = []
    for adv in members_live:
        eq = equipment_by_adv.get(
            adv["id"],
            {
                "equipment_snapshot": [],
                "equipment_power_snapshot": 0,
                "total_power_snapshot": _adventurer_effective_power(adv),
            },
        )
        m = {
            "id": str(uuid.uuid4()),
            "expedition_id": exp_id,
            "adventurer_id": adv["id"],
            "name_snapshot": adv["name"],
            "class_name_snapshot": adv.get("class_name", ""),
            "role_snapshot": adv.get("class_role", ""),
            "level_snapshot": adv.get("level", 1),
            "strength_snapshot": adv["strength"],
            "agility_snapshot": adv["agility"],
            "intellect_snapshot": adv["intellect"],
            "endurance_snapshot": adv["endurance"],
            "faith_snapshot": adv["faith"],
            "equipment_snapshot": eq["equipment_snapshot"],
            "equipment_power_snapshot": int(eq["equipment_power_snapshot"]),
            "total_power_snapshot": int(eq["total_power_snapshot"]),
            # Phase 13 — trait snapshot for deterministic resolution
            "traits_snapshot": traits_by_adv.get(adv["id"], []),
        }
        members_docs.append(m)
    if members_docs:
        await db.expedition_members.insert_many([dict(m) for m in members_docs])

    # Lock the adventurers
    await db.adventurers.update_many(
        {"id": {"$in": ids}, "guild_id": guild["id"]},
        {"$set": {"is_available": False, "updated_at": now.isoformat()}},
    )

    # Phase 8: sticky peak team_power. `$max` is atomic and idempotent.
    await db.guilds.update_one(
        {"id": guild["id"]},
        {
            "$max": {"max_team_power_ever": int(delta["final_team_power"])},
            "$set": {"updated_at": now.isoformat()},
        },
    )

    return {
        "expedition": expedition_public(exp_doc),
        "members": [member_public(m) for m in members_docs],
    }


# ─── Thin route-facing services ───────────────────────────────────────────────
async def start_expedition(db, guild: dict, payload) -> dict:
    return await _dispatch_expedition(
        db,
        guild=guild,
        dungeon_id=payload.dungeon_id,
        adventurer_ids=payload.adventurer_ids,
        is_replay=False,
    )


async def list_expeditions(db, guild: dict) -> dict:
    await complete_due_expeditions(db, guild["id"])
    rows = (
        await db.expeditions.find({"guild_id": guild["id"]}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(200)
    )
    return {"expeditions": [expedition_public(e) for e in rows]}


async def get_last_completed(db, guild: dict) -> dict:
    last_exp = await _find_last_completed_expedition(db, guild["id"])
    if not last_exp:
        raise HTTPException(status_code=404, detail="No completed expedition yet")
    can_replay, reason, adv_ids, _dungeon = await _check_replay_eligibility(
        db, guild, last_exp
    )
    return {
        "expedition": expedition_public(last_exp),
        "adventurer_ids": adv_ids,
        "can_replay": can_replay,
        "cannot_replay_reason": reason,
    }


async def replay_last(db, guild: dict) -> dict:
    last_exp = await _find_last_completed_expedition(db, guild["id"])
    if not last_exp:
        raise HTTPException(status_code=404, detail="No completed expedition yet")
    can_replay, reason, adv_ids, _dungeon = await _check_replay_eligibility(
        db, guild, last_exp
    )
    if not can_replay:
        # Locked dungeon → 403; any other replay blocker → 400.
        status = 403 if reason and reason.startswith("Dungeon locked") else 400
        raise HTTPException(status_code=status, detail=reason or "Cannot replay")
    return await _dispatch_expedition(
        db,
        guild=guild,
        dungeon_id=last_exp["dungeon_id"],
        adventurer_ids=adv_ids,
        is_replay=True,
    )


async def get_expedition(db, expedition_id: str, guild: dict) -> dict:
    await complete_due_expeditions(db, guild["id"])
    exp = await db.expeditions.find_one(
        {"id": expedition_id, "guild_id": guild["id"]}, {"_id": 0}
    )
    if not exp:
        # Don't leak 403 vs 404
        raise HTTPException(status_code=404, detail="Expedition not found")

    members = await db.expedition_members.find(
        {"expedition_id": expedition_id}, {"_id": 0}
    ).to_list(50)

    # Expand loot items, preserving order with possible duplicates
    loot_ids = exp.get("loot_item_ids", [])
    loot_items = []
    if loot_ids:
        items = await db.items.find(
            {"id": {"$in": loot_ids}}, {"_id": 0}
        ).to_list(50)
        item_by_id = {it["id"]: it for it in items}
        for lid in loot_ids:
            if lid in item_by_id:
                loot_items.append(item_public(item_by_id[lid]))

    # Phase 14.5 (ROUND 2 Fase 3) — explainability layer.
    # Pure builder, NO DB writes, NO new RNG roll. Legacy/in-progress
    # expeditions get {report_summary: None, report_steps: None} so the
    # UI can render its graceful fallback.
    from app.expeditions.report_builder import build_expedition_report
    dungeon = await db.dungeons.find_one(
        {"id": exp["dungeon_id"]}, {"_id": 0}
    )
    report = build_expedition_report(exp, members, dungeon, loot_items)

    return {
        "expedition": expedition_public(exp),
        "members": [member_public(m) for m in members],
        "loot_items": loot_items,
        "report_summary": report["report_summary"],
        "report_steps": report["report_steps"],
    }


__all__ = [
    # serializers
    "expedition_public",
    "member_public",
    # core orchestration
    "_dispatch_expedition",
    "_evaluate_dungeon_gate",
    "_complete_one_expedition",
    "complete_due_expeditions",
    "_find_last_completed_expedition",
    "_check_replay_eligibility",
    "_resolve_levelup",
    "_build_result_log",
    "CLASS_LEVELUP_STAT",
    # route-facing
    "start_expedition",
    "list_expeditions",
    "get_last_completed",
    "replay_last",
    "get_expedition",
]
