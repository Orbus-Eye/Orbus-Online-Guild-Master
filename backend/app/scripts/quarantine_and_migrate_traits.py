"""ROUND 6A.2b — Trait hygiene script.

Two idempotent migrations in one script (run in order):

  1. **Quarantine** suspicious traits (regex-matched test/admin leftovers
     that escaped the original `is_test=true` flag). Sets
     `is_test=True` + `is_active=False`. NEVER hard-deletes. Emits one
     `trait_quarantined` audit row per affected doc (idempotent: if the
     row already exists, skip).

  2. **Migrate display_name_it** for every active legitimate trait. Uses a
     manual mapping of canonical EN/snake_case names → human IT strings,
     with snake_case→Title Case fallback for unknowns. Idempotent: if a
     doc already has a non-empty `display_name_it`, leave it untouched.

Refuses APP_ENV=production.
"""
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# Regex patterns that identify clearly-test/admin trait names that leaked
# into the production pool. Add new patterns here as detected.
QUARANTINE_PATTERNS = [
    (re.compile(r"^X\d+$"), "X[0-9]+ placeholder"),
    (re.compile(r"^shorty\d+$"), "shorty[0-9]+ placeholder"),
    (re.compile(r"^AdminTrait_", re.I), "AdminTrait_* prefix"),
    (re.compile(r"^MyTrait[_X]", re.I), "MyTrait* placeholder"),
    (re.compile(r"^Trait_X$"), "Trait_X placeholder"),
    (re.compile(r"^Test", re.I), "Test* prefix"),
]


# Canonical IT translations. Keys are LOWERCASED versions of the EN name
# (so "Sharp Eye" and "sharp_eye" both hit "sharp eye" after norm).
IT_DICT = {
    "bandit past": "Passato da Bandito",
    "beast-friend": "Amico delle Bestie",
    "blessed": "Benedetto",
    "brave": "Coraggioso",
    "bull-strong": "Forte come un Toro",
    "clumsy": "Goffo",
    "cursed coin": "Moneta Maledetta",
    "devout": "Devoto",
    "disciplined": "Disciplinato",
    "faithless": "Senza Fede",
    "fast reader": "Lettore Veloce",
    "frail": "Fragile",
    "fragile": "Fragile",
    "glassmaker's child": "Figlio del Vetraio",
    "greedy": "Avido",
    "hollow-eyed": "Occhi Vuoti",
    "inspired": "Ispirato",
    "insomniac": "Insonne",
    "iron-willed": "Volontà di Ferro",
    "iron_will": "Volontà di Ferro",
    "lightfoot": "Piè Leggero",
    "loyal": "Leale",
    "lucky": "Fortunato",
    "quick learner": "Apprendista Veloce",
    "reckless": "Avventato",
    "salt-tongued": "Lingua Salata",
    "scholar": "Studioso",
    "sharp eye": "Occhio Acuto",
    "sharp_eye": "Occhio Acuto",
    "sickly": "Malaticcio",
    "slow-witted": "Lento di Cervello",
    "stargazer": "Osservatore di Stelle",
    "storm-marked": "Segnato dalla Tempesta",
    "sworn vow": "Voto Solenne",
    "tavern-born": "Nato in Taverna",
    "twin-born": "Gemello",
    "veteran's eye": "Occhio del Veterano",
    "wanderer": "Errante",
    "weak-armed": "Braccio Debole",
}


def to_it(name: str) -> str:
    """Resolve a trait EN name to its IT display string."""
    norm = (name or "").strip().lower()
    if norm in IT_DICT:
        return IT_DICT[norm]
    # Fallback: snake_case → Title Case.
    cleaned = name.replace("_", " ").replace("-", " ").strip()
    parts = [p.capitalize() for p in cleaned.split() if p]
    return " ".join(parts) or name


def main() -> int:
    if os.environ.get("APP_ENV") == "production":
        print("ERROR: refuses to run with APP_ENV=production", file=sys.stderr)
        return 2

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = MongoClient(mongo_url)
    db = client[db_name]
    now = datetime.now(timezone.utc).isoformat()

    # ─── Phase 1: Quarantine ──────────────────────────────────────────────
    all_active = list(db.adventurer_traits.find(
        {"is_test": {"$ne": True}}, {"_id": 0}
    ))
    quarantined = []
    for t in all_active:
        name = t.get("name") or ""
        for rx, reason in QUARANTINE_PATTERNS:
            if rx.search(name):
                # Idempotency guard: skip if an audit row already exists.
                already = db.audit_log.find_one({
                    "event_type": "trait_quarantined",
                    "related_entity_id": t["id"],
                })
                if not already:
                    db.audit_log.insert_one({
                        "event_type": "trait_quarantined",
                        "actor_user_id": "system",
                        "actor_guild_id": None,
                        "related_entity_id": t["id"],
                        "metadata": {
                            "entity_type": "trait",
                            "name": name,
                            "reason": reason,
                        },
                        "source": "script:quarantine_and_migrate_traits",
                        "created_at": now,
                    })
                db.adventurer_traits.update_one(
                    {"id": t["id"]},
                    {"$set": {"is_test": True, "is_active": False, "updated_at": now}},
                )
                quarantined.append((t["id"], name, reason))
                break

    # ─── Phase 2: display_name_it migration ───────────────────────────────
    # Run on EVERY trait (including the ones we just quarantined) so the
    # UI never shows raw `X710` when an old adventurer still references
    # the trait via traits[] subdoc.
    migrated = []
    for t in db.adventurer_traits.find({}, {"_id": 0}):
        if t.get("display_name_it"):
            continue
        dn = to_it(t.get("name") or "")
        db.adventurer_traits.update_one(
            {"id": t["id"]},
            {"$set": {"display_name_it": dn, "updated_at": now}},
        )
        migrated.append((t["id"], t.get("name"), dn))

    # ─── Report ────────────────────────────────────────────────────────────
    print(f"Quarantined: {len(quarantined)}")
    for qid, name, reason in quarantined:
        print(f"  - {name!r:30} → {reason}")
    print(f"\nMigrated display_name_it: {len(migrated)}")
    sample = migrated[:8]
    for mid, name, dn in sample:
        print(f"  - {name!r:30} → {dn!r}")
    if len(migrated) > 8:
        print(f"  ... and {len(migrated) - 8} more")

    # ─── Phase 3: backfill display_name_it on adventurer.traits[] subdocs ──
    # Adventurer trait subdocs were snapshotted at recruit time WITHOUT
    # display_name_it. Cross-reference the master collection by trait id (or
    # name fallback) and inject the IT display string so all roster/raid UIs
    # render IT immediately, including legacy adventurers.
    master_by_id = {}
    master_by_name = {}
    for t in db.adventurer_traits.find({}, {"_id": 0, "id": 1, "name": 1, "display_name_it": 1}):
        if t.get("display_name_it"):
            master_by_id[t.get("id")] = t["display_name_it"]
            master_by_name[t.get("name", "").strip().lower()] = t["display_name_it"]

    advs_backfilled = 0
    for adv in db.adventurers.find({}, {"_id": 0, "id": 1, "traits": 1}):
        traits = adv.get("traits") or []
        changed = False
        for sub in traits:
            if isinstance(sub, dict) and not sub.get("display_name_it"):
                tid = sub.get("id") or sub.get("trait_id")
                name_norm = (sub.get("name") or "").strip().lower()
                dni = master_by_id.get(tid) or master_by_name.get(name_norm)
                if dni:
                    sub["display_name_it"] = dni
                    changed = True
        if changed:
            db.adventurers.update_one(
                {"id": adv["id"]},
                {"$set": {"traits": traits, "updated_at": now}},
            )
            advs_backfilled += 1
    print(f"\nAdventurer subdoc backfill: {advs_backfilled} adventurer(s) updated")

    return 0


if __name__ == "__main__":
    sys.exit(main())
