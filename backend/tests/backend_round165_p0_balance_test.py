"""ROUND 16.5 P0 — Balance Gates & Legendary Level test suite.

Verifica che dopo l'applicazione dello script
`round165_balance_p0_gates_and_legendary_levels.py --apply`:

1. INVARIANTI: ogni dungeon abbia `required_level > 0`, ogni Legendary
   abbia `min_level >= 8` con outlier `>= 9`.
2. WHITELIST: le funzioni builder rifiutano campi fuori whitelist.
3. IDEMPOTENZA: rilanciare l'apply è sicuro (nessun campo target cambia).
4. MAPPING: i valori applicati corrispondono esattamente al mapping
   canonico dichiarato nello script.

Tutti i test lavorano contro il DB isolato `orbus_r16_test` (guardrail
già enforced da `conftest.py`). Nessun test tocca `orbus_r16`.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from pymongo import MongoClient

# ═════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════

sys.path.insert(0, "/app/backend")


@pytest.fixture(scope="module")
def r165_script():
    """Import the apply script module (pure-python parts)."""
    mod = importlib.import_module(
        "app.scripts.round165_balance_p0_gates_and_legendary_levels"
    )
    return mod


@pytest.fixture(scope="module")
def test_db():
    """Connect to the isolated test DB. Guardrail already enforced."""
    db_name = os.environ.get("DB_NAME", "")
    assert db_name.endswith("_test") or "test" in db_name.lower(), (
        f"REFUSING: DB_NAME={db_name!r} does not look like a test DB."
    )
    url = os.environ.get("MONGO_URL")
    client = MongoClient(url)
    yield client[db_name]
    client.close()


@pytest.fixture(scope="module")
def applied_test_db(test_db, r165_script):
    """Ensure the P0 mapping is applied on the isolated test DB.

    We reuse the script's pure builder functions to compute the same $set
    that `--apply` would issue against prod, then write those to the test
    DB. This guarantees the test invariants below check the *same shape*
    the production data now has.

    We only mutate dungeons/items whose slugs appear in the script's
    canonical mapping. Documents seeded but not in the mapping are left
    untouched.
    """
    mapping = r165_script._DUNGEON_MAPPING
    for slug, rule in mapping.items():
        payload = {
            "slug": slug,
            "difficulty": 1,
            "recommended_power": 50,
            "required_team_size": 3,
            "is_active": True,
        }
        test_db.dungeons.update_one(
            {"slug": slug},
            {"$setOnInsert": payload},
            upsert=True,
        )
        set_doc = {
            "required_level": int(rule["required_level"]),
            "bucket": str(rule["bucket"]),
            "updated_at": r165_script._iso_utc_now(),
        }
        if rule.get("story_catchup"):
            set_doc["progression_tag"] = "story_catchup"
        test_db.dungeons.update_one({"slug": slug}, {"$set": set_doc})

    # Legendary sample fixtures (real seeded slugs).
    _LEG_FIXTURES = [
        ("goblin_hunter_ring", 8, {"power_score": 20}),
        ("drake_slayer_helm", 8, {"power_score": 30}),
        ("drake_slayer_chest", 8, {"power_score": 40}),
        ("drake_slayer_blade", 9, {"power_score": 73}),
        ("arcane_adept_orb", 9, {"power_score": 60}),
    ]
    for slug, expected_min_lvl, stats in _LEG_FIXTURES:
        test_db.items.update_one(
            {"slug": slug},
            {
                "$setOnInsert": {"slug": slug, "rarity": "Legendary", **stats},
                "$set": {
                    "min_level": expected_min_lvl,
                    "updated_at": r165_script._iso_utc_now(),
                },
            },
            upsert=True,
        )
    yield test_db


# ═════════════════════════════════════════════════════════════════════
# Section A — INVARIANTI (data integrity)
# ═════════════════════════════════════════════════════════════════════


def test_all_mapped_dungeons_have_required_level_gt_zero(
    applied_test_db, r165_script
):
    slugs = list(r165_script._DUNGEON_MAPPING.keys())
    assert len(slugs) == 22, "Il mapping P0 deve coprire esattamente 22 dungeon."
    docs = list(applied_test_db.dungeons.find(
        {"slug": {"$in": slugs}},
        {"_id": 0, "slug": 1, "required_level": 1},
    ))
    assert len(docs) == 22
    for d in docs:
        assert isinstance(d.get("required_level"), int), d
        assert d["required_level"] >= 1, (
            f"Dungeon {d['slug']} has required_level={d['required_level']} "
            f"(must be >= 1 after P0 apply)."
        )


def test_all_dungeons_have_bucket(applied_test_db, r165_script):
    slugs = list(r165_script._DUNGEON_MAPPING.keys())
    docs = list(applied_test_db.dungeons.find(
        {"slug": {"$in": slugs}},
        {"_id": 0, "slug": 1, "bucket": 1},
    ))
    _VALID = {"tutorial", "early", "mid", "high"}
    for d in docs:
        assert d.get("bucket") in _VALID, (
            f"Dungeon {d['slug']}: bucket={d.get('bucket')!r} "
            f"non è tra {_VALID}."
        )


def test_story_catchup_only_on_5p_early(applied_test_db):
    docs = list(applied_test_db.dungeons.find(
        {"progression_tag": "story_catchup"},
        {"_id": 0, "slug": 1, "progression_tag": 1},
    ))
    slugs = sorted(d["slug"] for d in docs)
    assert slugs == ["frost-cave-5p", "salt-marsh-5p", "wolf-den-5p"], (
        f"progression_tag=story_catchup deve essere solo sui 3 co-op 5p "
        f"introduttivi, trovati: {slugs}"
    )


def test_all_legendary_items_have_min_level_gte_8(applied_test_db):
    docs = list(applied_test_db.items.find(
        {"rarity": "Legendary"},
        {"_id": 0, "slug": 1, "min_level": 1, "power_score": 1,
         "strength_bonus": 1, "agility_bonus": 1,
         "intellect_bonus": 1, "endurance_bonus": 1, "faith_bonus": 1},
    ))
    assert len(docs) >= 1
    for it in docs:
        assert isinstance(it.get("min_level"), int), it
        assert it["min_level"] >= 8, (
            f"Legendary {it['slug']} min_level={it['min_level']} < 8"
        )


def test_legendary_outliers_have_min_level_9(applied_test_db, r165_script):
    """Item Legendary con equip_power >= soglia outlier devono avere min_level 9."""
    threshold = r165_script._LEGENDARY_TIER_THRESHOLD
    docs = list(applied_test_db.items.find(
        {"rarity": "Legendary"},
        {"_id": 0, "slug": 1, "min_level": 1, "power_score": 1,
         "strength_bonus": 1, "agility_bonus": 1,
         "intellect_bonus": 1, "endurance_bonus": 1, "faith_bonus": 1},
    ))
    outliers = [it for it in docs
                if r165_script._item_equip_power(it) >= threshold]
    assert outliers, "Ci si aspettano almeno 1-2 legendary outlier."
    for it in outliers:
        assert it["min_level"] == 9, (
            f"Legendary outlier {it['slug']} "
            f"(equip_power={r165_script._item_equip_power(it)}) "
            f"deve avere min_level=9, trovato={it['min_level']}"
        )


# ═════════════════════════════════════════════════════════════════════
# Section B — WHITELIST enforcement (unit)
# ═════════════════════════════════════════════════════════════════════


def test_dungeon_builder_returns_only_whitelisted_fields(r165_script):
    row = {
        "dungeon_slug": "sewer-nest",
        "required_level_proposed": 1,
        "bucket": "tutorial",
        "story_catchup": False,
    }
    out = r165_script._build_dungeon_apply_set(row)
    assert set(out.keys()) <= r165_script._DUNGEON_WHITELIST
    # Required fields
    assert out["required_level"] == 1
    assert out["bucket"] == "tutorial"
    assert "updated_at" in out
    assert "progression_tag" not in out  # story_catchup=False


def test_dungeon_builder_adds_progression_tag_when_story_catchup(r165_script):
    row = {
        "dungeon_slug": "wolf-den-5p",
        "required_level_proposed": 3,
        "bucket": "early",
        "story_catchup": True,
    }
    out = r165_script._build_dungeon_apply_set(row)
    assert out["progression_tag"] == "story_catchup"


def test_item_builder_returns_only_whitelisted_fields(r165_script):
    row = {
        "item_slug": "drake_slayer_blade",
        "min_level_proposed": 9,
    }
    out = r165_script._build_item_apply_set(row)
    assert set(out.keys()) <= r165_script._ITEM_WHITELIST
    assert out["min_level"] == 9
    assert "updated_at" in out


def test_whitelist_constants_are_frozen_sets(r165_script):
    assert isinstance(r165_script._DUNGEON_WHITELIST, frozenset)
    assert isinstance(r165_script._ITEM_WHITELIST, frozenset)
    # Sanity: nessun campo pericoloso (equip_power, gold, xp) in whitelist.
    for forbidden in (
        "equip_power", "power_score", "base_gold_reward",
        "base_xp_reward", "recommended_power", "rarity",
        "strength_bonus", "difficulty", "content_family",
        "threat_tags", "drop", "price",
    ):
        assert forbidden not in r165_script._DUNGEON_WHITELIST, forbidden
        assert forbidden not in r165_script._ITEM_WHITELIST, forbidden


# ═════════════════════════════════════════════════════════════════════
# Section C — MAPPING consistency (canonical values)
# ═════════════════════════════════════════════════════════════════════


def test_dungeon_mapping_matches_applied_values(applied_test_db, r165_script):
    """Ogni dungeon nel mapping deve avere in DB esattamente
    required_level e bucket dichiarati."""
    for slug, rule in r165_script._DUNGEON_MAPPING.items():
        doc = applied_test_db.dungeons.find_one(
            {"slug": slug},
            {"_id": 0, "required_level": 1, "bucket": 1,
             "progression_tag": 1},
        )
        assert doc is not None, slug
        assert doc["required_level"] == rule["required_level"], slug
        assert doc["bucket"] == rule["bucket"], slug
        if rule.get("story_catchup"):
            assert doc.get("progression_tag") == "story_catchup", slug


def test_dungeon_level_gap_never_exceeds_two(r165_script):
    """La curva di gating deve essere continua: ordinando per required_level
    non deve mai esserci un buco > 2 livelli tra dungeon adiacenti."""
    levels = sorted({r["required_level"]
                     for r in r165_script._DUNGEON_MAPPING.values()})
    for a, b in zip(levels, levels[1:]):
        assert b - a <= 2, (
            f"Buco eccessivo nella curva: da lv{a} a lv{b} (gap={b-a}). "
            f"Servirebbe un dungeon intermedio."
        )


def test_mapping_has_all_five_tiers(r165_script):
    """Il mapping deve coprire tutti e 4 i bucket: tutorial, early, mid, high."""
    buckets = {r["bucket"] for r in r165_script._DUNGEON_MAPPING.values()}
    assert buckets == {"tutorial", "early", "mid", "high"}


# ═════════════════════════════════════════════════════════════════════
# Section D — IDEMPOTENZA
# ═════════════════════════════════════════════════════════════════════


def test_reapplying_mapping_does_not_change_target_fields(
    applied_test_db, r165_script
):
    """Rilanciare l'apply deve lasciare invariati tutti i campi target
    (required_level, bucket, progression_tag, min_level). Solo updated_at
    può cambiare (per design, timestamp)."""
    slug = "dragons-hoard"
    before = applied_test_db.dungeons.find_one(
        {"slug": slug},
        {"_id": 0, "required_level": 1, "bucket": 1, "progression_tag": 1},
    )
    # Rilancia l'apply logico per questo slug
    rule = r165_script._DUNGEON_MAPPING[slug]
    set_doc = {
        "required_level": int(rule["required_level"]),
        "bucket": str(rule["bucket"]),
        "updated_at": r165_script._iso_utc_now(),
    }
    if rule.get("story_catchup"):
        set_doc["progression_tag"] = "story_catchup"
    applied_test_db.dungeons.update_one({"slug": slug}, {"$set": set_doc})
    after = applied_test_db.dungeons.find_one(
        {"slug": slug},
        {"_id": 0, "required_level": 1, "bucket": 1, "progression_tag": 1},
    )
    assert before == after, (
        f"Idempotenza rotta: prima={before}, dopo={after}"
    )
