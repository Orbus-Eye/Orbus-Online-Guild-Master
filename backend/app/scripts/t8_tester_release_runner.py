"""Fail-closed, one-command T8 tester-release regression.

Dry-run by default. With ``--run`` it executes the isolated T5 journey, T6/T8
catalog and economy gates, then the production frontend build. It only accepts
the local Mongo endpoint and never authorizes deployment.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence
import uuid

from app.scripts.t5_isolated_playtest_runner import (
    DEFAULT_MONGO_URI,
    missing_modules,
    tcp_reachable,
    validate_mongo_uri,
)


T8_TEST_PATHS = (
    "tests/test_t8_tester_release_gate.py",
    "tests/test_t6_final_catalog.py",
    "tests/test_t6_item_pool_simulation.py",
    "tests/test_item_catalog_contract_t0.py",
    "tests/test_career_revamp_contract.py",
    "tests/test_level80_content_curve.py",
)
REQUIRED_MODULES = (
    "fastapi",
    "motor",
    "pymongo",
    "pytest",
    "xdist",
    "requests",
    "uvicorn",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mongo-uri", default=DEFAULT_MONGO_URI)
    parser.add_argument("--http-port", type=int, default=8878)
    parser.add_argument("--skip-managed-http", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    return parser


def _frontend_command(frontend_root: Path) -> list[str] | None:
    yarn = shutil.which("yarn") or shutil.which("yarn.cmd")
    if yarn:
        return [yarn, "build"]
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm:
        return [npm, "run", "build"]
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        host, port = validate_mongo_uri(args.mongo_uri)
    except ValueError as exc:
        print(json.dumps({"safe": False, "error": str(exc)}, indent=2))
        return 2
    if not 1024 <= args.http_port <= 65535:
        print(json.dumps({"safe": False, "error": "invalid HTTP port"}, indent=2))
        return 2

    backend_root = Path(__file__).resolve().parents[2]
    repository_root = backend_root.parent
    frontend_root = repository_root / "frontend"
    frontend_command = _frontend_command(frontend_root)
    missing = missing_modules(REQUIRED_MODULES)
    mongo_ready = tcp_reachable(host, port)
    http_port_ready = (
        args.skip_managed_http
        or not tcp_reachable("127.0.0.1", args.http_port)
    )
    frontend_ready = (
        args.skip_frontend
        or (
            frontend_command is not None
            and (frontend_root / "node_modules").is_dir()
        )
    )
    t5_command = [
        sys.executable,
        "-m",
        "app.scripts.t5_isolated_playtest_runner",
        "--run",
        "--mongo-uri",
        args.mongo_uri,
    ]
    if not args.skip_managed_http:
        t5_command.extend([
            "--start-isolated-http",
            "--http-port",
            str(args.http_port),
        ])
    t8_command = [
        sys.executable,
        "-m",
        "pytest",
        "-n",
        "0",
        "-q",
        *T8_TEST_PATHS,
    ]
    report = {
        "release_contract": "t8.tester-release.v1",
        "mode": "run" if args.run else "dry-run",
        "safe": True,
        "mongo": {
            "target": args.mongo_uri,
            "reachable": mongo_ready,
            "shared_database_selected": False,
        },
        "managed_http": {
            "enabled": not args.skip_managed_http,
            "port": args.http_port,
            "available": http_port_ready,
        },
        "frontend": {
            "enabled": not args.skip_frontend,
            "ready": frontend_ready,
            "command": frontend_command,
        },
        "missing_python_modules": missing,
        "commands": [t5_command, t8_command],
        "deployment_authorized": False,
        "class_sets_included": False,
    }
    print(json.dumps(report, indent=2))
    if not args.run:
        return 0
    if missing or not mongo_ready or not http_port_ready or not frontend_ready:
        print("T8 run blocked: preflight requirements are not satisfied.")
        return 3

    db_name = f"orbus_r16_rt2b_it_t8runner_{uuid.uuid4().hex}"
    child_env = os.environ.copy()
    child_env.update({
        "APP_ENV": "test",
        "DB_NAME": db_name,
        "MONGO_URL": args.mongo_uri,
        "JWT_SECRET": "t8-isolated-runner-not-a-deployment-secret",
        "TESTER_PASSWORD": "password123",
        "EMAIL_ENABLED": "false",
        "PYTHON_DOTENV_DISABLED": "1",
        "PYTEST_SKIP_DOTENV_OVERRIDE": "1",
        "MONGO_URI_LOCAL_ISOLATED": args.mongo_uri,
    })
    from pymongo import MongoClient

    try:
        for command, cwd in (
            (t5_command, backend_root),
            (t8_command, backend_root),
        ):
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=child_env,
                check=False,
            )
            if completed.returncode:
                return int(completed.returncode)
        if not args.skip_frontend:
            frontend_env = child_env.copy()
            frontend_env.update({
                "CI": "true",
                "DISABLE_ESLINT_PLUGIN": "true",
                "REACT_APP_BACKEND_URL": f"http://127.0.0.1:{args.http_port}",
            })
            completed = subprocess.run(
                frontend_command,
                cwd=frontend_root,
                env=frontend_env,
                check=False,
            )
            if completed.returncode:
                return int(completed.returncode)
        return 0
    finally:
        client = MongoClient(args.mongo_uri, serverSelectionTimeoutMS=2000)
        try:
            client.drop_database(db_name)
        finally:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "REQUIRED_MODULES",
    "T8_TEST_PATHS",
    "main",
]
