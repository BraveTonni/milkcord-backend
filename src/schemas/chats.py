from enum import IntEnum, auto
from pydantic import BaseModel, ConfigDict

from .users import UserPublic
from .response import SuccessResponse


class ChatType(IntEnum):
    PRIVATE = auto()


class ChatInfo(BaseModel):
    id: int

    user: UserPublic

    users: list[UserPublic]
    chat_type: ChatType

    created_at: int

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(SuccessResponse):
    chat: ChatInfo


class ChatsResponse(SuccessResponse):
    chats: list[ChatInfo]
