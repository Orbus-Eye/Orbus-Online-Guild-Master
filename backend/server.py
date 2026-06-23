"""
Orbus Online: Guild Master — backend (Phase 1)
Auth + Guild endpoints. All routes prefixed with /api.
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
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
from pymongo import ASCENDING
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
    return {"guild": guild_public(guild)}


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
    await seed_tester()
    logger.info("Orbus backend ready (env=%s)", APP_ENV)


@app.on_event("shutdown")
async def on_shutdown():
    mongo_client.close()
