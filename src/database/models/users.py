from .base import Base

from sqlalchemy import BigInteger, String, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.time_formatter import TimeFormatter
from src.utils.token_generator import generate_access_token


class UserBase(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    access_token: Mapped[str] = mapped_column(
        String(255), nullable=False, default=generate_access_token
    )

    bio: Mapped[str] = mapped_column(String(100), nullable=True)

    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[str] = mapped_column(String(500), nullable=True)

    last_seen: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix()
    )
    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix()
    )

    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    liked_posts = relationship(
        "PostLike", back_populates="user", cascade="all, delete-orphan"
    )
    comments = relationship(
        "PostComment", back_populates="user", cascade="all, delete-orphan"
    )
    pin_post = relationship(
        "PostPins", back_populates="user", cascade="all, delete-orphan"
    )

    friends_sent = relationship(
        "Friend",
        back_populates="user",
        foreign_keys="Friend.user_id",
        cascade="all, delete-orphan"
    )

    friends_received = relationship(
        "Friend",
        back_populates="friend",
        foreign_keys="Friend.friend_id",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_username_lower", text("LOWER(username)"), unique=True),
    )
