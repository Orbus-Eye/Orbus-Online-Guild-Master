"""ROUND 18.Reset.1b.ops - Backend Write-Freeze Maintenance Mode.

Middleware minimo che, quando ORBUS_MAINTENANCE_MODE=true (o file flag
/tmp/orbus_maintenance.flag presente), risponde 503 alle richieste
mutanti (POST/PUT/PATCH/DELETE). GET/HEAD/OPTIONS passano invariate
(inclusi preflight CORS OPTIONS).

Vincoli PM (R18.Reset.1b.ops):
    - Zero admin endpoint (nessuna nuova rotta)
    - Zero UI maintenance page (solo response JSON)
    - Zero modifica DB / schema / audit event dal middleware
    - Zero auth change
    - Zero leak tecnico (no stacktrace, no path interno, no versione)
    - Default disabled (ORBUS_MAINTENANCE_MODE=false)
    - Env var toggle richiede supervisor restart. File flag toggle e'
      runtime (rilettura per ogni request, no restart necessario).

Ordine wiring in app_factory.py:
    - CORSMiddleware   (add_middleware primo)   -> eseguito PER ULTIMO
    - CSRFMiddleware   (add_middleware secondo) -> eseguito PER SECONDO
    - MaintenanceMiddleware (add_middleware ultimo) -> eseguito PER PRIMO
    Starlette esegue i middleware in ordine INVERSO all'aggiunta.
    Quindi il maintenance check corre PRIMA di CSRF/CORS/auth deps.
"""
from __future__ import annotations

import os
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAINTENANCE_ENV_VAR = "ORBUS_MAINTENANCE_MODE"
MAINTENANCE_FLAG_FILE = "/tmp/orbus_maintenance.flag"
BLOCKED_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MAINTENANCE_RESPONSE_BODY: dict = {
    "detail": "Orbus è temporaneamente in manutenzione. Riprova tra poco."
}
RETRY_AFTER_SECONDS: int = 60


def _is_maintenance_enabled() -> bool:
    """Rilegge env var + file flag ad OGNI request.

    Env var: ORBUS_MAINTENANCE_MODE. Case-insensitive.
        Accettati come "true": "true", "1", "yes".
        Tutto il resto (compresi "false", "0", "no", "", None) = false.

    File flag: se /tmp/orbus_maintenance.flag esiste (indipendentemente dal
    contenuto), la modalita' e' attiva. Utile per toggle runtime senza
    restart del supervisor (l'env var richiede restart per essere raccolta).
    """
    env_val = os.getenv(MAINTENANCE_ENV_VAR, "false").strip().lower()
    if env_val in {"true", "1", "yes"}:
        return True
    if Path(MAINTENANCE_FLAG_FILE).exists():
        return True
    return False


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """Blocca POST/PUT/PATCH/DELETE quando maintenance mode e' attivo.

    Comportamento:
        - Maintenance OFF (default) -> passa TUTTE le request al next.
        - Maintenance ON:
            - POST/PUT/PATCH/DELETE -> 503 con body JSON localizzato +
              header Retry-After. Zero leak tecnico nel body.
            - GET/HEAD/OPTIONS       -> passa al next (inclusi preflight
              CORS OPTIONS che continua a funzionare regolarmente).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if (
            request.method in BLOCKED_METHODS
            and _is_maintenance_enabled()
        ):
            return JSONResponse(
                content=MAINTENANCE_RESPONSE_BODY,
                status_code=503,
                headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
            )
        return await call_next(request)


__all__ = [
    "MaintenanceMiddleware",
    "MAINTENANCE_ENV_VAR",
    "MAINTENANCE_FLAG_FILE",
    "BLOCKED_METHODS",
    "MAINTENANCE_RESPONSE_BODY",
    "RETRY_AFTER_SECONDS",
    "_is_maintenance_enabled",
]
