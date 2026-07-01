"""Business logic gilde."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.database import get_db


def _to_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "owner_user_id": doc["owner_user_id"],
        "name": doc["name"],
        "description": doc.get("description", ""),
        "level": doc.get("level", 1),
        "reputation": doc.get("reputation", 0),
        "gold": doc.get("gold", 100),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


async def create_guild(user_id: str, name: str, description: str) -> dict:
    db = get_db()
    # Check applicativo: un solo guild per utente
    existing = await db.guilds.find_one({"owner_user_id": user_id, "archived_at": None})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hai già fondato una gilda.",
        )
    # Check nome duplicato (case-insensitive equivalence via lowercase compare)
    name_clean = name.strip()
    if await db.guilds.find_one({"name": name_clean}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome gilda già in uso.",
        )
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "owner_user_id": user_id,
        "name": name_clean,
        "description": description.strip(),
        "level": 1,
        "reputation": 0,
        "gold": 100,
        "created_at": now,
        "updated_at": now,
        "archived_at": None,
    }
    try:
        await db.guilds.insert_one(doc)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome gilda o proprietario già presenti.",
        ) from exc
    return doc


async def get_my_guild(user_id: str) -> dict | None:
    db = get_db()
    return await db.guilds.find_one({"owner_user_id": user_id, "archived_at": None})
