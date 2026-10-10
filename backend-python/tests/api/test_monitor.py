from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    assert response.json() == {"name": "TEST API", "version": "9.9.9"}


async def test_unknown_route_uses_go_error_format(client: AsyncClient) -> None:
    response = await client.get("/api/v1/nope")
    assert response.status_code == 404
    assert response.json() == {"trace_id": "middlware-001", "message": "router not found"}


async def test_swagger_is_served(client: AsyncClient) -> None:
    assert (await client.get("/swagger")).status_code == 200
