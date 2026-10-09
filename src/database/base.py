from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings

from .models.base import Base


# Создаём движок БД
engine = create_async_engine(
    url=settings.DB_URI,
    echo=settings.SQL_ECHO,
    pool_size=10,
    max_overflow=5
)


async def init_db() -> None:
    """Базовый метод для инициализации базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
