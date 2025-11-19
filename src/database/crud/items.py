from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar('T')


async def update_item(session: AsyncSession, item: T) -> T:
    """
    Синхронизация объекта с базой данных, фиксиря изменения с обновлением
    аттрибутов
    """
    await session.commit()
    await session.refresh(item)

    return item


async def remove_item(session: AsyncSession, item: object) -> None:
    """Удаление объекта из базы данных и фиксирование изменений"""
    await session.delete(item)

    await session.commit()
