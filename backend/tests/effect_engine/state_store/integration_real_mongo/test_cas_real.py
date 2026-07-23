"""RT2-B-1B-1 · CAS real Mongo tests (success + conflicts + fencing)."""
from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store import (
    CasResultCode,
    ExpeditionRuntimeState,
)
from app.stats.runtime.state_store.models import RuntimeStatus
from app.stats.runtime.state_store.mongo_adapter import MongoExpeditionRuntimeStateStore
from app.stats.runtime.state_store.provisioning import COLLECTION_NAME


MONGO_URI = "mongodb://localhost:27017"


def _make_initial(expedition_id: str) -> ExpeditionRuntimeState:
    return ExpeditionRuntimeState(
        expedition_id=expedition_id,
        state_version=1,
        created_at="2026-02-01T12:00:00Z",
        updated_at="2026-02-01T12:00:00Z",
        expires_at="2026-02-01T18:00:00Z",
        runtime_status=RuntimeStatus.ACTIVE,
        loadout_snapshot_version=0,
        fencing_token=0,
    )


def _open_client_and_store(db_name):
    client = AsyncIOMotorClient(MONGO_URI)
    coll = client[db_name][COLLECTION_NAME]
    store = MongoExpeditionRuntimeStateStore(coll)
    return client, store


def test_real_create_and_get(provisioned_unique_db):
    async def go():
        client, store = _open_client_and_store(provisioned_unique_db)
        try:
            r1 = await store.create_state("exp-real-c1", _make_initial("exp-real-c1"))
            assert r1.code == CasResultCode.SUCCESS
            assert r1.new_state_version == 1
            r2 = await store.get_state("exp-real-c1")
            assert r2.code == CasResultCode.SUCCESS
            assert r2.state.state_version == 1
            assert r2.state.expedition_id == "exp-real-c1"
        finally:
            client.close()

    asyncio.run(go())


def test_real_create_duplicate_returns_already_exists(provisioned_unique_db):
    async def go():
        client, store = _open_client_and_store(provisioned_unique_db)
        try:
            await store.create_state("exp-real-c2", _make_initial("exp-real-c2"))
            r = await store.create_state("exp-real-c2", _make_initial("exp-real-c2"))
            assert r.code == CasResultCode.ALREADY_EXISTS
        finally:
            client.close()

    asyncio.run(go())


def test_real_cas_success(provisioned_unique_db):
    async def go():
        client, store = _open_client_and_store(provisioned_unique_db)
        try:
            await store.create_state("exp-real-c3", _make_initial("exp-real-c3"))
            lease = await store.reserve_writer("exp-real-c3", "worker-A", 30)
            assert lease.code == CasResultCode.SUCCESS
            cur = await store.get_state("exp-real-c3")
            r = await store.compare_and_update(
                "exp-real-c3",
                expected_state_version=cur.state.state_version,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 7},
            )
            assert r.code == CasResultCode.SUCCESS
            assert r.new_state_version == cur.state.state_version + 1
        finally:
            client.close()

    asyncio.run(go())


def test_real_cas_state_version_conflict(provisioned_unique_db):
    async def go():
        client, store = _open_client_and_store(provisioned_unique_db)
        try:
            await store.create_state("exp-real-c4", _make_initial("exp-real-c4"))
            lease = await store.reserve_writer("exp-real-c4", "worker-A", 30)
            cur = await store.get_state("exp-real-c4")
            r1 = await store.compare_and_update(
                "exp-real-c4",
                expected_state_version=cur.state.state_version,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 1},
            )
            assert r1.code == CasResultCode.SUCCESS
            r2 = await store.compare_and_update(
                "exp-real-c4",
                expected_state_version=cur.state.state_version,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 2},
            )
            assert r2.code == CasResultCode.STATE_VERSION_CONFLICT
        finally:
            client.close()

    asyncio.run(go())


def test_real_cas_fencing_mismatch(provisioned_unique_db):
    async def go():
        client, store = _open_client_and_store(provisioned_unique_db)
        try:
            await store.create_state("exp-real-c5", _make_initial("exp-real-c5"))
            lease = await store.reserve_writer("exp-real-c5", "worker-A", 30)
            cur = await store.get_state("exp-real-c5")
            r = await store.compare_and_update(
                "exp-real-c5",
                expected_state_version=cur.state.state_version,
                expected_fencing_token=999,
                mutation={"loadout_snapshot_version": 1},
            )
            assert r.code == CasResultCode.STALE_WRITER_REJECTED
        finally:
            client.close()

    asyncio.run(go())


def test_real_state_version_monotonicity(provisioned_unique_db):
    async def go():
        client, store = _open_client_and_store(provisioned_unique_db)
        try:
            await store.create_state("exp-real-c6", _make_initial("exp-real-c6"))
            lease = await store.reserve_writer("exp-real-c6", "worker-A", 30)
            versions = []
            for i in range(5):
                cur = await store.get_state("exp-real-c6")
                r = await store.compare_and_update(
                    "exp-real-c6",
                    expected_state_version=cur.state.state_version,
                    expected_fencing_token=lease.fencing_token,
                    mutation={"loadout_snapshot_version": i},
                )
                assert r.code == CasResultCode.SUCCESS
                versions.append(r.new_state_version)
            assert versions == sorted(versions)
            assert len(set(versions)) == len(versions)
        finally:
            client.close()

    asyncio.run(go())
