from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import Request, Depends, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database.crud import users as users_crud
from src.database.crud import items as items_crud
from src.database.models.users import UserBase
from src.database.session import get_session
from src.schemas.response import ErrorResponse
from src.schemas.users import (
    UserLogin,
    UserSignUp,
    UserResponse,
    UserBioUpdate,
    UserPublicResponse,
    UserSettingsUpdate,
)
from src.utils import crypto

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _serve_image(filename: str | None, subdir: str, default_name: str) -> FileResponse:
    """Отдаёт файл из static/<subdir> либо дефолтную картинку.

    Запрашиваемый путь резолвится и обязан остаться внутри поддиректории,
    иначе отдаётся картинка по умолчанию (защита от path traversal).
    """
    root = (settings.ROOT_DIR / "static" / subdir).resolve()

    if filename:
        candidate = (settings.ROOT_DIR / filename.lstrip("/")).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            media_type = IMAGE_MEDIA_TYPES.get(
                candidate.suffix.lower(), "application/octet-stream"
            )
            return FileResponse(candidate, media_type=media_type)

    return FileResponse(root / default_name, media_type="image/png")


async def _save_profile_image(
    file: UploadFile, user_id: int, subdir: str
) -> str | ErrorResponse:
    """Валидирует и сохраняет аватар/обложку, возвращает имя файла или ошибку."""
    if not file.content_type or not file.content_type.startswith("image/"):
        return ErrorResponse(error="Можно загружать только изображения")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return ErrorResponse(error="Недопустимый формат изображения")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        return ErrorResponse(error="Файл слишком большой")

    directory = settings.static_path(subdir)
    directory.mkdir(parents=True, exist_ok=True)

    # Имя формируем сами: имя файла от клиента не участвует в пути
    name = f"{user_id}_{int(datetime.now().timestamp())}_{uuid4().hex}{extension}"
    (directory / name).write_bytes(content)

    return name


@router.get("/me")
async def me(
    access_token: str, session: AsyncSession = Depends(get_session)
) -> UserResponse | ErrorResponse:
    existing_user = await users_crud.get_user_by_access_token(session, access_token)
    if not existing_user:
        return ErrorResponse(error="Пользователь не найден")

    return UserResponse(user=existing_user)


@router.get("/avatar")
async def get_avatar(filename: str | None = None) -> FileResponse:
    """
    Возвращает файл аватара из статической директории.
    """
    return _serve_image(filename, "avatars", "default.png")


@router.get("/cover")
async def get_cover(filename: str | None = None) -> FileResponse:
    """
    Возвращает файл обложки из статической директории.
    """
    return _serve_image(filename, "covers", "default.png")


@router.get("/profile/{identifier}")
async def profile(identifier: str, session: AsyncSession = Depends(get_session)):
    if identifier.isdigit():
        user = await users_crud.get_user_by_id(session, int(identifier))
    else:
        user = await users_crud.get_user_by_username(session, identifier)

    if not user:
        return ErrorResponse(error="Пользователь не найден")

    return UserPublicResponse(user=user)


@router.post("/login")
async def login(
    request: Request, user: UserLogin, session: AsyncSession = Depends(get_session)
) -> UserResponse | ErrorResponse:
    existing_user: Optional[UserBase] = await users_crud.get_user_by_username(
        session, user.username
    )

    if not existing_user:
        return ErrorResponse(error="Пользователь не найден")

    # Проверяем пароль
    input_password = crypto.hash_password(user.password)

    if input_password != existing_user.password:
        return ErrorResponse(error="Неправильный пароль")

    return UserResponse(user=existing_user)


@router.post("/signup")
async def signup(
    request: Request, user: UserSignUp, session: AsyncSession = Depends(get_session)
) -> UserResponse | ErrorResponse:
    existing_user: Optional[UserBase] = await users_crud.get_user_by_username(
        session, user.username
    )

    if existing_user:
        return ErrorResponse(error="Данный пользователь уже зарегистрирован")

    # Шифруем пароль в модели
    user.password = crypto.hash_password(user.password)

    existing_user = await users_crud.create_user(session, user)

    await items_crud.update_item(session, existing_user)

    print(existing_user)

    return UserResponse(user=existing_user)


@router.patch("/me/bio")
async def update_bio(
    access_token: str, data: UserBioUpdate, session: AsyncSession = Depends(get_session)
) -> UserResponse | ErrorResponse:
    # Проверяем токен
    existing_user = await users_crud.get_user_by_access_token(session, access_token)

    if not existing_user:
        return ErrorResponse(error="Пользователь не найден")

    # Обновляем через CRUD
    updated_user = await users_crud.update_user_bio(session, existing_user, data.bio)

    await items_crud.update_item(session, existing_user)

    return UserResponse(user=updated_user)


@router.post("/avatar")
async def upload_avatar(
    access_token: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> UserResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    name = await _save_profile_image(file, user.id, "avatars")
    if isinstance(name, ErrorResponse):
        return name

    avatar_url = f"/static/avatars/{name}"

    updated_user = await users_crud.update_user_avatar(session, user, avatar_url)

    return UserResponse(user=updated_user)


@router.post("/cover")
async def upload_cover(
    access_token: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> UserResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    name = await _save_profile_image(file, user.id, "covers")
    if isinstance(name, ErrorResponse):
        return name

    cover_url = f"/static/covers/{name}"

    updated_user = await users_crud.update_user_cover(session, user, cover_url)

    return UserResponse(user=updated_user)


@router.post("/settings/update")
async def update_user_settings(
    access_token: str,
    payload: UserSettingsUpdate,
    session: AsyncSession = Depends(get_session),
):
    # Проверяем пользователя
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Проверка занятости username
    existing_username = await users_crud.get_user_by_username(session, payload.username)
    if existing_username and existing_username.id != user.id:
        return ErrorResponse(error="Имя уже занято")

    # Проверка занятости email
    existing_email = await users_crud.get_user_by_email(session, payload.email)
    if existing_email and existing_email.id != user.id:
        return ErrorResponse(error="Email уже используется")

    # Обновляем поля
    user.username = payload.username
    user.email = payload.email

    if payload.password:
        user.password = crypto.hash_password(payload.password)

    await session.commit()
    await session.refresh(user)

    return UserResponse(user=user)
