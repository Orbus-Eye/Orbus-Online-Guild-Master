"""ROUND 12.D — Idempotent preview-only demo opponents seed.

3 lore-coherent guilds, each with:
  * Fictitious `is_demo_owner=true` user
  * Guild flagged `is_demo_opponent=true` (separate from `is_test_artifact`)
  * 5 ready-to-fight adventurers (Lv5-Lv10, Tank+Healer+3 DPS)
  * Valid PvP defense team
  * season_participations with target rating/league

In production these guilds can be soft-disabled by setting
`is_demo_opponent=false` (no hard delete).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.core.database import db

logger = logging.getLogger("orbus.seed_round12_demo_opponents")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEMO_GUILDS = [
    {"name": "Custodi del Vento", "rating": 1100, "league": "silver",
     "owner_email": "demo_custodi@orbus.preview"},
    {"name": "Esiliati del Vuoto", "rating": 1300, "league": "gold",
     "owner_email": "demo_esiliati@orbus.preview"},
    {"name": "Compagnia delle Tre Lune", "rating": 950, "league": "bronze",
     "owner_email": "demo_treluna@orbus.preview"},
]


ROLES = ["Tank", "Healer", "DPS", "DPS", "DPS"]
CLASSES = ["Guardian", "Cleric", "Berserker", "Ranger", "Mage"]
NAMES = ["Veronik", "Lyandra", "Korash", "Eithne", "Solandir",
         "Brenor", "Mireah", "Tor'val", "Asha", "Dremel",
         "Kael", "Sylvi", "Garrick", "Yuna", "Roric"]


async def _ensure_demo_owner(email: str, idx: int) -> dict:
    u = await db.users.find_one({"email": email})
    if u:
        if not u.get("is_demo_owner"):
            await db.users.update_one({"id": u["id"]}, {"$set": {"is_demo_owner": True}})
        return u
    uid = str(uuid.uuid4())
    doc = {
        "id": uid, "email": email,
        "username": f"demo_owner_{idx}",
        "password_hash": "!disabled-no-login-demo!",
        "is_admin": False, "is_demo_owner": True,
        "is_test_user": False,
        "created_at": _now(), "updated_at": _now(),
    }
    await db.users.insert_one(doc)
    return doc


async def _ensure_demo_guild(owner_id: str, meta: dict, idx: int) -> dict:
    g = await db.guilds.find_one({"name": meta["name"]})
    if g:
        if not g.get("is_demo_opponent"):
            await db.guilds.update_one({"id": g["id"]}, {"$set": {"is_demo_opponent": True}})
        return g
    gid = str(uuid.uuid4())
    public_id = gid[:8]
    doc = {
        "id": gid, "owner_user_id": owner_id,
        "public_id": public_id,
        "name": meta["name"], "description": f"Gilda demo {idx} (preview only).",
        "level": 5, "reputation": 50, "gold": 500,
        "is_demo_opponent": True,  # NEW: separate from is_test_artifact
        "is_test_artifact": False,
        "max_team_power_ever": 900 + (meta["rating"] - 1000),
        "created_at": _now(), "updated_at": _now(),
    }
    await db.guilds.insert_one(doc)
    return doc


async def _ensure_demo_adventurers(guild_id: str, base_name_idx: int) -> list[str]:
    advs = await db.adventurers.find(
        {"guild_id": guild_id}, {"_id": 0, "id": 1},
    ).to_list(10)
    if len(advs) >= 5:
        return [a["id"] for a in advs[:5]]
    ids = []
    for slot in range(5):
        aid = str(uuid.uuid4())
        adv_name = NAMES[(base_name_idx * 5 + slot) % len(NAMES)]
        lvl = 6 + (slot % 4)
        doc = {
            "id": aid, "guild_id": guild_id, "name": adv_name,
            "class": CLASSES[slot], "role": ROLES[slot], "level": lvl,
            "stats": {"atk": 12 + slot, "def": 12, "pwr": 14, "spd": 10},
            "team_power": 180 + slot * 8,
            "traits": [],
            "is_available": True, "archived": False, "retired": False, "frozen": False,
            "is_test_artifact": False,
            "created_at": _now(),
        }
        await db.adventurers.insert_one(doc)
        ids.append(aid)
    return ids


async def _ensure_defense_team(guild_id: str, adv_ids: list[str]) -> None:
    existing = await db.pvp_defense_teams.find_one({"guild_id": guild_id})
    if existing:
        return
    await db.pvp_defense_teams.insert_one({
        "guild_id": guild_id, "adventurer_ids": adv_ids,
        "is_valid": True, "last_validated_at": _now(),
        "warnings": [], "created_at": _now(), "updated_at": _now(),
    })


async def _ensure_participation(guild: dict, season: dict, meta: dict) -> None:
    p = await db.season_participations.find_one({
        "season_id": season["season_id"], "guild_id": guild["id"],
    })
    if p:
        return
    await db.season_participations.insert_one({
        "season_id": season["season_id"], "guild_id": guild["id"],
        "guild_public_id": guild["public_id"], "guild_name": guild["name"],
        "league": meta["league"], "rating": meta["rating"],
        "placement_matches_played": 10,
        "wins": 5, "losses": 4, "draws": 1,
        "attacks_played": 9, "defense_wins": 3, "defense_losses": 2,
        "best_rating": meta["rating"], "highest_league": meta["league"],
        "last_match_at": _now(),
        "is_test": False, "is_demo": True,
        "created_at": _now(), "updated_at": _now(),
    })


async def run():
    season = await db.seasons.find_one({"status": "active"})
    if not season:
        return {"status": "skipped", "reason": "no_active_season"}
    out = {"created": 0, "skipped": 0, "guilds": []}
    for idx, meta in enumerate(DEMO_GUILDS):
        existing = await db.guilds.find_one({"name": meta["name"]})
        is_new = existing is None
        owner = await _ensure_demo_owner(meta["owner_email"], idx)
        guild = await _ensure_demo_guild(owner["id"], meta, idx)
        adv_ids = await _ensure_demo_adventurers(guild["id"], idx)
        await _ensure_defense_team(guild["id"], adv_ids)
        await _ensure_participation(guild, season, meta)
        out["guilds"].append({"slug": guild["public_id"], "name": guild["name"],
                              "league": meta["league"], "rating": meta["rating"]})
        if is_new:
            out["created"] += 1
        else:
            out["skipped"] += 1
    return {"status": "done", **out}


if __name__ == "__main__":
    print(asyncio.run(run()))
