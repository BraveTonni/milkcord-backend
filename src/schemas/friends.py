from pydantic import BaseModel
from typing import List

from .response import SuccessResponse
from src.schemas.users import UserPublic


class FriendActionResponse(BaseModel):
    message: str
    friend_id: int
    status: str
    initiator_id: int | None = None


class FriendListResponse(SuccessResponse):
    friends: List[UserPublic]
