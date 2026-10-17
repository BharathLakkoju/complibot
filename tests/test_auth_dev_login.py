from complibot.config import Settings


def test_demo_dev_login_disabled_by_default() -> None:
    s = Settings(
        app_env="demo",
        dev_auth_secret="x" * 32,
        dev_login_enabled=None,
        aws_endpoint_url="",
        aws_access_key_id="",
        aws_secret_access_key="",
    )
    assert s.dev_login_enabled is False


def test_local_dev_login_enabled_by_default() -> None:
    s = Settings(app_env="local", dev_login_enabled=None)
    assert s.dev_login_enabled is True
