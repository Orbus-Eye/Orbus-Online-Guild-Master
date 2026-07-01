"""Phase 14.3-c — Italian trait catalog (10 canonical traits).

These are the public, player-facing traits exposed in roster, recruitment
and expedition previews. Each entry carries:
  - code:              stable snake_case identifier (DB primary handle)
  - display_name:      Italian player-facing label
  - display_name_en:   English fallback (used by i18n contentMap)
  - description:       Italian short text
  - description_en:    English fallback
  - rarity:            common | uncommon | rare | epic
  - polarity:          positive | negative | mixed
  - modifier_type:     "flat" | "percent" | null (no mechanical effect)
  - affected_stat:     stat code (or null for purely narrative traits)
  - modifier_value:    numeric delta
  - is_positive:       legacy flag, kept for backward compatibility

The seeder (`seed_italian_traits` in seed_runner.py) upserts these by
`code`, and stamps `is_test=False is_active=True`. Re-running is a no-op.
"""

ITALIAN_TRAIT_SEED = [
    {
        "code": "lucky",
        "display_name": "Fortunato",
        "display_name_en": "Lucky",
        "description": "Una stella gentile guida i suoi passi: bottino e tiri favorevoli vengono più spesso.",
        "description_en": "A kind star guides their steps: more frequent loot and lucky rolls.",
        "rarity": "uncommon",
        "polarity": "positive",
        "modifier_type": "percent",
        "affected_stat": "xp_gain",
        "modifier_value": 5.0,
        "is_positive": True,
    },
    {
        "code": "brave",
        "display_name": "Coraggioso",
        "display_name_en": "Brave",
        "description": "Saldo sotto pressione, mantiene la posizione anche quando gli altri esitano.",
        "description_en": "Steady under pressure, holds the line when others hesitate.",
        "rarity": "common",
        "polarity": "positive",
        "modifier_type": "flat",
        "affected_stat": "strength",
        "modifier_value": 1.0,
        "is_positive": True,
    },
    {
        "code": "disciplined",
        "display_name": "Disciplinato",
        "display_name_en": "Disciplined",
        "description": "Allenamento metodico: pochi sprechi di movimento, più resistenza nelle run lunghe.",
        "description_en": "Methodical training: fewer wasted moves, better endurance on long runs.",
        "rarity": "uncommon",
        "polarity": "positive",
        "modifier_type": "flat",
        "affected_stat": "endurance",
        "modifier_value": 2.0,
        "is_positive": True,
    },
    {
        "code": "sharp_eye",
        "display_name": "Occhio Acuto",
        "display_name_en": "Sharp Eye",
        "description": "Coglie aperture e dettagli che agli altri sfuggono. Vantaggio nelle imboscate.",
        "description_en": "Spots openings and details others miss. Edge during ambushes.",
        "rarity": "common",
        "polarity": "positive",
        "modifier_type": "flat",
        "affected_stat": "agility",
        "modifier_value": 1.0,
        "is_positive": True,
    },
    {
        "code": "reckless",
        "display_name": "Avventato",
        "display_name_en": "Reckless",
        "description": "Più danno inflitto, ma anche più ferite subite. Doppio taglio.",
        "description_en": "Hits harder, but takes more wounds. Double-edged.",
        "rarity": "rare",
        "polarity": "mixed",
        "modifier_type": "flat",
        "affected_stat": "strength",
        "modifier_value": 2.0,
        "is_positive": True,
    },
    {
        "code": "fragile",
        "display_name": "Fragile",
        "display_name_en": "Fragile",
        "description": "Costituzione delicata. Si stanca prima e rischia ferite più gravi.",
        "description_en": "Delicate constitution. Tires sooner and risks worse injuries.",
        "rarity": "common",
        "polarity": "negative",
        "modifier_type": "flat",
        "affected_stat": "endurance",
        "modifier_value": -2.0,
        "is_positive": False,
    },
    {
        "code": "greedy",
        "display_name": "Avido",
        "display_name_en": "Greedy",
        "description": "Più oro raccolto dai dungeon, ma compagni meno disposti a coprirgli le spalle.",
        "description_en": "Squeezes more gold from a run, but allies trust them less.",
        "rarity": "uncommon",
        "polarity": "mixed",
        "modifier_type": "flat",
        "affected_stat": "agility",
        "modifier_value": 0.0,
        "is_positive": True,
    },
    {
        "code": "loyal",
        "display_name": "Leale",
        "display_name_en": "Loyal",
        "description": "Non diserta mai, alza il morale della squadra nei momenti difficili.",
        "description_en": "Never deserts, lifts party morale in dark hours.",
        "rarity": "uncommon",
        "polarity": "positive",
        "modifier_type": "flat",
        "affected_stat": "faith",
        "modifier_value": 1.0,
        "is_positive": True,
    },
    {
        "code": "clumsy",
        "display_name": "Goffo",
        "display_name_en": "Clumsy",
        "description": "Inciampa nei momenti peggiori. Riduce schivata ed efficacia in trappola.",
        "description_en": "Stumbles at the worst times. Lowers dodge and trap handling.",
        "rarity": "common",
        "polarity": "negative",
        "modifier_type": "flat",
        "affected_stat": "agility",
        "modifier_value": -1.0,
        "is_positive": False,
    },
    {
        "code": "inspired",
        "display_name": "Ispirato",
        "display_name_en": "Inspired",
        "description": "Si nutre delle vittorie altrui: guadagna più esperienza con il party.",
        "description_en": "Feeds on group wins: gains more XP when adventuring with a party.",
        "rarity": "rare",
        "polarity": "positive",
        "modifier_type": "percent",
        "affected_stat": "xp_gain",
        "modifier_value": 10.0,
        "is_positive": True,
    },
]


__all__ = ["ITALIAN_TRAIT_SEED"]
