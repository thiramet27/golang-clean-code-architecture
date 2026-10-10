from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class PostgresProbe:
    name = "postgres"
    critical = True

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def check(self) -> None:
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))


class MongoProbe:
    name = "mongodb"
    critical = False  # only the /data/products example depends on it

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self._db = db

    async def check(self) -> None:
        await self._db.command("ping")
