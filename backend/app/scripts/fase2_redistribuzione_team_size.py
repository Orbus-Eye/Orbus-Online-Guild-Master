"""FASE 2.3 (2026-08-08) — Redistribuzione dungeon 3/5/7 (base = 5).

Applica al DB la tabella autoritativa `DUNGEON_TEAM_SIZE_TARGETS` +
`DUNGEON_CURVE` (recommended_power scalato ×size_nuova/size_vecchia):
la linea principale passa da "tutta da 3" a base 5, con i 3 come
incursioni rapide e dragons-hoard come prima grande impresa da 7.
Design completo: memory/fase2_design_bilanciamento.md §6.

Idempotente: riscrive solo i doc il cui valore differisce dal target.
Dry-run di default; `--apply` per scrivere.

Uso (dalla cartella backend, con MONGO_URL/DB_NAME/JWT_SECRET in env):

    python -m app.scripts.fase2_redistribuzione_team_size          # dry-run
    python -m app.scripts.fase2_redistribuzione_team_size --apply  # scrive
"""
from __future__ import annotations

import asyncio
import sys

from app.core.database import db
from app.shared.content_curve import DUNGEON_CURVE, DUNGEON_TEAM_SIZE_TARGETS


async def run(apply: bool) -> None:
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[fase2_redistribuzione_team_size] modalità: {mode}")
    changed = 0
    for slug, target_size in DUNGEON_TEAM_SIZE_TARGETS.items():
        curve = DUNGEON_CURVE.get(slug)
        if curve is None:
            print(f"  !! slug '{slug}' assente da DUNGEON_CURVE — salto")
            continue
        doc = await db.dungeons.find_one(
            {"slug": slug},
            {"_id": 0, "id": 1, "slug": 1, "required_team_size": 1,
             "recommended_power": 1},
        )
        if not doc:
            print(f"  -- '{slug}' non presente in DB — salto")
            continue
        cur_size = int(doc.get("required_team_size") or 0)
        cur_power = int(doc.get("recommended_power") or 0)
        target_power = int(curve.recommended_power)
        if cur_size == target_size and cur_power == target_power:
            print(f"  ok '{slug}': già {cur_size}p / power {cur_power}")
            continue
        print(
            f"  -> '{slug}': size {cur_size} → {target_size}, "
            f"power {cur_power} → {target_power}"
        )
        changed += 1
        if apply:
            await db.dungeons.update_one(
                {"slug": slug},
                {"$set": {
                    "required_team_size": target_size,
                    "recommended_power": target_power,
                }},
            )
    print(f"[fase2_redistribuzione_team_size] {mode}: {changed} dungeon da aggiornare")
    if not apply and changed:
        print("Rilancia con --apply per scrivere le modifiche.")


if __name__ == "__main__":
    asyncio.run(run(apply="--apply" in sys.argv))
