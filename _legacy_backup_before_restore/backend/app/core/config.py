"""Centralised env/config accessors for the backend.

Combines os.environ lookups with the gameplay/security constants from
`app.shared.constants` so the rest of the app has a single import surface.
"""
import os

from app.shared.constants import (
    JWT_ALGORITHM,
    JWT_EXPIRY_DAYS as ACCESS_TOKEN_TTL_DAYS,
    REFRESH_TOKEN_TTL_DAYS,
    PASSWORD_RESET_TTL_MINUTES,
    LOGIN_LOCK_MAX_ATTEMPTS as LOGIN_LOCKOUT_THRESHOLD,
    LOGIN_LOCK_DURATION_MINUTES as LOGIN_LOCKOUT_MINUTES,
    LOGIN_ATTEMPTS_TTL_SECONDS,
)


# ─── Env-driven settings ─────────────────────────────────────────────────────
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
APP_ENV = os.environ.get("APP_ENV", "development")


def get_cors_origins() -> list[str]:
    """Resolve allowed CORS origins. In production, `CORS_ORIGINS` must be
    set explicitly (no wildcard). In dev/preview, defaults to ['*']."""
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


__all__ = [
    "MONGO_URL",
    "DB_NAME",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "APP_ENV",
    "ACCESS_TOKEN_TTL_DAYS",
    "REFRESH_TOKEN_TTL_DAYS",
    "PASSWORD_RESET_TTL_MINUTES",
    "LOGIN_LOCKOUT_THRESHOLD",
    "LOGIN_LOCKOUT_MINUTES",
    "LOGIN_ATTEMPTS_TTL_SECONDS",
    "get_cors_origins",
]
