"""Client MongoDB (Motor) e provider di database.

Espone `get_db()` come dependency FastAPI e `init_indexes()` per creare
gli indici al primo avvio del server.
"""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def connect() -> AsyncIOMotorDatabase:
    """Inizializza il client Motor (idempotente)."""
    global _client, _db
    if _db is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongo_url)
        _db = _client[settings.db_name]
    return _db


def get_db() -> AsyncIOMotorDatabase:
    """Ritorna il database Motor (già connesso)."""
    if _db is None:
        return connect()
    return _db


async def init_indexes() -> None:
    """Crea/verifica tutti gli indici Mongo previsti dal dominio Fase 1."""
    db = get_db()
    # users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    # guilds
    await db.guilds.create_index("id", unique=True)
    await db.guilds.create_index("owner_user_id", unique=True)
    await db.guilds.create_index("name", unique=True)


async def close() -> None:
    """Chiude il client (usato dallo shutdown)."""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
