from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    # One engine (connection pool) for the whole app. The Go version opened a new pool in every
    # repository constructor, i.e. on every /data request.
    url = settings.sqlalchemy_url
    options: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        options |= {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "connect_args": {
                "timeout": settings.db_connect_timeout,
                # Postgres cancels any query running longer than this, so one slow query
                # can't hold a pooled connection (and a request) forever.
                "server_settings": {"statement_timeout": str(settings.db_statement_timeout_ms)},
            },
        }
    return create_async_engine(url, **options)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
