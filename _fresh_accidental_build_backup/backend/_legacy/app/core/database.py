"""Single Motor client + db handle. Re-imported by `server.py` and by
`app/auth/*` modules so they share a single connection pool.
"""
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGO_URL, DB_NAME


mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]


def get_db():
    """FastAPI dependency form. Yields the shared Motor db handle."""
    return db


async def close_database() -> None:
    mongo_client.close()


__all__ = ["mongo_client", "db", "get_db", "close_database"]
