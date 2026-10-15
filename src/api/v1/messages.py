import html
import logging

from fastapi.routing import APIRouter

from fastapi import Depends, Form, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete

from src.database.session import get_session

from src.database.models.messages import ChatMessageFile, ChatMessages

from src.database.crud import users as users_crud
from src.database.crud import chats as chats_crud
from src.database.crud import messages as messages_crud

from src.schemas.chats import ChatType
from src.schemas.messages import MessageResponse, MessageInfo, MessageFile
from src.schemas.users import UserPublic

from src.schemas.response import ErrorResponse

from src.schemas.messages import MessageCreate, MessageSticker, MessageKind

from src.core.ws_manager import ws_manager
from src.core.config import settings
from src.utils.helpers.files import FilesHelper
from src.utils.helpers.paths import PathHelper

router = APIRouter(prefix="/messages", tags=["Messages"])

logger = logging.getLogger(__name__)


@router.post("/send")
async def send_message(
    access_token: str, data: MessageCreate, session: AsyncSession = Depends(get_session)
) -> MessageResponse | ErrorResponse:
    data.content = html.escape(data.content).strip()

    # Проверяем токен
    user = await users_crud.get_user_by_access_token(session, access_token)

    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Получаем либо создаём чат
    chat = await chats_crud.get_or_create_chat(
        session, [user.id, data.to_user_id], ChatType.PRIVATE
    )

    # Загружаем пользователей
    from_user = await users_crud.get_user_by_id(session, user.id)
    to_user = await users_crud.get_user_by_id(session, data.to_user_id)

    # Отправляем сообщение
    message = await messages_crud.create_text_message(
        session,
        chat_id=chat.id,
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        content=data.content,
    )

    # Вебсокет
    to_user_ws = ws_manager.active_connections.get(to_user.id)
    from_user_ws = ws_manager.active_connections.get(from_user.id)

    if to_user_ws:
        await to_user_ws.websocket.send_json(
            {
                "event": "message",
                "payload": {
                    "id": message.id,
                    "content": message.content,
                    "from": {"id": from_user.id, "username": from_user.username},
                    "self": False,
                },
            }
        )

    if from_user_ws:
        await from_user_ws.websocket.send_json(
            {
                "event": "message",
                "payload": {
                    "id": message.id,
                    "content": message.content,
                    "from": {"id": from_user.id, "username": from_user.username},
                    "self": True,
                },
            }
        )

    message_info = MessageInfo(
        id=message.id,
        chat_id=message.chat_id,
        content=message.content,
        from_user=UserPublic.model_validate(from_user),
        to_user=UserPublic.model_validate(to_user),
        created_at=message.created_at,
        kind=MessageKind.TEXT,
    )

    return MessageResponse(message=message_info)


@router.post("/send/sticker")
async def send_sticker(
    access_token: str,
    data: MessageSticker,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse | ErrorResponse:
    # Проверяем токен
    user = await users_crud.get_user_by_access_token(session, access_token)

    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Получаем либо создаём чат
    chat = await chats_crud.get_or_create_chat(
        session, [user.id, data.to_user_id], ChatType.PRIVATE
    )

    # Загружаем пользователей
    from_user = await users_crud.get_user_by_id(session, user.id)
    to_user = await users_crud.get_user_by_id(session, data.to_user_id)

    # Отправляем сообщение
    message = await messages_crud.create_sticker_message(
        session,
        chat_id=chat.id,
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        pack_slug=data.pack_slug,
        sticker_slug=data.sticker_slug,
    )

    # Вебсокет
    to_user_ws = ws_manager.active_connections.get(to_user.id)
    from_user_ws = ws_manager.active_connections.get(from_user.id)

    if to_user_ws:
        await to_user_ws.websocket.send_json(
            {
                "event": "message:sticker",
                "payload": {
                    "id": message.id,
                    "pack": data.pack_slug,
                    "sticker": data.sticker_slug,
                    "from": {"id": from_user.id, "username": from_user.username},
                    "self": False,
                },
            }
        )

    if from_user_ws:
        await from_user_ws.websocket.send_json(
            {
                "event": "message:sticker",
                "payload": {
                    "id": message.id,
                    "pack": data.pack_slug,
                    "sticker": data.sticker_slug,
                    "from": {"id": from_user.id, "username": from_user.username},
                    "self": True,
                },
            }
        )

    message_info = MessageInfo(
        id=message.id,
        chat_id=message.chat_id,
        pack_slug=data.pack_slug,
        sticker_slug=data.sticker_slug,
        from_user=UserPublic.model_validate(from_user),
        to_user=UserPublic.model_validate(to_user),
        created_at=message.created_at,
        kind=MessageKind.STICKER,
    )

    return MessageResponse(message=message_info)


@router.get("/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int, access_token: str, session: AsyncSession = Depends(get_session)
) -> list[MessageInfo] | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    chat = await chats_crud.get_chat_by_id(session, chat_id)
    if not chat or user.id not in chat.user_ids:
        return ErrorResponse(error="Чат не найден или доступ запрещён")

    messages = await messages_crud.get_chat_messages(session, chat_id)

    user_ids = {msg.from_user_id for msg in messages} | {
        msg.to_user_id for msg in messages
    }
    users_result = await session.execute(
        select(users_crud.UserBase).where(users_crud.UserBase.id.in_(user_ids))
    )
    users_map = {
        u.id: UserPublic.model_validate(u) for u in users_result.scalars().all()
    }

    message_infos = [
        MessageInfo(
            id=msg.id,
            chat_id=msg.chat_id,
            kind=msg.kind,
            content=msg.content or None,
            pack_slug=msg.pack_slug if hasattr(msg, "pack_slug") else None,
            sticker_slug=msg.sticker_slug if hasattr(msg, "sticker_slug") else None,
            from_user=users_map[msg.from_user_id],
            to_user=users_map[msg.to_user_id],
            created_at=msg.created_at,
            files=[
                MessageFile(
                    id=f.id,
                    file_name=f.file_name,
                    orig_name=f.orig_name,
                    file_size=f.file_size,
                    created_at=f.created_at,
                )
                for f in msg.files
            ]
            if msg.files
            else None,
        )
        for msg in messages
    ]

    return message_infos


@router.post("/send/file")
async def send_file_message(
    access_token: str = Form(...),
    to_user_id: int = Form(...),
    files: list[UploadFile] = File(default=[]),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse | ErrorResponse:
    # Проверка
    if not files:
        return ErrorResponse(error="Файлы отсутствуют")

    if any(f.size and f.size > settings.MAX_UPLOAD_SIZE for f in files):
        return ErrorResponse(error="Файл слишком большой")

    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Чат
    chat = await chats_crud.get_or_create_chat(
        session, [user.id, to_user_id], ChatType.PRIVATE
    )

    from_user = await users_crud.get_user_by_id(session, user.id)
    to_user = await users_crud.get_user_by_id(session, to_user_id)

    # Создание сообщения + файлов
    message = await messages_crud.create_file_message(
        session=session,
        chat_id=chat.id,
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        files=files,
    )

    await session.commit()
    await session.refresh(message)

    # Подготовка файлов для ответа
    file_infos = [
        MessageFile(
            id=f.id,
            file_name=f.file_name,
            orig_name=f.orig_name,
            file_size=f.file_size,
            created_at=f.created_at,
        )
        for f in message.files
    ]

    # WebSocket
    payload = {
        "event": "message:file",
        "payload": {
            "id": message.id,
            "from": {"id": from_user.id, "username": from_user.username},
            "files": [
                {
                    "file_name": f.file_name,
                    "orig_name": f.orig_name,
                    "file_size": f.file_size,
                }
                for f in message.files
            ],
        },
    }

    to_ws = ws_manager.active_connections.get(to_user.id)
    if to_ws:
        payload["payload"]["self"] = False
        await to_ws.websocket.send_json(payload)

    from_ws = ws_manager.active_connections.get(from_user.id)
    if from_ws:
        payload["payload"]["self"] = True
        await from_ws.websocket.send_json(payload)

    # Респонс
    message_info = MessageInfo(
        id=message.id,
        chat_id=message.chat_id,
        kind=MessageKind.FILE,
        from_user=UserPublic.model_validate(from_user),
        to_user=UserPublic.model_validate(to_user),
        created_at=message.created_at,
        files=file_infos,
    )

    return MessageResponse(message=message_info)


@router.get("/get/{file_name}", response_model=None)
async def get_message_file(
    file_name: str, session: AsyncSession = Depends(get_session)
) -> FileResponse | ErrorResponse:
    result = await session.execute(
        select(ChatMessageFile).where(ChatMessageFile.file_name == file_name)
    )
    msg_file = result.scalar_one_or_none()

    if not msg_file:
        return ErrorResponse(error="Файл не найден")

    file_path = PathHelper.get_root() / "static" / "files" / "messages" / file_name
    resolved_path = file_path.resolve()
    allowed_root = (PathHelper.get_root() / "static" / "files").resolve()

    if not resolved_path.is_relative_to(allowed_root):
        return ErrorResponse(error="Недопустимый путь")

    if not resolved_path.exists():
        return ErrorResponse(error="Файл отсутствует на диске")

    return FileResponse(
        path=str(resolved_path),
        filename=msg_file.orig_name,
        media_type=FilesHelper.media_type_for(resolved_path),
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@router.post("/edit")
async def edit_message(
    access_token: str = Form(...),
    message_id: int = Form(...),
    new_text: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    new_text = html.escape(new_text).strip()

    # Авторизация
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Загружаем сообщение
    result = await session.execute(
        select(ChatMessages).where(ChatMessages.id == message_id)
    )
    msg = result.unique().scalar_one_or_none()

    if not msg:
        return ErrorResponse(error="Сообщение не найдено")

    # Проверка прав
    if msg.from_user_id != user.id:
        return ErrorResponse(error="Вы не можете редактировать это сообщение")

    # Проверяем что сообщение текстовое
    if msg.kind != MessageKind.TEXT:
        return ErrorResponse(error="Редактировать можно только текстовые сообщения")

    # Обновляем
    msg.content = new_text
    await session.commit()
    await session.refresh(msg)

    # WebSocket уведомления
    payload = {
        "event": "message:edit",
        "payload": {
            "id": msg.id,
            "new_text": msg.content,
        },
    }

    # Получатели
    to_ws = ws_manager.active_connections.get(msg.to_user_id)
    if to_ws:
        payload["payload"]["self"] = False
        await to_ws.websocket.send_json(payload)

    from_ws = ws_manager.active_connections.get(msg.from_user_id)
    if from_ws:
        payload["payload"]["self"] = True
        await from_ws.websocket.send_json(payload)

    return {"success": True}


@router.post("/delete")
async def delete_message(
    access_token: str = Form(...),
    message_id: int = Form(...),
    session: AsyncSession = Depends(get_session),
):
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Загружаем сообщение
    result = await session.execute(
        select(ChatMessages)
        .options(selectinload(ChatMessages.files))
        .where(ChatMessages.id == message_id)
    )

    msg = result.unique().scalar_one_or_none()

    if not msg:
        return ErrorResponse(error="Сообщение не найдено")

    if msg.from_user_id != user.id:
        return ErrorResponse(error="Вы не можете удалить это сообщение")

    # Удаляем файлы, если есть
    if msg.kind == MessageKind.FILE:
        for f in msg.files:
            file_path = (
                PathHelper.get_root() / "static" / "files" / "messages" / f.file_name
            )
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    logger.warning(
                        "не удалось удалить файл сообщения %s", file_path, exc_info=True
                    )

        await session.execute(
            delete(ChatMessageFile).where(ChatMessageFile.message_id == msg.id)
        )

    # Помечаем удалённым
    msg.is_deleted = True
    await session.commit()

    # WebSocket уведомление
    payload = {
        "event": "message:delete",
        "payload": {
            "id": msg.id,
        },
    }


    # recipient
    to_ws = ws_manager.active_connections.get(msg.to_user_id)
    if to_ws:
        payload["payload"]["self"] = False
        await to_ws.websocket.send_json(payload)

    # sender
    from_ws = ws_manager.active_connections.get(msg.from_user_id)
    if from_ws:
        payload["payload"]["self"] = True
        await from_ws.websocket.send_json(payload)

    return {"success": True}
