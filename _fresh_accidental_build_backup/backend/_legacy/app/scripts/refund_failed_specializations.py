"""ROUND 11.2 TASK 2 — One-shot CLI rimborso specializzazioni P0.

Strumento manuale per la recovery di account affetti dal bug pre-fix in cui
`POST /api/training/specialize/{id}` scalava gold (e potenzialmente
materiali) ma poi restituiva 500 senza completare la specializzazione.

Modi d'uso:

    # Dry-run (default, NESSUNA scrittura). Stampa il piano + report JSON.
    python -m app.scripts.refund_failed_specializations --dry-run

    # Esecuzione effettiva. Richiede `--apply` esplicito.
    python -m app.scripts.refund_failed_specializations --apply

    # Limita al singolo guild (utile per supporto mirato):
    python -m app.scripts.refund_failed_specializations --apply --guild-id <uuid>

Strategia di identificazione dei candidati al rimborso (Pre-fix):
  A) "Orphan signature pointer": adv ha `specialization.signature_item_id`
     ma nessuna inventory row matchante → applied parzialmente fallito.
  B) "Audit pending senza committed": dopo l'introduzione dei nuovi
     event_types `training_specialization_attempt`/`*_committed`, ogni
     attempt con status=pending e SENZA committed entro una finestra
     ragionevole è un candidato.

Idempotenza:
  Lo script controlla `audit_log.event_type=training_specialization_refund`
  con `metadata.original_attempt_id` (o `metadata.adventurer_id` per la
  modalità A storica) prima di scrivere ogni rimborso. Re-esecuzioni non
  duplicano mai un rimborso.

Sicurezza:
  - Non scrive mai senza `--apply`.
  - Stampa sempre il piano con email mascherate.
  - Audit event obbligatorio per ogni rimborso.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


def _mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "<unknown>"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


async def _has_refund_for_attempt(db, *, attempt_id: str | None,
                                  adventurer_id: str | None) -> bool:
    """Idempotency check: return True if we've already refunded this attempt."""
    query: dict = {"event_type": "training_specialization_refund"}
    if attempt_id:
        query["metadata.original_attempt_id"] = attempt_id
        if await db.audit_log.find_one(query, {"_id": 1}):
            return True
    if adventurer_id:
        # Mode A fallback (no attempt_id pre-fix). Match on adventurer.
        q2 = {
            "event_type": "training_specialization_refund",
            "metadata.adventurer_id": adventurer_id,
            "metadata.refund_mode": "orphan_signature_pointer",
        }
        if await db.audit_log.find_one(q2, {"_id": 1}):
            return True
    return False


async def _scan_orphan_pointers(db, *, guild_filter: str | None) -> list[dict]:
    """Mode A: adv.specialization.signature_item_id → inventory_items mancante."""
    candidates: list[dict] = []
    q: dict = {
        "specialization": {"$ne": None},
        "specialization.signature_item_id": {"$ne": None},
    }
    if guild_filter:
        q["guild_id"] = guild_filter
    async for adv in db.adventurers.find(q):
        sig_id = adv.get("specialization", {}).get("signature_item_id")
        if not sig_id:
            continue
        sig = await db.inventory_items.find_one(
            {"id": sig_id}, {"_id": 0, "id": 1},
        )
        if sig:
            continue  # signature exists → not a P0 case
        # Recover cost: training_grounds_level_at_apply → catalog.apply_cost
        from app.training.catalog import apply_cost_for_training_level
        tg_level = int(adv.get("specialization", {})
                       .get("training_grounds_level_at_apply", 1))
        cost = apply_cost_for_training_level(tg_level)
        already = await _has_refund_for_attempt(
            db, attempt_id=None, adventurer_id=adv.get("id"),
        )
        candidates.append({
            "mode": "orphan_signature_pointer",
            "guild_id": adv.get("guild_id"),
            "adventurer_id": adv.get("id"),
            "adventurer_name": adv.get("name"),
            "spec_slug": adv.get("specialization", {}).get("slug"),
            "cost_gold_to_refund": cost,
            "materials_to_refund": {},  # apply doesn't debit materials
            "applied_at": adv.get("specialization", {}).get("applied_at"),
            "already_refunded": already,
        })
    return candidates


async def _scan_pending_without_committed(db, *, guild_filter: str | None,
                                          min_age_seconds: int = 60) -> list[dict]:
    """Mode B: post-fix orphan attempts (debit happened, rollback never wrote)."""
    candidates: list[dict] = []
    now = datetime.now(timezone.utc)
    q: dict = {"event_type": "training_specialization_attempt"}
    if guild_filter:
        q["actor_guild_id"] = guild_filter
    async for ev in db.audit_log.find(q):
        attempt_id = (ev.get("metadata") or {}).get("attempt_id")
        if not attempt_id:
            continue
        # Skip if committed OR rolled_back already exists
        sibling = await db.audit_log.find_one({
            "metadata.attempt_id": attempt_id,
            "event_type": {"$in": [
                "training_specialization_committed",
                "training_specialization_rolled_back",
            ]},
        }, {"_id": 1})
        if sibling:
            continue
        # Age guard: skip very recent attempts (might still be in-flight).
        try:
            created = datetime.fromisoformat((ev.get("created_at") or "").replace("Z", "+00:00"))
            if (now - created).total_seconds() < min_age_seconds:
                continue
        except (ValueError, TypeError):
            continue
        already = await _has_refund_for_attempt(
            db, attempt_id=attempt_id,
            adventurer_id=(ev.get("metadata") or {}).get("adventurer_id"),
        )
        candidates.append({
            "mode": "pending_without_committed",
            "guild_id": ev.get("actor_guild_id"),
            "attempt_id": attempt_id,
            "adventurer_id": (ev.get("metadata") or {}).get("adventurer_id"),
            "spec_slug": (ev.get("metadata") or {}).get("spec_slug"),
            "cost_gold_to_refund": (ev.get("metadata") or {}).get("cost_gold", 0),
            "materials_to_refund": {},
            "attempt_at": ev.get("created_at"),
            "already_refunded": already,
        })
    return candidates


async def _enrich_owner_email(db, candidate: dict) -> None:
    g = await db.guilds.find_one(
        {"id": candidate["guild_id"]},
        {"_id": 0, "name": 1, "owner_user_id": 1, "public_id": 1},
    )
    candidate["guild_name"] = (g or {}).get("name")
    candidate["guild_public_id"] = (g or {}).get("public_id")
    owner = (g or {}).get("owner_user_id")
    if owner:
        u = await db.users.find_one({"id": owner}, {"_id": 0, "email": 1})
        candidate["owner_email_masked"] = _mask_email((u or {}).get("email"))
    else:
        candidate["owner_email_masked"] = "<no-owner>"


async def _apply_refund(db, candidate: dict) -> None:
    """Refund + write audit. Caller must check `already_refunded` first."""
    now_iso = datetime.now(timezone.utc).isoformat()
    gold = int(candidate.get("cost_gold_to_refund") or 0)
    if gold > 0:
        await db.guilds.update_one(
            {"id": candidate["guild_id"]},
            {"$inc": {"gold": gold}, "$set": {"updated_at": now_iso}},
        )
    # Detach orphan signature pointer (mode A) so the player isn't stuck
    # with a "specialized" flag pointing to nothing.
    if candidate["mode"] == "orphan_signature_pointer":
        await db.adventurers.update_one(
            {"id": candidate["adventurer_id"], "guild_id": candidate["guild_id"]},
            {"$set": {"specialization": None, "updated_at": now_iso}},
        )
    # Audit
    from app.audit.log import write_audit
    await write_audit(
        db,
        event_type="training_specialization_refund",
        actor_user_id=None,  # CLI tool — no human actor
        actor_guild_id=candidate["guild_id"],
        source="cli.refund_failed_specializations",
        related_entity_id=candidate.get("adventurer_id"),
        gold_delta=gold,
        metadata={
            "refund_mode": candidate["mode"],
            "original_attempt_id": candidate.get("attempt_id"),
            "adventurer_id": candidate.get("adventurer_id"),
            "spec_slug": candidate.get("spec_slug"),
            "refund_amount_gold": gold,
            "reason": "p0_atomicity_bug_round112",
            "applied_via": "cli_one_shot",
        },
    )


async def main_async(args: argparse.Namespace) -> int:
    load_dotenv("/app/backend/.env", override=True)
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]

    print(f"[refund] Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    if args.guild_id:
        print(f"[refund] Filtered to guild_id={args.guild_id}")

    mode_a = await _scan_orphan_pointers(db, guild_filter=args.guild_id)
    mode_b = await _scan_pending_without_committed(
        db, guild_filter=args.guild_id,
        min_age_seconds=args.min_age_seconds,
    )
    candidates = mode_a + mode_b
    for c in candidates:
        await _enrich_owner_email(db, c)

    pending = [c for c in candidates if not c["already_refunded"]]
    skipped = [c for c in candidates if c["already_refunded"]]
    total_gold = sum(int(c.get("cost_gold_to_refund") or 0) for c in pending)

    print(f"[refund] Candidates: total={len(candidates)} pending={len(pending)} "
          f"skipped_already_refunded={len(skipped)}")
    print(f"[refund] Total gold to refund: {total_gold}")
    print()
    for c in pending:
        print(f"  - mode={c['mode']:<28} guild={c.get('guild_public_id') or c['guild_id'][:8]}"
              f" owner={c.get('owner_email_masked')} adv={c.get('adventurer_id') and c['adventurer_id'][:8]}"
              f" spec={c.get('spec_slug')} gold={c.get('cost_gold_to_refund')}")

    # Write report file
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": not args.apply,
        "guild_filter": args.guild_id,
        "candidates_total": len(candidates),
        "pending": pending,
        "skipped_already_refunded": skipped,
        "total_gold_planned": total_gold,
    }
    out_path = f"/app/memory/round112_refund_report_{'apply' if args.apply else 'dryrun'}_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[refund] Report: {out_path}")

    if not args.apply:
        print("[refund] Dry-run complete. Re-run with --apply to execute.")
        cli.close()
        return 0

    # APPLY mode
    print("\n[refund] APPLYING refunds...")
    applied_count = 0
    for c in pending:
        try:
            await _apply_refund(db, c)
            applied_count += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[refund]   FAILED {c.get('adventurer_id')}: {exc}")
    print(f"[refund] Done. Applied {applied_count}/{len(pending)} refunds.")
    cli.close()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Default. Stampa il piano, NESSUNA scrittura.")
    parser.add_argument("--apply", action="store_true",
                        help="Esegui i rimborsi. Senza questo flag siamo in dry-run.")
    parser.add_argument("--guild-id", type=str, default=None,
                        help="Limita lo scan a un singolo guild (UUID).")
    parser.add_argument("--min-age-seconds", type=int, default=60,
                        help="Ignora attempts pending più recenti di N sec.")
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
