"""FASE 6 (2026-08-08) — Upload avatar personalizzato degli avventurieri.

Il giocatore può caricare un'immagine dal proprio PC come ritratto di un
avventuriero (richiesta K.24). Il file viene validato in modo severo e
salvato su disco; l'URL relativo finisce in `custom_avatar_url` sul doc
avventuriero. Il FE (utils/gameAssets.avatarSources) mette l'upload in
testa alla catena di fallback: rimosso l'upload si torna all'avatar
razziale di default — mai immagini rotte.

Sicurezza:
  * Solo PNG / JPEG / WEBP — verifica dei MAGIC BYTES, non solo del
    Content-Type dichiarato. Niente SVG (rischio XSS) né GIF.
  * Cap 2 MB per file.
  * Nome file generato dal server (`{adventurer_id}.{ext}`): nessun
    input dell'utente finisce nel filesystem → niente path traversal.
  * Sostituzione: i vecchi file dell'avventuriero vengono rimossi.

Storage: `AVATAR_UPLOAD_DIR` (env) o `<backend>/uploads/avatars`.
Serving: mount StaticFiles su `/api/uploads/avatars` (app_factory).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.avatars")

router = APIRouter(prefix="/api", tags=["avatars"])

MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB

# ext → verifica dei magic bytes (il Content-Type dichiarato non basta).
_MAGIC_CHECKS = {
    "png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
    "jpg": lambda b: b.startswith(b"\xff\xd8\xff"),
    "webp": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP",
}
_CONTENT_TYPE_TO_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


def avatar_upload_dir() -> Path:
    raw = os.environ.get("AVATAR_UPLOAD_DIR")
    if raw:
        path = Path(raw)
    else:
        path = Path(__file__).resolve().parents[2] / "uploads" / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sniff_image_ext(content: bytes, declared_content_type: str) -> str | None:
    """Ritorna l'estensione canonica SOLO se magic bytes e Content-Type
    dichiarato concordano. None = file rifiutato."""
    declared_ext = _CONTENT_TYPE_TO_EXT.get(
        (declared_content_type or "").lower().split(";")[0].strip()
    )
    if not declared_ext:
        return None
    check = _MAGIC_CHECKS[declared_ext]
    return declared_ext if check(content) else None


async def _owned_adventurer_or_404(guild: dict, adventurer_id: str) -> dict:
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"]},
        {"_id": 0, "id": 1, "custom_avatar_url": 1},
    )
    if not adv:
        raise HTTPException(status_code=404, detail="Avventuriero non trovato")
    return adv


def _remove_existing_files(adventurer_id: str) -> None:
    base = avatar_upload_dir()
    for ext in _MAGIC_CHECKS:
        candidate = base / f"{adventurer_id}.{ext}"
        try:
            if candidate.exists():
                candidate.unlink()
        except OSError:
            logger.warning("avatar cleanup failed: %s", candidate)


@router.post("/adventurers/{adventurer_id}/avatar")
async def upload_avatar(
    adventurer_id: str,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
):
    """Carica/sostituisce il ritratto personalizzato dell'avventuriero."""
    guild = await user_guild_or_404(db, current_user["id"])
    await _owned_adventurer_or_404(guild, adventurer_id)

    content = await file.read(MAX_AVATAR_BYTES + 1)
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail={
            "code": "avatar.too_large",
            "user_message": "Immagine troppo grande: massimo 2 MB.",
        })
    if len(content) < 100:
        raise HTTPException(status_code=422, detail={
            "code": "avatar.invalid",
            "user_message": "File immagine non valido.",
        })
    ext = sniff_image_ext(content, file.content_type or "")
    if not ext:
        raise HTTPException(status_code=422, detail={
            "code": "avatar.unsupported_format",
            "user_message": (
                "Formato non supportato: usa PNG, JPEG o WEBP."
            ),
        })

    _remove_existing_files(adventurer_id)
    filename = f"{adventurer_id}.{ext}"
    (avatar_upload_dir() / filename).write_bytes(content)

    # Cache-busting nel path salvato: i browser non devono mostrare il
    # vecchio ritratto dopo una sostituzione.
    from datetime import datetime, timezone
    version = int(datetime.now(timezone.utc).timestamp())
    url = f"/api/uploads/avatars/{filename}?v={version}"
    await db.adventurers.update_one(
        {"id": adventurer_id},
        {"$set": {"custom_avatar_url": url}},
    )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="avatar_uploaded",
            actor_user_id=current_user["id"], actor_guild_id=guild["id"],
            source="avatars.upload", related_entity_id=adventurer_id,
            metadata={"ext": ext, "bytes": len(content)},
        )
    except Exception:  # noqa: BLE001
        pass
    return {"adventurer_id": adventurer_id, "custom_avatar_url": url}


@router.delete("/adventurers/{adventurer_id}/avatar")
async def remove_avatar(
    adventurer_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Rimuove il ritratto personalizzato (torna all'avatar razziale)."""
    guild = await user_guild_or_404(db, current_user["id"])
    adv = await _owned_adventurer_or_404(guild, adventurer_id)
    if not adv.get("custom_avatar_url"):
        raise HTTPException(status_code=409, detail={
            "code": "avatar.none",
            "user_message": "Questo avventuriero non ha un ritratto personalizzato.",
        })
    _remove_existing_files(adventurer_id)
    await db.adventurers.update_one(
        {"id": adventurer_id},
        {"$set": {"custom_avatar_url": None}},
    )
    return {"adventurer_id": adventurer_id, "custom_avatar_url": None}


__all__ = ["router", "avatar_upload_dir", "sniff_image_ext",
           "MAX_AVATAR_BYTES"]
