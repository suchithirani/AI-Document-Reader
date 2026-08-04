from fastapi import  UploadFile
from pathlib import Path
from app.core.config import settings
from app.services.storage.base import BaseStorage
from app.services.storage.local_storage import LocalStorage


class StorageService:

    def __init__(self):
        self.storage = self._get_storage_provider()

    def _get_storage_provider(
        self,
    ) -> BaseStorage:

        match settings.STORAGE_PROVIDER.lower():

            case "local":
                return LocalStorage()

            case _:
                raise ValueError(
                    f"Unsupported storage provider: "
                    f"{settings.STORAGE_PROVIDER}"
                )

    async def save_file(
        self,
        file: UploadFile,
) -> tuple[str, str]:
        return await self.storage.save_file(
            file
        )

    async def delete_file(
        self,
        storage_path: str,
    ):
        return await self.storage.delete_file(
            storage_path
        )

    async def exists(
        self,
        storage_path: str,
    ):
        return await self.storage.exists(
            storage_path
        )

    async def get_download_url(
        self,
        storage_path: str,
    ):
        return await self.storage.get_download_url(
            storage_path
        )

    async def delete_file(
        self,
        storage_path: str,
    ) -> None:

        path = Path(storage_path)

        if path.exists():
            path.unlink()

    def get_file_path(
        self,
        storage_path: str,
    ) -> Path:

        path = Path(storage_path)

        if not path.exists():
            raise FileNotFoundError(
                "File not found."
            )

        return path