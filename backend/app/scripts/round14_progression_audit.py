"""ROUND 14 P2 — Progression curve simulator (read-only).

Projects gold accumulation, roster power, expedition success rate and
milestones for 4 archetypal player scenarios across a 30-day horizon.
The simulation is in-memory only; the script does not write to Mongo
and reads only catalogue tables (`dungeons`).

Run:
    cd /app/backend
    export $(grep -v '^#' .env | xargs)
    python3 -m app.scripts.round14_progression_audit
    python3 -m app.scripts.round14_progression_audit --days 30 --seed 42

Output:
    - Stdout: per-scenario table + Markdown summary.
    - File: /app/memory/round14_progression_audit_<ts>.json

Scenarios are immutable defaults but each field is overridable from
`--scenarios-json <path>` to support future tuning sweeps.

Read-only contract:
    Only `db.dungeons.find(...)` is used. No INSERT/UPDATE/DELETE.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import secrets
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

# Pure formulas — re-used so we never drift from runtime behaviour.
from app.expeditions.formulas import compute_success_chance
from app.shared.constants import (
    RECRUITMENT_COST_GOLD,
    XP_THRESHOLD_PER_LEVEL,
)


MEMORY_DIR = Path("/app/memory")
DEFAULT_DAYS = 30

# Scenarios (per spec). All values are *daily* unless noted. `raid_chance_eligible`
# is fired only after the roster crosses the raid threshold (12 adventurers).
SCENARIOS: dict[str, dict] = {
    "casual": {
        "sessions_per_day": 1,
        "expeditions_per_day": 2,
        "raids_per_day_if_eligible": 0,
        "arena_matches_per_day": 0,
        "training_active": False,
        "skip_days_at_start": 0,
    },
    "active": {
        "sessions_per_day": 2,
        "expeditions_per_day": 5,
        "raids_per_day_if_eligible": 1,
        "arena_matches_per_day": 2,
        "training_active": False,
        "skip_days_at_start": 0,
    },
    "power": {
        "sessions_per_day": 3,
        "expeditions_per_day": 8,
        "raids_per_day_if_eligible": 2,
        "arena_matches_per_day": 5,
        "training_active": True,
        "skip_days_at_start": 0,
    },
    "returning": {
        "sessions_per_day": 1,
        "expeditions_per_day": 3,
        "raids_per_day_if_eligible": 0,
        "arena_matches_per_day": 0,
        "training_active": False,
        "skip_days_at_start": 5,
    },
}

RAID_ROSTER_THRESHOLD = 12
INITIAL_GOLD = 100
TRAINING_DAILY_GOLD_COST = 30   # Approx avg cost; conservative.
ARENA_DAILY_GOLD_REWARD_AVG = 25   # Win rate ≈ 50% with bonus.
SNAPSHOT_DAYS = (1, 7, 14, 30)


def _make_rng(seed: int | None):
    if seed is None:
        return secrets.SystemRandom()
    return random.Random(seed)


async def _load_dungeons(db) -> list[dict]:
    """Read-only pull of the dungeon catalogue, sorted by recommended_power.
    """
    rows: list[dict] = []
    cur = db.dungeons.find({}, {
        "_id": 0, "slug": 1, "name": 1, "recommended_power": 1,
        "base_gold_reward": 1, "base_xp_reward": 1,
    })
    async for d in cur:
        if d.get("base_gold_reward") is not None and d.get("recommended_power") is not None:
            rows.append(d)
    rows.sort(key=lambda d: int(d.get("recommended_power") or 0))
    return rows


def _starter_adventurer() -> dict:
    """Approximate stats of a Tier-1 recruit. Stats follow the live seed.
    """
    return {
        "level": 1,
        "experience": 0,
        # Base stats roughly average across classes.
        "strength": 6, "agility": 6, "intellect": 6,
        "endurance": 6, "faith": 6,
        # Rarity Common → power_score ~30, equipment_power 0 initially.
        "total_power_snapshot": 32,
        "class_role": "DPS",
    }


def _team_power(adventurers: list[dict]) -> int:
    """Sum of total_power_snapshot + role composition bonuses (Tank/Healer/DPS)."""
    base = sum(a["total_power_snapshot"] for a in adventurers)
    roles = {a.get("class_role") for a in adventurers}
    bonus = 0
    if "Tank" in roles: bonus += 5
    if "Healer" in roles: bonus += 5
    if "DPS" in roles: bonus += 5
    if {"Tank", "Healer", "DPS"}.issubset(roles): bonus += 10
    return base + bonus


def _pick_dungeon(dungeons: list[dict], team_power: int) -> dict | None:
    """Player picks the highest-tier dungeon where success_chance >= 50.
    Falls back to the easiest if even Tier-1 is out of reach."""
    eligible = [d for d in dungeons if compute_success_chance(team_power, int(d.get("recommended_power") or 0)) >= 50]
    if eligible:
        return eligible[-1]
    return dungeons[0] if dungeons else None


def _apply_xp(adv: dict, gained: int) -> None:
    """Mirrors `_resolve_levelup` from app.expeditions.services."""
    adv["experience"] += gained
    while adv["experience"] >= adv["level"] * XP_THRESHOLD_PER_LEVEL:
        threshold = adv["level"] * XP_THRESHOLD_PER_LEVEL
        adv["experience"] -= threshold
        adv["level"] += 1
        # Approx: +1 stat (strength), refresh snapshot.
        adv["strength"] += 1
        adv["total_power_snapshot"] += 3  # +1 stat + +2 from level*2 formula


def _simulate(rng, scenario_name: str, scenario: dict, dungeons: list[dict], days: int) -> dict:
    """Run a single scenario for `days` days. Returns a structured report.
    """
    gold = INITIAL_GOLD
    roster: list[dict] = []
    expeditions_completed = 0
    raids_completed = 0
    arena_played = 0
    gold_in = 0
    gold_out = 0
    milestones: dict[str, int | None] = {
        "first_recruit_day": None,
        "first_expedition_day": None,
        "first_5_roster_day": None,
        "first_12_roster_day": None,
        "first_raid_day": None,
    }
    snapshots: dict[int, dict] = {}

    for day in range(1, days + 1):
        # Skip phase (only for `returning`).
        if day <= scenario["skip_days_at_start"]:
            if day in SNAPSHOT_DAYS:
                snapshots[day] = {
                    "gold": gold,
                    "roster_size": len(roster),
                    "team_power": _team_power(roster) if roster else 0,
                    "avg_level": 0,
                    "expeditions_completed": expeditions_completed,
                    "raids_completed": raids_completed,
                    "phase": "skip",
                }
            continue

        # 1) Recruitment — fill towards 5 first, then towards 12 if scenario
        # is mid/heavy. The player only recruits if affordable.
        target_roster = 5
        if scenario["expeditions_per_day"] >= 5:
            target_roster = 12 if scenario["raids_per_day_if_eligible"] > 0 else 8
        while len(roster) < target_roster and gold >= RECRUITMENT_COST_GOLD:
            gold -= RECRUITMENT_COST_GOLD
            gold_out += RECRUITMENT_COST_GOLD
            roster.append(_starter_adventurer())
            if milestones["first_recruit_day"] is None:
                milestones["first_recruit_day"] = day
            if len(roster) >= 5 and milestones["first_5_roster_day"] is None:
                milestones["first_5_roster_day"] = day
            if len(roster) >= RAID_ROSTER_THRESHOLD and milestones["first_12_roster_day"] is None:
                milestones["first_12_roster_day"] = day

        # 2) Expeditions for the day. Needs ≥5 adventurers for a party.
        if len(roster) >= 5:
            party = sorted(roster, key=lambda a: -a["total_power_snapshot"])[:5]
            tp = _team_power(party)
            for _ in range(scenario["expeditions_per_day"]):
                dungeon = _pick_dungeon(dungeons, tp)
                if not dungeon:
                    break
                sc = compute_success_chance(tp, int(dungeon["recommended_power"]))
                roll = rng.randint(1, 100)
                success = roll <= sc
                if success:
                    g = int(dungeon["base_gold_reward"])
                else:
                    g = int(int(dungeon["base_gold_reward"]) * 0.25)
                gold += g
                gold_in += g
                expeditions_completed += 1
                if milestones["first_expedition_day"] is None:
                    milestones["first_expedition_day"] = day

                # XP distributed to party members.
                xp_share = int(dungeon.get("base_xp_reward", 0))
                for adv in party:
                    _apply_xp(adv, xp_share if success else int(xp_share * 0.5))

        # 3) Raid (only if eligible).
        if len(roster) >= RAID_ROSTER_THRESHOLD:
            for _ in range(scenario["raids_per_day_if_eligible"]):
                # Raid baseline: +400g per success (mid-tier); we use 60% success
                # rate to remain conservative versus the live boss formula.
                if rng.randint(1, 100) <= 60:
                    gold += 400
                    gold_in += 400
                    raids_completed += 1
                    if milestones["first_raid_day"] is None:
                        milestones["first_raid_day"] = day
                else:
                    # Partial reward.
                    gold += 80
                    gold_in += 80

        # 4) Arena: net positive on average per spec.
        for _ in range(scenario["arena_matches_per_day"]):
            arena_played += 1
            delta = ARENA_DAILY_GOLD_REWARD_AVG // max(scenario["arena_matches_per_day"], 1)
            gold += delta
            gold_in += delta

        # 5) Training: a fixed daily gold sink.
        if scenario["training_active"]:
            if gold >= TRAINING_DAILY_GOLD_COST:
                gold -= TRAINING_DAILY_GOLD_COST
                gold_out += TRAINING_DAILY_GOLD_COST
                # +2 power on best adventurer (training output proxy).
                if roster:
                    best = max(roster, key=lambda a: a["total_power_snapshot"])
                    best["total_power_snapshot"] += 2

        # Snapshot
        if day in SNAPSHOT_DAYS:
            snapshots[day] = {
                "gold": gold,
                "roster_size": len(roster),
                "team_power": _team_power(roster) if roster else 0,
                "avg_level": round(sum(a["level"] for a in roster) / max(len(roster), 1), 2) if roster else 0,
                "expeditions_completed": expeditions_completed,
                "raids_completed": raids_completed,
                "phase": "active",
            }

    # Warnings
    warnings: list[str] = []
    if gold < 0:
        warnings.append(f"gold_negative_eod: gold={gold}")
    if snapshots.get(7, {}).get("gold", 0) <= 0:
        warnings.append("gold_stuck_at_day7")
    if scenario_name not in ("returning",):
        if snapshots.get(14, {}).get("expeditions_completed", 0) == 0:
            warnings.append("no_progress_by_day14")
    if scenario_name == "power":
        if snapshots.get(30, {}).get("roster_size", 0) < RAID_ROSTER_THRESHOLD:
            warnings.append("power_scenario_never_raid_eligible_day30")

    return {
        "scenario": scenario_name,
        "params": scenario,
        "days_simulated": days,
        "snapshots": {str(k): v for k, v in sorted(snapshots.items())},
        "final": {
            "gold": gold,
            "gold_in_total": gold_in,
            "gold_out_total": gold_out,
            "roster_size": len(roster),
            "team_power": _team_power(roster) if roster else 0,
            "expeditions_completed": expeditions_completed,
            "raids_completed": raids_completed,
            "arena_played": arena_played,
            "expedition_success_rate_pct": "—",  # we don't separately track success/fail above; left explicit
        },
        "milestones": milestones,
        "warnings": warnings,
    }


async def main():
    parser = argparse.ArgumentParser(description="Round 14 — progression curve audit (read-only).")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--scenarios-json", default=None,
                        help="Path JSON con override scenari (stessa struttura di SCENARIOS).")
    args = parser.parse_args()

    rng = _make_rng(args.seed)
    seed_label = f"seed={args.seed}" if args.seed is not None else "rng=SystemRandom"

    scenarios = dict(SCENARIOS)
    if args.scenarios_json:
        scenarios = json.loads(Path(args.scenarios_json).read_text())

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    dungeons = await _load_dungeons(db)
    client.close()

    if not dungeons:
        print("[ERR] Nessun dungeon trovato nel catalogo. Esegui i seed prima di rieseguire.")
        return

    reports = []
    for name, sc in scenarios.items():
        reports.append(_simulate(rng, name, sc, dungeons, args.days))

    payload = {
        "schema": "round14_progression_audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": args.days,
        "rng": seed_label,
        "snapshots_at": list(SNAPSHOT_DAYS),
        "constants": {
            "INITIAL_GOLD": INITIAL_GOLD,
            "RECRUITMENT_COST_GOLD": RECRUITMENT_COST_GOLD,
            "XP_THRESHOLD_PER_LEVEL": XP_THRESHOLD_PER_LEVEL,
            "RAID_ROSTER_THRESHOLD": RAID_ROSTER_THRESHOLD,
        },
        "scenarios": reports,
        "all_warnings": [{"scenario": r["scenario"], "warning": w}
                         for r in reports for w in r["warnings"]],
    }

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = MEMORY_DIR / f"round14_progression_audit_{ts}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    # Markdown summary
    print("\n# Progression Audit — Round 14")
    print(f"- generato: {payload['generated_at']}")
    print(f"- orizzonte: {args.days} giorni · rng: {seed_label}")
    print(f"- report file: {out}")
    print()
    print("| Scenario | Gold d7 | Gold d14 | Gold d30 | PWR d7 | PWR d30 | Roster d30 | Exp d30 | Raid d30 | Milestones |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in reports:
        s = r["snapshots"]
        ms = r["milestones"]
        ms_compact = ", ".join(
            f"{k.replace('first_', '').replace('_day', '')}=d{v}"
            for k, v in ms.items() if v is not None
        ) or "—"
        print(
            f"| {r['scenario']} | {s.get('7', {}).get('gold', '—')} | {s.get('14', {}).get('gold', '—')} "
            f"| {s.get('30', {}).get('gold', '—')} | {s.get('7', {}).get('team_power', '—')} "
            f"| {s.get('30', {}).get('team_power', '—')} | {s.get('30', {}).get('roster_size', '—')} "
            f"| {r['final']['expeditions_completed']} | {r['final']['raids_completed']} | {ms_compact} |"
        )

    total_warnings = len(payload["all_warnings"])
    print()
    if total_warnings == 0:
        print(":white_check_mark: Nessuno scenario bloccato. Curve coerenti.")
    else:
        print(f":warning: {total_warnings} warning emessi:")
        for w in payload["all_warnings"]:
            print(f"  - [{w['scenario']}] {w['warning']}")


if __name__ == "__main__":
    asyncio.run(main())
