"""Caricamento configurazione da variabili d'ambiente.

Non impone default per URI/credenziali sensibili: se manca .env, l'app
fallisce all'avvio in modo esplicito, come richiesto dalle regole di piattaforma.
"""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Contenitore di configurazione, valorizzato una sola volta."""

    def __init__(self) -> None:
        # ─── MongoDB (obbligatorio) ────────────────────────────────────────
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url:
            raise RuntimeError("MONGO_URL non impostato in .env")
        if not db_name:
            raise RuntimeError("DB_NAME non impostato in .env")
        self.mongo_url: str = mongo_url
        self.db_name: str = db_name

        # ─── JWT (obbligatorio) ────────────────────────────────────────────
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET non impostato in .env")
        self.jwt_secret: str = jwt_secret
        self.jwt_algorithm: str = "HS256"
        self.jwt_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 giorni

        # ─── CORS ──────────────────────────────────────────────────────────
        cors_raw = os.environ.get("CORS_ORIGINS", "*")
        self.cors_origins: list[str] = [
            o.strip() for o in cors_raw.split(",") if o.strip()
        ] or ["*"]

        # ─── App metadata ─────────────────────────────────────────────────
        self.app_env: str = os.environ.get("APP_ENV", "development")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cache singleton delle settings."""
    return Settings()
