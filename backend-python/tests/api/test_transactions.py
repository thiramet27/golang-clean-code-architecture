import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config.settings import Settings
from app.infrastructure.fastapi.container import Container
from app.infrastructure.fastapi.server import create_app
from app.interface.repositories.postgres.models import UserModel

BODY = {"email": "a@example.com", "password": "password123", "first_name": "A", "last_name": "B"}


async def test_commit_failure_is_reported_to_the_client(
    settings: Settings, container: Container, engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The commit runs before the response is sent, so a failed commit can't be answered with 201."""

    async def broken_commit(self: AsyncSession) -> None:
        raise RuntimeError("database went away")

    monkeypatch.setattr(AsyncSession, "commit", broken_commit)
    transport = ASGITransport(app=create_app(settings, container), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/users/register", json=BODY)

    monkeypatch.undo()
    assert response.status_code == 500
    async with async_sessionmaker(engine)() as session:
        assert await session.scalar(select(func.count()).select_from(UserModel)) == 0
