"""FASE 9E — contratto dei 108 set raid di classe (27 × 4, 540 pezzi)."""
from collections import Counter

from app.classes import CLASS_REGISTRY, role_focus_stats
from app.raids.class_sets import (
    RAID_CLASS_SET_ITEMS,
    RAID_CLASS_SETS,
    SET_FULL_PIECES,
    SET_PARTIAL_PIECES,
    active_set_bonuses,
    class_sets_public,
    set_bonus_power,
    set_bonus_stats,
)
from app.rewards.source_engine import evaluate_reward_eligibility
from app.shared.content_curve import RAID_CURVE

RAIDS = ("moonfall-vigil", "broken-bastion-siege",
         "necropolis-bells", "dragon-vault")


def test_108_set_completi():
    assert len(RAID_CLASS_SETS) == 27 * 4 == 108
    per_class = Counter(d.class_slug for d in RAID_CLASS_SETS.values())
    per_raid = Counter(d.raid_slug for d in RAID_CLASS_SETS.values())
    assert set(per_class) == set(CLASS_REGISTRY)
    assert all(count == 4 for count in per_class.values())
    assert set(per_raid) == set(RAIDS)
    assert all(count == 27 for count in per_raid.values())


def test_540_pezzi_su_slot_canonici():
    assert len(RAID_CLASS_SET_ITEMS) == 540
    slots = Counter(item["slot_type"] for item in RAID_CLASS_SET_ITEMS)
    assert slots == {"weapon": 108, "chest": 108, "legs": 108,
                     "head": 108, "accessory": 108}
    # Nessuno slot inventato: 5 pezzi per set.
    for definition in RAID_CLASS_SETS.values():
        assert len(definition.piece_slugs) == SET_FULL_PIECES


def test_nomi_slug_id_unici():
    for field in ("slug", "id", "display_name_it"):
        values = [item[field] for item in RAID_CLASS_SET_ITEMS]
        assert len(set(values)) == len(values), f"duplicati in {field}"
    names = [d.name_it for d in RAID_CLASS_SETS.values()]
    assert len(set(names)) == 108


def test_progressione_reale_tra_i_tier():
    for class_slug in CLASS_REGISTRY:
        rows = class_sets_public(class_slug)
        assert [r["tier"] for r in rows] == [1, 2, 3, 4]
        levels = [r["required_level"] for r in rows]
        assert levels == sorted(levels) and len(set(levels)) == 4
        bonuses = [sum(r["bonus_full"].values()) for r in rows]
        assert bonuses == sorted(bonuses)
    # Anche il budget stat per pezzo cresce col tier.
    budget_by_tier = {}
    for item in RAID_CLASS_SET_ITEMS:
        total = sum(
            item[f"{s}_bonus"] for s in
            ("strength", "agility", "intellect", "endurance", "faith")
        )
        budget_by_tier.setdefault(item["set_tier"], set()).add(total)
    tiers = sorted(budget_by_tier)
    maxima = [max(budget_by_tier[t]) for t in tiers]
    assert maxima == sorted(maxima)


def test_stat_allineate_al_ruolo_fisso():
    for definition in RAID_CLASS_SETS.values():
        focus, secondary = role_focus_stats(definition.class_slug)
        assert definition.focus_stat == focus
        assert definition.secondary_stat == secondary
        assert list(definition.bonus_partial) == [focus]
    # TANK → endurance, HEALER → faith, DPS → stat primaria della classe.
    assert RAID_CLASS_SETS["set_dragon-vault_paladino"].focus_stat == "endurance"
    assert RAID_CLASS_SETS["set_dragon-vault_bardo"].focus_stat == "faith"
    assert RAID_CLASS_SETS["set_dragon-vault_mago"].focus_stat == "intellect"


def test_ogni_pezzo_e_class_locked_e_droppa_dal_suo_raid():
    for item in RAID_CLASS_SET_ITEMS:
        assert item["required_class_optional"] in CLASS_REGISTRY
        assert item["source"].startswith("raid:")
        source = item["acquisition_sources"][0]
        assert source["source_type"] == "raid"
        assert source["source_slug"] in RAIDS
        level = RAID_CURVE[source["source_slug"]].required_level
        assert item["required_adventurer_level"] == level
        # Il pezzo è eleggibile nel motore ricompense del SUO raid.
        verdict = evaluate_reward_eligibility(
            item=item,
            source_policy_id=source["source_policy_id"],
            adventurer_level=level,
        )
        assert verdict["eligible"], (item["slug"], verdict["reasons"])


def test_bonus_set_parziale_e_completo():
    definition = RAID_CLASS_SETS["set_moonfall-vigil_guerriero"]
    pieces = [
        {"set_id": definition.set_id, "slug": slug}
        for slug in definition.piece_slugs
    ]
    assert set_bonus_stats(pieces[:2]) == {}          # sotto soglia
    partial = set_bonus_stats(pieces[:SET_PARTIAL_PIECES])
    assert partial == definition.bonus_partial
    full = set_bonus_stats(pieces)
    assert full == definition.bonus_full
    assert set_bonus_power(pieces) == sum(definition.bonus_full.values())
    # Pezzi duplicati dello stesso slot non contano due volte.
    assert set_bonus_stats([pieces[0], pieces[0], pieces[1]]) == {}
    summary = active_set_bonuses(pieces[:3])
    assert summary[0]["pieces_equipped"] == 3
    assert summary[0]["active_bonus"] == definition.bonus_partial


def test_item_estranei_non_attivano_nulla():
    assert set_bonus_stats([{"slug": "t6_universale_weapon_001"}]) == {}
    assert set_bonus_power([]) == 0
