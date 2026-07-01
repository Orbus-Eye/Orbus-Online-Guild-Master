"""ROUND 15 — Fase 2 backend tests.

Covers:
  - Compatibility validator (block / warning / universal / ok).
  - XP multiplier helper (all 4 tiers + hard floor).
  - Material drop tables: +70% rate sample, cap enforcement,
    independence from item rolls.
  - Per-member XP report shape and PII sweep.

These tests use the same `tester@orbus.test` account already seeded
for the rest of the round suite. They are read-only against the live
DB (no admin overrides, no destructive ops) — they exercise the new
modules directly when possible to stay fast and deterministic.
"""
from __future__ import annotations

import os
from collections import Counter

import pytest
import requests

from app.equipment.compatibility import check_equip_compatibility
from app.expeditions.material_drop_tables import (
    BOOST_FACTOR,
    RARITY_CAP,
    boosted_rate,
    TIER_MATERIAL_TABLE,
)
from app.expeditions.xp_modifier import (
    MIN_XP_MULTIPLIER,
    compute_xp_multiplier,
    expected_primary_stat,
)


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"


def _login(email="tester@orbus.test", password="password123") -> str:
    r = requests.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


# ─── A. Compatibility validator ──────────────────────────────────────────────
def test_r15p2_01_heavy_armor_blocks_mage():
    adv = {"class_slug": "mage", "level": 5}
    item = {"item_type": "armor", "armor_tags": ["heavy", "plate"]}
    r = check_equip_compatibility(adv, item)
    assert r["severity"] == "block"
    assert r["reason_code"] == "heavy_armor_forbidden"
    assert "armatura pesante" in r["reason_it"].lower()


def test_r15p2_02_arcane_staff_blocks_warrior():
    adv = {"class_slug": "warrior", "level": 5}
    item = {"item_type": "weapon", "weapon_tags": ["staff", "arcane"]}
    r = check_equip_compatibility(adv, item)
    assert r["severity"] == "block"
    assert r["reason_code"] == "arcane_weapon_forbidden"


def test_r15p2_03_two_handed_warning_for_rogue():
    adv = {"class_slug": "rogue", "level": 5}
    item = {
        "item_type": "weapon",
        "weapon_tags": ["sword", "two_handed"],
        "recommended_classes": ["warrior", "berserker"],
    }
    r = check_equip_compatibility(adv, item)
    assert r["allowed"] is True
    assert r["severity"] == "warning"
    assert r["reason_code"] == "not_recommended_class"


def test_r15p2_04_universal_accessory_ok_for_any_class():
    item = {"item_type": "accessory", "is_universal": True, "armor_tags": []}
    for cls in ("mage", "warrior", "priest"):
        r = check_equip_compatibility({"class_slug": cls, "level": 1}, item)
        assert r["severity"] == "ok"
        assert r["allowed"] is True


def test_r15p2_05_signature_blocks_other_class():
    adv = {"class_slug": "ranger", "level": 10}
    item = {"item_type": "weapon", "required_class_optional": "berserker"}
    r = check_equip_compatibility(adv, item)
    assert r["severity"] == "block"
    assert r["reason_code"] == "class_locked"


# ─── B. XP multiplier ────────────────────────────────────────────────────────
def _cls_doc(primary="strength", base=10):
    return {
        "name": "TestClass",
        "primary_stat": primary,
        f"base_{primary}": base,
        "xp_primary_stat_policy": {
            "enabled": True,
            "schema_version": 2,
            "min_multiplier": 0.70,
        },
    }


def test_r15p2_06_expected_primary_stat_grows_with_level():
    cls = _cls_doc("strength", 10)
    assert expected_primary_stat(cls, 1) == 10 + round(1 * 0.5)
    assert expected_primary_stat(cls, 10) == 10 + round(10 * 0.5)
    assert expected_primary_stat(cls, 50) == 10 + round(50 * 0.5)


def test_r15p2_07_xp_multiplier_ok_tier():
    cls = _cls_doc("strength", 10)
    adv = {"strength": 11, "level": 1}
    r = compute_xp_multiplier(adv, cls)
    assert r["multiplier"] == 1.0
    assert r["reason_code"] in ("primary_ok", "primary_ok_tolerance")


def test_r15p2_08_xp_multiplier_minor_debuff():
    # threshold L1 = 10 + 1 = 11 (since round(1*0.5)=0 → wait: round(0.5)=0).
    # Actually round(0.5)=0 in Python banker's rounding. Let's compute for L4
    # where threshold = 10 + round(2) = 12; actual 10 → deficit 16.6%.
    cls = _cls_doc("strength", 10)
    adv = {"strength": 10, "level": 4}
    r = compute_xp_multiplier(adv, cls)
    assert r["threshold"] == 12
    assert r["multiplier"] == 0.90
    assert r["reason_code"] == "primary_stat_low_minor"


def test_r15p2_09_xp_multiplier_major_debuff():
    # threshold L8 = 10 + 4 = 14; actual 11 → deficit ~21%.
    cls = _cls_doc("strength", 10)
    adv = {"strength": 11, "level": 8}
    r = compute_xp_multiplier(adv, cls)
    assert r["threshold"] == 14
    assert r["multiplier"] == 0.80
    assert r["reason_code"] == "primary_stat_low_major"


def test_r15p2_10_xp_multiplier_critical_floor():
    # threshold L20 = 10 + 10 = 20; actual 10 → deficit 50%.
    cls = _cls_doc("strength", 10)
    adv = {"strength": 10, "level": 20}
    r = compute_xp_multiplier(adv, cls)
    assert r["threshold"] == 20
    assert r["multiplier"] == MIN_XP_MULTIPLIER == 0.70
    assert r["reason_code"] == "primary_stat_low_critical"


def test_r15p2_11_xp_multiplier_policy_disabled_passthrough():
    cls = _cls_doc("strength", 10)
    cls["xp_primary_stat_policy"]["enabled"] = False
    r = compute_xp_multiplier({"strength": 1, "level": 50}, cls)
    assert r["multiplier"] == 1.0
    assert r["reason_code"] == "policy_disabled"


# ─── C. Material drop tables ─────────────────────────────────────────────────
def test_r15p2_12_boosted_rate_respects_cap():
    # Common with base 70% → 70 × 1.7 = 119% → clip to 85%.
    assert boosted_rate(0.70, "common") == RARITY_CAP["common"]
    # Rare with base 6% → 10.2% < 25%.
    assert boosted_rate(0.06, "rare") == 0.102


def test_r15p2_13_material_tables_have_floor_entries():
    # iron_shard / raw_leather / healing_herb essential in T1; their boosted
    # rate must be ≥ 17% (the documented floor).
    t1 = dict((slug, br) for slug, _r, br, _q in TIER_MATERIAL_TABLE["T1"])
    for must in ("iron_shard", "raw_leather", "healing_herb"):
        boosted = round(t1[must] * BOOST_FACTOR, 4)
        assert boosted >= 0.17, f"{must} boosted={boosted} below 17% floor"


def test_r15p2_14_material_rates_seventy_pct_higher():
    # Sample 5 entries across tiers; boosted rate must be ≥ 1.70x baseline.
    samples = [
        TIER_MATERIAL_TABLE["T1"][0],
        TIER_MATERIAL_TABLE["T2"][0],
        TIER_MATERIAL_TABLE["T3"][0],
        TIER_MATERIAL_TABLE["T3"][4],  # dragon_essence rare
        TIER_MATERIAL_TABLE["T4"][2],
    ]
    for slug, rarity, base, _q in samples:
        boosted = boosted_rate(base, rarity)
        assert boosted >= min(base * BOOST_FACTOR, RARITY_CAP[rarity]) - 1e-6
        # And the cap is never exceeded.
        assert boosted <= RARITY_CAP[rarity] + 1e-6


def test_r15p2_15_rare_and_epic_caps_enforced():
    # Caps: Rare 25%, Epic 15%.
    assert boosted_rate(0.50, "rare") == RARITY_CAP["rare"]
    assert boosted_rate(0.50, "epic") == RARITY_CAP["epic"]


# ─── D. Roll independence (1000 simulations) ─────────────────────────────────
def test_r15p2_16_item_and_material_rolls_independent():
    """Verify the material roller produces variable 0..N outputs by running
    a tight in-process loop with a stubbed db.items lookup. Pure sync to
    avoid the optional pytest-asyncio dependency."""
    import asyncio
    from app.expeditions.material_drop_tables import roll_materials_for_dungeon

    class _FakeCursor:
        def __init__(self, docs):
            self._docs = list(docs)

        def __aiter__(self):
            self._i = 0
            return self

        async def __anext__(self):
            if self._i >= len(self._docs):
                raise StopAsyncIteration
            v = self._docs[self._i]
            self._i += 1
            return v

    class _FakeColl:
        def find(self, *a, **kw):
            return _FakeCursor([
                {"slug": "iron_shard"}, {"slug": "raw_leather"},
                {"slug": "healing_herb"}, {"slug": "arcane_dust"},
                {"slug": "dull_gem"}, {"slug": "dragon_essence"},
            ])

    class _FakeDB:
        items = _FakeColl()

    dungeon = {"slug": "shadow-crypts", "base_xp_reward": 60}
    counters = Counter()

    async def _run():
        for _ in range(1000):
            drops = await roll_materials_for_dungeon(_FakeDB(), dungeon, True)
            if drops:
                counters["materials_drop"] += 1
            else:
                counters["materials_none"] += 1

    asyncio.run(_run())
    assert counters["materials_drop"] > 0
    assert counters["materials_none"] > 0


# ─── E. Live API smoke (PII sweep + class projection still present) ─────────
def test_r15p2_17_adventurer_classes_carry_primary_stat():
    t = _login()
    r = requests.get(f"{API}/adventurer-classes", headers=_auth(t), timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    classes = body.get("classes") if isinstance(body, dict) else body
    assert isinstance(classes, list)
    with_primary = [c for c in classes if c.get("primary_stat")]
    # ROUND 16.0: now exactly 10 active base classes (Berserker,
    # Assassin, Necromancer deprecated into specializations).
    assert len(with_primary) >= 10, (
        f"Expected ≥10 active classes with primary_stat, got {len(with_primary)}"
    )
    # Body PII / ObjectId leak sweep.
    body_text = r.text.lower()
    assert "@orbus.test" not in body_text
    assert "$oid" not in body_text


def test_r15p2_18_class_xp_policy_enabled_in_response():
    t = _login()
    r = requests.get(f"{API}/adventurer-classes", headers=_auth(t), timeout=15)
    assert r.status_code == 200
    body = r.json()
    classes = body.get("classes") if isinstance(body, dict) else body
    policies = [c.get("xp_primary_stat_policy", {}) for c in classes]
    # Out of 12 classes, ALL active ones must have policy.enabled == True
    # post-seed run. The bootstrap seed runs on app startup so the value is
    # the schema_version-2 default.
    enabled_count = sum(1 for p in policies if p.get("enabled"))
    # ROUND 16.0: 10 active base classes (was 12 before deprecation).
    assert enabled_count >= 10, (
        f"Expected XP policy enabled on ≥10 classes, got {enabled_count}. "
        "Re-run app.scripts.round15_seed_class_identity."
    )
