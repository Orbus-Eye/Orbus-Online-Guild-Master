"""FASE 5 + 8C (2026-08-08) — Test puri: dungeon a stanze e bivi.

Blueprint (22 dungeon canonici), percorsi con fork, snapshot, splice,
salvage. Nessun Mongo richiesto (--noconftest).
"""
import random

from app.dungeons.rooms import (
    COMPLETION_XP_BONUS,
    ROOM_BLUEPRINTS,
    apply_salvage,
    build_rooms_snapshot,
    iter_paths,
    resolve_fork,
    rooms_mode_for_dungeon,
)
from app.shared.content_curve import DUNGEON_CURVE


def _dungeon(slug="goblin-warrens", duration=300, gold=100, xp=60,
             difficulty=1):
    return {
        "slug": slug, "base_duration_seconds": duration,
        "base_gold_reward": gold, "base_xp_reward": xp,
        "difficulty": difficulty,
    }


# ── Copertura FASE 8C: tutti i canonici tranne il tutorial ──────────────

def test_tutti_i_dungeon_canonici_hanno_blueprint():
    """22 dungeon a stanze; training-yard resta single-block (tutorial
    day-1 con la logica starter-fallback dedicata)."""
    expected = set(DUNGEON_CURVE) - {"training-yard"}
    assert set(ROOM_BLUEPRINTS) == expected
    assert len(ROOM_BLUEPRINTS) == 22


def test_rooms_mode_per_tutti_i_blueprint():
    for slug in ROOM_BLUEPRINTS:
        assert rooms_mode_for_dungeon(_dungeon(slug)) is True
    assert rooms_mode_for_dungeon(_dungeon("training-yard")) is False


def test_ogni_percorso_somma_a_uno_e_chiude_col_boss():
    """Economia: ogni percorso completo (una scelta per bivio) somma
    ≈1.0 di share e termina col boss del dungeon."""
    for slug in ROOM_BLUEPRINTS:
        paths = iter_paths(slug)
        assert paths, f"{slug}: nessun percorso"
        for path in paths:
            for key in ("duration_share", "gold_share", "xp_share"):
                total = sum(r[key] for r in path)
                assert 0.9 <= total <= 1.15, (
                    f"{slug}: percorso somma {key}={total:.2f}"
                )
            assert path[-1]["kind"] == "boss", f"{slug}: boss non finale"


def test_quantita_stanze_per_difficolta():
    """Guida del mandato: iniziali 2-4, intermedi 4-6, avanzati 6-8."""
    def path_len(slug):
        return max(len(p) for p in iter_paths(slug))
    assert 2 <= path_len("sewer-nest") <= 4
    assert 4 <= path_len("lich-sanctum") <= 6
    assert 5 <= path_len("obsidian-arena-5p") <= 8
    assert 6 <= path_len("world-tree-roots-5p") <= 9


def test_almeno_dieci_dungeon_con_bivi():
    forked = [
        slug for slug, bp in ROOM_BLUEPRINTS.items()
        if any(e.get("type") == "fork" for e in bp)
    ]
    assert len(forked) >= 10, f"solo {len(forked)} dungeon con bivi"


# ── Snapshot + fork ──────────────────────────────────────────────────────

def test_snapshot_materializza_stanze_e_bivi():
    snap = build_rooms_snapshot(_dungeon("goblin-warrens"), base_chance=60)
    kinds = [e.get("type") for e in snap]
    assert "fork" in kinds
    fork = next(e for e in snap if e["type"] == "fork")
    assert len(fork["options"]) == 2
    # Le stanze delle opzioni sono già materializzate con la chance
    # dell'opzione: via sicura (+5 ambient +5) vs rischiosa (−8).
    safe_room = fork["options"][0]["rooms"][0]
    risky_room = fork["options"][1]["rooms"][0]
    assert safe_room["chance"] > risky_room["chance"]


def test_resolve_fork_splice_e_reindicizza():
    snap = build_rooms_snapshot(_dungeon("goblin-warrens"), base_chance=60)
    fork_pos = next(i for i, e in enumerate(snap) if e["type"] == "fork")
    resolved = resolve_fork(snap, fork_pos, "sala-bottino")
    assert resolved is not None
    assert all(e.get("type") != "fork" or i != fork_pos
               for i, e in enumerate(resolved))
    # Reindicizzazione completa e boss sempre in coda.
    assert [e["idx"] for e in resolved] == list(range(len(resolved)))
    assert resolved[-1]["kind"] == "boss"


def test_resolve_fork_opzione_invalida():
    snap = build_rooms_snapshot(_dungeon("goblin-warrens"), base_chance=60)
    fork_pos = next(i for i, e in enumerate(snap) if e["type"] == "fork")
    assert resolve_fork(snap, fork_pos, "opzione-inesistente") is None
    assert resolve_fork(snap, 0, "cunicolo") is None  # non è un fork


def test_snapshot_chance_clampata():
    snap = build_rooms_snapshot(_dungeon("sewer-nest"), base_chance=8)
    for entry in snap:
        rooms = [entry] if entry["type"] == "room" else [
            r for o in entry["options"] for r in o["rooms"]
        ]
        assert all(r["chance"] >= 5 for r in rooms)


def test_fallback_generator_per_slug_non_autorato():
    snap = build_rooms_snapshot(
        _dungeon("dungeon-futuro", difficulty=3), base_chance=50,
    )
    assert len(snap) == 5
    assert snap[-1]["kind"] == "boss"


# ── Salvage (J.21, invariato) ────────────────────────────────────────────

def test_salvage_completamento_tutto_piu_bonus_xp():
    rng = random.Random(1)
    gold, items, xp = apply_salvage(100, ["a", "b", "c"], 60,
                                    "completed", rng=rng)
    assert gold == 100
    assert items == ["a", "b", "c"]
    assert xp == round(60 * (1 + COMPLETION_XP_BONUS))


def test_salvage_fuga_meta_oro_e_item_casuali():
    rng = random.Random(42)
    items_in = [f"i{n}" for n in range(200)]
    gold, items, xp = apply_salvage(100, items_in, 60, "escaped", rng=rng)
    assert gold == 50
    assert xp == 30
    assert 70 <= len(items) <= 130
    assert set(items) <= set(items_in)


def test_salvage_sconfitta_quarto_oro_40pct_xp():
    rng = random.Random(7)
    gold, items, xp = apply_salvage(100, [f"i{n}" for n in range(200)],
                                    60, "failed", rng=rng)
    assert gold == 25
    assert xp == 24
    assert len(items) < 100


def test_salvage_vuoto_non_esplode():
    rng = random.Random(3)
    assert apply_salvage(0, [], 0, "escaped", rng=rng) == (0, [], 0)
