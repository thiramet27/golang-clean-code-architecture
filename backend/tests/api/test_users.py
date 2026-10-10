from tests.conftest import Api


async def test_register(api: Api) -> None:
    response = await api.register()
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "somchai@example.com"
    assert "password" not in body


async def test_register_duplicate_email(api: Api) -> None:
    await api.register()
    response = await api.register("SOMCHAI@example.com")
    assert response.status_code == 409
    assert response.json()["trace_id"] == "users-001"


async def test_register_invalid_body(api: Api) -> None:
    response = await api.register(email="not-an-email")
    assert response.status_code == 400
    assert response.json()["trace_id"] == "middlware-003"
    assert (await api.register(password="short")).status_code == 400


async def test_login_and_profile(api: Api) -> None:
    await api.register()
    login = await api.login()
    assert login.status_code == 200
    token = login.json()["token"]

    for method in ("GET", "POST"):
        profile = await api.client.request(
            method, "/api/v1/users/profile", headers=api.bearer(token["access"])
        )
        assert profile.status_code == 200
        assert profile.json()["email"] == "somchai@example.com"


async def test_login_wrong_password(api: Api) -> None:
    await api.register()
    response = await api.login(password="wrong-password")
    assert response.status_code == 400
    body = response.json()
    assert (body["trace_id"], body["message"]) == ("users-002", "email or password is invalid")


async def test_profile_requires_valid_token(api: Api) -> None:
    for headers in ({}, api.bearer("garbage")):
        response = await api.client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 401
        assert response.json()["trace_id"] == "middlware-002"


async def test_refresh_token(api: Api) -> None:
    tokens = (await api.register_and_login())["token"]
    response = await api.client.post("/api/v1/users/refresh-token", json={"refresh_token": tokens["refresh"]})
    assert response.status_code == 200
    new = response.json()["token"]
    assert (
        await api.client.get("/api/v1/users/profile", headers=api.bearer(new["access"]))
    ).status_code == 200
    assert (
        await api.client.get("/api/v1/users/profile", headers=api.bearer(tokens["access"]))
    ).status_code == 401


async def test_logout_revokes_tokens(api: Api) -> None:
    tokens = (await api.register_and_login())["token"]
    response = await api.client.post("/api/v1/users/logout", json={"refresh_token": tokens["refresh"]})
    assert response.status_code == 200
    assert (
        await api.client.get("/api/v1/users/profile", headers=api.bearer(tokens["access"]))
    ).status_code == 401

    again = await api.client.post("/api/v1/users/logout", json={"refresh_token": tokens["refresh"]})
    assert again.status_code == 400
    assert again.json()["trace_id"] == "users-004"
