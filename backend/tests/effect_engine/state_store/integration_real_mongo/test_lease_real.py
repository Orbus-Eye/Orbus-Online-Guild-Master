"""RT2-B-1B-1 · Lease + fencing lifecycle su Mongo reale."""
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


def _open_store(db_name):
    client = AsyncIOMotorClient(MONGO_URI)
    coll = client[db_name][COLLECTION_NAME]
    return client, MongoExpeditionRuntimeStateStore(coll)


def test_real_lease_acquire(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            await store.create_state("exp-l-r1", _make_initial("exp-l-r1"))
            r = await store.reserve_writer("exp-l-r1", "worker-A", 30)
            assert r.code == CasResultCode.SUCCESS
            assert r.lease_id
            assert r.fencing_token == 1
        finally:
            client.close()

    asyncio.run(go())


def test_real_lease_second_acquire_rejected_while_active(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            await store.create_state("exp-l-r2", _make_initial("exp-l-r2"))
            r1 = await store.reserve_writer("exp-l-r2", "worker-A", 30)
            assert r1.code == CasResultCode.SUCCESS
            r2 = await store.reserve_writer("exp-l-r2", "worker-B", 30)
            assert r2.code == CasResultCode.STATE_VERSION_CONFLICT
        finally:
            client.close()

    asyncio.run(go())


def test_real_lease_renewal_preserves_fencing_token(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            await store.create_state("exp-l-r3", _make_initial("exp-l-r3"))
            r1 = await store.reserve_writer("exp-l-r3", "worker-A", 30)
            assert r1.fencing_token == 1
            r2 = await store.renew_writer_lease("exp-l-r3", r1.lease_id, 1, extend_seconds=30)
            assert r2.code == CasResultCode.SUCCESS
            assert r2.fencing_token == 1
        finally:
            client.close()

    asyncio.run(go())


def test_real_lease_release_and_reacquire(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            await store.create_state("exp-l-r4", _make_initial("exp-l-r4"))
            r1 = await store.reserve_writer("exp-l-r4", "worker-A", 30)
            r2 = await store.release_writer("exp-l-r4", r1.lease_id, r1.fencing_token)
            assert r2.code == CasResultCode.SUCCESS
            r3 = await store.reserve_writer("exp-l-r4", "worker-B", 30)
            assert r3.code == CasResultCode.SUCCESS
            assert r3.fencing_token == 2
        finally:
            client.close()

    asyncio.run(go())
