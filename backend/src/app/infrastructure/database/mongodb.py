from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

Doc = dict[str, Any]


def create_mongo_database(
    uri: str | None, name: str, timeout_ms: int = 2000
) -> tuple[AsyncIOMotorClient[Doc] | None, AsyncIOMotorDatabase[Doc] | None]:
    if not uri:
        return None, None
    # Default server selection waits 30 s; with Mongo down every /data/products request would hang that long.
    client: AsyncIOMotorClient[Doc] = AsyncIOMotorClient(
        uri,
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
        socketTimeoutMS=timeout_ms * 3,
    )
    return client, client[name]
