"""FASE 5 (2026-08-08) — Test puri: dungeon a stanze.

Blueprint, snapshot, salvage. Nessun Mongo richiesto (--noconftest).
Design: memory/fase5_design_dungeon_stanze.md
"""
import random

from app.dungeons.rooms import (
    COMPLETION_XP_BONUS,
    ROOM_BLUEPRINTS,
    ROOMS_PILOT_SLUGS,
    apply_salvage,
    build_rooms_snapshot,
    rooms_mode_for_dungeon,
)


def _dungeon(slug="goblin-warrens", duration=300, gold=100, xp=60,
             difficulty=1):
    return {
        "slug": slug, "base_duration_seconds": duration,
        "base_gold_reward": gold, "base_xp_reward": xp,
        "difficulty": difficulty,
    }


# ── Blueprint autorati ───────────────────────────────────────────────────

def test_piloti_hanno_blueprint_autorato():
    for slug in ROOMS_PILOT_SLUGS:
        assert slug in ROOM_BLUEPRINTS, f"pilota senza blueprint: {slug}"


def test_share_sommano_a_uno_e_boss_finale():
    for slug, rooms in ROOM_BLUEPRINTS.items():
        for key in ("duration_share", "gold_share", "xp_share"):
            total = sum(r[key] for r in rooms)
            assert abs(total - 1.0) < 0.01, f"{slug}.{key} somma {total}"
        assert rooms[-1]["kind"] == "boss", f"{slug}: il boss deve chiudere"
        assert rooms[-1]["has_loot"] is True


def test_rooms_mode_solo_per_i_piloti():
    assert rooms_mode_for_dungeon(_dungeon("goblin-warrens")) is True
    assert rooms_mode_for_dungeon(_dungeon("sewer-nest")) is True
    assert rooms_mode_for_dungeon(_dungeon("training-yard")) is False
    assert rooms_mode_for_dungeon(_dungeon("lich-sanctum")) is False


# ── Snapshot ─────────────────────────────────────────────────────────────

def test_snapshot_congela_durate_ricompense_e_chance():
    snap = build_rooms_snapshot(_dungeon(), base_chance=60)
    assert len(snap) == 4  # goblin-warrens: 4 stanze autorate
    assert sum(r["gold"] for r in snap) in range(98, 103)  # ≈ base_gold
    assert sum(r["xp"] for r in snap) in range(58, 63)
    assert sum(r["duration_seconds"] for r in snap) in range(295, 306)
    # Boss: -10 sulla chance; treasure/ambient +5.
    by_kind = {r["kind"]: r for r in snap}
    assert by_kind["boss"]["chance"] == 50
    assert by_kind["treasure"]["chance"] == 65
    assert by_kind["guard"]["chance"] == 60


def test_snapshot_chance_clampata():
    snap_low = build_rooms_snapshot(_dungeon(), base_chance=8)
    assert all(r["chance"] >= 5 for r in snap_low)
    snap_high = build_rooms_snapshot(_dungeon(), base_chance=100)
    assert all(r["chance"] <= 100 for r in snap_high)


def test_fallback_generator_per_slug_non_autorato():
    snap = build_rooms_snapshot(
        _dungeon("dungeon-futuro", difficulty=3), base_chance=50,
    )
    assert len(snap) == 5  # difficoltà 3 → 5 stanze
    assert snap[-1]["kind"] == "boss"
    assert abs(sum(r["gold"] for r in snap) - 100) <= 2


# ── Salvage (J.21) ───────────────────────────────────────────────────────

def test_salvage_completamento_tutto_piu_bonus_xp():
    rng = random.Random(1)
    gold, items, xp = apply_salvage(100, ["a", "b", "c"], 60,
                                    "completed", rng=rng)
    assert gold == 100
    assert items == ["a", "b", "c"]
    assert xp == round(60 * (1 + COMPLETION_XP_BONUS))  # 75


def test_salvage_fuga_meta_oro_e_item_casuali():
    rng = random.Random(42)
    items_in = [f"i{n}" for n in range(200)]
    gold, items, xp = apply_salvage(100, items_in, 60, "escaped", rng=rng)
    assert gold == 50
    assert xp == 30
    # Selezione casuale ~50%: con 200 item resta tra il 35% e il 65%.
    assert 70 <= len(items) <= 130
    assert set(items) <= set(items_in)


def test_salvage_sconfitta_quarto_oro_40pct_xp():
    rng = random.Random(7)
    gold, items, xp = apply_salvage(100, [f"i{n}" for n in range(200)],
                                    60, "failed", rng=rng)
    assert gold == 25
    assert xp == 24
    assert len(items) < 100  # ~25%


def test_salvage_vuoto_non_esplode():
    rng = random.Random(3)
    assert apply_salvage(0, [], 0, "escaped", rng=rng) == (0, [], 0)
