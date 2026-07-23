"""RT2-B-1B-1 · Concurrent mutation tests (asyncio.gather race)."""
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


def test_real_concurrent_cas_only_one_winner(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            await store.create_state("exp-cc-1", _make_initial("exp-cc-1"))
            lease = await store.reserve_writer("exp-cc-1", "worker-A", 30)
            cur = await store.get_state("exp-cc-1")

            async def _do_cas(v):
                return await store.compare_and_update(
                    "exp-cc-1",
                    expected_state_version=cur.state.state_version,
                    expected_fencing_token=lease.fencing_token,
                    mutation={"loadout_snapshot_version": v},
                )

            results = await asyncio.gather(*[_do_cas(v) for v in range(4)])
            winners = [r for r in results if r.code == CasResultCode.SUCCESS]
            losers = [r for r in results if r.code == CasResultCode.STATE_VERSION_CONFLICT]
            assert len(winners) == 1
            assert len(losers) == 3
        finally:
            client.close()

    asyncio.run(go())


def test_real_concurrent_lease_only_one_holder(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            await store.create_state("exp-cc-2", _make_initial("exp-cc-2"))

            async def _reserve(worker_id):
                return await store.reserve_writer("exp-cc-2", worker_id, 30)

            results = await asyncio.gather(*[_reserve(f"worker-{i}") for i in range(3)])
            winners = [r for r in results if r.code == CasResultCode.SUCCESS]
            assert len(winners) == 1
        finally:
            client.close()

    asyncio.run(go())


def test_real_concurrent_state_isolation_across_expeditions(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_ids = [f"exp-iso-{i}" for i in range(5)]
            await asyncio.gather(*[
                store.create_state(eid, _make_initial(eid)) for eid in exp_ids
            ])
            states = await asyncio.gather(*[store.get_state(eid) for eid in exp_ids])
            seen = set()
            for eid, r in zip(exp_ids, states):
                assert r.code == CasResultCode.SUCCESS
                assert r.state.expedition_id == eid
                seen.add(eid)
            assert seen == set(exp_ids)
        finally:
            client.close()

    asyncio.run(go())
