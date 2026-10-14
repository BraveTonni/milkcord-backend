from fastapi.routing import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_session
from src.database.crud import users as users_crud
from src.database.crud import chats as chats_crud
from src.schemas.chats import ChatResponse, ChatsResponse, ChatInfo, ChatType
from src.schemas.response import ErrorResponse
from src.schemas.users import UserPublic
from src.database.models.users import UserBase

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.get("/all")
async def get_all_chats(
    access_token: str, session: AsyncSession = Depends(get_session)
) -> ChatsResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    chat_models = await chats_crud.get_all(session, user.id)
    if not chat_models:
        return ChatsResponse(chats=[])

    all_user_ids = {uid for chat in chat_models for uid in chat.user_ids}
    users_result = await session.execute(
        select(UserBase).where(UserBase.id.in_(all_user_ids))
    )
    users_map = {u.id: UserPublic.model_validate(u) for u in users_result.scalars().all()}

    chat_infos = []
    for chat in chat_models:
        chat_users = [users_map[uid] for uid in chat.user_ids if uid in users_map]
        other_user = next((u for u in chat_users if u.id != user.id), None)
        chat_info = ChatInfo(
            id=chat.id,
            user=other_user,
            users=chat_users,
            chat_type=chat.chat_type,
            created_at=chat.created_at,
        )
        chat_infos.append(chat_info)

    return ChatsResponse(chats=chat_infos)


@router.get("/chat/{user_id}")
async def get_or_create_chat(
    user_id: int, access_token: str, session: AsyncSession = Depends(get_session)
) -> ChatResponse | ErrorResponse:
    # Проверяем текущего пользователя
    current_user = await users_crud.get_user_by_access_token(session, access_token)
    if not current_user:
        return ErrorResponse(error="Пользователь не найден")

    # Проверяем, существует ли второй пользователь
    target_user = await users_crud.get_user_by_id(session, user_id)
    if not target_user:
        return ErrorResponse(error="Целевой пользователь не найден")

    # Получаем или создаём приватный чат
    chat = await chats_crud.get_or_create_chat(
        session, [current_user.id, user_id], ChatType.PRIVATE
    )

    # Загружаем пользователей чата
    users_result = await session.execute(
        select(UserBase).where(UserBase.id.in_(chat.user_ids))
    )
    users_map = {u.id: UserPublic.model_validate(u) for u in users_result.scalars().all()}

    chat_users = [users_map[uid] for uid in chat.user_ids if uid in users_map]
    other_user = next((u for u in chat_users if u.id != current_user.id), None)

    chat_info = ChatInfo(
        id=chat.id,
        user=other_user,
        users=chat_users,
        chat_type=chat.chat_type,
        created_at=chat.created_at,
    )

    return ChatResponse(chat=chat_info)
