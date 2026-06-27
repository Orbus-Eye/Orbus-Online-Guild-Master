"""ROUND 6A.2b — Trait quarantine + display_name_it migration tests."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@pytest.fixture(scope="module")
def db():
    c = MongoClient(os.environ["MONGO_URL"])
    try:
        yield c[os.environ["DB_NAME"]]
    finally:
        c.close()


def _run_script() -> int:
    """Run the migration script and return exit code."""
    return subprocess.run(
        [sys.executable, "-m", "app.scripts.quarantine_and_migrate_traits"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
    ).returncode


class TestTraitQuarantine:
    def test_Q1_quarantine_applied_or_noop(self, db):
        """First run quarantines, second run is a no-op (both succeed)."""
        rc = _run_script()
        assert rc == 0
        # Re-run must succeed and quarantine nothing new
        rc2 = _run_script()
        assert rc2 == 0

    def test_Q2_no_suspicious_in_active_pool(self, db):
        """No active legitimate trait matches the suspicious patterns."""
        import re
        patterns = [
            re.compile(r"^X\d+$"),
            re.compile(r"^shorty\d+$"),
            re.compile(r"^AdminTrait_", re.I),
            re.compile(r"^MyTrait[_X]", re.I),
            re.compile(r"^Trait_X$"),
        ]
        ts = list(db.adventurer_traits.find(
            {"is_active": True, "is_test": {"$ne": True}},
            {"_id": 0, "name": 1},
        ))
        for t in ts:
            name = t.get("name", "")
            for rx in patterns:
                assert not rx.search(name), f"suspicious leaked into active pool: {name!r}"

    def test_Q3_quarantined_rows_audited(self, db):
        rows = list(db.audit_log.find({"event_type": "trait_quarantined"}))
        assert len(rows) >= 6  # at least the 6 first-batch matches
        for r in rows:
            m = r.get("metadata") or {}
            assert m.get("entity_type") == "trait"
            assert m.get("name")
            assert m.get("reason")

    def test_Q4_quarantined_are_inactive_and_test(self, db):
        # All audit-quarantined traits should be is_active=False AND is_test=True
        ids = [r["related_entity_id"] for r in db.audit_log.find(
            {"event_type": "trait_quarantined"}, {"related_entity_id": 1}
        )]
        for tid in ids:
            doc = db.adventurer_traits.find_one({"id": tid}, {"_id": 0})
            assert doc is not None, f"trait deleted! ROUND 6A.2b forbids hard delete: {tid}"
            assert doc.get("is_active") is False
            assert doc.get("is_test") is True


class TestDisplayNameMigration:
    def test_D1_every_trait_has_display_name_it(self, db):
        without = list(db.adventurer_traits.find(
            {"$or": [{"display_name_it": {"$exists": False}}, {"display_name_it": ""}]},
            {"_id": 0, "name": 1, "id": 1},
        ))
        assert without == [], f"traits missing display_name_it: {[t['name'] for t in without]}"

    def test_D2_known_translations(self, db):
        """Spot-check well-known canonical names."""
        cases = [
            ("Brave", "Coraggioso"),
            ("Sharp Eye", "Occhio Acuto"),
            ("Frail", "Fragile"),
            ("Devout", "Devoto"),
        ]
        for en, it in cases:
            t = db.adventurer_traits.find_one({"name": en})
            if t is None:
                continue  # not seeded in this DB → skip
            assert t.get("display_name_it") == it, f"{en!r} → got {t.get('display_name_it')!r}, expected {it!r}"

    def test_D3_migration_idempotent_does_not_overwrite(self, db):
        # Find one known doc, change its display_name_it, run script, verify
        # it was NOT touched.
        t = db.adventurer_traits.find_one({"name": "Brave"})
        if t is None:
            pytest.skip("Brave trait not seeded")
        db.adventurer_traits.update_one(
            {"id": t["id"]}, {"$set": {"display_name_it": "Custom Override"}}
        )
        _run_script()
        t2 = db.adventurer_traits.find_one({"id": t["id"]})
        assert t2["display_name_it"] == "Custom Override"
        # Restore canonical
        db.adventurer_traits.update_one(
            {"id": t["id"]}, {"$set": {"display_name_it": "Coraggioso"}}
        )
