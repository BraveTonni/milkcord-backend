import shutil
import uuid

from pathlib import Path

from fastapi import UploadFile

from .paths import PathHelper


class FilesHelper:
    """Утилитный класс для работы с загружаемыми файлами"""

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