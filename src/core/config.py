import os

from pathlib import Path

from typing import ClassVar

from pydantic_settings import BaseSettings

from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class __Settings(BaseSettings):
    APP_NAME: ClassVar[str] = "MilkCord - API"

    # Database configuration
    DB_USER: ClassVar[str] = os.getenv("DB_USER")
    DB_HOST: ClassVar[str] = os.getenv("DB_HOST")
    DB_NAME: ClassVar[str] = os.getenv("DB_NAME")
    DB_PORT: ClassVar[str] = os.getenv("DB_PORT")
    DB_PASSWORD: ClassVar[str] = os.getenv("DB_PASSWORD")

    DB_URI: ClassVar[str] = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    AVATAR_DIR: ClassVar[str] = "static/avatars"
    COVER_DIR: ClassVar[str] = "static/covers"
    ROOT_DIR: ClassVar[str] = Path(__file__).resolve().parent.parent.parent


settings = __Settings()
