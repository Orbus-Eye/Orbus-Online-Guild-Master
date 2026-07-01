"""ROUND 16.3 P3.5 — Self-test of the pytest DB isolation guard-rail.

Verifies that conftest.py REFUSES to boot pytest when `DB_NAME` doesn't
look like a test DB and `APP_ENV` is not one of `test/testing/ci`. This is
a "smoke test for the guard-rail itself" — it ensures the isolation policy
in `/app/memory/pytest_db_isolation_policy.md` stays enforced.

The test spawns a subprocess pytest --collect-only with sanitized env so
the conftest guard runs and MUST raise RuntimeError.

Note: `--collect-only` is enough — the guard runs at conftest IMPORT time,
before any test module is loaded.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]


_PY_ARGS = ["python", "-m", "pytest", "-c", "/dev/null", "-o", "addopts=",
            "tests/test_forge_actions_p0.py", "--co", "-q"]


def _sanitize_env(db_name: str, app_env: str) -> dict:
    """Return an env dict with only the vars needed to boot pytest.

    Removes any `_test` bias inherited from the outer session so the guard
    is really tested against the given values.
    """
    env = os.environ.copy()
    # Explicit values under test.
    env["DB_NAME"] = db_name
    env["APP_ENV"] = app_env
    # Prevent the child conftest from loading `.env.test` (which would mask
    # our hostile DB_NAME/APP_ENV overrides). See conftest.py P3.5 note.
    env["PYTEST_SKIP_DOTENV_OVERRIDE"] = "1"
    # Prevent the outer .env.test from being loaded again by the child.
    # The child conftest will still call load_dotenv on backend/.env and
    # tests/.env.test — but the child's os.environ takes precedence.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "0"
    # Remove the isolated backend override so the child doesn't try to
    # spawn a nested uvicorn.
    env.pop("ISOLATED_HTTP_TESTS", None)
    env.pop("PYTEST_XDIST_WORKER", None)
    return env


def test_guardrail_refuses_prod_db_when_app_env_is_production():
    """conftest MUST refuse when DB_NAME=orbus_r16 + APP_ENV=production."""
    env = _sanitize_env(db_name="orbus_r16", app_env="production")
    # `--co -q` collects tests without running them, but still imports conftest.
    result = subprocess.run(
        _PY_ARGS,
        env=env, cwd=str(BACKEND_DIR),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, (
        "Guard-rail failed to refuse a non-test DB. "
        f"stdout={result.stdout[-400:]} stderr={result.stderr[-400:]}"
    )
    combined = (result.stdout + result.stderr).upper()
    assert "REFUSING" in combined, (
        "Guard-rail error message missing 'REFUSING' marker. "
        f"stdout={result.stdout[-400:]} stderr={result.stderr[-400:]}"
    )


def test_guardrail_refuses_prod_db_with_empty_app_env():
    """conftest MUST refuse when DB_NAME=orbus_r16 + no APP_ENV."""
    env = _sanitize_env(db_name="orbus_r16", app_env="")
    result = subprocess.run(
        _PY_ARGS,
        env=env, cwd=str(BACKEND_DIR),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, (
        "Guard-rail failed to refuse empty APP_ENV. "
        f"stdout={result.stdout[-400:]}"
    )


def test_guardrail_accepts_test_db_name():
    """conftest MUST accept DB_NAME=orbus_r16_test (or any *_test)."""
    env = _sanitize_env(db_name="orbus_r16_test", app_env="test")
    result = subprocess.run(
        _PY_ARGS,
        env=env, cwd=str(BACKEND_DIR),
        capture_output=True, text=True, timeout=30,
    )
    combined = (result.stdout + result.stderr).upper()
    assert "REFUSING" not in combined, (
        f"Guard-rail refused a legitimate test DB. combined={combined[-400:]}"
    )


def test_guardrail_accepts_app_env_test_even_with_prod_db_name():
    """conftest accepts APP_ENV=test regardless of DB_NAME."""
    env = _sanitize_env(db_name="orbus_r16", app_env="test")
    result = subprocess.run(
        _PY_ARGS,
        env=env, cwd=str(BACKEND_DIR),
        capture_output=True, text=True, timeout=30,
    )
    combined = (result.stdout + result.stderr).upper()
    assert "REFUSING" not in combined, (
        f"Guard-rail wrongly refused APP_ENV=test. combined={combined[-400:]}"
    )
