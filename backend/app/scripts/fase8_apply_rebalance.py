"""FASE 8A/8B (2026-08-08) — Applica al DB il rebalance di difficoltà.

Aggiorna (idempotente, solo i doc che differiscono):
  * `dungeons.recommended_power` dai valori FASE 8A di `DUNGEON_CURVE`;
  * `raid_dungeons.recommended_power_combined` dai valori di `RAID_CURVE`
    (usati anche dal nuovo PWR gate dei raid, FASE 8B).

Dry-run di default; `--apply` per scrivere. Ogni modifica è stampata
(auditabile). Compatibile con `fase2_redistribuzione_team_size` (le
team size restano di competenza di quello script; qui solo i poteri).

Uso (dalla cartella backend, env MONGO_URL/DB_NAME/JWT_SECRET):
    python -m app.scripts.fase8_apply_rebalance          # dry-run
    python -m app.scripts.fase8_apply_rebalance --apply  # scrive
"""
from __future__ import annotations

import asyncio
import sys

from app.core.database import db
from app.shared.content_curve import DUNGEON_CURVE, RAID_CURVE


async def run(apply: bool) -> None:
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[fase8_apply_rebalance] modalità: {mode}")
    changed = 0

    for slug, curve in DUNGEON_CURVE.items():
        doc = await db.dungeons.find_one(
            {"slug": slug}, {"_id": 0, "slug": 1, "recommended_power": 1},
        )
        if not doc:
            print(f"  -- dungeon '{slug}' non in DB — salto")
            continue
        cur = int(doc.get("recommended_power") or 0)
        target = int(curve.recommended_power)
        if cur == target:
            print(f"  ok '{slug}': recommended_power già {cur}")
            continue
        print(f"  -> '{slug}': recommended_power {cur} → {target}")
        changed += 1
        if apply:
            await db.dungeons.update_one(
                {"slug": slug},
                {"$set": {"recommended_power": target}},
            )

    for slug, curve in RAID_CURVE.items():
        doc = await db.raid_dungeons.find_one(
            {"slug": slug},
            {"_id": 0, "slug": 1, "recommended_power_combined": 1},
        )
        if not doc:
            print(f"  -- raid '{slug}' non in DB — salto")
            continue
        cur = int(doc.get("recommended_power_combined") or 0)
        target = int(curve.recommended_power)
        if cur == target:
            print(f"  ok raid '{slug}': già {cur}")
            continue
        print(f"  -> raid '{slug}': recommended_power_combined {cur} → {target}")
        changed += 1
        if apply:
            await db.raid_dungeons.update_one(
                {"slug": slug},
                {"$set": {"recommended_power_combined": target}},
            )

    print(f"[fase8_apply_rebalance] {mode}: {changed} documenti da aggiornare")
    if not apply and changed:
        print("Rilancia con --apply per scrivere le modifiche.")


if __name__ == "__main__":
    asyncio.run(run(apply="--apply" in sys.argv))
