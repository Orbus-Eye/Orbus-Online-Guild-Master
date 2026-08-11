"""FASE 9 A1 — l'endpoint avatar esercitato DAVVERO (TestClient, no Mongo).

Il test di Fase 6 copriva solo `sniff_image_ext`: l'endpoint non era mai
stato chiamato end-to-end e il bug player-facing (403 CSRF sul client
axios "nudo") è passato inosservato. Qui montiamo l'app COMPLETA
(create_app: middleware CSRF inclusi) con auth override e db finto, e
verifichiamo l'acceptance del mandato:

    PNG → 200 · JPEG → 200 · WEBP → 200 · SVG → 422 · >2MB → 413
    CSRF header assente/stantio con cookie auth → 403 auth.csrf.invalid

Eseguibile con `pytest --noconftest` (nessun Mongo: il db è fake).
Richiede httpx (dipendenza di TestClient): skip pulito se assente.
"""
from __future__ import annotations

import io
import os

import pytest

pytest.importorskip("httpx")

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "orbus_test")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "x" * 32)

from fastapi.testclient import TestClient  # noqa: E402

import app.avatars as avatars_mod  # noqa: E402
from app.core.app_factory import create_app  # noqa: E402
from app.core.security import get_current_user  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 200
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 200
SVG = b"<svg xmlns='http://www.w3.org/2000/svg'>" + b" " * 100 + b"</svg>"

AUTH_COOKIES = {"access_token": "dummy", "csrf_token": "tok123"}
CSRF_OK = {"X-CSRF-Token": "tok123"}


class _FakeAdventurers:
    def __init__(self):
        self.custom_avatar_url = None

    async def find_one(self, q, proj=None):
        return {"id": q.get("id", "adv1"),
                "custom_avatar_url": self.custom_avatar_url}

    async def update_one(self, q, u):
        self.custom_avatar_url = u["$set"]["custom_avatar_url"]
        return None


class _FakeDB:
    def __init__(self):
        self.adventurers = _FakeAdventurers()


async def _fake_guild(db, user_id):
    return {"id": "guild1"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AVATAR_UPLOAD_DIR", str(tmp_path / "avatars"))
    fake_db = _FakeDB()
    monkeypatch.setattr(avatars_mod, "db", fake_db)
    monkeypatch.setattr(avatars_mod, "user_guild_or_404", _fake_guild)
    application = create_app()
    application.dependency_overrides[get_current_user] = (
        lambda: {"id": "user1"}
    )
    # Senza context manager il lifespan NON parte: niente Mongo.
    test_client = TestClient(application)
    test_client._fake_db = fake_db
    return test_client


def _post(client, content, name, ctype, headers=CSRF_OK):
    return client.post(
        "/api/adventurers/adv1/avatar",
        files={"file": (name, io.BytesIO(content), ctype)},
        cookies=AUTH_COOKIES,
        headers=headers,
    )


def test_png_jpeg_webp_accettati(client):
    for content, name, ctype in (
        (PNG, "a.png", "image/png"),
        (JPG, "a.jpg", "image/jpeg"),
        (WEBP, "a.webp", "image/webp"),
    ):
        r = _post(client, content, name, ctype)
        assert r.status_code == 200, r.text
        url = r.json()["custom_avatar_url"]
        assert url.startswith("/api/uploads/avatars/adv1.")
        assert "?v=" in url  # cache-busting


def test_svg_rifiutato(client):
    r = _post(client, SVG, "a.svg", "image/svg+xml")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "avatar.unsupported_format"


def test_oltre_2mb_rifiutato(client):
    big = PNG + b"\x00" * (2 * 1024 * 1024)
    r = _post(client, big, "big.png", "image/png")
    assert r.status_code == 413
    assert r.json()["detail"]["code"] == "avatar.too_large"


def test_csrf_mancante_o_stantio_403(client):
    """La root cause del bug tester: cookie auth + header CSRF vuoto o
    stantio → 403. Il FE DEVE usare l'istanza `api` (retry con refresh),
    mai axios nudo."""
    for headers in ({"X-CSRF-Token": ""}, {"X-CSRF-Token": "vecchio"}, {}):
        r = _post(client, PNG, "a.png", "image/png", headers=headers)
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "auth.csrf.invalid"


def test_remove_torna_al_fallback(client):
    assert _post(client, PNG, "a.png", "image/png").status_code == 200
    r = client.delete(
        "/api/adventurers/adv1/avatar",
        cookies=AUTH_COOKIES, headers=CSRF_OK,
    )
    assert r.status_code == 200
    assert r.json()["custom_avatar_url"] is None
    # Secondo delete: nessun ritratto → 409 esplicito.
    r = client.delete(
        "/api/adventurers/adv1/avatar",
        cookies=AUTH_COOKIES, headers=CSRF_OK,
    )
    assert r.status_code == 409
