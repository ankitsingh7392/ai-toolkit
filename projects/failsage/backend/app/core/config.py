from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FailSage"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://qe:qe_secret@postgres:5432/failsage"
    database_url_sync: str = "postgresql+psycopg2://qe:qe_secret@postgres:5432/failsage"

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-4-6"
    ai_max_tokens: int = 4096
    ai_mock_mode: bool = False

    cluster_similarity_threshold: float = 0.72
    flaky_lookback_runs: int = 10
    flaky_fail_rate_threshold: float = 0.3

    slack_webhook_url: str = ""
    jira_url: str = ""
    jira_token: str = ""
    jira_project: str = "QE"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
