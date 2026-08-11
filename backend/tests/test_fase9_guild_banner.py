"""FASE 9K — endpoint banner di gilda esercitato davvero (no Mongo).

Stessa sicurezza dell'avatar (FASE 6): magic bytes, no SVG, cap 4 MB,
filename server-side, ownership gilda, replacement cleanup, fallback.
App COMPLETA (middleware CSRF inclusi) con auth override e db finto.
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

import app.banners as banners_mod  # noqa: E402
from app.core.app_factory import create_app  # noqa: E402
from app.core.security import get_current_user  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
SVG = b"<svg xmlns='http://www.w3.org/2000/svg'>" + b" " * 100 + b"</svg>"

AUTH_COOKIES = {"access_token": "dummy", "csrf_token": "tok123"}
CSRF_OK = {"X-CSRF-Token": "tok123"}


class _FakeGuilds:
    def __init__(self):
        self.custom_banner_url = None

    async def find_one(self, q, proj=None):
        return {"id": "guild1", "owner_user_id": "user1",
                "custom_banner_url": self.custom_banner_url}

    async def update_one(self, q, u):
        self.custom_banner_url = u["$set"]["custom_banner_url"]
        return None


class _FakeDB:
    def __init__(self):
        self.guilds = _FakeGuilds()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BANNER_UPLOAD_DIR", str(tmp_path / "banners"))
    monkeypatch.setenv("AVATAR_UPLOAD_DIR", str(tmp_path / "avatars"))
    fake_db = _FakeDB()
    monkeypatch.setattr(banners_mod, "db", fake_db)

    async def _fake_guild(db, user_id):
        return await fake_db.guilds.find_one({"owner_user_id": user_id})

    monkeypatch.setattr(banners_mod, "user_guild_or_404", _fake_guild)
    application = create_app()
    application.dependency_overrides[get_current_user] = (
        lambda: {"id": "user1"}
    )
    return TestClient(application)


def _post(client, content, name, ctype):
    return client.post(
        "/api/guilds/banner",
        files={"file": (name, io.BytesIO(content), ctype)},
        cookies=AUTH_COOKIES,
        headers=CSRF_OK,
    )


def test_png_accettato_con_priorita_e_cache_busting(client):
    r = _post(client, PNG, "b.png", "image/png")
    assert r.status_code == 200, r.text
    url = r.json()["custom_banner_url"]
    assert url.startswith("/api/uploads/banners/guild1.png")
    assert "?v=" in url


def test_svg_e_oversize_rifiutati(client):
    r = _post(client, SVG, "b.svg", "image/svg+xml")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "banner.unsupported_format"
    big = PNG + b"\x00" * (4 * 1024 * 1024)
    r = _post(client, big, "big.png", "image/png")
    assert r.status_code == 413
    assert r.json()["detail"]["code"] == "banner.too_large"


def test_remove_torna_al_banner_standard(client):
    assert _post(client, PNG, "b.png", "image/png").status_code == 200
    r = client.delete(
        "/api/guilds/banner", cookies=AUTH_COOKIES, headers=CSRF_OK,
    )
    assert r.status_code == 200
    assert r.json()["custom_banner_url"] is None
    r = client.delete(
        "/api/guilds/banner", cookies=AUTH_COOKIES, headers=CSRF_OK,
    )
    assert r.status_code == 409


def test_csrf_richiesto_anche_per_il_banner(client):
    r = client.post(
        "/api/guilds/banner",
        files={"file": ("b.png", io.BytesIO(PNG), "image/png")},
        cookies=AUTH_COOKIES,
        headers={"X-CSRF-Token": "sbagliato"},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "auth.csrf.invalid"
