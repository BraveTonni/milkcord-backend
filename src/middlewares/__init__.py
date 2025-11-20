from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Укажите ваш фронтенд
        allow_credentials=True,
        allow_methods=["*"],  # или ограничьте методами, которые нужны (GET, POST и т.д.)
        allow_headers=["*"],  # или укажите конкретные заголовки
    )