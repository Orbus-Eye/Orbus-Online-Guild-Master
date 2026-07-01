"""ROUND 6A.2a — Squads CRUD + validation tests (e2e via HTTP)."""
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("BACKEND_URL", "http://localhost:8001")
).rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user_with_advs(db, hint="r6a2a", n_advs=22):
    """Create a user + guild + n_advs adventurers (level 1, all roles)."""
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R6A2a {tag[-5:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})

    # Inject N adventurers directly (starter roster gives 5; we need up to 22 for raid_20)
    advs_existing = list(db.adventurers.find({"guild_id": g["id"]}, {"id": 1, "_id": 0}))
    needed = n_advs - len(advs_existing)
    if needed > 0:
        # Pull a class for role assignment
        cls = db.adventurer_classes.find_one({"is_active": True, "is_test": {"$ne": True}})
        for i in range(needed):
            aid = str(uuid.uuid4())
            db.adventurers.insert_one({
                "id": aid, "guild_id": g["id"],
                "name": f"R6A2aAdv_{tag}_{i:02d}",
                "adventurer_class_id": cls["id"], "class_name": cls["name"],
                "class_role": cls.get("role", "DPS"),
                "rarity": "Common", "level": 1, "experience": 0,
                "strength": 5, "agility": 5, "intellect": 5, "endurance": 5, "faith": 5,
                "stamina": 100, "morale": 100, "traits": [],
                "is_available": True, "is_starter": False, "rename_count": 0,
                "created_at": "2026-06-27T00:00:00+00:00",
                "updated_at": "2026-06-27T00:00:00+00:00",
            })
    advs = list(db.adventurers.find({"guild_id": g["id"]}, {"id": 1, "_id": 0}).limit(n_advs))
    return {
        "headers": h, "guild_id": g["id"], "email": email, "tag": tag,
        "adv_ids": [a["id"] for a in advs],
    }


class TestSquadsCreate:
    def test_S1_create_dungeon_3(self, db):
        u = _user_with_advs(db, "s1", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "Tre Mosche",
            "squad_type": "dungeon_3",
            "adventurer_ids": u["adv_ids"][:3],
        }, timeout=15)
        assert r.status_code == 201, r.text
        b = r.json()
        assert b["squad_type"] == "dungeon_3"
        assert b["member_count"] == 3
        assert b["total_power"] > 0
        assert b["is_archived"] is False
        assert "owner_user_id" not in b  # PII never exposed
        assert "name_lower" not in b  # internal field never exposed

    def test_S2_create_dungeon_5(self, db):
        u = _user_with_advs(db, "s2", n_advs=6)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "Cinque Lame",
            "squad_type": "dungeon_5",
            "adventurer_ids": u["adv_ids"][:5],
        }, timeout=15)
        assert r.status_code == 201, r.text
        assert r.json()["member_count"] == 5

    def test_S3_create_raid_20_with_parties(self, db):
        u = _user_with_advs(db, "s3", n_advs=22)
        ids = u["adv_ids"][:20]
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "Raid Test",
            "squad_type": "raid_20",
            "adventurer_ids": ids,
            "raid_parties": {
                "party_1": ids[0:5],
                "party_2": ids[5:10],
                "party_3": ids[10:15],
                "party_4": ids[15:20],
            },
        }, timeout=15)
        assert r.status_code == 201, r.text
        b = r.json()
        assert b["squad_type"] == "raid_20"
        assert len(b["adventurer_ids"]) == 20
        assert b["raid_parties"]["party_1"] == ids[0:5]


class TestSquadsValidation:
    def test_V1_wrong_size_returns_422(self, db):
        u = _user_with_advs(db, "v1", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "Sbagliata", "squad_type": "dungeon_3",
            "adventurer_ids": u["adv_ids"][:2],
        }, timeout=15)
        assert r.status_code == 422
        assert "size_invalid" in r.json()["detail"]

    def test_V2_duplicate_adventurer_returns_422(self, db):
        u = _user_with_advs(db, "v2", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "Doppia",
            "squad_type": "dungeon_3",
            "adventurer_ids": [u["adv_ids"][0], u["adv_ids"][0], u["adv_ids"][1]],
        }, timeout=15)
        assert r.status_code == 422
        assert "duplicate" in r.json()["detail"]

    def test_V3_html_in_name_returns_422(self, db):
        u = _user_with_advs(db, "v3", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "<script>x</script>", "squad_type": "dungeon_3",
            "adventurer_ids": u["adv_ids"][:3],
        }, timeout=15)
        assert r.status_code == 422

    def test_V4_cross_guild_adventurer_returns_422(self, db):
        u1 = _user_with_advs(db, "v4a", n_advs=4)
        u2 = _user_with_advs(db, "v4b", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u1["headers"], json={
            "name": "Furto", "squad_type": "dungeon_3",
            "adventurer_ids": [u1["adv_ids"][0], u1["adv_ids"][1], u2["adv_ids"][0]],
        }, timeout=15)
        assert r.status_code == 422
        assert "not_in_guild" in r.json()["detail"]

    def test_V5_raid_parties_required_for_raid_20(self, db):
        u = _user_with_advs(db, "v5", n_advs=22)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "RaidNoP", "squad_type": "raid_20",
            "adventurer_ids": u["adv_ids"][:20],
        }, timeout=15)
        assert r.status_code == 422
        assert "raid_parties" in r.json()["detail"]

    def test_V6_raid_parties_union_mismatch(self, db):
        u = _user_with_advs(db, "v6", n_advs=22)
        ids = u["adv_ids"][:20]
        # Swap one id in party_4 with one NOT in adventurer_ids → mismatch
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "RaidMismatch", "squad_type": "raid_20",
            "adventurer_ids": ids,
            "raid_parties": {
                "party_1": ids[0:5],
                "party_2": ids[5:10],
                "party_3": ids[10:15],
                "party_4": ids[15:19] + [u["adv_ids"][21]],
            },
        }, timeout=15)
        assert r.status_code == 422
        assert "union_mismatch" in r.json()["detail"] or "not_in_guild" in r.json()["detail"]

    def test_V7_name_unique_per_guild(self, db):
        u = _user_with_advs(db, "v7", n_advs=6)
        for _ in range(2):
            requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
                "name": "UniqName", "squad_type": "dungeon_3",
                "adventurer_ids": u["adv_ids"][:3],
            }, timeout=15)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "UniqName", "squad_type": "dungeon_5",
            "adventurer_ids": u["adv_ids"][:5],
        }, timeout=15)
        assert r.status_code == 409
        assert "name_taken" in r.json()["detail"]


class TestSquadsCRUD:
    def test_C1_list_filters_archived(self, db):
        u = _user_with_advs(db, "c1", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "ToArchive", "squad_type": "dungeon_3",
            "adventurer_ids": u["adv_ids"][:3],
        }, timeout=15)
        sid = r.json()["squad_id"]
        # Archive
        d = requests.delete(f"{BASE_URL}/api/squads/{sid}", headers=u["headers"], timeout=15)
        assert d.status_code == 200
        assert d.json()["is_archived"] is True
        # List excludes archived
        ls = requests.get(f"{BASE_URL}/api/squads", headers=u["headers"], timeout=15)
        assert all(s["squad_id"] != sid for s in ls.json()["squads"])
        # GET single also 404 after archive
        gone = requests.get(f"{BASE_URL}/api/squads/{sid}", headers=u["headers"], timeout=15)
        assert gone.status_code == 404
        # DB still has the doc (soft delete = no hard delete)
        doc = db.squads.find_one({"id": sid})
        assert doc is not None
        assert doc["is_archived"] is True

    def test_C2_owner_isolation(self, db):
        u1 = _user_with_advs(db, "c2a", n_advs=4)
        u2 = _user_with_advs(db, "c2b", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u1["headers"], json={
            "name": "MineOnly", "squad_type": "dungeon_3",
            "adventurer_ids": u1["adv_ids"][:3],
        }, timeout=15)
        sid = r.json()["squad_id"]
        # u2 cannot read u1's squad — should 404 (no info leak)
        forbidden = requests.get(
            f"{BASE_URL}/api/squads/{sid}", headers=u2["headers"], timeout=15
        )
        assert forbidden.status_code == 404
        # u2 cannot delete u1's squad
        d = requests.delete(f"{BASE_URL}/api/squads/{sid}", headers=u2["headers"], timeout=15)
        assert d.status_code == 404

    def test_C3_unauthenticated_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/squads", timeout=15)
        assert r.status_code == 401

    def test_C4_audit_log_emitted(self, db):
        u = _user_with_advs(db, "c4", n_advs=4)
        r = requests.post(f"{BASE_URL}/api/squads", headers=u["headers"], json={
            "name": "AuditSquad", "squad_type": "dungeon_3",
            "adventurer_ids": u["adv_ids"][:3],
        }, timeout=15)
        sid = r.json()["squad_id"]
        row = db.audit_log.find_one({
            "event_type": "squad_created", "related_entity_id": sid,
        })
        assert row is not None
        assert row["metadata"]["squad_type"] == "dungeon_3"
        assert row["metadata"]["member_count"] == 3
        # Archive emits squad_archived
        requests.delete(f"{BASE_URL}/api/squads/{sid}", headers=u["headers"], timeout=15)
        arch = db.audit_log.find_one({
            "event_type": "squad_archived", "related_entity_id": sid,
        })
        assert arch is not None
