"""Phase 14.3-c — anti-leak trait + dispatch preview tests.

Validates:
- /api/adventurers never exposes test traits or raw `code` fields.
- /api/expeditions/preview returns the correct shape, is read-only,
  enforces auth + ownership, and re-uses the canonical formulas.
"""
import os
import uuid
import re
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env.test", override=False)

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

TESTID_RE = re.compile(r"^(Test|TEST_|qa_|dev_|pytest_)|_[a-f0-9]{6,}$", re.IGNORECASE)


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    try:
        yield cli[DB_NAME]
    finally:
        cli.close()


@pytest.fixture(scope="module")
def player():
    """Register a fresh player with a guild; return (token, headers, guild_id)."""
    tag = f"p143c_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    # ROUND 6B FASE A — sourced from tests/.env.test (gitignored)
    password = os.environ["TEST_STRONG_PASSWORD"]

    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "username": tag, "password": password},
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(
        f"{BASE_URL}/api/guilds",
        headers=headers,
        json={"name": f"G_{tag}", "description": "preview test guild"},
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    guild_id = r.json().get("guild", r.json()).get("id") or r.json().get("id")
    assert guild_id

    # Recruit adventurers — request offers, then recruit top 3.
    r = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=headers, timeout=15)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    offers = body.get("offers") or body.get("candidates") or body.get("roster") or []
    cand_ids = [o.get("candidate_id") or o.get("id") for o in offers][:3]
    assert len(cand_ids) == 3, f"need 3 offers, got {len(cand_ids)}: {body}"

    adv_ids = []
    for cid in cand_ids:
        r = requests.post(
            f"{BASE_URL}/api/recruitment/recruit",
            headers=headers,
            json={"candidate_id": cid},
            timeout=15,
        )
        assert r.status_code in (200, 201), r.text
        adv = r.json().get("adventurer", r.json())
        adv_ids.append(adv["id"])

    yield {"token": token, "headers": headers, "guild_id": guild_id, "adv_ids": adv_ids}


# ─────────────────────────────────────────────────────────────────────────
# Anti-leak tests
# ─────────────────────────────────────────────────────────────────────────


def test_adventurers_never_expose_test_traits_or_raw_code(player):
    r = requests.get(f"{BASE_URL}/api/adventurers", headers=player["headers"], timeout=15)
    assert r.status_code == 200, r.text
    advs = r.json().get("adventurers", r.json())
    assert advs, "fresh player should have adventurers"
    for a in advs:
        traits = a.get("traits") or []
        for t in traits:
            label = (t.get("display_name") or "").strip()
            assert label, f"trait without display_name leaked: {t}"
            assert not TESTID_RE.search(label), f"Test pattern leaked in display_name: {label}"
            # Public projection must NOT contain backend-only fields.
            forbidden = {"code", "is_test", "is_active", "modifier_type", "affected_stat",
                         "modifier_value", "is_positive", "name"}
            leaked = forbidden & set(t.keys())
            assert not leaked, f"forbidden fields leaked in trait: {leaked} (trait={t})"
            assert t.get("rarity") in {"common", "uncommon", "rare", "epic"}
            assert t.get("polarity") in {"positive", "negative", "mixed"}


def test_no_test_trait_in_recruitment_pool(player):
    """Newly recruited adventurer never carries an is_test trait."""
    r = requests.get(
        f"{BASE_URL}/api/recruitment/candidates", headers=player["headers"], timeout=15
    )
    assert r.status_code in (200, 201)
    body = r.json()
    offers = body.get("offers") or body.get("candidates") or body.get("roster") or []
    # Candidates still expose legacy shape internally (name/is_positive). That
    # is acceptable IF every trait corresponds to an active, non-test row in
    # the trait collection. We validate via direct DB lookup.
    cli = MongoClient(MONGO_URL)
    try:
        names_seen = set()
        for o in offers:
            for t in (o.get("traits") or []):
                names_seen.add(t.get("name"))
        if names_seen:
            bad = cli[DB_NAME].adventurer_traits.count_documents(
                {"name": {"$in": list(names_seen)}, "$or": [
                    {"is_test": True}, {"is_active": False}
                ]}
            )
            assert bad == 0, f"recruitment served {bad} test traits"
    finally:
        cli.close()


# ─────────────────────────────────────────────────────────────────────────
# Dispatch preview tests
# ─────────────────────────────────────────────────────────────────────────


def _first_dungeon(headers):
    r = requests.get(f"{BASE_URL}/api/dungeons", headers=headers, timeout=15)
    assert r.status_code == 200
    return r.json().get("dungeons", r.json())[0]


def test_preview_requires_auth():
    r = requests.post(
        f"{BASE_URL}/api/expeditions/preview",
        json={"dungeon_id": "x", "adventurer_ids": ["y"]},
        timeout=15,
    )
    assert r.status_code in (401, 403)


def test_preview_happy_path(player):
    dungeon = _first_dungeon(player["headers"])
    r = requests.post(
        f"{BASE_URL}/api/expeditions/preview",
        headers=player["headers"],
        json={
            "dungeon_id": dungeon["id"],
            "adventurer_ids": player["adv_ids"][:dungeon.get("required_team_size", 3)],
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Shape
    assert isinstance(body["success_chance"], int)
    assert 0 <= body["success_chance"] <= 100
    assert body["injury_risk"] in {"low", "medium", "high"}
    er = body["expected_reward"]
    assert isinstance(er["gold_range"], list) and len(er["gold_range"]) == 2
    assert er["gold_range"][0] <= er["gold_range"][1]
    assert isinstance(er["xp_range"], list) and len(er["xp_range"]) == 2
    assert er["loot_rarity_hint"] in {"common", "uncommon", "rare"}
    assert isinstance(body["team_power"], int)
    assert isinstance(body["recommended_power"], int)
    assert isinstance(body["modifiers"], list)
    for m in body["modifiers"]:
        assert m["source"] in {"trait", "class"}
        assert m.get("display_name")
        assert m.get("polarity") in {"positive", "negative", "mixed"}
        # No leak of internal flags
        assert "is_test" not in m and "is_active" not in m
        # No Test* leak via display_name
        assert not TESTID_RE.search(m["display_name"]), m


def test_preview_is_read_only(player, db):
    """Multiple preview calls must not create expeditions / mutate guild."""
    dungeon = _first_dungeon(player["headers"])
    before_exps = db.expeditions.count_documents({"guild_id": player["guild_id"]})
    before_gold = (db.guilds.find_one({"id": player["guild_id"]}, {"gold": 1}) or {}).get("gold", 0)

    payload = {
        "dungeon_id": dungeon["id"],
        "adventurer_ids": player["adv_ids"][:dungeon.get("required_team_size", 3)],
    }
    for _ in range(5):
        r = requests.post(
            f"{BASE_URL}/api/expeditions/preview",
            headers=player["headers"], json=payload, timeout=15,
        )
        assert r.status_code == 200

    after_exps = db.expeditions.count_documents({"guild_id": player["guild_id"]})
    after_gold = (db.guilds.find_one({"id": player["guild_id"]}, {"gold": 1}) or {}).get("gold", 0)
    assert before_exps == after_exps
    assert before_gold == after_gold


def test_preview_rejects_foreign_adventurers(player):
    """Adventurer ids from another guild → 403."""
    dungeon = _first_dungeon(player["headers"])
    foreign_ids = [str(uuid.uuid4()) for _ in range(dungeon.get("required_team_size", 3))]
    r = requests.post(
        f"{BASE_URL}/api/expeditions/preview",
        headers=player["headers"],
        json={"dungeon_id": dungeon["id"], "adventurer_ids": foreign_ids},
        timeout=15,
    )
    assert r.status_code == 403, r.text


def test_preview_validates_team_size(player):
    dungeon = _first_dungeon(player["headers"])
    r = requests.post(
        f"{BASE_URL}/api/expeditions/preview",
        headers=player["headers"],
        json={"dungeon_id": dungeon["id"], "adventurer_ids": player["adv_ids"][:1]},
        timeout=15,
    )
    assert r.status_code == 422, r.text


def test_preview_unknown_dungeon(player):
    r = requests.post(
        f"{BASE_URL}/api/expeditions/preview",
        headers=player["headers"],
        json={"dungeon_id": str(uuid.uuid4()), "adventurer_ids": player["adv_ids"][:3]},
        timeout=15,
    )
    assert r.status_code == 404, r.text


# ─────────────────────────────────────────────────────────────────────────
# Leaderboard regression (Step A2)
# ─────────────────────────────────────────────────────────────────────────


def test_leaderboard_still_excludes_test_users():
    r = requests.get(f"{BASE_URL}/api/leaderboard/guilds?limit=50", timeout=15)
    assert r.status_code == 200
    body = r.json()
    for e in body["entries"]:
        # No legacy test guild names from earlier audit should leak.
        for forbidden in ("TEST_P2", "G_p10cls", "Guild_ref_poor", "Guild_p93"):
            assert forbidden not in e["guild_name"], f"leak: {e['guild_name']}"
        # No private fields exposed.
        assert "owner_user_id" not in e
        assert "email" not in e
        assert "is_test_user" not in e
