"""RT2-B-1B-1 · Deduplication + EVENT_ID_PAYLOAD_MISMATCH real Mongo."""
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


async def _setup(store, exp_id):
    await store.create_state(exp_id, _make_initial(exp_id))
    lease = await store.reserve_writer(exp_id, "worker-A", 30)
    cur = await store.get_state(exp_id)
    return lease, cur.state.state_version


def test_real_dedup_idempotent(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            lease, sv = await _setup(store, "exp-dedup-r1")
            r1 = await store.apply_event_once(
                expedition_id="exp-dedup-r1",
                event_id="evt-001",
                event_type="mark_progress",
                source_adventurer_id="adv-A",
                payload_hash="hash-A",
                expected_state_version=sv,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 1},
            )
            assert r1.code == CasResultCode.SUCCESS
            r2 = await store.apply_event_once(
                expedition_id="exp-dedup-r1",
                event_id="evt-001",
                event_type="mark_progress",
                source_adventurer_id="adv-A",
                payload_hash="hash-A",
                expected_state_version=sv,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 1},
            )
            assert r2.code == CasResultCode.DEDUPLICATED_NO_OP
        finally:
            client.close()

    asyncio.run(go())


def test_real_dedup_payload_mismatch(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            lease, sv = await _setup(store, "exp-dedup-r2")
            r1 = await store.apply_event_once(
                expedition_id="exp-dedup-r2",
                event_id="evt-x",
                event_type="mark_progress",
                source_adventurer_id="adv-A",
                payload_hash="hash-original",
                expected_state_version=sv,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 1},
            )
            assert r1.code == CasResultCode.SUCCESS
            r2 = await store.apply_event_once(
                expedition_id="exp-dedup-r2",
                event_id="evt-x",
                event_type="mark_progress",
                source_adventurer_id="adv-A",
                payload_hash="hash-forged",
                expected_state_version=sv,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 2},
            )
            assert r2.code == CasResultCode.EVENT_ID_PAYLOAD_MISMATCH
        finally:
            client.close()

    asyncio.run(go())


def test_real_dedup_retry_ten_times(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            lease, sv = await _setup(store, "exp-dedup-r3")
            await store.apply_event_once(
                expedition_id="exp-dedup-r3",
                event_id="evt-r3",
                event_type="mark_progress",
                source_adventurer_id="adv-A",
                payload_hash="hash-r3",
                expected_state_version=sv,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 5},
            )
            for _ in range(10):
                r = await store.apply_event_once(
                    expedition_id="exp-dedup-r3",
                    event_id="evt-r3",
                    event_type="mark_progress",
                    source_adventurer_id="adv-A",
                    payload_hash="hash-r3",
                    expected_state_version=sv,
                    expected_fencing_token=lease.fencing_token,
                    mutation={"loadout_snapshot_version": 5},
                )
                assert r.code == CasResultCode.DEDUPLICATED_NO_OP
        finally:
            client.close()

    asyncio.run(go())
