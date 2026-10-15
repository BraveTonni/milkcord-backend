import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.core.logging import setup_logging

from src.api import register_routers
from src.middlewares import register_middlewares

from src.database.base import init_db


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Таблицы создаются при старте приложения, а не в отдельной корутине
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

register_routers(app)
register_middlewares(app)

# Абсолютный путь: приложение запускается из любой рабочей директории
app.mount("/static", StaticFiles(directory=settings.ROOT_DIR / "static"), name="static")


def main() -> None:
    # Один процесс: ws_manager хранит соединения в памяти и не делится
    # между воркерами, поэтому workers>1 молча ломал бы уведомления
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.RELOAD,
    )


if __name__ == "__main__":
    main()
