from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Settings(BaseSettings):
    """Application settings.

    Values are read from the environment (or a .env file in the project root);
    every field has a safe default so the app starts without a .env in dev.
    """

    model_config = SettingsConfigDict(extra="ignore")

    APP_NAME: str = "MilkCord - API"

    # Database
    DB_USER: str = "milkcord"
    DB_NAME: str = "milkcord"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_PASSWORD: str = "change-me"

    SQL_ECHO: bool = False

    # Server
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 7000
    RELOAD: bool = False

    # CORS: comma-separated list of allowed frontend origins
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # Uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    AVATAR_DIR: str = "static/avatars"
    COVER_DIR: str = "static/covers"
    ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def DB_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    def static_path(self, *parts: str) -> Path:
        """Absolute path inside the project's static directory."""
        path = (self.ROOT_DIR / "static" / Path(*parts)).resolve()
        if not path.is_relative_to((self.ROOT_DIR / "static").resolve()):
            raise ValueError(f"Path escapes the static directory: {parts}")
        return path


settings = Settings()
