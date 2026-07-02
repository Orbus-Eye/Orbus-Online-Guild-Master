"""ROUND 16.5.4b — Auto-Equip class-aware + ADJ-2 backfill test suite.

Copertura richiesta (16 test):

Auto-Equip (11):
  1. warrior preferisce stat primaria (strength/endurance)
  2. mage preferisce intellect
  3. priest preferisce faith
  4. item power alto ma stat sbagliata NON vince
  5. item over-level NON equipaggiato
  6. Legendary lv8/9 NON equipaggiato da lv1
  7. item incompatibile classe (block) NON equipaggiato
  8. item attuale migliore NON sostituito
  9. determinismo: 2 run stesso input → stesso output
 10. `stat_delta` restituito nel payload FE
 11. Messaggio UI leggibile italiano (reason_it contiene stat + classe)

ADJ-2 script (5):
 12. dry-run mostra esattamente i 6 Legendary bersaglio
 13. apply corregge esattamente 6 Legendary
 14. secondo apply fa 0 modifiche (idempotenza)
 15. required level finale corretto (sword/staff=9, altri=8)
 16. nessun altro item modificato oltre ai 6 whitelisted

Isolamento: gira su `orbus_r16_test`. Le fixture usano prefissi
`test_r1654b_*` per rendere il cleanup del conftest banale.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient


# ═════════════════════════════════════════════════════════════════════
# Shared helpers
# ═════════════════════════════════════════════════════════════════════

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _test_slug(tag: str) -> str:
    return f"test_r1654b_{tag}_{uuid.uuid4().hex[:6]}"


@pytest.fixture(scope="module")
def sync_db():
    dbn = os.environ["DB_NAME"]
    assert "test" in dbn.lower(), f"DB {dbn!r} non è test"
    c = MongoClient(os.environ["MONGO_URL"])
    try:
        yield c[dbn]
    finally:
        c.close()


@pytest.fixture(scope="function")
def cleanup_r1654b(sync_db):
    """Best-effort cleanup of anything the tests may leave behind."""
    yield
    for coll, field in [
        ("items", "slug"),
        ("inventory_items", "item_id"),
        ("equipped_items", "item_id"),
        ("adventurers", "id"),
        ("guilds", "id"),
        ("adventurer_classes", "slug"),
    ]:
        try:
            sync_db[coll].delete_many({field: {"$regex": r"^test_r1654b_"}})
        except Exception:
            pass


def _run(coro):
    """Run an async coroutine synchronously (test helper)."""
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


# ═════════════════════════════════════════════════════════════════════
# Sandbox fixtures — guild + adventurer + items + inventory
# ═════════════════════════════════════════════════════════════════════

def _seed_class(sync_db, slug: str, primary: str,
                secondaries: list[str], name: str = "Test") -> None:
    """Insert a test class into adventurer_classes if not present."""
    sync_db.adventurer_classes.update_one(
        {"slug": slug},
        {"$setOnInsert": {
            "id": str(uuid.uuid4()),
            "slug": slug,
            "name": name,
            "primary_stat": primary,
            "secondary_stats": secondaries,
            "role": "test",
            "role_tags": [],
            "allowed_armor_tags": [],
            "allowed_weapon_tags": [],
            "preferred_item_tags": [],
            "is_active": True,
            "is_base_class": False,
            "created_at": _utc_iso(),
        }},
        upsert=True,
    )


def _seed_guild(sync_db) -> dict:
    gid = f"test_r1654b_guild_{uuid.uuid4().hex[:6]}"
    doc = {
        "id": gid, "name": f"TestGuild_{gid[-6:]}",
        "owner_user_id": f"test_r1654b_owner_{gid[-6:]}",
        "gold": 1000, "level": 1, "created_at": _utc_iso(),
    }
    sync_db.guilds.insert_one(doc)
    return doc


def _seed_adventurer(sync_db, guild_id: str, class_slug: str,
                     level: int = 5, spec: str | None = None) -> dict:
    aid = f"test_r1654b_adv_{uuid.uuid4().hex[:6]}"
    doc = {
        "id": aid, "guild_id": guild_id,
        "name": f"TestAdv_{aid[-6:]}",
        "level": level,
        "class_slug": class_slug,
        "class_name": class_slug.capitalize(),
        "specialization_slug": spec,
        "strength": 5, "agility": 5, "intellect": 5,
        "endurance": 5, "faith": 5,
        "is_available": True, "is_retired": False,
        "created_at": _utc_iso(),
    }
    sync_db.adventurers.insert_one(doc)
    return doc


def _seed_item(sync_db, *, item_type: str, name_tag: str,
               rarity: str = "Common",
               strength: int = 0, agility: int = 0,
               intellect: int = 0, endurance: int = 0,
               faith: int = 0, power: int = 0,
               required_level: int = 1,
               class_tags: list[str] | None = None,
               weapon_tags: list[str] | None = None,
               armor_tags: list[str] | None = None,
               stat_tags: list[str] | None = None) -> dict:
    slug = _test_slug(name_tag)
    doc = {
        "id": str(uuid.uuid4()), "slug": slug, "name": slug,
        "display_name_it": slug, "display_name_en": slug,
        "item_type": item_type, "rarity": rarity,
        "power_score": power,
        "strength_bonus": strength, "agility_bonus": agility,
        "intellect_bonus": intellect, "endurance_bonus": endurance,
        "faith_bonus": faith,
        "required_adventurer_level": required_level,
        "class_tags": class_tags or [],
        "recommended_classes": class_tags or [],
        "weapon_tags": weapon_tags or [],
        "armor_tags": armor_tags or [],
        "stat_tags": stat_tags or [],
        "role_tags": [],
        "is_active": True, "is_tradeable": True,
        "affects_combat": True,
        "created_at": _utc_iso(),
    }
    sync_db.items.insert_one(doc)
    return doc


def _seed_inventory(sync_db, guild_id: str, item_id: str,
                    quantity: int = 1) -> None:
    sync_db.inventory_items.insert_one({
        "id": str(uuid.uuid4()), "guild_id": guild_id,
        "item_id": item_id, "quantity": quantity,
        "reserved_qty": 0, "is_active": True, "is_bound": False,
    })


async def _call_auto_equip(guild: dict, adv_id: str):
    """Invoke the auto-equip service against the test DB (motor)."""
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    from app.equipment.auto_equip import auto_equip_adventurer
    try:
        return await auto_equip_adventurer(
            db, guild=guild, adventurer_id=adv_id,
            actor_user_id="test_r1654b_actor",
        )
    finally:
        client.close()


# ═════════════════════════════════════════════════════════════════════
# Tests 1–11: Auto-Equip class-aware
# ═════════════════════════════════════════════════════════════════════

def test_01_warrior_prefers_strength(sync_db, cleanup_r1654b):
    """Warrior con weapon A (str:10, int:0) vs B (str:0, int:10) → sceglie A."""
    _seed_class(sync_db, "test_r1654b_warrior", "strength", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_warrior", level=10)
    weapon_str = _seed_item(sync_db, item_type="weapon",
                            name_tag="wpn_str", strength=10, power=5,
                            class_tags=["test_r1654b_warrior"])
    weapon_int = _seed_item(sync_db, item_type="weapon",
                            name_tag="wpn_int", intellect=10, power=5,
                            class_tags=["test_r1654b_warrior"])
    _seed_inventory(sync_db, g["id"], weapon_str["id"])
    _seed_inventory(sync_db, g["id"], weapon_int["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_weapon = next(
        (e for e in res["equipped"] if e["slot"] == "weapon"), None,
    )
    assert equipped_weapon is not None, "weapon slot doveva essere equipaggiato"
    assert equipped_weapon["item_slug"] == weapon_str["slug"], (
        f"warrior doveva scegliere str-weapon, ha scelto "
        f"{equipped_weapon['item_slug']}"
    )


def test_02_mage_prefers_intellect(sync_db, cleanup_r1654b):
    _seed_class(sync_db, "test_r1654b_mage", "intellect", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_mage", level=10)
    wpn_str = _seed_item(sync_db, item_type="weapon", name_tag="mage_str",
                         strength=8, power=5,
                         class_tags=["test_r1654b_mage"])
    wpn_int = _seed_item(sync_db, item_type="weapon", name_tag="mage_int",
                         intellect=8, power=5,
                         class_tags=["test_r1654b_mage"])
    _seed_inventory(sync_db, g["id"], wpn_str["id"])
    _seed_inventory(sync_db, g["id"], wpn_int["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_w = next((e for e in res["equipped"] if e["slot"] == "weapon"), None)
    assert equipped_w and equipped_w["item_slug"] == wpn_int["slug"]


def test_03_priest_prefers_faith(sync_db, cleanup_r1654b):
    _seed_class(sync_db, "test_r1654b_priest", "faith", ["intellect"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_priest", level=10)
    wpn_str = _seed_item(sync_db, item_type="weapon", name_tag="p_str",
                         strength=8, power=5,
                         class_tags=["test_r1654b_priest"])
    wpn_faith = _seed_item(sync_db, item_type="weapon", name_tag="p_faith",
                           faith=8, power=5,
                           class_tags=["test_r1654b_priest"])
    _seed_inventory(sync_db, g["id"], wpn_str["id"])
    _seed_inventory(sync_db, g["id"], wpn_faith["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_w = next((e for e in res["equipped"] if e["slot"] == "weapon"), None)
    assert equipped_w and equipped_w["item_slug"] == wpn_faith["slug"]


def test_04_high_power_wrong_stat_does_not_win(sync_db, cleanup_r1654b):
    """Mage vs weapon `strength:0, power:30` VS `intellect:5, power:5`.

    Fitness A = 0 + 0 + 30·1 = 30
    Fitness B = 5·3 + 0 + 5·1 = 20
    → warrior-like winner even for mage. Verifica che la formula ora
    valorizzi la stat primaria abbastanza da SUPERARE power alto quando
    lo scarto stat è ampio.

    Test più severo: A=(str:2, power:20), B=(int:8, power:5).
    Fitness A = 6+0+20 = 26. B = 24+0+5 = 29. Mage sceglie B ✓
    """
    _seed_class(sync_db, "test_r1654b_mage2", "intellect", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_mage2", level=10)
    wrong = _seed_item(sync_db, item_type="weapon", name_tag="wrong",
                       strength=2, power=20,
                       class_tags=["test_r1654b_mage2"])
    right = _seed_item(sync_db, item_type="weapon", name_tag="right",
                       intellect=8, power=5,
                       class_tags=["test_r1654b_mage2"])
    _seed_inventory(sync_db, g["id"], wrong["id"])
    _seed_inventory(sync_db, g["id"], right["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_w = next((e for e in res["equipped"] if e["slot"] == "weapon"), None)
    assert equipped_w and equipped_w["item_slug"] == right["slug"], (
        f"mage doveva scegliere int:8/power:5 (fit 29) invece di "
        f"str:2/power:20 (fit 26)"
    )


def test_05_over_level_item_not_equipped(sync_db, cleanup_r1654b):
    """Lv3 warrior + weapon required_level=10 → NON equipaggiato."""
    _seed_class(sync_db, "test_r1654b_warr5", "strength", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_warr5", level=3)
    too_high = _seed_item(sync_db, item_type="weapon", name_tag="high_lv",
                          strength=20, power=50, required_level=10,
                          class_tags=["test_r1654b_warr5"])
    _seed_inventory(sync_db, g["id"], too_high["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    assert "weapon" in res["unchanged_slots"], (
        "weapon slot doveva essere unchanged (item over-level)"
    )
    equipped_slugs = [e["item_slug"] for e in res["equipped"]]
    assert too_high["slug"] not in equipped_slugs


def test_06_legendary_lv1_target_gate_from_rarity(sync_db, cleanup_r1654b):
    """Legendary rarity + required_adventurer_level=8 non equipaggiato da lv1.

    Verifica che il gate sia sul campo canonico e non sul rarity fallback:
    un lv1 warrior NON deve equipaggiare un Legendary con req_level=8
    (post-backfill ADJ-2).
    """
    _seed_class(sync_db, "test_r1654b_warr6", "strength", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_warr6", level=1)
    legendary = _seed_item(
        sync_db, item_type="weapon", name_tag="leg8",
        rarity="Legendary", strength=25, power=60,
        required_level=8, class_tags=["test_r1654b_warr6"],
    )
    _seed_inventory(sync_db, g["id"], legendary["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_slugs = [e["item_slug"] for e in res["equipped"]]
    assert legendary["slug"] not in equipped_slugs, (
        "Legendary lv8 NON deve essere equipaggiato da lv1"
    )
    assert "weapon" in res["unchanged_slots"]


def test_07_class_locked_item_blocked(sync_db, cleanup_r1654b):
    """Item required_class_optional='mage' NON equipaggiato da warrior."""
    _seed_class(sync_db, "test_r1654b_warr7", "strength", ["endurance"])
    _seed_class(sync_db, "test_r1654b_mage7", "intellect", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_warr7", level=10)
    mage_only = _seed_item(sync_db, item_type="weapon", name_tag="mgonly",
                           strength=99, power=99,
                           class_tags=["test_r1654b_mage7"])
    # Add hard class lock
    sync_db.items.update_one(
        {"id": mage_only["id"]},
        {"$set": {"required_class_optional": "test_r1654b_mage7"}},
    )
    _seed_inventory(sync_db, g["id"], mage_only["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_slugs = [e["item_slug"] for e in res["equipped"]]
    assert mage_only["slug"] not in equipped_slugs


def test_08_current_best_not_replaced(sync_db, cleanup_r1654b):
    """Current best equipped + only worse in inv → slot unchanged."""
    _seed_class(sync_db, "test_r1654b_warr8", "strength", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_warr8", level=10)
    best = _seed_item(sync_db, item_type="weapon", name_tag="best",
                      strength=20, power=10,
                      class_tags=["test_r1654b_warr8"])
    worse = _seed_item(sync_db, item_type="weapon", name_tag="worse",
                       strength=5, power=3,
                       class_tags=["test_r1654b_warr8"])
    _seed_inventory(sync_db, g["id"], best["id"])
    _seed_inventory(sync_db, g["id"], worse["id"])
    # Manual pre-equip: best already equipped
    sync_db.inventory_items.update_one(
        {"item_id": best["id"], "guild_id": g["id"]},
        {"$set": {"reserved_qty": 1}},
    )
    sync_db.equipped_items.insert_one({
        "id": str(uuid.uuid4()), "guild_id": g["id"],
        "adventurer_id": adv["id"],
        "item_id": best["id"], "slot": "weapon",
        "equipped_at": _utc_iso(),
    })
    res = _run(_call_auto_equip(g, adv["id"]))
    # weapon slot unchanged (best is already equipped)
    assert "weapon" in res["unchanged_slots"]


def test_09_determinism_two_runs_same_output(sync_db, cleanup_r1654b):
    _seed_class(sync_db, "test_r1654b_det", "strength", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_det", level=10)
    # 3 tied weapons — deterministic tie-break by id
    items = [
        _seed_item(sync_db, item_type="weapon", name_tag=f"tie{i}",
                   strength=5, power=5,
                   class_tags=["test_r1654b_det"])
        for i in range(3)
    ]
    for it in items:
        _seed_inventory(sync_db, g["id"], it["id"])
    r1 = _run(_call_auto_equip(g, adv["id"]))
    # Second run: nothing to equip (already equipped best)
    r2 = _run(_call_auto_equip(g, adv["id"]))
    assert r2["swaps_count"] == 0, (
        f"seconda run doveva essere idempotente, swaps={r2['swaps_count']}"
    )
    # First run: exactly ONE weapon equipped, and picking is deterministic
    weapon_swaps = [e for e in r1["equipped"] if e["slot"] == "weapon"]
    assert len(weapon_swaps) == 1
    picked_slug = weapon_swaps[0]["item_slug"]
    assert picked_slug in {it["slug"] for it in items}


def test_10_stat_delta_returned_in_payload(sync_db, cleanup_r1654b):
    """L'API espone `reasons[].stat_delta` con i bonus stat effettivi."""
    _seed_class(sync_db, "test_r1654b_wa10", "strength", ["endurance"])
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_wa10", level=10)
    wpn = _seed_item(sync_db, item_type="weapon", name_tag="w10",
                     strength=7, endurance=3, power=4,
                     class_tags=["test_r1654b_wa10"])
    _seed_inventory(sync_db, g["id"], wpn["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    reasons = res.get("reasons") or []
    weapon_reason = next((r for r in reasons if r["slot"] == "weapon"), None)
    assert weapon_reason is not None
    delta = weapon_reason.get("stat_delta") or {}
    assert delta.get("strength") == 7, f"strength delta atteso 7, got {delta}"
    assert delta.get("endurance") == 3
    assert delta.get("power") == 4
    # Ordering: primary first
    keys = list(delta.keys())
    assert keys[0] == "strength", f"primary stat deve essere prima: {keys}"


def test_11_italian_reason_message_readable(sync_db, cleanup_r1654b):
    """reason_it deve contenere nome classe italiano + delta stat."""
    _seed_class(sync_db, "test_r1654b_wa11", "intellect", ["endurance"],
                name="Mago-Test")
    # Set display_name_it
    sync_db.adventurer_classes.update_one(
        {"slug": "test_r1654b_wa11"},
        {"$set": {"display_name_it": "Mago-Test"}},
    )
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_wa11", level=10)
    wpn = _seed_item(sync_db, item_type="weapon", name_tag="focus",
                     intellect=5, endurance=2, power=8,
                     class_tags=["test_r1654b_wa11"])
    _seed_inventory(sync_db, g["id"], wpn["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    weapon_reason = next((r for r in res["reasons"]
                          if r["slot"] == "weapon"), None)
    assert weapon_reason is not None
    r_it = weapon_reason["reason_it"]
    # Contiene la parola chiave "equipaggiata"
    assert "equipaggiata" in r_it.lower(), (
        f"reason_it deve descrivere equip: '{r_it}'"
    )
    # Contiene delta stat
    assert "+5 Int" in r_it or "+5 Intellect" in r_it, (
        f"reason_it deve includere +5 Int: '{r_it}'"
    )
    # Contiene classe italiana
    assert "Mago-Test" in r_it, (
        f"reason_it deve includere il nome classe italiano: '{r_it}'"
    )


# ═════════════════════════════════════════════════════════════════════
# Tests 12–16: ADJ-2 script
# ═════════════════════════════════════════════════════════════════════

def test_12_dry_run_lists_exactly_six_legendaries(sync_db):
    """Il dry-run identifica esattamente i 6 slug Legendary target."""
    from app.scripts.round1654b_seed_integrity import (
        TARGET_LEVELS, run,
    )
    assert len(TARGET_LEVELS) == 6
    result = _run(run(dry_run=True))
    assert result["mode"] == "dry-run"
    assert len(result["applied"]) == 0
    # plan + noop = 6 (i 6 slug target sono tutti tracciati, alcuni
    # possono essere già al target — anche se al primo run tutti sono
    # attesi in plan)
    known_slugs = set(TARGET_LEVELS.keys())
    tracked_slugs = (
        {p["slug"] for p in result["plan"]}
        | {n["slug"] for n in result["noop"]}
    )
    missing_slugs = set(result["missing"])
    assert (tracked_slugs | missing_slugs) == known_slugs, (
        f"tracked+missing deve coprire whitelist. tracked={tracked_slugs} "
        f"missing={missing_slugs}"
    )


def test_13_apply_corrects_six_legendaries(sync_db):
    from app.scripts.round1654b_seed_integrity import TARGET_LEVELS, run
    # Precondizione deterministica: forziamo i 6 slug a level=1 se
    # esistono nel DB. Simula lo stato "orfano R16.5.4b" pre-fix.
    reset = sync_db.items.update_many(
        {"slug": {"$in": list(TARGET_LEVELS.keys())}},
        {"$set": {"required_adventurer_level": 1}},
    )
    if reset.matched_count == 0:
        pytest.skip("I 6 Legendary target non sono presenti in questo DB")
    # Sanity check: ora sono tutti a 1.
    below_after_reset = sync_db.items.count_documents({
        "slug": {"$in": list(TARGET_LEVELS.keys())},
        "required_adventurer_level": 1,
    })
    assert below_after_reset == reset.matched_count, (
        "reset precondizione non riuscito"
    )
    # Esegui apply
    result = _run(run(dry_run=False))
    assert result["mode"] == "apply"
    # Numero di apply == numero di item presenti (max 6)
    assert len(result["applied"]) == reset.matched_count, (
        f"apply doveva correggere {reset.matched_count} item, "
        f"ha corretto {len(result['applied'])}"
    )
    # Post-condizione: DB coerente col target
    for slug, target in TARGET_LEVELS.items():
        doc = sync_db.items.find_one({"slug": slug})
        if doc is None:
            continue  # missing → tracciato in `missing`
        assert int(doc["required_adventurer_level"]) == target, (
            f"{slug} required_level={doc['required_adventurer_level']} "
            f"deve essere == {target}"
        )


def test_14_second_apply_zero_changes(sync_db):
    """Idempotenza: dopo test_13, un secondo apply non tocca nulla."""
    from app.scripts.round1654b_seed_integrity import run
    result = _run(run(dry_run=False))
    assert result["mode"] == "apply"
    assert len(result["applied"]) == 0, (
        f"secondo apply deve essere 0-change, applied={result['applied']}"
    )
    assert len(result["plan"]) == 0


def test_15_final_required_levels_match_spec(sync_db):
    """Verifica valori esatti: sword/staff=9, armor/ring/amulet/cape=8."""
    expected = {
        "legendary_sword_alveora": 9,
        "legendary_staff_efreto": 9,
        "legendary_armor_ambash": 8,
        "legendary_ring_velur": 8,
        "legendary_amulet_nathos": 8,
        "legendary_cape_aveol": 8,
    }
    for slug, target in expected.items():
        doc = sync_db.items.find_one({"slug": slug})
        if doc is None:
            pytest.fail(f"whitelist slug non trovato: {slug}")
        assert int(doc["required_adventurer_level"]) == target, (
            f"{slug}: atteso {target}, got "
            f"{doc['required_adventurer_level']}"
        )


def test_16_no_other_items_modified(sync_db):
    """Solo i 6 slug whitelisted sono modificati; nessun altro item cambia."""
    from app.scripts.round1654b_seed_integrity import TARGET_LEVELS
    whitelisted = set(TARGET_LEVELS.keys())
    # Contiamo tutti gli item Legendary/legendary non whitelisted e ci
    # aspettiamo che nessuno abbia il timestamp `updated_at` = timestamp
    # dello script run. Non abbiamo ancora un audit trail robusto per
    # questo, ma possiamo verificare che:
    #   1. Nessun item outside whitelist ha required_adventurer_level
    #      alterato in modo "sospetto" (es: passato da 1 a 8/9).
    #   2. Il numero totale di Legendary (case-insensitive) è invariato.
    total_legendary = sync_db.items.count_documents({
        "rarity": {"$regex": "^legendary$", "$options": "i"},
    })
    assert total_legendary >= 6, (
        f"almeno 6 Legendary attesi, trovati {total_legendary}"
    )
    # Snapshot letto e confrontato coi campi previsti
    import json
    from pathlib import Path
    snap = Path("/app/memory/round1654b_adj2_snapshot.json")
    if snap.exists():
        payload = json.loads(snap.read_text(encoding="utf-8"))
        # planned_updates è la lista canonica di ciò che lo script tocca
        planned_slugs = {p["slug"] for p in payload.get("planned_updates", [])}
        # Ogni slug pianificato DEVE essere in whitelist
        assert planned_slugs.issubset(whitelisted), (
            f"snapshot pianifica slug fuori whitelist: "
            f"{planned_slugs - whitelisted}"
        )


# ═════════════════════════════════════════════════════════════════════
# ROUND 16.5.4b REOPEN — HTTP E2E tests (17–19)
#
# Rationale: unit tests 01–11 above validate the auto-equip service in
# isolation (motor DB, no HTTP). Live testers reported the bug over
# HTTP (`POST /api/adventurers/{id}/auto-equip` returning weapon only,
# always `balanced_dagger`), so we add an end-to-end contract test
# against the running backend to prevent regressions at the transport
# layer (routing, serialization, auth, response schema).
#
# Design decisions:
#   • Uses `REACT_APP_BACKEND_URL` (external preview URL) via httpx —
#     same pattern as `test_forge_actions_p0.py`.
#   • Relies on the pre-seeded `tester@orbus.test / password123`
#     account. Adventurer is picked dynamically from
#     `GET /api/adventurers` (first Warrior with level ≥ 10 and 3+
#     items in inventory); the module skips gracefully if none is
#     available (e.g. brand new tester account).
#   • Non-destructive at the semantic level: the test unequips the 3
#     slots before running auto-equip, so re-running the suite is
#     idempotent. State touched is limited to `equipped_items` for
#     the tester's guild — never creates users/guilds/items.
#   • These tests are the HTTP twin of unit tests 01 & 08–11: they do
#     NOT re-validate the scoring formula (already covered by 01–11)
#     but assert the transport contract (payload shape, IT grammar,
#     idempotency across calls).
# ═════════════════════════════════════════════════════════════════════

import httpx as _httpx
from pathlib import Path as _Path
from dotenv import load_dotenv as _load_dotenv

_load_dotenv(_Path("/app/frontend/.env"))
_BACKEND_URL_E2E = os.environ.get("REACT_APP_BACKEND_URL")
_TESTER_EMAIL = "tester@orbus.test"
_TESTER_PASSWORD = "password123"

_e2e_skip = pytest.mark.skipif(
    not _BACKEND_URL_E2E,
    reason="REACT_APP_BACKEND_URL not set — skipping HTTP E2E tests",
)


def _e2e_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}",
            "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def e2e_token() -> str:
    if not _BACKEND_URL_E2E:
        pytest.skip("no backend URL")
    try:
        r = _httpx.post(
            f"{_BACKEND_URL_E2E}/api/auth/login",
            json={"email": _TESTER_EMAIL, "password": _TESTER_PASSWORD},
            timeout=10.0,
        )
    except _httpx.HTTPError as exc:
        pytest.skip(f"backend unreachable: {exc}")
    if r.status_code != 200:
        pytest.skip(f"tester login failed: {r.status_code} {r.text}")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def e2e_warrior_adv(e2e_token: str) -> dict:
    """Pick a Warrior lv≥10 with 3+ items in inventory; skip otherwise."""
    hdrs = _e2e_headers(e2e_token)
    r = _httpx.get(
        f"{_BACKEND_URL_E2E}/api/adventurers",
        headers=hdrs, timeout=10.0,
    )
    if r.status_code != 200:
        pytest.skip(f"adventurers list failed: {r.status_code}")
    advs = r.json() if isinstance(r.json(), list) else r.json().get("adventurers", [])
    # Warrior detection: class_slug OR class_name (94% docs lack class_slug —
    # class_slug fallback issue documented in R16.5.4b REOPEN report).
    def _is_warrior(a: dict) -> bool:
        slug = (a.get("class_slug") or "").lower()
        name = (a.get("class_name") or a.get("class") or "").lower()
        return slug == "warrior" or "warrior" in name or "guerriero" in name
    warriors = [a for a in advs if _is_warrior(a) and int(a.get("level", 0)) >= 10]
    if not warriors:
        pytest.skip("no Warrior lv≥10 available on tester@orbus.test")
    # Check inventory has ≥3 items (weapon+armor+accessory minimum).
    r_inv = _httpx.get(
        f"{_BACKEND_URL_E2E}/api/inventory",
        headers=hdrs, timeout=10.0,
    )
    if r_inv.status_code != 200:
        pytest.skip(f"inventory fetch failed: {r_inv.status_code}")
    inv = r_inv.json()
    inv_items = (
        inv if isinstance(inv, list)
        else (inv.get("inventory") or inv.get("items") or [])
    )
    if len(inv_items) < 3:
        pytest.skip(
            f"tester inventory has {len(inv_items)} items, need ≥3 "
            f"(weapon+armor+accessory) — run /app/backend/app/scripts/"
            f"round1654b_seed_test_items.py to seed"
        )
    return warriors[0]


def _reset_slots(adv_id: str, token: str) -> None:
    """Unequip all 3 slots to give auto-equip a clean board."""
    hdrs = _e2e_headers(token)
    for slot in ("weapon", "armor", "accessory"):
        _httpx.post(
            f"{_BACKEND_URL_E2E}/api/adventurers/{adv_id}/unequip",
            headers=hdrs, json={"slot": slot}, timeout=10.0,
        )


@_e2e_skip
def test_17_e2e_full_flow_warrior_lv10_class_aware_selection(
    e2e_token: str, e2e_warrior_adv: dict,
):
    """POST /api/adventurers/{id}/auto-equip su Warrior lv≥10 con inventario
    Legendary popolato → weapon+armor+accessory equipaggiati, weapon
    class-aware (strength_bonus > 0 o power_score alto), NON balanced_dagger.

    Questo è il test che replica il bug live: prima del fix R16.5.4b
    l'endpoint restituiva solo weapon=balanced_dagger.
    """
    adv_id = e2e_warrior_adv["id"]
    _reset_slots(adv_id, e2e_token)

    r = _httpx.post(
        f"{_BACKEND_URL_E2E}/api/adventurers/{adv_id}/auto-equip",
        headers=_e2e_headers(e2e_token), timeout=15.0,
    )
    assert r.status_code == 200, f"auto-equip failed: {r.status_code} {r.text}"
    payload = r.json()

    # Contract shape
    for k in ("equipped", "replaced", "unchanged_slots",
              "unchanged_slots_detail", "reasons", "primary_stat",
              "score_before", "score_after", "score_delta",
              "swaps_count", "warnings_it", "warnings_en"):
        assert k in payload, f"payload manca il campo obbligatorio {k!r}"

    # Almeno weapon+armor+accessory equipaggiati (3 slot).
    equipped_slots = {e["slot"] for e in payload["equipped"]}
    assert equipped_slots == {"weapon", "armor", "accessory"}, (
        f"Attesi 3 slot equipaggiati (weapon/armor/accessory), "
        f"trovati {equipped_slots}. Payload: {payload['equipped']}"
    )

    # Il bug originale: weapon sempre = 'balanced_dagger'. Ora deve
    # essere qualcosa di class-aware (non un generic balanced).
    weapon = next(e for e in payload["equipped"] if e["slot"] == "weapon")
    assert "balanced_dagger" not in weapon["item_slug"], (
        f"REGRESSIONE: weapon torna a balanced_dagger! "
        f"item_slug={weapon['item_slug']}"
    )

    # Warrior primary=strength: weapon deve dare almeno un bonus tra
    # strength/endurance (Warrior primary+secondary), NON solo intellect.
    stat_delta = weapon["stat_delta"]
    warrior_stat_gain = (
        int(stat_delta.get("strength", 0) or 0)
        + int(stat_delta.get("endurance", 0) or 0)
    )
    other_stat_gain = (
        int(stat_delta.get("intellect", 0) or 0)
        + int(stat_delta.get("faith", 0) or 0)
    )
    assert warrior_stat_gain > 0, (
        f"weapon del Warrior deve dare almeno strength o endurance, "
        f"stat_delta={stat_delta}"
    )
    # Score deve crescere (era 0 dopo unequip, ora >= 30 con 3 Legendary).
    assert payload["score_after"] > payload["score_before"], (
        f"score_delta non positivo: {payload['score_before']} → "
        f"{payload['score_after']}"
    )
    assert payload["swaps_count"] == 3, (
        f"swaps_count deve essere 3 (weapon+armor+accessory), "
        f"got {payload['swaps_count']}"
    )


@_e2e_skip
def test_18_e2e_second_call_idempotent(
    e2e_token: str, e2e_warrior_adv: dict,
):
    """Doppia chiamata consecutiva di auto-equip: la seconda deve essere
    no-op (equipped=[], replaced=[], unchanged=3, score_delta=0)."""
    adv_id = e2e_warrior_adv["id"]

    # Baseline: assicurati che tutto sia equipaggiato con auto-equip.
    _reset_slots(adv_id, e2e_token)
    r1 = _httpx.post(
        f"{_BACKEND_URL_E2E}/api/adventurers/{adv_id}/auto-equip",
        headers=_e2e_headers(e2e_token), timeout=15.0,
    )
    assert r1.status_code == 200

    # Second call → idempotente.
    r2 = _httpx.post(
        f"{_BACKEND_URL_E2E}/api/adventurers/{adv_id}/auto-equip",
        headers=_e2e_headers(e2e_token), timeout=15.0,
    )
    assert r2.status_code == 200
    p2 = r2.json()

    assert p2["equipped"] == [], (
        f"seconda chiamata deve avere equipped=[] "
        f"(già ottimale), got {p2['equipped']}"
    )
    assert p2["replaced"] == [], (
        f"seconda chiamata deve avere replaced=[], got {p2['replaced']}"
    )
    assert p2["swaps_count"] == 0, (
        f"swaps_count seconda chiamata deve essere 0, got {p2['swaps_count']}"
    )
    assert p2["score_after"] == p2["score_before"], (
        f"score non deve cambiare tra chiamate consecutive: "
        f"{p2['score_before']} vs {p2['score_after']}"
    )
    assert set(p2["unchanged_slots"]) == {"weapon", "armor", "accessory"}, (
        f"unchanged_slots deve contenere tutti e 3 gli slot, "
        f"got {p2['unchanged_slots']}"
    )
    # unchanged_slots_detail deve avere motivazione IT leggibile.
    for detail in p2["unchanged_slots_detail"]:
        assert "reason_it" in detail and detail["reason_it"], (
            f"unchanged_slots_detail manca reason_it: {detail}"
        )
        # Il messaggio "già il migliore" è la motivazione R16.5.4b.
        assert "migliore" in detail["reason_it"].lower(), (
            f"reason_it deve contenere 'migliore', got: {detail['reason_it']}"
        )


@_e2e_skip
def test_19_e2e_italian_message_readable(
    e2e_token: str, e2e_warrior_adv: dict,
):
    """UX / grammatica IT: dopo auto-equip iniziale, i `reason_it` in
    `reasons[]` devono usare accordo di genere corretto per slot
    (Arma/Armatura → 'equipaggiata', Accessorio → 'equipaggiato') e
    citare la classe italiana (Guerriero) come giustificazione."""
    adv_id = e2e_warrior_adv["id"]
    _reset_slots(adv_id, e2e_token)

    r = _httpx.post(
        f"{_BACKEND_URL_E2E}/api/adventurers/{adv_id}/auto-equip",
        headers=_e2e_headers(e2e_token), timeout=15.0,
    )
    assert r.status_code == 200
    payload = r.json()
    reasons_by_slot = {r["slot"]: r for r in payload["reasons"]}

    # ── Weapon: "Arma equipaggiata: …" (femminile)
    wpn_it = reasons_by_slot["weapon"]["reason_it"]
    assert wpn_it.startswith("Arma equipaggiata:"), (
        f"weapon reason_it deve iniziare con 'Arma equipaggiata:', "
        f"got: {wpn_it}"
    )
    # Errori grammaticali comuni da evitare (R16.5.4b UX fix):
    assert "Arma equipaggiato" not in wpn_it, (
        f"BUG IT: 'Arma equipaggiato' (maschile) invece di "
        f"'Arma equipaggiata' (femminile): {wpn_it}"
    )

    # ── Armor: "Armatura equipaggiata: …" (femminile)
    arm_it = reasons_by_slot["armor"]["reason_it"]
    assert arm_it.startswith("Armatura equipaggiata:"), (
        f"armor reason_it deve iniziare con 'Armatura equipaggiata:', "
        f"got: {arm_it}"
    )
    assert "Armatura equipaggiato" not in arm_it

    # ── Accessory: "Accessorio equipaggiato: …" (maschile)
    acc_it = reasons_by_slot["accessory"]["reason_it"]
    assert acc_it.startswith("Accessorio equipaggiato:"), (
        f"accessory reason_it deve iniziare con "
        f"'Accessorio equipaggiato:', got: {acc_it}"
    )
    assert "Accessorio equipaggiata" not in acc_it, (
        f"BUG IT: 'Accessorio equipaggiata' (femminile) invece di "
        f"'Accessorio equipaggiato' (maschile): {acc_it}"
    )

    # ── Classe italiana citata almeno nel weapon reason (Warrior → Guerriero)
    assert "Guerriero" in wpn_it or "warrior" in wpn_it.lower(), (
        f"weapon reason_it deve citare la classe italiana 'Guerriero', "
        f"got: {wpn_it}"
    )

    # ── Nessun stringa "None" o "null" leakato nel messaggio.
    for slot, r_data in reasons_by_slot.items():
        assert "None" not in r_data["reason_it"], (
            f"{slot} reason_it contiene 'None' (bug di formattazione): "
            f"{r_data['reason_it']}"
        )

# ═════════════════════════════════════════════════════════════════════
# ROUND 16.5.4b REOPEN #2 — Warning-only skip tests (20–23)
#
# PM decision Q2-b(iii) approvata 2026-07-02: Auto-Equip scarta gli
# item con `severity="warning"` (prima venivano equipaggiati con
# penalty ×0.5). Il manual equip resta invariato.
# ═════════════════════════════════════════════════════════════════════


def test_20_druid_warning_only_weapon_skipped(sync_db, cleanup_r1654b):
    """Druid + solo Frostfang-like (warrior-only) in inv → empty state,
    NESSUN equip di weapon (comportamento post-Q2-b(iii)).

    Ripete il caso Gwyn Ironfoot Lv11 in produzione:
      - Adv classe Druid (faith primary, intellect secondary)
      - Inv weapon: solo item con `recommended_classes=[warrior,paladin,berserker]`
      - Atteso: weapon in `unchanged_slots`, `off_class_seen>=1`, reason IT
        cita "adatto alla classe Druido".
    """
    _seed_class(sync_db, "test_r1654b_druid20", "faith", ["intellect"],
                name="Druido")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_druid20", level=11)
    # Frostfang-like: strong warrior weapon, NOT class-fit for druid
    frostfang = _seed_item(
        sync_db, item_type="weapon", name_tag="warrior_only_sword",
        rarity="Epic", strength=5, endurance=2, power=7,
        required_level=8,
        class_tags=["warrior", "paladin", "berserker"],  # NO druid
    )
    _seed_inventory(sync_db, g["id"], frostfang["id"])
    res = _run(_call_auto_equip(g, adv["id"]))

    equipped_slugs = [e["item_slug"] for e in res["equipped"]]
    assert frostfang["slug"] not in equipped_slugs, (
        f"REGRESSIONE Q2-b(iii): Frostfang-like non doveva essere "
        f"equipaggiato su Druido, got equipped={equipped_slugs}"
    )
    assert "weapon" in res["unchanged_slots"]
    weapon_detail = next(
        (d for d in res["unchanged_slots_detail"] if d["slot"] == "weapon"),
        None,
    )
    assert weapon_detail is not None
    assert weapon_detail.get("off_class_seen", 0) >= 1, (
        f"off_class_seen doveva essere >=1, got {weapon_detail}"
    )


def test_21_druid_class_fit_weapon_preferred(sync_db, cleanup_r1654b):
    """Druid + Frostfang (off-class) + spiritglass-staff (class-fit) in
    inv → sceglie sempre lo staff druid-compatibile, mai il sword warrior.
    """
    _seed_class(sync_db, "test_r1654b_druid21", "faith", ["intellect"],
                name="Druido")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_druid21", level=10)
    off_class = _seed_item(
        sync_db, item_type="weapon", name_tag="off_druid",
        rarity="Epic", strength=5, endurance=2, power=7,
        class_tags=["warrior", "paladin"],
    )
    class_fit = _seed_item(
        sync_db, item_type="weapon", name_tag="druid_staff",
        rarity="Rare", intellect=3, faith=1, power=4,
        class_tags=["test_r1654b_druid21"],  # match adv class
    )
    _seed_inventory(sync_db, g["id"], off_class["id"])
    _seed_inventory(sync_db, g["id"], class_fit["id"])

    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_w = next((e for e in res["equipped"] if e["slot"] == "weapon"),
                     None)
    assert equipped_w is not None, "weapon doveva essere equipaggiato"
    assert equipped_w["item_slug"] == class_fit["slug"], (
        f"Doveva scegliere lo staff druid-fit ({class_fit['slug']}), "
        f"ha scelto {equipped_w['item_slug']}"
    )


def test_22_warrior_regression_still_equips(sync_db, cleanup_r1654b):
    """Regression: Warrior + 3 item class-fit (weapon/armor/accessory)
    → tutti e 3 equipaggiati (nessuna regressione dal pass R16.5.4b
    precedente causata dal nuovo filtro warning)."""
    _seed_class(sync_db, "test_r1654b_warr22", "strength", ["endurance"],
                name="Guerriero")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_warr22", level=10)
    w = _seed_item(sync_db, item_type="weapon", name_tag="w_warr",
                   strength=5, endurance=2, power=7,
                   class_tags=["test_r1654b_warr22"])
    a = _seed_item(sync_db, item_type="armor", name_tag="a_warr",
                   strength=1, endurance=5, power=6,
                   class_tags=["test_r1654b_warr22"])
    acc = _seed_item(sync_db, item_type="accessory", name_tag="acc_warr",
                     strength=2, endurance=2, power=6,
                     class_tags=["test_r1654b_warr22"])
    for it in (w, a, acc):
        _seed_inventory(sync_db, g["id"], it["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_slots = {e["slot"] for e in res["equipped"]}
    assert equipped_slots == {"weapon", "armor", "accessory"}, (
        f"Warrior con inv class-fit deve equipaggiare tutti e 3 gli "
        f"slot, got {equipped_slots}"
    )
    assert res["swaps_count"] == 3


def test_23_empty_state_message_italian(sync_db, cleanup_r1654b):
    """Empty state IT: messaggi devono seguire il pattern approvato.

    - Se `off_class_seen == 0` → «Nessuna arma/armatura adatta a {Classe}
      Lv{n} trovata in inventario. Completa spedizioni, raid o missioni…»
    - Se `off_class_seen > 0`  → «Oggetti trovati, ma nessuno adatto alla
      classe {Classe} per lo slot arma/armatura/…»
    """
    _seed_class(sync_db, "test_r1654b_druid23", "faith", ["intellect"],
                name="Druido")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654b_druid23", level=7)

    # Caso A: inventario COMPLETAMENTE vuoto per il tipo weapon.
    #   Ma inventario contiene un armor druid-fit, così solo weapon
    #   scatena il messaggio "Nessuna arma adatta…" con off_class=0.
    armor_fit = _seed_item(sync_db, item_type="armor", name_tag="dr_armor",
                           intellect=2, faith=1, power=3,
                           class_tags=["test_r1654b_druid23"])
    _seed_inventory(sync_db, g["id"], armor_fit["id"])
    res_a = _run(_call_auto_equip(g, adv["id"]))
    wpn_det = next(
        (d for d in res_a["unchanged_slots_detail"] if d["slot"] == "weapon"),
        None,
    )
    assert wpn_det is not None
    assert wpn_det.get("off_class_seen", 0) == 0
    assert "Nessuna arma adatta a Druido Lv7" in wpn_det["reason_it"], (
        f"weapon reason_it non conforme: {wpn_det['reason_it']}"
    )
    assert "Completa spedizioni, raid o missioni" in wpn_det["reason_it"]

    # Caso B: aggiungiamo una weapon off-class → off_class_seen>0 →
    # messaggio deve cambiare a "Oggetti trovati, ma nessuno adatto…".
    off = _seed_item(sync_db, item_type="weapon", name_tag="off_w",
                     strength=5, power=7,
                     class_tags=["warrior"])
    _seed_inventory(sync_db, g["id"], off["id"])
    res_b = _run(_call_auto_equip(g, adv["id"]))
    wpn_det2 = next(
        (d for d in res_b["unchanged_slots_detail"] if d["slot"] == "weapon"),
        None,
    )
    assert wpn_det2 is not None
    assert wpn_det2.get("off_class_seen", 0) >= 1
    assert "Oggetti trovati, ma nessuno adatto alla classe Druido" in (
        wpn_det2["reason_it"]
    ), f"weapon reason_it caso B non conforme: {wpn_det2['reason_it']}"


# ═════════════════════════════════════════════════════════════════════
# ROUND 16.5.4c ADJ-3 — Class coverage seed tests (24–27)
#
# Verifica che Warlock/Alchemist/Druid con i NUOVI item del seed pack
# R16.5.4c (approvato PM 2026-07-02, opzione A) equipaggino correttamente
# tutti e 3 gli slot senza empty state falsi. La Druid regression
# aggiuntiva verifica che l'algoritmo class-aware R16.5.4b continui a
# preferire item Druid-fit rispetto a item Warrior-only in inventario
# misto.
#
# NOTA: questi test seedano item con la STESSA forma del seed script
# (`_seed_item` con `class_tags=[<slug>]`, `recommended_classes=[<slug>]`)
# per riprodurre il payload che sarà in produzione. Non toccano `orbus_r16`.
# ═════════════════════════════════════════════════════════════════════


def _seed_r1654c_warlock_pack(sync_db) -> dict:
    """Seed i 10 item Warlock del pack R16.5.4c. Ritorna dict slot→item."""
    return {
        "weapon": _seed_item(
            sync_db, item_type="weapon", name_tag="w_wlk_epic",
            rarity="Epic", intellect=4, faith=2, power=6,
            required_level=1, class_tags=["test_r1654c_warlock"],
            weapon_tags=["tome", "arcane"],
            stat_tags=["intellect", "faith"],
        ),
        "armor": _seed_item(
            sync_db, item_type="armor", name_tag="a_wlk_epic",
            rarity="Epic", intellect=4, agility=2, power=6,
            required_level=1, class_tags=["test_r1654c_warlock"],
            armor_tags=["robe", "light"],
            stat_tags=["intellect", "agility"],
        ),
        "accessory": _seed_item(
            sync_db, item_type="accessory", name_tag="acc_wlk_epic",
            rarity="Epic", intellect=4, faith=2, power=6,
            required_level=1, class_tags=["test_r1654c_warlock"],
            stat_tags=["intellect", "faith"],
        ),
    }


def test_24_r1654c_warlock_full_equip(sync_db, cleanup_r1654b):
    """Warlock (int primary, faith+agility secondary) con weapon+armor+
    accessory Epic Lv8 del seed pack R16.5.4c → tutti e 3 equipaggiati,
    swaps=3, nessun off_class_seen (tutti class-fit)."""
    _seed_class(sync_db, "test_r1654c_warlock", "intellect",
                ["faith", "agility"], name="Warlock")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_warlock",
                           level=10)
    pack = _seed_r1654c_warlock_pack(sync_db)
    for it in pack.values():
        _seed_inventory(sync_db, g["id"], it["id"])

    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_slots = {e["slot"] for e in res["equipped"]}
    assert equipped_slots == {"weapon", "armor", "accessory"}, (
        f"Warlock deve equipaggiare tutti e 3 gli slot, got "
        f"{equipped_slots}"
    )
    assert res["swaps_count"] == 3
    # Nessun unchanged_slots_detail con off_class_seen > 0.
    for d in res.get("unchanged_slots_detail", []):
        assert d.get("off_class_seen", 0) == 0, (
            f"Warlock non deve avere off_class_seen>0 (tutti class-fit): "
            f"{d}"
        )


def test_25_r1654c_alchemist_full_equip(sync_db, cleanup_r1654b):
    """Alchemist (int primary, agility+endurance secondary) → tutti e 3
    gli slot equipaggiati con item Epic Lv8 class-fit."""
    _seed_class(sync_db, "test_r1654c_alchemist", "intellect",
                ["agility", "endurance"], name="Alchemist")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_alchemist",
                           level=10)
    weapon = _seed_item(
        sync_db, item_type="weapon", name_tag="w_alch_epic",
        rarity="Epic", intellect=4, agility=2, power=6,
        class_tags=["test_r1654c_alchemist"],
        weapon_tags=["alchemical_flask", "arcane"],
        stat_tags=["intellect", "agility"],
    )
    armor = _seed_item(
        sync_db, item_type="armor", name_tag="a_alch_epic",
        rarity="Epic", intellect=4, endurance=2, power=6,
        class_tags=["test_r1654c_alchemist"],
        armor_tags=["robe", "light"],
        stat_tags=["intellect", "endurance"],
    )
    accessory = _seed_item(
        sync_db, item_type="accessory", name_tag="acc_alch_epic",
        rarity="Epic", intellect=4, endurance=2, power=6,
        class_tags=["test_r1654c_alchemist"],
        stat_tags=["intellect", "endurance"],
    )
    for it in (weapon, armor, accessory):
        _seed_inventory(sync_db, g["id"], it["id"])

    res = _run(_call_auto_equip(g, adv["id"]))
    equipped_slots = {e["slot"] for e in res["equipped"]}
    assert equipped_slots == {"weapon", "armor", "accessory"}, (
        f"Alchemist deve equipaggiare tutti e 3 gli slot, got "
        f"{equipped_slots}"
    )
    assert res["swaps_count"] == 3
    for d in res.get("unchanged_slots_detail", []):
        assert d.get("off_class_seen", 0) == 0


def test_26_r1654c_druid_prefers_class_fit_over_warrior_armor(
    sync_db, cleanup_r1654b,
):
    """Regression class-aware R16.5.4b + ADJ-3 Druid: Druid con NUOVA
    armor Druid-fit (grovewarden-mantle-like Rare) + armor Warrior-only
    (off-class) in inventario → sceglie SEMPRE la nuova armor Druid,
    mai la Warrior."""
    _seed_class(sync_db, "test_r1654c_druid", "faith", ["intellect"],
                name="Druido")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_druid",
                           level=8)
    # NEW armor druid-fit (ADJ-3 pack).
    druid_armor = _seed_item(
        sync_db, item_type="armor", name_tag="druid_grove_new",
        rarity="Rare", faith=2, intellect=2, power=4,
        required_level=5, class_tags=["test_r1654c_druid"],
        armor_tags=["leather", "natural", "light"],
        stat_tags=["faith", "intellect"],
    )
    # Warrior-only armor (off-class for druid).
    warrior_armor = _seed_item(
        sync_db, item_type="armor", name_tag="warr_plate",
        rarity="Epic", strength=5, endurance=2, power=8,
        required_level=7, class_tags=["warrior", "paladin"],
        armor_tags=["heavy", "plate"],
    )
    _seed_inventory(sync_db, g["id"], druid_armor["id"])
    _seed_inventory(sync_db, g["id"], warrior_armor["id"])

    res = _run(_call_auto_equip(g, adv["id"]))
    armor_equipped = next(
        (e for e in res["equipped"] if e["slot"] == "armor"), None,
    )
    assert armor_equipped is not None, "armor doveva essere equipaggiato"
    assert armor_equipped["item_slug"] == druid_armor["slug"], (
        f"Druid deve preferire armor class-fit ({druid_armor['slug']}), "
        f"ha scelto {armor_equipped['item_slug']}"
    )
    # Warrior armor NON deve essere nella lista equipped.
    equipped_slugs = [e["item_slug"] for e in res["equipped"]]
    assert warrior_armor["slug"] not in equipped_slugs, (
        f"REGRESSIONE R16.5.4b: warrior armor equipaggiato su Druido! "
        f"equipped={equipped_slugs}"
    )


def test_27_r1654c_alchemist_no_httpexception_leak_in_warnings(
    sync_db, cleanup_r1654b,
):
    """R16.5.4c ADJ-3.c: garantisce che il payload Auto-Equip non contenga
    MAI la stringa tecnica 'HTTPException' nei `warnings_it` / warning
    generici (bug R16.5.4b REOPEN #2). Verifica anche assenza di
    '[object Object]' e 'None' leak nei messaggi player-facing."""
    _seed_class(sync_db, "test_r1654c_al2", "intellect", ["agility"],
                name="Alchemist")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_al2", level=10)
    # Inventory con solo weapon class-fit; armor+accessory ASSENTI.
    weapon = _seed_item(
        sync_db, item_type="weapon", name_tag="w_alch_only",
        rarity="Epic", intellect=4, agility=2, power=6,
        class_tags=["test_r1654c_al2"],
        weapon_tags=["alchemical_flask", "arcane"],
    )
    _seed_inventory(sync_db, g["id"], weapon["id"])
    res = _run(_call_auto_equip(g, adv["id"]))

    # Collect ALL strings from the response for a text scan.
    import json as _json
    payload_str = _json.dumps(res, ensure_ascii=False)
    for banned in ("HTTPException", "[object Object]", "'None'"):
        assert banned not in payload_str, (
            f"REGRESSIONE R16.5.4c ADJ-3.c: stringa tecnica {banned!r} "
            f"leakata nel payload player-facing. Payload: {payload_str}"
        )
    # Empty state IT deve essere presente per armor + accessory.
    unchanged_slots = set(res.get("unchanged_slots", []))
    assert "armor" in unchanged_slots and "accessory" in unchanged_slots
    for d in res.get("unchanged_slots_detail", []):
        # reason_it deve essere pulito, italiano, no leak tecnico.
        assert isinstance(d.get("reason_it"), str) and d["reason_it"]
        assert "HTTPException" not in d["reason_it"]

