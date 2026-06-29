"""ROUND 13a — Backend tests for the Recovery + Lore Pack.

Validates:
  • dungeon count (32) + raid count (8) invariant.
  • every dungeon/raid has `lore_reviewed=True`.
  • every active item has `required_adventurer_level>=1` + `lore_reviewed=True`.
  • equip gate refuses Lv1 → Legendary (Lv12) with HTTP 423.
  • slug count distinct invariato (dungeons/raids/items).
  • `/api/inventory` payload contains no PII (no email, no raw user_id, no $oid).
  • `/api/dungeons` + `/api/raids/catalog` expose new lore fields.
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"

# Pre-seeded tester (see /app/memory/test_credentials.md).
TESTER_EMAIL = os.environ.get("TESTER_EMAIL", "tester@orbus.test")
TESTER_PASSWORD = os.environ.get("TESTER_PASSWORD", "password123")


def _login() -> str:
    r = requests.post(
        f"{API}/auth/login",
        json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def token() -> str:
    return _login()


# ────────────────────────────────────────────────────────────────────────────
# 1. Dungeon catalog: 32 entries, all lore_reviewed=True, lore fields present.
# ────────────────────────────────────────────────────────────────────────────
def test_r13a_01_dungeons_count_and_lore_reviewed(token):
    r = requests.get(f"{API}/dungeons", headers=_auth(token), timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    dungeons = body["dungeons"]
    assert len(dungeons) == 32, f"expected 32 dungeons, got {len(dungeons)}"
    not_reviewed = [d["slug"] for d in dungeons if not d.get("lore_reviewed")]
    assert not_reviewed == [], f"dungeons missing lore_reviewed: {not_reviewed}"


def test_r13a_02_dungeons_expose_lore_fields(token):
    r = requests.get(f"{API}/dungeons", headers=_auth(token), timeout=15)
    dungeons = r.json()["dungeons"]
    required_keys = {
        "name_it", "description_it", "lore_theme", "content_family",
        "is_new", "is_void_undead", "spoiler_level", "min_adventurer_level",
    }
    for d in dungeons:
        missing = required_keys - set(d.keys())
        assert not missing, f"dungeon {d['slug']} missing keys: {missing}"
    # Verify the 10 R11.3 Void/Undead dungeons are flagged.
    new_void_slugs = {
        "echoes-of-the-broken-thread", "shattered-seal-of-ergolat",
        "obelisks-of-the-void", "plague-warrens-of-irthe",
        "moonlit-strings-of-alevora", "ashkaroth-crypt-court",
        "eclipthra-veiled-sanctum", "gralca-tide-of-the-deep",
        "xal-zoraax-throat-of-silence", "tip-of-oblivion-trial",
    }
    by_slug = {d["slug"]: d for d in dungeons}
    for s in new_void_slugs:
        assert s in by_slug, f"new R11.3 dungeon missing: {s}"
        assert by_slug[s]["is_new"] is True, f"{s} not flagged is_new"
        assert by_slug[s]["is_void_undead"] is True, f"{s} not flagged is_void_undead"


# ────────────────────────────────────────────────────────────────────────────
# 2. Raid catalog: 8 entries, all lore_reviewed=True, boss_name on every raid.
# ────────────────────────────────────────────────────────────────────────────
def test_r13a_03_raids_count_and_lore_reviewed(token):
    r = requests.get(f"{API}/raids/catalog", headers=_auth(token), timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    raids = body["raid_dungeons"]
    assert len(raids) == 8, f"expected 8 raids, got {len(raids)}"
    not_reviewed = [d["slug"] for d in raids if not d.get("lore_reviewed")]
    assert not_reviewed == [], f"raids missing lore_reviewed: {not_reviewed}"


def test_r13a_04_raids_expose_lore_fields(token):
    r = requests.get(f"{API}/raids/catalog", headers=_auth(token), timeout=15)
    raids = r.json()["raid_dungeons"]
    required_keys = {
        "name_it", "lore_theme", "content_family",
        "boss_name", "is_new", "is_void_undead", "spoiler_level",
        "min_adventurer_level",
    }
    for d in raids:
        missing = required_keys - set(d.keys())
        assert not missing, f"raid {d['slug']} missing keys: {missing}"
        # boss_name MUST be a non-empty string (R13a invariant).
        assert d["boss_name"], f"raid {d['slug']} has empty boss_name"


# ────────────────────────────────────────────────────────────────────────────
# 3. Item catalog: every active item has required_adventurer_level>=1 explicit
#    + lore_reviewed=True.
# ────────────────────────────────────────────────────────────────────────────
def test_r13a_05_items_required_level_and_reviewed(token):
    r = requests.get(f"{API}/items", headers=_auth(token), timeout=15)
    assert r.status_code == 200, r.text
    items = r.json().get("items", [])
    assert len(items) >= 100, f"expected >=100 items catalog, got {len(items)}"
    bad_lvl = [i["slug"] for i in items if not isinstance(i.get("required_adventurer_level"), int) or i["required_adventurer_level"] < 1]
    assert bad_lvl == [], f"items without explicit required_adventurer_level>=1: {bad_lvl[:5]}"
    not_reviewed = [i["slug"] for i in items if not i.get("lore_reviewed")]
    assert not_reviewed == [], f"items missing lore_reviewed: {not_reviewed[:5]}"


def test_r13a_06_items_display_name_it_and_lore_tags(token):
    r = requests.get(f"{API}/items", headers=_auth(token), timeout=15)
    items = r.json().get("items", [])
    missing_display = [i["slug"] for i in items if not i.get("display_name_it")]
    assert missing_display == [], f"items missing display_name_it: {missing_display[:5]}"
    # Voidpiercer Bow must have hand-written Italian display name.
    voidpiercer = next((i for i in items if i["slug"] == "voidpiercer-bow"), None)
    if voidpiercer is not None:
        assert voidpiercer["display_name_it"] == "Arco Trafittore del Vuoto"
        assert voidpiercer["required_adventurer_level"] == 8
        assert "vuoto" in (voidpiercer.get("lore_tags") or [])


# ────────────────────────────────────────────────────────────────────────────
# 4. Equip gate enforcement: Lv1 adv MUST NOT equip a Lv12 Legendary item.
# ────────────────────────────────────────────────────────────────────────────
def test_r13a_07_lv1_cannot_equip_legendary(token):
    # Find a Lv1 adventurer of the tester guild.
    advs = requests.get(f"{API}/adventurers", headers=_auth(token), timeout=15).json().get("adventurers", [])
    lv1 = next((a for a in advs if a.get("level", 1) == 1 and not a.get("is_retired")), None)
    if lv1 is None:
        pytest.skip("tester has no Lv1 adventurer available for equip gate test")

    # Find a legendary item with required_adventurer_level >= 12 in inventory.
    inv = requests.get(f"{API}/inventory", headers=_auth(token), timeout=15).json()
    rows = inv.get("inventory", []) or inv.get("rows", []) or inv
    if not isinstance(rows, list):
        rows = rows.get("items", []) if isinstance(rows, dict) else []
    legendary_row = None
    for r in rows:
        item = r.get("item") or {}
        if item.get("rarity") == "Legendary" and (item.get("required_adventurer_level") or 0) >= 12:
            legendary_row = r
            break
    if legendary_row is None:
        pytest.skip("tester inventory has no Legendary Lv12 item; cannot exercise the gate")

    # Try to equip → expect 423 with structured detail.
    r = requests.post(
        f"{API}/equipment/equip",
        headers=_auth(token),
        json={
            "adventurer_id": lv1["id"],
            "inventory_item_id": legendary_row.get("id") or legendary_row.get("instance_id"),
        },
        timeout=15,
    )
    assert r.status_code == 423, f"expected 423 got {r.status_code}: {r.text[:200]}"
    body = r.json()
    detail = body.get("detail")
    # Accept either string or structured dict (both shapes are valid).
    if isinstance(detail, dict):
        code = detail.get("code") or ""
    else:
        code = str(detail)
    assert "required_level" in code or "required_adventurer_level" in code, f"unexpected detail: {body}"


# ────────────────────────────────────────────────────────────────────────────
# 5. Slug count invariants — content catalog is additive, no regressions.
# ────────────────────────────────────────────────────────────────────────────
def test_r13a_08_slug_count_invariants(token):
    dungeons = requests.get(f"{API}/dungeons", headers=_auth(token), timeout=15).json()["dungeons"]
    raids = requests.get(f"{API}/raids/catalog", headers=_auth(token), timeout=15).json()["raid_dungeons"]
    items = requests.get(f"{API}/items", headers=_auth(token), timeout=15).json().get("items", [])
    assert len(set(d["slug"] for d in dungeons)) == len(dungeons), "duplicate dungeon slugs"
    assert len(set(d["slug"] for d in raids)) == len(raids), "duplicate raid slugs"
    assert len(set(i["slug"] for i in items)) == len(items), "duplicate item slugs"


# ────────────────────────────────────────────────────────────────────────────
# 6. PII guard — /api/inventory must not leak email / raw owner_user_id / $oid.
# ────────────────────────────────────────────────────────────────────────────
def test_r13a_09_no_pii_in_inventory(token):
    r = requests.get(f"{API}/inventory", headers=_auth(token), timeout=15)
    assert r.status_code == 200, r.text
    body_str = r.text.lower()
    assert "@orbus.test" not in body_str, "PII leak: tester email in /api/inventory"
    assert '"password' not in body_str, "PII leak: password field in /api/inventory"
    assert "$oid" not in body_str, "PII leak: raw MongoDB ObjectId in /api/inventory"
    assert "owner_user_id" not in body_str, "PII leak: owner_user_id in /api/inventory"
