import pytest

from app.scripts.t5_isolated_playtest_runner import (
    HTTP_TEST_PATH,
    REAL_MONGO_TEST_PATH,
    T5RunnerSafetyError,
    UNIT_TEST_PATHS,
    build_pytest_command,
    stop_process,
    validate_http_base_url,
    validate_mongo_uri,
)


def test_mongo_guard_accepts_only_fixture_endpoint():
    assert validate_mongo_uri("mongodb://127.0.0.1:27017") == (
        "127.0.0.1",
        27017,
    )
    for unsafe in (
        "mongodb://db.example.test:27017",
        "mongodb+srv://cluster.example.test",
        "mongodb://127.0.0.1:27018",
        "mongodb://127.0.0.1:not-a-port",
        "mongodb://127.0.0.1:27017/orbus_r16",
        "mongodb://127.0.0.1:27017/?authSource=admin",
    ):
        with pytest.raises(T5RunnerSafetyError):
            validate_mongo_uri(unsafe)


def test_http_guard_rejects_non_loopback_targets():
    assert validate_http_base_url("http://127.0.0.1:8000/") == (
        "http://127.0.0.1:8000"
    )
    for unsafe in (
        "https://preview.example.test",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:not-a-port",
    ):
        with pytest.raises(T5RunnerSafetyError):
            validate_http_base_url(unsafe)


def test_command_is_serial_and_targeted():
    command = build_pytest_command(
        "python",
        include_real_mongo=True,
        include_http=True,
    )
    assert command[:6] == ["python", "-m", "pytest", "-n", "0", "-q"]
    assert set(command[6:]) == {
        *UNIT_TEST_PATHS,
        REAL_MONGO_TEST_PATH,
        HTTP_TEST_PATH,
    }
    assert all(".env" not in part for part in command)


def test_stop_process_is_a_noop_for_absent_process():
    assert stop_process(None) is None
