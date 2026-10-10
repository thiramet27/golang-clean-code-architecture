import time
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config.settings import Settings
from app.infrastructure.database.mongodb import create_mongo_database
from app.infrastructure.fastapi.container import Container
from app.infrastructure.fastapi.server import create_app
from app.usecases.monitor import MonitorUsecase
from tests.conftest import Api


@pytest.fixture
async def lenient_client(settings: Settings, container: Container) -> AsyncIterator[AsyncClient]:
    """Client that returns 500 responses instead of re-raising server errors into the test."""
    transport = ASGITransport(app=create_app(settings, container), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_request_id_is_generated_or_propagated(api: Api) -> None:
    generated = await api.client.get("/api/v1/")
    assert len(generated.headers["X-Request-ID"]) == 32

    echoed = await api.client.get("/api/v1/", headers={"X-Request-ID": "trace-from-gateway-1"})
    assert echoed.headers["X-Request-ID"] == "trace-from-gateway-1"

    # Header injection attempts are replaced, not echoed
    unsafe = await api.client.get("/api/v1/", headers={"X-Request-ID": "x" * 200})
    assert unsafe.headers["X-Request-ID"] != "x" * 200


async def test_unexpected_error_is_json_with_request_id(
    lenient_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(self: MonitorUsecase) -> Any:
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(MonitorUsecase, "health_check", boom)
    response = await lenient_client.get("/api/v1/")
    body = response.json()
    assert response.status_code == 500
    assert body["trace_id"] == "internal-error"
    assert "secret" not in body["message"]
    assert body["request_id"] == response.headers["X-Request-ID"]


async def test_database_outage_returns_503(
    lenient_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def db_down(self: MonitorUsecase) -> Any:
        raise OperationalError("SELECT 1", None, ConnectionRefusedError("connection refused"))

    monkeypatch.setattr(MonitorUsecase, "health_check", db_down)
    response = await lenient_client.get("/api/v1/")
    assert response.status_code == 503
    assert response.json()["trace_id"] == "db-unavailable"


async def test_health_live_and_ready(api: Api) -> None:
    live = await api.client.get("/api/v1/health/live")
    assert live.json()["status"] == "ok"

    ready = (await api.client.get("/api/v1/health/ready")).json()
    assert ready["status"] == "ok"
    assert {c["name"]: c["ok"] for c in ready["checks"]} == {"postgres": True, "mongodb": True}


async def test_mongo_down_fails_fast_and_does_not_affect_postgres(
    settings: Settings, engine: AsyncEngine
) -> None:
    """Nothing listens on port 1: with default driver settings each request would hang for 30 s."""
    _, unreachable = create_mongo_database(
        "mongodb://127.0.0.1:1/?directConnection=true", "test", timeout_ms=300
    )
    container = Container(settings, engine=engine, mongo_db=unreachable)
    transport = ASGITransport(app=create_app(settings, container), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        api = Api(client)
        token = (await api.register_and_login())["token"]["access"]

        started = time.perf_counter()
        products = await client.get("/api/v1/data/products/", headers=api.bearer(token))
        assert products.status_code == 503
        assert time.perf_counter() - started < 2

        # Postgres-backed features keep working
        assert (await client.get("/api/v1/data/users/", headers=api.bearer(token))).status_code == 200
        ready = await client.get("/api/v1/health/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "degraded"
