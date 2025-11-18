from pydantic import BaseModel, EmailStr, ConfigDict

from typing import Optional
from .response import SuccessResponse


class UserLogin(BaseModel):
    username: str
    password: str


class UserSignUp(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str


class UserToken(BaseModel):
    access_token: str


class UserBioUpdate(BaseModel):
    bio: str


class UserSettingsUpdate(BaseModel):
    username: str
    email: EmailStr
    password: Optional[str] = None


class UserPrivate(BaseModel):
    id: int
    access_token: str
    username: str
    email: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None

    created_at: int
    last_seen: int

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = ""

    created_at: int
    last_seen: int

    model_config = ConfigDict(from_attributes=True)


class UserResponse(SuccessResponse):
    user: UserPrivate


class UserPublicResponse(SuccessResponse):
    user: UserPublic
