"""Fail-closed runner for the targeted T5 tester-path regressions.

The command is a dry-run unless ``--run`` is supplied.  It never loads the
application ``.env`` and accepts only loopback services.  Real-Mongo tests
create a unique allowlisted database and drop it in their own fixture.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Sequence
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen
import uuid


LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
MONGO_TEST_HOST = "127.0.0.1"
MONGO_TEST_PORT = 27017
DEFAULT_MONGO_URI = f"mongodb://{MONGO_TEST_HOST}:{MONGO_TEST_PORT}"

UNIT_TEST_PATHS = (
    "tests/test_tester_vertical_slice.py",
    "tests/test_class_hall_build_reachability.py",
    "tests/test_class_hall_build_lab.py",
    "tests/test_t5_isolated_playtest_runner.py",
)
REAL_MONGO_TEST_PATH = "tests/effect_engine/class_halls/integration_real_mongo"
HTTP_TEST_PATH = "tests/effect_engine/class_halls/integration_http"
REQUIRED_MODULES = ("fastapi", "motor", "pymongo", "pytest", "xdist")
HTTP_REQUIRED_MODULES = ("requests", "uvicorn")


class T5RunnerSafetyError(ValueError):
    """Raised before subprocess or network activity when a target is unsafe."""


def validate_mongo_uri(uri: str) -> tuple[str, int]:
    """Accept only the exact local endpoint used by the isolated fixture."""
    if not uri or "," in uri:
        raise T5RunnerSafetyError("Mongo target must contain one loopback host")
    parsed = urlsplit(uri)
    if parsed.scheme != "mongodb":
        raise T5RunnerSafetyError("Mongo target must use mongodb:// (not SRV)")
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise T5RunnerSafetyError("Credentials are forbidden for the local T5 run")
    if parsed.hostname not in LOOPBACK_HOSTS:
        raise T5RunnerSafetyError("Mongo target must be loopback")
    try:
        port = parsed.port or MONGO_TEST_PORT
    except ValueError as exc:
        raise T5RunnerSafetyError("Mongo target contains an invalid port") from exc
    if parsed.hostname != MONGO_TEST_HOST or port != MONGO_TEST_PORT:
        raise T5RunnerSafetyError(
            "The current real-Mongo fixture is pinned to 127.0.0.1:27017"
        )
    if parsed.path not in {"", "/"}:
        raise T5RunnerSafetyError(
            "Do not select an application database; the fixture creates its own"
        )
    return parsed.hostname, port


def validate_http_base_url(base_url: str) -> str:
    """Allow HTTP black-box writes only against an explicit loopback API."""
    parsed = urlsplit(base_url)
    if parsed.scheme != "http":
        raise T5RunnerSafetyError("HTTP target must use plain http://")
    if parsed.hostname != "127.0.0.1":
        raise T5RunnerSafetyError("HTTP target must use explicit 127.0.0.1")
    try:
        port = parsed.port
    except ValueError as exc:
        raise T5RunnerSafetyError("HTTP target contains an invalid port") from exc
    if port is None or not 1024 <= port <= 65535:
        raise T5RunnerSafetyError(
            "HTTP target must declare a non-privileged port (1024..65535)"
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise T5RunnerSafetyError("HTTP target cannot contain credentials/query")
    if parsed.path not in {"", "/"}:
        raise T5RunnerSafetyError("HTTP target must be an API origin, without path")
    return base_url.rstrip("/")


def missing_modules(modules: Sequence[str] = REQUIRED_MODULES) -> list[str]:
    missing: list[str] = []
    for module in modules:
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            available = False
        if not available:
            missing.append(module)
    return missing


def tcp_reachable(host: str, port: int, timeout_seconds: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def build_pytest_command(
    python_executable: str,
    *,
    include_real_mongo: bool = True,
    include_http: bool = False,
) -> list[str]:
    paths = list(UNIT_TEST_PATHS)
    if include_real_mongo:
        paths.append(REAL_MONGO_TEST_PATH)
    if include_http:
        paths.append(HTTP_TEST_PATH)
    return [python_executable, "-m", "pytest", "-n", "0", "-q", *paths]


def wait_for_http_health(
    base_url: str,
    process: subprocess.Popen,
    *,
    timeout_seconds: float = 90.0,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    health_url = f"{base_url}/api/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen(health_url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (OSError, URLError):
            pass
        time.sleep(0.25)
    return False


def stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def console_safe(text: str) -> str:
    """Keep failure diagnostics printable on Windows legacy code pages."""
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="backslashreplace").decode(encoding)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="execute after preflight")
    parser.add_argument("--mongo-uri", default=DEFAULT_MONGO_URI)
    parser.add_argument("--include-http", action="store_true")
    parser.add_argument(
        "--start-isolated-http",
        action="store_true",
        help="start and stop a loopback API bound to the per-run database",
    )
    parser.add_argument("--http-port", type=int, default=8765)
    parser.add_argument("--http-base-url")
    parser.add_argument(
        "--confirm-isolated-http-db",
        action="store_true",
        help="confirm that the loopback API uses a disposable isolated database",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        mongo_host, mongo_port = validate_mongo_uri(args.mongo_uri)
        http_base_url = None
        include_http = bool(args.include_http or args.start_isolated_http)
        if args.start_isolated_http:
            if args.http_base_url:
                raise T5RunnerSafetyError(
                    "--start-isolated-http cannot use an external base URL"
                )
            if not 1024 <= args.http_port <= 65535:
                raise T5RunnerSafetyError("managed HTTP port must be 1024..65535")
            http_base_url = validate_http_base_url(
                f"http://127.0.0.1:{args.http_port}"
            )
        elif include_http:
            if not args.http_base_url:
                raise T5RunnerSafetyError(
                    "--include-http requires --http-base-url"
                )
            if not args.confirm_isolated_http_db:
                raise T5RunnerSafetyError(
                    "HTTP writes require --confirm-isolated-http-db"
                )
            http_base_url = validate_http_base_url(args.http_base_url)
    except T5RunnerSafetyError as exc:
        print(json.dumps({"safe": False, "error": str(exc)}, indent=2))
        return 2

    required_modules = (
        (*REQUIRED_MODULES, *HTTP_REQUIRED_MODULES)
        if include_http
        else REQUIRED_MODULES
    )
    missing = missing_modules(required_modules)
    mongo_ready = tcp_reachable(mongo_host, mongo_port)
    http_port_available = not (
        args.start_isolated_http
        and tcp_reachable("127.0.0.1", args.http_port)
    )
    command = build_pytest_command(
        sys.executable,
        include_real_mongo=True,
        include_http=include_http,
    )
    report = {
        "mode": "run" if args.run else "dry-run",
        "safe": True,
        "loads_application_env": False,
        "mongo": {
            "target": args.mongo_uri,
            "reachable": mongo_ready,
            "database_policy": "unique allowlisted DB created/dropped by fixture",
        },
        "http": {
            "included": include_http,
            "managed": bool(args.start_isolated_http),
            "target": http_base_url,
            "isolated_db_confirmed": bool(
                args.confirm_isolated_http_db or args.start_isolated_http
            ),
            "port_available": http_port_available,
        },
        "missing_python_modules": missing,
        "command": command,
    }
    print(json.dumps(report, indent=2))

    if not args.run:
        return 0
    if missing or not mongo_ready or not http_port_available:
        print("T5 run blocked: preflight requirements are not satisfied.")
        return 3

    backend_root = Path(__file__).resolve().parents[2]
    runner_db_name = f"orbus_r16_rt2b_it_t5runner_{uuid.uuid4().hex}"
    child_env = os.environ.copy()
    # Satisfy the repository-wide pytest guard without exposing any app DB.
    # The global pollution sweep targets only this per-run database, while
    # the real-Mongo fixture uses its own unique databases.
    child_env["APP_ENV"] = "test"
    child_env["DB_NAME"] = runner_db_name
    child_env["MONGO_URL"] = args.mongo_uri
    child_env["JWT_SECRET"] = "t5-isolated-runner-not-a-deployment-secret"
    child_env["TESTER_PASSWORD"] = "password123"
    child_env["EMAIL_ENABLED"] = "false"
    child_env["PYTHON_DOTENV_DISABLED"] = "1"
    child_env["PYTEST_SKIP_DOTENV_OVERRIDE"] = "1"
    child_env["MONGO_URI_LOCAL_ISOLATED"] = args.mongo_uri
    if http_base_url:
        child_env["ORBUS_HTTP_E2E_BASE_URL"] = http_base_url
    from pymongo import MongoClient

    api_process: subprocess.Popen | None = None
    api_log_path: Path | None = None
    completed_returncode = 1
    try:
        if args.start_isolated_http:
            log_handle = tempfile.NamedTemporaryFile(
                prefix="orbus-t5-api-",
                suffix=".log",
                delete=False,
            )
            api_log_path = Path(log_handle.name)
            api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "server:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(args.http_port),
                    "--log-level",
                    "warning",
                ],
                cwd=backend_root,
                env=child_env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
            log_handle.close()
            if not wait_for_http_health(http_base_url, api_process):
                print("T5 managed API failed its loopback health check.")
                completed_returncode = 4
                return completed_returncode

        completed = subprocess.run(
            command,
            cwd=backend_root,
            env=child_env,
            check=False,
        )
        completed_returncode = int(completed.returncode)
    finally:
        stop_process(api_process)
        if (
            completed_returncode != 0
            and api_log_path is not None
            and api_log_path.exists()
        ):
            print("T5 managed API log tail:")
            print(
                console_safe(
                    api_log_path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )[-12000:]
                )
            )
        cleanup_client = MongoClient(args.mongo_uri, serverSelectionTimeoutMS=2000)
        try:
            cleanup_client.drop_database(runner_db_name)
        finally:
            cleanup_client.close()
        if api_log_path is not None:
            api_log_path.unlink(missing_ok=True)
    return completed_returncode


if __name__ == "__main__":
    raise SystemExit(main())
