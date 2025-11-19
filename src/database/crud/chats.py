from sqlalchemy import select, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.chats import ChatBase

from src.database.crud import items as items_crud

from src.schemas.chats import ChatType


async def get_chat(session: AsyncSession, user_id: int) -> ChatBase | None:
    result = await session.execute(
        select(ChatBase).where(
            ChatBase.user_ids.op('@>')(cast([user_id], JSONB))
        )
    )
    return result.scalar_one_or_none()


async def get_chat_by_id(session: AsyncSession, chat_id: int) -> ChatBase | None:
    result = await session.execute(
        select(ChatBase).where(ChatBase.id == chat_id)
    )
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession, user_id: int) -> list[ChatBase]:
    result = await session.execute(
        select(ChatBase)
        .where(ChatBase.user_ids.contains([user_id]))
        .order_by(ChatBase.created_at.desc())
    )
    chats = result.scalars().all()
    if not chats:
        return []

    return chats


async def create_chat(
    session: AsyncSession, user_ids: list[int], chat_type: ChatType
) -> ChatBase:
    # Убираем дубли
    user_ids = list(set(user_ids))

    chat = ChatBase(user_ids=user_ids, chat_type=chat_type)

    session.add(chat)
    await items_crud.update_item(session, chat)

    return chat


async def get_or_create_chat(
    session: AsyncSession, user_ids: list[int], chat_type: ChatType
) -> ChatBase:
    """Ищет личный чат по user_ids (отсортированным), если нет — создаёт"""
    user_ids = sorted(set(user_ids))

    if len(user_ids) != 2:
        raise ValueError("get_or_create_chat только для двух пользователей")

    result = await session.execute(
        select(ChatBase).where(
            ChatBase.user_ids == user_ids, ChatBase.chat_type == chat_type
        )
    )
    chat = result.scalar_one_or_none()

    if chat:
        return chat

    return await create_chat(
        session=session, user_ids=user_ids, chat_type=ChatType.PRIVATE
    )
