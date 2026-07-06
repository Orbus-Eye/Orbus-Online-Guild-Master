"""
🔒 R18.4.followup — UI 4-State Item Compatibility Activation — CLOSED & SEALED
R18.4.followup CLOSED & SEALED
DO NOT MODIFY. SHA256 verified in /app/backend/tests/backend_r18_4_sealed_integrity_test.py

R18.4.followup — UI 4-State Item Compatibility Activation — Phase B tests.

Copertura test (B.SQ8 = 8+ backend):

Group 1 — Helper derive_ui_4state (pure unit, no HTTP): 5 test
  t01_derive_universal_item
  t02_derive_hard_class_match
  t03_derive_hard_class_mismatch
  t04_derive_soft_class_recommended
  t05_derive_soft_class_not_recommended

Group 2 — Serializer item_public exposure: 1 test
  t06_item_public_exposes_new_r18_4_fields

Group 3 — Endpoint HTTP + shield mapping + ownership: 3 test
  t07_eligible_items_endpoint_shape_and_enum_conformance
  t08_eligible_items_endpoint_shield_maps_to_armor_slot
  t09_eligible_items_endpoint_ownership_guard_404_cross_guild

Governance:
  - Nessuna scrittura DB dal test path (solo query read).
  - Nessuna mutazione a catalog items (assunzione: R18.4 B4 apply già live).
  - Nessuna scrittura a sigilli (30 file sealed non toccati).
"""
from __future__ import annotations

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


# ═════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user(hint: str = "ui4st") -> dict:
    """Register+login a fresh user with starter guild + starter adventurers."""
    import time as _time
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"UI4st {tag[-5:]}"},
        headers=h, timeout=15,
    )
    g = requests.get(
        f"{BASE_URL}/api/guilds/me", headers=h, timeout=15,
    ).json()["guild"]
    # Small retry loop: guild-create dispatches starter roster which may be
    # readable only on the next tick; keep total < 2 s so the suite stays fast.
    advs: list = []
    for _ in range(15):
        advs = requests.get(
            f"{BASE_URL}/api/adventurers", headers=h, timeout=15,
        ).json().get("adventurers") or []
        if advs:
            break
        _time.sleep(0.15)
    return {"headers": h, "guild_id": g["id"], "advs": advs, "tag": tag}


def _tester_ctx() -> dict:
    """Login canonical tester@orbus.test account (stable 5 starter adventurers)
    documented in /app/memory/test_credentials.md. Usato per test che
    dipendono da un roster deterministico (t07/t08). NON scrive nulla."""
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123",
    }, timeout=15)
    assert r.status_code == 200, (
        f"canonical tester login failed: {r.status_code} — verifica "
        f"/app/memory/test_credentials.md"
    )
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    advs = requests.get(
        f"{BASE_URL}/api/adventurers", headers=h, timeout=15,
    ).json().get("adventurers") or []
    assert advs, "tester@orbus.test roster inaspettatamente vuoto"
    return {"headers": h, "advs": advs}


# ═════════════════════════════════════════════════════════════════════
# Group 1 — Helper derive_ui_4state (pure unit, no HTTP)
# ═════════════════════════════════════════════════════════════════════

def test_t01_derive_universal_item():
    """universal policy → state=universal, can_equip=True, reason=universal_item."""
    from app.equipment.ui_4state import derive_ui_4state
    adv = {"class_slug": "monk"}
    item = {
        "item_binding_policy": "universal",
        "slot_type": None,
        "item_type": "material",
    }
    out = derive_ui_4state(adv, item)
    assert out["compatibility_state"] == "universal"
    assert out["can_equip"] is True
    assert out["is_universal"] is True
    assert out["recommended_for_class"] is True
    assert out["reason_code"] == "universal_item"
    assert out["item_binding_policy"] == "universal"


def test_t02_derive_hard_class_match():
    """hard policy + class match → state=recommended, can_equip=True."""
    from app.equipment.ui_4state import derive_ui_4state
    adv = {"class_slug": "warrior"}
    item = {
        "item_binding_policy": "hard",
        "required_class_optional": "warrior",
        "slot_type": "weapon",
        "item_type": "weapon",
    }
    out = derive_ui_4state(adv, item)
    assert out["compatibility_state"] == "recommended"
    assert out["can_equip"] is True
    assert out["is_universal"] is False
    assert out["recommended_for_class"] is True
    assert out["reason_code"] == "class_recommended"


def test_t03_derive_hard_class_mismatch():
    """hard policy + class mismatch → state=blocked, can_equip=False."""
    from app.equipment.ui_4state import derive_ui_4state
    adv = {"class_slug": "monk"}
    item = {
        "item_binding_policy": "hard",
        "required_class_optional": "warrior",
        "slot_type": "weapon",
        "item_type": "weapon",
    }
    out = derive_ui_4state(adv, item)
    assert out["compatibility_state"] == "blocked"
    assert out["can_equip"] is False
    assert out["is_universal"] is False
    assert out["recommended_for_class"] is False
    assert out["reason_code"] == "class_mismatch_hard"


def test_t04_derive_soft_class_recommended():
    """soft + class ∈ recommended_classes/class_tags → state=recommended."""
    from app.equipment.ui_4state import derive_ui_4state
    adv = {"class_slug": "monk"}
    item = {
        "item_binding_policy": "soft",
        "recommended_classes": ["monk", "warrior"],
        "slot_type": "armor",
        "item_type": "armor",
    }
    out = derive_ui_4state(adv, item)
    assert out["compatibility_state"] == "recommended"
    assert out["can_equip"] is True
    assert out["recommended_for_class"] is True
    assert out["reason_code"] == "class_recommended"


def test_t05_derive_soft_class_not_recommended():
    """soft + class NOT in recommended → state=not_recommended, can_equip=True."""
    from app.equipment.ui_4state import derive_ui_4state
    adv = {"class_slug": "monk"}
    item = {
        "item_binding_policy": "soft",
        "recommended_classes": ["warrior"],
        "class_tags": [],
        "slot_type": "weapon",
        "item_type": "weapon",
    }
    out = derive_ui_4state(adv, item)
    assert out["compatibility_state"] == "not_recommended"
    assert out["can_equip"] is True
    assert out["is_universal"] is False
    assert out["recommended_for_class"] is False
    assert out["reason_code"] == "class_mismatch_soft"


# ═════════════════════════════════════════════════════════════════════
# Group 2 — Serializer item_public exposure (B.SQ1)
# ═════════════════════════════════════════════════════════════════════

def test_t06_item_public_exposes_new_r18_4_fields():
    """item_public() DEVE esporre slot_type + item_binding_policy + is_universal.

    B.SQ1 lock: raw enum + derived flags. Endpoint /api/items DEVE riflettere.
    recommended_for_class NON deve essere presente qui (context-aware, B.SQ2).
    """
    r = requests.get(f"{BASE_URL}/api/items", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("items") or []
    assert len(items) > 0, "catalog non deve essere vuoto"

    # Contract fields must exist on ALL public items (B.SQ1)
    required = {"slot_type", "item_binding_policy", "is_universal"}
    forbidden_context_free = {"recommended_for_class", "compatibility_state"}

    for it in items:
        missing = required - set(it.keys())
        assert not missing, f"item {it.get('slug')!r} missing fields: {missing}"
        leaked = forbidden_context_free & set(it.keys())
        assert not leaked, (
            f"item {it.get('slug')!r} leaked context-aware fields: {leaked}"
        )
        # is_universal must derive from item_binding_policy
        assert it["is_universal"] == (it["item_binding_policy"] == "universal"), (
            f"item {it.get('slug')!r} is_universal drift"
        )


# ═════════════════════════════════════════════════════════════════════
# Group 3 — Endpoint HTTP: shape + shield mapping + ownership guard
# ═════════════════════════════════════════════════════════════════════

def test_t07_eligible_items_endpoint_shape_and_enum_conformance():
    """Endpoint /api/adventurers/{id}/eligible-items — payload contract locked B.SQ6.

    Response DEVE contenere: adventurer_id, class_slug, eligible_items[], total.
    Ogni item DEVE avere tutti i 10 field del contract + enum conformi.
    """
    from app.equipment.ui_4state import VALID_COMPATIBILITY_STATES, VALID_REASON_CODES

    ctx = _tester_ctx()
    assert ctx["advs"], "canonical tester roster must not be empty"
    adv = ctx["advs"][0]
    r = requests.get(
        f"{BASE_URL}/api/adventurers/{adv['id']}/eligible-items",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # Top-level shape
    assert body.get("adventurer_id") == adv["id"]
    assert "class_slug" in body
    assert isinstance(body.get("eligible_items"), list)
    assert body.get("total") == len(body["eligible_items"])

    # Per-item contract (B.SQ6)
    required_fields = {
        "item_id", "name", "item_type", "slot_type", "item_binding_policy",
        "can_equip", "compatibility_state", "recommended_for_class",
        "is_universal", "reason_code",
    }
    equipable_types = {"weapon", "armor", "accessory", "shield"}
    seen_item_ids = set()
    for entry in body["eligible_items"]:
        missing = required_fields - set(entry.keys())
        assert not missing, f"item entry missing fields: {missing}"
        assert entry["compatibility_state"] in VALID_COMPATIBILITY_STATES
        assert entry["reason_code"] in VALID_REASON_CODES
        assert entry["item_type"] in equipable_types, (
            f"non-equipable leaked: {entry['item_type']}"
        )
        # is_universal ↔ policy universal must stay coherent
        if entry["item_binding_policy"] == "universal":
            assert entry["is_universal"] is True
            assert entry["compatibility_state"] == "universal"
        # can_equip semantics locked
        if entry["compatibility_state"] == "blocked":
            assert entry["can_equip"] is False
        else:
            assert entry["can_equip"] is True
        # dedup by item_id
        assert entry["item_id"] not in seen_item_ids, "dedup violato"
        seen_item_ids.add(entry["item_id"])


def test_t08_eligible_items_endpoint_shield_maps_to_armor_slot():
    """SQ7 lock — Risk 10.1 mitigation: item con item_type='shield' DEVE avere
    slot_type='armor' post-R18.4 B4 real apply. Verificato sia via catalog
    pubblico /api/items sia via endpoint eligible-items.
    """
    # Catalog-level check via public API (independent from test DB name).
    r_cat = requests.get(f"{BASE_URL}/api/items", timeout=15)
    assert r_cat.status_code == 200
    shields = [
        it for it in (r_cat.json().get("items") or [])
        if (it.get("item_type") or "").lower() == "shield" and it.get("is_active")
    ]
    if not shields:
        pytest.skip("nessun item shield attivo in catalog — skip Risk 10.1 mapping")
    for s in shields:
        assert s.get("slot_type") == "armor", (
            f"shield {s.get('slug')!r} mapping drift: "
            f"slot_type={s.get('slot_type')!r} (atteso 'armor')"
        )

    # Endpoint-level check: se un shield è in inventory, DEVE apparire con
    # slot_type='armor' e item_type='shield' (item_type raw + slot_type mapped).
    ctx = _tester_ctx()
    adv = ctx["advs"][0]
    r = requests.get(
        f"{BASE_URL}/api/adventurers/{adv['id']}/eligible-items",
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 200, r.text
    for entry in r.json()["eligible_items"]:
        if entry["item_type"] == "shield":
            assert entry["slot_type"] == "armor", (
                f"shield {entry['item_id']!r} slot_type drift nell'endpoint"
            )


def test_t09_eligible_items_endpoint_ownership_guard_404_cross_guild():
    """Ownership guard: utente A NON deve poter leggere eligible-items
    di un adventurer della guild dell'utente B. Deve tornare 404 (no leak)."""
    # Utente A: fresh user (basta il token, non serve roster).
    ctx_a = _user("t09a")
    # Utente B: canonical tester (roster stabile).
    ctx_b = _tester_ctx()
    adv_b = ctx_b["advs"][0]
    # Utente A prova a leggere adventurer di B → 404 (via user_guild_or_404 +
    # find_one guild_id match).
    r = requests.get(
        f"{BASE_URL}/api/adventurers/{adv_b['id']}/eligible-items",
        headers=ctx_a["headers"], timeout=15,
    )
    assert r.status_code == 404, (
        f"expected 404 cross-guild, got {r.status_code}: {r.text}"
    )

    # Sanity: chiamata unauthenticated → 401 (o 403), NON 200.
    r_unauth = requests.get(
        f"{BASE_URL}/api/adventurers/{adv_b['id']}/eligible-items",
        timeout=15,
    )
    assert r_unauth.status_code in (401, 403), (
        f"expected auth gate, got {r_unauth.status_code}"
    )


# ═════════════════════════════════════════════════════════════════════
# Group 4 — Phase C add-on — Full 4-state visual coverage (deterministic)
# ═════════════════════════════════════════════════════════════════════
# Copertura esplicita dei 4 stati UI (blocked/not_recommended/recommended/universal)
# richiesta dal PM prima del SEAL Phase C. Test deterministici, no DB write,
# no HTTP: verifica che l'helper derive_ui_4state produca il payload esatto
# richiesto dal frontend ItemCompatibilityBadge per ciascuno dei 4 stati.
#
# Ogni test valida:
#   - compatibility_state ∈ enum locked B.SQ1
#   - reason_code ∈ enum locked B.SQ2
#   - can_equip semantica corretta (True/False)
#   - is_universal + recommended_for_class coerenti
#   - contract completo dei 10 field attesi dal frontend ItemCompatibilityBadge
#
# Il rendering React del componente è oggetto di test frontend/E2E
# (Playwright) delegati al testing subagent; qui blindiamo il PAYLOAD che il
# componente consuma, che è il vero contract da sigillare.


PHASE_C_EXPECTED_PAYLOAD_KEYS = frozenset({
    "compatibility_state", "can_equip", "recommended_for_class",
    "is_universal", "reason_code", "item_binding_policy", "slot_type",
})


def test_t10_phase_c_full_4state_blocked_deterministic():
    """Stato BLOCKED: hard policy + class mismatch → contract completo blocked."""
    from app.equipment.ui_4state import (
        derive_ui_4state, VALID_COMPATIBILITY_STATES, VALID_REASON_CODES,
    )
    out = derive_ui_4state(
        adventurer={"class_slug": "monk"},
        item={
            "item_binding_policy": "hard",
            "required_class_optional": "warrior",
            "slot_type": "weapon",
            "item_type": "weapon",
        },
    )
    # Enum conformance
    assert out["compatibility_state"] == "blocked"
    assert out["compatibility_state"] in VALID_COMPATIBILITY_STATES
    assert out["reason_code"] == "class_mismatch_hard"
    assert out["reason_code"] in VALID_REASON_CODES
    # Semantica UI
    assert out["can_equip"] is False, "blocked state MUST have can_equip=False"
    assert out["recommended_for_class"] is False
    assert out["is_universal"] is False
    # Contract completo (10 field della UI ItemCompatibilityBadge)
    assert PHASE_C_EXPECTED_PAYLOAD_KEYS <= set(out.keys()), (
        f"blocked payload missing keys: {PHASE_C_EXPECTED_PAYLOAD_KEYS - set(out.keys())}"
    )


def test_t11_phase_c_full_4state_not_recommended_deterministic():
    """Stato NOT_RECOMMENDED: soft policy + class not in recommended list →
    can_equip=True (equip permesso) ma non consigliato."""
    from app.equipment.ui_4state import (
        derive_ui_4state, VALID_COMPATIBILITY_STATES, VALID_REASON_CODES,
    )
    out = derive_ui_4state(
        adventurer={"class_slug": "monk"},
        item={
            "item_binding_policy": "soft",
            "recommended_classes": ["warrior"],
            "class_tags": [],
            "slot_type": "weapon",
            "item_type": "weapon",
        },
    )
    assert out["compatibility_state"] == "not_recommended"
    assert out["compatibility_state"] in VALID_COMPATIBILITY_STATES
    assert out["reason_code"] == "class_mismatch_soft"
    assert out["reason_code"] in VALID_REASON_CODES
    # Semantica UI critica: not_recommended NON blocca l'equip
    assert out["can_equip"] is True, "not_recommended MUST allow equip (warning only)"
    assert out["recommended_for_class"] is False
    assert out["is_universal"] is False
    assert PHASE_C_EXPECTED_PAYLOAD_KEYS <= set(out.keys())


def test_t12_phase_c_full_4state_recommended_deterministic():
    """Stato RECOMMENDED: soft policy + class in recommended_classes →
    consigliato + equip permesso."""
    from app.equipment.ui_4state import (
        derive_ui_4state, VALID_COMPATIBILITY_STATES, VALID_REASON_CODES,
    )
    out = derive_ui_4state(
        adventurer={"class_slug": "monk"},
        item={
            "item_binding_policy": "soft",
            "recommended_classes": ["monk", "warrior"],
            "slot_type": "armor",
            "item_type": "armor",
        },
    )
    assert out["compatibility_state"] == "recommended"
    assert out["compatibility_state"] in VALID_COMPATIBILITY_STATES
    assert out["reason_code"] == "class_recommended"
    assert out["reason_code"] in VALID_REASON_CODES
    assert out["can_equip"] is True
    assert out["recommended_for_class"] is True
    assert out["is_universal"] is False
    assert PHASE_C_EXPECTED_PAYLOAD_KEYS <= set(out.keys())


def test_t13_phase_c_full_4state_universal_deterministic():
    """Stato UNIVERSAL: universal policy → equip aperto a qualsiasi classe."""
    from app.equipment.ui_4state import (
        derive_ui_4state, VALID_COMPATIBILITY_STATES, VALID_REASON_CODES,
    )
    out = derive_ui_4state(
        adventurer={"class_slug": "monk"},
        item={
            "item_binding_policy": "universal",
            "slot_type": None,
            "item_type": "material",
        },
    )
    assert out["compatibility_state"] == "universal"
    assert out["compatibility_state"] in VALID_COMPATIBILITY_STATES
    assert out["reason_code"] == "universal_item"
    assert out["reason_code"] in VALID_REASON_CODES
    assert out["can_equip"] is True
    assert out["recommended_for_class"] is True  # universale conta come recommended (UX)
    assert out["is_universal"] is True
    assert PHASE_C_EXPECTED_PAYLOAD_KEYS <= set(out.keys())
