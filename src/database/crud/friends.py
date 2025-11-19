from sqlalchemy import select, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.friends import Friend, FriendStatus
from src.database.models.users import UserBase
from src.utils.time_formatter import TimeFormatter


# === Отправить запрос в друзья ===
async def send_friend_request(
    session: AsyncSession, user_id: int, friend_id: int
) -> Friend:
    """
    Создаёт запрос в друзья от user_id к friend_id.
    """
    if user_id == friend_id:
        raise ValueError("Нельзя добавить самого себя в друзья")

    # Проверим, нет ли уже связи
    result = await session.execute(
        select(Friend).where(
            or_(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Дружба или запрос уже существует")

    friend_request = Friend(
        user_id=user_id,
        friend_id=friend_id,
        initiator_id=user_id,  # <-- добавлено
        status=FriendStatus.PENDING,
    )

    session.add(friend_request)
    await session.commit()
    await session.refresh(friend_request)

    return friend_request


# === Принять запрос в друзья ===
async def accept_friend_request(
    session: AsyncSession, user_id: int, friend_id: int
) -> Friend | None:
    """
    Принимает входящий запрос (friend_id отправил user_id).
    """
    result = await session.execute(
        select(Friend).where(
            and_(
                Friend.user_id == friend_id,
                Friend.friend_id == user_id,
                Friend.status == FriendStatus.PENDING,
            )
        )
    )
    friend_request = result.scalar_one_or_none()
    if not friend_request:
        return None

    friend_request.status = FriendStatus.ACCEPTED
    friend_request.updated_at = TimeFormatter.get_current_unix()

    session.add(friend_request)
    await session.commit()
    await session.refresh(friend_request)

    return friend_request


# === Удалить из друзей (или отменить запрос) ===
async def remove_friend(session: AsyncSession, user_id: int, friend_id: int) -> bool:
    """
    Удаляет дружбу (в любую сторону).
    """
    await session.execute(
        delete(Friend).where(
            or_(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
            )
        )
    )
    await session.commit()
    return True


# === Получить всех друзей ===
async def get_user_friends(session: AsyncSession, user_id: int) -> list[UserBase]:
    """
    Возвращает список пользователей, с которыми user_id — друзья (accepted).
    """
    result = await session.execute(
        select(UserBase)
        .join(
            Friend,
            or_(
                and_(Friend.user_id == user_id, Friend.friend_id == UserBase.id),
                and_(Friend.friend_id == user_id, Friend.user_id == UserBase.id),
            ),
        )
        .where(Friend.status == FriendStatus.ACCEPTED)
    )

    return list(result.scalars().all())


# === Получить входящие запросы ===
async def get_incoming_requests(session: AsyncSession, user_id: int) -> list[UserBase]:
    """
    Возвращает список пользователей, которые отправили запрос user_id.
    """
    result = await session.execute(
        select(UserBase)
        .join(Friend, Friend.user_id == UserBase.id)
        .where(
            Friend.friend_id == user_id,
            Friend.status == FriendStatus.PENDING,
        )
    )

    return list(result.scalars().all())


# === Получить исходящие запросы ===
async def get_outgoing_requests(session: AsyncSession, user_id: int) -> list[UserBase]:
    """
    Возвращает список пользователей, которым user_id отправил запрос.
    """
    result = await session.execute(
        select(UserBase)
        .join(Friend, Friend.friend_id == UserBase.id)
        .where(
            Friend.user_id == user_id,
            Friend.status == FriendStatus.PENDING,
        )
    )

    return list(result.scalars().all())


# === Получить статус дружбы ===
async def get_friend_status(session: AsyncSession, user_id: int, friend_id: int):
    """
    Возвращает объект Friend (или None), чтобы можно было узнать:
    - статус
    - инициатора (initiator_id)
    - направление (incoming/outgoing)
    """
    result = await session.execute(
        select(Friend).where(
            or_(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
            )
        )
    )
    friend_obj = result.scalar_one_or_none()
    return friend_obj
