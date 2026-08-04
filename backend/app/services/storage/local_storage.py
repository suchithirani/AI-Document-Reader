from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.services.storage.base import BaseStorage


class LocalStorage(BaseStorage):

    def __init__(self):
        self.upload_directory = Path(
            settings.UPLOAD_DIRECTORY
        )

        self.upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def save_file(
        self,
        file: UploadFile,
    ) -> tuple[str, str]:
        extension = Path(
            file.filename
        ).suffix

        filename = (
            f"{uuid4()}{extension}"
        )

        storage_path = (
            self.upload_directory
            / filename
        )

        with open(
            storage_path,
            "wb",
        ) as buffer:
            buffer.write(
                await file.read()
            )

        return (
            filename,
            str(storage_path),
        )

    async def delete_file(
        self,
        storage_path: str,
    ) -> None:
        path = Path(storage_path)

        if path.exists():
            path.unlink()

    async def exists(
        self,
        storage_path: str,
    ) -> bool:
        return Path(
            storage_path
        ).exists()

    async def get_download_url(
        self,
        storage_path: str,
    ) -> str:
        return storage_path