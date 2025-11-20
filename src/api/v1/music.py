from fastapi import Depends

from fastapi.routing import APIRouter

from src.database.session import get_session
from src.schemas.music import MusicResponse
from src.schemas.response import ErrorResponse

from src.database.crud import users as users_crud

from src.utils.helpers.music import MusicHelper

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/music", tags=["Music"])


@router.get("/list")
async def get_all_music(
    access_token: str, session: AsyncSession = Depends(get_session)
) -> MusicResponse | ErrorResponse:
    """Получение всех стикер паков"""
    user = await users_crud.get_user_by_access_token(session, access_token)

    if not user:
        return ErrorResponse(error="Пользователь не найден")

    return MusicResponse(tracks=MusicHelper.get_all())
