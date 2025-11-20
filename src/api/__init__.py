from fastapi import FastAPI
from fastapi.routing import APIRouter

from .v1 import register_v1_routers


def register_routers(app: FastAPI) -> None:
    """Register all routers"""
    api_router = APIRouter(
        prefix="/api"
    )

    register_v1_routers(api_router)

    app.include_router(api_router)
