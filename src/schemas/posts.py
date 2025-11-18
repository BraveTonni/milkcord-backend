from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from .response import SuccessResponse


# === ОСНОВНЫЕ МОДЕЛИ ===


class PostPins(BaseModel):
    post_id: int


class PostFileBase(BaseModel):
    id: int

    orig_name: str

    file_name: str
    file_size: int

    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    id: int
    user_id: int
    text: str
    liked: bool
    likes_count: int
    comments_count: int
    is_pin: bool
    created_at: int
    username: Optional[str] = None

    files: List[PostFileBase] = []

    model_config = ConfigDict(from_attributes=True)


class PostResponse(SuccessResponse):
    post: PostBase


class PostsResponse(SuccessResponse):
    posts: List[PostBase]


class PostPinResponse(SuccessResponse):
    is_new: bool


# === ЛАЙКИ ===


class LikeBase(BaseModel):
    user_id: int
    post_id: int

    model_config = ConfigDict(from_attributes=True)


class LikeResponse(SuccessResponse):
    liked: bool
    likes_count: int


# === КОММЕНТАРИИ ===


class CommentCreate(BaseModel):
    text: str


class CommentBase(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    text: str
    created_at: int

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(SuccessResponse):
    comment: CommentBase


class CommentsResponse(SuccessResponse):
    comments: List[CommentBase]
