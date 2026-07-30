"""Isolated real-Mongo fixtures for the classless → Class Hall journey."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store.provisioning import (
    generate_unique_run_id,
    it_database_name,
    verify_target,
)


MONGO_LOCALHOST_URI = "mongodb://127.0.0.1:27017"


async def _drop_database(db_name: str) -> None:
    client = AsyncIOMotorClient(MONGO_LOCALHOST_URI)
    try:
        await client.drop_database(db_name)
    finally:
        client.close()


@pytest.fixture(scope="function")
def class_hall_real_db() -> Iterator[str]:
    db_name = it_database_name(generate_unique_run_id())
    verify_target(MONGO_LOCALHOST_URI, db_name)
    yield db_name
    asyncio.run(_drop_database(db_name))
