"""FASE 8A (2026-08-08) — Test di ACCETTAZIONE del rebalance difficoltà.

Il test di regressione principale della tranche: una squadra ~Lv15 non
deve poter farmare dungeon consigliati Lv40. Tutto derivato dal modello
formale `app/shared/power_model.py` e dalla curva reale.
Nessun Mongo richiesto (--noconftest).
"""
from app.expeditions.formulas import compute_success_chance
from app.expeditions.power_gate import required_team_power_for
from app.shared.content_curve import DUNGEON_CURVE, RAID_CURVE
from app.shared.power_model import (
    recommended_power_for,
    team_power,
)


def _gate(rec: int) -> int:
    return required_team_power_for({"recommended_power": rec})


REC40 = DUNGEON_CURVE["obsidian-arena-5p"].recommended_power  # dungeon Lv40


# ── IL test di regressione principale (mandato Fase 8) ───────────────────

def test_lv15_non_farma_dungeon_lv40():
    """Squadra Lv15 vs dungeon Lv40: SOTTO IL GATE per tutte le fasce,
    inclusa 'molto_forte' (10 slot di item Rare)."""
    gate = _gate(REC40)
    for tier in ("sottopotenziata", "media", "ben_equipaggiata",
                 "molto_forte"):
        squad = team_power(15, 5, tier)
        assert squad < gate, (
            f"Lv15 {tier} (team {squad}) supera il gate {gate} "
            f"del dungeon Lv40 (rec {REC40})"
        )


def test_acceptance_progressione_lv15():
    """Le fasce d'accesso richieste dal mandato per una squadra Lv15
    NORMALMENTE equipaggiata (fascia media)."""
    squad = team_power(15, 5, "media")
    # Lv10–15 → affrontabile normalmente (≥ 50%).
    for lv in (10, 15):
        rec = DUNGEON_CURVE[
            {10: "druid-grove", 15: "cursed-mines"}[lv]
        ].recommended_power
        assert squad >= _gate(rec)
        assert compute_success_chance(squad, rec) >= 45
    # Lv20 → possibile ma impegnativo (sopra gate, chance bassa).
    rec20 = DUNGEON_CURVE["lich-sanctum"].recommended_power
    assert squad >= _gate(rec20)
    assert 10 <= compute_success_chance(squad, rec20) <= 40
    # Lv25–30 → fuori portata (sotto gate).
    for slug in ("storm-spire", "silent-monastery-5p"):
        rec = DUNGEON_CURVE[slug].recommended_power
        assert squad < _gate(rec)


def test_parita_50_percento_su_tutta_la_curva():
    """Diagonale: squadra media di pari livello ≈ 50% ovunque."""
    for lv in (10, 15, 20, 30, 40, 50, 60, 70, 80):
        rec = recommended_power_for(lv, 5)
        squad = team_power(lv, 5, "media")
        chance = compute_success_chance(squad, rec)
        assert 45 <= chance <= 55, f"Lv{lv}: parità = {chance}%"


def test_ben_equipaggiata_75_90():
    """Ben equipaggiata a pari livello → fascia alta (dove la rarità
    la distingue dalla media; ai livelli di convergenza epic il valore
    ricade sulla parità, artefatto documentato)."""
    for lv in (10, 20, 30, 50):
        rec = recommended_power_for(lv, 5)
        squad = team_power(lv, 5, "ben_equipaggiata")
        chance = compute_success_chance(squad, rec)
        assert chance >= 70, f"Lv{lv}: ben equipaggiata = {chance}%"


def test_endgame_farma_overpower_su_contenuti_vecchi():
    """Il farm dei reagenti bassi resta: Lv80 su contenuto Lv≤30 va
    dritto a rating ≥200 → chance 100 + Overpower ×3."""
    from app.expeditions.formulas import overpower_loot_multiplier, power_rating
    squad = team_power(80, 5, "media")
    for slug in ("goblin-warrens", "druid-grove", "lich-sanctum",
                 "silent-monastery-5p"):
        rec = DUNGEON_CURVE[slug].recommended_power
        rating = power_rating(squad, rec)
        assert rating >= 200
        assert compute_success_chance(squad, rec) == 100
        assert overpower_loot_multiplier(rating) == 3.0


def test_vincolo_difficolta_effettiva_50_percento():
    """Vincolo minimo del mandato: difficoltà effettiva +50%.

    Misura: il GATE d'ingresso di ogni dungeon cresce almeno ×1.5
    rispetto al vecchio (0.60 × curva pre-rebalance)."""
    old = {
        "training-yard": 15, "sewer-nest": 35, "goblin-warrens": 117,
        "bandit-hideout": 75, "druid-grove": 267, "shadow-crypts": 283,
        "cursed-mines": 333, "sunken-library": 215, "lich-sanctum": 408,
        "dragons-hoard": 642, "storm-spire": 483, "wolf-den-5p": 260,
        "frost-cave-5p": 310, "salt-marsh-5p": 360,
        "iron-foundry-5p": 410, "silent-monastery-5p": 460,
        "pirate-fleet-5p": 510, "obsidian-arena-5p": 560,
        "clockwork-vault-5p": 610, "voidspire-5p": 660,
        "infernal-pit-5p": 760, "celestial-citadel-5p": 810,
        "world-tree-roots-5p": 1600,
    }
    for slug, old_rec in old.items():
        old_gate = 0.60 * old_rec
        new_gate = _gate(DUNGEON_CURVE[slug].recommended_power)
        ratio = new_gate / old_gate
        assert ratio >= 1.5, f"{slug}: gate ×{ratio:.2f} (< 1.5)"


def test_curva_raid_piu_severa_del_pari_livello():
    """FASE 8B — i raid costano più del contenuto dungeon pari livello
    (a parità di potere per membro: severità ×1.15)."""
    for slug, curve in RAID_CURVE.items():
        size = {"moonfall-vigil": 10, "broken-bastion-siege": 15,
                "necropolis-bells": 20, "dragon-vault": 40}[slug]
        per_member_raid = curve.recommended_power / size
        per_member_dungeon = recommended_power_for(
            curve.required_level, 5) / 5
        assert per_member_raid > per_member_dungeon
