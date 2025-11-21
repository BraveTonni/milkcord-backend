import uvicorn
import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.core.config import settings

from src.api import register_routers
from src.middlewares import register_middlewares

from src.database.base import init_db


app = FastAPI(
    title=settings.APP_NAME
)

register_routers(app)
register_middlewares(app)

app.mount("/static", StaticFiles(directory="static"), name="static")


async def main():
    await init_db()

    uvicorn.run("main:app", reload=True, workers=4, port=7000)


if __name__ == "__main__":
    asyncio.run(
        main()
    )
