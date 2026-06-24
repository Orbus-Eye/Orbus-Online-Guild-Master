"""
Orbus Online: Guild Master — backend (Phase 1 + 2)
Auth + Guild + Adventurers/Recruitment endpoints. All routes prefixed with /api.
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import re
import uuid
import random
import secrets
import hashlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt
from typing import Annotated
from email_validator import validate_email, EmailNotValidError
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, BeforeValidator, Field, field_validator
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError


def _normalize_email(v):
    if not isinstance(v, str):
        raise ValueError("email must be a string")
    try:
        result = validate_email(
            v.strip(),
            check_deliverability=False,
            test_environment=True,
        )
    except EmailNotValidError as e:
        raise ValueError(str(e))
    return result.normalized.lower()


# Lenient email type: validates format but allows reserved TLDs like `.test`
OrbusEmail = Annotated[str, BeforeValidator(_normalize_email)]

# ─── Config ────────────────────────────────────────────────────────────────────
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7  # TODO Phase 6+: reduce access TTL to ~1h once frontend actively uses refresh endpoint
APP_ENV = os.environ.get("APP_ENV", "development")

# ─── Phase 5: Security Hardening ──────────────────────────────────────────────
REFRESH_TOKEN_TTL_DAYS = 30
PASSWORD_RESET_TTL_MINUTES = 60
LOGIN_LOCK_MAX_ATTEMPTS = 5
LOGIN_LOCK_DURATION_MINUTES = 15
LOGIN_ATTEMPTS_TTL_SECONDS = 86400  # 24h cleanup of stale attempt rows
PASSWORD_REGEX_LETTER = re.compile(r"[A-Za-z]")
PASSWORD_REGEX_DIGIT = re.compile(r"\d")

TESTER_EMAIL = "tester@orbus.test"
TESTER_PASSWORD = "password123"
TESTER_USERNAME = "tester"

# ─── Phase 2: Adventurers / Recruitment ───────────────────────────────────────
RECRUITMENT_COST_GOLD = 20
RECRUITMENT_CANDIDATES_PER_OFFER = 4
OFFER_TTL_MINUTES = 30

RARITY_WEIGHTS = [("Common", 70), ("Uncommon", 20), ("Rare", 8), ("Epic", 2)]
RARITY_BONUS = {"Common": 0, "Uncommon": 0, "Rare": 1, "Epic": 2}

FIRST_NAMES = [
    "Aldric", "Brenna", "Cassian", "Dorin", "Elara", "Faelan", "Gwyn",
    "Hadrian", "Iona", "Joren", "Kael", "Lyra", "Mira", "Nyx", "Oren",
    "Perrin", "Quill", "Rhea", "Soren", "Talia", "Ulric", "Vera", "Wren",
    "Yara", "Zane",
]
LAST_NAMES = [
    "the Bold", "Stoneheart", "Ashwood", "Stormwind", "Ironfoot",
    "Nightshade", "Brightblade",
]

CLASS_SEED = [
    {"slug": "warrior", "name": "Warrior", "role": "Tank",
     "description": "A stalwart front-liner who absorbs punishment so others may strike.",
     "base_strength": 8, "base_agility": 4, "base_intellect": 2,
     "base_endurance": 9, "base_faith": 2},
    {"slug": "rogue", "name": "Rogue", "role": "DPS",
     "description": "A nimble striker who finds the seams between armor plates.",
     "base_strength": 5, "base_agility": 9, "base_intellect": 3,
     "base_endurance": 4, "base_faith": 2},
    {"slug": "mage", "name": "Mage", "role": "DPS",
     "description": "A scholar of the arcane, frail in body but devastating in spell.",
     "base_strength": 2, "base_agility": 4, "base_intellect": 10,
     "base_endurance": 3, "base_faith": 3},
    {"slug": "priest", "name": "Priest", "role": "Healer",
     "description": "A devout channeler whose prayers mend wounds and lift spirits.",
     "base_strength": 2, "base_agility": 3, "base_intellect": 6,
     "base_endurance": 4, "base_faith": 10},
    {"slug": "ranger", "name": "Ranger", "role": "DPS",
     "description": "A keen-eyed scout who strikes from range before the foe closes.",
     "base_strength": 5, "base_agility": 8, "base_intellect": 4,
     "base_endurance": 5, "base_faith": 3},
]

TRAIT_SEED = [
    {"name": "Brave", "description": "Steady under pressure; lends raw strength.",
     "modifier_type": "flat", "affected_stat": "strength",
     "modifier_value": 1.0, "is_positive": True},
    {"name": "Quick Learner", "description": "Soaks up experience faster than peers.",
     "modifier_type": "percent", "affected_stat": "xp_gain",
     "modifier_value": 10.0, "is_positive": True},
    {"name": "Frail", "description": "Weaker constitution; tires sooner.",
     "modifier_type": "flat", "affected_stat": "endurance",
     "modifier_value": -1.0, "is_positive": False},
    {"name": "Sharp Eye", "description": "Spots openings others miss.",
     "modifier_type": "flat", "affected_stat": "agility",
     "modifier_value": 1.0, "is_positive": True},
    {"name": "Devout", "description": "Anchored to a higher calling.",
     "modifier_type": "flat", "affected_stat": "faith",
     "modifier_value": 1.0, "is_positive": True},
]

# ─── Phase 3: Dungeons, Items, Expeditions, Inventory ──────────────────────────
SUCCESS_CHANCE_MIN = 10
SUCCESS_CHANCE_MAX = 95
LOOT_DROP_CHANCE = 0.50  # 50%
LOOT_RARITIES = ["Common", "Uncommon"]  # MVP: no Rare/Epic loot
XP_THRESHOLD_PER_LEVEL = 100  # adventurer levels up when xp >= level * 100

DUNGEON_SEED = [
    {
        "slug": "goblin-warrens",
        "name": "Goblin Warrens",
        "description": "A damp tunnel network occupied by goblin scavengers and their crude traps.",
        "difficulty": 1,
        "required_team_size": 3,
        "base_duration_seconds": 60,
        "recommended_power": 45,
        "base_gold_reward": 35,
        "base_xp_reward": 25,
    },
]

ITEM_SEED = [
    {"slug": "rusted-sword", "name": "Rusted Sword",
     "description": "A pitted blade that has seen too many summers.",
     "item_type": "weapon", "rarity": "Common", "power_score": 1,
     "strength_bonus": 1, "agility_bonus": 0, "intellect_bonus": 0,
     "endurance_bonus": 0, "faith_bonus": 0, "affects_combat": True},
    {"slug": "goblin-dagger", "name": "Goblin Dagger",
     "description": "Crude, jagged, and surprisingly effective in a back alley.",
     "item_type": "weapon", "rarity": "Uncommon", "power_score": 2,
     "strength_bonus": 0, "agility_bonus": 2, "intellect_bonus": 0,
     "endurance_bonus": 0, "faith_bonus": 0, "affects_combat": True},
    {"slug": "cracked-staff", "name": "Cracked Staff",
     "description": "A wizard's staff with a hairline fracture; the focus crystal still hums.",
     "item_type": "weapon", "rarity": "Common", "power_score": 1,
     "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 1,
     "endurance_bonus": 0, "faith_bonus": 1, "affects_combat": True},
    {"slug": "novice-charm", "name": "Novice Charm",
     "description": "A small wooden pendant carved with a quiet prayer.",
     "item_type": "accessory", "rarity": "Common", "power_score": 1,
     "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 0,
     "endurance_bonus": 0, "faith_bonus": 1, "affects_combat": True},
    {"slug": "torn-leather-vest", "name": "Torn Leather Vest",
     "description": "Patched in three places. Still keeps the cold off.",
     "item_type": "armor", "rarity": "Common", "power_score": 4,
     "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 0,
     "endurance_bonus": 1, "faith_bonus": 0, "affects_combat": True},
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("orbus")

# ─── DB ────────────────────────────────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]


# ─── Phase 5: CORS env-gated config ───────────────────────────────────────────
def _resolve_cors_origins() -> list[str]:
    """In production, CORS_ORIGINS must be set explicitly (no '*').
    In dev/preview, defaults to ['*'] for convenience.
    """
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if APP_ENV == "production":
        if not raw or raw == "*":
            raise RuntimeError(
                "APP_ENV=production requires CORS_ORIGINS to be set explicitly "
                "(comma-separated, no '*')."
            )
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if "*" in origins:
            raise RuntimeError("CORS_ORIGINS cannot contain '*' when APP_ENV=production.")
        return origins
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


# ─── Phase 5: Lifespan (replaces deprecated on_event) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Names resolved at runtime; helper functions are defined further below.
    await ensure_indexes()
    await seed_classes_and_traits()
    await seed_dungeons_and_items()
    await seed_tester()
    logger.info("Orbus backend ready (env=%s)", APP_ENV)
    yield
    mongo_client.close()


# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Orbus Online: Guild Master",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

api = APIRouter(prefix="/api")
bearer_scheme = HTTPBearer(auto_error=False)


# ─── Helpers ───────────────────────────────────────────────────────────────────
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": utc_now(),
        "exp": utc_now() + timedelta(days=JWT_EXPIRY_DAYS),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def user_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "email": doc["email"],
        "username": doc["username"],
        "is_admin": doc.get("is_admin", False),
        "created_at": doc["created_at"],
    }


def guild_public(doc: dict) -> dict:
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


def class_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "slug": doc["slug"],
        "role": doc["role"],
        "description": doc.get("description", ""),
        "base_strength": doc["base_strength"],
        "base_agility": doc["base_agility"],
        "base_intellect": doc["base_intellect"],
        "base_endurance": doc["base_endurance"],
        "base_faith": doc["base_faith"],
        "is_active": doc.get("is_active", True),
    }


def trait_public(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "description": doc.get("description", ""),
        "modifier_type": doc["modifier_type"],
        "affected_stat": doc["affected_stat"],
        "modifier_value": doc["modifier_value"],
        "is_positive": doc["is_positive"],
        "is_active": doc.get("is_active", True),
    }


def adventurer_public(doc: dict) -> dict:
    # Phase 6: equipment fields are injected into `doc` upstream as `_equipment_slots`
    # and `_equipment_power` when available; otherwise default to empty/no-power.
    eq_slots = doc.get("_equipment_slots") or _empty_slot_map()
    eq_power = int(doc.get("_equipment_power", 0))
    base_power = _adventurer_unit_power(doc)
    return {
        "id": doc["id"],
        "guild_id": doc["guild_id"],
        "name": doc["name"],
        "adventurer_class_id": doc["adventurer_class_id"],
        "class_name": doc.get("class_name"),
        "class_role": doc.get("class_role"),
        "rarity": doc.get("rarity", "Common"),
        "level": doc.get("level", 1),
        "experience": doc.get("experience", 0),
        "strength": doc["strength"],
        "agility": doc["agility"],
        "intellect": doc["intellect"],
        "endurance": doc["endurance"],
        "faith": doc["faith"],
        "stamina": doc.get("stamina", 100),
        "morale": doc.get("morale", 100),
        "is_available": doc.get("is_available", True),
        "traits": doc.get("traits", []),
        "equipment": eq_slots,
        "base_power": base_power,
        "equipment_power": eq_power,
        "total_power": base_power + eq_power,
        "created_at": doc["created_at"],
        "updated_at": doc.get("updated_at", doc["created_at"]),
    }


def candidate_public(doc: dict) -> dict:
    return {
        "candidate_id": doc["id"],
        "name": doc["name"],
        "adventurer_class_id": doc["adventurer_class_id"],
        "class_name": doc["class_name"],
        "class_role": doc["class_role"],
        "rarity": doc["rarity"],
        "level": doc["level"],
        "experience": doc["experience"],
        "strength": doc["strength"],
        "agility": doc["agility"],
        "intellect": doc["intellect"],
        "endurance": doc["endurance"],
        "faith": doc["faith"],
        "stamina": doc["stamina"],
        "morale": doc["morale"],
        "traits": doc.get("traits", []),
        "cost": RECRUITMENT_COST_GOLD,
        "cost_gold": RECRUITMENT_COST_GOLD,
    }


def _weighted_choice(choices):
    total = sum(w for _, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for value, weight in choices:
        upto += weight
        if upto >= r:
            return value
    return choices[-1][0]


def _generate_name() -> str:
    first = random.choice(FIRST_NAMES)
    if random.random() < 0.6:
        return f"{first} {random.choice(LAST_NAMES)}"
    return first


def _roll_stat(base: int, rarity_bonus: int) -> int:
    return max(1, base + random.randint(-1, 2) + rarity_bonus)


def _pick_random_traits(traits_pool: list) -> list:
    """Pick 0–2 distinct traits with weighted distribution: 50%/35%/15%."""
    if not traits_pool:
        return []
    r = random.random()
    if r < 0.50:
        count = 0
    elif r < 0.85:
        count = 1
    else:
        count = 2
    count = min(count, len(traits_pool))
    if count == 0:
        return []
    chosen = random.sample(traits_pool, count)
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t.get("description", ""),
            "modifier_type": t["modifier_type"],
            "affected_stat": t["affected_stat"],
            "modifier_value": t["modifier_value"],
            "is_positive": t["is_positive"],
        }
        for t in chosen
    ]


def _apply_trait_effects(stats: dict, traits: list) -> dict:
    """Apply 'flat' modifiers on the 5 main stats; floor at 1.
    Phase 5+ TODO: apply percent xp_gain modifier in expedition reward calc."""
    affected = ("strength", "agility", "intellect", "endurance", "faith")
    for t in traits:
        if t.get("modifier_type") == "flat" and t.get("affected_stat") in affected:
            key = t["affected_stat"]
            stats[key] = max(1, int(stats[key]) + int(t.get("modifier_value", 0)))
    return stats


def _generate_candidate(klass: dict, guild_id: str, now: datetime,
                        traits_pool: list | None = None) -> dict:
    rarity = _weighted_choice(RARITY_WEIGHTS)
    bonus = RARITY_BONUS[rarity]
    stats = {
        "strength": _roll_stat(klass["base_strength"], bonus),
        "agility": _roll_stat(klass["base_agility"], bonus),
        "intellect": _roll_stat(klass["base_intellect"], bonus),
        "endurance": _roll_stat(klass["base_endurance"], bonus),
        "faith": _roll_stat(klass["base_faith"], bonus),
    }
    traits = _pick_random_traits(traits_pool or [])
    stats = _apply_trait_effects(stats, traits)
    return {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "name": _generate_name(),
        "adventurer_class_id": klass["id"],
        "class_name": klass["name"],
        "class_role": klass["role"],
        "rarity": rarity,
        "level": 1,
        "experience": 0,
        **stats,
        "stamina": 100,
        "morale": 100,
        "traits": traits,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=OFFER_TTL_MINUTES)).isoformat(),
    }


async def _user_guild_or_404(user_id: str) -> dict:
    guild = await db.guilds.find_one({"owner_user_id": user_id}, {"_id": 0})
    if not guild:
        raise HTTPException(status_code=404, detail="No guild found for this user")
    return guild


# ─── Phase 3 helpers: dungeon/item/expedition/inventory ────────────────────────
def dungeon_public(d: dict) -> dict:
    return {
        "id": d["id"],
        "slug": d["slug"],
        "name": d["name"],
        "description": d.get("description", ""),
        "difficulty": d["difficulty"],
        "required_team_size": d["required_team_size"],
        "base_duration_seconds": d["base_duration_seconds"],
        "recommended_power": d["recommended_power"],
        "base_gold_reward": d["base_gold_reward"],
        "base_xp_reward": d["base_xp_reward"],
        "is_active": d.get("is_active", True),
    }


def item_public(it: dict) -> dict:
    return {
        "id": it["id"],
        "slug": it["slug"],
        "name": it["name"],
        "description": it.get("description", ""),
        "item_type": it["item_type"],
        "rarity": it["rarity"],
        "level_required": it.get("level_required", 1),
        "power_score": it["power_score"],
        "strength_bonus": it.get("strength_bonus", 0),
        "agility_bonus": it.get("agility_bonus", 0),
        "intellect_bonus": it.get("intellect_bonus", 0),
        "endurance_bonus": it.get("endurance_bonus", 0),
        "faith_bonus": it.get("faith_bonus", 0),
        "is_tradeable": it.get("is_tradeable", True),
        "is_cosmetic": it.get("is_cosmetic", False),
        "affects_combat": it.get("affects_combat", False),
        "affects_economy": it.get("affects_economy", False),
        "affects_ranking": it.get("affects_ranking", False),
        "can_be_sold_for_gold": it.get("can_be_sold_for_gold", True),
        "can_be_sold_for_real_money": it.get("can_be_sold_for_real_money", False),
        "is_active": it.get("is_active", True),
    }


def inventory_entry_public(row: dict, item: Optional[dict], equipped_count: int = 0) -> dict:
    total = int(row.get("quantity", 1))
    equipped = max(0, int(equipped_count))
    available = max(0, total - equipped)
    out = {
        "id": row["id"],
        "guild_id": row["guild_id"],
        "item_id": row["item_id"],
        # Backward-compat: `quantity` keeps the legacy semantics (total owned)
        "quantity": total,
        "total_quantity": total,
        "equipped_quantity": equipped,
        "available_quantity": available,
        "acquired_at": row["acquired_at"],
    }
    if item:
        out["item"] = item_public(item)
    return out


def member_public(m: dict) -> dict:
    return {
        "id": m["id"],
        "expedition_id": m["expedition_id"],
        "adventurer_id": m["adventurer_id"],
        "name_snapshot": m["name_snapshot"],
        "class_name_snapshot": m["class_name_snapshot"],
        "role_snapshot": m["role_snapshot"],
        "level_snapshot": m["level_snapshot"],
        "strength_snapshot": m["strength_snapshot"],
        "agility_snapshot": m["agility_snapshot"],
        "intellect_snapshot": m["intellect_snapshot"],
        "endurance_snapshot": m["endurance_snapshot"],
        "faith_snapshot": m["faith_snapshot"],
        # Phase 6 — equipment at the moment of departure (immutable snapshot)
        "equipment_snapshot": m.get("equipment_snapshot", []),
        "equipment_power_snapshot": int(m.get("equipment_power_snapshot", 0)),
        "total_power_snapshot": int(
            m.get("total_power_snapshot")
            if m.get("total_power_snapshot") is not None
            else (
                int(m["strength_snapshot"])
                + int(m["agility_snapshot"])
                + int(m["intellect_snapshot"])
                + int(m["endurance_snapshot"])
                + int(m["faith_snapshot"])
                + int(m.get("level_snapshot", 1)) * 2
                + int(m.get("equipment_power_snapshot", 0))
            )
        ),
    }


def expedition_public(e: dict) -> dict:
    out = {
        "id": e["id"],
        "guild_id": e["guild_id"],
        "dungeon_id": e["dungeon_id"],
        "dungeon_name": e.get("dungeon_name", ""),
        "status": e["status"],
        "started_at": e.get("started_at"),
        "completes_at": e.get("completes_at"),
        "completed_at": e.get("completed_at"),
        "team_power": e.get("team_power", 0),
        "success_chance": e.get("success_chance", 0),
        "final_score": e.get("final_score"),
        "result_summary": e.get("result_summary"),
        "result_log": e.get("result_log"),
        "gold_reward": e.get("gold_reward", 0),
        "xp_reward": e.get("xp_reward", 0),
        "loot_item_ids": e.get("loot_item_ids", []),
        "created_at": e["created_at"],
        "updated_at": e.get("updated_at", e["created_at"]),
    }
    if out["status"] == "in_progress" and out["completes_at"]:
        try:
            ca = datetime.fromisoformat(out["completes_at"])
            remaining = int((ca - utc_now()).total_seconds())
            out["seconds_remaining"] = max(0, remaining)
        except Exception:
            out["seconds_remaining"] = 0
    return out


def validate_item_monetization(item: dict) -> None:
    """Reject inconsistent flags: real-money sale only allowed for pure cosmetics."""
    if item.get("can_be_sold_for_real_money"):
        if (
            not item.get("is_cosmetic", False)
            or item.get("affects_combat", False)
            or item.get("affects_economy", False)
            or item.get("affects_ranking", False)
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid item: can_be_sold_for_real_money requires "
                    "is_cosmetic=true AND affects_combat=false AND "
                    "affects_economy=false AND affects_ranking=false"
                ),
            )


def _adventurer_unit_power(adv: dict) -> int:
    return (
        int(adv["strength"])
        + int(adv["agility"])
        + int(adv["intellect"])
        + int(adv["endurance"])
        + int(adv["faith"])
        + int(adv.get("level", 1)) * 2
    )


# ─── Phase 6: Equipment helpers ────────────────────────────────────────────────
EQUIPMENT_SLOTS = ("weapon", "armor", "accessory")
SLOT_TO_ITEM_TYPE = {"weapon": "weapon", "armor": "armor", "accessory": "accessory"}


def _item_equip_power(item: dict) -> int:
    """Sum of stat-bonus deltas + power_score for an equipped item."""
    return (
        int(item.get("strength_bonus", 0))
        + int(item.get("agility_bonus", 0))
        + int(item.get("intellect_bonus", 0))
        + int(item.get("endurance_bonus", 0))
        + int(item.get("faith_bonus", 0))
        + int(item.get("power_score", 0))
    )


def _empty_slot_map() -> dict:
    return {slot: None for slot in EQUIPMENT_SLOTS}


def _equipped_slot_entry(equipped_row: dict, item: dict) -> dict:
    """Shape returned to clients for a single occupied slot."""
    return {
        "equipped_item_id": equipped_row["id"],
        "item": item_public(item),
        "slot": equipped_row["slot"],
    }


def _item_summary_for_snapshot(equipped_row: dict, item: dict) -> dict:
    """Frozen, minimal shape persisted on expedition_members.equipment_snapshot."""
    return {
        "slot": equipped_row["slot"],
        "item_id": item["id"],
        "item_name": item["name"],
        "rarity": item.get("rarity", "Common"),
        "strength_bonus": int(item.get("strength_bonus", 0)),
        "agility_bonus": int(item.get("agility_bonus", 0)),
        "intellect_bonus": int(item.get("intellect_bonus", 0)),
        "endurance_bonus": int(item.get("endurance_bonus", 0)),
        "faith_bonus": int(item.get("faith_bonus", 0)),
        "power_score": int(item.get("power_score", 0)),
    }


async def _load_equipment_for_adventurer(adventurer_id: str) -> tuple[dict, int, list[dict]]:
    """Return (slot_map_for_public_response, equipment_power, raw_equipped_rows_with_item).

    `raw_equipped_rows_with_item` is a list of {row, item} dicts (used for snapshots).
    """
    rows = await db.equipped_items.find(
        {"adventurer_id": adventurer_id}, {"_id": 0}
    ).to_list(10)
    slots = _empty_slot_map()
    eq_power = 0
    raw: list[dict] = []
    if not rows:
        return slots, 0, raw
    item_ids = list({r["item_id"] for r in rows})
    items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(50)
    items_by_id = {i["id"]: i for i in items}
    for r in rows:
        item = items_by_id.get(r["item_id"])
        if not item:
            continue
        if r["slot"] in slots:
            slots[r["slot"]] = _equipped_slot_entry(r, item)
        eq_power += _item_equip_power(item)
        raw.append({"row": r, "item": item})
    return slots, eq_power, raw


async def _load_equipment_for_guild(guild_id: str) -> dict[str, tuple[dict, int]]:
    """Batch-load equipment for all adventurers in a guild. Returns
    {adventurer_id: (slot_map, equipment_power)}.
    """
    rows = await db.equipped_items.find(
        {"guild_id": guild_id}, {"_id": 0}
    ).to_list(2000)
    if not rows:
        return {}
    item_ids = list({r["item_id"] for r in rows})
    items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(500)
    items_by_id = {i["id"]: i for i in items}
    by_adv: dict[str, tuple[dict, int]] = {}
    for r in rows:
        item = items_by_id.get(r["item_id"])
        if not item:
            continue
        slots, power = by_adv.get(r["adventurer_id"], (_empty_slot_map(), 0))
        slots[r["slot"]] = _equipped_slot_entry(r, item)
        by_adv[r["adventurer_id"]] = (slots, power + _item_equip_power(item))
    return by_adv


async def _count_equipped_for_guild_items(guild_id: str) -> dict[str, int]:
    """Returns {item_id: equipped_count} for the guild."""
    pipeline = [
        {"$match": {"guild_id": guild_id}},
        {"$group": {"_id": "$item_id", "count": {"$sum": 1}}},
    ]
    out: dict[str, int] = {}
    async for row in db.equipped_items.aggregate(pipeline):
        out[row["_id"]] = int(row["count"])
    return out


def _build_equipment_response(adventurer: dict, slots: dict, eq_power: int) -> dict:
    base_power = _adventurer_unit_power(adventurer)
    return {
        "adventurer_id": adventurer["id"],
        "slots": slots,
        "base_power": base_power,
        "equipment_power": eq_power,
        "total_power": base_power + eq_power,
    }


def compute_team_power(members: list) -> int:
    """members is a list of adventurer dicts (live or snapshot fields ending in _snapshot).

    Phase 6: if a member already carries `total_power_snapshot`, that value is
    treated as authoritative for the per-member contribution (already includes
    base + level + equipment). Otherwise the legacy formula (base only) is used.
    """
    def get(a, key):
        return a.get(key, a.get(key + "_snapshot", 0))

    base = 0
    roles = set()
    for a in members:
        if a.get("total_power_snapshot") is not None:
            base += int(a["total_power_snapshot"])
        else:
            base += (
                int(get(a, "strength"))
                + int(get(a, "agility"))
                + int(get(a, "intellect"))
                + int(get(a, "endurance"))
                + int(get(a, "faith"))
                + int(get(a, "level") or 1) * 2
            )
        role = a.get("class_role") or a.get("role_snapshot")
        if role:
            roles.add(role)
    if "Tank" in roles:
        base += 5
    if "Healer" in roles:
        base += 5
    if "DPS" in roles:
        base += 5
    if {"Tank", "Healer", "DPS"}.issubset(roles):
        base += 10
    return base


def compute_success_chance(team_power: int, recommended_power: int) -> int:
    raw = 50 + (team_power - recommended_power)
    return max(SUCCESS_CHANCE_MIN, min(SUCCESS_CHANCE_MAX, raw))


CLASS_LEVELUP_STAT = {
    "Warrior": lambda: random.choice(["strength", "endurance"]),
    "Rogue": lambda: "agility",
    "Mage": lambda: "intellect",
    "Priest": lambda: "faith",
    "Ranger": lambda: random.choice(["agility", "strength"]),
}


def _resolve_levelup(adv: dict) -> dict:
    """Apply level-up loop in-place on a dict. Returns the updated dict."""
    while adv["experience"] >= adv["level"] * XP_THRESHOLD_PER_LEVEL:
        threshold = adv["level"] * XP_THRESHOLD_PER_LEVEL
        adv["experience"] -= threshold
        adv["level"] += 1
        picker = CLASS_LEVELUP_STAT.get(adv.get("class_name", ""))
        stat = picker() if picker else "strength"
        adv[stat] = adv.get(stat, 0) + 1
    return adv


def _build_result_log(dungeon_name: str, member_names: list, success: bool) -> str:
    names = ", ".join(member_names) if member_names else "Your party"
    if success:
        return (
            f"Your party of {names} entered the {dungeon_name} at dawn. "
            f"After hours of careful work, they cleared the main chamber and returned "
            f"with what they could carry. The expedition was successful."
        )
    return (
        f"Your party pushed too deep into the {dungeon_name}. "
        f"A hidden ambush split the formation, and the group was forced to retreat. "
        f"The expedition failed, but the survivors returned with valuable experience."
    )


async def _complete_one_expedition(exp_id: str) -> None:
    """Atomically claim and finalize a single due expedition. Idempotent."""
    claimed = await db.expeditions.find_one_and_update(
        {"id": exp_id, "status": "in_progress"},
        {"$set": {"status": "completing"}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        return  # already completed by a concurrent caller

    dungeon = await db.dungeons.find_one({"id": claimed["dungeon_id"]}, {"_id": 0})
    if not dungeon:
        # Defensive fallback — should never happen
        await db.expeditions.update_one(
            {"id": exp_id},
            {"$set": {"status": "failed", "result_summary": "Failed",
                      "result_log": "Dungeon data unavailable.",
                      "completed_at": utc_now().isoformat()}},
        )
        return

    members = await db.expedition_members.find(
        {"expedition_id": exp_id}, {"_id": 0}
    ).to_list(50)

    final_score = random.randint(1, 100)
    success = final_score <= claimed["success_chance"]
    now = utc_now()

    if success:
        gold_reward = dungeon["base_gold_reward"]
        xp_per_member = dungeon["base_xp_reward"]
        loot_ids: list = []
        if random.random() < LOOT_DROP_CHANCE:
            pool = await db.items.find(
                {"is_active": True, "rarity": {"$in": LOOT_RARITIES}}, {"_id": 0}
            ).to_list(100)
            if pool:
                loot_ids = [random.choice(pool)["id"]]
    else:
        gold_reward = round(dungeon["base_gold_reward"] * 0.25)
        xp_per_member = round(dungeon["base_xp_reward"] * 0.4)
        loot_ids = []

    # Apply rewards to guild gold
    await db.guilds.update_one(
        {"id": claimed["guild_id"]},
        {"$inc": {"gold": gold_reward}, "$set": {"updated_at": now.isoformat()}},
    )

    # Apply XP + free adventurers, with level-up loop
    for m in members:
        adv = await db.adventurers.find_one(
            {"id": m["adventurer_id"], "guild_id": claimed["guild_id"]}, {"_id": 0}
        )
        if not adv:
            continue
        adv["experience"] = int(adv.get("experience", 0)) + int(xp_per_member)
        adv = _resolve_levelup(adv)
        adv["is_available"] = True
        adv["updated_at"] = now.isoformat()
        await db.adventurers.update_one(
            {"id": m["adventurer_id"]},
            {"$set": {
                "experience": adv["experience"],
                "level": adv["level"],
                "strength": adv["strength"],
                "agility": adv["agility"],
                "intellect": adv["intellect"],
                "endurance": adv["endurance"],
                "faith": adv["faith"],
                "is_available": True,
                "updated_at": now.isoformat(),
            }},
        )

    # Apply loot to inventory (upsert quantity)
    for item_id in loot_ids:
        await db.inventory_items.update_one(
            {"guild_id": claimed["guild_id"], "item_id": item_id},
            {
                "$inc": {"quantity": 1},
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "guild_id": claimed["guild_id"],
                    "item_id": item_id,
                    "acquired_at": now.isoformat(),
                },
            },
            upsert=True,
        )

    member_names = [m["name_snapshot"] for m in members]
    result_summary = "Success" if success else "Failed"
    result_log = _build_result_log(dungeon["name"], member_names, success)

    await db.expeditions.update_one(
        {"id": exp_id},
        {"$set": {
            "status": "completed",
            "completed_at": now.isoformat(),
            "final_score": final_score,
            "gold_reward": gold_reward,
            "xp_reward": xp_per_member,
            "loot_item_ids": loot_ids,
            "result_summary": result_summary,
            "result_log": result_log,
            "updated_at": now.isoformat(),
        }},
    )


async def complete_due_expeditions(guild_id: str) -> int:
    """Lazy sweep: complete any in_progress expedition whose completes_at <= now."""
    now_iso = utc_now().isoformat()
    due = await db.expeditions.find(
        {
            "guild_id": guild_id,
            "status": "in_progress",
            "completes_at": {"$lte": now_iso},
        },
        {"_id": 0, "id": 1},
    ).to_list(100)
    for d in due:
        await _complete_one_expedition(d["id"])
    return len(due)




async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(creds.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ─── Phase 5: Auth security helpers ────────────────────────────────────────────
PASSWORD_RULES_MESSAGE = (
    "Password must be at least 8 characters and contain a letter and a digit"
)


def _validate_password_strength(password: str) -> None:
    """Raise HTTP 400 if password does not satisfy the Phase-5 policy.

    Rules: min 8 chars + at least one letter + at least one digit.
    Validation is intentionally performed at the route layer (not in Pydantic),
    so the API returns HTTP 400 rather than 422.
    """
    if (
        len(password) < 8
        or not PASSWORD_REGEX_LETTER.search(password)
        or not PASSWORD_REGEX_DIGIT.search(password)
    ):
        raise HTTPException(status_code=400, detail=PASSWORD_RULES_MESSAGE)


def _hash_token(token: str) -> str:
    """SHA-256 hex digest. Used for opaque refresh/reset tokens at rest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_opaque_token() -> str:
    """URL-safe 256-bit opaque token."""
    return secrets.token_urlsafe(32)


async def _check_login_lock(email: str) -> None:
    """Raise HTTP 429 (with Retry-After header) if email is currently locked out."""
    row = await db.login_attempts.find_one({"email": email})
    if not row:
        return
    locked_until = row.get("locked_until")
    if locked_until and isinstance(locked_until, datetime):
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > utc_now():
            remaining = max(1, int((locked_until - utc_now()).total_seconds()))
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(remaining)},
            )


async def _record_login_failure(email: str) -> None:
    now = utc_now()
    row = await db.login_attempts.find_one_and_update(
        {"email": email},
        {
            "$inc": {"failed_count": 1},
            "$set": {"last_attempt_at": now},
            "$setOnInsert": {"email": email, "created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if row.get("failed_count", 0) >= LOGIN_LOCK_MAX_ATTEMPTS:
        lock_until = now + timedelta(minutes=LOGIN_LOCK_DURATION_MINUTES)
        await db.login_attempts.update_one(
            {"email": email},
            {"$set": {"locked_until": lock_until, "last_attempt_at": now}},
        )


async def _reset_login_attempts(email: str) -> None:
    await db.login_attempts.delete_one({"email": email})


async def _create_refresh_token(user_id: str) -> str:
    """Issue a new opaque refresh token and persist its hash."""
    token = _new_opaque_token()
    now = utc_now()
    await db.refresh_tokens.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "token_hash": _hash_token(token),
        "created_at": now,
        "expires_at": now + timedelta(days=REFRESH_TOKEN_TTL_DAYS),
        "revoked": False,
    })
    return token


async def _consume_refresh_token(token: str) -> dict:
    """Validate a refresh token. Returns the user doc or raises 401."""
    row = await db.refresh_tokens.find_one({"token_hash": _hash_token(token)})
    if not row or row.get("revoked"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    expires_at = row.get("expires_at")
    if expires_at and isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utc_now():
            raise HTTPException(status_code=401, detail="Refresh token expired")
    user = await db.users.find_one({"id": row["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def _revoke_refresh_token(token: str) -> bool:
    res = await db.refresh_tokens.update_one(
        {"token_hash": _hash_token(token)},
        {"$set": {"revoked": True, "revoked_at": utc_now()}},
    )
    return res.modified_count > 0


async def _revoke_all_refresh_tokens(user_id: str) -> int:
    res = await db.refresh_tokens.update_many(
        {"user_id": user_id, "revoked": False},
        {"$set": {"revoked": True, "revoked_at": utc_now()}},
    )
    return res.modified_count


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: OrbusEmail
    username: str = Field(min_length=2, max_length=32)
    # Password is validated in the route handler (HTTP 400) — not via Pydantic (422)
    password: str = Field(max_length=128)


class LoginIn(BaseModel):
    email: OrbusEmail
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=8, max_length=256)


class LogoutIn(BaseModel):
    refresh_token: str = Field(min_length=8, max_length=256)


class PasswordResetRequestIn(BaseModel):
    email: OrbusEmail


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=8, max_length=256)
    # new_password is validated in the route handler (HTTP 400) — not via Pydantic (422)
    new_password: str = Field(max_length=128)


class GuildCreateIn(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    description: str = Field(default="", max_length=300)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("name must be at least 3 characters")
        return v


class RecruitIn(BaseModel):
    candidate_id: str = Field(min_length=8, max_length=64)


class ExpeditionStartIn(BaseModel):
    dungeon_id: str = Field(min_length=8, max_length=64)
    adventurer_ids: list[str] = Field(min_length=1, max_length=10)


class EquipIn(BaseModel):
    item_id: str = Field(min_length=8, max_length=64)
    slot: str = Field(min_length=3, max_length=20)


class UnequipIn(BaseModel):
    slot: str = Field(min_length=3, max_length=20)


# ─── Endpoints: Health ─────────────────────────────────────────────────────────
@api.get("/health")
async def health():
    return {"status": "ok", "env": APP_ENV}


# ─── Endpoints: Auth ───────────────────────────────────────────────────────────
@api.post("/auth/register", status_code=201)
async def register(payload: RegisterIn):
    _validate_password_strength(payload.password)
    email = payload.email.lower().strip()
    username = payload.username.strip()

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    now = utc_now()
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email,
        "username": username,
        "password_hash": hash_password(payload.password),
        "is_admin": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    token = create_access_token(user_id)
    refresh = await _create_refresh_token(user_id)
    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_public(user_doc),
    }


@api.post("/auth/login")
async def login(payload: LoginIn):
    email = payload.email.lower().strip()
    await _check_login_lock(email)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        await _record_login_failure(email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await _reset_login_attempts(email)
    token = create_access_token(user["id"])
    refresh = await _create_refresh_token(user["id"])
    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_public(user),
    }


@api.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"user": user_public(current_user)}


# ─── Endpoints: Auth (Phase 5 refresh / logout / password-reset) ──────────────
@api.post("/auth/refresh")
async def refresh_token_endpoint(payload: RefreshIn):
    user = await _consume_refresh_token(payload.refresh_token)
    new_access = create_access_token(user["id"])
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "user": user_public(user),
    }


@api.post("/auth/logout")
async def logout(payload: LogoutIn):
    revoked = await _revoke_refresh_token(payload.refresh_token)
    return {"revoked": revoked}


@api.post("/auth/password-reset/request")
async def password_reset_request(payload: PasswordResetRequestIn):
    """Always returns 200 to avoid email enumeration. Logs link to console."""
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if user:
        token = _new_opaque_token()
        now = utc_now()
        await db.password_reset_tokens.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "token_hash": _hash_token(token),
            "created_at": now,
            "expires_at": now + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
            "used": False,
        })
        logger.info(
            "[PASSWORD-RESET] email=%s reset_token=%s expires_in=%dmin",
            email, token, PASSWORD_RESET_TTL_MINUTES,
        )
    return {"status": "ok"}


@api.post("/auth/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirmIn):
    _validate_password_strength(payload.new_password)
    row = await db.password_reset_tokens.find_one({"token_hash": _hash_token(payload.token)})
    if not row or row.get("used"):
        raise HTTPException(status_code=400, detail="Invalid or already-used reset token")
    expires_at = row.get("expires_at")
    if expires_at and isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utc_now():
            raise HTTPException(status_code=400, detail="Reset token expired")

    user = await db.users.find_one({"id": row["user_id"]})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    now = utc_now()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password_hash": hash_password(payload.new_password),
            "updated_at": now.isoformat(),
        }},
    )
    await db.password_reset_tokens.update_one(
        {"id": row["id"]},
        {"$set": {"used": True, "used_at": now}},
    )
    # Security best-practice: revoke all existing refresh tokens for this user
    await _revoke_all_refresh_tokens(user["id"])
    await _reset_login_attempts(user["email"])
    return {"status": "ok"}


# ─── Endpoints: Guilds ─────────────────────────────────────────────────────────
@api.post("/guilds", status_code=201)
async def create_guild(payload: GuildCreateIn, current_user: dict = Depends(get_current_user)):
    existing = await db.guilds.find_one({"owner_user_id": current_user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="You already own a guild")

    now = utc_now()
    guild_doc = {
        "id": str(uuid.uuid4()),
        "owner_user_id": current_user["id"],
        "name": payload.name.strip(),
        "description": payload.description.strip(),
        "level": 1,
        "reputation": 0,
        "gold": 100,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.guilds.insert_one(guild_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="You already own a guild")

    return {"guild": guild_public(guild_doc)}


@api.get("/guilds/me")
async def get_my_guild(current_user: dict = Depends(get_current_user)):
    guild = await db.guilds.find_one({"owner_user_id": current_user["id"]}, {"_id": 0})
    if not guild:
        raise HTTPException(status_code=404, detail="No guild found for this user")
    # Phase-3 lazy completion sweep
    await complete_due_expeditions(guild["id"])
    # Re-fetch guild after sweep (gold may have changed)
    guild = await db.guilds.find_one({"owner_user_id": current_user["id"]}, {"_id": 0})

    adv_count = await db.adventurers.count_documents({"guild_id": guild["id"]})
    active_exp = await db.expeditions.count_documents(
        {"guild_id": guild["id"], "status": "in_progress"}
    )
    last_exp = await db.expeditions.find_one(
        {"guild_id": guild["id"]},
        {"_id": 0, "id": 1, "status": 1, "result_summary": 1, "completed_at": 1, "created_at": 1},
        sort=[("created_at", -1)],
    )
    payload = guild_public(guild)
    payload["adventurer_count"] = adv_count
    payload["active_expedition_count"] = active_exp
    payload["last_expedition_id"] = last_exp["id"] if last_exp else None
    payload["last_expedition_summary"] = last_exp.get("result_summary") if last_exp else None
    return {"guild": payload}


# ─── Endpoints: Dungeons / Items (read-only catalogs) ──────────────────────────
@api.get("/dungeons")
async def list_dungeons():
    rows = await db.dungeons.find({"is_active": True}, {"_id": 0}).sort("difficulty", 1).to_list(100)
    return {"dungeons": [dungeon_public(d) for d in rows]}


@api.get("/items")
async def list_items():
    rows = await db.items.find({"is_active": True}, {"_id": 0}).sort("name", 1).to_list(500)
    return {"items": [item_public(i) for i in rows]}


# ─── Endpoints: Expeditions ────────────────────────────────────────────────────
@api.post("/expeditions", status_code=201)
async def start_expedition(
    payload: ExpeditionStartIn, current_user: dict = Depends(get_current_user)
):
    guild = await _user_guild_or_404(current_user["id"])

    dungeon = await db.dungeons.find_one(
        {"id": payload.dungeon_id, "is_active": True}, {"_id": 0}
    )
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon not found")

    # Validate team composition
    ids = payload.adventurer_ids
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=400, detail="Duplicate adventurer in team")
    if len(ids) != dungeon["required_team_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"This dungeon requires exactly {dungeon['required_team_size']} adventurers",
        )

    members_live = []
    for aid in ids:
        adv = await db.adventurers.find_one(
            {"id": aid, "guild_id": guild["id"]}, {"_id": 0}
        )
        if not adv:
            raise HTTPException(status_code=404, detail=f"Adventurer {aid} not found in your guild")
        if not adv.get("is_available", True):
            raise HTTPException(
                status_code=400,
                detail=f"Adventurer {adv['name']} is not available",
            )
        members_live.append(adv)

    # Phase 6: load equipment for each member; snapshot is frozen at departure.
    members_for_power: list[dict] = []
    equipment_by_adv: dict[str, dict] = {}
    for adv in members_live:
        slots, eq_power, raw = await _load_equipment_for_adventurer(adv["id"])
        snapshot = [_item_summary_for_snapshot(r["row"], r["item"]) for r in raw]
        base = _adventurer_unit_power(adv)
        equipment_by_adv[adv["id"]] = {
            "equipment_snapshot": snapshot,
            "equipment_power_snapshot": eq_power,
            "total_power_snapshot": base + eq_power,
        }
        members_for_power.append({
            **adv,
            "total_power_snapshot": base + eq_power,
        })

    team_power = compute_team_power(members_for_power)
    success_chance = compute_success_chance(team_power, dungeon["recommended_power"])

    now = utc_now()
    completes_at = now + timedelta(seconds=dungeon["base_duration_seconds"])
    exp_id = str(uuid.uuid4())
    exp_doc = {
        "id": exp_id,
        "guild_id": guild["id"],
        "dungeon_id": dungeon["id"],
        "dungeon_name": dungeon["name"],
        "status": "in_progress",
        "started_at": now.isoformat(),
        "completes_at": completes_at.isoformat(),
        "completed_at": None,
        "team_power": team_power,
        "success_chance": success_chance,
        "final_score": None,
        "result_summary": None,
        "result_log": None,
        "gold_reward": 0,
        "xp_reward": 0,
        "loot_item_ids": [],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.expeditions.insert_one(exp_doc)

    members_docs = []
    for adv in members_live:
        eq = equipment_by_adv.get(adv["id"], {
            "equipment_snapshot": [],
            "equipment_power_snapshot": 0,
            "total_power_snapshot": _adventurer_unit_power(adv),
        })
        m = {
            "id": str(uuid.uuid4()),
            "expedition_id": exp_id,
            "adventurer_id": adv["id"],
            "name_snapshot": adv["name"],
            "class_name_snapshot": adv.get("class_name", ""),
            "role_snapshot": adv.get("class_role", ""),
            "level_snapshot": adv.get("level", 1),
            "strength_snapshot": adv["strength"],
            "agility_snapshot": adv["agility"],
            "intellect_snapshot": adv["intellect"],
            "endurance_snapshot": adv["endurance"],
            "faith_snapshot": adv["faith"],
            "equipment_snapshot": eq["equipment_snapshot"],
            "equipment_power_snapshot": int(eq["equipment_power_snapshot"]),
            "total_power_snapshot": int(eq["total_power_snapshot"]),
        }
        members_docs.append(m)
    if members_docs:
        await db.expedition_members.insert_many([dict(m) for m in members_docs])

    # Lock the adventurers
    await db.adventurers.update_many(
        {"id": {"$in": ids}, "guild_id": guild["id"]},
        {"$set": {"is_available": False, "updated_at": now.isoformat()}},
    )

    return {
        "expedition": expedition_public(exp_doc),
        "members": [member_public(m) for m in members_docs],
    }


@api.get("/expeditions")
async def list_expeditions(current_user: dict = Depends(get_current_user)):
    guild = await _user_guild_or_404(current_user["id"])
    await complete_due_expeditions(guild["id"])
    rows = (
        await db.expeditions.find({"guild_id": guild["id"]}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(200)
    )
    return {"expeditions": [expedition_public(e) for e in rows]}


@api.get("/expeditions/{expedition_id}")
async def get_expedition(
    expedition_id: str, current_user: dict = Depends(get_current_user)
):
    guild = await _user_guild_or_404(current_user["id"])
    await complete_due_expeditions(guild["id"])
    exp = await db.expeditions.find_one(
        {"id": expedition_id, "guild_id": guild["id"]}, {"_id": 0}
    )
    if not exp:
        # Don't leak 403 vs 404
        raise HTTPException(status_code=404, detail="Expedition not found")

    members = await db.expedition_members.find(
        {"expedition_id": expedition_id}, {"_id": 0}
    ).to_list(50)

    # Expand loot items
    loot_ids = exp.get("loot_item_ids", [])
    loot_items = []
    if loot_ids:
        items = await db.items.find({"id": {"$in": loot_ids}}, {"_id": 0}).to_list(50)
        # preserve order of loot_ids with possible duplicates
        item_by_id = {it["id"]: it for it in items}
        for lid in loot_ids:
            if lid in item_by_id:
                loot_items.append(item_public(item_by_id[lid]))

    return {
        "expedition": expedition_public(exp),
        "members": [member_public(m) for m in members],
        "loot_items": loot_items,
    }


# ─── Endpoints: Inventory ──────────────────────────────────────────────────────
@api.get("/inventory")
async def list_inventory(current_user: dict = Depends(get_current_user)):
    guild = await _user_guild_or_404(current_user["id"])
    rows = await db.inventory_items.find(
        {"guild_id": guild["id"]}, {"_id": 0}
    ).sort("acquired_at", -1).to_list(500)
    # Resolve item info in a single query
    item_ids = list({r["item_id"] for r in rows})
    items_map = {}
    if item_ids:
        items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(500)
        items_map = {it["id"]: it for it in items}
    equipped_counts = await _count_equipped_for_guild_items(guild["id"])
    return {
        "inventory": [
            inventory_entry_public(
                r, items_map.get(r["item_id"]), equipped_counts.get(r["item_id"], 0)
            )
            for r in rows
        ]
    }


# ─── Endpoints: Adventurer Classes (read-only in Phase 2) ──────────────────────
@api.get("/adventurer-classes")
async def list_classes():
    classes = await db.adventurer_classes.find(
        {"is_active": True}, {"_id": 0}
    ).sort("name", ASCENDING).to_list(100)
    return {"classes": [class_public(c) for c in classes]}


# ─── Endpoints: Recruitment ────────────────────────────────────────────────────
@api.get("/recruitment/candidates")
async def get_recruitment_candidates(current_user: dict = Depends(get_current_user)):
    guild = await _user_guild_or_404(current_user["id"])

    classes = await db.adventurer_classes.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)
    if not classes:
        raise HTTPException(status_code=500, detail="No adventurer classes seeded")

    # Replace prior offers for this guild
    await db.recruitment_offers.delete_many({"guild_id": guild["id"]})

    traits_pool = await db.adventurer_traits.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)

    now = utc_now()
    candidates = [
        _generate_candidate(random.choice(classes), guild["id"], now, traits_pool)
        for _ in range(RECRUITMENT_CANDIDATES_PER_OFFER)
    ]
    await db.recruitment_offers.insert_many([dict(c) for c in candidates])

    return {
        "candidates": [candidate_public(c) for c in candidates],
        "guild_gold": guild.get("gold", 0),
        "cost_gold": RECRUITMENT_COST_GOLD,
        "expires_in_minutes": OFFER_TTL_MINUTES,
    }


@api.post("/recruitment/recruit", status_code=201)
async def recruit_adventurer(
    payload: RecruitIn, current_user: dict = Depends(get_current_user)
):
    guild = await _user_guild_or_404(current_user["id"])

    # Step 1: atomically claim the offer (delete) — owner-scoped lookup
    offer = await db.recruitment_offers.find_one_and_delete(
        {"id": payload.candidate_id, "guild_id": guild["id"]},
        projection={"_id": 0},
    )
    if not offer:
        raise HTTPException(
            status_code=404, detail="Candidate not found or already recruited"
        )

    # Expiry check (applicative — supports envs without TTL background pass yet)
    try:
        exp = datetime.fromisoformat(offer["expires_at"])
    except Exception:
        exp = utc_now() + timedelta(minutes=1)
    if exp < utc_now():
        raise HTTPException(status_code=404, detail="Candidate offer has expired")

    # Step 2: atomically decrement gold with affordability check
    now = utc_now()
    updated_guild = await db.guilds.find_one_and_update(
        {"id": guild["id"], "gold": {"$gte": RECRUITMENT_COST_GOLD}},
        {
            "$inc": {"gold": -RECRUITMENT_COST_GOLD},
            "$set": {"updated_at": now.isoformat()},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_guild:
        # Refund offer (best-effort) so user can retry once they have gold
        offer_to_restore = {k: v for k, v in offer.items() if k != "_id"}
        try:
            await db.recruitment_offers.insert_one(offer_to_restore)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Insufficient gold")

    # Step 3: create the adventurer from offer-saved stats (NOT client-provided)
    adventurer_doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "name": offer["name"],
        "adventurer_class_id": offer["adventurer_class_id"],
        "class_name": offer["class_name"],
        "class_role": offer["class_role"],
        "rarity": offer["rarity"],
        "level": offer["level"],
        "experience": offer["experience"],
        "strength": offer["strength"],
        "agility": offer["agility"],
        "intellect": offer["intellect"],
        "endurance": offer["endurance"],
        "faith": offer["faith"],
        "stamina": offer["stamina"],
        "morale": offer["morale"],
        "traits": offer.get("traits", []),
        "is_available": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.adventurers.insert_one(adventurer_doc)

    return {
        "adventurer": adventurer_public(adventurer_doc),
        "guild": {"gold": updated_guild["gold"]},
    }


# ─── Endpoints: Adventurers ────────────────────────────────────────────────────
@api.get("/adventurers")
async def list_adventurers(current_user: dict = Depends(get_current_user)):
    guild = await _user_guild_or_404(current_user["id"])
    rows = (
        await db.adventurers.find({"guild_id": guild["id"]}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(500)
    )
    equip_map = await _load_equipment_for_guild(guild["id"])
    out = []
    for r in rows:
        slots, power = equip_map.get(r["id"], (_empty_slot_map(), 0))
        r["_equipment_slots"] = slots
        r["_equipment_power"] = power
        out.append(adventurer_public(r))
    return {"adventurers": out}


# ─── Endpoints: Equipment (Phase 6) ────────────────────────────────────────────
async def _adventurer_owned_or_404(adventurer_id: str, guild_id: str) -> dict:
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    return adv


@api.get("/adventurers/{adventurer_id}/equipment")
async def get_adventurer_equipment(
    adventurer_id: str, current_user: dict = Depends(get_current_user)
):
    guild = await _user_guild_or_404(current_user["id"])
    adv = await _adventurer_owned_or_404(adventurer_id, guild["id"])
    slots, eq_power, _raw = await _load_equipment_for_adventurer(adv["id"])
    return _build_equipment_response(adv, slots, eq_power)


@api.post("/adventurers/{adventurer_id}/equip", status_code=201)
async def equip_item(
    adventurer_id: str, payload: EquipIn, current_user: dict = Depends(get_current_user)
):
    guild = await _user_guild_or_404(current_user["id"])
    adv = await _adventurer_owned_or_404(adventurer_id, guild["id"])

    if not adv.get("is_available", True):
        raise HTTPException(
            status_code=400,
            detail="Cannot modify equipment of adventurer currently in expedition",
        )

    slot = payload.slot.strip().lower()
    if slot not in EQUIPMENT_SLOTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid slot '{slot}'. Must be one of: {', '.join(EQUIPMENT_SLOTS)}",
        )

    item = await db.items.find_one(
        {"id": payload.item_id, "is_active": True}, {"_id": 0}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    expected_type = SLOT_TO_ITEM_TYPE[slot]
    if item.get("item_type") != expected_type:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Item type '{item.get('item_type')}' cannot be equipped in slot '{slot}'"
            ),
        )

    inv_row = await db.inventory_items.find_one(
        {"guild_id": guild["id"], "item_id": payload.item_id}, {"_id": 0}
    )
    if not inv_row:
        raise HTTPException(status_code=404, detail="Item not in your guild inventory")
    total_qty = int(inv_row.get("quantity", 0))
    equipped_qty = await db.equipped_items.count_documents(
        {"guild_id": guild["id"], "item_id": payload.item_id}
    )
    available = total_qty - equipped_qty
    if available <= 0:
        raise HTTPException(
            status_code=400, detail="Not enough copies of this item available"
        )

    now = utc_now()
    new_row = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "adventurer_id": adv["id"],
        "item_id": payload.item_id,
        "slot": slot,
        "equipped_at": now.isoformat(),
    }
    try:
        await db.equipped_items.insert_one(new_row)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400, detail="Slot already occupied, unequip first"
        )

    slots, eq_power, _raw = await _load_equipment_for_adventurer(adv["id"])
    return _build_equipment_response(adv, slots, eq_power)


@api.post("/adventurers/{adventurer_id}/unequip")
async def unequip_item(
    adventurer_id: str, payload: UnequipIn, current_user: dict = Depends(get_current_user)
):
    guild = await _user_guild_or_404(current_user["id"])
    adv = await _adventurer_owned_or_404(adventurer_id, guild["id"])

    if not adv.get("is_available", True):
        raise HTTPException(
            status_code=400,
            detail="Cannot modify equipment of adventurer currently in expedition",
        )

    slot = payload.slot.strip().lower()
    if slot not in EQUIPMENT_SLOTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid slot '{slot}'. Must be one of: {', '.join(EQUIPMENT_SLOTS)}",
        )

    res = await db.equipped_items.delete_one(
        {"adventurer_id": adv["id"], "slot": slot, "guild_id": guild["id"]}
    )
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"No item equipped in slot '{slot}'")

    slots, eq_power, _raw = await _load_equipment_for_adventurer(adv["id"])
    return _build_equipment_response(adv, slots, eq_power)



# ════════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL — all endpoints under /api/admin/* protected by get_admin_user
# ════════════════════════════════════════════════════════════════════════════════

def _slug_ok(s: str) -> bool:
    import re
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s or ""))


def _strip_db_fields(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "_id"}


# ─── Admin: Classes ────────────────────────────────────────────────────────────
@api.get("/admin/classes")
async def admin_list_classes(_: dict = Depends(get_admin_user)):
    rows = await db.adventurer_classes.find({}, {"_id": 0}).sort("name", ASCENDING).to_list(200)
    return {"classes": [class_public(r) for r in rows]}


@api.post("/admin/classes", status_code=201)
async def admin_create_class(payload: dict, _: dict = Depends(get_admin_user)):
    required = ["name", "slug", "role", "base_strength", "base_agility",
                "base_intellect", "base_endurance", "base_faith"]
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if not _slug_ok(payload["slug"]):
        raise HTTPException(400, "slug must be kebab-case (a-z, 0-9, hyphens)")
    if payload["role"] not in ("Tank", "DPS", "Healer"):
        raise HTTPException(400, "role must be one of Tank/DPS/Healer")
    now = utc_now()
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "slug": payload["slug"].strip(),
        "role": payload["role"],
        "description": payload.get("description", "").strip(),
        "base_strength": int(payload["base_strength"]),
        "base_agility": int(payload["base_agility"]),
        "base_intellect": int(payload["base_intellect"]),
        "base_endurance": int(payload["base_endurance"]),
        "base_faith": int(payload["base_faith"]),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.adventurer_classes.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "A class with this slug already exists")
    return {"class": class_public(doc)}


@api.patch("/admin/classes/{class_id}")
async def admin_update_class(class_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Class not found")
    updates = {}
    for k in ("name", "description"):
        if k in payload:
            updates[k] = str(payload[k]).strip()
    for k in ("base_strength", "base_agility", "base_intellect",
              "base_endurance", "base_faith"):
        if k in payload:
            updates[k] = int(payload[k])
    if "role" in payload:
        if payload["role"] not in ("Tank", "DPS", "Healer"):
            raise HTTPException(400, "role must be one of Tank/DPS/Healer")
        updates["role"] = payload["role"]
    if "is_active" in payload:
        updates["is_active"] = bool(payload["is_active"])
    if updates:
        updates["updated_at"] = utc_now().isoformat()
        await db.adventurer_classes.update_one({"id": class_id}, {"$set": updates})
    updated = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    return {"class": class_public(updated)}


@api.post("/admin/classes/{class_id}/toggle-active")
async def admin_toggle_class(class_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Class not found")
    new_active = not existing.get("is_active", True)
    await db.adventurer_classes.update_one(
        {"id": class_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.adventurer_classes.find_one({"id": class_id}, {"_id": 0})
    return {"class": class_public(updated)}


# ─── Admin: Traits ─────────────────────────────────────────────────────────────
VALID_AFFECTED_STAT = ("strength", "agility", "intellect", "endurance", "faith", "xp_gain")


@api.get("/admin/traits")
async def admin_list_traits(_: dict = Depends(get_admin_user)):
    rows = await db.adventurer_traits.find({}, {"_id": 0}).sort("name", ASCENDING).to_list(200)
    return {"traits": [trait_public(r) for r in rows]}


@api.post("/admin/traits", status_code=201)
async def admin_create_trait(payload: dict, _: dict = Depends(get_admin_user)):
    for k in ("name", "modifier_type", "affected_stat", "modifier_value"):
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if payload["modifier_type"] not in ("flat", "percent"):
        raise HTTPException(400, "modifier_type must be flat|percent")
    if payload["affected_stat"] not in VALID_AFFECTED_STAT:
        raise HTTPException(400, f"affected_stat must be one of {VALID_AFFECTED_STAT}")
    now = utc_now()
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "description": payload.get("description", "").strip(),
        "modifier_type": payload["modifier_type"],
        "affected_stat": payload["affected_stat"],
        "modifier_value": float(payload["modifier_value"]),
        "is_positive": bool(payload.get("is_positive", True)),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.adventurer_traits.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "A trait with this name already exists")
    return {"trait": trait_public(doc)}


@api.patch("/admin/traits/{trait_id}")
async def admin_update_trait(trait_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Trait not found")
    updates = {}
    for k in ("name", "description"):
        if k in payload:
            updates[k] = str(payload[k]).strip()
    if "modifier_type" in payload:
        if payload["modifier_type"] not in ("flat", "percent"):
            raise HTTPException(400, "modifier_type must be flat|percent")
        updates["modifier_type"] = payload["modifier_type"]
    if "affected_stat" in payload:
        if payload["affected_stat"] not in VALID_AFFECTED_STAT:
            raise HTTPException(400, f"affected_stat must be one of {VALID_AFFECTED_STAT}")
        updates["affected_stat"] = payload["affected_stat"]
    if "modifier_value" in payload:
        updates["modifier_value"] = float(payload["modifier_value"])
    if "is_positive" in payload:
        updates["is_positive"] = bool(payload["is_positive"])
    if "is_active" in payload:
        updates["is_active"] = bool(payload["is_active"])
    if updates:
        updates["updated_at"] = utc_now().isoformat()
        await db.adventurer_traits.update_one({"id": trait_id}, {"$set": updates})
    updated = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    return {"trait": trait_public(updated)}


@api.post("/admin/traits/{trait_id}/toggle-active")
async def admin_toggle_trait(trait_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Trait not found")
    new_active = not existing.get("is_active", True)
    await db.adventurer_traits.update_one(
        {"id": trait_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.adventurer_traits.find_one({"id": trait_id}, {"_id": 0})
    return {"trait": trait_public(updated)}


# ─── Admin: Dungeons ───────────────────────────────────────────────────────────
@api.get("/admin/dungeons")
async def admin_list_dungeons(_: dict = Depends(get_admin_user)):
    rows = await db.dungeons.find({}, {"_id": 0}).sort("difficulty", 1).to_list(200)
    return {"dungeons": [dungeon_public(r) for r in rows]}


@api.post("/admin/dungeons", status_code=201)
async def admin_create_dungeon(payload: dict, _: dict = Depends(get_admin_user)):
    required = ["name", "slug", "difficulty", "required_team_size",
                "base_duration_seconds", "recommended_power",
                "base_gold_reward", "base_xp_reward"]
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if not _slug_ok(payload["slug"]):
        raise HTTPException(400, "slug must be kebab-case")
    now = utc_now()
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "slug": payload["slug"].strip(),
        "description": payload.get("description", "").strip(),
        "difficulty": int(payload["difficulty"]),
        "required_team_size": int(payload["required_team_size"]),
        "base_duration_seconds": int(payload["base_duration_seconds"]),
        "recommended_power": int(payload["recommended_power"]),
        "base_gold_reward": int(payload["base_gold_reward"]),
        "base_xp_reward": int(payload["base_xp_reward"]),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.dungeons.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "A dungeon with this slug already exists")
    return {"dungeon": dungeon_public(doc)}


@api.patch("/admin/dungeons/{dungeon_id}")
async def admin_update_dungeon(dungeon_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Dungeon not found")
    updates = {}
    for k in ("name", "description"):
        if k in payload:
            updates[k] = str(payload[k]).strip()
    for k in ("difficulty", "required_team_size", "base_duration_seconds",
              "recommended_power", "base_gold_reward", "base_xp_reward"):
        if k in payload:
            updates[k] = int(payload[k])
    if "is_active" in payload:
        updates["is_active"] = bool(payload["is_active"])
    if updates:
        updates["updated_at"] = utc_now().isoformat()
        await db.dungeons.update_one({"id": dungeon_id}, {"$set": updates})
    updated = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    return {"dungeon": dungeon_public(updated)}


@api.post("/admin/dungeons/{dungeon_id}/toggle-active")
async def admin_toggle_dungeon(dungeon_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Dungeon not found")
    new_active = not existing.get("is_active", True)
    await db.dungeons.update_one(
        {"id": dungeon_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.dungeons.find_one({"id": dungeon_id}, {"_id": 0})
    return {"dungeon": dungeon_public(updated)}


# ─── Admin: Items ──────────────────────────────────────────────────────────────
VALID_ITEM_TYPES = ("weapon", "armor", "accessory", "consumable")
VALID_RARITIES = ("Common", "Uncommon", "Rare", "Epic")


def _build_item_doc(payload: dict, existing: Optional[dict] = None) -> dict:
    base = dict(existing) if existing else {
        "id": str(uuid.uuid4()),
        "level_required": 1,
        "strength_bonus": 0, "agility_bonus": 0, "intellect_bonus": 0,
        "endurance_bonus": 0, "faith_bonus": 0,
        "is_tradeable": True, "is_cosmetic": False,
        "affects_combat": True, "affects_economy": False, "affects_ranking": False,
        "can_be_sold_for_gold": True, "can_be_sold_for_real_money": False,
        "is_active": True,
    }
    # Apply patch fields
    for k in ("name", "slug", "description", "item_type", "rarity"):
        if k in payload:
            base[k] = str(payload[k]).strip()
    for k in ("level_required", "power_score", "strength_bonus", "agility_bonus",
              "intellect_bonus", "endurance_bonus", "faith_bonus"):
        if k in payload:
            base[k] = int(payload[k])
    for k in ("is_tradeable", "is_cosmetic", "affects_combat", "affects_economy",
              "affects_ranking", "can_be_sold_for_gold",
              "can_be_sold_for_real_money", "is_active"):
        if k in payload:
            base[k] = bool(payload[k])
    return base


@api.get("/admin/items")
async def admin_list_items(_: dict = Depends(get_admin_user)):
    rows = await db.items.find({}, {"_id": 0}).sort("name", 1).to_list(500)
    return {"items": [item_public(r) for r in rows]}


@api.post("/admin/items", status_code=201)
async def admin_create_item(payload: dict, _: dict = Depends(get_admin_user)):
    required = ["name", "slug", "item_type", "rarity", "power_score"]
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"Missing field: {k}")
    if not _slug_ok(payload["slug"]):
        raise HTTPException(400, "slug must be kebab-case")
    if payload["item_type"] not in VALID_ITEM_TYPES:
        raise HTTPException(400, f"item_type must be one of {VALID_ITEM_TYPES}")
    if payload["rarity"] not in VALID_RARITIES:
        raise HTTPException(400, f"rarity must be one of {VALID_RARITIES}")
    doc = _build_item_doc(payload)
    now = utc_now()
    doc["created_at"] = now.isoformat()
    doc["updated_at"] = now.isoformat()
    validate_item_monetization(doc)
    try:
        await db.items.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "An item with this slug already exists")
    return {"item": item_public(doc)}


@api.patch("/admin/items/{item_id}")
async def admin_update_item(item_id: str, payload: dict, _: dict = Depends(get_admin_user)):
    existing = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Item not found")
    if "item_type" in payload and payload["item_type"] not in VALID_ITEM_TYPES:
        raise HTTPException(400, f"item_type must be one of {VALID_ITEM_TYPES}")
    if "rarity" in payload and payload["rarity"] not in VALID_RARITIES:
        raise HTTPException(400, f"rarity must be one of {VALID_RARITIES}")
    merged = _build_item_doc(payload, existing=existing)
    merged["updated_at"] = utc_now().isoformat()
    validate_item_monetization(merged)
    await db.items.update_one({"id": item_id}, {"$set": _strip_db_fields(merged)})
    updated = await db.items.find_one({"id": item_id}, {"_id": 0})
    return {"item": item_public(updated)}


@api.post("/admin/items/{item_id}/toggle-active")
async def admin_toggle_item(item_id: str, _: dict = Depends(get_admin_user)):
    existing = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Item not found")
    new_active = not existing.get("is_active", True)
    await db.items.update_one(
        {"id": item_id},
        {"$set": {"is_active": new_active, "updated_at": utc_now().isoformat()}},
    )
    updated = await db.items.find_one({"id": item_id}, {"_id": 0})
    return {"item": item_public(updated)}



# ─── Wire router ───────────────────────────────────────────────────────────────
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Startup: indexes + seed ───────────────────────────────────────────────────
async def ensure_indexes():
    await db.users.create_index([("email", ASCENDING)], unique=True, name="users_email_unique")
    await db.users.create_index([("id", ASCENDING)], unique=True, name="users_id_unique")
    await db.guilds.create_index([("id", ASCENDING)], unique=True, name="guilds_id_unique")
    await db.guilds.create_index(
        [("owner_user_id", ASCENDING)], unique=True, name="guilds_owner_unique"
    )
    await db.guilds.create_index([("name", ASCENDING)], name="guilds_name_idx")
    # Phase 2
    await db.adventurer_classes.create_index(
        [("slug", ASCENDING)], unique=True, name="classes_slug_unique"
    )
    await db.adventurer_classes.create_index(
        [("id", ASCENDING)], unique=True, name="classes_id_unique"
    )
    await db.adventurer_traits.create_index(
        [("name", ASCENDING)], unique=True, name="traits_name_unique"
    )
    await db.adventurers.create_index(
        [("id", ASCENDING)], unique=True, name="adventurers_id_unique"
    )
    await db.adventurers.create_index(
        [("guild_id", ASCENDING)], name="adventurers_guild_idx"
    )
    await db.recruitment_offers.create_index(
        [("id", ASCENDING)], unique=True, name="offers_id_unique"
    )
    await db.recruitment_offers.create_index(
        [("guild_id", ASCENDING)], name="offers_guild_idx"
    )
    # Phase 3
    await db.dungeons.create_index([("slug", ASCENDING)], unique=True, name="dungeons_slug_unique")
    await db.dungeons.create_index([("id", ASCENDING)], unique=True, name="dungeons_id_unique")
    await db.items.create_index([("slug", ASCENDING)], unique=True, name="items_slug_unique")
    await db.items.create_index([("id", ASCENDING)], unique=True, name="items_id_unique")
    await db.expeditions.create_index([("id", ASCENDING)], unique=True, name="expeditions_id_unique")
    await db.expeditions.create_index(
        [("guild_id", ASCENDING), ("status", ASCENDING)], name="expeditions_guild_status_idx"
    )
    await db.expeditions.create_index(
        [("completes_at", ASCENDING)], name="expeditions_completes_at_idx"
    )
    await db.expedition_members.create_index(
        [("id", ASCENDING)], unique=True, name="members_id_unique"
    )
    await db.expedition_members.create_index(
        [("expedition_id", ASCENDING)], name="members_exp_idx"
    )
    await db.inventory_items.create_index(
        [("id", ASCENDING)], unique=True, name="inv_id_unique"
    )
    await db.inventory_items.create_index(
        [("guild_id", ASCENDING), ("item_id", ASCENDING)], unique=True, name="inv_guild_item_unique"
    )
    # Phase 6: equipped_items
    await db.equipped_items.create_index(
        [("id", ASCENDING)], unique=True, name="equipped_id_unique"
    )
    await db.equipped_items.create_index(
        [("guild_id", ASCENDING)], name="equipped_guild_idx"
    )
    await db.equipped_items.create_index(
        [("adventurer_id", ASCENDING)], name="equipped_adv_idx"
    )
    await db.equipped_items.create_index(
        [("item_id", ASCENDING)], name="equipped_item_idx"
    )
    await db.equipped_items.create_index(
        [("adventurer_id", ASCENDING), ("slot", ASCENDING)],
        unique=True,
        name="equipped_adv_slot_unique",
    )
    # Phase 5: security collections with TTL
    await db.login_attempts.create_index(
        [("email", ASCENDING)], unique=True, name="login_attempts_email_unique"
    )
    await db.login_attempts.create_index(
        [("last_attempt_at", ASCENDING)],
        expireAfterSeconds=LOGIN_ATTEMPTS_TTL_SECONDS,
        name="login_attempts_ttl",
    )
    await db.refresh_tokens.create_index(
        [("token_hash", ASCENDING)], unique=True, name="refresh_tokens_hash_unique"
    )
    await db.refresh_tokens.create_index(
        [("user_id", ASCENDING)], name="refresh_tokens_user_idx"
    )
    await db.refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="refresh_tokens_ttl",
    )
    await db.password_reset_tokens.create_index(
        [("token_hash", ASCENDING)], unique=True, name="password_reset_hash_unique"
    )
    await db.password_reset_tokens.create_index(
        [("user_id", ASCENDING)], name="password_reset_user_idx"
    )
    await db.password_reset_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="password_reset_ttl",
    )


async def seed_classes_and_traits():
    """Idempotent content seed (runs in all envs, including production)."""
    now = utc_now()
    for c in CLASS_SEED:
        await db.adventurer_classes.update_one(
            {"slug": c["slug"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now.isoformat(),
                },
                "$set": {
                    "name": c["name"],
                    "slug": c["slug"],
                    "role": c["role"],
                    "description": c["description"],
                    "base_strength": c["base_strength"],
                    "base_agility": c["base_agility"],
                    "base_intellect": c["base_intellect"],
                    "base_endurance": c["base_endurance"],
                    "base_faith": c["base_faith"],
                    "is_active": True,
                    "updated_at": now.isoformat(),
                },
            },
            upsert=True,
        )

    for t in TRAIT_SEED:
        await db.adventurer_traits.update_one(
            {"name": t["name"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now.isoformat(),
                },
                "$set": {
                    "name": t["name"],
                    "description": t["description"],
                    "modifier_type": t["modifier_type"],
                    "affected_stat": t["affected_stat"],
                    "modifier_value": t["modifier_value"],
                    "is_positive": t["is_positive"],
                    "is_active": True,
                    "updated_at": now.isoformat(),
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d classes and %d traits", len(CLASS_SEED), len(TRAIT_SEED))


async def seed_dungeons_and_items():
    """Idempotent Phase-3 content seed."""
    now = utc_now()
    for d in DUNGEON_SEED:
        await db.dungeons.update_one(
            {"slug": d["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now.isoformat()},
                "$set": {
                    "slug": d["slug"],
                    "name": d["name"],
                    "description": d["description"],
                    "difficulty": d["difficulty"],
                    "required_team_size": d["required_team_size"],
                    "base_duration_seconds": d["base_duration_seconds"],
                    "recommended_power": d["recommended_power"],
                    "base_gold_reward": d["base_gold_reward"],
                    "base_xp_reward": d["base_xp_reward"],
                    "is_active": True,
                    "updated_at": now.isoformat(),
                },
            },
            upsert=True,
        )

    for it in ITEM_SEED:
        full = {
            "level_required": 1,
            "is_tradeable": True,
            "is_cosmetic": False,
            "affects_economy": False,
            "affects_ranking": False,
            "can_be_sold_for_gold": True,
            "can_be_sold_for_real_money": False,
            **it,
        }
        validate_item_monetization(full)
        await db.items.update_one(
            {"slug": full["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now.isoformat()},
                "$set": {
                    "slug": full["slug"],
                    "name": full["name"],
                    "description": full["description"],
                    "item_type": full["item_type"],
                    "rarity": full["rarity"],
                    "level_required": full["level_required"],
                    "power_score": full["power_score"],
                    "strength_bonus": full["strength_bonus"],
                    "agility_bonus": full["agility_bonus"],
                    "intellect_bonus": full["intellect_bonus"],
                    "endurance_bonus": full["endurance_bonus"],
                    "faith_bonus": full["faith_bonus"],
                    "is_tradeable": full["is_tradeable"],
                    "is_cosmetic": full["is_cosmetic"],
                    "affects_combat": full["affects_combat"],
                    "affects_economy": full["affects_economy"],
                    "affects_ranking": full["affects_ranking"],
                    "can_be_sold_for_gold": full["can_be_sold_for_gold"],
                    "can_be_sold_for_real_money": full["can_be_sold_for_real_money"],
                    "is_active": True,
                    "updated_at": now.isoformat(),
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d dungeons and %d items", len(DUNGEON_SEED), len(ITEM_SEED))


async def seed_tester():
    if APP_ENV == "production":
        logger.info("APP_ENV=production → skipping tester seed")
        return
    now = utc_now()
    existing = await db.users.find_one({"email": TESTER_EMAIL})
    if existing:
        # Idempotent: ensure tester is admin in non-prod, even if user pre-existed
        if not existing.get("is_admin"):
            await db.users.update_one(
                {"email": TESTER_EMAIL},
                {"$set": {"is_admin": True, "updated_at": now.isoformat()}},
            )
            logger.info("Promoted existing tester to is_admin=True")
        else:
            logger.info("Tester account already exists with is_admin=True")
        return
    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": TESTER_EMAIL,
            "username": TESTER_USERNAME,
            "password_hash": hash_password(TESTER_PASSWORD),
            "is_admin": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
    )
    logger.info("Seeded tester account: %s (is_admin=True)", TESTER_EMAIL)


# Phase 5: startup/shutdown is now handled by the `lifespan` context manager
# defined near the top of this module (see `lifespan(app)`).
