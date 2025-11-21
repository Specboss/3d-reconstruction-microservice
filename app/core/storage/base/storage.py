"""Base storage interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseStorage(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    async def upload_file(self, local_path: Path, remote_key: str) -> str:
        """
        Upload file to storage.

        Args:
            local_path: Local file path
            remote_key: Remote object key/path

        Returns:
            URL to uploaded file
        """
        ...

    @abstractmethod
    async def download_file(self, remote_key: str, local_path: Path) -> None:
        """
        Download file from storage.

        Args:
            remote_key: Remote object key/path
            local_path: Local destination path
        """
        ...

    @abstractmethod
    async def download_url(self, url: str, local_path: Path) -> None:
        """
        Download file from URL.

        Args:
            url: Source URL
            local_path: Local destination path
        """
        ...

    @abstractmethod
    async def get_presigned_url(self, remote_key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for object.

        Args:
            remote_key: Remote object key/path
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        ...

    @abstractmethod
    async def delete_file(self, remote_key: str) -> None:
        """
        Delete file from storage.

        Args:
            remote_key: Remote object key/path
        """
        ...


__all__ = ["BaseStorage"]