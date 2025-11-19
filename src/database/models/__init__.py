# Импорт моделей, дабы SQLAlchemy увидел их и зарегистрировал
from .users import UserBase  # noqa: F401
from .friends import Friend  # noqa: F401
from .posts import Post, PostComment, PostLike, PostPins

__all__ = [
    "UserBase", "Friend", "Post",
    "PostComment", "PostLike", "PostPins"
]
