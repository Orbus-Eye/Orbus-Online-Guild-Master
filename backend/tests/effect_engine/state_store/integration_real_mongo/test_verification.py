"""RT2-B-1B-1 · Verification command (read-only)."""
from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store.provisioning import (
    TTL_INDEX_NAME,
    ProvisioningCommand,
)


MONGO_URI = "mongodb://localhost:27017"


def test_verify_reports_missing_collection(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            r = await cmd.verify()
            assert r.action == "verify"
            assert r.dry_run is True
            assert r.collection_present_before is False
            assert r.ttl_index_verified is False
            assert r.success is False
            assert "collection not present" in r.errors
        finally:
            client.close()

    asyncio.run(go())


def test_verify_reports_healthy_state(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            await cmd.apply(dry_run=False)
            r = await cmd.verify()
            assert r.success is True
            assert r.collection_present_before is True
            assert r.ttl_index_verified is True
            ttl = next(i for i in r.indexes_after if i["name"] == TTL_INDEX_NAME)
            assert ttl["expireAfterSeconds"] == 0
            assert ttl["key"] == {"expires_at": 1}
        finally:
            client.close()

    asyncio.run(go())


def test_verify_does_not_write(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            db = client[stable_test_db]
            colls_before = await db.list_collection_names()
            r = await cmd.verify()
            colls_after = await db.list_collection_names()
            assert colls_before == colls_after
            assert r.dry_run is True
        finally:
            client.close()

    asyncio.run(go())
