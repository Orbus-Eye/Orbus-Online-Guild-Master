"""Orbus Online: Guild Master — punto d'ingresso ASGI.

Sottile wrapper: tutta la logica di dominio vive in `app.main`.
Necessario per la compatibilità con supervisor (`server:app`).
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from app.main import app  # noqa: E402

__all__ = ["app"]
