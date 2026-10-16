import pytest

from src.core.config import Settings


def test_database_uri_is_built_from_fields():
    settings = Settings(
        DB_USER="user", DB_PASSWORD="pass", DB_HOST="db", DB_PORT=5432, DB_NAME="milkcord"
    )

    assert settings.DB_URI == "postgresql+asyncpg://user:pass@db:5432/milkcord"


def test_cors_origins_parsed_from_csv():
    settings = Settings(CORS_ORIGINS="http://a.test, http://b.test")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_static_path_rejects_escapes():
    settings = Settings()

    with pytest.raises(ValueError):
        settings.static_path("..", "..", "secret.txt")
