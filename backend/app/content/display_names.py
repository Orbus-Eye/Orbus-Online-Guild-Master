"""FASE 10B — nomi player-facing ITALIANI per dungeon e raid.

Unica fonte server-side per la rappresentazione IT dei nomi contenuto.
Gli slug/enum/campi API NON cambiano: qui si risolve solo il testo da
mostrare al giocatore (notifiche, report, narrativa, toast).

Fonti, in ordine di priorità:
  1. ``name_it`` già presente sul documento (seed R113 / raid round5);
  2. patch lore per slug (``app.content.lore_meta``);
  3. reverse-map nome EN canonico → slug (per documenti legacy che
     hanno persistito solo il nome inglese, es. expedition.dungeon_name);
  4. fallback: il valore originale (mai stringa vuota in UI).
"""
from __future__ import annotations

from functools import lru_cache

from app.content.lore_meta import DUNGEON_LORE_PATCHES, RAID_LORE_PATCHES


def _seed_rows_dungeons() -> list[dict]:
    # Import locale: i moduli seed sono data-only ma tenerli fuori dal
    # percorso di import di app.content evita cicli.
    from app.seeds.seed_data import DUNGEON_SEED
    from app.seeds.seed_round5 import DUNGEON_5P_SEED

    return [*DUNGEON_SEED, *DUNGEON_5P_SEED]


def _seed_rows_raids() -> list[dict]:
    from app.seeds.seed_round5 import RAID_DUNGEON_SEED

    return list(RAID_DUNGEON_SEED)


@lru_cache(maxsize=1)
def _dungeon_it_by_slug() -> dict[str, str]:
    out: dict[str, str] = {}
    for slug, patch in DUNGEON_LORE_PATCHES.items():
        if patch.get("name_it"):
            out[slug] = patch["name_it"]
    for row in _seed_rows_dungeons():
        if row.get("name_it"):
            out[row["slug"]] = row["name_it"]
    return out


@lru_cache(maxsize=1)
def _dungeon_slug_by_en_name() -> dict[str, str]:
    return {
        row["name"]: row["slug"]
        for row in _seed_rows_dungeons()
        if row.get("name")
    }


@lru_cache(maxsize=1)
def _raid_it_by_slug() -> dict[str, str]:
    out: dict[str, str] = {}
    for slug, patch in RAID_LORE_PATCHES.items():
        if patch.get("name_it"):
            out[slug] = patch["name_it"]
    # Il name_it del seed (documento live) vince sulla patch lore,
    # coerente con raid_dungeon_public (doc prima, meta poi).
    for row in _seed_rows_raids():
        if row.get("name_it"):
            out[row["slug"]] = row["name_it"]
    return out


@lru_cache(maxsize=1)
def _raid_slug_by_en_name() -> dict[str, str]:
    return {
        row["name"]: row["slug"]
        for row in _seed_rows_raids()
        if row.get("name")
    }


def dungeon_display_name_it(
    *,
    slug: str | None = None,
    name: str | None = None,
    fallback: str | None = None,
) -> str:
    """Nome IT di un dungeon dato lo slug e/o il nome EN persistito."""
    if slug:
        found = _dungeon_it_by_slug().get(slug)
        if found:
            return found
    if name:
        mapped_slug = _dungeon_slug_by_en_name().get(name)
        if mapped_slug:
            found = _dungeon_it_by_slug().get(mapped_slug)
            if found:
                return found
    return fallback or name or slug or ""


def raid_display_name_it(
    *,
    slug: str | None = None,
    name: str | None = None,
    fallback: str | None = None,
) -> str:
    """Nome IT di un raid dato lo slug e/o il nome EN persistito."""
    if slug:
        found = _raid_it_by_slug().get(slug)
        if found:
            return found
    if name:
        mapped_slug = _raid_slug_by_en_name().get(name)
        if mapped_slug:
            found = _raid_it_by_slug().get(mapped_slug)
            if found:
                return found
    return fallback or name or slug or ""


__all__ = [
    "dungeon_display_name_it",
    "raid_display_name_it",
]
