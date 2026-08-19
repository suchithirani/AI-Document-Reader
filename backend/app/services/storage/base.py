from abc import ABC, abstractmethod

from fastapi import UploadFile


class BaseStorage(ABC):

    @abstractmethod
    async def save_file(
        self,
        file: UploadFile,
    ) -> tuple[str, str]:
        """
        Returns:
            filename,
            storage_path
        """
        ...

    @abstractmethod
    async def delete_file(
        self,
        storage_path: str,
    ) -> None:
        ...

    @abstractmethod
    async def exists(
        self,
        storage_path: str,
    ) -> bool:
        ...

    @abstractmethod
    async def get_download_url(
        self,
        storage_path: str,
    ) -> str:
        ...

    @abstractmethod
    async def save_bytes(
        self,
        data: bytes,
        filename: str,
    ) -> str:
        ...