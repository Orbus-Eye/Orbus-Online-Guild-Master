"""Phase 9.3 — Email templates (EN/IT, inline strings).

Two templates × two locales = four renderers. No external engine (no Jinja2);
plain Python str.format is enough for our needs. Every renderer returns the
tuple `(subject, html, text)`.

Design notes:
* Inline CSS only (some email clients strip <style>).
* No external images or fonts.
* `text` fallback is generated alongside `html` for clients that disable HTML.
* The brand is intentionally text-only ("◆ ORBUS") — no remote assets.
* `app_url` is the public web URL (frontend), not the API base.
* Phase 9.3.1 — every user-controlled string is `html.escape()`d before being
  interpolated into the HTML body. The plaintext fallback strips newlines to
  avoid header injection. The Pydantic schema also rejects shell/HTML-unsafe
  characters at register time, so this is defense-in-depth.
"""
from __future__ import annotations

import html as _html
from typing import Tuple


def _safe_html(value: str) -> str:
    """HTML-escape a user-controlled string for safe inclusion in `<body>`."""
    if value is None:
        return ""
    return _html.escape(str(value), quote=True)


def _safe_text(value: str) -> str:
    """Strip CR/LF/control chars AND HTML-meta chars (`<>&"'`) from a
    user-controlled string before putting it into the plaintext body OR the
    subject header. Prevents header injection in MIME-encoded subjects and
    keeps subjects safe in mail clients that render markup.

    Phase 9.3.1 — defense in depth: even for accounts predating the strict
    Pydantic regex, the email rendering pipeline cannot expose unsafe chars.
    """
    if value is None:
        return ""
    cleaned = "".join(
        ch for ch in str(value)
        if 32 <= ord(ch) < 127 and ch not in "<>&\"'"
    )
    return cleaned.strip()

# Common inline styles for both templates
_WRAPPER_CSS = (
    "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;"
    " background:#0e0e10; color:#e6e6e6; padding:32px;"
)
_CARD_CSS = (
    "max-width:520px; margin:0 auto; background:#16161a; border:1px solid #2a2a2e;"
    " border-radius:6px; padding:32px;"
)
_BTN_CSS = (
    "display:inline-block; padding:12px 24px; background:#f5a524; color:#0e0e10;"
    " text-decoration:none; font-weight:600; border-radius:4px; letter-spacing:.04em;"
)
_LINK_CSS = "color:#f5a524; word-break:break-all;"
_FOOTER_CSS = "color:#888; font-size:12px; margin-top:24px;"


# ────────────────────────────────────────────────────────────────────────────
# Password reset
# ────────────────────────────────────────────────────────────────────────────
def render_password_reset(lang: str, reset_url: str) -> Tuple[str, str, str]:
    """Render the password-reset email for the given locale."""
    if lang == "it":
        subject = "Reset password — Orbus Online"
        intro = "Abbiamo ricevuto una richiesta di reset password per il tuo account Orbus."
        cta = "Reimposta password"
        body = (
            "Clicca il pulsante per impostare una nuova password. "
            "Il link è valido per <strong>60 minuti</strong> e può essere usato una sola volta."
        )
        fallback = "Se il pulsante non funziona, copia e incolla questo URL nel browser:"
        ignore = "Se non sei stato tu, ignora questa email — la tua password resta invariata."
        footer = "Orbus Online · Guild Master · email automatica, non rispondere."
    else:
        subject = "Reset your password — Orbus Online"
        intro = "We received a request to reset the password for your Orbus account."
        cta = "Reset password"
        body = (
            "Click the button below to set a new password. "
            "This link is valid for <strong>60 minutes</strong> and can be used only once."
        )
        fallback = "If the button does not work, copy and paste this URL into your browser:"
        ignore = "If you didn't request this, just ignore the email — your password stays as it is."
        footer = "Orbus Online · Guild Master · automated message, do not reply."

    html = f"""<!doctype html>
<html lang="{lang}">
<body style="{_WRAPPER_CSS}">
  <div style="{_CARD_CSS}">
    <div style="color:#f5a524; letter-spacing:.18em; font-size:11px; margin-bottom:18px;">◆ ORBUS // GUILDMASTER</div>
    <h1 style="font-size:22px; margin:0 0 16px;">{subject}</h1>
    <p style="line-height:1.6;">{intro}</p>
    <p style="line-height:1.6;">{body}</p>
    <p style="text-align:center; margin:28px 0;">
      <a href="{reset_url}" style="{_BTN_CSS}">{cta} →</a>
    </p>
    <p style="font-size:13px; color:#aaa;">{fallback}</p>
    <p style="font-size:12px;"><a href="{reset_url}" style="{_LINK_CSS}">{reset_url}</a></p>
    <p style="line-height:1.6; font-size:13px; color:#aaa;">{ignore}</p>
    <div style="{_FOOTER_CSS}">— {footer}</div>
  </div>
</body>
</html>"""

    text = (
        f"{subject}\n"
        f"{'=' * len(subject)}\n\n"
        f"{intro}\n\n"
        f"{body.replace('<strong>', '').replace('</strong>', '')}\n\n"
        f"{cta}: {reset_url}\n\n"
        f"{ignore}\n\n"
        f"— {footer}\n"
    )
    return subject, html, text


# ────────────────────────────────────────────────────────────────────────────
# Welcome (post-registration)
# ────────────────────────────────────────────────────────────────────────────
def render_welcome(lang: str, app_url: str, username: str) -> Tuple[str, str, str]:
    """Render the welcome email for the given locale.

    Phase 9.3.1 — username is HTML-escaped for the HTML body and sanitised
    (CR/LF stripped) for the subject + plaintext to prevent header injection
    and HTML rendering of attacker-controlled content. The Pydantic schema
    rejects unsafe patterns at register time as well.
    """
    raw_username = (username or "Guild Master").strip() or "Guild Master"
    safe_username_text = _safe_text(raw_username) or "Guild Master"
    safe_app_url = _safe_text(app_url) or "/"
    safe_app_url_html = _safe_html(safe_app_url)
    if lang == "it":
        subject = f"Benvenuto su Orbus, {safe_username_text}"
        intro = "Il tuo account Orbus è pronto. È ora di fondare la tua gilda."
        steps_title = "I tuoi primi quattro passi:"
        steps = [
            "Recluta 3 avventurieri (3 refresh gratis ogni giorno).",
            "Invia il tuo team alle Tane dei Goblin — il dungeon iniziale.",
            "Leggi il report: XP, oro, bottino.",
            "Equipaggia il bottino e scala la classifica per Potenza Peak.",
        ]
        cta = "Entra nella dashboard"
        footer = "Orbus Online · Guild Master · email automatica, non rispondere."
    else:
        subject = f"Welcome to Orbus, {safe_username_text}"
        intro = "Your Orbus account is ready. Time to found your guild."
        steps_title = "Your first four moves:"
        steps = [
            "Recruit 3 adventurers (3 free refreshes per day).",
            "Dispatch the team to Goblin Warrens — your starting dungeon.",
            "Read the after-action report: XP, gold, loot.",
            "Equip the loot and climb the leaderboard by Peak Team Power.",
        ]
        cta = "Open the dashboard"
        footer = "Orbus Online · Guild Master · automated message, do not reply."

    steps_html = "".join(
        f"<li style='margin:6px 0;'>{s}</li>" for s in steps
    )
    steps_text = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(steps))

    html = f"""<!doctype html>
<html lang="{lang}">
<body style="{_WRAPPER_CSS}">
  <div style="{_CARD_CSS}">
    <div style="color:#f5a524; letter-spacing:.18em; font-size:11px; margin-bottom:18px;">◆ ORBUS // GUILDMASTER</div>
    <h1 style="font-size:22px; margin:0 0 16px;">{_safe_html(subject)}</h1>
    <p style="line-height:1.6;">{intro}</p>
    <p style="line-height:1.6; color:#aaa; font-size:14px;">{steps_title}</p>
    <ol style="line-height:1.6; padding-left:22px;">{steps_html}</ol>
    <p style="text-align:center; margin:28px 0;">
      <a href="{safe_app_url_html}" style="{_BTN_CSS}">{cta} →</a>
    </p>
    <p style="font-size:12px;"><a href="{safe_app_url_html}" style="{_LINK_CSS}">{safe_app_url_html}</a></p>
    <div style="{_FOOTER_CSS}">— {footer}</div>
  </div>
</body>
</html>"""

    text = (
        f"{subject}\n"
        f"{'=' * len(subject)}\n\n"
        f"{intro}\n\n"
        f"{steps_title}\n{steps_text}\n\n"
        f"{cta}: {safe_app_url}\n\n"
        f"— {footer}\n"
    )
    return subject, html, text


__all__ = ["render_password_reset", "render_welcome"]
