"""Server-side rollout gates for classless Class Hall assignment."""

from __future__ import annotations

import os


_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _enabled(raw: str | None) -> bool:
    return (raw or "").strip().lower() in _TRUTHY


def assignment_enabled_for_hall(hall_id: str) -> bool:
    """Enable all canonical Halls in tester builds; production fails closed.

    Explicit environment values always win.  A production process therefore
    needs both the global switch and a per-Hall allowlist, while local,
    development, preview and test builds are immediately playable.
    """
    app_env = (os.getenv("APP_ENV") or "development").strip().lower()
    raw_global = os.getenv("ORBUS_CLASS_HALL_ASSIGNMENT_ENABLED")
    global_enabled = (
        _enabled(raw_global)
        if raw_global is not None
        else app_env in {"development", "dev", "preview", "test", "testing"}
    )
    if not global_enabled:
        return False
    raw_allowlist = os.getenv("ORBUS_CLASS_HALL_ASSIGNMENT_HALLS")
    allowlist = {
        value.strip().lower()
        for value in (raw_allowlist or "").split(",")
        if value.strip()
    }
    if raw_allowlist is None and app_env != "production":
        return bool(hall_id)
    return (hall_id or "").strip().lower() in allowlist


__all__ = ["assignment_enabled_for_hall"]
