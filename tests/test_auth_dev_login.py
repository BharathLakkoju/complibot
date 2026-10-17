import pytest
from complibot.config import DEFAULT_DEV_SECRET, Settings, get_settings
from complibot.main import app
from complibot.routers import auth as auth_router
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

DEMO_AWS = {"aws_endpoint_url": "", "aws_access_key_id": "", "aws_secret_access_key": ""}


def test_demo_dev_login_disabled_by_default() -> None:
    s = Settings(app_env="demo", dev_auth_secret="x" * 32, dev_login_enabled=None, **DEMO_AWS)
    assert s.dev_login_enabled is False


def test_local_dev_login_enabled_by_default() -> None:
    s = Settings(app_env="local", dev_login_enabled=None)
    assert s.dev_login_enabled is True


@pytest.mark.parametrize("secret", [DEFAULT_DEV_SECRET, "short-secret"])
@pytest.mark.parametrize("dev_login", [True, False])
def test_demo_rejects_default_or_short_secret(secret: str, dev_login: bool) -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="demo", dev_auth_secret=secret, dev_login_enabled=dev_login, **DEMO_AWS)


@pytest.mark.parametrize("ttl", [0, -1, 301])
def test_presign_ttl_bounds(ttl: int) -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="local", presign_ttl_seconds=ttl)


def test_demo_rejects_openrouter() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="demo", dev_auth_secret="x" * 32, llm_provider="openrouter", **DEMO_AWS)


async def test_dev_login_endpoint_403_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "dev_login_enabled", False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/v1/auth/dev-login", json={"email": "x@y.z", "name": "X"})
    assert res.status_code == 403


async def test_dev_login_rate_limited_per_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_router, "_login_attempts", {})
    monkeypatch.setattr(get_settings(), "dev_login_enabled", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        codes = [
            (
                await client.post(
                    "/v1/auth/dev-login", json={"email": "rl@complibot.local", "name": "RL"}
                )
            ).status_code
            for _ in range(auth_router._LOGIN_MAX_PER_WINDOW + 1)
        ]
    assert codes[:-1] == [200] * auth_router._LOGIN_MAX_PER_WINDOW
    assert codes[-1] == 429


def test_rate_limit_prunes_stale_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts: dict[str, list[float]] = {"203.0.113.9": [0.0]}
    monkeypatch.setattr(auth_router, "_login_attempts", attempts)
    monkeypatch.setattr(auth_router.time, "monotonic", lambda: 1_000.0)
    auth_router._rate_limit_client("198.51.100.1")
    assert set(attempts) == {"198.51.100.1"}
