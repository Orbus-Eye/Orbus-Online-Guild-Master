"""Phase 9.3 — Email provider abstraction.

Three concrete providers, picked at startup based on `EMAIL_PROVIDER` env var:

* `console`  : log subject/recipient to backend stdout (development default).
              Used by the test suite and by local-dev sessions without a
              Resend API key.
* `resend`   : real Resend transactional email (requires `RESEND_API_KEY`).
              The Resend Python SDK is synchronous; we wrap calls in
              `asyncio.to_thread` so the FastAPI loop stays non-blocking.
* `noop`     : production safety net when `EMAIL_PROVIDER=resend` is set but
              the API key is missing/empty. Calling `.send()` raises so the
              error is loud — but the password-reset flow catches it and
              swallows it (we never reveal account existence).

The factory `get_email_provider()` is memoized: pages handlers / services
hold a single instance per process. Tests can call `reset_provider_cache()`
to clear it between cases.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional, Protocol, runtime_checkable

logger = logging.getLogger("orbus.email")


@runtime_checkable
class EmailProvider(Protocol):
    name: str

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        ...


class ConsoleProvider:
    """Dev/test provider: logs the message instead of sending it."""

    name = "console"

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:  # noqa: ARG002
        logger.info(
            "[EMAIL/console] to=%s subject=%r text_preview=%r",
            to, subject, text[:120].replace("\n", " "),
        )
        return True


class NoopProvider:
    """Production fallback when Resend is requested but not configured.

    `.send()` returns False and logs an error — callers MUST treat False as a
    soft failure (we don't crash the request flow).
    """

    name = "noop"

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:  # noqa: ARG002
        logger.error(
            "[EMAIL/noop] Resend provider requested but RESEND_API_KEY is missing — "
            "email to %s NOT sent (subject=%r)",
            to, subject,
        )
        return False


class ResendProvider:
    """Real Resend SDK provider. Sync SDK wrapped in thread executor."""

    name = "resend"

    def __init__(self, api_key: str, from_addr: str) -> None:
        # Lazy import so the test suite never needs the SDK installed
        import resend  # type: ignore
        resend.api_key = api_key
        self._sdk = resend
        self._from = from_addr

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        params = {
            "from": self._from,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": text,
        }
        try:
            res = await asyncio.to_thread(self._sdk.Emails.send, params)
            logger.info("[EMAIL/resend] sent id=%s to=%s", res.get("id"), to)
            return True
        except Exception as exc:  # pragma: no cover — depends on live network
            logger.error("[EMAIL/resend] failed to=%s err=%s", to, exc)
            return False


_cached_provider: Optional[EmailProvider] = None


def get_email_provider() -> EmailProvider:
    """Resolve the active provider from env (memoized).

    Resolution order:
    * `EMAIL_PROVIDER=console`  → ConsoleProvider
    * `EMAIL_PROVIDER=resend`   → ResendProvider if `RESEND_API_KEY` is set,
                                  otherwise NoopProvider (logs an error)
    * default                   → ConsoleProvider in non-production,
                                  NoopProvider in production
    """
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider

    requested = (os.environ.get("EMAIL_PROVIDER") or "").strip().lower()
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    from_addr = (
        os.environ.get("EMAIL_FROM")
        or os.environ.get("SENDER_EMAIL")
        or "onboarding@resend.dev"
    )
    app_env = os.environ.get("APP_ENV", "development").lower()

    if requested == "console":
        _cached_provider = ConsoleProvider()
    elif requested == "resend":
        if api_key:
            _cached_provider = ResendProvider(api_key=api_key, from_addr=from_addr)
        else:
            _cached_provider = NoopProvider()
    else:
        # No explicit provider → fall back by environment
        if app_env == "production":
            _cached_provider = (
                ResendProvider(api_key=api_key, from_addr=from_addr)
                if api_key else NoopProvider()
            )
        else:
            _cached_provider = ConsoleProvider()
    return _cached_provider


def reset_provider_cache() -> None:
    """Test hook — drop the memoized provider so the next call re-reads env."""
    global _cached_provider
    _cached_provider = None


def detect_locale(accept_language: Optional[str]) -> str:
    """Parse the HTTP `Accept-Language` header → `"en" | "it"`.

    Falls back to `"en"` for any unknown / missing tag. Quality factors `;q=…`
    are honoured — the first tag with the highest q wins. Case-insensitive.
    """
    if not accept_language:
        return "en"
    best_lang = "en"
    best_q = -1.0
    for raw in accept_language.split(","):
        token = raw.strip()
        if not token:
            continue
        if ";" in token:
            tag, *params = [p.strip() for p in token.split(";")]
            q = 1.0
            for p in params:
                if p.startswith("q="):
                    try:
                        q = float(p[2:])
                    except ValueError:
                        q = 0.0
        else:
            tag, q = token, 1.0
        tag_lower = tag.lower()
        # Take primary subtag: "it-IT" → "it"
        primary = tag_lower.split("-", 1)[0]
        if primary in ("en", "it") and q > best_q:
            best_q = q
            best_lang = primary
    return best_lang


__all__ = [
    "EmailProvider",
    "ConsoleProvider",
    "NoopProvider",
    "ResendProvider",
    "get_email_provider",
    "reset_provider_cache",
    "detect_locale",
]
