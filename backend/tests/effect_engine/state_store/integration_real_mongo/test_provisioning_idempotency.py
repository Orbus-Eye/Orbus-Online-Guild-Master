"""RT2-B-1B-1 · Idempotency: apply × 2 → metadata identical."""
from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store.provisioning import (
    COLLECTION_NAME,
    TTL_INDEX_NAME,
    ProvisioningCommand,
)


MONGO_URI = "mongodb://localhost:27017"


def _index_signature(indexes):
    return sorted(
        (
            idx.get("name"),
            tuple(sorted((idx.get("key") or {}).items())),
            idx.get("expireAfterSeconds"),
        )
        for idx in indexes
    )


def test_apply_creates_collection_and_ttl_index(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            report = await cmd.apply(dry_run=False)
            assert report.success, report.errors
            assert report.collection_created is True
            assert report.ttl_index_created is True
            assert report.ttl_index_verified is True
            assert report.collection_present_after is True
            ttl_index = next(i for i in report.indexes_after if i.get("name") == TTL_INDEX_NAME)
            assert ttl_index["expireAfterSeconds"] == 0
            assert ttl_index["key"] == {"expires_at": 1}
        finally:
            client.close()

    asyncio.run(go())


def test_apply_is_idempotent(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            r1 = await cmd.apply(dry_run=False)
            assert r1.success
            sig_after_first = _index_signature(r1.indexes_after)
            colls_after_first = COLLECTION_NAME in await client[stable_test_db].list_collection_names()

            r2 = await cmd.apply(dry_run=False)
            assert r2.success
            sig_after_second = _index_signature(r2.indexes_after)
            colls_after_second = COLLECTION_NAME in await client[stable_test_db].list_collection_names()

            assert sig_after_first == sig_after_second, "index set changed on second apply"
            assert colls_after_first == colls_after_second is True
            assert r2.collection_created is False
            assert r2.ttl_index_created is False
            assert r2.ttl_index_verified is True
        finally:
            client.close()

    asyncio.run(go())


def test_apply_three_times_stable(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            sigs = []
            for _ in range(3):
                r = await cmd.apply(dry_run=False)
                assert r.success
                sigs.append(_index_signature(r.indexes_after))
            assert sigs[0] == sigs[1] == sigs[2]
        finally:
            client.close()

    asyncio.run(go())


def test_dry_run_does_not_write(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            db = client[stable_test_db]
            colls_before = await db.list_collection_names()
            assert COLLECTION_NAME not in colls_before, "stable DB was not clean pre-test"

            r = await cmd.apply(dry_run=True)
            assert r.dry_run is True
            assert r.collection_created is True

            colls_after = await db.list_collection_names()
            assert COLLECTION_NAME not in colls_after, "dry-run wrote to Mongo"
        finally:
            client.close()

    asyncio.run(go())
