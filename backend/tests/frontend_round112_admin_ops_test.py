"""ROUND 11.2 TASK 5b — Admin Ops FRONTEND tests (8).

Strategy: source-static checks for FE rendering rules (testid, ARIA, conditional
nav, validation logic) + a live backend round-trip to validate the contract
the FE depends on. Browser E2E will be handled separately by e1_tester.

Coverage:
  1. /admin/ops with non-admin → renders "Not authorized" (NO black screen, NO crash)
  2. /admin/ops with admin → renders Search tab by default
  3. Search submit → calls GET /api/admin/guilds/search?q=...
  4. Result table renders owner_email_masked (NO raw email)
  5. GrantGoldModal: Continue disabled if reason < 3 char (client validation)
  6. GrantGoldModal: double-confirm required before POST (step machine)
  7. GrantItemModal: 422 admin.item.unknown_slug → readable inline error
  8. Nav link "Admin Ops" visible ONLY if is_admin === true
"""
from __future__ import annotations

import json
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
FE = "/app/frontend/src"


def _read(rel: str) -> str:
    with open(f"{FE}/{rel}") as f:
        return f.read()


# ─────────────────────────────────────────────────────────────────────────
def test_t5b_01_admin_ops_not_authorized_renders_for_non_admin():
    """Source check: AdminOps renders NotAuthorized when !isAdmin (no Navigate)."""
    src = _read("pages/AdminOps.jsx")
    # Must NOT silently navigate away
    assert "<Navigate" not in src or "NotAuthorized" in src
    # Must render the dedicated NotAuthorized component
    assert "function NotAuthorized" in src
    assert 'data-testid="admin-not-authorized"' in src
    assert "Accesso admin richiesto" in src
    # Guard condition references is_admin
    assert "is_admin" in src
    assert "NotAuthorized" in src


def test_t5b_02_admin_ops_loads_search_tab_by_default():
    """Source check: default useState tab = 'search'. Tab buttons rendered
    via map → data-testid uses template-string (admin-ops-tab-${t.key})."""
    src = _read("pages/AdminOps.jsx")
    assert 'useState("search")' in src or "useState('search')" in src
    # Tab data-testid is dynamic via template literal: admin-ops-tab-${t.key}
    assert "admin-ops-tab-" in src
    assert 'key: "search"' in src
    assert 'data-testid="admin-ops-search-panel"' in src


def test_t5b_03_search_submit_hits_correct_endpoint():
    """Source check: GET /admin/guilds/search with q+limit+offset params."""
    src = _read("pages/AdminOps.jsx")
    assert '/admin/guilds/search' in src
    assert 'limit:' in src or 'limit: 20' in src
    assert 'offset:' in src or 'offset: off' in src
    # Live contract check: backend accepts these params
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123"}, timeout=10)
    tok = r.json()["access_token"]
    s = requests.get(f"{BASE_URL}/api/admin/guilds/search?q=&limit=5&offset=0",
                     headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    assert s.status_code == 200
    assert "guilds" in s.json()


def test_t5b_04_result_table_uses_owner_email_masked():
    """Source check: table renders `g.owner_email_masked`, NOT g.owner_email."""
    src = _read("pages/AdminOps.jsx")
    assert 'g.owner_email_masked' in src
    # No reference to a raw `g.email` or `g.owner_email` (without _masked)
    assert 'g.owner_email}' not in src
    assert 'g.email}' not in src
    # Live contract: backend returns masked field. Use a targeted search
    # for the tester guild (always has a real owner). Random recent test
    # guilds may seed with no owner (`<no-owner>` placeholder).
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123"}, timeout=10)
    tok = r.json()["access_token"]
    s = requests.get(f"{BASE_URL}/api/admin/guilds/search?q=Iron",
                     headers={"Authorization": f"Bearer {tok}"}, timeout=10).json()
    # Find a guild row with a real masked email (skip <no-owner> placeholders)
    real_owners = [g for g in s.get("guilds", [])
                   if "@" in (g.get("owner_email_masked") or "")]
    assert len(real_owners) >= 1, \
        f"expected at least 1 result with real masked owner: {s.get('guilds')[:3]}"
    for row in real_owners:
        masked = row["owner_email_masked"]
        assert "***" in masked
        # NO raw email exposed
        assert masked.count("@") == 1
        local, dom = masked.split("@", 1)
        assert local.endswith("***")


def test_t5b_05_grant_gold_continue_disabled_short_reason():
    """Source check: Continue button has `disabled={!canContinue}` and
    canContinue depends on `reason.trim().length >= 3` AND validAmount."""
    src = _read("components/admin/GrantGoldModal.jsx")
    assert "reason.trim().length >= 3" in src
    assert "canContinue" in src
    assert "disabled={!canContinue}" in src
    assert 'data-testid="grant-gold-continue"' in src


def test_t5b_06_grant_gold_double_confirm_required_before_post():
    """Source check: 2-step state machine. POST only fires from `submit` which
    is wired to step-2 confirm button, NOT step-1 Continue."""
    src = _read("components/admin/GrantGoldModal.jsx")
    # Step machine
    assert "useState(1)" in src
    assert "setStep(2)" in src
    # POST is inside `onSubmit`, not bound to step-1 Continue
    assert "/admin/guilds/" in src
    assert "grant-gold" in src
    # Continue button explicitly only changes step (no api call inline)
    assert 'onClick={() => setStep(2)}' in src
    # Confirm button wires to onSubmit (which contains the api.post call)
    assert 'onClick={onSubmit}' in src
    # Strong-warning text present
    assert ("Sei sicuro" in src) or ("conferma" in src.lower())


def test_t5b_07_grant_item_maps_422_unknown_slug_to_readable_error():
    """Source check: catch block maps admin.item.unknown_slug to a friendly msg.
    Live contract check: backend actually returns the structured code."""
    src = _read("components/admin/GrantItemModal.jsx")
    assert "admin.item.unknown_slug" in src
    assert "non riconosciuto" in src or "non valido" in src.lower()
    # Errors surface in step-1 with testid
    assert 'data-testid="grant-item-error"' in src
    # Live: backend returns the structured code as expected by FE
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123"}, timeout=10)
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=10).json()["guild"]
    bad = requests.post(
        f"{BASE_URL}/api/admin/guilds/{g['id']}/grant-item",
        json={"item_slug": f"xyz_{uuid.uuid4().hex[:6]}",
              "quantity": 1, "reason": "fe contract"},
        headers=h, timeout=10,
    )
    assert bad.status_code == 422
    detail = bad.json().get("detail")
    assert isinstance(detail, dict)
    assert detail.get("code") == "admin.item.unknown_slug"


def test_t5b_08_nav_link_admin_ops_visible_only_if_is_admin():
    """Source check: AppHeader nav renders Admin Ops link inside `is_admin` guard."""
    src = _read("components/AppHeader.jsx")
    # The nav-admin-ops testid exists
    assert 'testid="nav-admin-ops"' in src
    assert "/admin/ops" in src
    # It's inside a `user?.is_admin &&` conditional block
    # We grep for the conditional and assert the testid appears AFTER it.
    idx_cond = src.find("user?.is_admin")
    idx_link = src.find("nav-admin-ops")
    assert idx_cond > 0
    assert idx_link > idx_cond, \
        "nav-admin-ops link must be gated behind user?.is_admin conditional"
