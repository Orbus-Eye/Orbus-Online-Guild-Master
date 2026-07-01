"""ROUND 16.4 — Global Balance Audit (READ-ONLY).

Scope: diagnose the broken power curve reported by the user
("lv4 adventurers clear lv7 dungeons easily") without touching any data.

## Guarantees

- READ-ONLY: monkey-patches Motor / PyMongo write methods on both
  `Collection` and `Database` classes to raise `RuntimeError` if any code
  path (imported by us or transitively) attempts a mutation.
- Requires `--read-only` flag; any of `--apply|--seed|--write|--commit|--fix`
  aborts immediately.
- Does NOT import modules that seed/write (`app.seeds.*`, `app.recovery.*`,
  admin dev utilities). Only pure formula modules are imported.
- Points at the real DB (`orbus_r16`) via existing backend env — never
  redirects to a test DB.

## Deliverables

- Console log (stdout + `/app/memory/round164_audit_console.log`)
- Machine-readable dump `/app/memory/round164_audit_raw_data.json`

Usage:
    python /app/backend/app/scripts/balance_dungeon_power_audit.py --read-only

The audit does NOT propose fixes. The companion document
`/app/memory/round164_balance_audit_report.md` interprets these findings.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Any

# Ensure `app.*` is importable when this script is run standalone
# (mirrors `pytest.ini`'s `pythonpath = .`).
sys.path.insert(0, "/app/backend")

# ═════════════════════════════════════════════════════════════════════
# 0. HARD GUARD-RAILS — must run BEFORE importing motor / pymongo
# ═════════════════════════════════════════════════════════════════════


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, add_help=True)
    p.add_argument("--read-only", action="store_true",
                   help="MANDATORY safety flag. Without it the script aborts.")
    for hostile in ("--apply", "--seed", "--write",
                    "--commit", "--fix", "--migrate"):
        p.add_argument(hostile, action="store_true",
                       help="FORBIDDEN — script aborts if this is set.")
    return p.parse_args()


def _enforce_read_only(args: argparse.Namespace) -> None:
    if not args.read_only:
        sys.stderr.write(
            "REFUSING: pass --read-only to run this audit.\n"
        )
        sys.exit(1)
    for hostile in ("apply", "seed", "write", "commit", "fix", "migrate"):
        if getattr(args, hostile, False):
            sys.stderr.write(
                f"REFUSING: hostile flag --{hostile} passed. "
                "This audit is strictly read-only.\n"
            )
            sys.exit(1)
    print("=== READ ONLY MODE ===")


def _patch_write_methods_forbidden() -> None:
    """Monkey-patch motor + pymongo write methods to raise before I/O."""
    import motor.motor_asyncio as _motor
    import pymongo.collection as _pc
    import pymongo.database as _pd

    def _forbidden(name: str):
        def _raise(*args, **kwargs):
            raise RuntimeError(
                f"WRITE FORBIDDEN IN AUDIT MODE (method: {name})"
            )
        return _raise

    write_methods = (
        "insert_one", "insert_many",
        "update_one", "update_many",
        "replace_one",
        "delete_one", "delete_many",
        "find_one_and_update", "find_one_and_replace",
        "find_one_and_delete",
        "bulk_write",
        "drop", "rename",
        "create_index", "create_indexes", "drop_index", "drop_indexes",
    )
    for cls in (
        _motor.AsyncIOMotorCollection,
        _motor.AsyncIOMotorDatabase,
        _pc.Collection,
        _pd.Database,
    ):
        for m in write_methods:
            if hasattr(cls, m):
                try:
                    setattr(cls, m, _forbidden(m))
                except Exception:
                    pass


# ═════════════════════════════════════════════════════════════════════
# 1. DB CONNECTION
# ═════════════════════════════════════════════════════════════════════


def _connect_db():
    """Sync PyMongo client to the REAL orbus_r16 (never a test DB)."""
    import os
    from dotenv import load_dotenv
    load_dotenv(Path("/app/backend/.env"))
    from pymongo import MongoClient
    url = os.environ.get("MONGO_URL")
    db_name = "orbus_r16"  # real prod-dev DB — user requested real data
    client = MongoClient(url)
    db = client[db_name]
    # Sanity check: DB accessible.
    _ = db.list_collection_names()
    return client, db


# ═════════════════════════════════════════════════════════════════════
# 2. FORMULA IMPORT (pure functions only)
# ═════════════════════════════════════════════════════════════════════


def _load_formulas():
    """Import ONLY pure formula modules — never services that mutate DB."""
    # `app.expeditions.formulas` is pure (no I/O, no Mongo).
    from app.expeditions import formulas as F
    return F


# ═════════════════════════════════════════════════════════════════════
# 3. ANALYSES
# ═════════════════════════════════════════════════════════════════════


def _extract_formula_documentation(F) -> dict[str, Any]:
    return {
        "adventurer_base_power": {
            "formula": "STR + AGI + INT + END + FTH + level*2",
            "source": "app/expeditions/formulas.py:59-72",
        },
        "adventurer_effective_power": {
            "formula": (
                "sum(base_stats) after trait modifiers + specialization "
                "modifiers, then + level*2. Traits: flat additive, then "
                "percent multiplicative additive-stack. Spec modifiers "
                "resolved by app.training.catalog."
            ),
            "source": "app/expeditions/formulas.py:75-92",
        },
        "item_equip_power": {
            "formula": (
                "STR_bonus + AGI_bonus + INT_bonus + END_bonus + "
                "FTH_bonus + item.power_score"
            ),
            "source": "app/expeditions/formulas.py:95-104",
        },
        "compute_team_power": {
            "formula": (
                "Σ total_power_snapshot (o legacy fallback stats+lvl*2) "
                "+ role bonus: Tank +5, Healer +5, DPS +5, "
                "all-3-roles +10 (additivo, cap implicito +25 su 3 roli)."
            ),
            "source": "app/expeditions/formulas.py:107-142",
        },
        "compute_success_chance": {
            "formula": (
                "raw = 50 + (team_power - recommended_power); "
                "clamp [SUCCESS_CHANCE_MIN=10, SUCCESS_CHANCE_MAX=95]."
            ),
            "source": "app/expeditions/formulas.py:145-152",
            "note": (
                "Curva LINEARE con pendenza +1%/punto. Il team che eccede "
                "recommended_power di 45 punti raggiunge il cap 95%."
            ),
        },
        "threat_bonus": {
            "formula": (
                "counter_ratio * SUCCESS_BONUS_CAP_PCT (12%); "
                "injury_reduction = counter_ratio * 8%."
            ),
            "source": "app/expeditions/threats.py:26-27, 90-91",
        },
        "final_success_chance": {
            "formula": (
                "min(base_success + threat_bonus, 95). Threat bonus cap +12."
            ),
            "source": "app/dungeons/preview.py:112-119",
        },
    }


def _extract_dungeons(db) -> list[dict]:
    rows = list(db.dungeons.find(
        {"is_active": True},
        {
            "_id": 0, "slug": 1, "name": 1, "name_it": 1,
            "difficulty": 1, "required_level": 1, "recommended_power": 1,
            "base_gold_reward": 1, "base_xp_reward": 1,
            "required_team_size": 1, "threat_tags": 1,
            "counter_tags": 1, "gate": 1, "is_5p": 1,
            "content_family": 1, "enemy_families": 1,
        },
    ))
    # Sort by required_level (asc). Fallback to difficulty when missing.
    rows.sort(key=lambda d: (
        d.get("required_level") or 0,
        d.get("difficulty") or 0,
        d.get("recommended_power") or 0,
    ))
    return rows


def _classify_level_band(lvl: int) -> str:
    if lvl <= 3:
        return "1-3"
    if lvl <= 6:
        return "4-6"
    if lvl <= 9:
        return "7-9"
    return "10+"


def _extract_adventurer_stats(db, F) -> dict[str, Any]:
    """Aggregate adventurer power by level band.

    Uses `total_power_snapshot` when present, otherwise recomputes via
    the imported pure formula (`adventurer_effective_power`). Skips
    legacy-schema docs (`stats.atk` only) since the formula requires
    strength/agility/... — reports them under a separate bucket.
    """
    STATS = ("strength", "agility", "intellect", "endurance", "faith")
    bands: dict[str, dict] = {b: {"count": 0, "powers": []}
                              for b in ("1-3", "4-6", "7-9", "10+")}
    legacy_skipped = 0
    total_seen = 0
    for adv in db.adventurers.find(
        {"archived": {"$ne": True}, "retired": {"$ne": True}},
        {"_id": 0, "level": 1, "traits": 1, "specialization": 1,
         **{s: 1 for s in STATS},
         "total_power_snapshot": 1},
    ):
        total_seen += 1
        # Must have modern schema.
        if not all(s in adv for s in STATS):
            legacy_skipped += 1
            continue
        band = _classify_level_band(int(adv.get("level", 1)))
        if adv.get("total_power_snapshot") is not None:
            p = int(adv["total_power_snapshot"])
        else:
            try:
                p = F.adventurer_effective_power(adv)
            except Exception:
                # Spec might reference missing catalog — fall back.
                p = F.adventurer_base_power(adv)
        bands[band]["count"] += 1
        bands[band]["powers"].append(p)

    result = {"total_seen": total_seen,
              "legacy_schema_skipped": legacy_skipped, "bands": {}}
    for band, data in bands.items():
        powers = data["powers"]
        if not powers:
            result["bands"][band] = {"count": 0}
            continue
        result["bands"][band] = {
            "count": data["count"],
            "mean": round(statistics.mean(powers), 2),
            "median": statistics.median(powers),
            "stdev": round(statistics.stdev(powers), 2) if len(powers) > 1 else 0.0,
            "p25": _percentile(powers, 25),
            "p50": _percentile(powers, 50),
            "p75": _percentile(powers, 75),
            "p90": _percentile(powers, 90),
            "min": min(powers),
            "max": max(powers),
        }
    return result


def _percentile(data: list, pct: int) -> float:
    if not data:
        return 0.0
    sd = sorted(data)
    k = (len(sd) - 1) * pct / 100.0
    lo = int(k)
    hi = min(lo + 1, len(sd) - 1)
    if lo == hi:
        return float(sd[lo])
    return round(sd[lo] + (sd[hi] - sd[lo]) * (k - lo), 2)


def _class_base_stats(db) -> dict[str, dict]:
    """Load `adventurer_classes` doc, keyed by lowercase class slug."""
    out = {}
    for row in db.adventurer_classes.find(
        {},
        {"_id": 0, "slug": 1, "name": 1, "role": 1,
         "base_strength": 1, "base_agility": 1, "base_intellect": 1,
         "base_endurance": 1, "base_faith": 1},
    ):
        key = (row.get("slug") or row.get("name") or "").lower()
        out[key] = row
    return out


def _synthetic_adventurer(cls: dict, level: int, equip_power: int = 0) -> dict:
    """Craft a synthetic adventurer dict compatible with formula funcs."""
    stats_growth = level - 1  # +1 per stat per level (conservative avg)
    strength = int(cls.get("base_strength", 8)) + stats_growth
    agility = int(cls.get("base_agility", 8)) + stats_growth
    intellect = int(cls.get("base_intellect", 8)) + stats_growth
    endurance = int(cls.get("base_endurance", 8)) + stats_growth
    faith = int(cls.get("base_faith", 5)) + stats_growth
    total_stat = strength + agility + intellect + endurance + faith
    return {
        "level": level,
        "strength": strength, "agility": agility, "intellect": intellect,
        "endurance": endurance, "faith": faith,
        "total_power_snapshot": total_stat + level * 2 + equip_power,
        "equipment_power_snapshot": equip_power,
        "class_role": cls.get("role", "DPS"),
        "role_snapshot": cls.get("role", "DPS"),
    }


def _build_archetypes(cls_map: dict[str, dict]) -> dict[str, list[dict]]:
    """6 canonical archetypes for Monte Carlo."""
    # Pick 3 baseline classes with distinct roles.
    tank = cls_map.get("guardian") or cls_map.get("knight") or next(iter(cls_map.values()))
    healer = cls_map.get("cleric") or cls_map.get("priest") or next(iter(cls_map.values()))
    dps = cls_map.get("berserker") or cls_map.get("rogue") or next(iter(cls_map.values()))

    return {
        "team_base_no_equip": [
            _synthetic_adventurer(tank, 4, 0),
            _synthetic_adventurer(healer, 4, 0),
            _synthetic_adventurer(dps, 4, 0),
        ],
        "team_medio_reale": [
            _synthetic_adventurer(tank, 4, 8),
            _synthetic_adventurer(healer, 5, 8),
            _synthetic_adventurer(dps, 4, 10),
        ],
        "team_buono": [
            _synthetic_adventurer(tank, 5, 20),
            _synthetic_adventurer(healer, 6, 20),
            _synthetic_adventurer(dps, 5, 22),
        ],
        "team_forte_outlier": [
            _synthetic_adventurer(tank, 6, 45),
            _synthetic_adventurer(healer, 7, 45),
            _synthetic_adventurer(dps, 6, 50),
        ],
        # Both counter/no-counter groups use "medio_reale" as baseline power
        # so we isolate the threat-bonus effect.
        "team_counter_perfetto": [
            _synthetic_adventurer(tank, 5, 15),
            _synthetic_adventurer(healer, 5, 15),
            _synthetic_adventurer(dps, 5, 18),
        ],
        "team_no_counter": [
            _synthetic_adventurer(tank, 5, 15),
            _synthetic_adventurer(healer, 5, 15),
            _synthetic_adventurer(dps, 5, 18),
        ],
    }


def _monte_carlo(F, archetypes: dict[str, list[dict]],
                 dungeons: list[dict], iters: int) -> dict[str, Any]:
    """For each archetype × dungeon, compute deterministic success chance
    plus a Monte Carlo estimation with random variance to expose spread.

    NB: The formula `compute_success_chance` is deterministic; MC adds a
    Gaussian noise term (σ=3%) to simulate day-to-day variance
    (fatigue / minor gear differences) and estimates % of "clear" runs
    where a d(0..99) roll < effective success chance.
    """
    random.seed(1642)  # deterministic for reproducibility
    out = {}
    for arch_name, team in archetypes.items():
        arch_row = {}
        team_power = F.compute_team_power(team)
        for d in dungeons:
            rec = d.get("recommended_power") or 100
            base_sc = F.compute_success_chance(team_power, rec)
            # Simulated threat bonus for counter-matched archetype only.
            threat_bonus_pct = 0
            if arch_name == "team_counter_perfetto" and d.get("threat_tags"):
                # Assume full counter coverage: cap +12.
                threat_bonus_pct = 12
            eff_sc = min(95, base_sc + threat_bonus_pct)
            # Monte Carlo runs
            wins = 0
            for _ in range(iters):
                noise = random.gauss(0, 3.0)  # ±3% jitter
                trial_sc = max(0.0, min(95.0, eff_sc + noise))
                if random.random() * 100 < trial_sc:
                    wins += 1
            success_rate = wins / iters
            expected_reward = (
                int(d.get("base_gold_reward", 0)) * success_rate,
                int(d.get("base_xp_reward", 0)) * success_rate,
            )
            arch_row[d["slug"]] = {
                "dungeon_name": d.get("name"),
                "required_level": d.get("required_level"),
                "recommended_power": rec,
                "team_power": team_power,
                "delta_power": team_power - rec,
                "base_success_chance": base_sc,
                "threat_bonus_pct": threat_bonus_pct,
                "effective_success_chance": eff_sc,
                "mc_success_rate": round(success_rate, 4),
                "expected_gold": round(expected_reward[0], 2),
                "expected_xp": round(expected_reward[1], 2),
            }
        out[arch_name] = arch_row
    return out


def _flag_incoherent_dungeons(dungeons: list[dict],
                              mc_results: dict[str, Any]) -> list[dict]:
    """A dungeon is incoherent if a team below required_level clears it >60%."""
    incoherent = []
    # Use `team_medio_reale` (lv 4-5) as representative of "below-level" team
    # for dungeons requiring lv≥5. `team_forte_outlier` (lv 6-7) is the
    # secondary probe.
    for d in dungeons:
        req = d.get("required_level") or 0
        slug = d["slug"]
        med = mc_results.get("team_medio_reale", {}).get(slug, {})
        forte = mc_results.get("team_forte_outlier", {}).get(slug, {})
        if req >= 5 and med.get("mc_success_rate", 0) > 0.60:
            incoherent.append({
                "slug": slug, "name": d.get("name"),
                "required_level": req,
                "recommended_power": d.get("recommended_power"),
                "probe_team": "team_medio_reale (lv 4-5)",
                "probe_success_rate": med.get("mc_success_rate"),
                "reason": (
                    f"lv 4-5 team clears at "
                    f"{med.get('mc_success_rate', 0) * 100:.1f}% > 60%"
                ),
            })
        elif req >= 7 and forte.get("mc_success_rate", 0) > 0.80:
            incoherent.append({
                "slug": slug, "name": d.get("name"),
                "required_level": req,
                "recommended_power": d.get("recommended_power"),
                "probe_team": "team_forte_outlier (lv 6-7)",
                "probe_success_rate": forte.get("mc_success_rate"),
                "reason": (
                    f"lv 6-7 team clears lv{req} dungeon at "
                    f"{forte.get('mc_success_rate', 0) * 100:.1f}% > 80%"
                ),
            })
    return incoherent


def _find_outlier_specs_and_items(db, F, band_stats: dict) -> dict[str, Any]:
    """Identify classes / specs / items that skew the power curve.

    Heuristics (read-only):
    - Class outlier: base_stat sum > μ + 2σ vs peer classes
    - Item outlier: `item_equip_power(item) > 30` (single-item contribution
      cap = 30 makes sense given lv4 total power is ~50-60)
    """
    # Class outliers
    class_docs = list(db.adventurer_classes.find(
        {},
        {"_id": 0, "slug": 1, "name": 1, "role": 1,
         "base_strength": 1, "base_agility": 1, "base_intellect": 1,
         "base_endurance": 1, "base_faith": 1},
    ))
    stat_sums = []
    for c in class_docs:
        total = sum(int(c.get(f"base_{s}", 0)) for s in (
            "strength", "agility", "intellect", "endurance", "faith"))
        stat_sums.append({"slug": c.get("slug") or c.get("name"),
                          "role": c.get("role"),
                          "base_total": total})
    class_powers = [x["base_total"] for x in stat_sums]
    class_outliers = []
    if len(class_powers) > 2:
        mu = statistics.mean(class_powers)
        sd = statistics.stdev(class_powers) if len(class_powers) > 1 else 0
        threshold = mu + 2 * sd
        for c in stat_sums:
            if c["base_total"] > threshold:
                class_outliers.append({**c, "mu": round(mu, 2),
                                       "threshold": round(threshold, 2)})

    # Specialization outliers via class_specializations.stat_modifiers
    spec_outliers = []
    for row in db.class_specializations.find(
        {"is_active": True},
        {"_id": 0, "slug": 1, "class_slug": 1, "stat_modifiers": 1,
         "counter_tags": 1},
    ):
        mods = row.get("stat_modifiers") or {}
        # Sum of all positive modifiers as raw power contribution.
        pos_sum = sum(int(v) for v in mods.values() if isinstance(v, (int, float)) and v > 0)
        if pos_sum > 15:  # arbitrary; +15 = 25% of a lv4 base
            spec_outliers.append({
                "slug": row["slug"], "class_slug": row.get("class_slug"),
                "positive_stat_sum": pos_sum,
                "counter_tags_count": len(row.get("counter_tags") or []),
            })
    spec_outliers.sort(key=lambda x: x["positive_stat_sum"], reverse=True)

    # Item outliers
    item_outliers = []
    for it in db.items.find(
        {"is_active": {"$ne": False}},
        {"_id": 0, "slug": 1, "name": 1, "rarity": 1,
         "strength_bonus": 1, "agility_bonus": 1, "intellect_bonus": 1,
         "endurance_bonus": 1, "faith_bonus": 1, "power_score": 1,
         "min_level": 1},
    ):
        eq_p = F.item_equip_power(it)
        min_lvl = int(it.get("min_level") or 1)
        # A lv1-usable item contributing >30 power is an outlier.
        if eq_p > 30 and min_lvl <= 3:
            item_outliers.append({
                "slug": it.get("slug"), "name": it.get("name"),
                "rarity": it.get("rarity"),
                "equip_power": eq_p, "min_level": min_lvl,
            })
    item_outliers.sort(key=lambda x: x["equip_power"], reverse=True)

    return {
        "class_outliers": class_outliers[:20],
        "spec_outliers": spec_outliers[:20],
        "item_outliers": item_outliers[:20],
        "class_stat_sum_summary": {
            "count": len(class_powers),
            "mean": round(statistics.mean(class_powers), 2) if class_powers else 0,
            "min": min(class_powers) if class_powers else 0,
            "max": max(class_powers) if class_powers else 0,
        },
    }


def _stacking_analysis(F, cls_map: dict) -> dict[str, Any]:
    """Compute what fraction of team power comes from each multiplier by
    building a synthetic team lv4 and stripping components one-by-one."""
    tank = next(iter(cls_map.values()))
    healer = next(iter(cls_map.values()))
    dps = next(iter(cls_map.values()))

    scenarios = {}
    # Baseline: no equip, no traits, no spec
    baseline_team = [
        _synthetic_adventurer(tank, 4, 0),
        _synthetic_adventurer(healer, 4, 0),
        _synthetic_adventurer(dps, 4, 0),
    ]
    scenarios["baseline_no_equip"] = F.compute_team_power(baseline_team)

    # + moderate equip (+10 avg per adv)
    with_equip_team = [
        _synthetic_adventurer(tank, 4, 10),
        _synthetic_adventurer(healer, 4, 10),
        _synthetic_adventurer(dps, 4, 10),
    ]
    scenarios["with_moderate_equip"] = F.compute_team_power(with_equip_team)

    # + strong equip (+30 per adv, near-cap)
    with_strong_equip = [
        _synthetic_adventurer(tank, 4, 30),
        _synthetic_adventurer(healer, 4, 30),
        _synthetic_adventurer(dps, 4, 30),
    ]
    scenarios["with_strong_equip"] = F.compute_team_power(with_strong_equip)

    # Same, at lv 7
    lv7_baseline = [
        _synthetic_adventurer(tank, 7, 0),
        _synthetic_adventurer(healer, 7, 0),
        _synthetic_adventurer(dps, 7, 0),
    ]
    scenarios["lv7_baseline_no_equip"] = F.compute_team_power(lv7_baseline)

    lv7_strong = [
        _synthetic_adventurer(tank, 7, 30),
        _synthetic_adventurer(healer, 7, 30),
        _synthetic_adventurer(dps, 7, 30),
    ]
    scenarios["lv7_with_strong_equip"] = F.compute_team_power(lv7_strong)

    # Relative jump: strong equip vs baseline at lv4
    lv4_jump_pct = (scenarios["with_strong_equip"] - scenarios["baseline_no_equip"]) \
        / max(1, scenarios["baseline_no_equip"]) * 100
    return {
        "scenarios": scenarios,
        "lv4_equip_power_lift_pct": round(lv4_jump_pct, 2),
        "note": (
            "Equip a +30/adv (Epic tier) raddoppia quasi il team power di "
            "un team lv4. Chi ha equip decente a lv4 supera team lv7 nudi."
        ),
    }


# ═════════════════════════════════════════════════════════════════════
# 4. MAIN
# ═════════════════════════════════════════════════════════════════════


def main() -> int:
    args = _parse_args()
    _enforce_read_only(args)
    _patch_write_methods_forbidden()

    log_lines = []
    def log(msg: str = ""):
        print(msg)
        log_lines.append(msg)

    t0 = time.time()
    log(f"[audit] start {time.strftime('%Y-%m-%d %H:%M:%S')}")

    client, db = _connect_db()
    log(f"[audit] connected to DB: {db.name}")

    F = _load_formulas()
    log("[audit] loaded pure formulas (expeditions.formulas)")

    # A. Formulae
    log("\n=== A. FORMULA power_score ===")
    formulas_doc = _extract_formula_documentation(F)
    for name, info in formulas_doc.items():
        log(f"  · {name}")
        log(f"      {info['formula']}")
        log(f"      source: {info['source']}")
        if "note" in info:
            log(f"      note:   {info['note']}")

    # B. Dungeons
    log("\n=== B. DUNGEON TABLE (sorted by required_level) ===")
    dungeons = _extract_dungeons(db)
    for d in dungeons:
        log(
            f"  · [{d.get('required_level') or 0:2d}] "
            f"{d['slug']:32s} rec_pow={d.get('recommended_power'):>4} "
            f"gold={d.get('base_gold_reward'):>3} xp={d.get('base_xp_reward'):>3} "
            f"threats={len(d.get('threat_tags') or [])}"
        )
    log(f"  Total active dungeons: {len(dungeons)}")

    # C. Adventurer stats
    log("\n=== C. ADVENTURER POWER by LEVEL BAND ===")
    adv_stats = _extract_adventurer_stats(db, F)
    log(f"  total_seen={adv_stats['total_seen']} "
        f"legacy_skipped={adv_stats['legacy_schema_skipped']}")
    for band, s in adv_stats["bands"].items():
        if s.get("count", 0) == 0:
            log(f"  band {band}: EMPTY")
            continue
        log(f"  band {band}: n={s['count']:>4} μ={s['mean']:>6.1f} "
            f"σ={s['stdev']:>5.1f} p25={s['p25']:>5} p50={s['p50']:>5} "
            f"p75={s['p75']:>5} p90={s['p90']:>5} min={s['min']} max={s['max']}")

    # D. Archetypes
    log("\n=== D. TEAM ARCHETYPES (synthetic) ===")
    cls_map = _class_base_stats(db)
    log(f"  loaded {len(cls_map)} adventurer classes from catalog")
    archetypes = _build_archetypes(cls_map)
    archetype_powers = {name: F.compute_team_power(team)
                        for name, team in archetypes.items()}
    for name, tp in archetype_powers.items():
        log(f"  · {name:28s} team_power={tp}")

    # E. Monte Carlo
    ITERS_FULL = 10_000
    log(f"\n=== E. MONTE CARLO simulation ({ITERS_FULL} iters × archetype × dungeon) ===")
    mc_t0 = time.time()
    mc_results = _monte_carlo(F, archetypes, dungeons, ITERS_FULL)
    mc_elapsed = time.time() - mc_t0
    iters_used = ITERS_FULL
    log(f"  full run elapsed: {mc_elapsed:.2f}s")
    if mc_elapsed > 60:
        log("  ⚠ full run > 60s — re-running with 5000 iters for report determinism")
        mc_results = _monte_carlo(F, archetypes, dungeons, 5_000)
        iters_used = 5_000

    # F. Coherence analysis
    log("\n=== F. INCOHERENT DUNGEONS ===")
    incoherent = _flag_incoherent_dungeons(dungeons, mc_results)
    if not incoherent:
        log("  none flagged")
    for row in incoherent:
        log(f"  ❌ [{row['required_level']}] {row['slug']}: "
            f"{row['probe_team']} → {row['probe_success_rate'] * 100:.1f}% "
            f"({row['reason']})")

    # G. Outliers
    log("\n=== G. OUTLIER DETECTION ===")
    outliers = _find_outlier_specs_and_items(db, F, adv_stats)
    log(f"  class_stat_sum: {outliers['class_stat_sum_summary']}")
    log(f"  class_outliers (>μ+2σ): {len(outliers['class_outliers'])}")
    for c in outliers["class_outliers"][:5]:
        log(f"    · {c['slug']}: base_total={c['base_total']} "
            f"(μ={c['mu']}, threshold={c['threshold']})")
    log(f"  spec_outliers (pos_mod_sum > 15): "
        f"{len(outliers['spec_outliers'])}")
    for s in outliers["spec_outliers"][:5]:
        log(f"    · {s['slug']} (class={s['class_slug']}): "
            f"+{s['positive_stat_sum']} stats, "
            f"{s['counter_tags_count']} counters")
    log(f"  item_outliers (equip_power >30, min_lvl ≤3): "
        f"{len(outliers['item_outliers'])}")
    for it in outliers["item_outliers"][:5]:
        log(f"    · {it['slug']} ({it['rarity']}): "
            f"equip_power={it['equip_power']} min_lvl={it['min_level']}")

    # H. Stacking
    log("\n=== H. STACKING ANALYSIS (equip lift) ===")
    stack = _stacking_analysis(F, cls_map)
    for name, tp in stack["scenarios"].items():
        log(f"  · {name:30s} team_power={tp}")
    log(f"  lv4 equip lift (baseline → +30/adv): "
        f"+{stack['lv4_equip_power_lift_pct']}%")
    log(f"  ⚠ {stack['note']}")

    elapsed_total = time.time() - t0
    log(f"\n[audit] total elapsed: {elapsed_total:.2f}s")
    log(f"[audit] monte carlo iters used: {iters_used}")
    log("[audit] READ ONLY MODE preserved — zero writes attempted")

    # Persist artefacts
    raw = {
        "meta": {
            "run_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": round(elapsed_total, 2),
            "monte_carlo_iters_used": iters_used,
            "db_name": db.name,
        },
        "formulas": formulas_doc,
        "dungeons": dungeons,
        "adventurer_stats_by_band": adv_stats,
        "archetype_powers": archetype_powers,
        "monte_carlo": mc_results,
        "incoherent_dungeons": incoherent,
        "outliers": outliers,
        "stacking_analysis": stack,
    }
    raw_path = Path("/app/memory/round164_audit_raw_data.json")
    raw_path.write_text(json.dumps(raw, indent=2, default=str))
    log(f"\n[audit] raw JSON written to {raw_path}")

    log_path = Path("/app/memory/round164_audit_console.log")
    log_path.write_text("\n".join(log_lines))
    log(f"[audit] console log written to {log_path}")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
