# src/database/models/messages.py

from .base import Base
from sqlalchemy import BigInteger, ForeignKey, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.schemas.messages import MessageKind
from src.utils.time_formatter import TimeFormatter


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    kind: Mapped[MessageKind] = mapped_column(
        SAEnum(MessageKind),
        nullable=False,
        default=MessageKind.TEXT,
    )

    from_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    pack_slug: Mapped[str | None] = mapped_column(Text, nullable=True)
    sticker_slug: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    files: Mapped[list["ChatMessageFile"]] = relationship(
        "ChatMessageFile",
        back_populates="message",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )


class ChatMessageFile(Base):
    __tablename__ = "chat_message_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    orig_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    message: Mapped["ChatMessages"] = relationship(
        "ChatMessages",
        back_populates="files",
    )