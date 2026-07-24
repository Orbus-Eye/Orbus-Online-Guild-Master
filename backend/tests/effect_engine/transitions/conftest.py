"""Shared fixtures for RT2-B-2B-1 transitions test suite.

Pattern: pytest sync + asyncio.run() (coerente con `tests/effect_engine/state_store/`).
"""
from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.stats.runtime.state_store.fake_store import FakeExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    ExpeditionRuntimeState,
    RuntimeStatus,
)
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    TrustedDrainReceipt,
)


def run(coro):
    """Run a coroutine in a fresh event loop (deterministic per test)."""
    return asyncio.new_event_loop().run_until_complete(coro)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


class _Clock:
    """Deterministic clock that can be advanced by tests."""

    def __init__(self, initial: datetime) -> None:
        self._now = initial

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: int) -> None:
        self._now = self._now + timedelta(seconds=seconds)


@pytest.fixture
def clock_fn():
    return _Clock(datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def fake_store(clock_fn):
    return FakeExpeditionRuntimeStateStore(clock=clock_fn)


@pytest.fixture
def expedition_id() -> str:
    return f"exp-{uuid.uuid4().hex[:12]}"


@pytest.fixture
def adventurer_id() -> str:
    return "adv-cdv-01"


@pytest.fixture
def target_id() -> str:
    return "target-boss-01"


@pytest.fixture
def initialized_state(fake_store, expedition_id, clock_fn):
    """Create an initial shell state and return (store, expedition_id) synchronously."""
    now = clock_fn()
    shell = ExpeditionRuntimeState(
        expedition_id=expedition_id,
        state_version=1,
        fencing_token=0,
        created_at=_iso(now),
        updated_at=_iso(now),
        expires_at=_iso(now + timedelta(hours=6)),
        runtime_status=RuntimeStatus.ACTIVE,
        adventurer_class_states=(),
        processed_event_keys=(),
        last_event_sequence=0,
        owner_worker_or_lease_id=None,
        lease=None,
    )
    result = run(fake_store.create_state(expedition_id, shell))
    assert result.success, f"initial state creation failed: {result.code}"
    return fake_store, expedition_id


def make_event(
    event_type: str,
    *,
    expedition_id: str,
    source_adventurer_id: str,
    target_id: str = "",
    amount: int = 0,
    reason_code: str | None = None,
    trusted_drain_receipt: TrustedDrainReceipt | None = None,
    expected_state_version: int = 1,
    event_id: str | None = None,
    payload_extra: dict | None = None,
) -> ClassStateEvent:
    eid = event_id or f"evt-{uuid.uuid4().hex[:16]}"
    payload_seed = {
        "event_type": event_type,
        "expedition_id": expedition_id,
        "source_adventurer_id": source_adventurer_id,
        "target_id": target_id,
        "amount": amount,
        "reason_code": reason_code,
        **(payload_extra or {}),
    }
    payload_hash = hashlib.sha256(str(sorted(payload_seed.items())).encode()).hexdigest()
    return ClassStateEvent(
        event_id=eid,
        event_type=event_type,
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        target_id=target_id or None,
        amount=amount,
        payload_version=1,
        payload_hash=payload_hash,
        requested_at=_iso(datetime.now(timezone.utc)),
        expected_state_version=expected_state_version,
        reason_code=reason_code,
        trusted_drain_receipt=trusted_drain_receipt,
    )


def make_trusted_receipt(
    *,
    source_adventurer_id: str,
    target_id: str = "target-boss-01",
    expedition_id: str = "",
    mark_application_id: str = "",
) -> TrustedDrainReceipt:
    return TrustedDrainReceipt(
        drain_execution_id=f"drn-{uuid.uuid4().hex[:16]}",
        source_adventurer_id=source_adventurer_id,
        target_id=target_id,
        mark_application_id=mark_application_id or f"app-{uuid.uuid4().hex[:16]}",
        completed_at=_iso(datetime.now(timezone.utc)),
        result_code="SUCCESS",
        expedition_id=expedition_id,
        phase_id=f"expedition:{expedition_id}:phase:1" if expedition_id else "",
    )


def trusted_context(*, feature_enabled: bool = True, test_user_verified: bool = True) -> dict:
    return {
        "feature_enabled": feature_enabled,
        "test_user_verified": test_user_verified,
        "test_user_id": "test-user-01",
        "db_allowlisted": True,
        "phase_ended": False,
    }
