"""ROUND 15 — Fase 2 / Task A1: idempotent backfill for item compatibility tags.

Adds the following fields to every active item document in `items`:

    weapon_tags:           list[str]   (only on item_type='weapon')
    armor_tags:            list[str]   (only on item_type='armor')
    class_tags:            list[str]   (slugs of recommended classes)
    role_tags:             list[str]   (e.g. ["tank", "dps_melee"])
    stat_tags:             list[str]   (derived from *_bonus fields > 0)
    recommended_classes:   list[str]   (explicit best-fit classes)
    is_universal:          bool
    required_class_optional: str|None  (hard-lock: signature items only)

Rules (deterministic, slug + name + stat-based):
    1. Signature items (slug startswith 'spec_signature_'):
       - required_class_optional = mapped class slug
       - is_universal = False
       - tags derived from the rest of the rules
    2. Weapons → infer weapon_tags by name keyword (sword/axe/bow/staff/...).
       Recommended classes derived from the dominant stat bonus + tag.
    3. Armor → infer armor_tags by name keyword (mail/plate/leather/cloth/robe).
    4. Accessories with NO stat dominance → is_universal = True.
    5. stat_tags = ["strength"] if strength_bonus > 0 etc.

Idempotency contract:
    Re-running on a clean DB produces 0 updates. Only writes a field if
    it is None/empty/different.

Audit:
    Emits an `audit_logs` row per touched item:
        event = 'item_tags_seeded_round15_phase2'

Run:
    cd /app/backend
    export $(grep -v '^#' .env | xargs)
    python3 -m app.scripts.round15_seed_item_tags
    python3 -m app.scripts.round15_seed_item_tags --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


# Signature item → mapped class slug (signature/legendary catalog).
SIGNATURE_CLASS_MAP: dict[str, str] = {
    "spec_signature_truestrike_bow": "ranger",
    "spec_signature_bloodied_greataxe": "berserker",
    "spec_signature_silent_kris": "assassin",
    "spec_signature_storm_rod": "mage",
    "spec_signature_corrupted_blade": "necromancer",
    "spec_signature_twin_blades": "rogue",
    "spec_signature_breakers_gauntlets": "warrior",
    "spec_signature_runic_aegis": "paladin",
    "drake_slayer_blade": "warrior",
    "drake_slayer_helm": "warrior",
    "drake_slayer_chest": "warrior",
}

# Stat → preferred classes (used when a non-signature item has clear
# stat dominance).
STAT_TO_CLASSES = {
    "strength": ["warrior", "paladin", "berserker"],
    "agility": ["rogue", "ranger", "assassin", "monk"],
    "intellect": ["mage", "necromancer", "bard"],
    "endurance": ["warrior", "paladin", "berserker"],
    "faith": ["priest", "druid", "paladin"],
}

STAT_TO_ROLE_TAGS = {
    "strength": ["tank", "dps_melee"],
    "agility": ["dps_melee", "dps_ranged", "stealth"],
    "intellect": ["dps_caster", "support"],
    "endurance": ["tank", "frontline"],
    "faith": ["healer_dedicated", "healer_aoe", "support"],
}


def _norm(s: str) -> str:
    return (s or "").lower().replace("'", "").replace("-", " ").replace("_", " ")


def infer_weapon_tags(item: dict) -> list[str]:
    name = _norm(item.get("name", "") + " " + (item.get("slug") or ""))
    tags: list[str] = []
    if any(k in name for k in (" sword", " blade", "claymore", "longsword", "shortsword", "rapier", "kris", "arming")):
        tags.append("sword")
        if any(k in name for k in ("two", "great", "claymore", "long")):
            tags.append("two_handed")
        if "rapier" in name or "shortsword" in name or "kris" in name:
            tags.append("finesse")
    if "dagger" in name or "knife" in name:
        tags += ["dagger", "finesse"]
    if "axe" in name:
        tags.append("axe")
        if "great" in name or "two" in name:
            tags.append("two_handed")
    if "mace" in name or "warhammer" in name or "hammer" in name or "flail" in name or "cudgel" in name or "rosary" in name:
        tags.append("mace")
        if "warhammer" in name or "great" in name:
            tags.append("two_handed")
    if "bow" in name or "crossbow" in name or "sling" in name:
        tags += ["bow", "ranged"]
    if "spear" in name or "pitchfork" in name:
        tags += ["spear", "two_handed"]
    if "staff" in name or "rod" in name:
        tags += ["staff", "arcane"]
    if "wand" in name or "focus" in name:
        tags += ["wand", "arcane"]
    if "grimoire" in name or "tome" in name or "book" in name:
        tags += ["grimoire", "arcane"]
    if "scythe" in name:
        tags += ["scythe", "dark"]
    if "flute" in name or "instrument" in name or "lute" in name or "songsteel" in name:
        tags += ["instrument", "sonic"]
    if "scepter" in name or "sceptre" in name:
        tags += ["mace", "holy"]
    if "fang" in name and "drake" in name:
        tags.append("two_handed")
    return sorted(set(tags))


def infer_armor_tags(item: dict) -> list[str]:
    name = _norm(item.get("name", "") + " " + (item.get("slug") or ""))
    tags: list[str] = []
    if any(k in name for k in ("plate", "half plate", "platemail")):
        tags += ["heavy", "plate"]
    if "mail" in name or "chainmail" in name or "chain" in name:
        tags.append("heavy" if "chainmail" in name or "plate" in name else "medium")
        tags.append("mail")
    if "scale" in name or "dragonscale" in name:
        tags += ["heavy", "scale"]
    if "leather" in name or "jerkin" in name or "studded" in name:
        tags += ["light", "leather"]
    if "robe" in name or "vestment" in name or "weave" in name:
        tags += ["cloth", "robe", "light"]
    if "tunic" in name or "hempcloth" in name:
        tags += ["cloth", "light"]
    if "cloak" in name or "mantle" in name:
        tags += ["light", "cloth"]
    if "cuirass" in name or "half" in name and "plate" in name:
        tags += ["heavy", "plate"]
    if "vest" in name or "padded" in name:
        tags += ["light"]
    if "helm" in name or "cap" in name:
        tags += ["light"] if "leather" in name or "cap" in name else ["medium"]
    if "buckler" in name or "shield" in name or "aegis" in name:
        tags += ["shield"]
    if "gauntlets" in name or "gloves" in name:
        tags += ["medium"]
    if "bark" in name and "mantle" in name:
        tags = ["natural", "leather", "light"]
    return sorted(set(tags))


def derive_stat_tags(item: dict) -> list[str]:
    tags = []
    for stat in ("strength", "agility", "intellect", "endurance", "faith"):
        if int(item.get(f"{stat}_bonus", 0) or 0) > 0:
            tags.append(stat)
    return tags


def derive_recommended_classes(item: dict, stat_tags: list[str]) -> list[str]:
    """Best-fit class list. Empty if too generic (treated as off-class
    by the warning rule but never blocked)."""
    if not stat_tags:
        return []
    pool: list[str] = []
    for stat in stat_tags:
        for cls in STAT_TO_CLASSES.get(stat, []):
            if cls not in pool:
                pool.append(cls)
    return pool[:6]  # cap to keep response payload bounded.


def derive_role_tags(stat_tags: list[str]) -> list[str]:
    if not stat_tags:
        return []
    pool: list[str] = []
    for stat in stat_tags:
        for r in STAT_TO_ROLE_TAGS.get(stat, []):
            if r not in pool:
                pool.append(r)
    return pool


def is_universal_accessory(item: dict) -> bool:
    """Accessories with no stat dominance are universal."""
    if item.get("item_type") != "accessory":
        return False
    return not derive_stat_tags(item)


def build_delta(item: dict) -> dict:
    """Compute the set of fields to write. Empty → no-op."""
    out: dict = {}
    item_type = item.get("item_type")
    slug = (item.get("slug") or "").lower()

    if item_type == "weapon":
        new_wt = infer_weapon_tags(item)
        if item.get("weapon_tags") != new_wt:
            out["weapon_tags"] = new_wt
    if item_type == "armor":
        new_at = infer_armor_tags(item)
        if item.get("armor_tags") != new_at:
            out["armor_tags"] = new_at

    stat_tags = derive_stat_tags(item)
    if item.get("stat_tags") != stat_tags:
        out["stat_tags"] = stat_tags

    recommended = derive_recommended_classes(item, stat_tags)
    if item.get("recommended_classes") != recommended:
        out["recommended_classes"] = recommended

    class_tags = recommended  # for now: class_tags mirror recommended_classes.
    if item.get("class_tags") != class_tags:
        out["class_tags"] = class_tags

    role_tags = derive_role_tags(stat_tags)
    if item.get("role_tags") != role_tags:
        out["role_tags"] = role_tags

    is_uni = is_universal_accessory(item)
    if bool(item.get("is_universal")) != is_uni:
        out["is_universal"] = is_uni

    # Signature / legendary class lock.
    locked = SIGNATURE_CLASS_MAP.get(slug)
    if locked and item.get("required_class_optional") != locked:
        out["required_class_optional"] = locked
    elif slug.startswith("spec_signature_") and not locked:
        # Unknown signature → leave as-is, don't lock.
        pass

    return out


async def _audit_log(db, event: str, payload: dict) -> None:
    try:
        await db.audit_logs.insert_one({
            "event": event,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit log insert failed: {exc!r}")


async def main():
    parser = argparse.ArgumentParser(
        description="ROUND 15 — Phase 2: seed item compatibility tags (idempotent).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    cursor = db.items.find(
        {"is_active": True, "is_test": {"$ne": True}}, {"_id": 0},
    )
    total = 0
    updated = 0
    untouched = 0
    sample_updated: list[dict] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    async for item in cursor:
        total += 1
        delta = build_delta(item)
        if not delta:
            untouched += 1
            continue
        delta["updated_at"] = now_iso
        if args.dry_run:
            if len(sample_updated) < 5:
                sample_updated.append({"slug": item["slug"], "fields": sorted(delta.keys())})
        else:
            await db.items.update_one({"id": item["id"]}, {"$set": delta})
            await _audit_log(db, "item_tags_seeded_round15_phase2", {
                "item_slug": item["slug"],
                "fields_set": sorted(delta.keys()),
            })
            if len(sample_updated) < 5:
                sample_updated.append({"slug": item["slug"], "fields": sorted(delta.keys())})
        updated += 1

    print("=== SUMMARY ===")
    print(f"  items scanned:    {total}")
    print(f"  updated:          {updated}")
    print(f"  untouched:        {untouched}")
    print("  sample updates:")
    for s in sample_updated:
        print(f"    - {s['slug']:35s} → {s['fields']}")
    if args.dry_run:
        print("  (dry-run: nessuna scrittura, nessun audit log)")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
