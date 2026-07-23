"""RT2-A · test_property.py

Property-based tests eseguiti come loop deterministici densi (no hypothesis
dependency introdotta). Verifica:
- monotonicity: x2 >= x1 → effective(x2) >= effective(x1)
- non-negative output: nominal e effective >= 0
- deterministic output: pure function
- disabled-flag equivalence: flags OFF → risultati byte-equivalenti a legacy path
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.stats.runtime import feature_flags as ff
from app.stats.runtime.modifier_order import evaluate_runtime_stats
from app.stats.runtime.shadow_comparison import compare_shadow
from app.stats.runtime.soft_caps import effective_intelligence


# ─── Property 1: Monotonicity ──────────────────────────────────────────
def test_effective_intelligence_monotonic():
    """x2 >= x1 → effective(x2) >= effective(x1) su ampio range."""
    prev_val = Decimal(-1)
    for x in range(0, 2000):
        cur = effective_intelligence(x)
        assert cur >= prev_val, f"monotonicity failed at x={x}: {cur} < {prev_val}"
        prev_val = cur


# ─── Property 2: Non-negative output ───────────────────────────────────
def test_effective_intelligence_non_negative():
    for x in range(-100, 1000):
        assert effective_intelligence(x) >= Decimal(0)


def test_evaluate_runtime_stats_non_negative():
    """Su ampio range di input inclusi negativi via perm modifier: output sempre >= 0."""
    from app.stats.runtime.stat_bridge import RUNTIME_STATS
    samples = [
        {"strength": 100, "intellect": 200},
        {"strength": 5, "intellect": 50},
        {"strength": 0, "intellect": 0},
        {"strength": 1, "intellect": 1000},
    ]
    perm_variants = [
        None,
        {"strength": -50},
        {"strength": -1000},  # crea nominal negativo → clamp 0
    ]
    for base in samples:
        for perm in perm_variants:
            r = evaluate_runtime_stats(base_stats=base, permanent_modifiers=perm)
            for s in RUNTIME_STATS:
                assert r.nominal_stats[s] >= 0
                assert r.effective_stats[s] >= Decimal(0)


# ─── Property 3: Deterministic output ──────────────────────────────────
def test_soft_cap_deterministic():
    """Stessa input → stessa output su 500 iterazioni."""
    for x in [0, 50, 100, 101, 150, 200, 500, 1000]:
        results = [effective_intelligence(x) for _ in range(500)]
        assert all(r == results[0] for r in results)


def test_evaluate_deterministic():
    base = {"strength": 100, "intellect": 150}
    items = [{"strength_bonus": 20, "intellect_bonus": 30}]
    pct = {"strength": 10}
    results = []
    for _ in range(200):
        r = evaluate_runtime_stats(
            base_stats=base, equipment_items=items, percent_modifiers=pct,
        )
        # confronto solo campi deterministic (esclude evaluation_duration_ns)
        results.append((r.nominal_stats, r.effective_stats, r.soft_cap_applied))
    assert all(x == results[0] for x in results)


# ─── Property 4: Disabled-flag equivalence ─────────────────────────────
@pytest.fixture
def clean_flags(monkeypatch):
    for f in ff.ALL_FLAGS:
        monkeypatch.delenv(f"ORBUS_FLAG_{f.upper()}", raising=False)
    ff.reset_cache()
    yield
    ff.reset_cache()


def test_flags_off_shadow_returns_none(clean_flags):
    """Entrambi i flag OFF → compare_shadow ritorna None (nessun percorso RT2-A)."""
    assert not ff.is_enabled("runtime_stat_soft_cap_enabled")
    assert not ff.is_enabled("runtime_stat_shadow_enabled")
    result = compare_shadow(
        expedition_id="e1",
        adventurer_id="a1",
        current_base_power=100,
        base_stats={"strength": 50},
    )
    assert result is None  # nessuna diagnostica emessa


def test_flags_off_no_side_effect_on_input(clean_flags):
    """Flags OFF → chiamare shadow non modifica input né emette record."""
    base = {"strength": 100, "intellect": 200}
    base_copy = dict(base)
    compare_shadow(
        expedition_id="e1", adventurer_id="a1",
        current_base_power=999, base_stats=base,
    )
    assert base == base_copy


def test_pure_function_same_args_same_result(clean_flags, monkeypatch):
    """evaluate_runtime_stats è pure: no dipendenza da env, no hidden state."""
    base = {"intellect": 100}
    monkeypatch.setenv("APP_ENV", "development")
    r1 = evaluate_runtime_stats(base_stats=base)
    monkeypatch.setenv("APP_ENV", "production")
    r2 = evaluate_runtime_stats(base_stats=base)
    assert r1.nominal_stats == r2.nominal_stats
    assert r1.effective_stats == r2.effective_stats
    assert r1.soft_cap_applied == r2.soft_cap_applied
