from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_engine(url: str) -> AsyncEngine:
    # One engine (connection pool) for the whole app. The Go version opened a new pool in every
    # repository constructor, i.e. on every /data request.
    return create_async_engine(url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
