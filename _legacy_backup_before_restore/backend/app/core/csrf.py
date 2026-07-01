"""ROUND 11.1 Slice 2 — CSRF double-submit middleware.

Verifies the `X-CSRF-Token` header equals the `csrf_token` cookie on
mutating requests **when the caller authenticates via the access cookie**.
Bearer-authenticated requests are exempt (legacy + server-to-server).
Login / register / logout / csrf / health are explicitly exempt.

Threat model: a malicious cross-origin site cannot read the `csrf_token`
cookie (we don't expose it on cross-origin requests via SameSite=Lax),
nor read it from JS on the attacker origin, so it cannot forge the
matching header. The httpOnly access cookie is sent automatically, but
without the matching header the request is rejected with 403.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
)

MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

# Paths exempt from CSRF verification.
EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/logout",
    "/api/auth/csrf",
    "/api/auth/refresh",
    "/api/auth/password-reset/request",
    "/api/auth/password-reset/confirm",
    "/api/health",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        path = request.url.path
        # GET/HEAD/OPTIONS safe by RFC; only mutating methods need CSRF.
        if method not in MUTATING_METHODS:
            return await call_next(request)
        if path in EXEMPT_PATHS:
            return await call_next(request)
        # Bearer fallback: if no access cookie, treat as Bearer-authed
        # (legacy client / server-to-server) and let the auth dependency
        # validate it. CSRF is not applicable for Bearer auth.
        access_cookie = request.cookies.get(ACCESS_COOKIE_NAME)
        if not access_cookie:
            return await call_next(request)
        # Cookie-authed mutating request → enforce double-submit.
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if (
            not csrf_cookie or not csrf_header
            or csrf_cookie != csrf_header
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": {
                    "code": "auth.csrf.invalid",
                    "user_message": (
                        "Token CSRF non valido. Aggiorna la pagina."
                    ),
                }},
            )
        return await call_next(request)


__all__ = ["CSRFMiddleware"]
