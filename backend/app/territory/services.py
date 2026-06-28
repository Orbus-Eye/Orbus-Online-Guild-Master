"""ROUND 6B.1 — Territory services.

Provides:
- `ensure_guild_structures_doc(db, guild_id)`: lazy-create the document for
  a guild that does not yet have one (used on first GET).
- `get_territory(db, guild_id)`: fetch the document, lazily create if missing.
- `purchase_structure(db, guild, slug)`: unlock a structure at Lv1 (no atomic deduction yet in 6B.1).
- `upgrade_structure(db, guild, slug)`: bump a structure level by +1 (no atomic deduction yet).

Errors are raised as HTTPException with a structured `detail` dict so the
frontend can render localized banners (UI lives in 6B.2).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.territory.costs import cost_for
from app.territory.structures import (
    VALID_STRUCTURE_SLUGS,
    default_structures_doc,
    get_prerequisites,
    get_structure_max_level,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_doc(doc: dict) -> dict:
    """Strip the BSON `_id` and return only the public shape.

    ROUND 11.2 EXT TASK 10 PRE-S2 — also enriches each structure with a
    `next_level_cost` preview (gold + materials map) so the FE can show
    "ti mancano: 36× Frammento di Ferro" BEFORE the user clicks Potenzia.
    Eliminates the "ho l'oggetto ma non permette" UX trap where the
    backend rejected a click for a cost the FE never displayed.

    TASK 10 M1 — `next_level_cost.materials` is also returned as a flat
    map (slug → required) plus an opt-in enriched list when an inventory
    snapshot is provided by the caller via `_enrich_with_inventory()`.
    """
    structures = doc["structures"] or {}
    enriched: dict[str, dict] = {}
    for slug, info in structures.items():
        info = dict(info or {})
        cur_level = int(info.get("level", 0))
        next_cost = None
        if cur_level >= 1:
            max_lv = get_structure_max_level(slug, allow_legacy=False)
            if cur_level < max_lv:
                raw = cost_for(slug, cur_level + 1)
                if raw is not None:
                    next_cost = {
                        "target_level": cur_level + 1,
                        "gold": int(raw.get("gold", 0)),
                        "materials": dict(raw.get("materials") or {}),
                    }
        info["next_level_cost"] = next_cost
        enriched[slug] = info
    return {
        "id": doc["id"],
        "guild_id": doc["guild_id"],
        "structures": enriched,
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def _enrich_territory_with_inventory(db, payload: dict, guild_id: str) -> dict:
    """ROUND 11.2 EXT TASK 10 M1 — enrich `next_level_cost` with the
    actual guild inventory snapshot so the FE renders cost preview as
    `(owned/required, can_afford, missing[])` without a second roundtrip.

    Adds per-structure:
      * `next_level_cost.materials_detail`: list of
        `{slug, display_name_it, display_name_en, required, owned, missing}`
      * `next_level_cost.owned_gold`: guild's current gold.
      * `next_level_cost.can_afford`: bool — gold AND every material OK.
      * `next_level_cost.missing`: `{gold:int, materials:[{slug,display_name_it,missing}]}`

    No side effects, no PII leak, no equipment exposed.
    """
    structures = payload.get("structures") or {}
    # Collect all material slugs referenced by any next_level_cost.
    all_slugs: set[str] = set()
    for info in structures.values():
        nlc = info.get("next_level_cost")
        if nlc:
            for slug in (nlc.get("materials") or {}).keys():
                all_slugs.add(slug)
    if not all_slugs:
        # Still attach owned_gold to anything with a next_level_cost so
        # the FE can render "Oro X/Y" even for material-free upgrades.
        g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "gold": 1})
        gold_owned = int((g or {}).get("gold", 0))
        for info in structures.values():
            nlc = info.get("next_level_cost")
            if nlc:
                nlc["owned_gold"] = gold_owned
                nlc["can_afford"] = bool(gold_owned >= int(nlc.get("gold", 0)))
                nlc["missing"] = {"gold": max(0, int(nlc.get("gold", 0)) - gold_owned), "materials": []}
                nlc["materials_detail"] = []
        return payload

    # Resolve slugs → template ids + display names (single query).
    items_by_slug: dict[str, dict] = {}
    async for it in db.items.find(
        {"slug": {"$in": list(all_slugs)}, "item_type": "material"},
        {"_id": 0, "id": 1, "slug": 1, "display_name_it": 1, "display_name_en": 1, "name": 1},
    ):
        items_by_slug[it["slug"]] = it
    template_ids = [v["id"] for v in items_by_slug.values()]

    # Aggregate owned quantities (single query across all templates).
    # ROUND 11.2 EXT S3 P1 FIX — `owned` here reflects *available*
    # quantity (= quantity - market_locked_qty). This keeps the FE
    # preview honest: materials currently listed in an active auction
    # are NOT spendable on a Territory upgrade, and the preview MUST
    # mirror the same gate used by `_atomic_debit_materials`.
    owned_by_template: dict[str, int] = {tid: 0 for tid in template_ids}
    if template_ids:
        async for row in db.inventory_items.find(
            {"guild_id": guild_id, "item_id": {"$in": template_ids}},
            {"_id": 0, "item_id": 1, "quantity": 1, "market_locked_qty": 1},
        ):
            available = max(
                0,
                int(row.get("quantity", 0)) - int(row.get("market_locked_qty", 0)),
            )
            owned_by_template[row["item_id"]] = (
                owned_by_template.get(row["item_id"], 0) + available
            )

    g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "gold": 1})
    gold_owned = int((g or {}).get("gold", 0))

    for slug, info in structures.items():
        nlc = info.get("next_level_cost")
        if not nlc:
            continue
        materials = nlc.get("materials") or {}
        detail: list[dict] = []
        missing_mats: list[dict] = []
        for mat_slug, required in materials.items():
            item = items_by_slug.get(mat_slug, {})
            tid = item.get("id")
            owned = int(owned_by_template.get(tid, 0)) if tid else 0
            required_q = int(required)
            display_it = (
                item.get("display_name_it")
                or item.get("name")
                or mat_slug.replace("_", " ").title()
            )
            display_en = item.get("display_name_en") or item.get("name") or mat_slug
            detail.append({
                "slug": mat_slug,
                "display_name_it": display_it,
                "display_name_en": display_en,
                "required": required_q,
                "owned": owned,
                "missing": max(0, required_q - owned),
            })
            if owned < required_q:
                missing_mats.append({
                    "slug": mat_slug,
                    "display_name_it": display_it,
                    "missing": required_q - owned,
                })
        gold_required = int(nlc.get("gold", 0))
        gold_missing = max(0, gold_required - gold_owned)
        nlc["materials_detail"] = detail
        nlc["owned_gold"] = gold_owned
        nlc["missing"] = {"gold": gold_missing, "materials": missing_mats}
        nlc["can_afford"] = bool(gold_missing == 0 and not missing_mats)
    return payload


async def ensure_guild_structures_doc(db, guild_id: str) -> dict:
    """Lazy creation: if no doc exists for this guild, insert a default one.

    Idempotent and race-safe via the unique index on `guild_id` (created at
    boot in `app.core.indexes`). On DuplicateKeyError we re-read.

    ROUND 6E FIX 0 — for guilds created BEFORE a new structure slug was
    added to ``STRUCTURE_CATALOG`` (e.g. `training_grounds` from 6C or
    `contract_board` from 6D), the embedded sub-doc lacks the new slugs.
    We backfill them in-place with the default shape so the public
    ``GET /api/territory`` response always carries the full catalog —
    no more `contract_board: null` on legacy guilds.
    """
    existing = await db.guild_structures.find_one({"guild_id": guild_id})
    if existing:
        return await _backfill_missing_catalog_slugs(db, existing)
    now = _utc_now_iso()
    doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "structures": default_structures_doc(),
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.guild_structures.insert_one(doc)
    except Exception:
        # If a parallel request beat us to it, just re-read.
        existing = await db.guild_structures.find_one({"guild_id": guild_id})
        if existing:
            return await _backfill_missing_catalog_slugs(db, existing)
        raise
    return doc


async def _backfill_missing_catalog_slugs(db, doc: dict) -> dict:
    """ROUND 6E FIX 0 — patch `structures` with any catalog slug absent
    from the embedded doc. Uses a per-slug ``$set`` so we never overwrite
    an unlocked structure. Returns the doc with the patched sub-fields
    so the caller can return it without an extra read.
    """
    current = doc.get("structures") or {}
    missing: dict[str, dict] = {}
    defaults = default_structures_doc()
    for slug, default_value in defaults.items():
        if slug not in current:
            missing[slug] = default_value
    if not missing:
        return doc
    updates = {f"structures.{slug}": value for slug, value in missing.items()}
    updates["updated_at"] = _utc_now_iso()
    await db.guild_structures.update_one(
        {"id": doc["id"]}, {"$set": updates},
    )
    # Patch the in-memory doc so the caller sees the same view.
    doc.setdefault("structures", {}).update(missing)
    doc["updated_at"] = updates["updated_at"]
    return doc


async def get_territory(db, guild_id: str) -> dict:
    doc = await ensure_guild_structures_doc(db, guild_id)
    payload = _public_doc(doc)
    # ROUND 11.2 EXT TASK 10 M1 — overlay owned/missing/can_afford.
    return await _enrich_territory_with_inventory(db, payload, guild_id)


def _validate_slug(slug: str) -> None:
    if slug not in VALID_STRUCTURE_SLUGS:
        raise HTTPException(
            status_code=422,
            detail={"code": "structure_slug.invalid", "slug": slug},
        )


def _check_prerequisites(structures: dict, slug: str) -> None:
    """Raise 423 (Locked) if any prerequisite is unmet."""
    reqs = get_prerequisites(slug)
    if not reqs:
        return
    unmet = []
    for req_slug, req_level in reqs.items():
        cur = structures.get(req_slug) or {}
        if int(cur.get("level", 0)) < int(req_level):
            unmet.append({"structure": req_slug, "min_level": req_level,
                          "current_level": int(cur.get("level", 0))})
    if unmet:
        raise HTTPException(
            status_code=423,
            detail={"code": "structure.prerequisites_unmet", "unmet": unmet},
        )


async def _resolve_material_template_ids(db, materials: dict) -> dict[str, str]:
    """ROUND 6B.3 — map material slug → item template id. Raises 500 if a
    slug referenced by `UPGRADE_COSTS` is missing from the `items` collection
    (configuration bug, not user-actionable)."""
    if not materials:
        return {}
    slugs = list(materials.keys())
    rows = await db.items.find(
        {"slug": {"$in": slugs}}, {"_id": 0, "id": 1, "slug": 1},
    ).to_list(len(slugs))
    by_slug = {r["slug"]: r["id"] for r in rows}
    missing = [s for s in slugs if s not in by_slug]
    if missing:
        raise HTTPException(
            status_code=500,
            detail={"code": "territory.material_template_missing",
                    "missing_slugs": missing,
                    "hint": "Server config error: item templates are missing in DB. "
                            "Contact admin."},
        )
    return by_slug


async def _atomic_debit_gold(db, *, guild_id: str, gold_cost: int) -> int:
    """ROUND 6B.3 — atomic gold debit. Single-doc `$inc` with `gold >= cost`
    filter guarantees gold never goes negative even under concurrent writes.

    Returns the NEW gold balance on success. Raises 422 with current
    balance on failure (re-read for the user message).
    """
    if gold_cost <= 0:
        # No-op fast path (starter Lv1 with cost=0).
        g = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "gold": 1})
        return int((g or {}).get("gold", 0))
    res = await db.guilds.find_one_and_update(
        {"id": guild_id, "gold": {"$gte": gold_cost}},
        {"$inc": {"gold": -gold_cost}},
        projection={"_id": 0, "gold": 1},
        return_document=True,  # returns post-update doc
    )
    # motor's find_one_and_update returns None if filter didn't match.
    if not res:
        cur = await db.guilds.find_one({"id": guild_id}, {"_id": 0, "gold": 1})
        raise HTTPException(
            status_code=422,
            detail={"code": "resources.gold_insufficient",
                    "required": gold_cost,
                    "available": int((cur or {}).get("gold", 0))},
        )
    return int(res.get("gold", 0))


async def _atomic_debit_materials(
    db,
    *,
    guild_id: str,
    materials: dict,
    template_by_slug: dict[str, str],
) -> list[tuple[str, str, int]]:
    """ROUND 6B.3 — atomic per-material debit. Returns a list of applied
    debits `(slug, template_id, qty)` so the caller can compensate-rollback
    if a later step fails. Raises 422 on first insufficient material; the
    caller is responsible for the gold refund + already-debited materials
    refund (see `_compensate_refund`).

    ROUND 11.2 EXT S3 P1 FIX — the check now uses *available* quantity
    (= ``quantity - market_locked_qty``) instead of raw ``quantity``.
    Materials listed in an active auction are no longer spendable on
    Territory upgrades, eliminating a latent double-spend window where a
    player could consume a listed stack, have the listing remain valid,
    and ship the buyer phantom goods at sale time.
    """
    applied: list[tuple[str, str, int]] = []
    for slug, qty in materials.items():
        qty = int(qty)
        if qty <= 0:
            continue
        template_id = template_by_slug[slug]
        # Atomic CAS on `quantity - market_locked_qty >= qty`. Materials
        # never get `equipped_count`, so equipped is implicitly 0.
        res = await db.inventory_items.find_one_and_update(
            {
                "guild_id": guild_id,
                "item_id": template_id,
                "$expr": {
                    "$gte": [
                        {"$subtract": [
                            "$quantity",
                            {"$ifNull": ["$market_locked_qty", 0]},
                        ]},
                        qty,
                    ],
                },
            },
            {"$inc": {"quantity": -qty}},
            projection={"_id": 0, "quantity": 1, "market_locked_qty": 1},
            return_document=True,
        )
        if not res:
            # Roll back what we've already debited in this loop, plus the
            # caller will refund gold. The exception detail names the
            # missing material so the UI can surface it cleanly. The
            # `available` value reported here MUST be computed identically
            # to the gating condition above so the player message matches
            # what the FE preview shows.
            await _compensate_refund(
                db, guild_id=guild_id,
                gold_refund=0, materials_refund=applied,
            )
            cur = await db.inventory_items.find_one(
                {"guild_id": guild_id, "item_id": template_id},
                {"_id": 0, "quantity": 1, "market_locked_qty": 1},
            )
            cur_total = int((cur or {}).get("quantity", 0))
            cur_locked = int((cur or {}).get("market_locked_qty", 0))
            cur_available = max(0, cur_total - cur_locked)
            raise HTTPException(
                status_code=422,
                detail={"code": "resources.material_insufficient",
                        "slug": slug, "required": qty,
                        "available": cur_available},
            )
        applied.append((slug, template_id, qty))
    return applied


async def _compensate_refund(
    db,
    *,
    guild_id: str,
    gold_refund: int,
    materials_refund: list[tuple[str, str, int]],
) -> None:
    """ROUND 6B.3 — best-effort compensating action when a later step in
    the atomic flow fails (e.g. CAS race on structure update). Failures
    here are logged at WARN but never re-raised: the user already saw a
    422/409, and we must not mask that with a 500."""
    try:
        if gold_refund > 0:
            await db.guilds.update_one(
                {"id": guild_id}, {"$inc": {"gold": gold_refund}},
            )
    except Exception:  # noqa: BLE001
        import logging
        logging.getLogger("orbus.territory").warning(
            "compensate gold refund failed for guild=%s amount=%d",
            guild_id, gold_refund,
        )
    for slug, template_id, qty in materials_refund:
        try:
            await db.inventory_items.update_one(
                {"guild_id": guild_id, "item_id": template_id},
                {"$inc": {"quantity": qty}},
            )
        except Exception:  # noqa: BLE001
            import logging
            logging.getLogger("orbus.territory").warning(
                "compensate material refund failed for guild=%s slug=%s qty=%d",
                guild_id, slug, qty,
            )


async def _emit_purchase_audit(
    db, *, guild: dict, slug: str, from_level: int, to_level: int, cost: dict,
    event: str, source: str,
) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type=event,
            actor_user_id=guild.get("owner_user_id"),
            actor_guild_id=guild["id"],
            source=source,
            gold_delta=-int(cost.get("gold", 0)),
            metadata={"structure_slug": slug, "from_level": from_level,
                      "to_level": to_level, "cost": cost},
        )
    except Exception:  # noqa: BLE001
        pass


async def _atomic_purchase_or_upgrade(
    db,
    *,
    guild: dict,
    slug: str,
    doc: dict,
    from_level: int,
    to_level: int,
    cost: dict,
    event: str,
    source: str,
) -> None:
    """ROUND 6B.3 — single atomic flow shared by purchase + upgrade.

    Steps (in order, with compensating rollback on failure):
      1. Resolve material template ids (raises 500 if config-broken).
      2. Debit gold atomically ($inc with `gold >= cost` filter).
      3. Debit each material atomically (per-slug $inc with `qty >= need`).
         On failure: refund already-debited materials + raise 422.
      4. Update structure with CAS guard on previous level. On CAS miss
         (concurrent purchase / out-of-band edit): refund gold + materials
         + raise 409.
      5. Write audit log (best-effort, never blocks).
    """
    materials = dict(cost.get("materials") or {})
    template_by_slug = await _resolve_material_template_ids(db, materials)

    gold_cost = int(cost.get("gold", 0))
    # Step 2: gold debit
    await _atomic_debit_gold(db, guild_id=guild["id"], gold_cost=gold_cost)
    # Step 3: material debit (will auto-refund itself on partial failure;
    # if anything raises, we still need to refund the gold from step 2).
    try:
        debited_materials = await _atomic_debit_materials(
            db, guild_id=guild["id"], materials=materials,
            template_by_slug=template_by_slug,
        )
    except HTTPException:
        # _atomic_debit_materials already rolled back partial materials,
        # but it doesn't know about the gold debit.
        await _compensate_refund(
            db, guild_id=guild["id"],
            gold_refund=gold_cost, materials_refund=[],
        )
        raise

    # Step 4: CAS structure update.
    now = _utc_now_iso()
    update_path = f"structures.{slug}"
    new_struct = {
        "level": to_level,
        "is_unlocked": True,
        "purchased_at": doc["structures"].get(slug, {}).get("purchased_at") or now,
        "upgraded_at": now,
        "acquired_via": (doc["structures"].get(slug, {}).get("acquired_via")
                         if from_level > 0 else "purchase") or "purchase",
    }
    cas_filter = {
        "id": doc["id"],
        f"{update_path}.level": from_level,
    }
    res = await db.guild_structures.update_one(
        cas_filter,
        {"$set": {update_path: new_struct, "updated_at": now}},
    )
    if res.matched_count == 0:
        # CAS miss: someone else moved the structure between our read and
        # our write. Refund everything and surface a 409 — the client can
        # re-fetch and retry.
        await _compensate_refund(
            db, guild_id=guild["id"],
            gold_refund=gold_cost,
            materials_refund=debited_materials,
        )
        raise HTTPException(
            status_code=409,
            detail={"code": "structure.concurrent_modification",
                    "slug": slug,
                    "hint": "Refresh and retry."},
        )

    # Step 5: audit log (real delta now — gold has actually moved).
    await _emit_purchase_audit(
        db, guild=guild, slug=slug,
        from_level=from_level, to_level=to_level,
        cost=cost, event=event, source=source,
    )


async def purchase_structure(db, guild: dict, slug: str) -> dict:
    """Move a structure from Lv0 (locked) → Lv1 (unlocked).

    ROUND 6B.3 — atomic debit (gold + materials) enforced via single-doc
    `$inc` queries with quantity guards; compensating refund on partial
    failure. Audit log now reflects the REAL debit.

    Errors:
      - 422 structure_slug.invalid
      - 409 structure.already_unlocked (already Lv≥1)
      - 423 structure.prerequisites_unmet
      - 422 resources.gold_insufficient
      - 422 resources.material_insufficient
      - 409 structure.concurrent_modification (CAS race)
    """
    _validate_slug(slug)
    doc = await ensure_guild_structures_doc(db, guild["id"])
    cur = doc["structures"].get(slug, {})
    cur_level = int(cur.get("level", 0))
    if cur_level >= 1:
        raise HTTPException(
            status_code=409,
            detail={"code": "structure.already_unlocked", "slug": slug,
                    "current_level": cur_level},
        )
    _check_prerequisites(doc["structures"], slug)
    # ROUND 6B.3 — cost ALWAYS read from server-side constant table.
    # Never trust a client-side value (would be a P2W exploit).
    cost = cost_for(slug, 1) or {}
    await _atomic_purchase_or_upgrade(
        db, guild=guild, slug=slug, doc=doc,
        from_level=0, to_level=1, cost=cost,
        event="guild_structure_purchased", source="territory.purchase",
    )
    return await get_territory(db, guild["id"])


async def upgrade_structure(db, guild: dict, slug: str) -> dict:
    """Bump a structure level by +1 (Lv N → Lv N+1).

    ROUND 6B.3 — atomic debit (see `purchase_structure`).

    Errors:
      - 422 structure_slug.invalid
      - 423 structure.locked (current level is 0 → purchase first)
      - 409 structure.already_max_level
      - 423 structure.prerequisites_unmet
      - 422 resources.gold_insufficient
      - 422 resources.material_insufficient
      - 422 structure.upgrade_not_available (None in cost table = legacy-only)
      - 409 structure.concurrent_modification
    """
    _validate_slug(slug)
    doc = await ensure_guild_structures_doc(db, guild["id"])
    cur = doc["structures"].get(slug, {})
    cur_level = int(cur.get("level", 0))
    if cur_level < 1:
        raise HTTPException(
            status_code=423,
            detail={"code": "structure.locked", "slug": slug,
                    "hint": "Call POST /api/territory/purchase first."},
        )
    max_lv = get_structure_max_level(slug, allow_legacy=False)
    if cur_level >= max_lv:
        raise HTTPException(
            status_code=409,
            detail={"code": "structure.already_max_level", "slug": slug,
                    "current_level": cur_level, "max_level": max_lv},
        )
    next_level = cur_level + 1
    cost = cost_for(slug, next_level)
    if cost is None:
        # Migration-only level — cannot be reached via user upgrade.
        raise HTTPException(
            status_code=422,
            detail={"code": "structure.upgrade_not_available", "slug": slug,
                    "target_level": next_level,
                    "hint": "This level can only be unlocked via legacy migration."},
        )
    _check_prerequisites(doc["structures"], slug)
    await _atomic_purchase_or_upgrade(
        db, guild=guild, slug=slug, doc=doc,
        from_level=cur_level, to_level=next_level, cost=cost,
        event="guild_structure_upgraded", source="territory.upgrade",
    )
    # ROUND 6D — contract progress (structures_upgraded)
    try:
        from app.contracts.services import increment_contract_progress
        await increment_contract_progress(
            db, guild["id"], "structures_upgraded", 1,
        )
    except Exception:
        pass
    return await get_territory(db, guild["id"])


__all__ = [
    "ensure_guild_structures_doc",
    "get_territory",
    "purchase_structure",
    "upgrade_structure",
]
