"""FASE 8B (2026-08-08) — Test puri: PWR gate dei raid.

I raid seguono la filosofia dei dungeon (accesso = potere, livello
informativo) ma con soglia più severa (75% su curva già ×1.15).
Nessun Mongo richiesto (--noconftest).
"""
import pytest
from fastapi import HTTPException

from app.raids.power_gate import (
    RAID_POWER_GATE_RATIO,
    enforce_raid_min_power,
    raid_recommended_power,
    raid_required_team_power,
)
from app.shared.content_curve import RAID_CURVE
from app.shared.power_model import team_power


def test_soglia_75_percento():
    assert RAID_POWER_GATE_RATIO == 0.75
    rd = {"slug": "moonfall-vigil"}
    rec = RAID_CURVE["moonfall-vigil"].recommended_power
    assert raid_recommended_power(rd) == rec
    assert raid_required_team_power(rd) == -(-rec * 3 // 4)  # ceil 75%


def test_curva_canonica_vince_sul_doc():
    """RAID_CURVE è la source of truth anche se il doc DB è vecchio."""
    rd = {"slug": "dragon-vault", "recommended_power_combined": 8000}
    assert raid_recommended_power(rd) == 24100


def test_fallback_doc_per_raid_non_in_curva():
    rd = {"slug": "raid-futuro", "recommended_power_combined": 5000}
    assert raid_recommended_power(rd) == 5000
    assert raid_required_team_power(rd) == 3750


def test_gate_blocca_sotto_soglia():
    rd = {"slug": "moonfall-vigil"}
    required = raid_required_team_power(rd)
    with pytest.raises(HTTPException) as exc:
        enforce_raid_min_power(required - 1, rd, source="raid.start")
    detail = exc.value.detail
    assert exc.value.status_code == 423
    assert detail["code"] == "raid.power_too_low"
    assert detail["required_team_power"] == required
    assert "user_message" in detail


def test_gate_passa_alla_soglia():
    rd = {"slug": "moonfall-vigil"}
    enforce_raid_min_power(
        raid_required_team_power(rd), rd, source="raid.preview",
    )


def test_roster_lv15_non_entra_nel_raid_lv40():
    """Coerenza col rebalance: 10 avventurieri Lv15 medi non entrano
    nella Veglia di Lunacaduta (Lv40)."""
    combined = 2 * team_power(15, 5, "media")  # 2 party da 5 medi
    rd = {"slug": "moonfall-vigil"}
    with pytest.raises(HTTPException):
        enforce_raid_min_power(combined, rd, source="raid.start")


def test_roster_pari_livello_entra():
    """10 avventurieri Lv40 medi superano il gate del raid Lv40
    (poi la severità ×1.15 morde sulla chance, non sull'accesso)."""
    combined = 2 * team_power(40, 5, "media")
    rd = {"slug": "moonfall-vigil"}
    enforce_raid_min_power(combined, rd, source="raid.start")
