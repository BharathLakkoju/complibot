import pytest
from complibot.main import app
from complibot.routers import auth as auth_router
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_router, "_login_attempts", {})


async def test_register_login_and_wrong_password() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post(
            "/v1/auth/register",
            json={"email": "user@example.com", "password": "securepass1", "name": "User"},
        )
        assert reg.status_code == 200
        assert reg.json()["accessToken"]
        dup = await client.post(
            "/v1/auth/register",
            json={"email": "user@example.com", "password": "securepass1"},
        )
        assert dup.status_code == 409
        bad = await client.post(
            "/v1/auth/login",
            json={"email": "user@example.com", "password": "wrongpassword"},
        )
        assert bad.status_code == 401
        assert bad.json()["detail"] == "Invalid credentials"
        ok = await client.post(
            "/v1/auth/login",
            json={"email": "user@example.com", "password": "securepass1"},
        )
        assert ok.status_code == 200
        me = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {ok.json()['accessToken']}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "user@example.com"


async def test_dev_login_still_works_for_passwordless_users() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/v1/auth/dev-login",
            json={"email": "legacy@complibot.local", "name": "Legacy"},
        )
        assert res.status_code == 200
