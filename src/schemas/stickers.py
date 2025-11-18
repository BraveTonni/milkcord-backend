from pydantic import BaseModel

from .response import SuccessResponse


class Sticker(BaseModel):
    slug: str

    title: str
    description: str


class StickerPack(BaseModel):
    slug: str

    title: str

    stickers: list[Sticker]


class StickerPackResponse(SuccessResponse):
    pack: StickerPack


class StickerPacksResponse(SuccessResponse):
    packs: list[StickerPack]
