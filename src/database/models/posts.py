from sqlalchemy import BigInteger, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from src.utils.time_formatter import TimeFormatter


# === Пост ===
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(String(300), nullable=False)

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    # ORM-связи
    user = relationship("UserBase", back_populates="posts")
    likes = relationship(
        "PostLike", back_populates="post", cascade="all, delete-orphan"
    )
    comments = relationship(
        "PostComment", back_populates="post", cascade="all, delete-orphan"
    )
    files = relationship(
        "PostFile", back_populates="post", cascade="all, delete-orphan"
    )


# === Файлы к посту ===
class PostFile(Base):
    __tablename__ = "post_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    orig_name: Mapped[str] = mapped_column(String(500), nullable=False)

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)  # Уникальное название файла
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    # ORM-связи
    post = relationship("Post", back_populates="files")


# === Лайки ===
class PostLike(Base):
    __tablename__ = "post_likes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    # ORM-связи
    post = relationship("Post", back_populates="likes")
    user = relationship("UserBase", back_populates="liked_posts")

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_user_post_like"),
    )


# === Комментарии ===
class PostComment(Base):
    __tablename__ = "post_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    # ORM-связи
    post = relationship("Post", back_populates="comments")
    user = relationship("UserBase", back_populates="comments")


# === Закрепы ===
class PostPins(Base):
    __tablename__ = "post_pins"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[int] = mapped_column(
        BigInteger, default=TimeFormatter.get_current_unix
    )

    # ORM-связи
    user = relationship("UserBase", back_populates="pin_post")

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_pin"),)
