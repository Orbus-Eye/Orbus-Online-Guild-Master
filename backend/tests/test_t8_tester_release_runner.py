from app.scripts.t8_tester_release_runner import main


def test_t8_runner_is_dry_run_by_default():
    assert main([]) == 0


def test_t8_runner_rejects_non_loopback_mongo():
    assert main(["--mongo-uri", "mongodb://example.com:27017"]) == 2


def test_t8_runner_rejects_privileged_http_port():
    assert main(["--http-port", "80"]) == 2
