from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_session

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health(session: AsyncSession = Depends(get_session)) -> JSONResponse:
    """Readiness-эндпоинт: приложение живо и база отвечает.

    200 — всё в порядке, 503 — база недоступна (для алертов и балансировщика).
    """
    database = "ok"
    status_code = 200

    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        database = "unavailable"
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if status_code == 200 else "degraded", "database": database},
    )
