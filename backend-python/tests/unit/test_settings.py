import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_production_refuses_default_secret() -> None:
    with pytest.raises(ValidationError, match="GOAPP_SECRET_KEY"):
        Settings(_env_file=None, env="production", secret_key="1234567890")  # type: ignore[call-arg]


def test_issuer_replaces_spaces() -> None:
    # Go discarded the strings.Replace result, so the issuer kept its spaces
    assert Settings(_env_file=None, name="GOLANG FIRST API APP").issuer == "golang-first-api-app"  # type: ignore[call-arg]


def test_database_url_override() -> None:
    assert Settings(_env_file=None).sqlalchemy_url.startswith("postgresql+asyncpg://")  # type: ignore[call-arg]
    assert (
        Settings(_env_file=None, database_url="sqlite+aiosqlite://").sqlalchemy_url == "sqlite+aiosqlite://"
    )  # type: ignore[call-arg]
