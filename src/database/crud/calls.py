from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import UTC, datetime

from src.database.models.calls import Call


def _utcnow() -> datetime:
    """Текущее UTC-время без таймзоны: колонки DateTime объявлены без tz."""
    return datetime.now(UTC).replace(tzinfo=None)


async def start_call(session: AsyncSession, caller_id: int, callee_id: int, kind: str):
    call = Call(
        caller_id=caller_id,
        callee_id=callee_id,
        kind=kind,
        started_at=_utcnow(),
    )
    session.add(call)
    await session.commit()
    await session.refresh(call)
    return call


async def end_call(session: AsyncSession, call_id: int, closed_by: int):
    q = await session.execute(select(Call).where(Call.id == call_id))
    call = q.scalar_one_or_none()

    if not call:
        return None

    call.ended_at = _utcnow()
    call.closed_by = closed_by
    await session.commit()
    await session.refresh(call)

    return call


async def get_call(session: AsyncSession, call_id: int):
    q = await session.execute(select(Call).where(Call.id == call_id))
    return q.scalar_one_or_none()
