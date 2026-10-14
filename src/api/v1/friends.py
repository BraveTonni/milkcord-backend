from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_session
from src.database.crud import friends as friends_crud, users as users_crud
from src.schemas.response import ErrorResponse
from src.schemas.friends import FriendListResponse, FriendActionResponse

router = APIRouter(prefix="/friends", tags=["Friends"])


# === Отправить запрос в друзья ===
@router.post("/request/{friend_username}")
async def send_friend_request(
    access_token: str,
    friend_username: str,
    session: AsyncSession = Depends(get_session),
) -> FriendActionResponse | ErrorResponse:
    """Отправить запрос в друзья"""
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    friend = await users_crud.get_user_by_username(session, friend_username)
    if not friend:
        return ErrorResponse(error="Пользователь для добавления не найден")

    try:
        request_obj = await friends_crud.send_friend_request(
            session, user.id, friend.id
        )
    except ValueError as e:
        return ErrorResponse(error=str(e))

    return FriendActionResponse(
        message=f"Запрос в друзья отправлен пользователю {friend.username}",
        friend_id=friend.id,
        status=request_obj.status.name,
    )


# === Принять запрос ===
@router.post("/accept/{friend_username}")
async def accept_friend_request(
    access_token: str,
    friend_username: str,
    session: AsyncSession = Depends(get_session),
) -> FriendActionResponse | ErrorResponse:
    """Принять запрос в друзья"""
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    friend = await users_crud.get_user_by_username(session, friend_username)
    if not friend:
        return ErrorResponse(error="Пользователь не найден")

    result = await friends_crud.accept_friend_request(session, user.id, friend.id)
    if not result:
        return ErrorResponse(error="Запрос не найден")

    return FriendActionResponse(
        message=f"Вы теперь друзья с {friend.username}",
        friend_id=friend.id,
        status=result.status.name,
    )


# === Удалить друга / отменить запрос ===
@router.delete("/remove/{friend_username}")
async def remove_friend(
    access_token: str,
    friend_username: str,
    session: AsyncSession = Depends(get_session),
) -> FriendActionResponse | ErrorResponse:
    """Удалить друга или отменить запрос"""
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    friend = await users_crud.get_user_by_username(session, friend_username)
    if not friend:
        return ErrorResponse(error="Пользователь не найден")

    await friends_crud.remove_friend(session, user.id, friend.id)

    return FriendActionResponse(
        message=f"Дружба с {friend.username} удалена",
        friend_id=friend.id,
        status="REMOVED",
    )


# === Получить список друзей ===
@router.get("/list")
async def get_friends(
    username: str,
    session: AsyncSession = Depends(get_session),
) -> FriendListResponse | ErrorResponse:
    """Получить список друзей"""
    user = await users_crud.get_user_by_username(session, username)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    friends = await friends_crud.get_user_friends(session, user.id)

    return FriendListResponse(friends=friends)


# === Входящие запросы ===
@router.get("/incoming")
async def get_incoming(
    access_token: str,
    session: AsyncSession = Depends(get_session),
) -> FriendListResponse | ErrorResponse:
    """Получить входящие запросы"""
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    incoming = await friends_crud.get_incoming_requests(session, user.id)
    return FriendListResponse(friends=incoming)


# === Исходящие запросы ===
@router.get("/outgoing")
async def get_outgoing(
    access_token: str,
    session: AsyncSession = Depends(get_session),
) -> FriendListResponse | ErrorResponse:
    """Получить исходящие запросы"""
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    outgoing = await friends_crud.get_outgoing_requests(session, user.id)
    return FriendListResponse(friends=outgoing)


# === Получить статус дружбы с пользователем ===
@router.get("/status/{friend_username}")
async def get_friend_status(
    access_token: str,
    friend_username: str,
    session: AsyncSession = Depends(get_session),
) -> FriendActionResponse | ErrorResponse:
    """Получить статус дружбы между пользователями"""
    # Текущий пользователь
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    # Второй пользователь
    friend = await users_crud.get_user_by_username(session, friend_username)
    if not friend:
        return ErrorResponse(error="Пользователь не найден")

    # Проверяем статус дружбы
    relation = await friends_crud.get_friend_status(session, user.id, friend.id)

    if not relation:
        return FriendActionResponse(
            message=f"Нет отношений между {user.username} и {friend.username}",
            friend_id=friend.id,
            status="none",
        )

    return FriendActionResponse(
        message=f"Текущий статус дружбы с {friend.username}",
        friend_id=friend.id,
        status=relation.status.name,
        initiator_id=relation.initiator_id,
    )
