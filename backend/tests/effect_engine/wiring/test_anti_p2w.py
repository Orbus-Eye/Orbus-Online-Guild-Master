"""RT2-B-2A · Test Anti-P2W + response contract invariance.

FS6: nessun bonus derivato dal transient state su gold/xp/rank/economy.
FS3: invarianza response contract Expedition legacy.
"""
from __future__ import annotations

import pytest

from app.stats.runtime.wiring.audit import (
    _ALLOWED_FIELDS,
    _FORBIDDEN_FIELDS,
    compute_evaluation_hash,
    emit_audit_event,
)


def test_audit_whitelist_blacklist_disjoint():
    """T-2A-17: whitelist e blacklist audit sono disgiunti."""
    intersect = _ALLOWED_FIELDS & _FORBIDDEN_FIELDS
    assert intersect == set(), f"Overlap tra whitelist/blacklist: {intersect}"


def test_audit_forbidden_fields_verbatim_B2Q05():
    """T-2A-18: blacklist B2Q05 verbatim (seed RNG, loadout, credenziali, mongo payload)."""
    required_forbidden = {"seed_rng", "loadout", "credentials", "mongo_payload"}
    assert required_forbidden.issubset(_FORBIDDEN_FIELDS)


def test_audit_allowed_fields_verbatim_B2Q05():
    """T-2A-19: whitelist B2Q05 verbatim (expedition_id, adventurer_id, state_version, ecc.)."""
    required_allowed = {
        "expedition_id", "adventurer_id", "current_power", "candidate_power",
        "delta", "soft_cap_applied", "state_version", "result_code", "duration_ms",
    }
    assert required_allowed.issubset(_ALLOWED_FIELDS)


def test_audit_forbidden_field_drops_record(caplog):
    """T-2A-20: presenza di campo blacklist → record NON emesso."""
    caplog.set_level("ERROR")
    emitted = emit_audit_event("runtime_state_created", {
        "expedition_id": "exp-001",
        "seed_rng": "leaked_seed_value",  # FORBIDDEN
    })
    assert emitted is False
    assert any("audit_forbidden_field" in r.message for r in caplog.records)


def test_audit_whitelist_only_emission(caplog):
    """T-2A-21: solo campi whitelist finiscono nell'audit line."""
    caplog.set_level("INFO")
    emitted = emit_audit_event("runtime_state_created", {
        "expedition_id": "exp-001",
        "state_version": 1,
        "result_code": "SUCCESS",
        "unknown_field_ignored": "should be dropped",  # non in whitelist né blacklist → dropped
    })
    assert emitted is True
    audit_lines = [r.getMessage() for r in caplog.records if "audit_event" in r.getMessage()]
    assert audit_lines, "audit_event non emesso"
    line = audit_lines[-1]
    assert "unknown_field_ignored" not in line
    assert "exp-001" in line


def test_evaluation_hash_deterministic():
    """T-2A-22: evaluation_hash è deterministico per stesso payload."""
    payload = {
        "expedition_id": "exp-hash-001",
        "current_power": 100,
        "candidate_power": 105,
        "delta": 5,
    }
    h1 = compute_evaluation_hash(payload)
    h2 = compute_evaluation_hash(payload)
    assert h1 == h2
    assert len(h1) == 64


def test_evaluation_hash_stable_across_key_order():
    """T-2A-23: evaluation_hash invariant rispetto all'ordine dei campi."""
    p1 = {"expedition_id": "exp-hash-001", "delta": 5, "current_power": 100}
    p2 = {"current_power": 100, "expedition_id": "exp-hash-001", "delta": 5}
    assert compute_evaluation_hash(p1) == compute_evaluation_hash(p2)


def test_evaluation_hash_ignores_forbidden_fields():
    """T-2A-24: campi non-whitelist esclusi dal hash (garantisce no PII leakage)."""
    p1 = {"expedition_id": "exp-001", "current_power": 100}
    p2 = {"expedition_id": "exp-001", "current_power": 100, "seed_rng": "SECRET"}
    # Il campo forbidden è filtrato via `_ALLOWED_FIELDS` — hash identico.
    assert compute_evaluation_hash(p1) == compute_evaluation_hash(p2)


def test_anti_p2w_no_gameplay_field_in_audit_whitelist():
    """T-2A-25: FS6 · nessun campo gameplay-affecting (gold/xp/rank/loot) nella whitelist."""
    gameplay_forbidden = {"gold", "xp", "rank", "loot", "reward", "prestige"}
    intersection = _ALLOWED_FIELDS & gameplay_forbidden
    assert intersection == set(), (
        f"Anti-P2W violation: gameplay fields in whitelist: {intersection}"
    )


def test_expedition_public_contract_unchanged():
    """T-2A-26: FS3 · `expedition_public()` shape invariante rispetto al legacy."""
    from app.expeditions.services import expedition_public
    now = "2026-02-01T00:00:00+00:00"
    exp_doc = {
        "id": "exp-legacy-001",
        "guild_id": "guild-001",
        "dungeon_id": "dungeon-001",
        "dungeon_name": "Test Dungeon",
        "status": "completed",
        "started_at": now,
        "completes_at": now,
        "completed_at": now,
        "team_power": 100,
        "success_chance": 75,
        "created_at": now,
        "updated_at": now,
    }
    out = expedition_public(exp_doc)
    # Contract invariante: nessun campo runtime_state_* / shadow_* nel payload player.
    for key in out.keys():
        assert not key.startswith("runtime_state_")
        assert not key.startswith("shadow_")
        assert not key.startswith("class_state_")
    # Presenza campi legacy (regression sentinel)
    for legacy_key in ("id", "guild_id", "dungeon_id", "status", "team_power",
                       "success_chance", "gold_reward", "xp_reward"):
        assert legacy_key in out, f"campo legacy mancante: {legacy_key}"
