"""ROUND 16.5.4c — ADJ-3 seed pack Warlock + Alchemist + Druid.

Approvato dal PM il 2026-07-02 (opzione A, Epic Lv8, no Legendary):
  * Warlock:   10 nuovi item (4 weapon + 3 armor + 3 accessory)
  * Alchemist: 10 nuovi item (4 weapon + 3 armor + 3 accessory)
  * Druid:      2 nuovi item (armor Rare Lv5 + armor Epic Lv8, colma il gap
                Rare/Epic evidenziato dall'audit R16.5.4c-ADJ-3).

Contract:
  * Solo `insert_one` sul `db.items`. **No update, no delete** sui documenti
    esistenti. Se lo slug esiste già → skip (log + counter).
  * Dry-run di default; `--apply` per scrivere.
  * Idempotenza: secondo `--apply` = 0 insert.
  * Snapshot pre-change su `/app/memory/round1654c_adj3_snapshot.json`.
  * Audit event `CLASS_COVERAGE_SEED_APPLIED` con matched/inserted/skipped.
  * Nessuna modifica a drop / expedition / recipe / reward / economy / PvP /
    premium: lo script tocca UNICAMENTE la collection `items`.
  * Rarity in forma canonica Capitalized (`Common`, `Uncommon`, `Rare`,
    `Epic`) coerente con ADJ-1.

Uso:
    python -m app.scripts.round1654c_class_coverage_seed --dry-run
    python -m app.scripts.round1654c_class_coverage_seed --apply
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

SNAPSHOT_PATH = Path("/app/memory/round1654c_adj3_snapshot.json")
AUDIT_EVENT = "CLASS_COVERAGE_SEED_APPLIED"


# ── 22 item hardcoded — proposta approvata ────────────────────────────
# Nota curva (verificata su catalog esistente):
#   Common Lv1  → P:1, +1 stat singolo
#   Uncommon Lv3 → P:2, +2 stat (spread)
#   Rare Lv5    → P:4, +2 primary + 1-2 secondary
#   Epic Lv8    → P:6, +4 primary + 2 secondary
# Nessun Legendary. Nessun outlier rispetto alle medie del catalog.

def _item(*, slug: str, name: str, item_type: str, rarity: str,
          lvl: int, power: int, cls: str,
          weapon_tags: list[str] | None = None,
          armor_tags: list[str] | None = None,
          equipment_tags: list[str] | None = None,
          stat_tags: list[str] | None = None,
          **stat_bonuses: int) -> dict:
    """Costruisce un dict item con lo schema canonico del catalog."""
    doc = {
        "slug": slug,
        "name": name,
        "item_type": item_type,
        "rarity": rarity,
        "required_adventurer_level": lvl,
        "power_score": power,
        "recommended_classes": [cls],
        "class_tags": [cls],
        "stat_tags": stat_tags or [],
        "equipment_tags": equipment_tags or [],
        "is_active": True,
        "affects_combat": True,
        # Round 16.5.4c origin marker (traceable in DB).
        "seed_source": "round1654c_class_coverage",
    }
    if item_type == "weapon" and weapon_tags is not None:
        doc["weapon_tags"] = weapon_tags
    if item_type == "armor" and armor_tags is not None:
        doc["armor_tags"] = armor_tags
    for stat, val in stat_bonuses.items():
        if val:
            doc[f"{stat}_bonus"] = int(val)
    return doc


NEW_ITEMS: list[dict] = [
    # ═══════════════ WARLOCK — 10 item ═══════════════════════════════════
    # Weapon (4)
    _item(slug="warlock_apprentice_tome", name="Tomo del Novizio",
          item_type="weapon", rarity="Common", lvl=1, power=1, cls="warlock",
          weapon_tags=["tome", "arcane"], stat_tags=["intellect"],
          intellect=1),
    _item(slug="warlock_hex_grimoire", name="Grimorio del Malèfico",
          item_type="weapon", rarity="Uncommon", lvl=3, power=2, cls="warlock",
          weapon_tags=["tome", "arcane"], stat_tags=["intellect"],
          intellect=2),
    _item(slug="warlock_shadowbound_grimoire",
          name="Grimorio dell'Ombra Vincolata",
          item_type="weapon", rarity="Rare", lvl=5, power=4, cls="warlock",
          weapon_tags=["tome", "arcane"],
          stat_tags=["intellect", "faith"],
          intellect=2, faith=1),
    _item(slug="warlock_witchking_codex", name="Codice del Re-Strega",
          item_type="weapon", rarity="Epic", lvl=8, power=6, cls="warlock",
          weapon_tags=["tome", "arcane"],
          stat_tags=["intellect", "faith"],
          intellect=4, faith=2),
    # Armor (3)
    _item(slug="warlock_novice_robe", name="Veste del Novizio Occulto",
          item_type="armor", rarity="Common", lvl=1, power=1, cls="warlock",
          armor_tags=["robe", "cloth", "light"], stat_tags=["intellect"],
          intellect=1),
    _item(slug="warlock_shadowweave_robe", name="Veste in Trama d'Ombra",
          item_type="armor", rarity="Rare", lvl=5, power=4, cls="warlock",
          armor_tags=["robe", "light"], stat_tags=["intellect", "faith"],
          intellect=2, faith=2),
    _item(slug="warlock_coven_mantle", name="Mantello del Coven",
          item_type="armor", rarity="Epic", lvl=8, power=6, cls="warlock",
          armor_tags=["robe", "light"], stat_tags=["intellect", "agility"],
          intellect=4, agility=2),
    # Accessory (3)
    _item(slug="warlock_cursed_pendant", name="Pendente Maledetto",
          item_type="accessory", rarity="Common", lvl=1, power=1,
          cls="warlock", equipment_tags=["pendant", "arcane"],
          stat_tags=["intellect"], intellect=1),
    _item(slug="warlock_hex_sigil", name="Sigillo del Malocchio",
          item_type="accessory", rarity="Rare", lvl=5, power=4,
          cls="warlock", equipment_tags=["sigil", "arcane"],
          stat_tags=["intellect", "faith", "agility"],
          intellect=2, faith=1, agility=1),
    _item(slug="warlock_patron_seal", name="Sigillo del Patrono",
          item_type="accessory", rarity="Epic", lvl=8, power=6,
          cls="warlock", equipment_tags=["seal", "arcane"],
          stat_tags=["intellect", "faith"],
          intellect=4, faith=2),

    # ═══════════════ ALCHEMIST — 10 item ═════════════════════════════════
    # Weapon (4)
    _item(slug="alchemist_apprentice_flask",
          name="Boccetta dell'Apprendista",
          item_type="weapon", rarity="Common", lvl=1, power=1,
          cls="alchemist",
          weapon_tags=["alchemical_flask", "arcane"],
          stat_tags=["intellect"], intellect=1),
    _item(slug="alchemist_elemental_flask", name="Boccetta Elementale",
          item_type="weapon", rarity="Uncommon", lvl=3, power=2,
          cls="alchemist",
          weapon_tags=["alchemical_flask", "arcane"],
          stat_tags=["intellect"], intellect=2),
    _item(slug="alchemist_transmuters_tome", name="Tomo del Trasmutatore",
          item_type="weapon", rarity="Rare", lvl=5, power=4,
          cls="alchemist",
          weapon_tags=["tome", "arcane"],
          stat_tags=["intellect", "agility", "endurance"],
          intellect=2, agility=1, endurance=1),
    _item(slug="alchemist_philosophers_flask",
          name="Boccetta del Filosofo",
          item_type="weapon", rarity="Epic", lvl=8, power=6,
          cls="alchemist",
          weapon_tags=["alchemical_flask", "arcane"],
          stat_tags=["intellect", "agility"],
          intellect=4, agility=2),
    # Armor (3)
    _item(slug="alchemist_apron", name="Grembiule dell'Alchimista",
          item_type="armor", rarity="Common", lvl=1, power=1,
          cls="alchemist", armor_tags=["light", "robe"],
          stat_tags=["intellect"], intellect=1),
    _item(slug="alchemist_ember_lined_vest",
          name="Panciotto dalla Fodera d'Ember",
          item_type="armor", rarity="Rare", lvl=5, power=4,
          cls="alchemist", armor_tags=["light"],
          stat_tags=["intellect", "endurance"],
          intellect=2, endurance=2),
    _item(slug="alchemist_quintessence_robe",
          name="Veste della Quintessenza",
          item_type="armor", rarity="Epic", lvl=8, power=6,
          cls="alchemist", armor_tags=["robe", "light"],
          stat_tags=["intellect", "endurance"],
          intellect=4, endurance=2),
    # Accessory (3)
    _item(slug="alchemist_reagent_pouch", name="Borsa dei Reagenti",
          item_type="accessory", rarity="Common", lvl=1, power=1,
          cls="alchemist", equipment_tags=["pouch", "arcane"],
          stat_tags=["intellect"], intellect=1),
    _item(slug="alchemist_alembic_pendant", name="Pendente dell'Alambicco",
          item_type="accessory", rarity="Rare", lvl=5, power=4,
          cls="alchemist", equipment_tags=["pendant", "arcane"],
          stat_tags=["intellect", "agility", "endurance"],
          intellect=2, agility=1, endurance=1),
    _item(slug="alchemist_transmutation_medallion",
          name="Medaglione della Trasmutazione",
          item_type="accessory", rarity="Epic", lvl=8, power=6,
          cls="alchemist", equipment_tags=["medallion", "arcane"],
          stat_tags=["intellect", "endurance"],
          intellect=4, endurance=2),

    # ═══════════════ DRUID — 2 armor gap fillers ═════════════════════════
    _item(slug="druid_grovewarden_mantle",
          name="Manto del Guardiano del Bosco",
          item_type="armor", rarity="Rare", lvl=5, power=4, cls="druid",
          armor_tags=["leather", "natural", "light"],
          stat_tags=["faith", "intellect"],
          faith=2, intellect=2),
    _item(slug="druid_elder_vestments",
          name="Paramenti dell'Anziano Druido",
          item_type="armor", rarity="Epic", lvl=8, power=6, cls="druid",
          armor_tags=["cloth", "natural", "light"],
          stat_tags=["faith", "intellect"],
          faith=4, intellect=2),
]


# ── Curva max ammessa per rarity/level (dal catalog audit R16.5.4c) ───
# Se la proposta supera anche solo di 1 il max di catalog per (type, rarity, lvl)
# lo script si ferma con "power_creep" e chiede review. Serve come guardrail
# programmatico per la clausola PM #8.
POWER_MAX_BY_BUCKET: dict[tuple[str, str, int], int] = {
    ("weapon", "common", 1): 5,
    ("weapon", "uncommon", 3): 8,
    ("weapon", "rare", 5): 4,
    ("weapon", "epic", 8): 7,
    ("armor", "common", 1): 4,
    ("armor", "uncommon", 3): 7,
    ("armor", "rare", 5): 4,
    ("armor", "epic", 8): 6,
    ("accessory", "common", 1): 2,
    ("accessory", "uncommon", 3): 6,
    ("accessory", "rare", 5): 10,
    ("accessory", "epic", 8): 6,
}


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _verify_no_power_creep() -> list[str]:
    """Ritorna lista di violazioni (empty se tutto OK)."""
    problems: list[str] = []
    for it in NEW_ITEMS:
        key = (it["item_type"], (it["rarity"] or "").lower(),
               int(it["required_adventurer_level"]))
        max_allowed = POWER_MAX_BY_BUCKET.get(key)
        if max_allowed is None:
            problems.append(
                f"{it['slug']}: bucket {key} non ha un massimo definito, "
                f"impossibile verificare power creep"
            )
            continue
        if int(it["power_score"]) > max_allowed:
            problems.append(
                f"{it['slug']}: power_score={it['power_score']} > "
                f"max_catalog={max_allowed} per {key}"
            )
    return problems


def _verify_schema() -> list[str]:
    """Verifica statica delle clausole 10/11/12/13 (schema-side)."""
    problems: list[str] = []
    seen_slugs: set[str] = set()
    for it in NEW_ITEMS:
        slug = it["slug"]
        if slug in seen_slugs:
            problems.append(f"slug duplicato nella proposta: {slug}")
        seen_slugs.add(slug)
        # Clausola 10 — recommended_classes non vuoto.
        if not it.get("recommended_classes"):
            problems.append(f"{slug}: recommended_classes vuoto")
        # Clausola 11 — slot canonico.
        if it["item_type"] not in ("weapon", "armor", "accessory"):
            problems.append(f"{slug}: item_type non canonico "
                            f"({it['item_type']})")
        # Clausola 12 — required_adventurer_level >= 1.
        if int(it.get("required_adventurer_level", 0)) < 1:
            problems.append(
                f"{slug}: required_adventurer_level non valido"
            )
        # Clausola 13 — rarity Capitalized (ADJ-1 canonical form).
        if it["rarity"] not in ("Common", "Uncommon", "Rare", "Epic"):
            problems.append(f"{slug}: rarity non canonica ({it['rarity']})")
    return problems


async def _verify_no_collision(db) -> list[str]:
    """Clausola 9 — nessuno degli slug proposti deve esistere già."""
    slugs = [it["slug"] for it in NEW_ITEMS]
    existing = await db.items.find(
        {"slug": {"$in": slugs}}, {"_id": 0, "slug": 1}
    ).to_list(length=None)
    if not existing:
        return []
    return [f"slug in collision: {e['slug']}" for e in existing]


async def _snapshot_pre_change() -> None:
    payload = {
        "generated_at": _utc_iso_now(),
        "item_count": len(NEW_ITEMS),
        "slugs": [it["slug"] for it in NEW_ITEMS],
        "items": NEW_ITEMS,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    SNAPSHOT_PATH.write_text(body + "\n", encoding="utf-8")
    print(f"[snapshot] {SNAPSHOT_PATH} · sha256={_sha256(body)[:16]}…")


async def _audit_emit(db, *, inserted: int, skipped: int,
                     collisions: list[str]) -> None:
    try:
        await db.audit_events.insert_one({
            "event_type": AUDIT_EVENT,
            "actor_user_id": None,
            "actor_guild_id": None,
            "related_entity_id": None,
            "source": "script.round1654c_class_coverage_seed",
            "occurred_at": _utc_iso_now(),
            "metadata": {
                "matched": len(NEW_ITEMS),
                "inserted": inserted,
                "skipped": skipped,
                "collisions_sample": collisions[:20],
            },
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit emit failed: {exc}", file=sys.stderr)


async def _coverage_before(db) -> dict:
    out: dict = {}
    for cls in ("warlock", "alchemist", "druid"):
        cov = {}
        for typ in ("weapon", "armor", "accessory"):
            cov[typ] = await db.items.count_documents({
                "item_type": typ,
                "$or": [{"recommended_classes": cls},
                       {"class_tags": cls}],
                "is_active": {"$ne": False},
            })
        out[cls] = cov
    return out


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL o DB_NAME mancante nell'ambiente",
              file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name}")
    print(f"[plan] proposta: {len(NEW_ITEMS)} item nuovi")

    # ── Verifiche statiche (clausole 8-13) ────────────────────────────
    schema_issues = _verify_schema()
    if schema_issues:
        print("[FAIL] schema violations:")
        for p in schema_issues:
            print(f"  - {p}")
        return 3

    creep = _verify_no_power_creep()
    if creep:
        print("[FAIL] power creep violations (clausola 8):")
        for p in creep:
            print(f"  - {p}")
        return 4

    collisions = await _verify_no_collision(db)
    if collisions:
        # ROUND 16.5.4c ADJ-3 — Idempotenza pulita: se TUTTI gli slug della
        # proposta esistono già → seed già applicato → exit(0). Se solo
        # ALCUNI → stato inconsistente (crash parziale), STOP e chiedi.
        if len(collisions) == len(NEW_ITEMS):
            print(f"\n[idempotent] Tutti {len(NEW_ITEMS)} gli item della "
                  f"proposta esistono già nel DB. Seed già applicato. "
                  f"0 modifiche.")
            return 0
        print(f"[FAIL] slug collision (clausola 9): {len(collisions)} "
              f"su {len(NEW_ITEMS)} slug esistono già (stato inconsistente):")
        for c in collisions:
            print(f"  - {c}")
        print("STOP — non applicare. Chiedi al PM come procedere.")
        return 5

    # ── Coverage baseline (clausola 14 - "before") ────────────────────
    coverage_before = await _coverage_before(db)
    print("\n[coverage BEFORE]")
    for cls, cov in coverage_before.items():
        print(f"  {cls:10s} weapon={cov['weapon']:>3d} "
              f"armor={cov['armor']:>3d} accessory={cov['accessory']:>3d}")

    # ── Report per classe (breakdown insert) ──────────────────────────
    from collections import Counter, defaultdict
    per_class = defaultdict(lambda: Counter())
    for it in NEW_ITEMS:
        cls = it["recommended_classes"][0]
        per_class[cls][it["item_type"]] += 1
    print("\n[insert plan per class]")
    for cls in ("warlock", "alchemist", "druid"):
        c = per_class[cls]
        print(f"  {cls:10s} weapon+{c['weapon']:<2d} "
              f"armor+{c['armor']:<2d} accessory+{c['accessory']:<2d} "
              f"(total {sum(c.values())})")

    # ── Verifica finale delle 14 clausole PM ──────────────────────────
    print("\n[14 clausole PM]")
    print(f"  1. 22 INSERT previsti ................ "
          f"{len(NEW_ITEMS)} → {'✅' if len(NEW_ITEMS)==22 else '❌'}")
    print(f"  2. 0 UPDATE ........................ ✅ (script only INSERT)")
    print(f"  3. 0 DELETE ........................ ✅ (script only INSERT)")
    print(f"  4. No drop table changes ........... ✅ "
          f"(script tocca solo `items`)")
    print(f"  5. No reward changes ............... ✅")
    print(f"  6. No economy changes .............. ✅")
    print(f"  7. No recipe/crafting changes ...... ✅")
    print(f"  8. No power creep vs catalog ....... "
          f"{'✅' if not creep else '❌'}")
    print(f"  9. Slug unici (no collision) ....... "
          f"{'✅' if not collisions else '❌'}")
    print(f" 10. recommended_classes popolato .... "
          f"{'✅' if not any('recommended_classes vuoto' in p for p in schema_issues) else '❌'}")
    print(f" 11. Slot canonico .................. "
          f"{'✅' if not any('item_type non canonico' in p for p in schema_issues) else '❌'}")
    print(f" 12. required_adventurer_level OK ... "
          f"{'✅' if not any('required_adventurer_level' in p for p in schema_issues) else '❌'}")
    print(f" 13. Rarity canonica (Capitalized) .. "
          f"{'✅' if not any('rarity non canonica' in p for p in schema_issues) else '❌'}")
    print(f" 14. Coverage prima catalogata ...... ✅ (vedi sopra)")

    if dry_run:
        print("\n[dry-run] Tutte le 14 clausole PASS. Rieseguire con "
              "--apply per scrivere.")
        return 0

    # ── APPLY ─────────────────────────────────────────────────────────
    await _snapshot_pre_change()
    now = _utc_iso_now()
    inserted = 0
    skipped: list[str] = []
    for it in NEW_ITEMS:
        # Re-check anti-race collision al momento dell'insert.
        exists = await db.items.count_documents({"slug": it["slug"]})
        if exists:
            skipped.append(it["slug"])
            continue
        doc = dict(it)
        doc["id"] = str(uuid.uuid4())
        doc["created_at"] = now
        doc["updated_at"] = now
        await db.items.insert_one(doc)
        inserted += 1

    print(f"\n[apply] inserted={inserted} skipped={len(skipped)}")
    if skipped:
        for s in skipped:
            print(f"  [skip] {s} già presente")
    await _audit_emit(db, inserted=inserted, skipped=len(skipped),
                      collisions=skipped)

    coverage_after = await _coverage_before(db)
    print("\n[coverage AFTER]")
    for cls, cov in coverage_after.items():
        b = coverage_before[cls]
        print(f"  {cls:10s} weapon={b['weapon']:>3d}→{cov['weapon']:>3d} "
              f"armor={b['armor']:>3d}→{cov['armor']:>3d} "
              f"accessory={b['accessory']:>3d}→{cov['accessory']:>3d}")

    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__ or "")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true", default=True)
    grp.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    dry_run = not args.apply_
    rc = asyncio.run(run(dry_run=dry_run))
    sys.exit(rc)


if __name__ == "__main__":
    main()
