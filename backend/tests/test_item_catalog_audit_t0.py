"""Offline T0 item snapshot audit."""
from app.scripts.t0_item_catalog_audit import build_dry_run_report


def test_dry_run_audit_is_non_mutating_and_actionable():
    rows = [
        {
            "slug": "same",
            "name": "Nome",
            "rarity": "Legendary",
            "level_required": 12,
            "acquisition_mode": "random_drop",
        },
        {
            "slug": "same",
            "name": "nome",
            "rarity": "Unique",
            "level_required": 15,
            "lore_source": "orbus:test",
        },
    ]
    original = [dict(row) for row in rows]
    report = build_dry_run_report(rows)

    assert rows == original
    assert report["mode"] == "dry_run_read_only"
    assert report["mutations"] == 0
    assert report["ready_for_1500_import"] is False
    findings = report["findings"]
    assert len(findings["duplicate_slugs"]) == 1
    assert len(findings["duplicate_names_casefold"]) == 1
    assert findings["endgame_below_max_level"][0]["slug"] == "same"
    assert findings["forbidden_ordinary_endgame_drops"] == [
        {"slug": "same", "rarity": "Legendary"}
    ]
