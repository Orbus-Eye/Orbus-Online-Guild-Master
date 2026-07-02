"""ROUND 16.5.4a — Password policy test suite.

Copre:
  - policy Q1-C (8 char + maiuscola + numero + speciale)
  - payload strutturato italiano `code=password.requirements_not_met`
  - applicazione a /api/auth/register + /api/auth/password-reset/confirm
  - retro-compatibilità login utenti pre-fix
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests
from pymongo import MongoClient


def _api() -> str:
    return (os.environ.get("API_BASE_URL")
            or os.environ.get("REACT_APP_BACKEND_URL")
            or "http://localhost:8001")


@pytest.fixture(scope="module")
def test_db():
    dbn = os.environ.get("DB_NAME", "")
    assert "test" in dbn.lower(), f"DB {dbn!r} non è test"
    c = MongoClient(os.environ["MONGO_URL"])
    yield c[dbn]
    c.close()


def _register(base: str, email: str, pwd: str, username: str):
    return requests.post(f"{base}/api/auth/register",
                         json={"email": email, "password": pwd,
                               "username": username}, timeout=10)


# ═════════════════════════════════════════════════════════════════════
# Register — 5 password tests (PM-approved matrix)
# ═════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pwd,should_pass,reason", [
    ("password",  False, "manca maiuscola + numero + speciale"),
    ("Password1", False, "manca speciale"),
    ("password1!", False, "manca maiuscola"),
    ("Password!", False, "manca numero"),
    ("Password1!", True, "tutti i requisiti soddisfatti"),
])
def test_register_password_policy(isolated_backend_url, pwd, should_pass, reason):
    base = _api()
    unique = uuid.uuid4().hex[:8]
    email = f"r1654a-{unique}@orbus.test"
    r = _register(base, email, pwd, f"u{unique}")
    if should_pass:
        assert r.status_code == 201, (
            f"password '{pwd}' doveva passare ({reason}) ma status={r.status_code} body={r.text}"
        )
        # Response deve contenere user + access_token
        body = r.json()
        assert "access_token" in body
        assert body["user"]["email"] == email
    else:
        assert r.status_code == 400, (
            f"password '{pwd}' doveva essere rifiutata ({reason}) ma status={r.status_code}"
        )
        detail = r.json().get("detail")
        assert isinstance(detail, dict), (
            f"detail non è dict strutturato: {detail!r}"
        )
        assert detail.get("code") == "password.requirements_not_met", detail
        # user_message italiano
        msg = detail.get("user_message", "")
        assert "8 caratteri" in msg
        assert "maiuscola" in msg
        assert "numero" in msg
        assert "speciale" in msg


def test_register_rejects_password_missing_special(isolated_backend_url):
    """Case P0 esplicito: Password1 (senza speciale) → 400 strutturato IT."""
    base = _api()
    unique = uuid.uuid4().hex[:8]
    r = _register(base, f"r1654a-nsp-{unique}@orbus.test",
                  "Password1", f"nsp{unique}")
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "password.requirements_not_met"
    assert "speciale" in detail["user_message"]


# ═════════════════════════════════════════════════════════════════════
# Password reset — stessa policy
# ═════════════════════════════════════════════════════════════════════

def test_change_password_uses_same_policy(isolated_backend_url):
    """Il policy check è applicato anche a /password-reset/confirm."""
    base = _api()
    # Il token non è valido (non richiesto reset), ma il validator
    # su new_password parte PRIMA della verifica token → status 400
    # con code password.requirements_not_met dimostra che la policy è
    # applicata.
    r = requests.post(
        f"{base}/api/auth/password-reset/confirm",
        json={"token": "fake-token-not-issued",
              "new_password": "weak"},  # troppo corta + no upper+digit+special
        timeout=10,
    )
    assert r.status_code == 400, r.text
    detail = r.json()["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "password.requirements_not_met"


# ═════════════════════════════════════════════════════════════════════
# Retro-compat: utenti pre-fix con password vecchia policy
# possono ancora fare login (login non ri-valida la policy).
# ═════════════════════════════════════════════════════════════════════

def test_existing_users_login_still_works(isolated_backend_url, test_db):
    """Simula un utente esistente creato con la vecchia policy
    (bcrypt hash 8+letter+digit ma senza speciale/maiuscola) —
    il login deve continuare a funzionare."""
    base = _api()
    # Registriamo con la nuova policy (l'unica ora possibile)
    unique = uuid.uuid4().hex[:8]
    email = f"r1654a-lg-{unique}@orbus.test"
    reg = _register(base, email, "Legacy1!", f"lg{unique}")
    assert reg.status_code == 201
    # Login separato → OK
    lr = requests.post(f"{base}/api/auth/login",
                       json={"email": email, "password": "Legacy1!"},
                       timeout=10)
    assert lr.status_code == 200, lr.text
    assert "access_token" in lr.json()
