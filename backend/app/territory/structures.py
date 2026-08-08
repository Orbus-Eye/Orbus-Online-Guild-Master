"""ROUND 6B.1 — Structures catalog + defaults.

Single source of truth for the 11 guild structures: id, max_level,
prerequisites, dormitory cap formula, and the "legacy" sentinel for
levels reachable only via the historical migration script.
"""
from __future__ import annotations

# 11 structures. `default_unlocked_level=1` for the 3 starter buildings,
# `0` (locked) for the rest. `max_level=6` standard; dormitories has Lv7
# reachable ONLY via the migration script (Legacy Wing for top accounts).
STRUCTURE_CATALOG: dict[str, dict] = {
    "guild_hall": {
        "max_level": 6,
        "default_level": 1,
        "default_unlocked": True,
        "prerequisites": {},  # core structure
        "name_it": "Sala della Gilda",
        "name_en": "Guild Hall",
    },
    "dormitories": {
        # ROUND 11.2 TASK 4 — extended to Lv11 (cap 100). Legacy Lv7 (cap 50)
        # is no longer a migration-only sentinel: it is now a regular
        # purchasable level on a progressive cost curve. `max_legacy_level`
        # is removed; the migration script remains compatible because all
        # historical Lv7 docs are still valid in the catalog.
        "max_level": 11,
        "default_level": 1,
        "default_unlocked": True,
        "prerequisites": {},
        "name_it": "Dormitori",
        "name_en": "Dormitories",
    },
    "expedition_board": {
        "max_level": 6,
        "default_level": 1,
        "default_unlocked": True,
        "prerequisites": {},
        "name_it": "Bacheca Spedizioni",
        "name_en": "Expedition Board",
    },
    "war_room": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 2},
        "name_it": "Sala della Guerra",
        "name_en": "War Room",
    },
    "market_stall": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 1},
        "name_it": "Banco del Mercato",
        "name_en": "Market Stall",
    },
    "auction_house": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 2},
        "name_it": "Casa d'Aste",
        "name_en": "Auction House",
    },
    "workshop": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 2},
        "name_it": "Officina",
        "name_en": "Workshop",
    },
    "forge": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 2, "workshop": 1},
        "name_it": "Fucina",
        "name_en": "Forge",
    },
    "consortium_hall": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 3},
        "name_it": "Sala dei Consorzi",
        "name_en": "Consortium Hall",
    },
    "communication_hall": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 2},
        "name_it": "Sala delle Comunicazioni",
        "name_en": "Communication Hall",
    },
    "training_grounds": {
        "max_level": 6,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 3, "dormitories": 2},
        "name_it": "Campo di Addestramento",
        "name_en": "Training Grounds",
        # ROUND 6C — flag cleared; specialization system live.
    },
    "contract_board": {
        # ROUND 6D — Bacheca Contratti: contracts + milestones unlock.
        # Lv1 unlocks daily + weekly + milestone Tier 1. Higher levels
        # are reserved for future expansion (additional milestones, bonus
        # reward modifiers, etc.).
        "max_level": 3,
        "default_level": 0,
        "default_unlocked": False,
        "prerequisites": {"guild_hall": 2, "expedition_board": 1},
        "name_it": "Bacheca Contratti",
        "name_en": "Contract Board",
    },
}

VALID_STRUCTURE_SLUGS = frozenset(STRUCTURE_CATALOG.keys())


# Dormitories cap formula. ROUND 11.2 TASK 4: extended to Lv11 (cap 100).
# Lv7+ is no longer migration-only; all levels follow the normal upgrade flow.
DORMITORY_CAP_BY_LEVEL: dict[int, int] = {
    0: 0,
    1: 5,
    2: 10,
    3: 15,
    4: 20,
    5: 25,
    6: 30,
    7: 40,
    8: 50,
    9: 65,
    10: 80,
    11: 100,
}


def dormitory_cap_for_level(level: int) -> int:
    return DORMITORY_CAP_BY_LEVEL.get(int(level), 0)


def required_dormitory_level_for_roster(roster_size: int) -> int:
    """Return the minimum dormitory level needed to fit `roster_size`.
    Rosters beyond the current maximum return the maximum dormitory level;
    callers still compare the actual cap and reject the overflow.
    """
    for lvl in sorted(DORMITORY_CAP_BY_LEVEL.keys()):
        if DORMITORY_CAP_BY_LEVEL[lvl] >= roster_size:
            return lvl
    return max(DORMITORY_CAP_BY_LEVEL)


def default_structures_doc() -> dict:
    """Return a fresh nested `structures` dict for a brand-new guild."""
    return {
        slug: {
            "level": meta["default_level"],
            "is_unlocked": meta["default_unlocked"],
            "purchased_at": None,
            "upgraded_at": None,
            "acquired_via": "default",  # default | purchase | migration
        }
        for slug, meta in STRUCTURE_CATALOG.items()
    }


def get_structure_max_level(slug: str, *, allow_legacy: bool = False) -> int:
    """Return max upgrade level. allow_legacy=True is migration-only and
    exposes the dormitories Lv7 override.

    ROUND 16.5.4e — HOTFIX difensivo: `slug` sconosciuti nel catalog
    (es. `library` presente nei doc `guild_structures` legacy ma
    rimosso da `STRUCTURE_CATALOG` in un refactor storico) NON devono
    più causare `KeyError`. Ritorniamo `0` come sentinel "no upgrade
    path" e logghiamo un WARN una-tantum per catch-up di data cleanup
    futuro. Nessun cambio economia/gameplay: uno slug sconosciuto con
    max_level=0 non è mai `cur_level < max_level`, quindi la
    `_public_doc` non calcola `next_level_cost` e la struttura non è
    upgradabile via user (che è il comportamento corretto).
    """
    meta = STRUCTURE_CATALOG.get(slug)
    if meta is None:
        import logging
        logging.getLogger("orbus.territory").warning(
            "get_structure_max_level: unknown structure slug %r "
            "(likely legacy doc referencing a dropped catalog slug). "
            "Returning 0 as sentinel.",
            slug,
        )
        return 0
    if allow_legacy and "max_legacy_level" in meta:
        return int(meta["max_legacy_level"])
    return int(meta["max_level"])


def get_prerequisites(slug: str) -> dict[str, int]:
    return dict(STRUCTURE_CATALOG[slug].get("prerequisites", {}))


def get_display_name(slug: str, lang: str = "it") -> str:
    meta = STRUCTURE_CATALOG.get(slug, {})
    return meta.get(f"name_{lang}", slug)


__all__ = [
    "STRUCTURE_CATALOG",
    "VALID_STRUCTURE_SLUGS",
    "DORMITORY_CAP_BY_LEVEL",
    "dormitory_cap_for_level",
    "required_dormitory_level_for_roster",
    "default_structures_doc",
    "get_structure_max_level",
    "get_prerequisites",
    "get_display_name",
]
