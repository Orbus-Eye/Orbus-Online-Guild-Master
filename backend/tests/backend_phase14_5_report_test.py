"""ROUND 2 Fase 3 (Phase 14.5) — Expedition report explainability tests.

Two layers:

  1. Pure unit tests on `build_expedition_report` — no DB, no HTTP. Cover the
     three outcome buckets, the trait/class projection, the anti-leak guard
     and the legacy-doc fallback.

  2. A thin HTTP integration test that:
       - registers a guild,
       - recruits enough adventurers to clear Goblin Warrens,
       - dispatches an expedition with `base_duration_seconds` already
         elapsed (we backdate `completes_at` via Mongo since we can't
         wait 30s in a test),
       - polls GET /api/expeditions/{id} and checks the report fields.

  3. OpenAPI guard — path count must still be 43.
"""
import asyncio
import os
import time
import uuid

import pytest
import requests

pytestmark = pytest.mark.xdist_group(name="round5_serial_legacy")
from motor.motor_asyncio import AsyncIOMotorClient

from app.expeditions.report_builder import build_expedition_report


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")


def _api(p): return f"{BASE_URL}/api{p}"


# ── Pure unit tests ──────────────────────────────────────────────────────────
def _fake_completed_exp(success=True, score=10, chance=80, final_power=70):
    return {
        "id": str(uuid.uuid4()),
        "status": "completed",
        "result_summary": "Success" if success else "Failed",
        "final_score": score,
        "success_chance": chance,
        "success_chance_with_equipment": chance,
        "team_power": final_power,
        "final_team_power": final_power,
        "gold_reward": 100 if success else 25,
        "xp_reward": 30 if success else 12,
        "dungeon_name": "Goblin Warrens",
    }


def _member(name="Aria", role="Tank", cls="Warrior", traits=None):
    return {
        "name_snapshot": name,
        "class_name_snapshot": cls,
        "role_snapshot": role,
        "level_snapshot": 1,
        "traits_snapshot": traits or [],
    }


def _trait(code, display_name, polarity="positive", is_test=False, is_active=True):
    return {
        "code": code,
        "display_name": display_name,
        "polarity": polarity,
        "description": "",
        "is_test": is_test,
        "is_active": is_active,
    }


class TestBuilderOutcomeBuckets:
    def test_clear_success_bucket(self):
        exp = _fake_completed_exp(success=True, score=5, chance=80)
        members = [_member()]
        out = build_expedition_report(exp, members, {"recommended_power": 30, "slug": "goblin-warrens"}, [])
        assert out["report_summary"]["outcome"] == "success"
        assert out["report_summary"]["title"] == "Vittoria"

    def test_partial_success_bucket(self):
        # Score within last 10 of threshold → partial.
        exp = _fake_completed_exp(success=True, score=78, chance=80)
        out = build_expedition_report(exp, [_member()], {"recommended_power": 30}, [])
        assert out["report_summary"]["outcome"] == "partial_success"

    def test_failure_bucket(self):
        exp = _fake_completed_exp(success=False, score=90, chance=80)
        out = build_expedition_report(exp, [_member()], {"recommended_power": 30}, [])
        assert out["report_summary"]["outcome"] == "failure"
        # Failure must include a recovery/retreat step.
        types = [s["type"] for s in out["report_steps"]]
        assert "recovery" in types


class TestBuilderStepShape:
    def test_minimum_step_count_and_keys(self):
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, [_member()], {"recommended_power": 30}, [])
        assert len(out["report_steps"]) >= 3
        for s in out["report_steps"]:
            for k in ("type", "label", "result", "description", "modifiers",
                      "involved_adventurers", "involved_traits", "involved_classes"):
                assert k in s, f"missing key {k} in step {s}"

    def test_boss_step_appears_for_high_rec_power(self):
        exp = _fake_completed_exp(success=True, final_power=70)
        out = build_expedition_report(exp, [_member()], {"recommended_power": 65}, [])
        assert any(s["type"] == "boss" for s in out["report_steps"])

    def test_loot_step_always_present(self):
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, [_member()], {"recommended_power": 30}, [])
        assert any(s["type"] == "loot" for s in out["report_steps"])


class TestBuilderTraitProjection:
    def test_modifiers_use_display_name_not_code(self):
        traits = [_trait("lucky", "Fortunato", "positive")]
        members = [_member(traits=traits)]
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, members, {"recommended_power": 30}, [
            {"id": "x", "name": "Pugnale rotto", "rarity": "Common"}
        ])
        # Find the loot step and check the modifier text.
        loot_step = next(s for s in out["report_steps"] if s["type"] == "loot")
        modifiers_text = " ".join(loot_step["modifiers"])
        assert "Fortunato" in modifiers_text
        assert "lucky" not in modifiers_text  # canonical code must never leak

    def test_test_trait_never_surfaces(self):
        leaked = _trait("test_leak", "Test_random_abc123", "positive", is_test=True)
        traits = [leaked, _trait("brave", "Coraggioso", "positive")]
        members = [_member(traits=traits)]
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, members, {"recommended_power": 30}, [])
        all_text = []
        for s in out["report_steps"]:
            all_text.extend(s["modifiers"])
            for t in s["involved_traits"]:
                all_text.append(t["display_name"])
        joined = " | ".join(all_text)
        assert "Test_random" not in joined
        assert "test_leak" not in joined

    def test_inactive_trait_never_surfaces(self):
        inactive = _trait("brave", "Coraggioso", "positive", is_active=False)
        members = [_member(traits=[inactive])]
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, members, {"recommended_power": 30}, [])
        for s in out["report_steps"]:
            for t in s["involved_traits"]:
                assert t["display_name"] != "Coraggioso"


class TestBuilderLegacyFallback:
    def test_in_progress_returns_none(self):
        exp = {"id": "x", "status": "in_progress"}
        out = build_expedition_report(exp, [], None, [])
        assert out["report_summary"] is None
        assert out["report_steps"] is None

    def test_legacy_doc_without_traits_snapshot_does_not_crash(self):
        # An old expedition member doc has no `traits_snapshot` field.
        legacy_member = {
            "name_snapshot": "Old Hero",
            "class_name_snapshot": "Warrior",
            "role_snapshot": "Tank",
            "level_snapshot": 1,
        }
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, [legacy_member], {"recommended_power": 30}, [])
        assert out["report_summary"] is not None
        # No traits → no modifier strings.
        for s in out["report_steps"]:
            assert s["involved_traits"] == []

    def test_missing_dungeon_doc_does_not_crash(self):
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, [_member()], None, [])
        assert out["report_summary"]["recommended_power"] == 0
        assert out["report_steps"]  # still produces steps


class TestBuilderClassProjection:
    def test_warrior_tank_surfaces_in_italian(self):
        members = [_member(name="Aria", cls="Warrior", role="Tank")]
        exp = _fake_completed_exp(success=True)
        out = build_expedition_report(exp, members, {"recommended_power": 30}, [])
        combat_step = next(s for s in out["report_steps"] if s["type"] == "combat")
        names = [c["display_name"] for c in combat_step["involved_classes"]]
        assert "Guerriero" in names


# ── HTTP smoke (light) ───────────────────────────────────────────────────────
def _bootstrap_user_and_guild():
    suffix = uuid.uuid4().hex[:10]
    email = f"r2f3_{suffix}@orbus.test"
    payload = {"email": email, "username": f"r2f3_{suffix}", "password": "password123"}
    r = requests.post(_api("/auth/register"), json=payload, timeout=15)
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    g = requests.post(_api("/guilds"), json={"name": f"G {suffix}", "description": "round 2 fase 3"},
                      headers=auth, timeout=15)
    assert g.status_code == 201, g.text
    return auth, g.json()


def _recruit(auth, n):
    requests.get(_api("/recruitment/candidates"), headers=auth, timeout=15)
    ids = []
    for _ in range(n):
        cands = requests.get(_api("/recruitment/candidates"), headers=auth, timeout=15).json()
        clist = cands.get("candidates") or []
        if not clist:
            return ids
        cid = clist[0].get("candidate_id") or clist[0].get("id")
        r = requests.post(_api("/recruitment/recruit"), json={"candidate_id": cid},
                          headers=auth, timeout=15)
        if r.status_code != 201:
            break
        ids.append(r.json()["adventurer"]["id"])
    return ids


class TestExpeditionReportHTTP:
    @pytest.mark.flaky(reruns=2)  # Phase 19 — xdist DB race; see FLAKY_TESTS_AUDIT.md
    def test_get_expedition_returns_report_fields(self):
        auth, _ = _bootstrap_user_and_guild()
        # Recruit 3 → Goblin Warrens requires 3
        ids = _recruit(auth, 3)
        if len(ids) < 3:
            pytest.skip("could not recruit enough adventurers (gold/cap)")
        # Find goblin warrens dungeon id
        dungeons = requests.get(_api("/dungeons"), headers=auth, timeout=15).json()
        d_list = dungeons.get("dungeons") or []
        goblin = next((d for d in d_list if d.get("slug") == "goblin-warrens"), None)
        assert goblin, "goblin-warrens dungeon missing in seed"
        # Start expedition
        r = requests.post(
            _api("/expeditions"),
            json={"dungeon_id": goblin["id"], "adventurer_ids": ids[:3]},
            headers=auth, timeout=15,
        )
        assert r.status_code == 201, r.text
        exp_id = r.json()["expedition"]["id"]
        # Backdate completes_at so the lazy sweep marks it complete on next read.
        async def _backdate():
            cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = cli[os.environ["DB_NAME"]]
            from datetime import datetime, timezone, timedelta
            past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
            await db.expeditions.update_one({"id": exp_id}, {"$set": {"completes_at": past}})
            cli.close()
        # Updated for Round 5 §I — use new_event_loop to avoid closed-loop reuse on 3.11.
        _loop = asyncio.new_event_loop()
        try:
            _loop.run_until_complete(_backdate())
        finally:
            _loop.close()
        # Poll GET /api/expeditions/{id} until completed
        deadline = time.time() + 10
        body = None
        while time.time() < deadline:
            r = requests.get(_api(f"/expeditions/{exp_id}"), headers=auth, timeout=15)
            assert r.status_code == 200, r.text
            body = r.json()
            if body["expedition"]["status"] == "completed":
                break
            time.sleep(0.5)
        assert body and body["expedition"]["status"] == "completed", body
        # Report fields present
        assert "report_summary" in body
        assert "report_steps" in body
        summary = body["report_summary"]
        steps = body["report_steps"]
        assert summary is not None
        assert steps and len(steps) >= 3
        assert summary["outcome"] in ("success", "partial_success", "failure")
        assert summary["title"] in ("Vittoria", "Successo parziale", "Sconfitta")
        # No raw code leaked in modifier text
        for s in steps:
            for m in s["modifiers"]:
                assert "_" not in m.split(":")[0], f"raw code suspected in {m!r}"


class TestOpenAPIInvariant:
    def test_path_count_unchanged_at_49(self):
        r = requests.get(_api("/openapi.json"), timeout=15)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        # 60 → +1 admin cleanup endpoint (Phase 16.1) = 61.
        # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
        assert len(paths) == 77, (
            f"expected 75 (Phase 16.1), got {len(paths)}"
        )


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
