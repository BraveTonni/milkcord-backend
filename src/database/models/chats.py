from .base import Base

from sqlalchemy import BigInteger, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.time_formatter import TimeFormatter

from src.schemas.chats import ChatType


class ChatBase(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False)
    chat_type: Mapped[ChatType] = mapped_column(SAEnum(ChatType), nullable=False)

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )
