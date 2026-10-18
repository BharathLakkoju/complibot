from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET = "dev-only-change-me"
MIN_DEV_AUTH_SECRET_LEN = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+asyncpg://complibot:complibot@localhost:5432/complibot"
    aws_endpoint_url: str | None = "http://localhost:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    s3_bucket: str = "complibot-demo"
    backup_s3_bucket: str = ""
    sqs_queue_url: str = "http://localhost:4566/000000000000/complibot-review"
    jwt_issuer: str = "http://localhost:8080/mock-issuer"
    jwt_audience: str = "complibot-local"
    dev_auth_secret: str = DEFAULT_DEV_SECRET
    dev_login_enabled: bool | None = None
    llm_provider: str = "mock"
    bedrock_model_id: str = "amazon.nova-micro-v1:0"
    bedrock_region: str | None = None
    llm_bedrock_fallback_mock: bool = False
    openrouter_api_key: str = ""
    openrouter_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    openrouter_fallback_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    openrouter_max_tokens: int = 8000
    openrouter_timeout_seconds: int = 120
    frameworks_path: str = "ai/frameworks"
    replay_max_events: int = 5000
    token_streaming_enabled: bool = True
    cors_origins: str = "http://localhost:3000"
    inline_worker: bool = True
    schema_auto_create: bool = True
    ws_max_message_bytes: int = 65536
    presign_ttl_seconds: int = 300

    @model_validator(mode="after")
    def validate_security(self) -> Self:
        if self.dev_login_enabled is None:
            self.dev_login_enabled = self.app_env == "local"

        if self.app_env != "local" and self.dev_auth_secret == DEFAULT_DEV_SECRET:
            raise ValueError("Set DEV_AUTH_SECRET to a long random value before non-local deploy")

        # The same secret verifies every JWT, so its length matters even with dev login off.
        if self.app_env != "local" and len(self.dev_auth_secret) < MIN_DEV_AUTH_SECRET_LEN:
            raise ValueError(
                f"DEV_AUTH_SECRET must be at least {MIN_DEV_AUTH_SECRET_LEN} characters "
                "outside local"
            )

        if self.bedrock_region is None:
            self.bedrock_region = self.aws_region

        if not 0 < self.presign_ttl_seconds <= 300:
            raise ValueError("PRESIGN_TTL_SECONDS must be between 1 and 300 (5 minutes)")

        if not 0 < self.ws_max_message_bytes <= 65536:
            raise ValueError("WS_MAX_MESSAGE_BYTES must be between 1 and 65536")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
