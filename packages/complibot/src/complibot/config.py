from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+asyncpg://complibot:complibot@localhost:5432/complibot"
    aws_endpoint_url: str | None = "http://localhost:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    s3_bucket: str = "complibot-demo"
    sqs_queue_url: str = "http://localhost:4566/000000000000/complibot-review"
    jwt_issuer: str = "http://localhost:8080/mock-issuer"
    jwt_audience: str = "complibot-local"
    dev_auth_secret: str = "dev-only-change-me"
    llm_provider: str = "mock"
    frameworks_path: str = "ai/frameworks"
    replay_max_events: int = 5000
    token_streaming_enabled: bool = True
    cors_origins: str = "http://localhost:3000"
    inline_worker: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
