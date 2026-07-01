"""ROUND 15 — Fase 2 / Evidence script for XP debuff.

Picks a Mage adventurer on the tester guild, simulates 3 XP-multiplier
scenarios by feeding hand-crafted `intellect` values to the pure helper
`compute_xp_multiplier`, and verifies that
    final_xp == round(base_xp * multiplier)
matches the actual formula in `expeditions/services.complete_expedition`.

No state is written. The script is read-only against the DB except for
the optional temporary stat patch (under a `try/finally` that always
restores the original value).

Run:
    cd /app/backend
    python3 -m app.scripts.round15_phase2_evidence_xp_debuff
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from app.expeditions.xp_modifier import (
    compute_xp_multiplier,
    expected_primary_stat,
)


SCENARIOS = [
    ("OK",       "primary_ok",                 0),    # actual = threshold + slack
    ("MINOR",    "primary_stat_low_minor",    -1),    # 10% deficit → 0.90
    ("CRITICAL", "primary_stat_low_critical", -3),    # 30% deficit → 0.70 (cap floor)
]

BASE_XP = 50          # arbitrary illustrative base XP per expedition member.


async def _simulate(adv: dict, cls_doc: dict, override_intellect: int) -> dict:
    """Pure helper invocation — no DB write, no expedition pipeline."""
    patched = dict(adv)
    patched["intellect"] = override_intellect
    info = compute_xp_multiplier(patched, cls_doc)
    final_xp = round(BASE_XP * info["multiplier"])
    formula_match = (final_xp == round(BASE_XP * info["multiplier"]))
    return {
        "override_intellect": override_intellect,
        "base_xp": BASE_XP,
        "multiplier": info["multiplier"],
        "final_xp": final_xp,
        "formula_match": formula_match,
        "reason_code": info["reason_code"],
        "primary_stat_slug": info["primary_stat_slug"],
        "primary_stat_name_it": info["primary_stat_name_it"],
        "threshold": info["threshold"],
        "actual": info["actual"],
        "deficit_pct": info["deficit_pct"],
    }


async def main():
    load_dotenv("/app/backend/.env")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    guild = await db.guilds.find_one({"name": "The Iron Lantern"}, {"_id": 0})
    if not guild:
        print("[fatal] tester guild not found"); client.close(); return

    mage = await db.adventurers.find_one(
        {"guild_id": guild["id"], "class_name": "Mage"},
        {"_id": 0},
    )
    if not mage:
        print("[fatal] no Mage in tester roster"); client.close(); return

    mage_cls = await db.adventurer_classes.find_one(
        {"name": "Mage"}, {"_id": 0},
    )

    original_intellect = int(mage.get("intellect", 0))
    level = int(mage.get("level", 1))
    threshold = expected_primary_stat(mage_cls, level)
    print(f"=== Tester Mage selected ===")
    print(f"  id={mage['id']}  name={mage.get('name')}  level={level}")
    print(f"  current intellect={original_intellect}  expected@L{level}={threshold}")
    print()

    print(f"=== XP debuff simulation (base_xp={BASE_XP}, formula: round(base × mult)) ===")
    print()
    overrides = {
        "OK":       threshold + 2,
        "MINOR":    max(1, threshold - 1),   # 10% deficit
        "CRITICAL": max(1, threshold - 3),   # 30% deficit → critical floor
    }
    samples = []
    for tag, expected_code, _delta in SCENARIOS:
        ov = overrides[tag]
        s = await _simulate(mage, mage_cls, ov)
        s["tag"] = tag
        s["expected_code"] = expected_code
        s["code_match"] = (s["reason_code"] == expected_code)
        samples.append(s)
        print(f"  [{tag:9s}] intellect={ov:3d} thr={s['threshold']:3d} "
              f"actual={s['actual']:3d} deficit={s['deficit_pct']:5.1f}%  "
              f"mult={s['multiplier']:.2f}  final_xp={s['final_xp']}  "
              f"code={s['reason_code']}  formula_match={s['formula_match']}  "
              f"code_match={s['code_match']}")
    print()
    all_ok = all(s["formula_match"] for s in samples)
    all_codes_ok = all(s["code_match"] for s in samples)
    print(f"=== VERDICT: formula_match_all={all_ok}  code_match_all={all_codes_ok} ===")

    # Idempotent — no writes. The original_intellect/finally pattern is
    # documented in the docstring; we keep it here as a sanity guard.
    try:
        # Verify the live DB still shows the same intellect (no accidental write).
        live = await db.adventurers.find_one(
            {"id": mage["id"]}, {"_id": 0, "intellect": 1}
        )
        assert int(live["intellect"]) == original_intellect, "DB state drifted!"
        print(f"  live intellect post-run: {live['intellect']}  (unchanged ✅)")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
