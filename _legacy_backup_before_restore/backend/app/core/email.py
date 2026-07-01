"""Phase 9.3 — Email provider abstraction.

Concrete providers, picked at startup based on `EMAIL_PROVIDER` env var:

* `console`  : log subject/recipient to backend stdout (development default).
* `smtp`     : generic SMTP w/ STARTTLS (IONOS, Gmail-SMTP, custom MX, …).
               Sync `smtplib` wrapped in `asyncio.to_thread`.
* `resend`   : Resend transactional email (requires `RESEND_API_KEY`).
* `noop`     : production safety net when a real provider is requested but
               not configured. `.send()` returns False loudly.

The factory `get_email_provider()` is memoized: handlers / services hold a
single instance per process. Tests can call `reset_provider_cache()`.

Security notes
--------------
* Credentials (`RESEND_API_KEY`, `SMTP_PASSWORD`) are NEVER logged.
* SMTP error logging captures only `type(exc).__name__` to avoid leaking
  AUTH details from `smtplib` exception strings.
* `to=` and `subject=` are logged; full body is not (only a 120-char text
  preview in console-mode dev logs).
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

    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        ...


def _resolved_reply_to(reply_to: Optional[str]) -> Optional[str]:
    """Pick explicit reply_to over env default."""
    if reply_to:
        return reply_to
    env = (os.environ.get("EMAIL_REPLY_TO") or "").strip()
    return env or None


class ConsoleProvider:
    """Dev/test provider: logs the message instead of sending it."""

    name = "console"

    async def send(
        self, to: str, subject: str, html: str, text: str,
        reply_to: Optional[str] = None,
    ) -> bool:  # noqa: ARG002
        logger.info(
            "[EMAIL/console] to=%s subject=%r text_preview=%r",
            to, subject, text[:120].replace("\n", " "),
        )
        return True


class NoopProvider:
    """Production fallback when a real provider is requested but not
    configured. `.send()` returns False and logs an error — callers MUST
    treat False as a soft failure (we don't crash the request flow).
    """

    name = "noop"

    def __init__(self, reason: str = "provider misconfigured") -> None:
        self._reason = reason

    async def send(
        self, to: str, subject: str, html: str, text: str,
        reply_to: Optional[str] = None,
    ) -> bool:  # noqa: ARG002
        logger.error(
            "[EMAIL/noop] %s — email to %s NOT sent (subject=%r)",
            self._reason, to, subject,
        )
        return False


class ResendProvider:
    """Real Resend SDK provider. Sync SDK wrapped in thread executor."""

    name = "resend"

    def __init__(self, api_key: str, from_addr: str) -> None:
        import resend  # type: ignore
        resend.api_key = api_key
        self._sdk = resend
        self._from = from_addr

    async def send(
        self, to: str, subject: str, html: str, text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        params = {
            "from": self._from,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": text,
        }
        eff_reply = _resolved_reply_to(reply_to)
        if eff_reply:
            params["reply_to"] = [eff_reply]
        try:
            res = await asyncio.to_thread(self._sdk.Emails.send, params)
            logger.info("[EMAIL/resend] sent id=%s to=%s", res.get("id"), to)
            return True
        except Exception as exc:
            logger.error("[EMAIL/resend] failed to=%s err=%s", to, type(exc).__name__)
            return False


class SMTPProvider:
    """Generic SMTP provider (STARTTLS by default).

    Tested mock-only — no live IONOS/Gmail connection in CI. Wraps the
    sync `smtplib` flow inside `asyncio.to_thread` so the FastAPI event
    loop stays non-blocking.

    The password is held in memory but never logged. AUTH errors are
    sanitised: only the exception class name is emitted.
    """

    name = "smtp"

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_addr: str,
        use_tls: bool = True,
        timeout: int = 10,
    ) -> None:
        self.host = host
        self.port = int(port)
        self.username = username
        self._password = password  # private, never logged
        self.from_addr = from_addr
        self.use_tls = bool(use_tls)
        self.timeout = int(timeout)

    def _build_message(
        self, to: str, subject: str, html: str, text: str,
        reply_to: Optional[str],
    ):
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_addr or self.username
        msg["To"] = to
        eff_reply = _resolved_reply_to(reply_to)
        if eff_reply:
            msg["Reply-To"] = eff_reply
        msg.set_content(text or "")
        msg.add_alternative(html or "", subtype="html")
        return msg

    async def send(
        self, to: str, subject: str, html: str, text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        msg = self._build_message(to, subject, html, text, reply_to)

        def _send_sync() -> bool:
            import smtplib
            import ssl
            ctx = ssl.create_default_context()
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as srv:
                srv.ehlo()
                if self.use_tls:
                    srv.starttls(context=ctx)
                    srv.ehlo()
                srv.login(self.username, self._password)
                srv.send_message(msg)
            return True

        try:
            ok = await asyncio.to_thread(_send_sync)
            if ok:
                logger.info(
                    "[EMAIL/smtp] sent host=%s to=%s subject=%r",
                    self.host, to, subject,
                )
            return ok
        except Exception as exc:
            # Sanitised — never log password, never log raw exception text
            # (smtplib may include username in AUTH error strings).
            logger.error(
                "[EMAIL/smtp] send failed host=%s to=%s err=%s",
                self.host, to, type(exc).__name__,
            )
            return False


_cached_provider: Optional[EmailProvider] = None


def get_email_provider() -> EmailProvider:
    """Resolve the active provider from env (memoized).

    Resolution order:
      * `EMAIL_PROVIDER=console` → ConsoleProvider
      * `EMAIL_PROVIDER=smtp`    → SMTPProvider if creds present, else fallback
      * `EMAIL_PROVIDER=resend`  → ResendProvider if RESEND_API_KEY set, else fallback
      * default                  → ConsoleProvider in non-prod, NoopProvider in prod
    """
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider

    requested = (os.environ.get("EMAIL_PROVIDER") or "").strip().lower()
    from_addr = (
        os.environ.get("EMAIL_FROM")
        or os.environ.get("SENDER_EMAIL")
        or "onboarding@resend.dev"
    )
    app_env = os.environ.get("APP_ENV", "development").lower()

    if requested == "console":
        _cached_provider = ConsoleProvider()
        return _cached_provider

    if requested == "smtp":
        host = (os.environ.get("SMTP_HOST") or "").strip()
        port_raw = (os.environ.get("SMTP_PORT") or "587").strip()
        username = (os.environ.get("SMTP_USERNAME") or "").strip()
        password = os.environ.get("SMTP_PASSWORD") or ""
        use_tls = (os.environ.get("SMTP_USE_TLS", "true") or "true").strip().lower() == "true"
        if not (host and username and password):
            _cached_provider = _safety_fallback(
                "smtp", "missing SMTP credentials (HOST/USERNAME/PASSWORD)",
                app_env,
            )
            return _cached_provider
        try:
            port = int(port_raw)
        except ValueError:
            port = 587
        _cached_provider = SMTPProvider(
            host=host, port=port, username=username, password=password,
            from_addr=from_addr, use_tls=use_tls,
        )
        return _cached_provider

    if requested == "resend":
        api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
        if api_key:
            _cached_provider = ResendProvider(api_key=api_key, from_addr=from_addr)
        else:
            _cached_provider = _safety_fallback(
                "resend", "RESEND_API_KEY is missing", app_env,
            )
        return _cached_provider

    # No explicit provider → fall back by environment
    if app_env == "production":
        _cached_provider = NoopProvider("no EMAIL_PROVIDER configured in production")
    else:
        _cached_provider = ConsoleProvider()
    return _cached_provider


def _safety_fallback(requested: str, reason: str, app_env: str) -> EmailProvider:
    """Pick the safest fallback when a real provider was asked for but
    is not configured. Dev → Console; Production → Noop (loud no-op).
    """
    if app_env == "production":
        return NoopProvider(f"{requested} requested but {reason}")
    logger.warning(
        "[EMAIL] %s requested but %s — falling back to ConsoleProvider for dev",
        requested, reason,
    )
    return ConsoleProvider()


def reset_provider_cache() -> None:
    """Test hook — drop the memoized provider so the next call re-reads env."""
    global _cached_provider
    _cached_provider = None


def detect_locale(accept_language: Optional[str]) -> str:
    """Parse the HTTP `Accept-Language` header → `"en" | "it"`."""
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
        primary = tag.lower().split("-", 1)[0]
        if primary in ("en", "it") and q > best_q:
            best_q = q
            best_lang = primary
    return best_lang


__all__ = [
    "EmailProvider",
    "ConsoleProvider",
    "NoopProvider",
    "ResendProvider",
    "SMTPProvider",
    "get_email_provider",
    "reset_provider_cache",
    "detect_locale",
]
