"""Business logic account: creazione utente e verifica login."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.database import get_db
from app.core.security import hash_password, verify_password


def _to_public(doc: dict) -> dict:
    """Estrai i campi pubblici da un documento utente Mongo."""
    return {
        "id": doc["id"],
        "email": doc["email"],
        "role": doc.get("role", "player"),
        "created_at": doc["created_at"],
    }


async def create_user(email: str, password: str) -> dict:
    """Registra un nuovo utente. Solleva 400 se email già presente."""
    db = get_db()
    email_lc = email.lower().strip()
    existing = await db.users.find_one({"email": email_lc})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata.",
        )
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "email": email_lc,
        "password_hash": hash_password(password),
        "role": "player",
        "created_at": now,
        "updated_at": now,
        "archived_at": None,
    }
    await db.users.insert_one(doc)
    return doc


async def authenticate(email: str, password: str) -> dict:
    """Verifica credenziali; solleva 401 se invalide o utente archiviato."""
    db = get_db()
    email_lc = email.lower().strip()
    user = await db.users.find_one({"email": email_lc, "archived_at": None})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide.",
        )
    return user
