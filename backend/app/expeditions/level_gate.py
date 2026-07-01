"""ROUND 11.3 TASK A — Adventurer-level gate for dungeons & raids.

Centralised level-requirement enforcement. Both expeditions (dungeons) and
raids must reject teams that include adventurers below the content's
`min_adventurer_level`. Critically, **PWR alone does NOT bypass the
level gate** — a power-stacked Lv1 cannot enter a Lv12 raid.

Why a dedicated module:
  * Used by 3 call sites (start, preview, replay-last) for dungeons + 2 for
    raids. Single source of truth avoids drift.
  * Legacy seed docs lack `min_adventurer_level` — we derive a conservative
    default from `difficulty` (dungeons) / `tier` (raids) so older content
    keeps working without a backfill migration.

Error contract (HTTP 423 — Locked, mirrors `adventurers.retired_in_set`):

    {
        "code": "adventurer.level_too_low",
        "source": "<expedition.dispatch|expedition.preview|raid.start|raid.preview>",
        "min_required_level": <int>,
        "offending_adventurers": [
            {"id": "...", "name": "...", "level": <int>}
        ],
        "user_message": "Avventurieri sotto il livello richiesto (..)"
    }

No PII (no email, no user_id, no _id). Adventurer names are guild-scoped so
they are safe to expose to the caller (already exposed elsewhere).
"""
from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException


# ─── Legacy mappings ──────────────────────────────────────────────────────────
# Conservative defaults applied ONLY when the seed document lacks an explicit
# `min_adventurer_level`. New content created by the round 11.3 seeds is
# expected to carry the field explicitly.
_DUNGEON_DIFFICULTY_TO_MIN_LEVEL: dict[int, int] = {
    1: 1,   # facile  → Lv1
    2: 3,   # medio   → Lv3
    3: 7,   # difficile → Lv7
    4: 12,  # elite   → Lv12
}

# Raids: derive from `tier` if present, otherwise fall back on
# recommended_power_combined buckets. Endgame raids = Lv15.
_RAID_TIER_TO_MIN_LEVEL: dict[int, int] = {
    1: 8,
    2: 12,
    3: 15,
}


def legacy_min_level_for_dungeon(dungeon: dict) -> int:
    """Resolve `min_adventurer_level` for a dungeon document.

    ROUND 16.5 P0.3 — precedenza:
      1. `required_level` (nuovo campo canonico, P0.2 apply).
      2. `min_adventurer_level` (legacy, esplicito).
      3. Fallback mappa `difficulty` → min_level.
      4. 0 (nessun gate) se tutto assente.

    Semantica falsy: 0/None/valore non-int vengono ignorati e si passa
    al prossimo step. Un valore >= 1 vince immediatamente.
    """
    # 1. Nuovo canonical field (P0.2 apply).
    r165 = dungeon.get("required_level")
    if isinstance(r165, int) and r165 >= 1:
        return r165
    # 2. Legacy esplicito.
    explicit = dungeon.get("min_adventurer_level")
    if isinstance(explicit, int) and explicit >= 1:
        return explicit
    # 3. Fallback su difficulty (comportamento pre-R16.5).
    diff = int(dungeon.get("difficulty", 1) or 1)
    return _DUNGEON_DIFFICULTY_TO_MIN_LEVEL.get(diff, 1)


def legacy_min_level_for_raid(raid_dungeon: dict) -> int:
    """Resolve `min_adventurer_level` for a raid_dungeons document."""
    explicit = raid_dungeon.get("min_adventurer_level")
    if isinstance(explicit, int) and explicit >= 1:
        return explicit
    tier = int(raid_dungeon.get("tier", 1) or 1)
    if tier in _RAID_TIER_TO_MIN_LEVEL:
        return _RAID_TIER_TO_MIN_LEVEL[tier]
    # Power-bucket fallback for very old seeds without tier.
    rec = int(raid_dungeon.get("recommended_power_combined", 0))
    if rec >= 6000:
        return 15
    if rec >= 3500:
        return 12
    return 8


def enforce_min_adventurer_level(
    advs: Iterable[dict],
    min_required_level: int,
    *,
    source: str,
    dungeon_slug: str | None = None,
) -> None:
    """Raise 423 if any adventurer is below `min_required_level`.

    `advs` is an iterable of adventurer dicts loaded from `db.adventurers`.
    `source` is a stable string ("expedition.dispatch", "raid.start", etc.)
    used by the FE to branch error UI and by audit dashboards to count
    blocked attempts per surface.

    ROUND 16.5 P0.3 — se il chiamante conosce lo slug del dungeon lo
    include nel payload d'errore per un debugging più chiaro sul FE.
    """
    if min_required_level <= 1:
        return  # no-op gate
    offenders = []
    for adv in advs:
        lvl = int(adv.get("level", 1) or 1)
        if lvl < min_required_level:
            offenders.append({
                "id": adv.get("id"),
                "name": adv.get("name", "?"),
                "level": lvl,
            })
    if not offenders:
        return
    # ROUND 11.3 micro-ROI: log blocked attempts to a dedicated stdout
    # marker so balance design can aggregate which dungeons/raids are the
    # main psychological walls. We log only counts + source — NO PII.
    import logging
    logging.getLogger("orbus.level_gate").info(
        "level_gate.blocked_attempts source=%s min_level=%d count=%d slug=%s",
        source, min_required_level, len(offenders), dungeon_slug or "-",
    )
    names = ", ".join(f"{o['name']} (Lv{o['level']})" for o in offenders[:3])
    suffix = "" if len(offenders) <= 3 else f" e altri {len(offenders) - 3}"
    detail = {
        "code": "adventurer.level_too_low",
        "source": source,
        "min_required_level": min_required_level,
        "adventurers_below": offenders,
        # Alias legacy (retro-compatibilità con FE pre-R16.5).
        "offending_adventurers": offenders,
        "count": len(offenders),
        "user_message": (
            f"Servono avventurieri di livello {min_required_level}+. "
            f"Sotto soglia: {names}{suffix}."
        ),
    }
    if dungeon_slug:
        detail["dungeon_slug"] = dungeon_slug
    raise HTTPException(status_code=423, detail=detail)


__all__ = [
    "legacy_min_level_for_dungeon",
    "legacy_min_level_for_raid",
    "enforce_min_adventurer_level",
]
