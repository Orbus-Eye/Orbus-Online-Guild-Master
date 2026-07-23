"""RT2-B-1B-1 · Unit tests per guardrail funzionali."""
from __future__ import annotations

import pytest

from app.stats.runtime.state_store.provisioning import (
    ProvisioningGuardError,
    verify_database_allowlist,
    verify_host_localhost,
    verify_not_orbus_r16,
    verify_target,
)


class TestHostLocalhost:
    def test_localhost_accepted(self):
        assert verify_host_localhost("mongodb://localhost:27017") == "localhost"

    def test_127_0_0_1_accepted(self):
        assert verify_host_localhost("mongodb://127.0.0.1:27017") == "127.0.0.1"

    def test_ipv6_loopback_accepted(self):
        assert verify_host_localhost("mongodb://[::1]:27017") == "::1"

    def test_remote_host_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_host_localhost("mongodb://prod-mongo.example.com:27017")
        assert exc_info.value.code == "TARGET_ENVIRONMENT_REJECTED"

    def test_srv_remote_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_host_localhost("mongodb+srv://cluster.example.com")
        assert exc_info.value.code == "TARGET_ENVIRONMENT_REJECTED"

    def test_empty_uri_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_host_localhost("")
        assert exc_info.value.code == "TARGET_ENVIRONMENT_REJECTED"

    def test_non_mongo_scheme_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_host_localhost("http://localhost:27017")
        assert exc_info.value.code == "TARGET_ENVIRONMENT_REJECTED"


class TestDatabaseAllowlist:
    def test_stable_db_accepted(self):
        verify_database_allowlist("orbus_r16_rt2b_test")

    def test_it_db_accepted(self):
        verify_database_allowlist("orbus_r16_rt2b_it_abcd1234_master_deadbeef")
        verify_database_allowlist("orbus_r16_rt2b_it_1234567890_5_master_ab12cd34")

    def test_orbus_r16_explicit_block(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_database_allowlist("orbus_r16")
        assert exc_info.value.code == "FORBIDDEN_DATABASE_ORBUS_R16"

    def test_orbus_r16_test_rejected(self):
        # orbus_r16_test is a pre-existing test DB — NOT usable for RT2-B (B1BQ02)
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_database_allowlist("orbus_r16_test")
        assert exc_info.value.code == "TARGET_DATABASE_REJECTED"

    def test_preview_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_database_allowlist("preview_db")
        assert exc_info.value.code == "TARGET_DATABASE_REJECTED"

    def test_empty_string_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_database_allowlist("")
        assert exc_info.value.code == "TARGET_DATABASE_REJECTED"

    def test_none_rejected(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_database_allowlist(None)  # type: ignore[arg-type]
        assert exc_info.value.code == "TARGET_DATABASE_REJECTED"

    def test_uppercase_it_pattern_rejected(self):
        # allowlist regex is strict lowercase
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_database_allowlist("orbus_r16_rt2b_it_ABCDEF")
        assert exc_info.value.code == "TARGET_DATABASE_REJECTED"


class TestVerifyNotOrbusR16:
    def test_orbus_r16_blocked(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_not_orbus_r16("orbus_r16")
        assert exc_info.value.code == "FORBIDDEN_DATABASE_ORBUS_R16"

    def test_other_dbs_pass(self):
        verify_not_orbus_r16("orbus_r16_rt2b_test")
        verify_not_orbus_r16("orbus_r16_test")
        verify_not_orbus_r16("random_db")


class TestVerifyTargetCompose:
    def test_success(self):
        host, db = verify_target("mongodb://localhost:27017", "orbus_r16_rt2b_test")
        assert host == "localhost"
        assert db == "orbus_r16_rt2b_test"

    def test_bad_host_stops_before_db_check(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_target("mongodb://prod-mongo.example.com", "orbus_r16_rt2b_test")
        assert exc_info.value.code == "TARGET_ENVIRONMENT_REJECTED"

    def test_localhost_but_orbus_r16(self):
        with pytest.raises(ProvisioningGuardError) as exc_info:
            verify_target("mongodb://localhost:27017", "orbus_r16")
        assert exc_info.value.code == "FORBIDDEN_DATABASE_ORBUS_R16"
