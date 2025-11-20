from fastapi import Depends

from fastapi.responses import FileResponse

from fastapi.routing import APIRouter

from src.database.session import get_session
from src.schemas.stickers import StickerPacksResponse
from src.schemas.response import ErrorResponse

from src.database.crud import users as users_crud

from src.utils.helpers.stickers import StickerHelper
from src.utils.helpers.paths import PathHelper

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/stickers", tags=["Stickers"])


@router.get("/list")
async def get_all_stickers(
    access_token: str, session: AsyncSession = Depends(get_session)
) -> StickerPacksResponse | ErrorResponse:
    """Получение всех стикер паков"""
    user = await users_crud.get_user_by_access_token(session, access_token)

    if not user:
        return ErrorResponse(error="Пользователь не найден")

    return StickerPacksResponse(packs=StickerHelper.get_all())


@router.get("/{pack_slug}/{sticker_slug}")
async def get_sticker(
    pack_slug: str,
    sticker_slug: str,
) -> FileResponse:
    """
    Отдаёт файл стикера по slug пака и slug стикера.
    Пример: GET /stickers/korzhik/sit.png
    """
    sticker_path = (
        PathHelper.get_root() / "static" / "sticker_packs" / pack_slug / sticker_slug
    )

    # Безопасная проверка: не даём выйти за пределы папки стикеров
    try:
        sticker_path = sticker_path.resolve()
        stickers_root = (PathHelper.get_root() / "static" / "sticker_packs").resolve()

        if not sticker_path.is_relative_to(stickers_root):
            return ErrorResponse(error="Недопустимый путь к стикеру")

        if not sticker_path.exists():
            return ErrorResponse(error="Стикер не найден")

    except Exception:
        return ErrorResponse(error="Ошибка при проверке пути")

    # Определяем MIME-тип (поддержка png, webp, gif)
    mime_type = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(sticker_path.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(sticker_path),
        media_type=mime_type,
        filename=sticker_slug,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",  # Кешируем на год
            "Access-Control-Allow-Origin": "*",
        },
    )
