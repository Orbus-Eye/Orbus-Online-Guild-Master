"""ROUND 16.3 Phase 7B — Cosmetic catalog for PvP seasons.

ANTI-P2W GUARANTEE
──────────────────
Every entry in this catalog is STRICTLY DECORATIVE.
Types are limited to: title, badge, frame.
They MUST NOT confer any stat, gold, XP, loot, cap, cooldown, drop-rate
or economic advantage. Only the winner's name+profile is decorated.

They are earned exclusively via weekly leaderboard rank on each continent
and cannot be purchased with any currency. No monetization path exists.

Distribution rules (rank cutoff, cumulative — top1 owns all three):
  rank 1        → title + badge + frame  (Campione)
  rank 2..3     → badge + frame          (Podio)
  rank 4..10    → frame                  (Top 10)
  rank 11+      → nothing

The catalog covers 8 continents × 3 cosmetics = 24 items total.
"""
from __future__ import annotations

from typing import Iterator


# 8 canonical continent slugs (source of truth: `app.world.CONTINENTS_SEED`).
# Duplicated here (constant tuple) to avoid a hard import that would pull
# the full world module for a compile-time list of strings.
CONTINENT_SLUGS: tuple[str, ...] = (
    "ambash", "velur", "soe", "efreto",
    "irthe", "nathos", "ergolat", "aveol",
)

# Human-readable Italian names for narrative labels.
CONTINENT_NAMES_IT: dict[str, str] = {
    "ambash": "Ambash",
    "velur": "Velur",
    "soe": "Soe",
    "efreto": "Efreto",
    "irthe": "Irthe",
    "nathos": "Nathos",
    "ergolat": "Ergolat",
    "aveol": "Aveol",
}

# Cosmetic type → max rank eligible.
COSMETIC_TYPE_TO_MAX_RANK: dict[str, int] = {
    "title": 1,
    "badge": 3,
    "frame": 10,
}


def _entry(slug_template: str, ctype: str, name_it: str,
           description_it: str, rank_required: int) -> dict:
    return {
        "type": ctype,
        "name_it": name_it,
        "description_it": description_it,
        "rank_required": rank_required,
    }


def _build_catalog() -> dict[str, dict]:
    catalog: dict[str, dict] = {}
    for slug in CONTINENT_SLUGS:
        name = CONTINENT_NAMES_IT[slug]
        # Title — top 1 only
        catalog[f"champion_title_{slug}"] = _entry(
            f"champion_title_{slug}", "title",
            f"Campione di {name}",
            (
                f"Titolo onorifico assegnato alla gilda al primo posto "
                f"della classifica settimanale PvP di {name}. "
                "Puramente decorativo — nessun effetto su statistiche, "
                "oro, XP o loot."
            ),
            1,
        )
        # Badge — top 3
        catalog[f"champion_badge_{slug}"] = _entry(
            f"champion_badge_{slug}", "badge",
            f"Distintivo del Podio di {name}",
            (
                f"Distintivo assegnato alla top 3 della classifica "
                f"settimanale PvP di {name}. Puramente decorativo."
            ),
            3,
        )
        # Frame — top 10
        catalog[f"champion_frame_{slug}"] = _entry(
            f"champion_frame_{slug}", "frame",
            f"Cornice della Top 10 di {name}",
            (
                f"Cornice profilo assegnata alla top 10 della classifica "
                f"settimanale PvP di {name}. Puramente decorativa."
            ),
            10,
        )
    return catalog


COSMETIC_CATALOG: dict[str, dict] = _build_catalog()


def cosmetics_for_rank(continent_slug: str, rank: int) -> list[str]:
    """Return the list of cosmetic_slug awarded for a given rank on a continent.

    Cumulative: rank 1 gets title+badge+frame; rank 2-3 badge+frame;
    rank 4-10 frame; rank >10 nothing.
    """
    if continent_slug not in CONTINENT_SLUGS:
        return []
    out: list[str] = []
    if rank <= 1:
        out.append(f"champion_title_{continent_slug}")
    if rank <= 3:
        out.append(f"champion_badge_{continent_slug}")
    if rank <= 10:
        out.append(f"champion_frame_{continent_slug}")
    return out


def iter_catalog() -> Iterator[tuple[str, dict]]:
    """Iterate ``(slug, entry)`` pairs, sorted for deterministic listings."""
    yield from sorted(COSMETIC_CATALOG.items(), key=lambda x: x[0])


__all__ = [
    "CONTINENT_SLUGS",
    "CONTINENT_NAMES_IT",
    "COSMETIC_TYPE_TO_MAX_RANK",
    "COSMETIC_CATALOG",
    "cosmetics_for_rank",
    "iter_catalog",
]
