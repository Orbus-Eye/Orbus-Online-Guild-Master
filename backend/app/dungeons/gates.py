"""Data-driven dungeon gate evaluator (Phase 11.2).

Each new dungeon may carry a `gate` dict in its seed document. The 3 original
dungeons (`goblin-warrens`, `shadow-crypts`, `dragons-hoard`) keep their
hard-coded Phase-7/8 gate logic in `app.expeditions.services._evaluate_dungeon_gate`
for byte-identical behaviour.

Gate schema (all keys optional, evaluated as AND):
- `min_adventurers`: int — guild must own ≥ N adventurers
- `min_max_team_power_ever`: int — sticky peak power ≥ N
- `min_guild_level_or_peak`: [level, peak] — unlocked if guild.level >= level
  OR max_team_power_ever >= peak (OR semantics — used for Tier 3)
- `min_total_expeditions_completed`: int — guild must have ≥ N completed runs

Always returns `(unlocked: bool, unlock_reason: Optional[str])`.
"""
from typing import Optional


async def evaluate_data_driven_gate(
    db, dungeon: dict, guild: dict
) -> tuple[bool, Optional[str]]:
    gate = dungeon.get("gate") or {}
    if not gate:
        return True, None  # no gate → unlocked

    # ── min_adventurers (AND) ────────────────────────────────────────────────
    min_adv = int(gate.get("min_adventurers", 0))
    if min_adv > 0:
        adv_count = await db.adventurers.count_documents({"guild_id": guild["id"]})
        if adv_count < min_adv:
            return (
                False,
                f"Requires {min_adv} adventurers, you have {adv_count}",
            )

    # ── min_total_expeditions_completed (AND) ────────────────────────────────
    min_exp = int(gate.get("min_total_expeditions_completed", 0))
    if min_exp > 0:
        # FASE 10G — le run AUTOMATICHE non sbloccano contenuti nuovi:
        # contano solo le spedizioni giocate manualmente.
        completed = await db.expeditions.count_documents(
            {"guild_id": guild["id"], "status": "completed",
             "auto_mode": {"$ne": True}}
        )
        if completed < min_exp:
            return (
                False,
                f"Requires {min_exp} completed expeditions, you have {completed}",
            )

    # ── min_max_team_power_ever (AND) ────────────────────────────────────────
    min_peak = int(gate.get("min_max_team_power_ever", 0))
    if min_peak > 0:
        peak = int(guild.get("max_team_power_ever", 0))
        if peak < min_peak:
            return (
                False,
                f"Requires max team power {min_peak}+, current: {peak}",
            )

    # ── min_guild_level_or_peak (OR pair, used for Tier 3) ───────────────────
    pair = gate.get("min_guild_level_or_peak")
    if pair and isinstance(pair, (list, tuple)) and len(pair) == 2:
        req_level = int(pair[0])
        req_peak = int(pair[1])
        guild_level = int(guild.get("level", 1))
        peak = int(guild.get("max_team_power_ever", 0))
        if guild_level < req_level and peak < req_peak:
            return (
                False,
                f"Requires guild level {req_level}+ OR peak team power {req_peak}+ (current: lvl {guild_level}, peak {peak})",
            )

    return True, None


__all__ = ["evaluate_data_driven_gate"]
