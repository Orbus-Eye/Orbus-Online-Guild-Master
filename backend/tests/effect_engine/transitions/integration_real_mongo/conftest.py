"""RT2-B-2B-1-V1 · Conftest per transitions real-Mongo integration.

Riusa il pattern del conftest esistente in `state_store/integration_real_mongo/`:
- fixture ritornano solo stringhe (DB name)
- client Motor istanziato *dentro* asyncio.run per evitare cross-loop
- cleanup teardown best-effort (drop_database)
- DB allowlisted: `orbus_r16_rt2b_test` e `orbus_r16_rt2b_it_<unique_run_id>`
"""
from __future__ import annotations

import asyncio
from typing import Iterator

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store.provisioning import (
    ALLOWED_STABLE_DATABASE,
    COLLECTION_NAME,
    ProvisioningCommand,
    generate_unique_run_id,
    it_database_name,
    verify_target,
)


MONGO_LOCALHOST_URI = "mongodb://localhost:27017"


@pytest.fixture(scope="session")
def mongo_localhost_uri() -> str:
    return MONGO_LOCALHOST_URI


async def _drop_database(uri: str, db_name: str) -> None:
    client = AsyncIOMotorClient(uri)
    try:
        await client.drop_database(db_name)
    finally:
        client.close()


async def _apply_provisioning(uri: str, db_name: str) -> None:
    client = AsyncIOMotorClient(uri)
    try:
        cmd = ProvisioningCommand(client, uri, db_name)
        report = await cmd.apply(dry_run=False)
        if not report.success:
            raise AssertionError(f"provisioning failed: {report.errors}")
    finally:
        client.close()


@pytest.fixture(scope="function")
def unique_test_db() -> Iterator[str]:
    """DB unico per-run, drop dell'intero DB in teardown."""
    run_id = generate_unique_run_id()
    db_name = it_database_name(run_id)
    verify_target(MONGO_LOCALHOST_URI, db_name)
    yield db_name
    try:
        asyncio.run(_drop_database(MONGO_LOCALHOST_URI, db_name))
    except Exception:
        pass


@pytest.fixture(scope="function")
def provisioned_unique_db(unique_test_db: str) -> str:
    """DB unico già provisioned (collection + indici RT2-B)."""
    asyncio.run(_apply_provisioning(MONGO_LOCALHOST_URI, unique_test_db))
    return unique_test_db
