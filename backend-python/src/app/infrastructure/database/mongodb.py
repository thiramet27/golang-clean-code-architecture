from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

Doc = dict[str, Any]


def create_mongo_database(
    uri: str | None, name: str
) -> tuple[AsyncIOMotorClient[Doc] | None, AsyncIOMotorDatabase[Doc] | None]:
    if not uri:
        return None, None
    client: AsyncIOMotorClient[Doc] = AsyncIOMotorClient(uri)
    return client, client[name]
