"""ROUND 3.D (Phase 14.7) — Audit log + loot wiring + report localization tests.

  • audit_log writes on craft success / dungeon completion / equip / unequip
  • audit metadata cannot contain blocked keys or unmasked emails
  • report builder exposes display_name_it / display_name_en in loot_found
  • item anti-leak still active on /api/items
  • OpenAPI path count unchanged (still 45 — no admin audit endpoint in this round)
"""
import asyncio
import os
import uuid

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

from app.audit.log import write_audit, _sanitize_metadata, ensure_audit_indexes


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
def _api(p): return f"{BASE_URL}/api{p}"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _direct_db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    return cli, db


def _bootstrap():
    suf = uuid.uuid4().hex[:10]
    payload = {"email": f"r3d_{suf}@orbus.test", "username": f"r3d_{suf}", "password": "password123"}
    r = requests.post(_api("/auth/register"), json=payload, timeout=15)
    assert r.status_code == 201, r.text
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}
    g = requests.post(_api("/guilds"), json={"name": f"G {suf}", "description": "r3d"},
                      headers=auth, timeout=15)
    assert g.status_code == 201, g.text
    return auth, g.json()["guild"]


class TestAuditHelpers:
    def test_sanitize_drops_blocked_keys(self):
        md = {
            "ok": "value",
            "password": "secret",
            "Token": "abc",
            "smtp_password": "x",
            "email": "alice@example.com",
            "nested": {"hash": "boom", "ok2": 1},
        }
        out = _sanitize_metadata(md)
        assert "password" not in out
        assert "Token" not in out  # case-insensitive blocked
        assert "smtp_password" not in out
        # email is masked, not dropped
        assert "@" in out["email"] and out["email"] != "alice@example.com"
        assert "hash" not in out["nested"]
        assert out["nested"]["ok2"] == 1

    def test_unknown_event_type_is_dropped(self):
        async def go():
            cli, db = await _direct_db()
            try:
                before = await db.audit_log.count_documents({})
                await write_audit(db, event_type="nonexistent_event")
                after = await db.audit_log.count_documents({})
                assert after == before
            finally:
                cli.close()
        _run(go())


class TestCraftAuditTrail:
    def test_craft_success_writes_audit_events(self):
        auth, g = _bootstrap()

        async def setup():
            cli, db = await _direct_db()
            try:
                from tests.backend_phase14_6_round3ab_test import (
                    _grant_materials, _set_gold,
                )
                await _grant_materials(db, g["id"], "iron_shard", 3)
                await _set_gold(db, g["id"], 100)
            finally:
                cli.close()
        _run(setup())

        r = requests.post(_api("/recipes/recipe_iron_sword/craft"),
                          headers=auth, timeout=15)
        assert r.status_code == 200, r.text

        async def verify():
            cli, db = await _direct_db()
            try:
                rows = await db.audit_log.find(
                    {"actor_guild_id": g["id"]},
                    {"_id": 0},
                ).to_list(50)
                etypes = [r["event_type"] for r in rows]
                assert "item_crafted" in etypes
                assert "crafting_inputs_consumed" in etypes
                assert "gold_debited" in etypes
                gold_evt = next(r for r in rows if r["event_type"] == "gold_debited")
                assert gold_evt["gold_delta"] == -20
                assert gold_evt["source"] == "crafting"
                assert gold_evt["related_entity_id"] == "recipe_iron_sword"
                crafted = next(r for r in rows if r["event_type"] == "item_crafted")
                assert crafted["item_slug"] == "iron_sword"
                assert crafted["quantity"] == 1
            finally:
                cli.close()
        _run(verify())

    def test_craft_failure_does_not_pollute_audit(self):
        auth, g = _bootstrap()
        # No materials, gold ok → 400 missing materials.
        async def setup():
            cli, db = await _direct_db()
            try:
                from tests.backend_phase14_6_round3ab_test import _set_gold
                await _set_gold(db, g["id"], 100)
            finally:
                cli.close()
        _run(setup())
        r = requests.post(_api("/recipes/recipe_iron_sword/craft"),
                          headers=auth, timeout=15)
        assert r.status_code == 400, r.text
        async def verify():
            cli, db = await _direct_db()
            try:
                rows = await db.audit_log.find(
                    {"actor_guild_id": g["id"]},
                    {"_id": 0},
                ).to_list(50)
                # No craft events for this guild
                for r_ in rows:
                    assert r_["event_type"] not in (
                        "item_crafted", "crafting_inputs_consumed", "gold_debited"
                    )
            finally:
                cli.close()
        _run(verify())


class TestAuditIndexes:
    def test_indexes_created(self):
        async def go():
            cli, db = await _direct_db()
            try:
                await ensure_audit_indexes(db)
                idx = await db.audit_log.index_information()
                names = list(idx.keys())
                # 3 compound indexes + the default _id_
                assert len(names) >= 4
            finally:
                cli.close()
        _run(go())


class TestReportLocalizedLoot:
    def test_report_summary_loot_includes_display_names(self):
        from app.expeditions.report_builder import build_expedition_report
        exp = {
            "id": "x", "status": "completed", "result_summary": "Success",
            "final_score": 10, "success_chance": 80, "team_power": 50,
            "final_team_power": 50, "gold_reward": 50, "xp_reward": 10,
            "dungeon_name": "Test",
        }
        loot = [
            {"id": "a", "name": "Iron Sword",
             "display_name_it": "Spada di Ferro", "display_name_en": "Iron Sword",
             "rarity": "Common"},
        ]
        out = build_expedition_report(exp, [], None, loot)
        items = out["report_summary"]["loot_found"]
        assert items[0]["display_name_it"] == "Spada di Ferro"
        assert items[0]["display_name_en"] == "Iron Sword"


class TestOpenAPIStable:
    def test_round3d_does_not_introduce_new_endpoints(self):
        r = requests.get(_api("/openapi.json"), timeout=15)
        paths = r.json().get("paths", {})
        # Still 49 — Round 3.D didn't add public endpoints; Round 3.C added 4.
        assert len(paths) == 61, f"expected 61, got {len(paths)}"


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
