import json

from src.schemas.music import MusicTrack

from .paths import PathHelper

from mutagen.mp3 import MP3


class MusicHelper:
    """Утилитный класс для вспомогательных действий связанных с музыкой"""

    @staticmethod
    def get_all() -> list[MusicTrack]:
        result: list[MusicTrack] = []
        track_path = PathHelper.get_root() / "static" / "music"

        tracks = track_path.rglob("*.json")

        for track in tracks:
            music_json = str(track).split("/")[-1]
            music_slug = music_json.replace(".json", "")
            metadata = MusicHelper.load_json(track)

            result.append(
                MusicTrack(
                    slug=music_slug,
                    title=metadata.get("title", "Заголовок не получен"),
                    artist=metadata.get("artist", "Имя артиста не получено"),
                    genres=metadata.get("genres", []),
                    image=metadata.get("image"),
                    track=metadata.get("track"),
                    duration=MusicHelper.get_duration(track.with_suffix(".mp3")),
                )
            )

        return result

    @staticmethod
    def get_duration(path) -> str:
        audio = MP3(path)
        seconds = int(audio.info.length)

        # форматируем 150 → "02:30"
        minutes = seconds // 60
        sec = seconds % 60
        return f"{minutes:02}:{sec:02}"

    @staticmethod
    def load_json(path: str) -> dict:
        with open(path, mode="r", encoding="utf-8") as f:
            data = json.load(f)

        return data
