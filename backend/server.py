"""
Orbus Online: Guild Master — backend (Phase 1 + 2)
Auth + Guild + Adventurers/Recruitment endpoints. All routes prefixed with /api.
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import random
import logging
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
JWT_EXPIRY_DAYS = 7
APP_ENV = os.environ.get("APP_ENV", "development")

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("orbus")

# ─── DB ────────────────────────────────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Orbus Online: Guild Master",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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


def _generate_candidate(klass: dict, guild_id: str, now: datetime) -> dict:
    rarity = _weighted_choice(RARITY_WEIGHTS)
    bonus = RARITY_BONUS[rarity]
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
        "strength": _roll_stat(klass["base_strength"], bonus),
        "agility": _roll_stat(klass["base_agility"], bonus),
        "intellect": _roll_stat(klass["base_intellect"], bonus),
        "endurance": _roll_stat(klass["base_endurance"], bonus),
        "faith": _roll_stat(klass["base_faith"], bonus),
        "stamina": 100,
        "morale": 100,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=OFFER_TTL_MINUTES)).isoformat(),
    }


async def _user_guild_or_404(user_id: str) -> dict:
    guild = await db.guilds.find_one({"owner_user_id": user_id}, {"_id": 0})
    if not guild:
        raise HTTPException(status_code=404, detail="No guild found for this user")
    return guild




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


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: OrbusEmail
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: OrbusEmail
    password: str = Field(min_length=1, max_length=128)


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


# ─── Endpoints: Health ─────────────────────────────────────────────────────────
@api.get("/health")
async def health():
    return {"status": "ok", "env": APP_ENV}


# ─── Endpoints: Auth ───────────────────────────────────────────────────────────
@api.post("/auth/register", status_code=201)
async def register(payload: RegisterIn):
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
    return {"access_token": token, "token_type": "bearer", "user": user_public(user_doc)}


@api.post("/auth/login")
async def login(payload: LoginIn):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "user": user_public(user)}


@api.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"user": user_public(current_user)}


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
    adv_count = await db.adventurers.count_documents({"guild_id": guild["id"]})
    payload = guild_public(guild)
    payload["adventurer_count"] = adv_count
    return {"guild": payload}


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

    now = utc_now()
    candidates = [
        _generate_candidate(random.choice(classes), guild["id"], now)
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
    return {"adventurers": [adventurer_public(r) for r in rows]}


# ─── Wire router ───────────────────────────────────────────────────────────────
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
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


async def seed_tester():
    if APP_ENV == "production":
        logger.info("APP_ENV=production → skipping tester seed")
        return
    existing = await db.users.find_one({"email": TESTER_EMAIL})
    if existing:
        logger.info("Tester account already exists, skipping seed")
        return
    now = utc_now()
    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": TESTER_EMAIL,
            "username": TESTER_USERNAME,
            "password_hash": hash_password(TESTER_PASSWORD),
            "is_admin": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
    )
    logger.info("Seeded tester account: %s", TESTER_EMAIL)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_classes_and_traits()
    await seed_tester()
    logger.info("Orbus backend ready (env=%s)", APP_ENV)


@app.on_event("shutdown")
async def on_shutdown():
    mongo_client.close()
