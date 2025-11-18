from pydantic import BaseModel, Field

from .response import SuccessResponse


class MusicTrack(BaseModel):
    slug: str

    artist: str
    title: str

    image: str
    track: str

    duration: str

    genres: list[str] = Field(default_factory=list)


class MusicResponse(SuccessResponse):
    tracks: list[MusicTrack]
