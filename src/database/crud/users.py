from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import UserSignUp

from src.database.models.users import UserBase

from src.database.crud import items as items_crud


async def create_user(session: AsyncSession, user: UserSignUp) -> UserBase:
    """Создание пользователя"""
    user = UserBase(username=user.username, email=user.email, password=user.password)
    session.add(user)

    return await items_crud.update_item(session, user)


async def get_user_by_username(session: AsyncSession, username: str) -> UserBase | None:
    """Получение пользователя по юзернейму из базы данных"""
    result = await session.execute(
        select(UserBase).where(func.lower(UserBase.username) == username.lower())
    )

    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> UserBase | None:
    """Получение пользователя по юзернейму из базы данных"""
    result = await session.execute(select(UserBase).where(UserBase.id == user_id))

    return result.scalar_one_or_none()


async def get_users_by_ids(session: AsyncSession, user_ids: list[int]):
    result = await session.execute(select(UserBase).where(UserBase.id.in_(user_ids)))
    return result.scalars().all()


async def get_user_by_access_token(
    session: AsyncSession, access_token: str
) -> UserBase | None:
    """Получение пользователя по токену"""
    result = await session.execute(
        select(UserBase).where(UserBase.access_token == access_token)
    )

    return result.scalar_one_or_none()


async def update_user_bio(session, user: UserBase, new_bio: str) -> UserBase:
    """
    Обновляет bio пользователя.
    """
    user.bio = new_bio
    session.add(user)

    return user


async def update_user_avatar(session, user: UserBase, avatar_url: str) -> UserBase:
    """Обновляет ссылку на аватар пользователя"""
    user.avatar_url = avatar_url
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user


async def update_user_cover(session, user: UserBase, cover_url: str) -> UserBase:
    """Обновляет ссылку на аватар пользователя"""
    user.cover_url = cover_url
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user


async def update_last_seen(session, user: UserBase, unix: int) -> UserBase:
    """Обновляет ссылку на аватар пользователя"""
    user.last_seen = unix
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user


async def get_user_by_email(session: AsyncSession, email: str) -> UserBase | None:
    """Получение пользователя по email"""
    result = await session.execute(
        select(UserBase).where(func.lower(UserBase.email) == email.lower())
    )
    return result.scalar_one_or_none()
