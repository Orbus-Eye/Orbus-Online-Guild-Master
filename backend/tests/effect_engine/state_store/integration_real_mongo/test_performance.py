"""RT2-B-1B-1 · Performance acceptance (p95 targets · 50+ samples)."""
from __future__ import annotations

import asyncio
import statistics
import time

from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store import (
    CasResultCode,
    ExpeditionRuntimeState,
)
from app.stats.runtime.state_store.models import RuntimeStatus
from app.stats.runtime.state_store.mongo_adapter import MongoExpeditionRuntimeStateStore
from app.stats.runtime.state_store.provisioning import COLLECTION_NAME


MONGO_URI = "mongodb://localhost:27017"
SAMPLE_COUNT = 50


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


def _percentile(samples, p):
    sorted_samples = sorted(samples)
    k = int(round((p / 100.0) * (len(sorted_samples) - 1)))
    return sorted_samples[k]


def _report(label, samples_ms, budget_ms):
    p50 = _percentile(samples_ms, 50)
    p95 = _percentile(samples_ms, 95)
    p99 = _percentile(samples_ms, 99)
    print(
        f"[PERF] {label} n={len(samples_ms)} "
        f"p50={p50:.2f}ms p95={p95:.2f}ms p99={p99:.2f}ms "
        f"budget_p95={budget_ms}ms mean={statistics.mean(samples_ms):.2f}ms"
    )
    return p50, p95, p99


def test_perf_single_state_read_p95(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-perf-read"
            await store.create_state(exp_id, _make_initial(exp_id))
            samples = []
            for _ in range(SAMPLE_COUNT):
                t0 = time.perf_counter()
                await store.get_state(exp_id)
                samples.append((time.perf_counter() - t0) * 1000)
            p50, p95, p99 = _report("single_state_read", samples, 25)
            assert p95 <= 25, f"single-state read p95={p95:.2f}ms exceeds 25ms budget"
        finally:
            client.close()

    asyncio.run(go())


def test_perf_cas_mutation_p95(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-perf-cas"
            await store.create_state(exp_id, _make_initial(exp_id))
            lease = await store.reserve_writer(exp_id, "w-perf", 300)
            samples = []
            for i in range(SAMPLE_COUNT):
                cur = await store.get_state(exp_id)
                t0 = time.perf_counter()
                r = await store.compare_and_update(
                    exp_id,
                    expected_state_version=cur.state.state_version,
                    expected_fencing_token=lease.fencing_token,
                    mutation={"loadout_snapshot_version": i},
                )
                samples.append((time.perf_counter() - t0) * 1000)
                assert r.code == CasResultCode.SUCCESS
            p50, p95, p99 = _report("cas_mutation", samples, 35)
            assert p95 <= 35, f"CAS mutation p95={p95:.2f}ms exceeds 35ms budget"
        finally:
            client.close()

    asyncio.run(go())


def test_perf_lease_acquire_renew_p95(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            acquire_samples = []
            renew_samples = []
            for i in range(SAMPLE_COUNT):
                exp_id = f"exp-perf-lease-{i}"
                await store.create_state(exp_id, _make_initial(exp_id))
                t0 = time.perf_counter()
                lease = await store.reserve_writer(exp_id, f"w-{i}", 30)
                acquire_samples.append((time.perf_counter() - t0) * 1000)
                assert lease.code == CasResultCode.SUCCESS
                t0 = time.perf_counter()
                r = await store.renew_writer_lease(exp_id, lease.lease_id, lease.fencing_token, 30)
                renew_samples.append((time.perf_counter() - t0) * 1000)
                assert r.code == CasResultCode.SUCCESS
            _report("lease_acquire", acquire_samples, 35)
            _report("lease_renew", renew_samples, 35)
            assert _percentile(acquire_samples, 95) <= 35
            assert _percentile(renew_samples, 95) <= 35
        finally:
            client.close()

    asyncio.run(go())


def test_perf_deduplicated_retry_p95(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-perf-dedup"
            await store.create_state(exp_id, _make_initial(exp_id))
            lease = await store.reserve_writer(exp_id, "w-d", 30)
            cur = await store.get_state(exp_id)
            await store.apply_event_once(
                expedition_id=exp_id,
                event_id="evt-perf",
                event_type="mark_progress",
                source_adventurer_id="adv-A",
                payload_hash="h-perf",
                expected_state_version=cur.state.state_version,
                expected_fencing_token=lease.fencing_token,
                mutation={"loadout_snapshot_version": 1},
            )
            samples = []
            for _ in range(SAMPLE_COUNT):
                t0 = time.perf_counter()
                r = await store.apply_event_once(
                    expedition_id=exp_id,
                    event_id="evt-perf",
                    event_type="mark_progress",
                    source_adventurer_id="adv-A",
                    payload_hash="h-perf",
                    expected_state_version=cur.state.state_version,
                    expected_fencing_token=lease.fencing_token,
                    mutation={"loadout_snapshot_version": 1},
                )
                samples.append((time.perf_counter() - t0) * 1000)
                assert r.code == CasResultCode.DEDUPLICATED_NO_OP
            p50, p95, p99 = _report("dedup_retry", samples, 25)
            assert p95 <= 25, f"dedup retry p95={p95:.2f}ms exceeds 25ms budget"
        finally:
            client.close()

    asyncio.run(go())
