"""Phase 14.3-c — read-only expedition preview.

Computes success_chance, injury_risk, expected_reward and modifier list
for a dispatch combo (dungeon + 3 adventurers) WITHOUT touching the DB
beyond read queries. Re-uses the canonical formulas from
`app.expeditions.formulas` so the preview matches the actual dispatch
math exactly.
"""
from typing import List

from fastapi import HTTPException

from app.adventurers.services import (
    _is_test_trait_doc,
    _polarity_for,
    _trait_display_name,
)
from app.expeditions.formulas import (
    adventurer_effective_power as _eff_power,
    compute_team_power,
    compute_success_chance,
    overpower_loot_multiplier,
    power_rating,
)


def _injury_risk(team_power: int, recommended: int, has_healer: bool, has_tank: bool) -> str:
    delta = team_power - recommended
    # Tank/Healer presence shifts risk down by ~5 power-equivalent.
    if has_tank:
        delta += 5
    if has_healer:
        delta += 5
    if delta < -10:
        return "high"
    if delta < 10:
        return "medium"
    return "low"


def _loot_rarity_hint(success_chance: int) -> str:
    if success_chance >= 80:
        return "rare"
    if success_chance >= 50:
        return "uncommon"
    return "common"


def _trait_modifier_entry(t: dict) -> dict | None:
    if not isinstance(t, dict) or _is_test_trait_doc(t):
        return None
    return {
        "source": "trait",
        "code": t.get("code") or (t.get("name") or "").lower(),
        "display_name": _trait_display_name(t),
        "polarity": _polarity_for(t),
        "description": t.get("description", "") or "",
    }


def _class_modifier_entry(name: str, role: str) -> dict | None:
    if not name:
        return None
    return {
        "source": "class",
        "code": (name or "").lower(),
        "display_name": name,
        "polarity": "positive",
        "description": f"Bonus di squadra grazie al ruolo {role or '—'}.",
    }


async def preview_expedition(
    db, guild: dict, dungeon_id: str, adventurer_ids: List[str]
) -> dict:
    """Read-only preview. Validates dungeon + team ownership.

    Returns the canonical shape documented in the public spec
    (Phase 14.3-c Fase 2). Never writes to DB.
    """
    # FASE 8E — messaggi player-facing in italiano.
    if not dungeon_id:
        raise HTTPException(status_code=422, detail="Indica il dungeon")
    if not adventurer_ids:
        raise HTTPException(status_code=422, detail="Seleziona gli avventurieri")

    dungeon = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon non trovato")

    required = int(dungeon.get("required_team_size", 3))
    if len(adventurer_ids) != required:
        raise HTTPException(
            status_code=422,
            detail=f"Questo dungeon richiede esattamente {required} avventurieri",
        )
    if len(set(adventurer_ids)) != len(adventurer_ids):
        raise HTTPException(status_code=422, detail="Duplicate adventurer ids")

    # Ownership + existence (single query)
    advs = await db.adventurers.find(
        {"id": {"$in": adventurer_ids}, "guild_id": guild["id"]},
        {"_id": 0},
    ).to_list(len(adventurer_ids))
    if len(advs) != len(adventurer_ids):
        raise HTTPException(
            status_code=403,
            detail="Uno o più avventurieri non appartengono alla tua gilda",
        )

    # FASE 2.2 — il level-gate è stato sostituito dal gate a potere del
    # gruppo, applicato più sotto DOPO il calcolo del team_power (serve
    # l'equipaggiamento per un potere realistico).

    # Phase 6+ snapshot equivalent: equip power lookup
    from app.equipment.services import _load_equipment_for_guild
    equip_map = await _load_equipment_for_guild(db, guild["id"])
    members_for_power = []
    classes_seen = set()
    for a in advs:
        _, eq_power = equip_map.get(a["id"], ({}, 0))
        eff = _eff_power(a)
        members_for_power.append({
            "total_power_snapshot": int(eff) + int(eq_power),
            "equipment_power_snapshot": int(eq_power),
            "class_role": a.get("class_role"),
            "level": a.get("level", 1),
        })
        classes_seen.add((a.get("class_name") or "", a.get("class_role") or ""))

    team_power = compute_team_power(members_for_power)
    recommended = int(dungeon.get("recommended_power", 0))

    # FASE 2.2 — gate a potere: blocca il preview con lo stesso 423 del
    # dispatch, così il FE mostra l'errore PRIMA di "Avvia Spedizione".
    from app.expeditions.power_gate import enforce_min_team_power
    enforce_min_team_power(team_power, dungeon, source="expedition.preview")

    success_chance = compute_success_chance(team_power, recommended)
    rating = power_rating(team_power, recommended)
    loot_multiplier = overpower_loot_multiplier(rating)
    roles = {m["class_role"] for m in members_for_power if m.get("class_role")}
    injury_risk = _injury_risk(
        team_power, recommended,
        has_healer="Healer" in roles, has_tank="Tank" in roles,
    )

    base_gold = int(dungeon.get("base_gold_reward", 0))
    base_xp = int(dungeon.get("base_xp_reward", 0))
    expected_reward = {
        "gold_range": [int(round(base_gold * 0.25)), base_gold],
        "xp_range": [int(round(base_xp * 0.5)), base_xp],
        "loot_rarity_hint": _loot_rarity_hint(success_chance),
    }

    modifiers = []
    for a in advs:
        for t in (a.get("traits") or []):
            entry = _trait_modifier_entry(t)
            if entry:
                modifiers.append(entry)
    for class_name, role in classes_seen:
        c = _class_modifier_entry(class_name, role)
        if c:
            modifiers.append(c)

    return {
        "success_chance": int(success_chance),
        "injury_risk": injury_risk,
        "expected_reward": expected_reward,
        "team_power": int(team_power),
        "recommended_power": int(recommended),
        # FASE 2.1 — Rating di Potenza + bonus Overpower per la UI.
        "power_rating": int(rating),
        "overpower_loot_multiplier": float(loot_multiplier),
        "modifiers": modifiers,
    }


__all__ = ["preview_expedition"]
