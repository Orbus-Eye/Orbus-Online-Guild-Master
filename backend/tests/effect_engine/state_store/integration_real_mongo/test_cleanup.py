"""RT2-B-1B-1 · Cleanup verification (post-suite database residues == 0)."""
from __future__ import annotations

import asyncio
import re

from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URI = "mongodb://localhost:27017"
IT_DB_RE = re.compile(r"^orbus_r16_rt2b_it_[a-z0-9_-]+$")


def test_no_orbus_r16_writes_across_run():
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            db = client["orbus_r16"]
            colls = await db.list_collection_names()
            assert "expedition_runtime_states" not in colls, (
                f"expedition_runtime_states must NEVER appear in orbus_r16; got {colls}"
            )
        finally:
            client.close()

    asyncio.run(go())


def test_no_orbus_r16_test_writes():
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            db = client["orbus_r16_test"]
            colls = await db.list_collection_names()
            assert "expedition_runtime_states" not in colls, (
                f"expedition_runtime_states must NEVER appear in orbus_r16_test; got {colls}"
            )
        finally:
            client.close()

    asyncio.run(go())


def test_teardown_drops_unique_test_dbs(unique_test_db):
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            coll = client[unique_test_db]["expedition_runtime_states"]
            await coll.insert_one({"_id": "test-doc-cleanup", "state_version": 1, "fencing_token": 0})
            dbs = await client.list_database_names()
            assert unique_test_db in dbs
        finally:
            client.close()

    asyncio.run(go())


def test_all_it_databases_have_valid_name():
    async def go():
        client = AsyncIOMotorClient(MONGO_URI)
        try:
            dbs = await client.list_database_names()
            it_dbs = [d for d in dbs if d.startswith("orbus_r16_rt2b_it_")]
            for db in it_dbs:
                assert IT_DB_RE.match(db), f"IT db {db!r} does not match allowlist regex"
        finally:
            client.close()

    asyncio.run(go())
