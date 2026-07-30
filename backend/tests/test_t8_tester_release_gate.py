from copy import deepcopy

from app.admin.tester_release import (
    T8_CHECKLIST_KEYS,
    audit_t8_runtime_catalog,
    normalized_t8_checklist,
)
from app.items.final_catalog import FINAL_ITEM_CATALOG


def test_t8_final_catalog_passes_release_economy_and_identity_gates():
    report = audit_t8_runtime_catalog(list(FINAL_ITEM_CATALOG))
    assert report["ready"], report["diagnostics"]
    assert report["total"] == 1500
    assert all(report["catalog_gate"].values())
    assert all(report["economy_gate"].values())
    assert report["diagnostics"]["random_unique_slugs"] == [
        "l_unico_anello_della_compagnia"
    ]


def test_t8_runtime_gate_rejects_missing_lore_and_real_money_item():
    rows = [deepcopy(item) for item in FINAL_ITEM_CATALOG]
    rows[0]["lore_source"] = ""
    rows[0]["can_be_sold_for_real_money"] = True
    report = audit_t8_runtime_catalog(rows)
    assert not report["ready"]
    assert not report["catalog_gate"]["required_fields_complete"]
    assert not report["economy_gate"]["no_real_money_items"]


def test_t8_human_checklist_is_explicit_and_requires_every_check():
    partial = normalized_t8_checklist({T8_CHECKLIST_KEYS[0]: True})
    complete = normalized_t8_checklist({
        **{key: True for key in T8_CHECKLIST_KEYS},
        "notes": "Desktop e mobile verificati.",
    })
    assert not partial["completed"]
    assert partial["completed_count"] == 1
    assert complete["completed"]
    assert complete["completed_count"] == complete["required_count"] == 6
