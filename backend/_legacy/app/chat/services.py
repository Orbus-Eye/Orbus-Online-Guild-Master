"""Phase 19.3 — Chat MVP services.

Hard rules (binding):
  • No PII in API responses (no email, no internal user_id/guild_id,
    no ObjectId). Only `sender_public_name` (gilda) is exposed.
  • Test-user messages (`users.is_test_user=True`) are filtered FROM
    global chat responses, EXCEPT the requesting user always sees
    their own messages (keeps QA flow functional in dev).
  • Rate limit: max 5 messages per 10 seconds per user (sliding window
    against `chat_messages` itself, persistent).
  • Validation: text trim → 1..500 chars, html.escape, no HTML render.
  • Consortium endpoints: 403 if user is not a member of `consortium_id`.
"""
import html
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException


logger = logging.getLogger("orbus.chat")

MESSAGE_MAX_LEN = 500
RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW_S = 10
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


# ─── Index bootstrap ──────────────────────────────────────────────────────
async def ensure_chat_indexes(db) -> None:
    """Create indexes for chat_messages (idempotent)."""
    await db.chat_messages.create_index(
        [("channel_type", 1), ("created_at", -1)],
        name="chat_channel_created_idx",
    )
    await db.chat_messages.create_index(
        [("consortium_id", 1), ("created_at", -1)],
        name="chat_consortium_created_idx",
        sparse=True,
    )
    await db.chat_messages.create_index(
        [("sender_user_id", 1), ("created_at", -1)],
        name="chat_sender_created_idx",
    )
    await db.chat_messages.create_index(
        "message_id", name="chat_message_id_idx", unique=True
    )


# ─── Validation ───────────────────────────────────────────────────────────
_WS_RE = re.compile(r"\s+")


def _sanitize_text(raw: str) -> str:
    """Trim, collapse internal whitespace runs to single space, HTML-escape.

    Raises 422 for empty or over-long messages.
    """
    if not isinstance(raw, str):
        raise HTTPException(status_code=422, detail="chat.invalid_text")
    text = raw.strip()
    if not text:
        raise HTTPException(status_code=422, detail="chat.text_required")
    if len(text) > MESSAGE_MAX_LEN:
        raise HTTPException(status_code=422, detail="chat.text_too_long")
    # Normalize internal whitespace runs (no newlines spam) then escape.
    text = _WS_RE.sub(" ", text)
    return html.escape(text, quote=True)


# ─── Public projection (no PII) ───────────────────────────────────────────
def message_public(doc: dict) -> dict:
    """Return ONLY safe player-facing fields. NEVER expose user/guild ids,
    email, ObjectId, or internal moderation metadata payloads."""
    return {
        "message_id": doc["message_id"],
        "channel_type": doc["channel_type"],
        "sender_public_name": doc.get("sender_public_name", "Anonymous Guild"),
        "message_text": doc.get("message_text", ""),
        "created_at": doc["created_at"],
        "edited_at": doc.get("edited_at"),
        "moderation_status": doc.get("moderation_status", "visible"),
    }


# ─── Rate limit (sliding window on chat_messages itself) ──────────────────
async def _check_rate_limit(db, user_id: str) -> None:
    cutoff_iso = (
        datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_WINDOW_S)
    ).isoformat()
    recent = await db.chat_messages.count_documents({
        "sender_user_id": user_id,
        "created_at": {"$gt": cutoff_iso},
    })
    if recent >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="chat.rate_limited")


# ─── Membership / sender resolution ───────────────────────────────────────
async def _resolve_sender(db, current_user: dict) -> dict:
    """Resolve sender's guild + public name. 403 if user has no guild
    (chat is gated behind owning a guild — same model as everything else)."""
    guild = await db.guilds.find_one(
        {"owner_user_id": current_user["id"]}, {"_id": 0, "id": 1, "name": 1}
    )
    if not guild:
        raise HTTPException(status_code=403, detail="chat.guild_required")
    return guild


async def _require_consortium_membership(
    db, user_id: str, consortium_id: str
) -> dict:
    """Return membership row; 403 if user is not in this consortium."""
    member = await db.consortium_members.find_one(
        {"user_id": user_id, "consortium_id": consortium_id}, {"_id": 0}
    )
    if not member:
        raise HTTPException(status_code=403, detail="chat.not_consortium_member")
    return member


# ─── Test-user privacy filter (global only) ───────────────────────────────
async def _global_test_user_filter(db, current_user_id: str) -> dict:
    """Build the filter clause that hides messages authored by test users
    (`is_test_user=True`) EXCEPT the requesting user's own messages.

    This keeps `tester@orbus.test` (which is itself flagged as a test user
    in dev seeds) able to validate the chat flow without polluting other
    real players' view.
    """
    ids = await db.users.distinct("id", {"is_test_user": True})
    ids = [i for i in ids if i and i != current_user_id]
    if not ids:
        return {}
    return {"sender_user_id": {"$nin": ids}}


# ─── Send ─────────────────────────────────────────────────────────────────
async def send_message(
    db,
    *,
    current_user: dict,
    channel_type: str,
    consortium_id: Optional[str],
    raw_text: str,
) -> dict:
    text = _sanitize_text(raw_text)
    guild = await _resolve_sender(db, current_user)
    if channel_type == "consortium":
        if not consortium_id:
            raise HTTPException(status_code=422, detail="chat.consortium_id_required")
        await _require_consortium_membership(db, current_user["id"], consortium_id)
    elif channel_type != "global":
        raise HTTPException(status_code=422, detail="chat.invalid_channel")

    await _check_rate_limit(db, current_user["id"])

    now_iso = datetime.now(timezone.utc).isoformat()
    doc = {
        "message_id": str(uuid.uuid4()),
        "channel_type": channel_type,
        "consortium_id": consortium_id if channel_type == "consortium" else None,
        "sender_user_id": current_user["id"],          # internal, never exposed
        "sender_guild_id": guild["id"],                 # internal, never exposed
        "sender_public_name": guild.get("name", "Anonymous Guild"),
        "message_text": text,
        "created_at": now_iso,
        "edited_at": None,
        "deleted_at": None,
        "is_deleted": False,
        "moderation_status": "visible",
        "metadata": {},
    }
    await db.chat_messages.insert_one(doc)
    return message_public(doc)


# ─── Fetch ────────────────────────────────────────────────────────────────
async def fetch_global(
    db, *, current_user: dict, after_iso: Optional[str], limit: int
) -> list[dict]:
    q: dict = {
        "channel_type": "global",
        "is_deleted": {"$ne": True},
        "moderation_status": "visible",
    }
    if after_iso:
        q["created_at"] = {"$gt": after_iso}
    test_filter = await _global_test_user_filter(db, current_user["id"])
    # Combine — test_filter uses sender_user_id $nin; merge cleanly.
    q.update(test_filter)
    rows = (
        await db.chat_messages.find(q, {"_id": 0})
        .sort("created_at", -1)
        .limit(min(max(int(limit or DEFAULT_LIMIT), 1), MAX_LIMIT))
        .to_list(MAX_LIMIT)
    )
    rows.reverse()  # ascending for client convenience
    return [message_public(r) for r in rows]


async def fetch_consortium(
    db,
    *,
    current_user: dict,
    consortium_id: str,
    after_iso: Optional[str],
    limit: int,
) -> list[dict]:
    await _require_consortium_membership(db, current_user["id"], consortium_id)
    q: dict = {
        "channel_type": "consortium",
        "consortium_id": consortium_id,
        "is_deleted": {"$ne": True},
        "moderation_status": "visible",
    }
    if after_iso:
        q["created_at"] = {"$gt": after_iso}
    rows = (
        await db.chat_messages.find(q, {"_id": 0})
        .sort("created_at", -1)
        .limit(min(max(int(limit or DEFAULT_LIMIT), 1), MAX_LIMIT))
        .to_list(MAX_LIMIT)
    )
    rows.reverse()
    return [message_public(r) for r in rows]


__all__ = [
    "ensure_chat_indexes",
    "send_message",
    "fetch_global",
    "fetch_consortium",
    "message_public",
    "MESSAGE_MAX_LEN",
    "RATE_LIMIT_COUNT",
    "RATE_LIMIT_WINDOW_S",
]
