"""ROUND 11.1 B4 — Centralized public identifier hashing.

Converts internal user UUIDs (PII-adjacent — they uniquely identify a
person across sessions and let an attacker correlate behaviour across
endpoints) into short, stable, NON-reversible public ids.

Properties:
  * **Stable** — same `internal_uuid` always maps to the same public id
    across requests, processes, and pod restarts (salt is constant per
    environment).
  * **Non-reversible** — SHA-256 means recovering the UUID from the hash
    is computationally infeasible (no rainbow tables work because of
    the salt).
  * **Non-collidable enough** — 16 hex chars = 64 bits of entropy, well
    below the birthday bound for realistic user counts (~ 4 billion to
    hit 1% collision probability).
  * **Distinct shape** — 16 hex chars without dashes makes it visually
    impossible to confuse with a UUID4 (32 hex + 4 dashes).

The salt is loaded from `PUBLIC_ID_SALT` env at module import time. If
not set, a constant fallback is used — safe because the property we
care about is "stable across requests within the same deployment", not
cryptographic secret-hiding.
"""
from __future__ import annotations

import hashlib
import os

_SALT = os.environ.get(
    "PUBLIC_ID_SALT",
    # Stable fallback keyed to the project. Rotation = breaking change
    # because all server-stored public_ids would shift.
    "orbus-online::r11.1::public-id::v1",
)


def to_public_id(internal_uuid: str | None, *, salt: str | None = None) -> str | None:
    """Convert an internal UUID into a short public id.

    Returns `None` for falsy inputs so callers don't have to guard.
    """
    if not internal_uuid:
        return None
    pepper = (salt or _SALT).encode("utf-8")
    payload = str(internal_uuid).encode("utf-8")
    digest = hashlib.sha256(pepper + b":" + payload).hexdigest()
    return digest[:16]


__all__ = ["to_public_id"]
