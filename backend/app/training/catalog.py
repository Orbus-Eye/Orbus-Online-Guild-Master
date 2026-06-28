"""ROUND 6C — Specialization catalog (static, server-authoritative).

Two parallel datasets:

* `SPEC_DEFINITIONS`  — 10 hybrid specs with:
    - eligible class slugs (1-3 classes per spec)
    - tier (`starter` | `full`)
    - additive stat modifiers (+2 main / +1 secondary; NO percentages, NO P2W)
    - signature_item_slug → resolves into `SPEC_SIGNATURE_ITEMS`

* `SPEC_SIGNATURE_ITEMS` — catalog of the "free, generated on-apply" items
  that get bound to the adventurer (`bound_to_adventurer_id`,
  `bound_reason="specialization_signature"`).

Tier unlock rules (Q7b decision):
  Training Grounds Lv 1-2  → starter tier (4 specs)
  Training Grounds Lv 3-6  → full tier (10 specs)
  Training Grounds Lv 4-6  → placeholder for future Round 6D+ master variants

Apply cost (Q7b decision):
  Lv1: 500 gold
  Lv2: 400 gold (sconto)
  Lv3+: 1500 gold (full tier)

Required adventurer level (Q6 decision): 5
"""
from __future__ import annotations


MIN_ADVENTURER_LEVEL = 5  # Q6 decision

# Training Grounds level → which spec tier unlocks
# Returns one of {"starter", "full"} or None if not yet unlocked.
def tier_for_training_level(level: int) -> str | None:
    if level <= 0:
        return None
    if level <= 2:
        return "starter"
    return "full"  # Lv 3-6


def apply_cost_for_training_level(level: int) -> int:
    """Gold cost to apply a specialization at this training_grounds level."""
    if level <= 0:
        return 0  # gate-locked at the require_unlocked layer; defensive 0
    if level == 1:
        return 500
    if level == 2:
        return 400   # Lv2 sconto starter tier
    return 1500      # Lv3+ full tier


# ─── Spec catalog ────────────────────────────────────────────────────────────
# Each entry has:
#   slug, name_it, name_en, role, tier, eligible_classes (list of class slugs),
#   modifiers (dict of stat → +int), signature_item_slug

SPEC_DEFINITIONS: list[dict] = [
    # ─── Starter (Tier 1) ────────────────────────────────────────────────────
    {
        "slug": "spec_difensore",
        "name_it": "Difensore",
        "name_en": "Defender",
        "role": "Tank",
        "tier": "starter",
        "eligible_classes": ["warrior", "paladin"],
        "modifiers": {"endurance": 2, "strength": 1},
        "signature_item_slug": "spec_signature_aegis_of_the_defender",
        "description_it": "Reggi la linea. +2 END, +1 STR.",
        "description_en": "Hold the line. +2 END, +1 STR.",
    },
    {
        "slug": "spec_cecchino",
        "name_it": "Cecchino",
        "name_en": "Marksman",
        "role": "DPS",
        "tier": "starter",
        "eligible_classes": ["ranger", "rogue"],
        "modifiers": {"agility": 2, "intellect": 1},
        "signature_item_slug": "spec_signature_truestrike_bow",
        "description_it": "Il colpo che decide. +2 AGI, +1 INT.",
        "description_en": "The shot that decides. +2 AGI, +1 INT.",
    },
    {
        "slug": "spec_restauratore",
        "name_it": "Restauratore",
        "name_en": "Restorer",
        "role": "Healer",
        "tier": "starter",
        "eligible_classes": ["priest", "druid"],
        "modifiers": {"faith": 2, "intellect": 1},
        "signature_item_slug": "spec_signature_sacred_chalice",
        "description_it": "Cura profonda. +2 FAI, +1 INT.",
        "description_en": "Deep mend. +2 FAI, +1 INT.",
    },
    {
        "slug": "spec_stratega",
        "name_it": "Stratega",
        "name_en": "Strategist",
        "role": "Support",
        "tier": "starter",
        "eligible_classes": ["bard", "paladin"],
        "modifiers": {"intellect": 1, "faith": 1, "endurance": 1},
        "signature_item_slug": "spec_signature_battle_standard",
        "description_it": "La squadra che vince è quella che pianifica. +1 INT, +1 FAI, +1 END.",
        "description_en": "Wins favor the prepared. +1 INT, +1 FAI, +1 END.",
    },
    # ─── Full Hybrid (Tier 2, Training Lv 3+) ────────────────────────────────
    {
        "slug": "spec_furia",
        "name_it": "Furia",
        "name_en": "Frenzy",
        "role": "DPS",
        "tier": "full",
        "eligible_classes": ["warrior", "berserker"],
        "modifiers": {"strength": 2, "agility": 1},
        "signature_item_slug": "spec_signature_bloodied_greataxe",
        "description_it": "Forza bruta e velocità. +2 STR, +1 AGI.",
        "description_en": "Brute force and speed. +2 STR, +1 AGI.",
    },
    {
        "slug": "spec_distruttore",
        "name_it": "Distruttore",
        "name_en": "Destroyer",
        "role": "DPS",
        "tier": "full",
        "eligible_classes": ["berserker", "monk"],
        "modifiers": {"strength": 2, "endurance": 1},
        "signature_item_slug": "spec_signature_breakers_gauntlets",
        "description_it": "Frantumi tutto. +2 STR, +1 END.",
        "description_en": "Break everything. +2 STR, +1 END.",
    },
    {
        "slug": "spec_assassino",
        "name_it": "Assassino",
        "name_en": "Assassin",
        "role": "DPS",
        "tier": "full",
        "eligible_classes": ["rogue", "assassin"],
        "modifiers": {"agility": 3},
        "signature_item_slug": "spec_signature_silent_kris",
        "description_it": "Un solo colpo. +3 AGI.",
        "description_en": "One single strike. +3 AGI.",
    },
    {
        "slug": "spec_arcanista",
        "name_it": "Arcanista",
        "name_en": "Arcanist",
        "role": "DPS",
        "tier": "full",
        "eligible_classes": ["mage", "necromancer"],
        "modifiers": {"intellect": 2, "faith": 1},
        "signature_item_slug": "spec_signature_runed_focus",
        "description_it": "Padronanza arcana. +2 INT, +1 FAI.",
        "description_en": "Arcane mastery. +2 INT, +1 FAI.",
    },
    {
        "slug": "spec_elementalista",
        "name_it": "Elementalista",
        "name_en": "Elementalist",
        "role": "DPS",
        "tier": "full",
        "eligible_classes": ["mage", "druid"],
        "modifiers": {"intellect": 2, "endurance": 1},
        "signature_item_slug": "spec_signature_storm_rod",
        "description_it": "Tempesta e fuoco. +2 INT, +1 END.",
        "description_en": "Storm and fire. +2 INT, +1 END.",
    },
    {
        "slug": "spec_cantore_di_battaglia",
        "name_it": "Cantore di Battaglia",
        "name_en": "Battle Chanter",
        "role": "Support",
        "tier": "full",
        "eligible_classes": ["bard"],
        "modifiers": {"strength": 1, "agility": 1, "faith": 1},
        "signature_item_slug": "spec_signature_warhorn",
        "description_it": "Il canto che spinge in battaglia. +1 STR, +1 AGI, +1 FAI.",
        "description_en": "A song that drives the charge. +1 STR, +1 AGI, +1 FAI.",
    },
    # ROUND 6E — 4 hybrid specs aggiuntive (TG Lv3 / Full tier)
    {
        "slug": "spec_paladino_oscuro",
        "name_it": "Paladino Oscuro",
        "name_en": "Dark Paladin",
        "role": "Tank/DPS",
        "tier": "full",
        # Warlock non esiste fra le 12 classi di gioco — il flavour caster
        # offensivo è coperto da Necromancer + Mage.
        "eligible_classes": ["necromancer", "mage"],
        "modifiers": {"intellect": 2, "strength": 1},
        "signature_item_slug": "spec_signature_corrupted_blade",
        "description_it": "Magia oscura intrisa di acciaio. +2 INT, +1 STR.",
        "description_en": "Dark magic laced with steel. +2 INT, +1 STR.",
    },
    {
        "slug": "spec_difensore_della_natura",
        "name_it": "Difensore della Natura",
        "name_en": "Warden of Nature",
        "role": "Tank/Support",
        "tier": "full",
        "eligible_classes": ["druid", "ranger"],
        "modifiers": {"endurance": 2, "faith": 1},
        "signature_item_slug": "spec_signature_thornwood_shield",
        "description_it": "La foresta ti protegge. +2 END, +1 FAI.",
        "description_en": "The forest shields you. +2 END, +1 FAI.",
    },
    {
        "slug": "spec_maestro_di_armi",
        "name_it": "Maestro d'Armi",
        "name_en": "Weapon Master",
        "role": "DPS",
        "tier": "full",
        "eligible_classes": ["warrior", "berserker"],
        "modifiers": {"strength": 2, "agility": 1},
        "signature_item_slug": "spec_signature_twin_blades",
        "description_it": "Maestria con ogni lama. +2 STR, +1 AGI.",
        "description_en": "Mastery of every blade. +2 STR, +1 AGI.",
    },
    {
        "slug": "spec_guardiano_runico",
        "name_it": "Guardiano Runico",
        "name_en": "Runic Guardian",
        "role": "Tank/Caster",
        "tier": "full",
        "eligible_classes": ["mage", "paladin"],
        "modifiers": {"endurance": 2, "intellect": 1},
        "signature_item_slug": "spec_signature_runic_aegis",
        "description_it": "Rune incise sulla carne. +2 END, +1 INT.",
        "description_en": "Runes carved into flesh. +2 END, +1 INT.",
    },
]


# Signature items generated on-apply.
# Each yields one inventory row with `bound_to_adventurer_id` set and
# `bound_reason="specialization_signature"`. NOT redeemable on Auction/Shop.
SPEC_SIGNATURE_ITEMS: dict[str, dict] = {
    "spec_signature_aegis_of_the_defender": {
        "slug": "spec_signature_aegis_of_the_defender",
        "name_it": "Egida del Difensore",
        "name_en": "Aegis of the Defender",
        "rarity": "Rare",
        "slot": "shield",
        "endurance_bonus": 3,
        "strength_bonus": 1,
        "power_score": 4,
    },
    "spec_signature_truestrike_bow": {
        "slug": "spec_signature_truestrike_bow",
        "name_it": "Arco del Colpo Vero",
        "name_en": "Truestrike Bow",
        "rarity": "Rare",
        "slot": "weapon",
        "agility_bonus": 3,
        "intellect_bonus": 1,
        "power_score": 4,
    },
    "spec_signature_sacred_chalice": {
        "slug": "spec_signature_sacred_chalice",
        "name_it": "Calice Sacro",
        "name_en": "Sacred Chalice",
        "rarity": "Rare",
        "slot": "accessory",
        "faith_bonus": 3,
        "intellect_bonus": 1,
        "power_score": 4,
    },
    "spec_signature_battle_standard": {
        "slug": "spec_signature_battle_standard",
        "name_it": "Stendardo da Battaglia",
        "name_en": "Battle Standard",
        "rarity": "Rare",
        "slot": "accessory",
        "intellect_bonus": 2,
        "faith_bonus": 1,
        "endurance_bonus": 1,
        "power_score": 4,
    },
    "spec_signature_bloodied_greataxe": {
        "slug": "spec_signature_bloodied_greataxe",
        "name_it": "Grand'Ascia Insanguinata",
        "name_en": "Bloodied Greataxe",
        "rarity": "Epic",
        "slot": "weapon",
        "strength_bonus": 3,
        "agility_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_breakers_gauntlets": {
        "slug": "spec_signature_breakers_gauntlets",
        "name_it": "Manopole del Sfondatore",
        "name_en": "Breaker's Gauntlets",
        "rarity": "Epic",
        "slot": "armor",
        "strength_bonus": 3,
        "endurance_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_silent_kris": {
        "slug": "spec_signature_silent_kris",
        "name_it": "Kris Silente",
        "name_en": "Silent Kris",
        "rarity": "Epic",
        "slot": "weapon",
        "agility_bonus": 4,
        "intellect_bonus": 1,
        "power_score": 5,
    },
    "spec_signature_runed_focus": {
        "slug": "spec_signature_runed_focus",
        "name_it": "Focus Runico",
        "name_en": "Runed Focus",
        "rarity": "Epic",
        "slot": "accessory",
        "intellect_bonus": 3,
        "faith_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_storm_rod": {
        "slug": "spec_signature_storm_rod",
        "name_it": "Bastone della Tempesta",
        "name_en": "Storm Rod",
        "rarity": "Epic",
        "slot": "weapon",
        "intellect_bonus": 3,
        "endurance_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_warhorn": {
        "slug": "spec_signature_warhorn",
        "name_it": "Corno di Guerra",
        "name_en": "Warhorn",
        "rarity": "Epic",
        "slot": "accessory",
        "strength_bonus": 2,
        "agility_bonus": 2,
        "faith_bonus": 2,
        "power_score": 5,
    },
    # ROUND 6E — 4 signature items for the new hybrid specs (Epic, slot-balanced)
    "spec_signature_corrupted_blade": {
        "slug": "spec_signature_corrupted_blade",
        "name_it": "Lama Corrotta",
        "name_en": "Corrupted Blade",
        "rarity": "Epic",
        "slot": "weapon",
        "intellect_bonus": 3,
        "strength_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_thornwood_shield": {
        "slug": "spec_signature_thornwood_shield",
        "name_it": "Scudo di Spinalegno",
        "name_en": "Thornwood Shield",
        "rarity": "Epic",
        "slot": "shield",
        "endurance_bonus": 3,
        "faith_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_twin_blades": {
        "slug": "spec_signature_twin_blades",
        "name_it": "Lame Gemelle",
        "name_en": "Twin Blades",
        "rarity": "Epic",
        "slot": "weapon",
        "strength_bonus": 3,
        "agility_bonus": 2,
        "power_score": 5,
    },
    "spec_signature_runic_aegis": {
        "slug": "spec_signature_runic_aegis",
        "name_it": "Egida Runica",
        "name_en": "Runic Aegis",
        "rarity": "Epic",
        "slot": "armor",
        "endurance_bonus": 3,
        "intellect_bonus": 2,
        "power_score": 5,
    },
}


# Pre-computed lookup tables for O(1) access in hot paths.
SPEC_BY_SLUG: dict[str, dict] = {s["slug"]: s for s in SPEC_DEFINITIONS}


def specs_for_class_and_tier(class_slug: str, tier: str) -> list[dict]:
    """Return spec definitions eligible for `class_slug` at unlock `tier` or below."""
    allowed_tiers = {"starter"} if tier == "starter" else {"starter", "full"}
    return [
        s for s in SPEC_DEFINITIONS
        if class_slug in s["eligible_classes"] and s["tier"] in allowed_tiers
    ]


def apply_specialization_modifiers(stats: dict, spec: dict | None) -> dict:
    """Apply additive specialization modifiers to a stats dict (pre-sum).

    Mirrors the trait-modifier pattern in `expeditions/formulas.py` so power
    computations remain a clean fold over (base → traits → spec → equip).
    """
    if not spec or not spec.get("modifiers"):
        return stats
    mods = spec["modifiers"]
    return {k: int(v) + int(mods.get(k, 0)) for k, v in stats.items()}


__all__ = [
    "MIN_ADVENTURER_LEVEL",
    "SPEC_DEFINITIONS",
    "SPEC_BY_SLUG",
    "SPEC_SIGNATURE_ITEMS",
    "apply_cost_for_training_level",
    "apply_specialization_modifiers",
    "specs_for_class_and_tier",
    "tier_for_training_level",
]
