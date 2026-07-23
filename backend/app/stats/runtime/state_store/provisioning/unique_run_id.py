"""RT2-B-1B-1 · Generator di `unique_run_id` per database integration-test.

Ogni run di suite integration deve avere un `unique_run_id` che genera
un database name distinto (fixture `unique_test_database`), evitando
collision cross-worker sotto `pytest-xdist -n 2`.
"""
from __future__ import annotations

import os
import re
import time
import uuid


_ALLOWED_CHARS = re.compile(r"[^a-z0-9_-]")


def _sanitize(fragment: str) -> str:
    return _ALLOWED_CHARS.sub("-", fragment.lower())


def generate_unique_run_id() -> str:
    """Return short, filesystem-safe unique run id.

    Format: `<ms_timestamp>_<pid>_<worker>_<uuid8>`.
    """
    ms = int(time.time() * 1000)
    pid = os.getpid()
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    worker = _sanitize(worker) or "master"
    short_uuid = uuid.uuid4().hex[:8]
    return f"{ms}_{pid}_{worker}_{short_uuid}"


def it_database_name(unique_run_id: str) -> str:
    """Return the canonical IT database name for a given run id.

    Format: `orbus_r16_rt2b_it_<unique_run_id>` (must match the allowlist
    regex enforced by `guards.verify_database_allowlist`).
    """
    sanitized = _sanitize(unique_run_id)
    if not sanitized:
        raise ValueError("unique_run_id sanitizes to empty string")
    return f"orbus_r16_rt2b_it_{sanitized}"


__all__ = ["generate_unique_run_id", "it_database_name"]
