from dataclasses import dataclass

from src.database.models.users import UserBase

from fastapi import WebSocket

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class WSConnection:
    websocket: WebSocket
    user: UserBase

    session: AsyncSession
