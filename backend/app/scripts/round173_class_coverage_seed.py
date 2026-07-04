"""ROUND 17.3 Step 2 C1P1 — Class coverage patch (Monk/Warlock/Alchemist).

Approvato dal PM il 2026-07-04 (opzione P-A, bucket 1/3/5/8 safe, no Legendary,
no power creep, 20 item):
  * Monk:      4 nuovi accessory (coverage 1 → 5)
  * Warlock:   8 nuovi item (2 weapon + 3 armor + 3 accessory) — 4/3/3 → 6/6/6
  * Alchemist: 8 nuovi item (2 weapon + 3 armor + 3 accessory) — 4/3/3 → 6/6/6

Contract (identico a R16.5.4c):
  * Solo `insert_one` sul `db.items`. **No update, no delete** sui documenti
    esistenti. Se lo slug esiste già → skip (log + counter).
  * Dry-run di default; `--apply` per scrivere.
  * Idempotenza: secondo `--apply` = 0 insert.
  * Snapshot pre-change su `/app/memory/round173step2_c1p1_snapshot.json`.
  * Audit event `CLASS_COVERAGE_SEED_APPLIED` con matched/inserted/skipped.
  * Nessuna modifica a drop / expedition / recipe / reward / economy / PvP /
    premium: lo script tocca UNICAMENTE la collection `items`.
  * Rarity in forma canonica Capitalized (`Common`, `Uncommon`, `Rare`,
    `Epic`) coerente con ADJ-1.
  * Bucket allineati a POWER_MAX_BY_BUCKET (Lv 1/3/5/8) — NO Lv 6/9/12.

Uso:
    python -m app.scripts.round173_class_coverage_seed --dry-run
    python -m app.scripts.round173_class_coverage_seed --apply
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

SNAPSHOT_PATH = Path("/app/memory/round173step2_c1p1_snapshot.json")
AUDIT_EVENT = "CLASS_COVERAGE_SEED_APPLIED"


# ── Curva (identica a R16.5.4c) ────────────────────────────────────────
#   Common Lv1   → P:1-2, +1 stat singolo
#   Uncommon Lv3 → P:2-4, +2 stat (spread)
#   Rare Lv5     → P:4-5, +2 primary + 1 secondary
#   Epic Lv8     → P:6,   +3 primary + 2 secondary
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
        # Round 17.3 Step 2 origin marker (traceable in DB).
        "seed_source": "round173_class_coverage_step2",
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
    # ═══════════════ MONK — 4 accessory ══════════════════════════════════
    # Coverage attuale: 13w / 6a / 1acc → target 13w / 6a / 5acc
    _item(slug="monk_jade_cord", name="Cordone di Giada",
          item_type="accessory", rarity="Common", lvl=1, power=1, cls="monk",
          equipment_tags=["cord", "natural", "light"],
          stat_tags=["agility"],
          agility=1),
    _item(slug="monk_serpent_anklet", name="Cavigliera del Serpente",
          item_type="accessory", rarity="Uncommon", lvl=3, power=3, cls="monk",
          equipment_tags=["anklet", "natural", "light"],
          stat_tags=["agility"],
          agility=2),
    _item(slug="monk_mantra_bead", name="Grano da Mantra",
          item_type="accessory", rarity="Rare", lvl=5, power=5, cls="monk",
          equipment_tags=["bead", "arcane", "light"],
          stat_tags=["agility", "endurance"],
          agility=2, endurance=1),
    _item(slug="monk_thousand_hands_bracer",
          name="Bracciale delle Mille Mani",
          item_type="accessory", rarity="Epic", lvl=8, power=6, cls="monk",
          equipment_tags=["bracer", "martial", "medium"],
          stat_tags=["agility", "endurance"],
          agility=3, endurance=2),

    # ═══════════════ WARLOCK — 8 item ═══════════════════════════════════
    # Coverage attuale: 4w / 3a / 3acc → target 6w / 6a / 6acc
    # Weapon (+2)
    _item(slug="warlock_apprentice_grimoire",
          name="Grimorio dell'Apprendista",
          item_type="weapon", rarity="Uncommon", lvl=3, power=4, cls="warlock",
          weapon_tags=["tome", "arcane"],
          stat_tags=["intellect"],
          intellect=2),
    _item(slug="warlock_pact_binder", name="Legatore del Patto",
          item_type="weapon", rarity="Rare", lvl=5, power=4, cls="warlock",
          weapon_tags=["tome", "arcane"],
          stat_tags=["intellect", "faith"],
          intellect=2, faith=1),
    # Armor (+3)
    _item(slug="warlock_hex_focus_robe", name="Veste del Focus Malèfico",
          item_type="armor", rarity="Common", lvl=1, power=2, cls="warlock",
          armor_tags=["cloth", "arcane", "light"],
          stat_tags=["intellect"],
          intellect=1),
    _item(slug="warlock_shadow_mail", name="Cotta d'Ombra",
          item_type="armor", rarity="Uncommon", lvl=3, power=3, cls="warlock",
          armor_tags=["cloth", "dark", "medium"],
          stat_tags=["intellect", "endurance"],
          intellect=2, endurance=1),
    _item(slug="warlock_covenant_robe", name="Veste del Vecchio Patto",
          item_type="armor", rarity="Rare", lvl=5, power=4, cls="warlock",
          armor_tags=["cloth", "arcane", "medium"],
          stat_tags=["intellect", "endurance"],
          intellect=2, endurance=1),
    # Accessory (+3)
    _item(slug="warlock_fetish_charm", name="Feticcio Malevolo",
          item_type="accessory", rarity="Common", lvl=1, power=1, cls="warlock",
          equipment_tags=["trinket", "arcane"],
          stat_tags=["intellect"],
          intellect=1),
    _item(slug="warlock_imp_collar", name="Collare dell'Imp",
          item_type="accessory", rarity="Uncommon", lvl=3, power=3, cls="warlock",
          equipment_tags=["trinket", "dark"],
          stat_tags=["intellect"],
          intellect=2),
    _item(slug="warlock_black_ring", name="Anello del Nero Patto",
          item_type="accessory", rarity="Rare", lvl=5, power=5, cls="warlock",
          equipment_tags=["ring", "arcane"],
          stat_tags=["intellect", "faith"],
          intellect=2, faith=1),

    # ═══════════════ ALCHEMIST — 8 item ═════════════════════════════════
    # Coverage attuale: 4w / 3a / 3acc → target 6w / 6a / 6acc
    # Weapon (+2)
    _item(slug="alchemist_glass_wand", name="Bacchetta di Vetro",
          item_type="weapon", rarity="Uncommon", lvl=3, power=4,
          cls="alchemist",
          weapon_tags=["focus", "arcane"],
          stat_tags=["intellect"],
          intellect=2),
    _item(slug="alchemist_catalyst_flask", name="Fiala del Catalizzatore",
          item_type="weapon", rarity="Rare", lvl=5, power=4,
          cls="alchemist",
          weapon_tags=["focus", "arcane"],
          stat_tags=["intellect", "endurance"],
          intellect=2, endurance=1),
    # Armor (+3)
    _item(slug="alchemist_brewers_apron", name="Grembiule del Distillatore",
          item_type="armor", rarity="Common", lvl=1, power=2,
          cls="alchemist",
          armor_tags=["cloth", "artisan", "light"],
          stat_tags=["intellect"],
          intellect=1),
    _item(slug="alchemist_quicksilver_vest", name="Corpetto Mercuriale",
          item_type="armor", rarity="Uncommon", lvl=3, power=3,
          cls="alchemist",
          armor_tags=["cloth", "artisan", "medium"],
          stat_tags=["intellect", "endurance"],
          intellect=2, endurance=1),
    _item(slug="alchemist_philosophers_plate", name="Placca del Filosofo",
          item_type="armor", rarity="Rare", lvl=5, power=4,
          cls="alchemist",
          armor_tags=["leather", "artisan", "medium"],
          stat_tags=["intellect", "endurance"],
          intellect=1, endurance=2),
    # Accessory (+3)
    _item(slug="alchemist_brew_belt", name="Cintura Distillante",
          item_type="accessory", rarity="Common", lvl=1, power=1,
          cls="alchemist",
          equipment_tags=["belt", "artisan"],
          stat_tags=["endurance"],
          endurance=1),
    _item(slug="alchemist_catalyst_ring", name="Anello Catalitico",
          item_type="accessory", rarity="Uncommon", lvl=3, power=3,
          cls="alchemist",
          equipment_tags=["ring", "arcane"],
          stat_tags=["intellect"],
          intellect=2),
    _item(slug="alchemist_golden_vial", name="Fiala d'Oro",
          item_type="accessory", rarity="Rare", lvl=5, power=5,
          cls="alchemist",
          equipment_tags=["trinket", "artisan"],
          stat_tags=["intellect", "endurance"],
          intellect=2, endurance=1),
]

# Sanity checks statici a livello modulo (fail-fast in caso di editing).
assert len(NEW_ITEMS) == 20, f"expected 20 items, got {len(NEW_ITEMS)}"


# ── POWER_MAX_BY_BUCKET (importato da R16.5.4c per non duplicare) ─────
# Se non trovabile, fallback locale con gli stessi valori.
try:
    from app.scripts.round1654c_class_coverage_seed import (
        POWER_MAX_BY_BUCKET,
    )
except Exception:
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
    """Verifica statica: slug unici, slot canonico, level>=1, rarity canonica."""
    problems: list[str] = []
    seen_slugs: set[str] = set()
    for it in NEW_ITEMS:
        slug = it["slug"]
        if slug in seen_slugs:
            problems.append(f"slug duplicato nella proposta: {slug}")
        seen_slugs.add(slug)
        if not it.get("recommended_classes"):
            problems.append(f"{slug}: recommended_classes vuoto")
        if it["item_type"] not in ("weapon", "armor", "accessory"):
            problems.append(f"{slug}: item_type non canonico "
                            f"({it['item_type']})")
        if int(it.get("required_adventurer_level", 0)) < 1:
            problems.append(
                f"{slug}: required_adventurer_level non valido"
            )
        if it["rarity"] not in ("Common", "Uncommon", "Rare", "Epic"):
            problems.append(f"{slug}: rarity non canonica ({it['rarity']})")
        # No Legendary — hard guard (clausola PM P-A).
        if it["rarity"] == "Legendary":
            problems.append(f"{slug}: Legendary vietato (clausola P-A)")
    return problems


async def _verify_no_collision(db) -> list[str]:
    """Nessuno degli slug proposti deve esistere già."""
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
        "round": "R17.3-Step2-C1P1",
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
            "source": "script.round173_class_coverage_step2",
            "occurred_at": _utc_iso_now(),
            "metadata": {
                "round": "R17.3-Step2-C1P1",
                "matched": len(NEW_ITEMS),
                "inserted": inserted,
                "skipped": skipped,
                "collisions_sample": collisions[:20],
            },
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit emit failed: {exc}", file=sys.stderr)


async def _coverage(db) -> dict:
    out: dict = {}
    for cls in ("monk", "warlock", "alchemist"):
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
    print(f"[mode] {mode} · db={db_name} · round=R17.3-Step2-C1P1")
    print(f"[plan] proposta: {len(NEW_ITEMS)} item nuovi (bucket 1/3/5/8)")

    schema_issues = _verify_schema()
    if schema_issues:
        print("[FAIL] schema violations:")
        for p in schema_issues:
            print(f"  - {p}")
        return 3

    creep = _verify_no_power_creep()
    if creep:
        print("[FAIL] power creep violations:")
        for p in creep:
            print(f"  - {p}")
        return 4

    collisions = await _verify_no_collision(db)
    if collisions:
        if len(collisions) == len(NEW_ITEMS):
            print(f"\n[idempotent] Tutti {len(NEW_ITEMS)} gli item della "
                  f"proposta esistono già nel DB. Seed già applicato. "
                  f"0 modifiche.")
            return 0
        print(f"[FAIL] slug collision: {len(collisions)} "
              f"su {len(NEW_ITEMS)} slug esistono già (stato inconsistente):")
        for c in collisions:
            print(f"  - {c}")
        print("STOP — non applicare. Chiedi al PM come procedere.")
        return 5

    coverage_before = await _coverage(db)
    print("\n[coverage BEFORE]")
    for cls, cov in coverage_before.items():
        print(f"  {cls:10s} weapon={cov['weapon']:>3d} "
              f"armor={cov['armor']:>3d} accessory={cov['accessory']:>3d}")

    from collections import Counter, defaultdict
    per_class = defaultdict(lambda: Counter())
    for it in NEW_ITEMS:
        cls = it["recommended_classes"][0]
        per_class[cls][it["item_type"]] += 1
    print("\n[insert plan per class]")
    for cls in ("monk", "warlock", "alchemist"):
        c = per_class[cls]
        print(f"  {cls:10s} weapon+{c['weapon']:<2d} "
              f"armor+{c['armor']:<2d} accessory+{c['accessory']:<2d} "
              f"(total {sum(c.values())})")

    print("\n[clausole P-A]")
    print(f"  1. 20 INSERT previsti ................ "
          f"{len(NEW_ITEMS)} → {'✅' if len(NEW_ITEMS) == 20 else '❌'}")
    print(f"  2. 0 UPDATE .......................... ✅ (script only INSERT)")
    print(f"  3. 0 DELETE .......................... ✅ (script only INSERT)")
    print(f"  4. No drop table changes ............. ✅")
    print(f"  5. No reward changes ................. ✅")
    print(f"  6. No economy changes ................ ✅")
    print(f"  7. No Legendary ...................... "
          f"{'✅' if not any(i['rarity']=='Legendary' for i in NEW_ITEMS) else '❌'}")
    print(f"  8. No power creep vs POWER_MAX_BY_BUCKET "
          f"{'✅' if not creep else '❌'}")
    print(f"  9. Bucket 1/3/5/8 solo ............... "
          f"{'✅' if all(i['required_adventurer_level'] in (1,3,5,8) for i in NEW_ITEMS) else '❌'}")
    print(f" 10. Slug unici (no collision) ........ "
          f"{'✅' if not collisions else '❌'}")
    print(f" 11. Slot canonico .................... "
          f"{'✅' if not any('item_type non canonico' in p for p in schema_issues) else '❌'}")
    print(f" 12. Rarity canonica Capitalized ...... "
          f"{'✅' if not any('rarity non canonica' in p for p in schema_issues) else '❌'}")
    print(f" 13. recommended_classes popolato ..... "
          f"{'✅' if not any('recommended_classes vuoto' in p for p in schema_issues) else '❌'}")
    print(f" 14. Coverage prima catalogata ........ ✅ (vedi sopra)")

    if dry_run:
        print("\n[dry-run] Tutte le clausole PASS. Rieseguire con "
              "--apply per scrivere.")
        return 0

    await _snapshot_pre_change()
    now = _utc_iso_now()
    inserted = 0
    skipped: list[str] = []
    for it in NEW_ITEMS:
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

    coverage_after = await _coverage(db)
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
