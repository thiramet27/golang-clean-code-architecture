from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRETS = {"", "1234567890", "change-me"}


class Settings(BaseSettings):
    """Same GOAPP_* variables as the Go template, so the existing .env file keeps working."""

    model_config = SettingsConfigDict(env_prefix="GOAPP_", env_file=(".env", ".env.dev"), extra="ignore")

    env: str = "development"  # development | test | production
    host: str = "127.0.0.1"
    port: int = 3000
    name: str = "PYTHON CLEAN API"
    version: str = "0.1.0"

    postgres_db_name: str = "postgres"
    postgres_db_user: str = "postgres"
    postgres_db_password: str = "golang-first-api"
    postgres_db_host: str = "localhost"
    postgres_db_port: int = 5432
    # Overrides the postgres_* fields when set (tests use sqlite+aiosqlite)
    database_url: str | None = None

    mongodb_db_atlas_uri: str | None = None
    mongodb_db_name: str = "python_cleancode_example"

    secret_key: str = "1234567890"
    jwt_access_expires: int = 86400  # seconds
    jwt_refresh_expires: int = 172800

    cors_origins: list[str] = ["http://localhost:5173"]

    workers: int = 1  # uvicorn worker processes (ignored in development, which uses --reload)

    # Fail fast instead of piling up requests when a database is slow or down
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_timeout: float = 5.0  # seconds to wait for a free connection
    db_connect_timeout: float = 3.0
    db_statement_timeout_ms: int = 5000
    mongodb_timeout_ms: int = 2000
    health_check_timeout: float = 2.0

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_db_user}:{self.postgres_db_password}"
            f"@{self.postgres_db_host}:{self.postgres_db_port}/{self.postgres_db_name}"
        )

    @property
    def issuer(self) -> str:
        return self.name.replace(" ", "-").lower()

    @model_validator(mode="after")
    def _refuse_weak_secret_in_production(self) -> "Settings":
        if self.env == "production" and (self.secret_key in INSECURE_SECRETS or len(self.secret_key) < 32):
            raise ValueError(
                "GOAPP_SECRET_KEY must be a random string of at least 32 characters in production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
