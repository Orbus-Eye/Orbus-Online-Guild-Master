"""FASE 1.3 (2026-08-08) — Auto-Equip: gate unico dei candidati.

Bug tester: l'Auto-Equip equipaggiava oggetti che la UI mostra come
"Bloccato". Causa: l'Auto-Equip filtrava solo con
`check_equip_compatibility` (R15/16) e NON consultava `derive_ui_4state`
(R18.4), che è la fonte del badge "Bloccato" player-facing. I due
validatori divergono in almeno due casi reali:

  * item con `item_binding_policy="hard"` ma SENZA `required_class_optional`
    e senza tag classe → UI: Bloccato (class_mismatch_hard);
    compatibility: "ok" (nessun tag da controllare).
  * item equipaggiabile senza `slot_type` → UI: Bloccato (slot_missing);
    compatibility: non guarda slot_type.

`candidate_gate` (pure function, no I/O) ora combina i due validatori.
Questi test NON richiedono Mongo.
"""
from app.equipment.auto_equip import candidate_gate


MAGO = {
    "id": "adv-mago", "name": "Elara", "level": 20,
    "class_slug": "mage", "class_name": "Mage",
}


def test_hard_policy_senza_tag_e_bloccato_dalla_ui():
    """Il caso principale del bug: compat dice ok, la UI dice Bloccato."""
    item = {
        "id": "it1", "item_type": "weapon", "slot_type": "weapon",
        "item_binding_policy": "hard",
        # nessun required_class_optional, nessun class_tags/recommended
    }
    allowed, reason = candidate_gate(MAGO, item)
    assert allowed is False
    assert reason == "ui4_blocked"


def test_item_equipaggiabile_senza_slot_type_e_bloccato():
    item = {
        "id": "it2", "item_type": "weapon",  # slot_type mancante
        "item_binding_policy": "soft",
        "class_tags": ["mage"],
    }
    allowed, reason = candidate_gate(MAGO, item)
    assert allowed is False
    assert reason == "ui4_blocked"


def test_item_raccomandato_passa_il_gate():
    item = {
        "id": "it3", "item_type": "weapon", "slot_type": "weapon",
        "item_binding_policy": "soft",
        "class_tags": ["mage"], "recommended_classes": ["mage"],
        "weapon_tags": ["staff"],
    }
    allowed, reason = candidate_gate(MAGO, item)
    assert allowed is True
    assert reason == "ok"


def test_armatura_pesante_su_mago_resta_block():
    item = {
        "id": "it4", "item_type": "armor", "slot_type": "armor",
        "item_binding_policy": "soft",
        "armor_tags": ["heavy"], "class_tags": ["mage"],
    }
    allowed, reason = candidate_gate(MAGO, item)
    assert allowed is False
    assert reason == "compat_block"


def test_warning_off_class_resta_escluso():
    """Decisione PM R16.5.4b REOPEN #2: i warning NON entrano nel pool."""
    item = {
        "id": "it5", "item_type": "weapon", "slot_type": "weapon",
        "item_binding_policy": "soft",
        "class_tags": ["warrior"], "recommended_classes": ["warrior"],
    }
    allowed, reason = candidate_gate(MAGO, item)
    assert allowed is False
    assert reason == "compat_warning"


def test_item_universale_passa():
    item = {
        "id": "it6", "item_type": "trinket", "slot_type": "trinket",
        "item_binding_policy": "universal", "is_universal": True,
    }
    allowed, reason = candidate_gate(MAGO, item)
    assert allowed is True
