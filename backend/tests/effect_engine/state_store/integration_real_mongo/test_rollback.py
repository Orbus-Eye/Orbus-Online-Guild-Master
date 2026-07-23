"""RT2-B-1B-1 · Rollback (guarded drop)."""
from __future__ import annotations

import asyncio

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store.provisioning import (
    COLLECTION_NAME,
    ProvisioningCommand,
    ProvisioningGuardError,
)


MONGO_URI = "mongodb://localhost:27017"


def test_rollback_dry_run_does_not_drop(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            await cmd.apply(dry_run=False)
            r = await cmd.rollback(dry_run=True)
            assert r.dry_run is True
            assert r.collection_dropped is True
            colls = await client[stable_test_db].list_collection_names()
            assert COLLECTION_NAME in colls
        finally:
            client.close()

    asyncio.run(go())


def test_rollback_drops_collection(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            await cmd.apply(dry_run=False)
            r = await cmd.rollback(dry_run=False)
            assert r.success is True
            assert r.collection_dropped is True
            assert r.collection_present_after is False
            colls = await client[stable_test_db].list_collection_names()
            assert COLLECTION_NAME not in colls
        finally:
            client.close()

    asyncio.run(go())


def test_rollback_idempotent_when_missing(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            r = await cmd.rollback(dry_run=False)
            assert r.success is True
            assert r.collection_dropped is False
            assert r.collection_present_after is False
        finally:
            client.close()

    asyncio.run(go())


def test_full_cycle_apply_rollback_reapply(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            cmd = ProvisioningCommand(client, MONGO_URI, stable_test_db)
            r1 = await cmd.apply(dry_run=False)
            assert r1.success
            r2 = await cmd.rollback(dry_run=False)
            assert r2.success
            r3 = await cmd.apply(dry_run=False)
            assert r3.success
            assert r3.collection_created is True
            assert r3.ttl_index_verified is True
        finally:
            client.close()

    asyncio.run(go())


def test_rollback_refuses_non_allowlisted_db(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            with pytest.raises(ProvisioningGuardError) as exc_info:
                ProvisioningCommand(client, MONGO_URI, "orbus_r16")
            assert exc_info.value.code == "FORBIDDEN_DATABASE_ORBUS_R16"
        finally:
            client.close()

    asyncio.run(go())


def test_provisioning_command_refuses_non_localhost(stable_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            with pytest.raises(ProvisioningGuardError) as exc_info:
                ProvisioningCommand(
                    client,
                    "mongodb://prod-cluster.example.com:27017",
                    "orbus_r16_rt2b_test",
                )
            assert exc_info.value.code == "TARGET_ENVIRONMENT_REJECTED"
        finally:
            client.close()

    asyncio.run(go())
