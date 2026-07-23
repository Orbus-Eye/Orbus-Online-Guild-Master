"""RT2-B-2A · Fixtures per test wiring shadow.

Utilizza `FakeExpeditionRuntimeStateStore` per isolamento test (nessun Mongo
reale). Sostituisce il coordinator interno via monkeypatch.
"""
from __future__ import annotations

import os
from typing import Any

import pytest

from app.stats.runtime import feature_flags
from app.stats.runtime.state_store import FakeExpeditionRuntimeStateStore
from app.stats.runtime.wiring.coordinator import ExpeditionRuntimeCoordinator


@pytest.fixture
def enable_cdv_flag(monkeypatch):
    """Attiva `cdv_transient_state_enabled=true` via env var, poi reset."""
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    feature_flags.reset_cache()
    yield
    feature_flags.reset_cache()


@pytest.fixture
def disable_cdv_flag(monkeypatch):
    """Forza `cdv_transient_state_enabled=false` (default)."""
    monkeypatch.delenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", raising=False)
    feature_flags.reset_cache()
    yield
    feature_flags.reset_cache()


class _FakeDb:
    """Fake db handle per test wiring: espone `.users.find_one` async."""

    def __init__(self, user_docs: list[dict] | None = None) -> None:
        self.users = _FakeCollection(user_docs or [])
        self.guilds = _FakeCollection([])

    @property
    def client(self):  # pragma: no cover — used only when coordinator is built
        return None


class _FakeCollection:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = list(docs)

    async def find_one(self, filt: dict, projection: dict | None = None):
        for d in self._docs:
            if all(d.get(k) == v for k, v in filt.items()):
                if projection:
                    return {k: v for k, v in d.items() if k in projection and projection.get(k)}
                return dict(d)
        return None


@pytest.fixture
def fake_db_test_user() -> _FakeDb:
    """`fake db` con un utente test-user server-authoritative."""
    return _FakeDb(user_docs=[
        {"id": "user-test-001", "is_test_user": True, "email": "tester@orbus.test"},
        {"id": "user-normal-001", "is_test_user": False, "email": "player@example.com"},
    ])


@pytest.fixture
def fake_coordinator_allowlisted() -> ExpeditionRuntimeCoordinator:
    """Coordinator con Fake store + target DB allowlisted."""
    store = FakeExpeditionRuntimeStateStore()
    return ExpeditionRuntimeCoordinator(
        store=store,
        target_db_name="orbus_r16_rt2b_test",
    )


@pytest.fixture
def fake_coordinator_forbidden() -> ExpeditionRuntimeCoordinator:
    """Coordinator con target DB VIETATO (guardrail B2Q10)."""
    store = FakeExpeditionRuntimeStateStore()
    return ExpeditionRuntimeCoordinator(
        store=store,
        target_db_name="orbus_r16",
    )
