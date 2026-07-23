"""RT2-B-1B-1 · Guardrail funzionali per provisioning locale isolato.

Funzioni pure di verifica host/database prima di qualsiasi operazione
Mongo. Non hanno side-effect e non toccano il DB.

Fail-stop obbligatori (ognuno lancia `ProvisioningGuardError` con codice):
- `TARGET_ENVIRONMENT_REJECTED` — host != localhost
- `TARGET_DATABASE_REJECTED` — db non in allowlist
- `FORBIDDEN_DATABASE_ORBUS_R16` — db == "orbus_r16" (blocco esplicito)

Regole:
- Host allowlist: `{"localhost", "127.0.0.1", "::1"}` (loopback).
- Database allowlist: `orbus_r16_rt2b_test` (fisso, verifica manuale/idempotency)
  OR regex `^orbus_r16_rt2b_it_[a-z0-9_-]+$` (integration test per-run).
- `orbus_r16` blocked assert esplicito (double-safety).
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse


ALLOWED_STABLE_DATABASE = "orbus_r16_rt2b_test"
IT_DATABASE_REGEX = re.compile(r"^orbus_r16_rt2b_it_[a-z0-9_-]+$")
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
EXPLICIT_FORBIDDEN_DATABASES = frozenset({"orbus_r16"})


class ProvisioningGuardError(RuntimeError):
    """Raised on any guardrail violation. Includes fail-stop `code`."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _extract_host(uri: str) -> Optional[str]:
    """Return hostname from Mongo URI, or None if not parseable."""
    if not uri:
        return None
    if uri.startswith("mongodb://") or uri.startswith("mongodb+srv://"):
        parsed = urlparse(uri)
        return parsed.hostname
    return None


def verify_host_localhost(uri: str) -> str:
    """Assert Mongo host is loopback. Fail-stop `TARGET_ENVIRONMENT_REJECTED`."""
    host = _extract_host(uri)
    if host is None:
        raise ProvisioningGuardError(
            "TARGET_ENVIRONMENT_REJECTED",
            f"unparseable Mongo URI or non-mongodb scheme: {uri!r}",
        )
    if host not in LOOPBACK_HOSTS:
        raise ProvisioningGuardError(
            "TARGET_ENVIRONMENT_REJECTED",
            f"Mongo host must be loopback (localhost/127.0.0.1/::1); got {host!r}",
        )
    return host


def verify_not_orbus_r16(db_name: str) -> None:
    """Explicit block for the production dev DB. Fail-stop `FORBIDDEN_DATABASE_ORBUS_R16`."""
    if db_name in EXPLICIT_FORBIDDEN_DATABASES:
        raise ProvisioningGuardError(
            "FORBIDDEN_DATABASE_ORBUS_R16",
            f"database {db_name!r} is explicitly forbidden for RT2-B provisioning",
        )


def verify_database_allowlist(db_name: str) -> None:
    """Assert db in `{orbus_r16_rt2b_test}` OR matches IT regex.

    Fail-stop `TARGET_DATABASE_REJECTED` on any mismatch.
    Also runs `verify_not_orbus_r16` as a double-safety.
    """
    if not db_name or not isinstance(db_name, str):
        raise ProvisioningGuardError(
            "TARGET_DATABASE_REJECTED",
            f"database name must be a non-empty string; got {db_name!r}",
        )
    verify_not_orbus_r16(db_name)
    if db_name == ALLOWED_STABLE_DATABASE:
        return
    if IT_DATABASE_REGEX.match(db_name):
        return
    raise ProvisioningGuardError(
        "TARGET_DATABASE_REJECTED",
        f"database {db_name!r} is not in allowlist "
        f"({ALLOWED_STABLE_DATABASE!r} or match {IT_DATABASE_REGEX.pattern!r})",
    )


def verify_target(uri: str, db_name: str) -> tuple[str, str]:
    """Compose host + db verification. Return `(host, db_name)` on success."""
    host = verify_host_localhost(uri)
    verify_database_allowlist(db_name)
    return host, db_name


__all__ = [
    "ALLOWED_STABLE_DATABASE",
    "IT_DATABASE_REGEX",
    "LOOPBACK_HOSTS",
    "EXPLICIT_FORBIDDEN_DATABASES",
    "ProvisioningGuardError",
    "verify_host_localhost",
    "verify_not_orbus_r16",
    "verify_database_allowlist",
    "verify_target",
]
