"""FASE 3.1 (2026-08-08) — Un reagente principale per dungeon/raid.

Sostituisce (per i contenuti mappati) il roll a tier condiviso di
`material_drop_tables.py`: ogni dungeon fa cadere SOLO il suo reagente,
coerente con la lore, così "dove trovo X?" ha sempre una risposta e i
dungeon vecchi restano farm utili (l'Overpower di Fase 2 moltiplica le
quantità). I reagenti più rari vivono SOLO nei raid, garantiti a
vittoria. Design: memory/fase3_design_reagenti_crafting.md §1.

Tabelle pure (nessun I/O) → unit-testabili senza Mongo.
"""
from __future__ import annotations

import secrets

_rng = secrets.SystemRandom()


# Rate/qty per fascia di rarità del reagente principale (dungeon).
_RARITY_PROFILE: dict[str, tuple[float, tuple[int, int]]] = {
    # rarity → (drop_rate a successo, (qty_min, qty_max))
    "common": (0.60, (1, 3)),
    "uncommon": (0.50, (1, 2)),
    "rare": (0.35, (1, 2)),
    "epic": (0.22, (1, 1)),
}

# Dungeon slug → (material_slug, rarity). UNIVOCA per dungeon.
DUNGEON_PRIMARY_REAGENT: dict[str, tuple[str, str]] = {
    # ── comuni (base della Fucina/Cucina) ────────────────────────────
    "training-yard": ("iron_shard", "common"),
    "goblin-warrens": ("iron_shard", "common"),
    "iron-foundry-5p": ("iron_shard", "common"),
    "sewer-nest": ("raw_leather", "common"),
    "bandit-hideout": ("raw_leather", "common"),
    "wolf-den-5p": ("raw_leather", "common"),
    "druid-grove": ("healing_herb", "common"),
    "silent-monastery-5p": ("healing_herb", "common"),
    # ── uncommon ─────────────────────────────────────────────────────
    "shadow-crypts": ("arcane_dust", "uncommon"),
    "sunken-library": ("arcane_dust", "uncommon"),
    "cursed-mines": ("dull_gem", "uncommon"),
    "pirate-fleet-5p": ("dull_gem", "uncommon"),
    "lich-sanctum": ("ossa_antiche", "uncommon"),
    "frost-cave-5p": ("ghiaccio_eterno", "uncommon"),
    "salt-marsh-5p": ("spezia_palustre", "uncommon"),
    # ── rare ─────────────────────────────────────────────────────────
    "dragons-hoard": ("scaglia_di_drago", "rare"),
    "storm-spire": ("essenza_di_tempesta", "rare"),
    "obsidian-arena-5p": ("ossidiana", "rare"),
    "clockwork-vault-5p": ("ingranaggio_arcano", "rare"),
    "voidspire-5p": ("frammento_del_vuoto", "rare"),
    # ── epic (fine linea dungeon) ────────────────────────────────────
    "infernal-pit-5p": ("cenere_infernale", "epic"),
    "celestial-citadel-5p": ("lacrima_celeste", "epic"),
    "world-tree-roots-5p": ("linfa_del_mondo", "epic"),
}

# Raid slug → (material_slug, rarity, (qty_min, qty_max) a vittoria).
# GARANTITO a vittoria; su esito parziale qty dimezzata (min 1) al 50%
# di probabilità. Nessun drop su sconfitta.
RAID_PRIMARY_REAGENT: dict[str, tuple[str, str, tuple[int, int]]] = {
    "moonfall-vigil": ("polvere_di_luna", "epic", (2, 3)),
    "broken-bastion-siege": ("nucleo_d_assedio", "epic", (2, 3)),
    "necropolis-bells": ("rintocco_spettrale", "legendary", (1, 2)),
    "dragon-vault": ("dragon_essence", "legendary", (1, 2)),
}


def primary_reagent_for_dungeon(slug: str) -> tuple[str, str] | None:
    """(material_slug, rarity) del reagente principale, o None se non mappato."""
    return DUNGEON_PRIMARY_REAGENT.get((slug or "").lower())


def roll_primary_reagent(slug: str, success: bool, *, rng=None) -> list[dict]:
    """Roll del reagente principale di un dungeon.

    Ritorna [] o [{slug, rarity, qty}] — stessa shape del roller legacy.
    Fallimento = 50% del rate (premio di consolazione).
    """
    entry = primary_reagent_for_dungeon(slug)
    if not entry:
        return []
    material_slug, rarity = entry
    rate, (qmin, qmax) = _RARITY_PROFILE[rarity]
    roller = rng or _rng
    effective = rate if success else rate * 0.5
    if roller.random() >= effective:
        return []
    return [{"slug": material_slug, "rarity": rarity,
             "qty": roller.randint(qmin, qmax)}]


def raid_reagent_grant(slug: str, outcome: str, *, rng=None) -> list[dict]:
    """Reagente del raid: garantito a vittoria, 50%/qty ridotta su parziale.

    `outcome` ∈ {"victory", "partial", altro} — altro = nessun drop.
    """
    entry = RAID_PRIMARY_REAGENT.get((slug or "").lower())
    if not entry:
        return []
    material_slug, rarity, (qmin, qmax) = entry
    roller = rng or _rng
    if outcome == "victory":
        return [{"slug": material_slug, "rarity": rarity,
                 "qty": roller.randint(qmin, qmax)}]
    if outcome == "partial":
        if roller.random() < 0.5:
            return [{"slug": material_slug, "rarity": rarity,
                     "qty": max(1, qmin // 2 or 1)}]
    return []


__all__ = [
    "DUNGEON_PRIMARY_REAGENT",
    "RAID_PRIMARY_REAGENT",
    "primary_reagent_for_dungeon",
    "roll_primary_reagent",
    "raid_reagent_grant",
]
