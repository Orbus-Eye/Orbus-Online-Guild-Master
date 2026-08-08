"""ROUND 16.1 Phase 2 — Dungeon pre-launch preview builder.

Computes the data shown in the FE preview modal:
  - dungeon meta (name_it/name_en, difficulty, duration, recommended power)
  - threats matrix (countered / uncountered, source per counter)
  - team_power + estimated success_chance (incl. threat bonus)
  - injury risk band (low/medium/high)
  - rewards preview (gold/xp range + items/materials sample)
  - bilingual weakness suggestion text
"""
from __future__ import annotations

from typing import Any

from app.class_halls.mechanics import resolve_class_mechanic
from app.dungeons.encounters import (
    COUNTER_THREAT_MAP,
    apply_dungeon_encounter,
)
from app.equipment.services import _load_equipment_for_adventurer
from app.expeditions.formulas import (
    adventurer_effective_power,
    compute_team_power,
    compute_success_chance,
)
from app.expeditions.threats import (
    SUCCESS_BONUS_CAP_PCT,
    INJURY_REDUCTION_CAP_PCT,
    compute_threat_resolution,
)


THREAT_NAME_IT = {
    "boss": "Boss", "minion": "Sgherri", "spell": "Incantesimo",
    "trap": "Trappola", "curse": "Maledizione", "ambush": "Imboscata",
    "elite": "Elite", "undead": "Non-morti", "beast": "Bestie",
    "elemental": "Elementali", "void": "Corruzione del Vuoto",
    "poison": "Veleno", "disease": "Malattia", "siege": "Assedio",
    "stealth": "Furtività", "magic_barrier": "Barriera Magica",
}
THREAT_NAME_EN = {
    "boss": "Boss", "minion": "Minions", "spell": "Spell",
    "trap": "Trap", "curse": "Curse", "ambush": "Ambush",
    "elite": "Elite", "undead": "Undead", "beast": "Beasts",
    "elemental": "Elemental", "void": "Void Corruption",
    "poison": "Poison", "disease": "Disease", "siege": "Siege",
    "stealth": "Stealth", "magic_barrier": "Magic Barrier",
}


async def _resolve_counter_sources(db, threat_slug: str,
                                    team: list[dict]) -> list[dict]:
    """Return list of {adv_id, name, source} for each team member that
    counters the given threat (either via spec.counter_tags or
    trait.counter_tags). Empty list if no member counters this threat."""
    counters_for_threat = {
        counter_slug
        for counter_slug, threats in COUNTER_THREAT_MAP.items()
        if threat_slug in threats
    }
    async for c in db.counter_tags.find(
        {"is_active": True, "threats_countered": threat_slug},
        {"_id": 0, "slug": 1},
    ):
        counters_for_threat.add(c["slug"])

    spec_counter_cache: dict[str, set[str]] = {}
    trait_counter_cache: dict[str, set[str]] = {}
    sources: list[dict] = []
    for m in team:
        mechanic_counters = set(
            m.get("class_mechanic_counter_tags") or []
        )
        if counters_for_threat & mechanic_counters:
            sources.append({
                "adv_id": m.get("id"),
                "name": m.get("name"),
                "source": (
                    "class_mechanic:"
                    f"{m.get('class_mechanic_id') or 'active'}"
                ),
            })
            continue
        spec = m.get("specialization_slug")
        if spec and spec not in spec_counter_cache:
            doc = await db.class_specializations.find_one(
                {"slug": spec}, {"_id": 0, "counter_tags": 1})
            spec_counter_cache[spec] = set(doc.get("counter_tags") or []) if doc else set()
        if spec and counters_for_threat & spec_counter_cache.get(spec, set()):
            sources.append({"adv_id": m.get("id"), "name": m.get("name"),
                            "source": f"spec:{spec}"})
            continue
        for raw_trait in (m.get("traits_snapshot") or []):
            if isinstance(raw_trait, str):
                trait_slug = raw_trait
            elif isinstance(raw_trait, dict):
                trait_slug = (
                    raw_trait.get("slug")
                    or raw_trait.get("code")
                    or raw_trait.get("name")
                )
            else:
                trait_slug = None
            if not trait_slug:
                continue
            if trait_slug not in trait_counter_cache:
                tdoc = await db.adventurer_traits.find_one(
                    {"$or": [
                        {"slug": trait_slug},
                        {"code": trait_slug},
                        {"name": trait_slug},
                    ]},
                    {"_id": 0, "counter_tags": 1},
                )
                trait_counter_cache[trait_slug] = (
                    set(tdoc.get("counter_tags") or []) if tdoc else set()
                )
            if counters_for_threat & trait_counter_cache.get(
                trait_slug,
                set(),
            ):
                sources.append({"adv_id": m.get("id"), "name": m.get("name"),
                                "source": f"trait:{trait_slug}"})
                break
    return sources


def _injury_risk_band(counter_ratio: float, has_threats: bool) -> str:
    """Bucket the counter ratio into a high-level risk label."""
    if not has_threats:
        return "low"
    if counter_ratio < 0.34:
        return "high"
    if counter_ratio < 0.67:
        return "medium"
    return "low"


async def build_dungeon_preview(db, *, guild: dict, slug: str,
                                 team_ids: list[str]) -> dict[str, Any]:
    d = apply_dungeon_encounter(
        await db.dungeons.find_one({"slug": slug}, {"_id": 0})
    )
    if not d:
        return {"error": "not_found"}

    # Resolve team adventurer docs (only members owned by the guild).
    team: list[dict] = []
    if team_ids:
        team = [a async for a in db.adventurers.find(
            {"guild_id": guild["id"], "id": {"$in": team_ids}},
            {"_id": 0},
        )]

    # Team power + success_chance baseline.
    members_for_power: list[dict] = []
    for adventurer in team:
        _slots, equipment_power, raw_equipment = (
            await _load_equipment_for_adventurer(db, adventurer["id"])
        )
        equipped_items = [row["item"] for row in raw_equipment]
        mechanic = resolve_class_mechanic(
            adventurer=adventurer,
            equipment_items=equipped_items,
        )
        members_for_power.append({
            **adventurer,
            "traits_snapshot": (
                adventurer.get("traits_snapshot")
                or adventurer.get("traits")
                or []
            ),
            "equipment_power_snapshot": equipment_power,
            "class_mechanic_id": mechanic.get("mechanic_id"),
            "class_mechanic_counter_tags": mechanic.get(
                "active_counter_tags",
                [],
            ),
            "class_mechanic_power_bonus": int(
                mechanic.get("power_bonus", 0)
            ),
            "total_power_snapshot": (
                adventurer_effective_power(adventurer)
                + equipment_power
                + int(mechanic.get("power_bonus", 0))
            ),
        })
    team_power = compute_team_power(members_for_power) if team else 0
    base_success = compute_success_chance(team_power, d.get("recommended_power") or 100) \
        if team else 0

    # Threat resolution (cap +12% / -8% on Void/Undead only).
    # FASE 2 — satura al nuovo massimo (100, non più 95).
    from app.shared.constants import SUCCESS_CHANCE_MAX
    tr = await compute_threat_resolution(
        db, team_members=members_for_power, dungeon=d)
    bonus = int(tr.get("success_bonus_pct", 0)) if tr.get("applies") else 0
    success_chance = min(base_success + bonus, SUCCESS_CHANCE_MAX) if team else 0

    # Threats matrix with sources.
    threats_payload = []
    threat_tags = d.get("threat_tags") or []
    for t_slug in threat_tags:
        sources = await _resolve_counter_sources(
            db,
            t_slug,
            members_for_power,
        )
        threats_payload.append({
            "slug": t_slug,
            "name_it": THREAT_NAME_IT.get(t_slug, t_slug),
            "name_en": THREAT_NAME_EN.get(t_slug, t_slug),
            "countered": len(sources) > 0,
            "by": sources,
        })

    # Injury risk band.
    risk = _injury_risk_band(tr.get("counter_ratio", 0.0) if tr.get("applies") else 1.0,
                              bool(threat_tags))

    # Rewards preview (sample only — no spoilers on formulas).
    gold_min = int((d.get("rewards_gold_min") or 0))
    gold_max = int((d.get("rewards_gold_max") or 0))
    xp_min = int((d.get("rewards_xp_min") or 0))
    xp_max = int((d.get("rewards_xp_max") or 0))
    item_sample = [it.get("slug") for it in (d.get("loot_table") or [])][:5]
    mat_sample = [m.get("slug") for m in (d.get("material_drop_table") or [])][:5]

    # Bilingual weakness suggestion.
    weak_it: str | None = None
    weak_en: str | None = None
    uncovered = [t for t in threats_payload if not t["countered"]]
    if team and uncovered:
        names_it = ", ".join(t["name_it"] for t in uncovered)
        names_en = ", ".join(t["name_en"] for t in uncovered)
        weak_it = (f"Squadra debole contro {len(uncovered)} minacce: {names_it}. "
                   "Aggiungi un avventuriero con la specializzazione adeguata.")
        weak_en = (f"Party weak against {len(uncovered)} threat(s): {names_en}. "
                   "Add an adventurer with the matching specialization.")

    return {
        "dungeon": {
            "slug": d.get("slug"),
            "name_it": d.get("name_it") or d.get("name"),
            "name_en": d.get("name_en") or d.get("name"),
            "difficulty": d.get("difficulty"),
            "duration_seconds": d.get("base_duration_seconds"),
            "recommended_power": d.get("recommended_power"),
            "required_level": d.get("required_level"),
            "encounter_type": d.get("encounter_type"),
            "progression_bucket": d.get("bucket"),
            "encounter_phases": d.get("encounter_phases") or [],
        },
        "team_power": int(team_power),
        "success_chance": int(success_chance),
        "threats": threats_payload,
        "threat_resolution": tr if tr.get("applies") else None,
        "injury_risk": risk,
        "rewards_preview": {
            "gold_range": [gold_min, gold_max],
            "xp_range": [xp_min, xp_max],
            "items_sample": item_sample,
            "materials_sample": mat_sample,
            "profile": d.get("reward_profile"),
        },
        "weakness_suggestion_it": weak_it,
        "weakness_suggestion_en": weak_en,
        "caps_info": {
            "success_bonus_cap_pct": SUCCESS_BONUS_CAP_PCT,
            "injury_reduction_cap_pct": INJURY_REDUCTION_CAP_PCT,
        },
    }
