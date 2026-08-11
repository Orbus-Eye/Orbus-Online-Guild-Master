"""FASE 9K — Banner personalizzato della gilda (upload dal PC).

Riusa ESATTAMENTE il modello di sicurezza dell'upload avatar (FASE 6):
  * solo PNG / JPEG / WEBP — verifica dei MAGIC BYTES, mai solo il
    Content-Type dichiarato; niente SVG (XSS) né GIF;
  * cap dimensione 4 MB (i banner hero sono più grandi dei ritratti);
  * nome file generato dal server (`{guild_id}.{ext}`): nessun input
    utente nel filesystem → niente path traversal;
  * ownership: solo il proprietario della gilda può caricare/rimuovere;
  * sostituzione: i vecchi file della gilda vengono rimossi;
  * fallback FE: rimosso il banner si torna a quello standard
    (`assets/banners/dashboard.svg`) — mai immagini rotte.

Storage: `BANNER_UPLOAD_DIR` (env) o `<backend>/uploads/banners`
(persistente: stesso volume degli avatar in produzione).
Serving: mount StaticFiles su `/api/uploads/banners` (app_factory).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.avatars import sniff_image_ext
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.banners")

router = APIRouter(prefix="/api", tags=["banners"])

MAX_BANNER_BYTES = 4 * 1024 * 1024  # 4 MB
_KNOWN_EXTS = ("png", "jpg", "webp")


def banner_upload_dir() -> Path:
    raw = os.environ.get("BANNER_UPLOAD_DIR")
    if raw:
        path = Path(raw)
    else:
        path = Path(__file__).resolve().parents[2] / "uploads" / "banners"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _remove_existing_files(guild_id: str) -> None:
    base = banner_upload_dir()
    for ext in _KNOWN_EXTS:
        candidate = base / f"{guild_id}.{ext}"
        try:
            if candidate.exists():
                candidate.unlink()
        except OSError:
            logger.warning("banner cleanup failed: %s", candidate)


@router.post("/guilds/banner")
async def upload_guild_banner(
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
):
    """Carica/sostituisce il banner personalizzato della gilda."""
    guild = await user_guild_or_404(db, current_user["id"])

    content = await file.read(MAX_BANNER_BYTES + 1)
    if len(content) > MAX_BANNER_BYTES:
        raise HTTPException(status_code=413, detail={
            "code": "banner.too_large",
            "user_message": "Immagine troppo grande: massimo 4 MB.",
        })
    if len(content) < 100:
        raise HTTPException(status_code=422, detail={
            "code": "banner.invalid",
            "user_message": "File immagine non valido.",
        })
    ext = sniff_image_ext(content, file.content_type or "")
    if not ext:
        raise HTTPException(status_code=422, detail={
            "code": "banner.unsupported_format",
            "user_message": "Formato non supportato: usa PNG, JPEG o WEBP.",
        })

    _remove_existing_files(guild["id"])
    filename = f"{guild['id']}.{ext}"
    (banner_upload_dir() / filename).write_bytes(content)

    # Cache-busting: dopo una sostituzione i browser non devono mostrare
    # il vecchio banner.
    version = int(datetime.now(timezone.utc).timestamp())
    url = f"/api/uploads/banners/{filename}?v={version}"
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$set": {"custom_banner_url": url}},
    )
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="guild_banner_uploaded",
            actor_user_id=current_user["id"], actor_guild_id=guild["id"],
            source="banners.upload", related_entity_id=guild["id"],
            metadata={"ext": ext, "bytes": len(content)},
        )
    except Exception:  # noqa: BLE001
        pass
    return {"guild_id": guild["id"], "custom_banner_url": url}


@router.delete("/guilds/banner")
async def remove_guild_banner(
    current_user: dict = Depends(get_current_user),
):
    """Rimuove il banner personalizzato (torna al banner standard)."""
    guild = await user_guild_or_404(db, current_user["id"])
    if not guild.get("custom_banner_url"):
        raise HTTPException(status_code=409, detail={
            "code": "banner.none",
            "user_message": "La gilda non ha un banner personalizzato.",
        })
    _remove_existing_files(guild["id"])
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$set": {"custom_banner_url": None}},
    )
    return {"guild_id": guild["id"], "custom_banner_url": None}


__all__ = ["router", "banner_upload_dir", "MAX_BANNER_BYTES"]
