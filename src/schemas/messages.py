from enum import IntEnum, auto

from pydantic import BaseModel, ConfigDict

from typing import Optional

from .users import UserPublic
from .response import SuccessResponse


class MessageKind(IntEnum):
    TEXT = auto()
    STICKER = auto()
    FILE = auto()


class MessageCreate(BaseModel):
    to_user_id: int
    content: str


class MessageSticker(BaseModel):
    to_user_id: int

    pack_slug: str
    sticker_slug: str


class MessageFile(BaseModel):
    id: int
    file_name: str
    orig_name: str
    file_size: int
    created_at: int


class MessageInfo(BaseModel):
    id: int

    chat_id: int

    kind: MessageKind

    from_user: UserPublic
    to_user: UserPublic

    created_at: int

    content: Optional[str] = ""

    pack_slug: Optional[str] = ""
    sticker_slug: Optional[str] = ""

    files: list[MessageFile] | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(SuccessResponse):
    message: MessageInfo
