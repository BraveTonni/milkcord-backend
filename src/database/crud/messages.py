from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.schemas.messages import MessageKind

from src.database.models.messages import ChatMessages

from src.utils.time_formatter import TimeFormatter

from src.database.crud import items as items_crud

from src.database.models.messages import ChatMessageFile
from src.utils.helpers.files import FilesHelper


# === СОЗДАТЬ СООБЩЕНИЕ ===
async def create_text_message(
    session: AsyncSession,
    chat_id: int,
    from_user_id: int,
    to_user_id: int,
    content: str,
) -> ChatMessages:
    message = ChatMessages(
        chat_id=chat_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        content=content,
        created_at=TimeFormatter.get_current_unix(),
        kind=MessageKind.TEXT,
    )
    session.add(message)
    await items_crud.update_item(session, message)
    return message


async def create_file_message(
    session: AsyncSession,
    chat_id: int,
    from_user_id: int,
    to_user_id: int,
    files: list,
) -> ChatMessages:
    # создаём "пустое" сообщение FILE типа
    message = ChatMessages(
        chat_id=chat_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        kind=MessageKind.FILE,
        created_at=TimeFormatter.get_current_unix(),
    )

    session.add(message)
    await session.flush()  # получаем message.id, но без commit

    # сохраняем файлы
    for upload_file in files:
        file_name = await FilesHelper.save_upload_file(upload_file, "messages")

        session.add(
            ChatMessageFile(
                message_id=message.id,
                file_name=file_name,
                orig_name=upload_file.filename,
                file_size=upload_file.size or 0,
            )
        )

    # как и в других сообщениях
    await items_crud.update_item(session, message)

    return message


async def create_sticker_message(
    session: AsyncSession,
    chat_id: int,
    from_user_id: int,
    to_user_id: int,
    pack_slug: str,
    sticker_slug: str,
) -> ChatMessages:
    message = ChatMessages(
        chat_id=chat_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        pack_slug=pack_slug,
        sticker_slug=sticker_slug,
        created_at=TimeFormatter.get_current_unix(),
        kind=MessageKind.STICKER,
    )
    session.add(message)
    await items_crud.update_item(session, message)

    return message


# === ПОЛУЧИТЬ СООБЩЕНИЯ ЧАТА ===
async def get_chat_messages(
    session: AsyncSession,
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[ChatMessages]:
    result = await session.execute(
        select(ChatMessages)
        .options(selectinload(ChatMessages.files))
        .where(ChatMessages.chat_id == chat_id)
        .where(ChatMessages.is_deleted == False)  # noqa
        .order_by(ChatMessages.id.desc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.unique().scalars().all()

    # Важно: переворачиваем, чтобы на фронте было от старого → к новому
    return list(reversed(messages))


# === ПОЛУЧИТЬ ПОСЛЕДНЕЕ СООБЩЕНИЕ ===
async def get_last_message(
    session: AsyncSession,
    chat_id: int,
) -> Optional[ChatMessages]:
    result = await session.execute(
        select(ChatMessages)
        .where(ChatMessages.chat_id == chat_id)
        .order_by(ChatMessages.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# === УДАЛИТЬ СООБЩЕНИЕ ===
async def delete_message(
    session: AsyncSession,
    message_id: int,
    user_id: int,
) -> bool:
    result = await session.execute(
        delete(ChatMessages)
        .where(ChatMessages.id == message_id, ChatMessages.from_user_id == user_id)
        .returning(ChatMessages.id)
    )
    deleted = result.scalar_one_or_none()
    if deleted:
        await session.commit()
        return True
    return False
