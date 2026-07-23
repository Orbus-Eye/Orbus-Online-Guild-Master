"""RT2-A · test_performance.py

Benchmark performance con acceptance criteria P0Q07 (relative-baseline):
- functional stat calculation p95 overhead ≤ max(5% baseline, 1 ms)
- shadow evaluation p95 overhead ≤ max(10% baseline, 2 ms)
- memory growth per evaluated adventurer = bounded
- unbounded cache growth = 0
- database query increase = 0
- network call increase = 0

Baseline measurement: usiamo la formula legacy attuale
(`app.expeditions.formulas.adventurer_effective_power`) come reference.

NOTA: se la baseline non è riproducibile nell'ambiente CI (varianza alta),
i test emettono warning + xfail deterministico. Il chat report finale
dichiarerà `PERFORMANCE_BASELINE_MISSING` solo se lo stesso ambiente + stesso
fixture set produce varianza > 50% fra 2 run consecutivi.
"""
from __future__ import annotations

import gc
import statistics
import time
import tracemalloc

import pytest

from app.expeditions.formulas import adventurer_effective_power
from app.stats.runtime import feature_flags as ff
from app.stats.runtime.modifier_order import derived_base_power, evaluate_runtime_stats
from app.stats.runtime.shadow_comparison import compare_shadow


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for f in ff.ALL_FLAGS:
        monkeypatch.delenv(f"ORBUS_FLAG_{f.upper()}", raising=False)
    ff.reset_cache()
    yield
    ff.reset_cache()


def _sample_adventurers(n=20):
    """Genera fixture avventurieri riproducibili (deterministic seed via index)."""
    out = []
    for i in range(n):
        out.append({
            "id": f"adv-{i:04d}",
            "level": (i % 20) + 1,
            "strength": 20 + (i * 3) % 80,
            "agility": 10 + (i * 5) % 50,
            "intellect": 30 + (i * 7) % 120,  # some >100 per soft-cap coverage
            "endurance": 15 + (i * 2) % 40,
            "faith": 5 + (i * 4) % 25,
            # No trait modifiers per baseline pulita
            "traits": [],
            "specialization": None,
        })
    return out


def _measure_p95_ns(fn, iterations: int = 500) -> tuple[int, int, int]:
    """Ritorna (p50_ns, p95_ns, p99_ns) su iterations chiamate di fn (zero-arg)."""
    gc.collect()
    samples = []
    # Warm-up
    for _ in range(50):
        fn()
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns() - t0)
    samples.sort()
    p50 = samples[len(samples) // 2]
    p95 = samples[int(len(samples) * 0.95)]
    p99 = samples[int(len(samples) * 0.99)]
    return p50, p95, p99


def test_functional_overhead_within_criteria():
    """RT2-A functional stat calculation p95 overhead ≤ max(5% baseline, 1 ms)."""
    advs = _sample_adventurers(20)
    idx = [0]

    def legacy_call():
        adv = advs[idx[0] % len(advs)]
        idx[0] += 1
        adventurer_effective_power(adv)

    def rt2a_call():
        adv = advs[idx[0] % len(advs)]
        idx[0] += 1
        base = {
            "strength": adv["strength"], "agility": adv["agility"],
            "intellect": adv["intellect"], "endurance": adv["endurance"],
            "faith": adv["faith"],
        }
        r = evaluate_runtime_stats(base_stats=base)
        derived_base_power(r, level=adv["level"])

    _, baseline_p95_ns, _ = _measure_p95_ns(legacy_call, iterations=500)
    _, rt2a_p95_ns, _ = _measure_p95_ns(rt2a_call, iterations=500)

    overhead_ns = rt2a_p95_ns - baseline_p95_ns
    threshold_ns = max(baseline_p95_ns * 5 // 100, 1_000_000)  # 5% baseline OR 1 ms

    # Stash for report; il test è tollerante entro criterion P0Q07
    print(
        f"[perf] baseline_p95={baseline_p95_ns}ns rt2a_p95={rt2a_p95_ns}ns "
        f"overhead={overhead_ns}ns threshold={threshold_ns}ns"
    )
    assert overhead_ns <= threshold_ns, (
        f"functional overhead p95 {overhead_ns}ns exceeds threshold {threshold_ns}ns "
        f"(baseline p95={baseline_p95_ns}ns)"
    )


def test_shadow_overhead_within_criteria(monkeypatch):
    """RT2-A shadow evaluation p95 overhead ≤ max(10% baseline, 2 ms)."""
    monkeypatch.setenv("ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED", "true")
    ff.reset_cache()
    advs = _sample_adventurers(20)
    idx = [0]

    def legacy_call():
        adv = advs[idx[0] % len(advs)]
        idx[0] += 1
        adventurer_effective_power(adv)

    def shadow_call():
        adv = advs[idx[0] % len(advs)]
        idx[0] += 1
        base = {k: adv[k] for k in ("strength", "agility", "intellect", "endurance", "faith")}
        # Baseline: legacy path + shadow overlay
        adventurer_effective_power(adv)
        compare_shadow(
            expedition_id=f"e-{idx[0]}", adventurer_id=adv["id"],
            current_base_power=100, base_stats=base, level=adv["level"],
        )

    _, baseline_p95_ns, _ = _measure_p95_ns(legacy_call, iterations=500)
    _, shadow_p95_ns, _ = _measure_p95_ns(shadow_call, iterations=500)

    overhead_ns = shadow_p95_ns - baseline_p95_ns
    threshold_ns = max(baseline_p95_ns * 10 // 100, 2_000_000)  # 10% baseline OR 2 ms
    print(
        f"[perf-shadow] baseline_p95={baseline_p95_ns}ns shadow_p95={shadow_p95_ns}ns "
        f"overhead={overhead_ns}ns threshold={threshold_ns}ns"
    )
    assert overhead_ns <= threshold_ns, (
        f"shadow overhead p95 {overhead_ns}ns exceeds threshold {threshold_ns}ns "
        f"(baseline p95={baseline_p95_ns}ns)"
    )


def test_memory_growth_bounded():
    """Memory per evaluated adventurer = bounded (no leak, no unbounded cache growth)."""
    advs = _sample_adventurers(50)
    gc.collect()
    tracemalloc.start()
    snap_pre = tracemalloc.take_snapshot()
    # 200 iterazioni di full evaluation
    for _ in range(200):
        for adv in advs:
            base = {k: adv[k] for k in ("strength", "agility", "intellect", "endurance", "faith")}
            r = evaluate_runtime_stats(base_stats=base)
            derived_base_power(r, level=adv["level"])
    gc.collect()
    snap_post = tracemalloc.take_snapshot()
    tracemalloc.stop()
    stats = snap_post.compare_to(snap_pre, "filename")
    total_growth_bytes = sum(s.size_diff for s in stats if s.size_diff > 0)
    # Bound assertion: dopo 200 * 50 = 10k evaluations, la crescita dev'essere
    # sostanzialmente costante (no cache unbounded). Threshold conservativo: 5 MB.
    assert total_growth_bytes < 5_000_000, (
        f"unbounded memory growth detected: {total_growth_bytes} bytes"
    )


def test_zero_db_query_increase():
    """RT2-A NON deve introdurre chiamate DB. Verifica statica basata su AST."""
    import ast
    from app.stats.runtime import (
        equipment_aggregation, feature_flags, loadout_snapshot,
        modifier_order, shadow_comparison, soft_caps, stat_bridge, models, events,
    )
    forbidden_import_prefixes = ("motor", "pymongo", "beanie", "odmantic")
    forbidden_attr_calls = {"find_one", "insert_one", "update_one", "delete_one",
                            "insert_many", "update_many", "delete_many", "find_one_and_update",
                            "aggregate", "count_documents"}
    for mod in (equipment_aggregation, feature_flags, loadout_snapshot,
                modifier_order, shadow_comparison, soft_caps, stat_bridge, models, events):
        with open(mod.__file__, "rb") as f:
            tree = ast.parse(f.read().decode())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for pref in forbidden_import_prefixes:
                        assert not alias.name.startswith(pref), (
                            f"{mod.__name__} imports forbidden module {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                for pref in forbidden_import_prefixes:
                    assert not (node.module or "").startswith(pref), (
                        f"{mod.__name__} imports from forbidden module {node.module}"
                    )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_attr_calls:
                    raise AssertionError(
                        f"{mod.__name__} contains forbidden DB call: .{node.func.attr}(...)"
                    )


def test_zero_network_call_increase():
    """RT2-A NON deve introdurre chiamate rete. Verifica statica basata su AST."""
    import ast
    from app.stats.runtime import (
        equipment_aggregation, feature_flags, loadout_snapshot,
        modifier_order, shadow_comparison, soft_caps, stat_bridge, models, events,
    )
    forbidden_import_prefixes = ("requests", "httpx", "aiohttp", "urllib3", "socket")
    for mod in (equipment_aggregation, feature_flags, loadout_snapshot,
                modifier_order, shadow_comparison, soft_caps, stat_bridge, models, events):
        with open(mod.__file__, "rb") as f:
            tree = ast.parse(f.read().decode())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for pref in forbidden_import_prefixes:
                        assert not alias.name.startswith(pref), (
                            f"{mod.__name__} imports forbidden network module {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                for pref in forbidden_import_prefixes:
                    assert not (node.module or "").startswith(pref), (
                        f"{mod.__name__} imports from forbidden network module {node.module}"
                    )
