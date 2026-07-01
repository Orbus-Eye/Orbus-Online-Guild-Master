"""ROUND 16.5 P0.3 — Wiring runtime `required_level` gate HTTP test.

Verifica via HTTP isolato (`ISOLATED_HTTP_TESTS=1`, port 8002,
`orbus_r16_test`) che il nuovo campo `required_level` è correttamente
letto dal runtime enforcement in `expeditions/level_gate.py`.

Scenari coperti (7):
1. Team lv4 → world-tree-roots-5p (req=14) → 423 blocco
2. Team lv7 → silent-monastery-5p (req=7) → NO 423 gate
3. Team con 1 membro sotto livello (2×lv8 + 1×lv3) → 423 blocco
4. Dungeon con `required_level=0` e `min_adventurer_level=5` → gate legge 5
5. Dungeon con entrambi assenti + difficulty=1 → nessun gate
6. Fallback edge case: dungeon vecchio non aggiornato in P0.2
7. Payload errore contiene required_level, adventurers_below, dungeon_slug
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient


# ═════════════════════════════════════════════════════════════════════
# 0. Fixtures
# ═════════════════════════════════════════════════════════════════════


def _api_base() -> str:
    """Ritorna la URL dell'isolated backend (port 8002) — enforced da
    conftest quando ISOLATED_HTTP_TESTS=1."""
    return (
        os.environ.get("API_BASE_URL")
        or os.environ.get("REACT_APP_BACKEND_URL")
        or "http://localhost:8001"
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture(scope="module")
def test_db():
    db_name = os.environ.get("DB_NAME", "")
    assert db_name.endswith("_test") or "test" in db_name.lower(), (
        f"REFUSING: DB_NAME={db_name!r} non è un test DB."
    )
    client = MongoClient(os.environ["MONGO_URL"])
    yield client[db_name]
    client.close()


@pytest.fixture(scope="module")
def tester_auth(isolated_backend_url, test_db):
    """Registra (o riusa) un utente + gilda DEDICATI al P0.3 wiring test.

    Non usiamo `tester@orbus.test` per evitare contaminazione con altri
    adv/dungeon lasciati da altri test suite. Se l'utente esiste già,
    facciamo login. Poi puliamo AGGRESSIVAMENTE tutti gli adventurer
    della sua gilda per aprire spazio al roster cap (dormitory lv1 = 5).
    """
    base = _api_base()
    email = "r165p03@orbus.test"
    password = "R165P03!password"
    username = "r165p03_user"
    # Register or login
    r = requests.post(
        f"{base}/api/auth/register",
        json={"email": email, "password": password, "username": username},
        timeout=10,
    )
    if r.status_code in (200, 201):
        token = r.json()["access_token"]
    else:
        r2 = requests.post(
            f"{base}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        assert r2.status_code == 200, f"login failed: {r2.status_code} {r2.text}"
        token = r2.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Guild
    r = requests.get(f"{base}/api/guilds/me", headers=headers, timeout=10)
    if r.status_code == 404:
        r = requests.post(
            f"{base}/api/guilds",
            headers=headers,
            json={"name": f"R165P03Guild{int(time.time())}",
                  "description": "R16.5 P0.3 wiring test dedicated"},
            timeout=10,
        )
        assert r.status_code in (200, 201), r.text
        payload = r.json()
    else:
        assert r.status_code == 200, r.text
        payload = r.json()
    guild = payload.get("guild", payload)
    guild_id = guild.get("id") or guild.get("guild_id")
    assert guild_id, f"guild id missing: {payload}"
    # ── CLEANUP roster: rimuovi TUTTI gli adv esistenti nella gilda,
    # poi setta dormitory a livello alto per evitare over-cap. Il DB è
    # `orbus_r16_test` (isolato) → operazione sicura.
    test_db.adventurers.delete_many({"guild_id": guild_id})
    # Trigger lazy-init del doc guild_structures via un GET su territory.
    requests.get(f"{base}/api/territory", headers=headers, timeout=10)
    # Ora il doc esiste con schema legittimo. Alziamo dormitories.level
    # per ampliare il roster cap.
    test_db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "structures.dormitories.level": 10,
            "structures.dormitories.is_unlocked": True,
            "updated_at": _now_iso(),
        }},
    )
    # Bypass del soft-progression gate (evaluate_dungeon_gate): serve
    # `guild.level >= 2` e `max_team_power_ever >= 340` per superare
    # world-tree-roots-5p (min_max_team_power_ever=340) e altri gate.
    test_db.guilds.update_one(
        {"id": guild_id},
        {"$set": {
            "level": 20,
            "max_team_power_ever": 999,
            "updated_at": _now_iso(),
        }},
    )
    return {"token": token, "headers": headers, "guild_id": guild_id}


@pytest.fixture
def seeded_dungeons(test_db):
    """Popola dungeon di test con configurazioni specifiche del gate.

    NB: opera SOLO su slug prefissati `r165test-*` per non toccare
    seed reali. Idempotente.
    """
    now = _now_iso()
    dungeons = [
        # Test 4 — required_level=0, min_adventurer_level=5 (fallback legacy)
        {
            "id": f"r165test-fallback-legacy-{uuid.uuid4()}",
            "slug": "r165test-fallback-legacy",
            "name": "R165 Test Fallback Legacy",
            "name_it": "R165 Test Fallback Legacy",
            "required_level": 0,
            "min_adventurer_level": 5,
            "difficulty": 1,
            "recommended_power": 100,
            "required_team_size": 3,
            "base_gold_reward": 10,
            "base_xp_reward": 10,
            "base_duration_seconds": 60,
            "is_active": True,
        },
        # Test 5 — entrambi assenti, difficulty=1 (fallback finale: 1)
        {
            "id": f"r165test-nogate-{uuid.uuid4()}",
            "slug": "r165test-nogate-legacy",
            "name": "R165 Test No Gate",
            "name_it": "R165 Test No Gate",
            "required_level": 0,
            "min_adventurer_level": None,
            "difficulty": 1,
            "recommended_power": 100,
            "required_team_size": 3,
            "base_gold_reward": 10,
            "base_xp_reward": 10,
            "base_duration_seconds": 60,
            "is_active": True,
        },
        # Test 6 — dungeon "vecchio" (P0.2 non applicato): required_level
        # assente completamente + min_adventurer_level esplicito = 7.
        {
            "id": f"r165test-legacy-only-{uuid.uuid4()}",
            "slug": "r165test-legacy-only",
            "name": "R165 Test Legacy Only",
            "name_it": "R165 Test Legacy Only",
            "min_adventurer_level": 7,
            "difficulty": 2,
            "recommended_power": 120,
            "required_team_size": 3,
            "base_gold_reward": 10,
            "base_xp_reward": 10,
            "base_duration_seconds": 60,
            "is_active": True,
        },
        # Test A.3.4 — dungeon con SOLO difficulty=4 (nessun required_level,
        # nessun min_adventurer_level). Post-D2 il fallback difficulty è
        # rimosso → gate = 0 (accesso libero). Pre-D2 era gate=12.
        {
            "id": f"r165test-diff-only-{uuid.uuid4()}",
            "slug": "r165test-diff-only",
            "name": "R165 Test Difficulty Only",
            "name_it": "R165 Test Difficulty Only",
            "difficulty": 4,  # avrebbe mappato → gate=12 pre-D2
            "recommended_power": 100,
            "required_team_size": 3,
            "base_gold_reward": 10,
            "base_xp_reward": 10,
            "base_duration_seconds": 60,
            "is_active": True,
        },
    ]
    for d in dungeons:
        d_id = d["id"]
        test_db.dungeons.update_one(
            {"slug": d["slug"]},
            {"$set": {**d, "id": d_id, "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    yield {
        d["slug"]: test_db.dungeons.find_one({"slug": d["slug"]}, {"_id": 0})
        for d in dungeons
    }


@pytest.fixture
def seeded_team(test_db, tester_auth):
    """Seed 5 avventurieri con livelli specifici nella gilda tester.

    Ritorna dict slug→adv_dict. I livelli sono controllati per i test:
      lv3, lv4a, lv4b, lv7, lv8
    """
    guild_id = tester_auth["guild_id"]
    now = _now_iso()
    levels = {"lv3": 3, "lv4a": 4, "lv4b": 4, "lv4c": 4, "lv7a": 7,
              "lv7b": 7, "lv7c": 7, "lv8a": 8, "lv8b": 8}
    advs: dict[str, dict] = {}
    for key, lvl in levels.items():
        adv_id = f"r165test-adv-{key}"
        doc = {
            "id": adv_id,
            "guild_id": guild_id,
            "name": f"R165Test-{key}",
            "level": lvl,
            "experience": 0,
            "is_available": True,
            "is_retired": False,
            "retired": False,
            "archived": False,
            "frozen": False,
            "is_test_artifact": True,
            # Schema legacy compatibile con runtime
            "class_name": "Warrior",
            "class_role": "Tank",
            "class": "Warrior",
            "role": "Tank",
            "strength": 10 + lvl,
            "agility": 5 + lvl,
            "intellect": 3 + lvl,
            "endurance": 8 + lvl,
            "faith": 3 + lvl,
            "stats": {"strength": 10 + lvl, "agility": 5 + lvl,
                      "intellect": 3 + lvl, "endurance": 8 + lvl,
                      "faith": 3 + lvl},
            "team_power": 30 + lvl * 5,
            "traits": [],
            "phase13_unbaked": False,
        }
        test_db.adventurers.update_one(
            {"id": adv_id},
            {"$set": {**doc, "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        advs[key] = doc
    yield advs


def _dungeon_id_from_slug(test_db, slug: str) -> str:
    d = test_db.dungeons.find_one({"slug": slug}, {"_id": 0, "id": 1})
    assert d, f"dungeon slug {slug!r} not found in test DB"
    return d["id"]


def _post_expedition(base: str, headers: dict, dungeon_id: str,
                     adventurer_ids: list[str]) -> requests.Response:
    return requests.post(
        f"{base}/api/expeditions",
        headers=headers,
        json={"dungeon_id": dungeon_id, "adventurer_ids": adventurer_ids},
        timeout=15,
    )


# ═════════════════════════════════════════════════════════════════════
# TESTS
# ═════════════════════════════════════════════════════════════════════


def test_1_team_lv4_vs_worldtree_lv14_blocked(
    test_db, tester_auth, seeded_team,
):
    """Un team lv4 tenta `world-tree-roots-5p` (required_level=14).
    Deve rispondere 423 con code=adventurer.level_too_low."""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "world-tree-roots-5p")
    ids = [seeded_team[k]["id"]
           for k in ("lv4a", "lv4b", "lv4c", "lv3", "lv7a")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    assert r.status_code == 423, (
        f"expected 423, got {r.status_code}: {r.text}"
    )
    detail = r.json().get("detail", {})
    assert detail.get("code") == "adventurer.level_too_low", detail
    assert detail.get("min_required_level") == 14, detail
    assert detail.get("source") == "expedition.dispatch"
    assert detail.get("dungeon_slug") == "world-tree-roots-5p"
    below = detail.get("adventurers_below") or detail.get("offending_adventurers")
    assert below, detail
    # Almeno i lv4 e il lv3 devono essere elencati (lv7a è sopra)
    below_levels = sorted(b["level"] for b in below)
    assert 3 in below_levels
    assert 4 in below_levels


def test_2_team_lv7_vs_silent_monastery_lv7_gate_passes(
    test_db, tester_auth, seeded_team,
):
    """Team lv7 vs silent-monastery-5p (required_level=7): il gate
    NON deve rispondere 423 adventurer.level_too_low. Può fallire per
    altri motivi (team_size, class fields, ecc.) — verifichiamo solo
    che il gate NON scatti."""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "silent-monastery-5p")
    # silent-monastery-5p ha team_size=5, uso 5 avv lv7+
    ids = [seeded_team[k]["id"]
           for k in ("lv7a", "lv7b", "lv7c", "lv8a", "lv8b")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    # Il gate NON deve produrre 423 con code=adventurer.level_too_low.
    if r.status_code == 423:
        detail = r.json().get("detail", {})
        assert detail.get("code") != "adventurer.level_too_low", (
            f"423 gate erroneously raised on level_too_low: {detail}"
        )
    # 201 (successo pieno) o altro errore non-level-gate: entrambi OK.
    # Documentiamo il response code per audit.
    print(f"[test_2] silent-monastery-5p HTTP={r.status_code} "
          f"detail_head={str(r.text)[:120]}")


def test_3_one_underleveled_blocks_whole_team(
    test_db, tester_auth, seeded_team,
):
    """Team 3p: 2×lv8 + 1×lv3 vs lich-sanctum (required_level=5).
    Basta un singolo membro sotto livello per bloccare."""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "lich-sanctum")
    ids = [seeded_team[k]["id"] for k in ("lv8a", "lv8b", "lv3")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    assert r.status_code == 423, r.text
    detail = r.json().get("detail", {})
    assert detail.get("code") == "adventurer.level_too_low", detail
    assert detail.get("min_required_level") == 5, detail
    below = detail.get("adventurers_below") or detail.get("offending_adventurers")
    assert len(below) == 1, f"expected 1 offender, got {below}"
    assert below[0]["level"] == 3


def test_4_fallback_reads_min_adventurer_level_when_required_level_zero(
    test_db, tester_auth, seeded_team, seeded_dungeons,
):
    """Dungeon con `required_level=0` e `min_adventurer_level=5`:
    il gate deve leggere 5 (fallback P0.3 rule 2)."""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "r165test-fallback-legacy")
    # Team 3p tutto lv4 → sotto min_adventurer_level=5
    ids = [seeded_team[k]["id"] for k in ("lv4a", "lv4b", "lv4c")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    assert r.status_code == 423, r.text
    detail = r.json().get("detail", {})
    assert detail.get("code") == "adventurer.level_too_low"
    assert detail.get("min_required_level") == 5, detail
    assert detail.get("dungeon_slug") == "r165test-fallback-legacy"


def test_5_no_gate_when_both_fields_absent(
    test_db, tester_auth, seeded_team, seeded_dungeons,
):
    """Dungeon senza `required_level` e senza `min_adventurer_level`,
    con `difficulty=1` → fallback finale 1 → nessun gate su team lv4."""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "r165test-nogate-legacy")
    ids = [seeded_team[k]["id"] for k in ("lv4a", "lv4b", "lv4c")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    # Non ci aspettiamo 423 adventurer.level_too_low: il gate è min=1.
    if r.status_code == 423:
        detail = r.json().get("detail", {})
        assert detail.get("code") != "adventurer.level_too_low", (
            f"gate scattato ma non doveva: {detail}"
        )


def test_6_legacy_only_dungeon_uses_min_adventurer_level(
    test_db, tester_auth, seeded_team, seeded_dungeons,
):
    """Dungeon "vecchio" con SOLO `min_adventurer_level=7` (nessun
    `required_level`) — simula il caso in cui P0.2 non è stato
    applicato su quel doc. Team lv4 → 423 con required=7 dal fallback."""
    base = _api_base()
    d = test_db.dungeons.find_one(
        {"slug": "r165test-legacy-only"}, {"_id": 0},
    )
    dungeon_id = d["id"]
    ids = [seeded_team[k]["id"] for k in ("lv4a", "lv4b", "lv4c")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    assert r.status_code == 423, r.text
    detail = r.json().get("detail", {})
    assert detail.get("code") == "adventurer.level_too_low"
    assert detail.get("min_required_level") == 7, detail


def test_7_payload_shape_contains_all_required_fields(
    test_db, tester_auth, seeded_team,
):
    """Verifica che il payload errore contiene:
    - code
    - source
    - min_required_level
    - adventurers_below (lista con id/name/level)
    - dungeon_slug
    - user_message (localizzato in italiano)"""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "world-tree-roots-5p")
    ids = [seeded_team[k]["id"]
           for k in ("lv4a", "lv4b", "lv4c", "lv3", "lv7a")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    assert r.status_code == 423
    detail = r.json()["detail"]
    for k in (
        "code", "source", "min_required_level",
        "adventurers_below", "dungeon_slug", "user_message",
    ):
        assert k in detail, f"missing key {k!r} in payload: {detail}"
    # adventurers_below shape
    for a in detail["adventurers_below"]:
        assert set(a.keys()) >= {"id", "name", "level"}, a
    # user_message localizzato IT
    assert "livello" in detail["user_message"].lower()
    assert isinstance(detail["min_required_level"], int)


# ═════════════════════════════════════════════════════════════════════
# FASE A.3 — Test rimozione fallback `difficulty` (D2)
# ═════════════════════════════════════════════════════════════════════


def test_A3_source_code_no_difficulty_fallback_in_resolver():
    """Verifica statica: la funzione `legacy_min_level_for_dungeon` NON
    referenzia più `_DUNGEON_DIFFICULTY_TO_MIN_LEVEL` come fallback.

    La costante può restare esportata a fini documentali/telemetria, ma
    NON deve comparire nel body della funzione resolver."""
    import inspect
    from app.expeditions import level_gate
    src = inspect.getsource(level_gate.legacy_min_level_for_dungeon)
    # Strip commenti e docstring per verificare solo il codice eseguibile.
    import ast
    tree = ast.parse(src)
    func_node = tree.body[0]
    if (isinstance(func_node.body[0], ast.Expr)
            and isinstance(func_node.body[0].value, ast.Constant)):
        func_node.body = func_node.body[1:]  # drop docstring
    code_only = ast.unparse(func_node)
    assert "_DUNGEON_DIFFICULTY_TO_MIN_LEVEL" not in code_only, (
        "REGRESSIONE D2: `legacy_min_level_for_dungeon` referenzia ancora "
        "la mappa difficulty come fallback nel codice eseguibile."
    )
    assert 'dungeon.get("difficulty"' not in code_only, (
        "REGRESSIONE D2: il resolver legge ancora `dungeon.get('difficulty')`."
    )
    assert "dungeon.get('difficulty'" not in code_only, (
        "REGRESSIONE D2: il resolver legge ancora `dungeon.get('difficulty')`."
    )


def test_A3_difficulty_only_dungeon_now_has_zero_gate(
    test_db, tester_auth, seeded_team, seeded_dungeons,
):
    """Dungeon con SOLO `difficulty=4` (nessun `required_level`, nessun
    `min_adventurer_level`).

    Pre-D2: fallback mappava difficulty=4 → gate=12 (team lv1-11 bloccati).
    Post-D2: gate=0 (accesso libero). Team lv3 deve poter entrare senza 423
    di level gate."""
    base = _api_base()
    d = test_db.dungeons.find_one(
        {"slug": "r165test-diff-only"}, {"_id": 0},
    )
    dungeon_id = d["id"]
    # Team 3p tutto lv3 (pre-D2 sarebbe stato bloccato con min=12)
    ids = [seeded_team[k]["id"] for k in ("lv3", "lv4a", "lv4b")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    # Non deve tornare 423 con code=adventurer.level_too_low.
    if r.status_code == 423:
        detail = r.json().get("detail", {})
        assert detail.get("code") != "adventurer.level_too_low", (
            f"REGRESSIONE D2: gate scattato ma fallback difficulty è "
            f"stato rimosso. Detail: {detail}"
        )


def test_A3_regression_team_lv4_still_blocked_on_worldtree_lv14(
    test_db, tester_auth, seeded_team,
):
    """Regression: dopo la rimozione del fallback difficulty, team lv4
    deve continuare a essere bloccato su dungeon `required_level=14`.
    Il gate `required_level` è la prima priorità e rimane attivo."""
    base = _api_base()
    dungeon_id = _dungeon_id_from_slug(test_db, "world-tree-roots-5p")
    ids = [seeded_team[k]["id"]
           for k in ("lv4a", "lv4b", "lv4c", "lv3", "lv7a")]
    r = _post_expedition(base, tester_auth["headers"], dungeon_id, ids)
    assert r.status_code == 423
    detail = r.json()["detail"]
    assert detail["code"] == "adventurer.level_too_low"
    assert detail["min_required_level"] == 14
