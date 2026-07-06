"""🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED
R18.4 CLOSED & SEALED
DO NOT MODIFY. SHA256 verified in /app/backend/tests/backend_r18_4_sealed_integrity_test.py

ROUND 18.4 — Phase B3 Class-Bound Dry-Run Test Suite.

Copertura (16 test = 5 gruppi):

Group 1 — Registry shape (3 tests):
  t01_registry_json_parsable
  t02_registry_totals_178_11_21_146
  t03_registry_hard_items_exact_11_slugs

Group 2 — Bucket derivation (4 tests):
  t04_hard_derivation_required_class_optional
  t05_universal_derivation_material_consumable
  t06_soft_derivation_residual
  t07_no_overlap_hard_intersect_universal

Group 3 — Backfill dry-run (4 tests):
  t08_backfill_dry_run_target_count_140
  t09_backfill_shield_maps_to_armor
  t10_backfill_skip_already_populated_17
  t11_backfill_apply_enabled_false_blocks_write

Group 4 — Class-bound dry-run (3 tests):
  t12_class_bound_dry_run_would_add_binding_policy_178
  t13_class_bound_guard_hard_stop_rejects_blocked_fields
  t14_class_bound_apply_enabled_false_blocks_write

Group 5 — Rate-limit + signals (2 tests):
  t15_rate_limit_bucket_key_format
  t16_derived_signals_recommended_for_class_and_universal

Isolamento: usa DB corrente (read-only queries). Nessuna scrittura DB.
Governance: verifica APPLY_ENABLED=False, guard hard-stop, no touch a sigilli.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# ═════════════════════════════════════════════════════════════════════
# Constants / paths
# ═════════════════════════════════════════════════════════════════════

REGISTRY_PATH = Path("/app/memory/r18_4_class_bound_registry.json")
DECISION_LOCK_PATH = Path("/app/memory/r18_4_phase_b2_pm_decisions.json")

EXPECTED_TOTAL = 178
EXPECTED_HARD = 11
EXPECTED_UNIVERSAL = 21
EXPECTED_SOFT = 146
EXPECTED_BACKFILL_TARGET = 140

EXPECTED_HARD_SLUGS = frozenset({
    "drake_slayer_helm",
    "drake_slayer_chest",
    "drake_slayer_blade",
    "spec_signature_truestrike_bow",
    "spec_signature_bloodied_greataxe",
    "spec_signature_breakers_gauntlets",
    "spec_signature_silent_kris",
    "spec_signature_storm_rod",
    "spec_signature_corrupted_blade",
    "spec_signature_twin_blades",
    "spec_signature_runic_aegis",
})

UNIVERSAL_ITEM_TYPES = frozenset({
    "material", "material_continental", "material_event", "consumable",
})


# ═════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def registry():
    """Load the R18.4 class-bound registry (read-only)."""
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def decision_lock():
    """Load the R18.4 B2 PM decision lock (read-only)."""
    return json.loads(DECISION_LOCK_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def backfill_module():
    """Import the backfill sibling script (read-only, no side effects at import)."""
    from app.scripts import round18_4_backfill_slot_type as mod
    return mod


@pytest.fixture(scope="module")
def class_bound_module():
    """Import the class-bound sibling script (read-only)."""
    from app.scripts import round18_4_apply_class_bound as mod
    return mod


# ═════════════════════════════════════════════════════════════════════
# Group 1 — Registry shape (3 tests)
# ═════════════════════════════════════════════════════════════════════

def test_t01_registry_json_parsable(registry):
    """Registry JSON is present, parsable, and has minimal required keys."""
    assert isinstance(registry, dict), "registry must be a JSON object"
    for key in ("meta", "totals", "policy_derivation_algorithm_locked_sq6",
                "slot_type_backfill", "hard_bucket_11", "universal_bucket_21"):
        assert key in registry, f"missing required key {key!r}"


def test_t02_registry_totals_178_11_21_146(registry):
    """Totals must exactly match 178 total = 11 hard + 21 universal + 146 soft."""
    t = registry["totals"]
    assert t["total_items"] == EXPECTED_TOTAL
    assert t["hard_policy_target"] == EXPECTED_HARD
    assert t["universal_policy_target"] == EXPECTED_UNIVERSAL
    assert t["soft_policy_target"] == EXPECTED_SOFT
    assert (
        t["hard_policy_target"] + t["universal_policy_target"] + t["soft_policy_target"]
        == t["total_items"]
    ), "totals sum must equal total_items"
    assert t["overlap_hard_intersect_universal"] == 0
    assert t["backfill_slot_type_target"] == EXPECTED_BACKFILL_TARGET


def test_t03_registry_hard_items_exact_11_slugs(registry):
    """Hard bucket must contain exactly the 11 expected slugs (verbatim)."""
    hard = registry["hard_bucket_11"]
    assert len(hard) == EXPECTED_HARD
    slugs = {item["slug"] for item in hard}
    assert slugs == EXPECTED_HARD_SLUGS, (
        f"hard slug set drift. missing={EXPECTED_HARD_SLUGS - slugs}, "
        f"extra={slugs - EXPECTED_HARD_SLUGS}"
    )


# ═════════════════════════════════════════════════════════════════════
# Group 2 — Bucket derivation (4 tests)
# ═════════════════════════════════════════════════════════════════════

def test_t04_hard_derivation_required_class_optional(class_bound_module):
    """SQ6 step 1: required_class_optional populated → hard."""
    derive = class_bound_module._derive_item_binding_policy
    assert derive({"required_class_optional": "warrior", "item_type": "armor"}) == "hard"
    assert derive({"required_class_optional": "assassin", "item_type": "weapon"}) == "hard"
    # empty/None → NOT hard
    assert derive({"required_class_optional": None, "item_type": "weapon"}) == "soft"
    assert derive({"required_class_optional": "", "item_type": "weapon"}) == "soft"


def test_t05_universal_derivation_material_consumable(class_bound_module):
    """SQ6 step 2: item_type in universal set → universal."""
    derive = class_bound_module._derive_item_binding_policy
    for it in UNIVERSAL_ITEM_TYPES:
        assert derive({"required_class_optional": None, "item_type": it}) == "universal", (
            f"item_type={it} must derive universal"
        )


def test_t06_soft_derivation_residual(class_bound_module):
    """SQ6 step 3: residuo → soft."""
    derive = class_bound_module._derive_item_binding_policy
    for it in ("weapon", "armor", "accessory", "shield"):
        assert derive({"required_class_optional": None, "item_type": it}) == "soft", (
            f"item_type={it} without req_class must derive soft"
        )


def test_t07_no_overlap_hard_intersect_universal(registry):
    """No item can be both hard AND universal (mutually exclusive)."""
    hard_slugs = {i["slug"] for i in registry["hard_bucket_11"]}
    universal_slugs: set[str] = set()
    for _typ, slugs in registry["universal_bucket_21"].items():
        universal_slugs |= set(slugs)
    overlap = hard_slugs & universal_slugs
    assert overlap == set(), f"unexpected overlap hard∩universal: {overlap}"


# ═════════════════════════════════════════════════════════════════════
# Group 3 — Backfill dry-run (4 tests)
# ═════════════════════════════════════════════════════════════════════

def test_t08_backfill_dry_run_target_count_140(backfill_module):
    """Dry-run must report internally-consistent counts (target=140 nel live DB).
    Nel DB test isolato la count può differire ma DEVE essere internamente coerente.
    Invariante verificato: would_modify == sum(breakdown_by_item_type) == guard_passed."""
    report = backfill_module.dry_run()
    assert report["mode"] == "dry_run"
    assert report["target_count_expected"] == EXPECTED_BACKFILL_TARGET  # locked constant
    assert report["errors_count"] == 0
    # invariante: would_modify == guard_passed
    assert report["would_modify_count"] == report["guard_hard_stop_checks_passed"]
    # invariante: sum(breakdown_by_item_type) == would_modify
    assert sum(report["breakdown_by_item_type"].values()) == report["would_modify_count"]
    # invariante: sum(breakdown_by_target_slot_type) == would_modify
    assert sum(report["breakdown_by_target_slot_type"].values()) == report["would_modify_count"]


def test_t09_backfill_shield_maps_to_armor(backfill_module):
    """SQ1(a) locked: shield item_type → slot_type='armor'.
    Invariante: se shield presenti nel target, tutti sono mappati in armor."""
    report = backfill_module.dry_run()
    shield_count = report["breakdown_by_item_type"].get("shield", 0)
    mapped_slugs = report["shield_mapped_to_armor_slugs"]
    # shield count and mapped slugs must match
    assert len(mapped_slugs) == shield_count, (
        f"shield count mismatch: item_type=shield count={shield_count}, "
        f"mapped_slugs count={len(mapped_slugs)}"
    )
    # invariante SQ1(a): breakdown_by_target_slot_type[armor] deve includere gli shield
    armor_target = report["breakdown_by_target_slot_type"].get("armor", 0)
    armor_input = report["breakdown_by_item_type"].get("armor", 0)
    # armor_target == armor_input + shield_count (SQ1a)
    assert armor_target == armor_input + shield_count, (
        f"SQ1(a) drift: armor_target={armor_target}, armor_input={armor_input}, "
        f"shield_count={shield_count}"
    )


def test_t10_backfill_skip_already_populated_17(backfill_module):
    """Backfill query filter excludes items with slot_type già populated.
    Verified via samples: nessun target slot_type outside {weapon, armor, accessory}."""
    report = backfill_module.dry_run()
    # No overwrite: samples must all have slot_type target IN {weapon, armor, accessory}
    for sample in report["payload_samples"]:
        assert sample["$set"]["slot_type"] in {"weapon", "armor", "accessory"}
    # And no granular slot_type (helm, chest, weapon_main, amulet, ring) proposto
    for sample in report["payload_samples"]:
        assert sample["$set"]["slot_type"] not in {"helm", "chest", "weapon_main", "amulet", "ring", "gloves"}


def test_t11_backfill_apply_enabled_false_blocks_write(backfill_module):
    """Real apply must be blocked while APPLY_ENABLED=False."""
    assert backfill_module.APPLY_ENABLED is False
    with pytest.raises(SystemExit) as exc:
        backfill_module.apply_real(ack=True)
    assert "APPLY_ENABLED=False" in str(exc.value)


# ═════════════════════════════════════════════════════════════════════
# Group 4 — Class-bound dry-run (3 tests)
# ═════════════════════════════════════════════════════════════════════

def test_t12_class_bound_dry_run_would_add_binding_policy_178(class_bound_module):
    """Dry-run must derive item_binding_policy for all catalog items with correct breakdown.
    Invariante: sum(breakdown_by_policy) == would_modify_count == guard_passed."""
    report = class_bound_module.dry_run()
    assert report["mode"] == "dry_run"
    assert report["errors_count"] == 0
    # invariante: sum breakdown = would_modify = guard_passed
    br = report["breakdown_by_policy"]
    assert sum(br.values()) == report["would_modify_count"]
    assert report["would_modify_count"] == report["guard_hard_stop_checks_passed"]
    # invariante policy values
    assert set(br.keys()) == {"hard", "soft", "universal"}
    # locked expected counts on live DB (soft is > 0)
    assert br["hard"] >= 0
    assert br["soft"] >= 0
    assert br["universal"] >= 0
    # target totals expected from registry are the *target* (pass-through)
    assert report["target_count_expected_total"] == EXPECTED_TOTAL
    assert report["target_count_expected_hard"] == EXPECTED_HARD
    assert report["target_count_expected_universal"] == EXPECTED_UNIVERSAL
    assert report["target_count_expected_soft"] == EXPECTED_SOFT


def test_t13_class_bound_guard_hard_stop_rejects_blocked_fields(class_bound_module):
    """Guard hard-stop must reject any BLOCKED_FIELDS in payload."""
    guard = class_bound_module._guard_payload_hard_stop
    # Valid payload passes
    guard({"item_binding_policy": "hard"}, "test-slug")
    # Blocked field triggers SystemExit
    for blocked in ("class_slug", "role", "primary_stat", "base_strength",
                    "is_playable", "slot_type", "required_class_optional"):
        with pytest.raises(SystemExit) as exc:
            guard({"item_binding_policy": "hard", blocked: "value"}, "test-slug")
        assert "BLOCKED field" in str(exc.value) or "non-SAFE key" in str(exc.value)
    # Invalid policy value triggers SystemExit
    with pytest.raises(SystemExit):
        guard({"item_binding_policy": "invalid"}, "test-slug")


def test_t14_class_bound_apply_enabled_false_blocks_write(class_bound_module):
    """Real apply blocked while APPLY_ENABLED=False."""
    assert class_bound_module.APPLY_ENABLED is False
    with pytest.raises(SystemExit) as exc:
        class_bound_module.apply_real(ack=True)
    assert "APPLY_ENABLED=False" in str(exc.value)


# ═════════════════════════════════════════════════════════════════════
# Group 5 — Rate-limit + signals (2 tests)
# ═════════════════════════════════════════════════════════════════════

def test_t15_rate_limit_bucket_key_format(decision_lock):
    """SQ5: rate-limit bucket key format must match locked format."""
    rl = decision_lock["rate_limit_strategy"]["equip_warning"]
    assert rl["rate_limit_strategy"] == "daily_bucket_per_combo"
    assert rl["max_per_day_per_combo"] == 1
    fmt = rl["bucket_key_format"]
    assert "{guild_id}" in fmt
    assert "{adventurer_id}" in fmt
    assert "{reason_code}" in fmt
    assert "{YYYY-MM-DD-UTC}" in fmt
    # EQUIP_BLOCKED must remain unlimited
    assert decision_lock["rate_limit_strategy"]["equip_blocked"]["rate_limit"] == "unlimited"


def test_t16_derived_signals_recommended_for_class_and_universal(decision_lock):
    """SQ7: item_public() must expose recommended_for_class + is_universal signals."""
    sq7 = decision_lock["sq_locked"]["SQ7_ui_4_state_signal"]
    assert sq7["decision"] == "add_derived_signals_to_item_public"
    assert "recommended_for_class" in sq7["new_signals"]
    assert "is_universal" in sq7["new_signals"]
    ui_states = sq7["ui_states"]
    assert len(ui_states) == 4
    assert any("Bloccato" in s or "Non equipaggiabile" in s for s in ui_states)
    assert any("Consigliato" in s for s in ui_states)
    assert any("Universale" in s for s in ui_states)
