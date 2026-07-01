"""Seed idempotente per account di test e gilda di esempio.

Eseguito una sola volta all'avvio del server. Nessuna operazione
distruttiva; usa `upsert`-style skip su vincoli esistenti.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import hash_password

logger = logging.getLogger("orbus.seed")

# Definizione fissa degli account di seed
_SEED_ACCOUNTS = [
    {
        "email": "admin@orbus.test",
        "password": "admin123",
        "role": "admin",
        "guild": None,
    },
    {
        "email": "tester@orbus.test",
        "password": "password123",
        "role": "player",
        "guild": {"name": "Ordo Aurorae", "description": "Gilda di test principale."},
    },
    {
        "email": "clean@orbus.test",
        "password": "password123",
        "role": "player",
        "guild": None,
    },
]


async def run_seed() -> None:
    """Crea account e gilda di test se assenti. Log del risultato."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    users_created = 0
    guilds_created = 0

    for spec in _SEED_ACCOUNTS:
        existing = await db.users.find_one({"email": spec["email"]})
        if existing:
            user_id = existing["id"]
        else:
            user_id = str(uuid.uuid4())
            doc = {
                "id": user_id,
                "email": spec["email"],
                "password_hash": hash_password(spec["password"]),
                "role": spec["role"],
                "created_at": now,
                "updated_at": now,
                "archived_at": None,
            }
            await db.users.insert_one(doc)
            users_created += 1

        # Seed gilda se richiesto e non presente
        if spec["guild"]:
            has_guild = await db.guilds.find_one({"owner_user_id": user_id})
            if not has_guild:
                guild_doc = {
                    "id": str(uuid.uuid4()),
                    "owner_user_id": user_id,
                    "name": spec["guild"]["name"],
                    "description": spec["guild"]["description"],
                    "level": 1,
                    "reputation": 0,
                    "gold": 100,
                    "created_at": now,
                    "updated_at": now,
                    "archived_at": None,
                }
                try:
                    await db.guilds.insert_one(guild_doc)
                    guilds_created += 1
                except Exception as exc:
                    # Se il nome è già in uso da un altro test, ignoriamo.
                    logger.warning("Seed gilda '%s' saltato: %s", spec["guild"]["name"], exc)

    total_users = await db.users.count_documents({})
    total_guilds = await db.guilds.count_documents({})
    logger.info(
        "Seed completato: %d utenti, %d gilda (nuovi utenti: %d, nuove gilde: %d)",
        total_users,
        total_guilds,
        users_created,
        guilds_created,
    )
