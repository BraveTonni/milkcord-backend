import os

from typing import Optional

from fastapi.routing import APIRouter

from sqlalchemy import text, select

from src.schemas.users import UserResponse
from src.schemas.response import ErrorResponse
from src.schemas.users import UserSettingsUpdate
from src.database.models.users import UserBase
from src.utils import crypto

from fastapi import Request, Depends, UploadFile, File
from fastapi.responses import FileResponse
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import (
    UserLogin,
    UserSignUp,
    UserResponse,
    UserBioUpdate,
    UserPublicResponse,
)
from src.schemas.response import ErrorResponse

from src.database.models.users import UserBase

from src.database.crud import users as users_crud
from src.database.crud import items as items_crud

from src.database.session import get_session

from src.utils import crypto

from src.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def me(
    access_token: str, session: AsyncSession = Depends(get_session)
) -> UserResponse | ErrorResponse:
    existing_user = await users_crud.get_user_by_access_token(session, access_token)
    if not existing_user:
        return ErrorResponse(error="Пользователь не найден")

    return UserResponse(user=existing_user)


@router.get("/avatar")
async def get_avatar(filename: str):
    """
    Возвращает файл аватара из статической директории.
    """
    file_path = os.path.join(settings.ROOT_DIR, filename.lstrip("/"))

    # Проверяем, существует ли файл
    if not os.path.exists(file_path) or not filename:
        default_path = os.path.join(settings.ROOT_DIR, "static/avatars/default.png")
        return FileResponse(default_path, media_type="image/jpeg")

    return FileResponse(file_path, media_type="image/jpeg")


@router.get("/cover")
async def get_cover(filename: str):
    """
    Возвращает файл обложки из статической директории.
    """
    file_path = os.path.join(settings.ROOT_DIR, filename.lstrip("/"))

    # Проверяем, существует ли файл
    if not os.path.exists(file_path) or not filename:
        default_path = os.path.join(settings.ROOT_DIR, "static/covers/default.png")
        return FileResponse(default_path, media_type="image/jpeg")

    return FileResponse(file_path, media_type="image/jpeg")


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

    # Проверяем тип файла
    if not file.content_type.startswith("image/"):
        return ErrorResponse(error="Можно загружать только изображения")

    # Создаём папку, если нет
    os.makedirs(settings.AVATAR_DIR, exist_ok=True)

    # Генерируем уникальное имя файла
    filename = f"{user.id}_{int(datetime.now().timestamp())}_{file.filename}"
    file_path = os.path.join(settings.AVATAR_DIR, filename)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Формируем URL для фронтенда
    avatar_url = f"/{file_path}"

    # Обновляем пользователя
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

    # Проверяем тип файла
    if not file.content_type.startswith("image/"):
        return ErrorResponse(error="Можно загружать только изображения")

    # Создаём папку, если нет
    os.makedirs(settings.COVER_DIR, exist_ok=True)

    # Генерируем уникальное имя файла
    filename = f"{user.id}_{int(datetime.now().timestamp())}_{file.filename}"
    file_path = os.path.join(settings.COVER_DIR, filename)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Формируем URL для фронтенда
    cover_url = f"/{file_path}"

    # Обновляем пользователя
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
