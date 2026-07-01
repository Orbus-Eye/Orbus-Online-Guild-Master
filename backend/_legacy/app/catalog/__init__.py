"""ROUND 11.2 TASK 6 G1-G2 — Public catalog endpoints.

Single module owning:
  * GET /api/traits/catalog  (data-driven, filtered)
  * GET /api/stats/catalog   (static, code-defined)

Both endpoints are intentionally PUBLIC (no auth) — they expose the same
player-facing information rendered in the in-game Guide and on the
landing/marketing surface. PII-safe by construction (no user/guild ids,
no `code`, no internal moderation flags).
"""
from app.catalog.routes import router

__all__ = ["router"]
