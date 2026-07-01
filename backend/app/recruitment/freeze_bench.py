"""ROUND 11.3 TASK C — Recruit Freeze Bench.

Lets a player "park" up to 2 desirable recruitment candidates that survive
refreshes. Frozen candidates do NOT count toward the roster cap (they are
not adventurers yet — they are immutable snapshots living on `guilds`).

Storage shape on `guilds`:

    recruit_freeze_bench = {
        "frozen_candidates": [<snapshot>, ...],   # max 2 entries
        "max_slots": 2,
    }

Where `<snapshot>` is a frozen, server-authoritative copy of all the
generated stats / traits / class / rarity / cost needed to materialise the
adventurer on `recruit_frozen_candidate`. Adding a `frozen_id` (separate
from the original `candidate_id` to avoid collisions with future pool
re-rolls) lets the FE address each slot deterministically.

Why subdoc on `guilds` instead of a dedicated collection:
  * Hard ceiling of 2 entries → no scaling concern.
  * Atomic CAS via `$push` with `$position`/`$slice` and `$pull` by
    `frozen_id`. Single document → no two-collection 2-phase write.
  * Survives `find_one_and_replace` refresh of `recruitment_offers`
    because the bench lives on `guilds`, not `recruitment_offers`.

Cost model:
  * Freezing a candidate: FREE (the value lives in the recruit later).
  * Recruiting from the bench: same `RECRUITMENT_COST_GOLD` as a normal
    recruit (no discount → no P2W). The bench is a convenience, not an
    economy lever. Documented explicitly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.shared.constants import RECRUITMENT_COST_GOLD


MAX_FROZEN_SLOTS = 2


# ─── Snapshot helpers ─────────────────────────────────────────────────────────
# Single source of truth for which fields are persisted in a frozen snapshot.
# Adding a field here propagates to GET /frozen + the recruit-frozen flow.
_SNAPSHOT_FIELDS = (
    "name", "adventurer_class_id", "class_name", "class_role", "rarity",
    "level", "experience",
    "strength", "agility", "intellect", "endurance", "faith",
    "stamina", "morale", "traits",
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_snapshot_from_offer(offer: dict) -> dict:
    """Project a recruitment offer doc into an immutable bench snapshot.

    We intentionally do NOT carry over `id` (= original candidate_id) into
    the snapshot — we mint a fresh `frozen_id`. This stops a player from
    re-freezing the same offer twice by triggering a refresh that surfaces
    the same template (a Test* edge case).
    """
    snap = {k: offer.get(k) for k in _SNAPSHOT_FIELDS}
    snap["frozen_id"] = str(uuid.uuid4())
    snap["original_candidate_id"] = offer.get("id")
    snap["cost_gold"] = RECRUITMENT_COST_GOLD
    snap["frozen_at"] = _now_utc().isoformat()
    return snap


def frozen_public(snap: dict) -> dict:
    """Public projection — mirrors `candidate_public` shape for FE parity."""
    from app.expeditions.formulas import adventurer_base_power
    base_power = adventurer_base_power(snap)
    return {
        "frozen_id": snap["frozen_id"],
        # Carry the original candidate id so the FE can deduplicate against
        # the active pool if it ever re-surfaces (the freeze endpoint already
        # prevents this on the server side).
        "original_candidate_id": snap.get("original_candidate_id"),
        "name": snap["name"],
        "adventurer_class_id": snap["adventurer_class_id"],
        "class_name": snap["class_name"],
        "class_role": snap["class_role"],
        "rarity": snap["rarity"],
        "level": snap["level"],
        "experience": snap["experience"],
        "strength": snap["strength"],
        "agility": snap["agility"],
        "intellect": snap["intellect"],
        "endurance": snap["endurance"],
        "faith": snap["faith"],
        "stamina": snap["stamina"],
        "morale": snap["morale"],
        "traits": snap.get("traits", []),
        "base_power": base_power,
        "equipment_power": 0,
        "total_power": base_power,
        "cost": snap.get("cost_gold", RECRUITMENT_COST_GOLD),
        "cost_gold": snap.get("cost_gold", RECRUITMENT_COST_GOLD),
        "frozen_at": snap.get("frozen_at"),
    }


# ─── DB helpers ───────────────────────────────────────────────────────────────
def _bench(guild: dict) -> dict:
    """Return the bench subdoc (empty default for legacy guilds)."""
    bench = guild.get("recruit_freeze_bench") or {}
    bench.setdefault("frozen_candidates", [])
    bench.setdefault("max_slots", MAX_FROZEN_SLOTS)
    return bench


async def get_frozen(db, guild_id: str) -> dict:
    """Return the bench payload for a guild (initializes lazily)."""
    g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "recruit_freeze_bench": 1})
    bench = _bench(g or {})
    return {
        "frozen": [frozen_public(s) for s in bench["frozen_candidates"]],
        "max_slots": bench["max_slots"],
        "used_slots": len(bench["frozen_candidates"]),
    }


async def freeze_candidate(db, guild: dict, candidate_id: str) -> dict:
    """Move an offer candidate onto the bench.

    Atomicity:
      1. Atomic `$pull` of the offer from `recruitment_offers` (single doc
         since each offer is its own row keyed by `id`).
      2. Capacity CAS: `$push` with `$where`-style guard on the array length
         via `find_one_and_update` matching `frozen_candidates.<idx>` exists.

    Race: if two `freeze` calls fire in parallel and the bench already has
    1 slot used, the second one will succeed (1+1=2 still ≤ max). If both
    target a 2-slot full bench, the CAS fails and we 409. The candidate
    pull is reverted in that case (compensating insert).
    """
    bench = _bench(guild)
    if len(bench["frozen_candidates"]) >= bench["max_slots"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "freeze_bench.full",
                "max_slots": bench["max_slots"],
                "used_slots": len(bench["frozen_candidates"]),
                "user_message": (
                    f"Panchina Reclute piena ({bench['max_slots']}/"
                    f"{bench['max_slots']}). Rilascia un candidato per liberare uno slot."
                ),
            },
        )
    # Guard: cannot freeze the same offer twice (idempotency at the
    # original_candidate_id level — relevant if the FE double-submits).
    if any(s.get("original_candidate_id") == candidate_id for s in bench["frozen_candidates"]):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "freeze_bench.already_frozen",
                "user_message": "Questo candidato è già in panchina.",
            },
        )

    # Atomic pull from the offer pool — guarantees the candidate exists
    # and is consumed in one shot.
    offer = await db.recruitment_offers.find_one_and_delete(
        {"id": candidate_id, "guild_id": guild["id"]},
        projection={"_id": 0},
    )
    if not offer:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "recruit.candidate_not_found",
                "user_message": "Candidato non trovato o già consumato.",
            },
        )

    snap = build_snapshot_from_offer(offer)

    # CAS push with capacity guard: only push if the current bench has
    # strictly fewer than max_slots entries.
    updated = await db.guilds.find_one_and_update(
        {
            "id": guild["id"],
            # `$expr` lets us inspect the array length atomically.
            "$expr": {
                "$lt": [
                    {"$size": {"$ifNull": ["$recruit_freeze_bench.frozen_candidates", []]}},
                    MAX_FROZEN_SLOTS,
                ]
            },
        },
        {
            "$push": {"recruit_freeze_bench.frozen_candidates": snap},
            "$set": {
                "recruit_freeze_bench.max_slots": MAX_FROZEN_SLOTS,
                "updated_at": _now_utc().isoformat(),
            },
        },
        projection={"_id": 0, "recruit_freeze_bench": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        # Compensating insert: restore the offer we just pulled.
        try:
            await db.recruitment_offers.insert_one({k: v for k, v in offer.items() if k != "_id"})
        except Exception:
            pass
        raise HTTPException(
            status_code=409,
            detail={
                "code": "freeze_bench.full",
                "max_slots": MAX_FROZEN_SLOTS,
                "user_message": "Panchina piena (race). Riprova.",
            },
        )

    # Best-effort audit (NEVER fail the response on audit error).
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="recruit_candidate_frozen",
            actor_guild_id=guild["id"],
            related_entity_id=snap["frozen_id"],
            source="recruitment.freeze",
            metadata={
                "original_candidate_id": snap.get("original_candidate_id"),
                "rarity": snap.get("rarity"),
                "class_name": snap.get("class_name"),
            },
        )
    except Exception:
        pass

    new_bench = _bench(updated)
    return {
        "frozen": [frozen_public(s) for s in new_bench["frozen_candidates"]],
        "max_slots": new_bench["max_slots"],
        "used_slots": len(new_bench["frozen_candidates"]),
        "newly_frozen": frozen_public(snap),
    }


async def unfreeze_candidate(db, guild: dict, frozen_id: str) -> dict:
    """Drop a snapshot from the bench. Candidate is NOT returned to the
    offer pool (that would let a player duplicate offers by freezing →
    refreshing → unfreezing)."""
    updated = await db.guilds.find_one_and_update(
        {
            "id": guild["id"],
            "recruit_freeze_bench.frozen_candidates.frozen_id": frozen_id,
        },
        {
            "$pull": {"recruit_freeze_bench.frozen_candidates": {"frozen_id": frozen_id}},
            "$set": {"updated_at": _now_utc().isoformat()},
        },
        projection={"_id": 0, "recruit_freeze_bench": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "freeze_bench.not_found",
                "user_message": "Slot panchina non trovato.",
            },
        )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="recruit_candidate_unfrozen",
            actor_guild_id=guild["id"],
            related_entity_id=frozen_id,
            source="recruitment.unfreeze",
        )
    except Exception:
        pass
    new_bench = _bench(updated)
    return {
        "frozen": [frozen_public(s) for s in new_bench["frozen_candidates"]],
        "max_slots": new_bench["max_slots"],
        "used_slots": len(new_bench["frozen_candidates"]),
    }


async def recruit_from_bench(db, guild: dict, frozen_id: str) -> tuple[dict, dict]:
    """Materialise a frozen snapshot into a real adventurer.

    Atomicity flow (mirrors `recruit_from_offer`):
      1. CAS pull the snapshot from the bench (proves existence + reserves).
      2. CAS debit `RECRUITMENT_COST_GOLD` from guild. On failure → push
         the snapshot back to the bench (compensating).
      3. Insert adventurer doc.
      4. Post-insert cap re-count. If over cap → delete the adv + refund
         gold + push snapshot back to bench + raise 423.
      5. Audit `recruit_frozen_candidate_hired` on success.
    """
    # Step 1: atomic pull of the snapshot from the bench.
    before = await db.guilds.find_one_and_update(
        {
            "id": guild["id"],
            "recruit_freeze_bench.frozen_candidates.frozen_id": frozen_id,
        },
        {
            "$pull": {"recruit_freeze_bench.frozen_candidates": {"frozen_id": frozen_id}},
        },
        projection={"_id": 0, "recruit_freeze_bench": 1},
        return_document=ReturnDocument.BEFORE,
    )
    if not before:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "freeze_bench.not_found",
                "user_message": "Slot panchina non trovato.",
            },
        )
    snap = next(
        (s for s in (before.get("recruit_freeze_bench") or {}).get("frozen_candidates", [])
         if s.get("frozen_id") == frozen_id),
        None,
    )
    if not snap:
        # Defensive: shouldn't happen given the match clause above.
        raise HTTPException(
            status_code=404,
            detail={"code": "freeze_bench.not_found", "user_message": "Slot non trovato."},
        )

    async def _restore_snapshot():
        try:
            await db.guilds.update_one(
                {"id": guild["id"]},
                {"$push": {"recruit_freeze_bench.frozen_candidates": snap}},
            )
        except Exception:
            pass

    # Step 2: gold debit CAS.
    now = _now_utc()
    cost = int(snap.get("cost_gold", RECRUITMENT_COST_GOLD))
    updated_guild = await db.guilds.find_one_and_update(
        {"id": guild["id"], "gold": {"$gte": cost}},
        {"$inc": {"gold": -cost}, "$set": {"updated_at": now.isoformat()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_guild:
        await _restore_snapshot()
        raise HTTPException(
            status_code=402,
            detail={
                "code": "economy.insufficient_gold",
                "required": cost,
                "user_message": f"Oro insufficiente: servono {cost}g.",
            },
        )

    # Step 3: insert adventurer doc.
    adv_doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "name": snap["name"],
        "adventurer_class_id": snap["adventurer_class_id"],
        "class_name": snap["class_name"],
        "class_role": snap["class_role"],
        "rarity": snap["rarity"],
        "level": snap["level"],
        "experience": snap["experience"],
        "strength": snap["strength"],
        "agility": snap["agility"],
        "intellect": snap["intellect"],
        "endurance": snap["endurance"],
        "faith": snap["faith"],
        "stamina": snap["stamina"],
        "morale": snap["morale"],
        "traits": snap.get("traits", []),
        "is_available": True,
        "is_starter": False,
        "rename_count": 0,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.adventurers.insert_one(adv_doc)

    # Step 4: post-insert cap re-count.
    try:
        from app.territory.guards import compute_adventurer_cap_state
        cap_state = await compute_adventurer_cap_state(db, guild["id"])
        if int(cap_state.get("current", 0)) > int(cap_state.get("cap", 0)):
            # Loser branch: rollback insert + refund gold + restore snapshot.
            await db.adventurers.delete_one({"id": adv_doc["id"]})
            await db.guilds.update_one(
                {"id": guild["id"]},
                {"$inc": {"gold": cost}, "$set": {"updated_at": now.isoformat()}},
            )
            await _restore_snapshot()
            raise HTTPException(
                status_code=423,
                detail={
                    "code": "roster_over_capacity",
                    "current": int(cap_state.get("current", 0)),
                    "cap": int(cap_state.get("cap", 0)),
                    "source": "recruitment.recruit_frozen",
                    "user_message": (
                        "Capienza avventurieri raggiunta. Potenzia i Dormitori o "
                        "congeda qualcuno prima di reclutare dalla panchina."
                    ),
                },
            )
    except HTTPException:
        raise
    except Exception:
        # If the cap check itself blows up, we play safe and roll back
        # the adventurer + refund.
        await db.adventurers.delete_one({"id": adv_doc["id"]})
        await db.guilds.update_one(
            {"id": guild["id"]},
            {"$inc": {"gold": cost}, "$set": {"updated_at": now.isoformat()}},
        )
        await _restore_snapshot()
        raise

    # Refresh guild to reflect the (still-debited) gold post-cap-check.
    final_guild = await db.guilds.find_one({"id": guild["id"]}, {"_id": 0})
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="recruit_frozen_candidate_hired",
            actor_guild_id=guild["id"],
            related_entity_id=adv_doc["id"],
            source="recruitment.recruit_frozen",
            metadata={
                "frozen_id": frozen_id,
                "original_candidate_id": snap.get("original_candidate_id"),
                "rarity": snap.get("rarity"),
                "cost_gold": cost,
            },
        )
    except Exception:
        pass
    return adv_doc, final_guild


__all__ = [
    "MAX_FROZEN_SLOTS",
    "get_frozen",
    "freeze_candidate",
    "unfreeze_candidate",
    "recruit_from_bench",
    "frozen_public",
    "build_snapshot_from_offer",
]
