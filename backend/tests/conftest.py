from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config.settings import Settings
from app.infrastructure.fastapi.container import Container
from app.infrastructure.fastapi.server import create_app
from app.interface.repositories.postgres.models import Base

TEST_SECRET = "test-secret-key-that-is-long-enough-123"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        env="test",
        name="TEST API",
        version="9.9.9",
        secret_key=TEST_SECRET,
        database_url="sqlite+aiosqlite://",
    )


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    # In-memory SQLite shared by every session of the test (StaticPool = one connection)
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def mongo_db() -> Any:
    return AsyncMongoMockClient()["test"]


@pytest.fixture
async def container(settings: Settings, engine: AsyncEngine, mongo_db: Any) -> Container:
    return Container(settings, engine=engine, mongo_db=mongo_db)


@pytest.fixture
async def client(settings: Settings, container: Container) -> AsyncIterator[AsyncClient]:
    app = create_app(settings, container)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class Api:
    """Small helper so API tests read like user stories."""

    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def register(self, email: str = "somchai@example.com", password: str = "password123") -> Any:
        return await self.client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password, "first_name": "Somchai", "last_name": "Jaidee"},
        )

    async def login(self, email: str = "somchai@example.com", password: str = "password123") -> Any:
        return await self.client.post("/api/v1/users/login", json={"email": email, "password": password})

    async def register_and_login(self, email: str = "somchai@example.com") -> dict[str, Any]:
        await self.register(email)
        return (await self.login(email)).json()  # type: ignore[no-any-return]

    @staticmethod
    def bearer(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api(client: AsyncClient) -> Api:
    return Api(client)
