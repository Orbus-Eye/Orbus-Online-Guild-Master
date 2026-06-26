"""Phase 16 — Consortiums MVP (cross-guild social groups).

Design constraints (binding):
- 1 user / 1 guild can belong to AT MOST 1 consortium at a time.
- Open join (no invites in MVP).
- No power bonuses, no XP/gold/loot/ranking rewards.
- No free chat: members can read the consortium's public event feed
  (derived from the audit log scoped to member guilds) but cannot post.
- Name validation: 3-40 chars, unique case-insensitive, no Test* prefix,
  no email/@ characters, no leading/trailing whitespace.
- Audit logging on create / join / leave (event_types `consortium_*`).

Collections (created lazily; indexes ensured on first import via lifespan
in services._ensure_indexes called from the routes module on import):
- consortiums: {id, name, name_lower, tag, description, founder_user_id,
  founder_guild_id, created_at}
- consortium_members: {id, consortium_id, user_id, guild_id, role
  (founder/admin/member), joined_at}

Indexes:
- consortiums.name_lower UNIQUE
- consortium_members.user_id UNIQUE  ← enforces 1 consortium per user
- consortium_members.guild_id UNIQUE ← enforces 1 consortium per guild
- consortium_members.consortium_id (non-unique index for fan-out queries)
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

logger = logging.getLogger("orbus.consortiums")

NAME_MIN = 3
NAME_MAX = 40
TAG_MIN = 2
TAG_MAX = 6
DESCRIPTION_MAX = 300

_TEST_NAME_RE = re.compile(r"^\s*test", re.IGNORECASE)
_NAME_FORBIDDEN_CHARS_RE = re.compile(r"[@<>\\/]")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_consortium_indexes(db) -> None:
    """Idempotent index creation (called by lifespan)."""
    try:
        await db.consortiums.create_index("id", unique=True, name="consortiums_id_unique")
        await db.consortiums.create_index(
            "name_lower", unique=True, name="consortiums_name_lower_unique"
        )
        await db.consortium_members.create_index(
            "id", unique=True, name="cmembers_id_unique"
        )
        await db.consortium_members.create_index(
            "user_id", unique=True, name="cmembers_user_id_unique"
        )
        await db.consortium_members.create_index(
            "guild_id", unique=True, name="cmembers_guild_id_unique"
        )
        await db.consortium_members.create_index(
            "consortium_id", name="cmembers_consortium_id_idx"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_consortium_indexes: %s", exc)


def _validate_name(name: str) -> str:
    s = (name or "").strip()
    if not (NAME_MIN <= len(s) <= NAME_MAX):
        raise HTTPException(422, f"name must be {NAME_MIN}-{NAME_MAX} chars")
    if _TEST_NAME_RE.match(s):
        raise HTTPException(422, "name cannot start with 'Test'")
    if _NAME_FORBIDDEN_CHARS_RE.search(s):
        raise HTTPException(422, "name contains forbidden characters")
    return s


def _validate_tag(tag: str | None) -> str | None:
    if not tag:
        return None
    s = tag.strip()
    if not (TAG_MIN <= len(s) <= TAG_MAX):
        raise HTTPException(422, f"tag must be {TAG_MIN}-{TAG_MAX} chars")
    if not re.match(r"^[A-Za-z0-9_-]+$", s):
        raise HTTPException(422, "tag must be alphanumeric (also _ -)")
    return s.upper()


def _validate_description(desc: str | None) -> str:
    s = (desc or "").strip()
    if len(s) > DESCRIPTION_MAX:
        raise HTTPException(422, f"description must be ≤{DESCRIPTION_MAX} chars")
    return s


async def _get_user_guild(db, user_id: str) -> dict:
    g = await db.guilds.find_one({"owner_user_id": user_id})
    if not g:
        raise HTTPException(403, "user has no guild")
    return g


async def _membership_of(db, user_id: str) -> dict | None:
    return await db.consortium_members.find_one({"user_id": user_id}, {"_id": 0})


async def create_consortium(
    db, *, current_user: dict, name: str, tag: str | None, description: str | None
) -> dict:
    name = _validate_name(name)
    tag = _validate_tag(tag)
    description = _validate_description(description)
    user_id = current_user["id"]

    if await _membership_of(db, user_id):
        raise HTTPException(409, "user already belongs to a consortium")
    guild = await _get_user_guild(db, user_id)

    cid = str(uuid.uuid4())
    name_lower = name.casefold()
    doc = {
        "id": cid,
        "name": name,
        "name_lower": name_lower,
        "tag": tag,
        "description": description,
        "founder_user_id": user_id,
        "founder_guild_id": guild["id"],
        "created_at": _now_iso(),
    }
    try:
        await db.consortiums.insert_one(doc)
    except Exception as exc:
        if "duplicate key" in str(exc).lower():
            raise HTTPException(409, "consortium name already taken")
        raise

    member = {
        "id": str(uuid.uuid4()),
        "consortium_id": cid,
        "user_id": user_id,
        "guild_id": guild["id"],
        "guild_name": guild.get("name", ""),
        "role": "founder",
        "joined_at": _now_iso(),
    }
    try:
        await db.consortium_members.insert_one(member)
    except Exception:
        # Roll back the consortium row to preserve uniqueness invariants.
        await db.consortiums.delete_one({"id": cid})
        raise

    await _audit(db, "consortium_created", user_id, guild["id"], cid, name)
    out = {k: v for k, v in doc.items() if k not in ("name_lower", "_id")}
    out["member_count"] = 1
    return out


async def list_consortiums(db, *, limit: int = 50) -> list[dict]:
    rows = await db.consortiums.find({}, {"_id": 0, "name_lower": 0}) \
        .sort("created_at", -1).limit(int(limit)).to_list(int(limit))
    if not rows:
        return []
    cids = [r["id"] for r in rows]
    # Aggregate member counts per consortium
    pipeline = [
        {"$match": {"consortium_id": {"$in": cids}}},
        {"$group": {"_id": "$consortium_id", "n": {"$sum": 1}}},
    ]
    counts = {r["_id"]: r["n"] async for r in db.consortium_members.aggregate(pipeline)}
    for r in rows:
        r["member_count"] = int(counts.get(r["id"], 0))
    return rows


async def get_consortium_detail(db, cid: str) -> dict:
    c = await db.consortiums.find_one({"id": cid}, {"_id": 0, "name_lower": 0})
    if not c:
        raise HTTPException(404, "consortium not found")
    members = await db.consortium_members.find(
        {"consortium_id": cid},
        {"_id": 0, "user_id": 0},  # never expose user_id publicly
    ).sort("joined_at", 1).to_list(200)
    c["members"] = members
    c["member_count"] = len(members)
    return c


async def join_consortium(db, *, current_user: dict, cid: str) -> dict:
    user_id = current_user["id"]
    if await _membership_of(db, user_id):
        raise HTTPException(409, "user already belongs to a consortium")
    c = await db.consortiums.find_one({"id": cid})
    if not c:
        raise HTTPException(404, "consortium not found")
    guild = await _get_user_guild(db, user_id)
    member = {
        "id": str(uuid.uuid4()),
        "consortium_id": cid,
        "user_id": user_id,
        "guild_id": guild["id"],
        "guild_name": guild.get("name", ""),
        "role": "member",
        "joined_at": _now_iso(),
    }
    try:
        await db.consortium_members.insert_one(member)
    except Exception as exc:
        if "duplicate key" in str(exc).lower():
            raise HTTPException(409, "user or guild already in a consortium")
        raise
    await _audit(db, "consortium_joined", user_id, guild["id"], cid, c["name"])
    return await get_consortium_detail(db, cid)


async def leave_consortium(db, *, current_user: dict) -> dict:
    user_id = current_user["id"]
    member = await _membership_of(db, user_id)
    if not member:
        raise HTTPException(404, "user is not in any consortium")
    cid = member["consortium_id"]
    # Founder cannot leave unless they are the last member (in MVP we
    # auto-delete the empty consortium).
    if member.get("role") == "founder":
        other = await db.consortium_members.count_documents({
            "consortium_id": cid, "user_id": {"$ne": user_id},
        })
        if other > 0:
            raise HTTPException(
                409,
                "founder cannot leave while other members remain (transfer not implemented in MVP)",
            )
        await db.consortiums.delete_one({"id": cid})
    await db.consortium_members.delete_one({"id": member["id"]})
    await _audit(db, "consortium_left", user_id, member.get("guild_id"), cid, None)
    return {"success": True, "consortium_id": cid}


async def my_consortium(db, *, current_user: dict) -> dict | None:
    member = await _membership_of(db, current_user["id"])
    if not member:
        return None
    return await get_consortium_detail(db, member["consortium_id"])


async def consortium_activity(db, cid: str, *, limit: int = 20, lang: str = "it") -> dict:
    """Recent audit events scoped to member guilds — sanitized via the
    chronicle service (same privacy filters)."""
    members = await db.consortium_members.find(
        {"consortium_id": cid}, {"_id": 0, "guild_id": 1}
    ).to_list(500)
    guild_ids = [m["guild_id"] for m in members]
    if not guild_ids:
        return {"events": []}
    from app.chronicle.services import list_chronicle, PUBLIC_EVENTS  # lazy import
    # Reuse the chronicle pipeline but pre-filter to member guilds.
    # Quick implementation: query directly, format minimally.
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    cutoff = (_dt.now(_tz.utc) - _td(days=14)).isoformat()
    raw = await db.audit_log.find(
        {
            "event_type": {"$in": list(PUBLIC_EVENTS)},
            "actor_guild_id": {"$in": guild_ids},
            "created_at": {"$gte": cutoff},
        },
        {"_id": 0},
    ).sort("created_at", -1).limit(int(limit) * 2).to_list(int(limit) * 2)
    # Reuse format helpers by calling list_chronicle's logic indirectly:
    # we re-implement a minimal projection here to avoid extra DB round-trips.
    # Build guild_name lookup
    g_rows = await db.guilds.find(
        {"id": {"$in": list(set(guild_ids))}},
        {"_id": 0, "id": 1, "name": 1},
    ).to_list(200)
    g_map = {g["id"]: g.get("name", "") for g in g_rows}
    out = []
    for r in raw:
        gname = g_map.get(r.get("actor_guild_id"), "")
        if not gname:
            continue
        out.append({
            "id": r.get("id"),
            "kind": r.get("event_type"),
            "guild_name": gname,
            "created_at": r.get("created_at"),
            "summary": r.get("event_type"),
        })
        if len(out) >= int(limit):
            break
    return {"events": out}


async def _audit(db, event_type: str, user_id: str, guild_id: str | None, cid: str, name: str | None):
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type=event_type,
            actor_user_id=user_id,
            actor_guild_id=guild_id,
            metadata={"consortium_id": cid, "consortium_name": name},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("consortium audit log failed (%s): %s", event_type, exc)


__all__ = [
    "ensure_consortium_indexes",
    "create_consortium",
    "list_consortiums",
    "get_consortium_detail",
    "join_consortium",
    "leave_consortium",
    "my_consortium",
    "consortium_activity",
]
