import json

from src.schemas.stickers import Sticker, StickerPack

from .paths import PathHelper


class StickerHelper:
    """Утилитный класс для вспомогательных действий связанных со стикер паками"""

    @staticmethod
    def get_all() -> list[StickerPack]:
        result: list[StickerPack] = []
        stickers_dir = PathHelper.get_root() / "static" / "sticker_packs"

        sticker_meta_paths = stickers_dir.glob("*.json")

        for sticker_meta_path in sticker_meta_paths:
            sticker_json = str(sticker_meta_path).split("/")[-1]
            sticker_slug = sticker_json.replace(".json", "")
            metadata = StickerHelper.load_json(sticker_meta_path)

            result.append(
                StickerPack(
                    slug=sticker_slug,
                    title=metadata.get("title", "Заголовок не получен"),
                    stickers=StickerHelper.__get_stickers(sticker_slug)
                )
            )

        return result

    @staticmethod
    def __get_stickers(slug: str) -> list[str]:
        result: list[Sticker] = []
        stickers_dir = PathHelper.get_root() / "static" / "sticker_packs" / slug

        sticker_meta_paths = stickers_dir.glob("*.json")

        for sticker_meta_path in sticker_meta_paths:
            sticker_json = str(sticker_meta_path).split("/")[-1]
            metadata = StickerHelper.load_json(sticker_meta_path)

            result.append(
                Sticker(
                    slug=metadata.get("file"),
                    title=metadata.get("title", "Не удалось получить"),
                    description=metadata.get("description", "Не удалось получить")
                )
            )

        return result

    @staticmethod
    def load_json(path: str) -> dict:
        with open(path, mode="r", encoding="utf-8") as f:
            data = json.load(f)

        return data