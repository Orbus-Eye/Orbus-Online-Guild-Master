"""FASE 8D (2026-08-08) — Test puri: raid a fasi (pilota Lunacaduta).

Nessun Mongo richiesto (--noconftest).
"""
from app.raids.phases import (
    CHECKPOINT_OPTIONS,
    PHASE_BLUEPRINTS,
    RAID_PHASES_SLUGS,
    build_phases_snapshot,
    checkpoint_index,
    checkpoint_option,
    phases_mode_for_raid,
    resolve_phase,
)


def _rd(slug="moonfall-vigil", duration=3600):
    return {"slug": slug, "base_duration_seconds": duration}


def test_pilota_ha_blueprint_completo():
    for slug in RAID_PHASES_SLUGS:
        phases = PHASE_BLUEPRINTS[slug]
        kinds = [p["kind"] for p in phases]
        # Struttura richiesta: sezioni, boss intermedio, checkpoint,
        # evento, boss finale.
        assert "miniboss" in kinds
        assert "checkpoint" in kinds
        assert "event" in kinds
        assert kinds[-1] == "boss"
        assert len(phases) >= 5
        total = sum(p["duration_share"] for p in phases)
        assert 0.95 <= total <= 1.05


def test_phases_mode_solo_per_il_pilota():
    assert phases_mode_for_raid(_rd("moonfall-vigil")) is True
    assert phases_mode_for_raid(_rd("dragon-vault")) is False


def test_snapshot_durate_e_chance():
    snap = build_phases_snapshot(_rd(), base_combined_chance=60)
    assert len(snap) == 5
    assert sum(p["duration_seconds"] for p in snap) in range(3400, 3800)
    by_kind = {p["kind"]: p for p in snap}
    assert by_kind["boss"]["chance"] == 50       # -10
    assert by_kind["approach"]["chance"] == 65   # +5
    assert by_kind["miniboss"]["chance"] == 55   # -5


def test_checkpoint_index():
    snap = build_phases_snapshot(_rd(), base_combined_chance=60)
    cp = checkpoint_index(snap)
    assert snap[cp]["kind"] == "checkpoint"
    # Il checkpoint è nel mezzo: prima c'è il miniboss, dopo il boss.
    assert 0 < cp < len(snap) - 1


def test_resolve_phase_deterministico():
    snap = build_phases_snapshot(_rd(), base_combined_chance=60)
    a = resolve_phase(snap[1], "raid-123")
    b = resolve_phase(snap[1], "raid-123")
    assert a == b                       # replay-safe
    c = resolve_phase(snap[1], "raid-456")
    assert a["roll"] != c["roll"] or a == c  # seed diverso → roll diverso (quasi sempre)


def test_checkpoint_sempre_superato():
    snap = build_phases_snapshot(_rd(), base_combined_chance=60)
    cp = checkpoint_index(snap)
    result = resolve_phase(snap[cp], "raid-qualunque")
    assert result["success"] is True
    assert result["kind"] == "checkpoint"


def test_bonus_modifier_applicato():
    snap = build_phases_snapshot(_rd(), base_combined_chance=60)
    boss = snap[-1]
    base = resolve_phase(boss, "raid-x", 0)
    ritual = resolve_phase(boss, "raid-x", +5)
    assert ritual["chance"] == base["chance"] + 5
    assert ritual["roll"] == base["roll"]  # stesso seed, stessa fase


def test_opzioni_checkpoint():
    assert checkpoint_option("rituale")["chance_modifier"] == 5
    assalto = checkpoint_option("assalto")
    assert assalto["chance_modifier"] == -8
    assert assalto["gold_factor"] == 1.25
    assert checkpoint_option("inesistente") is None
    # La PRIMA opzione è quella prudente (auto-scelta alla deadline).
    assert CHECKPOINT_OPTIONS[0]["key"] == "rituale"
