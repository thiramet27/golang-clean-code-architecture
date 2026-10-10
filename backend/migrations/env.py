"""Alembic migrations (Go: src/infrastructure/database/postgres/migration/main.go used AutoMigrate)."""

import asyncio

from alembic import context
from sqlalchemy.engine import Connection

from app.config.settings import get_settings
from app.infrastructure.database.postgres import create_engine
from app.interface.repositories.postgres.models import Base

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_engine(get_settings())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(url=get_settings().sqlalchemy_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_migrations_online())
