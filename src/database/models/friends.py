from sqlalchemy import BigInteger, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models.base import Base
from src.core.enums.friends import FriendStatus

from src.utils.time_formatter import TimeFormatter


class Friend(Base):
    __tablename__ = "friends"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    initiator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    status: Mapped[FriendStatus] = mapped_column(
        SQLEnum(FriendStatus, name="friend_status", create_type=True)
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )
    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    user = relationship(
        "UserBase", back_populates="friends_sent", foreign_keys=[user_id]
    )
    friend = relationship(
        "UserBase", back_populates="friends_received", foreign_keys=[friend_id]
    )
