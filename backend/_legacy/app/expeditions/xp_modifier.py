"""ROUND 15 — Fase 2 / Task B: XP debuff for low primary stat.

When an adventurer's primary stat is significantly below the expected
threshold for their level, XP gain is reduced. Formula and tiers are
codified here so other domains (raids, contracts) can reuse the helper.

Tier table (delta_pct = (expected - actual) / expected * 100):

    delta_pct ≤ 0           → 1.00  (stat ok)
    0 < delta_pct < 10      → 1.00  (tolerance zone, no debuff)
    10 ≤ delta_pct < 20     → 0.90  (minor)
    20 ≤ delta_pct < 30     → 0.80  (major)
    delta_pct ≥ 30          → 0.70  (critical, hard cap)

Scope:
    Applied to expedition member XP. NOT applied to:
    - guild XP / achievement progress
    - PvP Elo
    - any cosmetic / non-progression counter

`expected_primary_stat(class_slug, level)` is the single source of truth
for the threshold; it falls back to a conservative default if the class
doc is missing or lacks `base_<primary>`.

Italian player-facing strings live in `xp_modifier_reason_it()` so
report builders can render them without duplicating wording.
"""
from __future__ import annotations

from typing import Optional

# Italian display names for the 5 primary stats. Mirrors STAT_IT in
# ClassesAndStatsSection.jsx; if we ever ship more languages we'll move
# this to a shared i18n module.
PRIMARY_STAT_IT = {
    "strength": "Forza",
    "agility": "Destrezza",
    "intellect": "Intelletto",
    "endurance": "Costituzione",
    "faith": "Fede",
}

# Per-level growth coefficient. 0.5 means each level adds half a point of
# expected primary stat — at L10 expected = base + 5, at L50 = base + 25.
PER_LEVEL_GROWTH = 0.5

# Hard floor on the multiplier — never punish below 0.70.
MIN_XP_MULTIPLIER = 0.70


def expected_primary_stat(class_doc: Optional[dict], level: int) -> int:
    """Threshold = `base_<primary>` + round(level * PER_LEVEL_GROWTH).

    Returns 0 when the class doc is missing or has no `primary_stat`.
    Level is clamped to ≥ 1 to avoid pathological inputs.
    """
    if not class_doc:
        return 0
    primary = (class_doc.get("primary_stat") or "").strip().lower()
    if not primary:
        return 0
    base_field = f"base_{primary}"
    base = int(class_doc.get(base_field, 0) or 0)
    lvl = max(1, int(level or 1))
    return base + round(lvl * PER_LEVEL_GROWTH)


def compute_xp_multiplier(
    adventurer: dict, class_doc: Optional[dict]
) -> dict:
    """Return the XP multiplier for `adventurer` given its class.

    Output dict:
        {
          "multiplier": float,
          "reason_code": str,
          "threshold": int,
          "actual": int,
          "deficit_pct": float,
          "primary_stat_slug": str,
          "primary_stat_name_it": str,
        }

    `reason_code` ∈ {
        "policy_disabled", "primary_ok", "primary_ok_tolerance",
        "primary_stat_low_minor", "primary_stat_low_major",
        "primary_stat_low_critical",
    }
    """
    if not class_doc:
        return {
            "multiplier": 1.0, "reason_code": "policy_disabled",
            "threshold": 0, "actual": 0, "deficit_pct": 0.0,
            "primary_stat_slug": "", "primary_stat_name_it": "",
        }
    policy = class_doc.get("xp_primary_stat_policy") or {}
    if not policy.get("enabled"):
        return {
            "multiplier": 1.0, "reason_code": "policy_disabled",
            "threshold": 0, "actual": 0, "deficit_pct": 0.0,
            "primary_stat_slug": class_doc.get("primary_stat") or "",
            "primary_stat_name_it": PRIMARY_STAT_IT.get(
                class_doc.get("primary_stat") or "", ""
            ),
        }

    primary = (class_doc.get("primary_stat") or "").strip().lower()
    if not primary:
        return {
            "multiplier": 1.0, "reason_code": "primary_ok",
            "threshold": 0, "actual": 0, "deficit_pct": 0.0,
            "primary_stat_slug": "", "primary_stat_name_it": "",
        }

    actual = int(adventurer.get(primary, 0) or 0)
    level = int(adventurer.get("level", 1) or 1)
    threshold = expected_primary_stat(class_doc, level)
    if threshold <= 0:
        return {
            "multiplier": 1.0, "reason_code": "primary_ok",
            "threshold": 0, "actual": actual, "deficit_pct": 0.0,
            "primary_stat_slug": primary,
            "primary_stat_name_it": PRIMARY_STAT_IT.get(primary, primary),
        }

    deficit_pct = max(0.0, (threshold - actual) / threshold * 100.0)

    if deficit_pct <= 0:
        mult, code = 1.0, "primary_ok"
    elif deficit_pct < 10:
        mult, code = 1.0, "primary_ok_tolerance"
    elif deficit_pct < 20:
        mult, code = 0.90, "primary_stat_low_minor"
    elif deficit_pct < 30:
        mult, code = 0.80, "primary_stat_low_major"
    else:
        mult, code = MIN_XP_MULTIPLIER, "primary_stat_low_critical"

    return {
        "multiplier": float(mult),
        "reason_code": code,
        "threshold": int(threshold),
        "actual": int(actual),
        "deficit_pct": round(deficit_pct, 1),
        "primary_stat_slug": primary,
        "primary_stat_name_it": PRIMARY_STAT_IT.get(primary, primary),
    }


def xp_modifier_reason_it(info: dict) -> str:
    """Player-facing one-liner — empty string when no debuff applied."""
    code = info.get("reason_code", "")
    if code in ("policy_disabled", "primary_ok", "primary_ok_tolerance"):
        return ""
    stat_name = info.get("primary_stat_name_it") or "Stat primaria"
    debuff_pct = int(round((1.0 - info.get("multiplier", 1.0)) * 100))
    return (
        f"XP ridotta: {stat_name} sotto soglia classe (-{debuff_pct}%)."
    )


__all__ = [
    "PRIMARY_STAT_IT",
    "PER_LEVEL_GROWTH",
    "MIN_XP_MULTIPLIER",
    "expected_primary_stat",
    "compute_xp_multiplier",
    "xp_modifier_reason_it",
]
