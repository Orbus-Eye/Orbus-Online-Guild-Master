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
import re
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
from app.expeditions.material_drop_tables import roll_materials_for_dungeon
from app.expeditions.threats import compute_threat_resolution
from app.expeditions.xp_modifier import compute_xp_multiplier
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
        "equipment_delta_text": _translate_legacy_equipment_delta(
            e.get("equipment_delta_text")
        ),
        "final_score": e.get("final_score"),
        "result_summary": e.get("result_summary"),
        "result_log": _translate_legacy_result_log(e.get("result_log")),
        "gold_reward": e.get("gold_reward", 0),
        "xp_reward": e.get("xp_reward", 0),
        "loot_item_ids": e.get("loot_item_ids", []),
        # ROUND 15 FASE 2 — separate material drops + per-member XP debuff.
        "materials_found": e.get("materials_found", []),
        "xp_debuff_reports": e.get("xp_debuff_reports", []),
        # ROUND 6B.2c — expose adventurer_ids for "Save as squad" deep-link.
        "adventurer_ids": list(e.get("adventurer_ids", [])),
        # Phase 8: marks the run as a "Replay Last Run" dispatch (UI label).
        "is_replay": bool(e.get("is_replay", False)),
        # ROUND 16.0 Phase 4 — Threat resolution (Void/Undead only; None elsewhere).
        "threat_resolution": e.get("threat_resolution"),
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
    """ROUND 17.1b P0.1 — Narrativa IT del report spedizione."""
    names = ", ".join(member_names) if member_names else "Il tuo gruppo"
    if success:
        return (
            f"Il tuo gruppo composto da {names} è entrato in {dungeon_name} all'alba. "
            f"Dopo ore di lavoro attento, ha ripulito la camera principale ed è tornato "
            f"con tutto ciò che è riuscito a trasportare. La spedizione è stata un successo."
        )
    return (
        f"Il tuo gruppo si è spinto troppo in profondità in {dungeon_name}. "
        f"Un'imboscata nascosta ha diviso la formazione e il gruppo è stato costretto a ritirarsi. "
        f"La spedizione è fallita, ma i superstiti sono tornati con preziosa esperienza."
    )


# ROUND 17.1b P0.1 — Mappa di traduzione per report LEGACY (docs pre-R17.1b in DB)
# con stringhe EN già persistite. Applicato in `expedition_public` a runtime,
# senza migration DB. Zero regression per docs nuovi (già IT).
_LEGACY_LOG_EN_IT_MAP = (
    (
        re.compile(
            r"^Your party of (.+?) entered the (.+?) at dawn\. "
            r"After hours of careful work, they cleared the main chamber and returned "
            r"with what they could carry\. The expedition was successful\.$"
        ),
        lambda m: (
            f"Il tuo gruppo composto da {m.group(1)} è entrato in {m.group(2)} all'alba. "
            f"Dopo ore di lavoro attento, ha ripulito la camera principale ed è tornato "
            f"con tutto ciò che è riuscito a trasportare. La spedizione è stata un successo."
        ),
    ),
    (
        re.compile(
            r"^Your party pushed too deep into the (.+?)\. "
            r"A hidden ambush split the formation, and the group was forced to retreat\. "
            r"The expedition failed, but the survivors returned with valuable experience\.$"
        ),
        lambda m: (
            f"Il tuo gruppo si è spinto troppo in profondità in {m.group(1)}. "
            f"Un'imboscata nascosta ha diviso la formazione e il gruppo è stato costretto a ritirarsi. "
            f"La spedizione è fallita, ma i superstiti sono tornati con preziosa esperienza."
        ),
    ),
)


def _translate_legacy_result_log(text):
    """Return IT translation for legacy EN result_log; passthrough otherwise."""
    if not text:
        return text
    stripped = text.strip()
    for pattern, translator in _LEGACY_LOG_EN_IT_MAP:
        m = pattern.match(stripped)
        if m:
            return translator(m)
    if stripped == "Dungeon data unavailable.":
        return "Dati del dungeon non disponibili."
    return text


# ROUND 17.1b P0.1 — Legacy EN → IT map per `equipment_delta_text`.
_LEGACY_EQUIP_DELTA_EN_IT_MAP = (
    (
        re.compile(r"^No equipment was used on this run\.$"),
        lambda m: "Nessun equipaggiamento è stato consumato in questa spedizione.",
    ),
    (
        re.compile(
            r"^Equipment contributed \+(\d+) team power\. "
            r"Success chance was already at maximum \((\d+)%\)\.$"
        ),
        lambda m: (
            f"L'equipaggiamento ha aggiunto +{m.group(1)} al potere della squadra. "
            f"La probabilità di successo era già al massimo ({m.group(2)}%)."
        ),
    ),
    (
        re.compile(
            r"^Equipment contributed \+(\d+) team power, "
            r"improving success chance from (\d+)% to (\d+)%\.$"
        ),
        lambda m: (
            f"L'equipaggiamento ha aggiunto +{m.group(1)} al potere della squadra, "
            f"aumentando la probabilità di successo dal {m.group(2)}% "
            f"al {m.group(3)}%."
        ),
    ),
)


def _translate_legacy_equipment_delta(text):
    """Return IT translation for legacy EN equipment_delta_text; passthrough otherwise."""
    if not text:
        return text
    stripped = text.strip()
    for pattern, translator in _LEGACY_EQUIP_DELTA_EN_IT_MAP:
        m = pattern.match(stripped)
        if m:
            return translator(m)
    return text


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
                    "result_log": "Dati del dungeon non disponibili.",
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
    # ROUND 15 FASE 2 — material drop, INDEPENDENT roll from items.
    materials_found = await roll_materials_for_dungeon(db, dungeon, success)

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
    # ROUND 15 FASE 2 — apply class-primary-stat XP multiplier (debuff
    # when primary stat is below class threshold for current level).
    # Materials granted on the spot, idempotency follows the same
    # `status: in_progress → completing` claim used for gold/xp/loot.
    xp_debuff_reports: list[dict] = []
    # ROUND 16.3 Phase 5B — apply Arfus leader_experience bonus (0 if none).
    from app.arfus_forge import bonus_pct as _arfus_bonus
    _leader_xp_bonus = await _arfus_bonus(claimed["guild_id"],
                                          "leader_experience")
    # Pre-load class docs by name for the members in this expedition.
    class_names = list({(m.get("class_name_snapshot") or "").strip() for m in members})
    class_docs_by_name: dict[str, dict] = {}
    if class_names:
        async for c in db.adventurer_classes.find(
            {"name": {"$in": class_names}}, {"_id": 0},
        ):
            class_docs_by_name[c.get("name") or ""] = c
    for m in members:
        adv = await db.adventurers.find_one(
            {"id": m["adventurer_id"], "guild_id": claimed["guild_id"]}, {"_id": 0}
        )
        if not adv:
            continue
        traits_snap = m.get("traits_snapshot") or []
        xp_pct = sum_xp_percent(traits_snap)
        base_xp_with_traits = int(round(int(xp_per_member) * (1.0 + xp_pct / 100.0)))
        # ROUND 16.3 Phase 5B — apply leader_experience multiplier (0 if none).
        base_xp_with_traits = int(round(
            base_xp_with_traits * (1.0 + _leader_xp_bonus / 100.0)))
        # ROUND 15 FASE 2 — primary-stat policy multiplier.
        cls_doc = class_docs_by_name.get(m.get("class_name_snapshot") or "")
        xp_info = compute_xp_multiplier(adv, cls_doc)
        final_member_xp = int(round(base_xp_with_traits * float(xp_info["multiplier"])))
        xp_debuff_reports.append({
            "adventurer_id": m["adventurer_id"],
            "name_snapshot": m.get("name_snapshot"),
            "base_xp": int(base_xp_with_traits),
            "multiplier": float(xp_info["multiplier"]),
            "final_xp": int(final_member_xp),
            "reason_code": xp_info.get("reason_code"),
            "primary_stat_slug": xp_info.get("primary_stat_slug"),
            "primary_stat_name_it": xp_info.get("primary_stat_name_it"),
            "threshold": int(xp_info.get("threshold") or 0),
            "actual": int(xp_info.get("actual") or 0),
            "deficit_pct": float(xp_info.get("deficit_pct") or 0.0),
        })
        adv["experience"] = int(adv.get("experience", 0)) + final_member_xp
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
                    "instance_id": str(uuid.uuid4()),  # ROUND 4 forge field
                    "guild_id": claimed["guild_id"],
                    "item_id": item_id,
                    "acquired_at": now.isoformat(),
                    "source": "dungeon",
                    "bind_state": "unbound",
                    # Phase 19.2 fix — ensure ROUND 4 default fields are set
                    # on first insert so the idempotency test stays green.
                    "is_bound": False,
                    "disenchanted_at": None,
                    "refinement_level": 0,
                    "enchants": [],
                    "affixes": [],
                    "reroll_count": 0,
                },
            },
            upsert=True,
        )

    # ROUND 15 FASE 2 — credit materials into inventory_items (separate
    # from item drops). Each row uses the material slug to lookup the
    # `items` template id. Materials reuse the same inventory_items
    # collection so the rest of the stack (FE, transmute, audit) works
    # without changes.
    if materials_found:
        mat_slugs = list({m["slug"] for m in materials_found})
        mat_templates = {
            mt["slug"]: mt
            async for mt in db.items.find(
                {"slug": {"$in": mat_slugs}, "item_type": "material"},
                {"_id": 0},
            )
        }
        for drop in materials_found:
            tpl = mat_templates.get(drop["slug"])
            if not tpl:
                continue
            await db.inventory_items.update_one(
                {"guild_id": claimed["guild_id"], "item_id": tpl["id"]},
                {
                    "$inc": {"quantity": int(drop["qty"])},
                    "$setOnInsert": {
                        "id": str(uuid.uuid4()),
                        "instance_id": str(uuid.uuid4()),
                        "guild_id": claimed["guild_id"],
                        "item_id": tpl["id"],
                        "acquired_at": now.isoformat(),
                        "source": "dungeon_material",
                        "bind_state": "unbound",
                        "is_bound": False,
                        "disenchanted_at": None,
                        "refinement_level": 0,
                        "enchants": [],
                        "affixes": [],
                        "reroll_count": 0,
                    },
                },
                upsert=True,
            )

    # Phase 14.7 — persistent audit log (best-effort, non-blocking).
    try:
        from app.audit.log import write_audit
        if gold_reward:
            await write_audit(
                db, event_type="gold_credited",
                actor_guild_id=claimed["guild_id"], gold_delta=gold_reward,
                source="dungeon", related_entity_id=exp_id,
                metadata={"dungeon_slug": dungeon.get("slug")},
            )
        if loot_ids:
            items_for_audit = await db.items.find(
                {"id": {"$in": list(set(loot_ids))}}, {"_id": 0, "id": 1, "slug": 1}
            ).to_list(50)
            slug_by_id = {i["id"]: i.get("slug") for i in items_for_audit}
            for item_id in loot_ids:
                await write_audit(
                    db, event_type="loot_awarded",
                    actor_guild_id=claimed["guild_id"],
                    item_slug=slug_by_id.get(item_id),
                    item_template_id=item_id,
                    quantity=1,
                    source="dungeon", related_entity_id=exp_id,
                    metadata={"dungeon_slug": dungeon.get("slug")},
                )
    except Exception as _exc:  # noqa: BLE001
        pass

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
                # ROUND 15 FASE 2 — material drops + per-member XP debuff report.
                "materials_found": materials_found,
                "xp_debuff_reports": xp_debuff_reports,
                "result_summary": result_summary,
                "result_log": result_log,
                "updated_at": now.isoformat(),
            }
        },
    )
    # ROUND 15 Phase 3 — achievement trigger only on success
    # (failed expeditions don't credit `dungeon_completed`).
    if success:
        try:
            from app.achievements.engine import evaluate_achievements
            await evaluate_achievements(
                claimed["guild_id"], "dungeon_completed",
                {"dungeon_slug": dungeon.get("slug"),
                 "expedition_id": exp_id},
                db=db,
            )
        except Exception:
            pass

    # ROUND 17.1 P0.5 — Fallback reward per il primo fallimento sullo
    # starter dungeon (una volta sola per gilda). Vincoli PM:
    #   - solo dungeon `is_starter=True` (attualmente: `training-yard`)
    #   - solo se `guild.first_expedition_fallback_granted != True`
    #   - reward piccolo: +5 gold + +5 XP Prestigio, NO loot, NO XP adventurer
    if (not success) and (dungeon.get("is_starter") is True):
        try:
            _guild_doc = await db.guilds.find_one(
                {"id": claimed["guild_id"]},
                {"first_expedition_fallback_granted": 1, "gold": 1},
            )
            already_granted = bool(
                (_guild_doc or {}).get("first_expedition_fallback_granted")
            )
            if not already_granted:
                # 1. Guard flag + gold (transactional-ish: setta il flag
                # DENTRO l'update per prevenire double-grant su race).
                res = await db.guilds.update_one(
                    {
                        "id": claimed["guild_id"],
                        "first_expedition_fallback_granted": {"$ne": True},
                    },
                    {
                        "$inc": {"gold": 5},
                        "$set": {
                            "first_expedition_fallback_granted": True,
                            "first_expedition_fallback_granted_at": now.isoformat(),
                            "updated_at": now.isoformat(),
                        },
                    },
                )
                if res.modified_count == 1:
                    # 2. +5 XP Prestigio via hook standard (rispetta
                    # cap giornalieri e audit event `guild_xp_gained`).
                    try:
                        from app.achievements.engine import add_guild_xp
                        await add_guild_xp(
                            db,
                            guild_id=claimed["guild_id"],
                            xp_amount=5,
                            source="starter_fallback_grant",
                            source_id=exp_id,
                        )
                    except Exception:
                        pass
                    # 3. Audit dedicato del grant.
                    try:
                        from app.audit.log import write_audit
                        await write_audit(
                            db,
                            event_type="STARTER_FALLBACK_REWARD_GRANTED",
                            actor_guild_id=claimed["guild_id"],
                            source="expeditions.complete",
                            related_entity_id=exp_id,
                            metadata={
                                "dungeon_slug": dungeon.get("slug"),
                                "gold_bonus": 5,
                                "prestige_xp_bonus": 5,
                            },
                        )
                    except Exception:
                        pass
        except Exception:  # noqa: BLE001
            pass

    # ROUND 17.1 P0.3+P0.4 — funnel event FIRST_EXPEDITION_COMPLETED.
    # Emesso qui nel completion hook (non nel report GET), così vale
    # anche se il player non apre mai il report. Idempotente per guild.
    try:
        from app.audit.first_events import emit_first_event
        await emit_first_event(
            db, event_type="FIRST_EXPEDITION_COMPLETED",
            guild_id=claimed["guild_id"],
            extra={
                "expedition_id": exp_id,
                "dungeon_slug": dungeon.get("slug"),
                "success": success,
            },
        )
    except Exception:  # noqa: BLE001
        pass

    # Phase 14 — daily quest progress (best-effort, non-critical)
    try:
        from app.quests.services import increment_quest_progress
        await increment_quest_progress(db, claimed["guild_id"], "expedition_complete")
    except Exception:
        pass
    # Phase 14.1 — weekly quest progress (best-effort)
    try:
        from app.quests.services import increment_weekly_progress
        await increment_weekly_progress(
            db, claimed["guild_id"], "expeditions_completed", 1
        )
        if loot_ids:
            await increment_weekly_progress(
                db, claimed["guild_id"], "expedition_loot_items", len(loot_ids)
            )
    except Exception:
        pass
    # ROUND 6D — contract progress (best-effort, non-critical)
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(
            db, claimed["guild_id"], "expeditions_completed", 1
        )
    except Exception:
        pass

    # ROUND 16.5.3 P1 — Guild XP drip (Prestigio di Gilda). Best-effort,
    # idempotente su expedition_id, cap 8/giorno. Success +15, fail +5.
    try:
        from app.achievements.xp_hooks import on_expedition_completed
        await on_expedition_completed(
            db, claimed["guild_id"],
            expedition_id=exp_id, success=success,
        )
    except Exception:
        pass

    # ROUND 13b — seasonal `dungeon_clears` counter (best-effort, idempotent).
    # The CAS filter on expeditions.id + flag ensures a replay (lazy sweep
    # re-running on a stuck row) cannot double-count.
    if success:
        try:
            from app.seasons.season_stats import increment_seasonal_stat
            await increment_seasonal_stat(
                db,
                guild_id=claimed["guild_id"],
                field="dungeon_clears",
                delta=1,
                source="expedition_complete",
                source_collection="expeditions",
                source_id=exp_id,
                flag_key="season_stat_recorded",
            )
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
    retired_ids: list[str] = []
    for aid in ids:
        adv = await db.adventurers.find_one(
            {"id": aid, "guild_id": guild["id"]}, {"_id": 0}
        )
        if not adv:
            raise HTTPException(
                status_code=404,
                detail=f"Adventurer {aid} not found in your guild",
            )
        if adv.get("is_retired") is True:
            retired_ids.append(aid)
            continue
        if not adv.get("is_available", True):
            raise HTTPException(
                status_code=400,
                detail=f"Adventurer {adv['name']} is not available",
            )
        members_live.append(adv)
    # ROUND 6B.3 Wave 1.5 — explicit retired check (423 with structured detail)
    if retired_ids:
        raise HTTPException(
            status_code=423,
            detail={
                "code": "adventurers.retired_in_set",
                "source": "expedition.dispatch",
                "retired_adventurer_ids": retired_ids,
                "count": len(retired_ids),
                "user_message": (
                    f"La spedizione include {len(retired_ids)} avventurier"
                    f"{'i' if len(retired_ids) > 1 else 'o'} congedat"
                    f"{'i' if len(retired_ids) > 1 else 'o'}. Rimuovili dalla selezione."
                ),
            },
        )

    # ROUND 18.1.1 Hotfix 2 — Guard "recruit_unassigned" / non-playable class.
    # Safety-only backend guard: rifiuta gli avventurieri con class_slug
    # tecnico (`recruit_unassigned`) o classi non canoniche/non giocabili.
    # NON è il class-bound HARD (arriva in R18.4) — è protezione minima
    # contro dispatch diretto via API di adventurers orphan-migrated.
    # Feature flag independent (safety layer). User-message in italiano.
    _playable_slugs: set[str] = set()
    async for _c in db.adventurer_classes.find(
        {"is_playable": {"$ne": False}}, {"_id": 0, "slug": 1}
    ):
        _playable_slugs.add(_c["slug"])
    _unassigned_advs: list[dict] = []
    for _adv in members_live:
        _cs = _adv.get("class_slug")
        if _cs == "recruit_unassigned" or not _cs or _cs not in _playable_slugs:
            _unassigned_advs.append({
                "adventurer_id": _adv.get("id"),
                "name": _adv.get("name"),
                "class_slug": _cs,
            })
    if _unassigned_advs:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "adventurers.recruit_unassigned_in_set",
                "source": "expedition.dispatch",
                "unassigned_adventurers": _unassigned_advs,
                "count": len(_unassigned_advs),
                "user_message": (
                    "Questo avventuriero non ha ancora una classe assegnata. "
                    "Riassegnalo prima di mandarlo in missione."
                ),
            },
        )

    # ROUND 11.3 TASK A — Adventurer-level gate.
    # MUST run AFTER the live/retired filter (so we only complain about
    # advs that would actually enter the dungeon) and BEFORE the heavier
    # equipment snapshot. PWR alone does NOT bypass.
    from app.expeditions.level_gate import (
        enforce_min_adventurer_level,
        legacy_min_level_for_dungeon,
    )
    enforce_min_adventurer_level(
        members_live,
        legacy_min_level_for_dungeon(dungeon),
        source="expedition.dispatch",
        dungeon_slug=dungeon.get("slug"),
    )

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

    # ROUND 16.0 Phase 4 — Threat & counter resolution (Void/Undead schema).
    # Additive: dungeons without `threat_tags` keep behaviour unchanged.
    threat_resolution = await compute_threat_resolution(
        db, team_members=members_for_power, dungeon=dungeon,
    )
    if threat_resolution.get("applies"):
        bonus = int(threat_resolution.get("success_bonus_pct", 0))
        if bonus:
            success_chance = min(success_chance + bonus, 95)

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
        # ROUND 6B.2c — persist team ids for "Save as squad" deep-link from report.
        "adventurer_ids": list(adventurer_ids),
        # Phase 8: mark replay expeditions so the FE can label them differently.
        "is_replay": bool(is_replay),
        # ROUND 16.0 Phase 4 — Threat resolution (only when dungeon has threat_tags).
        "threat_resolution": threat_resolution if threat_resolution.get("applies") else None,
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

    # ROUND 6B.2c — historical fallback: if `adventurer_ids` was not persisted
    # on the expedition doc (pre-6B.2c records), reconstruct it from the
    # expedition_members snapshot so the "Save as squad" CTA works retroactively.
    if not exp.get("adventurer_ids") and members:
        exp["adventurer_ids"] = [m["adventurer_id"] for m in members if m.get("adventurer_id")]

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

    # ROUND 17.1 P0.5 (UI feedback) — Derivazione READ-ONLY del flag
    # fallback_reward per questa specifica spedizione. Il grant vero
    # è già stato applicato in `_complete_one_expedition` (idempotente).
    # Qui non scriviamo mai su DB: leggiamo `guild.first_expedition_fallback_granted_at`
    # e lo confrontiamo con `exp.completed_at`. Se coincidono → questa
    # spedizione è quella che ha triggerato il grant.
    fallback_reward: dict | None = None
    if (
        exp.get("result_summary") == "Failed"
        and dungeon is not None
        and dungeon.get("is_starter") is True
    ):
        guild_doc = await db.guilds.find_one(
            {"id": guild["id"]},
            {
                "first_expedition_fallback_granted": 1,
                "first_expedition_fallback_granted_at": 1,
            },
        )
        if guild_doc and guild_doc.get("first_expedition_fallback_granted"):
            granted_at = guild_doc.get("first_expedition_fallback_granted_at")
            completed_at = exp.get("completed_at")
            if granted_at and completed_at and granted_at == completed_at:
                fallback_reward = {
                    "granted": True,
                    "gold": 5,
                    "prestige_xp": 5,
                }

    # ROUND 17.1b P0.2 + P1.1 — Derivazione READ-ONLY di:
    #   - guild_prestige_delta: XP Prestigio guadagnata IN QUESTA spedizione
    #     (aggregata da `audit_log.guild_xp_gained` con source_id=exp.id)
    #     + snapshot corrente del livello gilda + progresso verso il prossimo.
    #   - milestones: flag one-shot per triggerare toast client-side.
    # Zero scritture DB.
    guild_prestige_delta: dict | None = None
    milestones = {
        "is_first_expedition_completed": False,
        "is_first_prestige_gained": False,
    }
    if exp.get("status") in ("completed",) or exp.get("result_summary") in ("Success", "Failed"):
        # Aggregate XP earned in this expedition (regular +15/+5 + starter fallback +5).
        xp_docs = await db.audit_log.find(
            {
                "event_type": "guild_xp_gained",
                "actor_guild_id": guild["id"],
                "related_entity_id": expedition_id,
            },
            {"_id": 0, "metadata.xp_amount": 1},
        ).to_list(20)
        xp_gained_total = 0
        for doc in xp_docs:
            meta = doc.get("metadata") or {}
            xp_gained_total += int(meta.get("xp_amount", 0) or 0)

        # Fetch current guild XP + level.
        guild_doc_full = await db.guilds.find_one(
            {"id": guild["id"]},
            {"_id": 0, "guild_xp": 1, "guild_level": 1, "last_guild_level_up_at": 1},
        ) or {}
        cur_xp = int(guild_doc_full.get("guild_xp", 0) or 0)
        cur_level = int(guild_doc_full.get("guild_level", 1) or 1)

        # Level curve import (already used elsewhere in the codebase).
        try:
            from app.achievements.levels import xp_required_for_level, current_level_for_xp
            level_by_xp = current_level_for_xp(cur_xp)
            next_level = level_by_xp + 1
            next_level_at = xp_required_for_level(next_level)
            level_start = xp_required_for_level(level_by_xp)
            xp_into_level = max(0, cur_xp - level_start)
            xp_for_next_level = max(0, next_level_at - cur_xp)
        except Exception:
            level_by_xp = cur_level
            next_level = cur_level + 1
            next_level_at = cur_xp
            xp_into_level = 0
            xp_for_next_level = 0

        # Level up: did last_guild_level_up_at happen at (or just after) this
        # expedition's completion timestamp?
        completed_at = exp.get("completed_at")
        last_lvlup = guild_doc_full.get("last_guild_level_up_at")
        level_up_this_expedition = bool(
            completed_at and last_lvlup and last_lvlup >= completed_at
            and last_lvlup <= (completed_at[:19] + completed_at[-6:] if len(completed_at) >= 25 else completed_at)
        ) if False else (
            # Simpler heuristic: if lvlup timestamp equals completed_at exactly.
            bool(completed_at and last_lvlup and last_lvlup == completed_at)
        )

        guild_prestige_delta = {
            "xp_gained": xp_gained_total,
            "guild_level": cur_level,
            "guild_xp": cur_xp,
            "xp_into_level": xp_into_level,
            "next_level": next_level,
            "next_level_at": next_level_at,
            "xp_for_next_level": xp_for_next_level,
            "level_up_this_expedition": level_up_this_expedition,
        }

        # ROUND 17.2 P1 — Prestigio next reward tooltip.
        # ROUND 17.3 Step 2 D — Esteso a Lv2 Missioni Risorse (nuovo primo
        # step post-onboarding). Sorgente unica: costanti backend
        # (`MIN_GUILD_LEVEL`) dei moduli feature-gated. NO hardcode duplicato.
        try:
            from app.resources import MIN_GUILD_LEVEL as _RES_LVL
        except Exception:
            _RES_LVL = 2
        try:
            from app.legendary_forge import MIN_GUILD_LEVEL as _LF_LVL
        except Exception:
            _LF_LVL = 5
        try:
            from app.arfus_forge import MIN_GUILD_LEVEL as _AF_LVL
        except Exception:
            _AF_LVL = 6
        try:
            from app.guild_specialization import MIN_GUILD_LEVEL as _GS_LVL
        except Exception:
            _GS_LVL = 8
        _unlocks = [
            (_RES_LVL, "Missioni Risorse"),
            (_LF_LVL, "Forgia Leggendaria"),
            (_AF_LVL, "Forgia di Arfus"),
            (_GS_LVL, "Specializzazione della Gilda"),
        ]
        next_unlock = None
        for lvl, name in sorted(_unlocks, key=lambda t: t[0]):
            if cur_level < lvl:
                next_unlock = {"level": lvl, "feature_it": name}
                break
        guild_prestige_delta["next_unlock"] = next_unlock

        # Milestones — derive from audit_log with strict guard (this exp is
        # the SAME one that triggered the FIRST_* event).
        first_complete_count = await db.audit_log.count_documents({
            "event_type": "FIRST_EXPEDITION_COMPLETED",
            "actor_guild_id": guild["id"],
        })
        first_complete_doc = await db.audit_log.find_one({
            "event_type": "FIRST_EXPEDITION_COMPLETED",
            "actor_guild_id": guild["id"],
        }, {"_id": 0, "related_entity_id": 1, "metadata.expedition_id": 1})
        if first_complete_count == 1 and first_complete_doc:
            same_exp = (
                first_complete_doc.get("related_entity_id") == expedition_id
                or (first_complete_doc.get("metadata") or {}).get("expedition_id") == expedition_id
            )
            milestones["is_first_expedition_completed"] = bool(same_exp)

        first_prestige_count = await db.audit_log.count_documents({
            "event_type": "FIRST_PRESTIGE_GAINED",
            "actor_guild_id": guild["id"],
        })
        first_prestige_doc = await db.audit_log.find_one({
            "event_type": "FIRST_PRESTIGE_GAINED",
            "actor_guild_id": guild["id"],
        }, {"_id": 0, "related_entity_id": 1, "metadata.expedition_id": 1, "created_at": 1})
        if first_prestige_count == 1 and first_prestige_doc:
            # first-prestige is tied to a `guild_xp_gained` event whose source_id
            # matches this expedition id (audit's related_entity_id or metadata).
            related = first_prestige_doc.get("related_entity_id")
            meta_exp = (first_prestige_doc.get("metadata") or {}).get("expedition_id")
            milestones["is_first_prestige_gained"] = bool(
                related == expedition_id or meta_exp == expedition_id
            )

    return {
        "expedition": expedition_public(exp),
        "members": [member_public(m) for m in members],
        "loot_items": loot_items,
        "report_summary": report["report_summary"],
        "report_steps": report["report_steps"],
        "fallback_reward": fallback_reward,
        "guild_prestige_delta": guild_prestige_delta,
        "milestones": milestones,
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
