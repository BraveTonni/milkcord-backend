import shutil
import uuid

from pathlib import Path

from fastapi import UploadFile

from .paths import PathHelper


class FilesHelper:
    """Утилитный класс для работы с загружаемыми файлами"""

    # Что раздаём как есть, всё остальное — бинарным потоком (защита от stored XSS)
    MEDIA_TYPES = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".zip": "application/zip",
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
    }

    @classmethod
    def media_type_for(cls, path: Path | str) -> str:
        """MIME-тип для отдачи файла; неизвестные и html/js расширения
        получают application/octet-stream, браузер скачает их, а не исполнит."""
        return cls.MEDIA_TYPES.get(Path(path).suffix.lower(), "application/octet-stream")

    @staticmethod
    async def save_upload_file(
        upload_file: UploadFile,
        subdir: str = "posts"
    ) -> str:
        upload_dir = PathHelper.get_root() / "static" / "files" / subdir
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_ext = Path(upload_file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return unique_filename