from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.interface.repositories.postgres.models import UserPermissionModel
from tests.conftest import Api


async def grant(engine: AsyncEngine, user_id: int, permission: str) -> None:
    async with async_sessionmaker(engine)() as session, session.begin():
        session.add(UserPermissionModel(user_id=user_id, permission=permission))


@pytest.fixture
async def token(api: Api) -> str:
    for i in range(1, 13):
        await api.register(f"user{i:02}@example.com")
    return (await api.login("user01@example.com")).json()["token"]["access"]  # type: ignore[no-any-return]


async def get(api: Api, path: str, token: str, **params: Any) -> Any:
    return await api.client.get(f"/api/v1/data/{path}", headers=api.bearer(token), params=params)


async def test_requires_login(api: Api) -> None:
    response = await api.client.get("/api/v1/data/users/")
    assert response.status_code == 401


async def test_list_users_paginates_with_real_total(api: Api, token: str) -> None:
    body = (await get(api, "users/", token, _page=2, _pageSize=5)).json()
    assert [u["email"] for u in body["data"]] == [f"user{i:02}@example.com" for i in range(6, 11)]
    assert (body["total_data"], body["total_page"], body["page"], body["page_size"]) == (12, 3, 2, 5)


async def test_password_is_never_returned(api: Api, token: str) -> None:
    body = (await get(api, "users/", token)).json()
    assert all("password" not in u for u in body["data"])
    assert "password" not in [f["name"] for f in body["data_schema"]["fields"]]


async def test_filters_are_applied_and_whitelisted(api: Api, token: str) -> None:
    body = (await get(api, "users/", token, email="user07@example.com")).json()
    assert [u["id"] for u in body["data"]] == [7]

    for bad in ({"password": "x"}, {"nope": "x"}, {"id": "abc"}):
        response = await get(api, "users/", token, **bad)
        assert response.status_code == 400, bad


async def test_get_one_and_describe(api: Api, token: str) -> None:
    body = (await get(api, "users/3", token)).json()
    assert body["data"]["email"] == "user03@example.com"
    assert body["data_schema"]["name"] == "user-model"

    schema = (await get(api, "users/describe", token)).json()
    assert {"name": "email", "type": "string"} in schema["fields"]
    assert {"name": "created_at", "type": "datetime"} in schema["fields"]


@pytest.mark.parametrize("path", ["users/999", "users/not-a-number", "nope/", "user-tokens/"])
async def test_not_found(api: Api, token: str, path: str) -> None:
    # user-tokens existed in the Go version and leaked every user's tokens; here it is not exposed.
    response = await get(api, path, token)
    assert response.status_code == 404
    assert response.json()["trace_id"] == "data-001"


async def test_admin_only_model(api: Api, token: str, engine: AsyncEngine) -> None:
    assert (await get(api, "user-permissions/", token)).status_code == 403
    await grant(engine, 1, "admin")
    response = await get(api, "user-permissions/", token)
    assert response.status_code == 200
    assert response.json()["data"][0]["permission"] == "admin"


async def test_mongodb_model(api: Api, token: str, mongo_db: Any) -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    result = await mongo_db.products.insert_many(
        [
            {"name": "Camera", "price": 12900.0, "in_stock": True, "created_at": created},
            {"name": "Tripod", "price": 990.0, "in_stock": False, "created_at": created},
        ]
    )
    body = (await get(api, "products/", token, in_stock="true")).json()
    assert [p["name"] for p in body["data"]] == ["Camera"]
    assert body["total_data"] == 1

    one = (await get(api, f"products/{result.inserted_ids[1]}", token)).json()
    assert one["data"]["name"] == "Tripod"
    assert (await get(api, "products/not-an-object-id", token)).status_code == 404
    assert (await get(api, "products/", token, **{"$where": "1"})).status_code == 400
