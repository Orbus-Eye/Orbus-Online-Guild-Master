"""RT2-B-1A · Unit tests specifici del Mongo adapter.

Verifica:
- Injection contract: costruttore FALLISCE se collection is None.
- Filter construction: ogni mutation include `_id`, `state_version`,
  `fencing_token` nel filtro (verifica via mock call log).
- `find_one_and_update` invocation correctness.
- Error mapping: exception generica → `StoreInfraError`.

Nessun accesso a un real DB. Nessuna network call.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.stats.runtime.state_store import (
    CasResultCode,
    ExpeditionRuntimeState,
    MongoExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.errors import StoreInfraError
from app.stats.runtime.state_store.models import RuntimeStatus


def _make_state(expedition_id: str = "exp-u1") -> ExpeditionRuntimeState:
    return ExpeditionRuntimeState(
        expedition_id=expedition_id,
        state_version=1,
        created_at="2026-02-01T12:00:00Z",
        updated_at="2026-02-01T12:00:00Z",
        expires_at="2026-02-01T18:00:00Z",
        runtime_status=RuntimeStatus.ACTIVE,
        fencing_token=0,
    )


def _run(coro):
    # RT2-B-2B-1-V1 fix: use `new_event_loop()` (matches `transitions/conftest.py`
    # pattern). `get_event_loop()` raised `RuntimeError: There is no current event
    # loop in thread 'MainThread'` on Python 3.11 after `asyncio.run()` calls in
    # `integration_real_mongo/` fixtures consumed the default policy loop.
    return asyncio.new_event_loop().run_until_complete(coro)


# ═══════════════════════ Injection contract ═══════════════════════
def test_mongo_adapter_requires_injected_collection() -> None:
    with pytest.raises(ValueError, match="requires an injected collection"):
        MongoExpeditionRuntimeStateStore(None)


def test_mongo_adapter_accepts_injected_mock() -> None:
    mock = AsyncMock()
    adapter = MongoExpeditionRuntimeStateStore(mock)
    assert adapter is not None


# ═══════════════════════ Filter construction (CAS min) ═══════════════════════
def test_cas_filter_includes_id_state_version_fencing_token(mongo_mock_collection) -> None:
    """Verifica che il filtro CAS includa esattamente `_id + state_version + fencing_token`."""
    async def go():
        store = MongoExpeditionRuntimeStateStore(mongo_mock_collection)
        await store.create_state("exp-f1", _make_state("exp-f1"))
        await store.reserve_writer("exp-f1", "w-A", 30)
        # First mutation
        await store.compare_and_update(
            "exp-f1", expected_state_version=1, expected_fencing_token=1, mutation={"loadout_snapshot_version": 42},
        )
        # Inspect the last find_one_and_update call for CAS filter shape
        muts = [c for c in mongo_mock_collection.calls if c["op"] == "find_one_and_update"]
        # Skip lease acquire mutation (has different filter shape)
        cas_calls = [c for c in muts if "state_version" in c["filter"] and "fencing_token" in c["filter"]]
        assert len(cas_calls) >= 1
        last = cas_calls[-1]
        assert last["filter"]["_id"] == "exp-f1"
        assert last["filter"]["state_version"] == 1
        assert last["filter"]["fencing_token"] == 1
        # And the update must include $inc state_version
        assert last["update"].get("$inc", {}).get("state_version") == 1

    _run(go())


def test_apply_event_once_filter_includes_dedup_guard(mongo_mock_collection) -> None:
    """La CAS di apply_event_once deve contenere il guard `processed_event_keys.event_id != X`."""
    async def go():
        store = MongoExpeditionRuntimeStateStore(mongo_mock_collection)
        await store.create_state("exp-f2", _make_state("exp-f2"))
        await store.reserve_writer("exp-f2", "w-A", 30)
        await store.apply_event_once(
            "exp-f2", "evt-1", "mark_apply", "adv-A", "hash-x",
            expected_state_version=1, expected_fencing_token=1, mutation={},
        )
        muts = [c for c in mongo_mock_collection.calls if c["op"] == "find_one_and_update"]
        # Find the mutation that has processed_event_keys.event_id in filter
        dedup_calls = [c for c in muts if "processed_event_keys.event_id" in c["filter"]]
        assert len(dedup_calls) >= 1
        f = dedup_calls[-1]["filter"]
        # dedup guard uses $ne
        guard = f["processed_event_keys.event_id"]
        assert isinstance(guard, dict) and "$ne" in guard
        assert guard["$ne"] == "evt-1"

    _run(go())


# ═══════════════════════ Error mapping ═══════════════════════
def test_find_one_error_maps_to_store_infra_error() -> None:
    async def go():
        broken = AsyncMock()
        broken.find_one.side_effect = RuntimeError("connection lost")
        store = MongoExpeditionRuntimeStateStore(broken)
        with pytest.raises(StoreInfraError):
            await store.get_state("exp-any")

    _run(go())


def test_find_one_and_update_error_maps_to_store_infra_error() -> None:
    async def go():
        broken = AsyncMock()
        broken.find_one.return_value = {
            "_id": "exp-x", "state_version": 1, "fencing_token": 0,
            "last_event_sequence": 0, "processed_event_keys": [],
        }
        broken.find_one_and_update.side_effect = RuntimeError("timeout")
        store = MongoExpeditionRuntimeStateStore(broken)
        with pytest.raises(StoreInfraError):
            await store.compare_and_update("exp-x", 1, 0, {})

    _run(go())


def test_insert_one_duplicate_returns_already_exists(mongo_mock_collection) -> None:
    async def go():
        store = MongoExpeditionRuntimeStateStore(mongo_mock_collection)
        r1 = await store.create_state("exp-dup", _make_state("exp-dup"))
        assert r1.code == CasResultCode.SUCCESS
        r2 = await store.create_state("exp-dup", _make_state("exp-dup"))
        assert r2.code == CasResultCode.ALREADY_EXISTS

    _run(go())


# ═══════════════════════ Serialization sanity ═══════════════════════
def test_get_state_reconstructs_state_from_document(mongo_mock_collection) -> None:
    async def go():
        store = MongoExpeditionRuntimeStateStore(mongo_mock_collection)
        await store.create_state("exp-r", _make_state("exp-r"))
        r = await store.get_state("exp-r")
        assert r.code == CasResultCode.SUCCESS
        assert r.state.expedition_id == "exp-r"
        assert r.state.state_version == 1
        assert r.state.runtime_status == RuntimeStatus.ACTIVE

    _run(go())


def test_no_direct_db_import_in_adapter() -> None:
    """Il modulo `mongo_adapter` NON deve importare motor.motor_asyncio o pymongo direttamente."""
    import app.stats.runtime.state_store.mongo_adapter as mod
    src = open(mod.__file__).read()
    # Non importa motor / pymongo (usa duck-typing via injection)
    assert "from motor" not in src
    assert "import motor" not in src
    assert "from pymongo" not in src
    assert "import pymongo" not in src
