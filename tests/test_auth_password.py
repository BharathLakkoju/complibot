import jwt
import pytest
from complibot.config import get_settings
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
        assert dup.json()["detail"] == "Registration failed"
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


async def test_register_jwt_matches_dev_login_claim_shape() -> None:
    settings = get_settings()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post(
            "/v1/auth/register",
            json={"email": "jwt-shape@example.com", "password": "securepass1"},
        )
        dev = await client.post(
            "/v1/auth/dev-login",
            json={"email": "jwt-dev@complibot.local", "name": "Dev"},
        )
    reg_claims = jwt.decode(
        reg.json()["accessToken"],
        settings.dev_auth_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    dev_claims = jwt.decode(
        dev.json()["accessToken"],
        settings.dev_auth_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    for key in ("sub", "tenant_id", "email", "name", "iss", "aud", "exp", "iat"):
        assert key in reg_claims
        assert key in dev_claims


async def test_login_rate_limited_per_ip() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        codes = [
            (
                await client.post(
                    "/v1/auth/login",
                    json={"email": "nobody@example.com", "password": "wrongpass1"},
                )
            ).status_code
            for _ in range(auth_router._LOGIN_MAX_PER_WINDOW + 1)
        ]
    assert codes[:-1] == [401] * auth_router._LOGIN_MAX_PER_WINDOW
    assert codes[-1] == 429


async def test_dev_login_still_works_for_passwordless_users() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/v1/auth/dev-login",
            json={"email": "legacy@complibot.local", "name": "Legacy"},
        )
        assert res.status_code == 200
