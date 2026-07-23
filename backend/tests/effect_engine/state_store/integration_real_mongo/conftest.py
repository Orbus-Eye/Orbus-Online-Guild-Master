"""RT2-B-1B-1 · Conftest per integration test real-Mongo.

**Design pattern**: fixture returnano **solo stringhe** (URI, db name); il
`AsyncIOMotorClient` viene istanziato *dentro* ogni `asyncio.run(go())`
per evitare cross-loop binding issues (motor si lega al loop al primo
await, quindi non può sopravvivere all'uscita di `asyncio.run`).

Fixture esposte:
- `mongo_localhost_uri` — costante `mongodb://localhost:27017`.
- `stable_test_db` — nome db fisso `orbus_r16_rt2b_test` (idempotency/manual verify).
- `unique_test_db` — nome db `orbus_r16_rt2b_it_<unique_run_id>`, con teardown drop.
- `provisioned_stable_db` — db name già provisioned (chiama `--apply` prima del test).
- `provisioned_unique_db` — db name già provisioned + drop in teardown.

Cleanup teardown = best-effort mandatory. Il drop viene eseguito con un
`asyncio.run` dedicato (nuovo loop) per garantire indipendenza dal loop
del test.
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


async def _ensure_collection_absent(uri: str, db_name: str) -> None:
    client = AsyncIOMotorClient(uri)
    try:
        db = client[db_name]
        if COLLECTION_NAME in await db.list_collection_names():
            await db.drop_collection(COLLECTION_NAME)
    finally:
        client.close()


async def _drop_collection(uri: str, db_name: str) -> None:
    client = AsyncIOMotorClient(uri)
    try:
        db = client[db_name]
        if COLLECTION_NAME in await db.list_collection_names():
            await db.drop_collection(COLLECTION_NAME)
    finally:
        client.close()


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
            raise AssertionError(f"provisioning setup failed: {report.errors}")
    finally:
        client.close()


@pytest.fixture(scope="function")
def stable_test_db() -> Iterator[str]:
    """Nome DB fisso (stringa). Pulisce la collection RT2-B pre + post."""
    db_name = ALLOWED_STABLE_DATABASE
    verify_target(MONGO_LOCALHOST_URI, db_name)
    asyncio.run(_ensure_collection_absent(MONGO_LOCALHOST_URI, db_name))
    yield db_name
    try:
        asyncio.run(_drop_collection(MONGO_LOCALHOST_URI, db_name))
    except Exception:
        pass


@pytest.fixture(scope="function")
def unique_test_db() -> Iterator[str]:
    """Nome DB per-run (stringa). Drop dell'intero DB in teardown."""
    run_id = generate_unique_run_id()
    db_name = it_database_name(run_id)
    verify_target(MONGO_LOCALHOST_URI, db_name)
    yield db_name
    try:
        asyncio.run(_drop_database(MONGO_LOCALHOST_URI, db_name))
    except Exception:
        pass


@pytest.fixture(scope="function")
def provisioned_stable_db(stable_test_db: str) -> str:
    """Stable DB già provisioned. Ritorna solo il nome."""
    asyncio.run(_apply_provisioning(MONGO_LOCALHOST_URI, stable_test_db))
    return stable_test_db


@pytest.fixture(scope="function")
def provisioned_unique_db(unique_test_db: str) -> str:
    """Unique DB già provisioned. Ritorna solo il nome."""
    asyncio.run(_apply_provisioning(MONGO_LOCALHOST_URI, unique_test_db))
    return unique_test_db
