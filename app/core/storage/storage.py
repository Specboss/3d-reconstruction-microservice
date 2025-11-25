from abc import ABC, abstractmethod
from pathlib import Path

from app.core.logger import Logger, get_logger
from app.core.settings import AwsConfigModel


class BaseStorage(ABC):
    """Abstract base class for storage providers."""

    def __init__(self, config: AwsConfigModel, access_key: str, secret_key: str, logger: Logger | None = None):
        self.config = config
        self.access_key = access_key
        self.secret_key = secret_key
        self.logger = logger or get_logger(self.__class__.__name__)

    @abstractmethod
    async def upload_file(self, local_path: Path, remote_key: str) -> str:
        """
        Upload file to storage.
        """
        pass

    @abstractmethod
    async def download_file(self, remote_key: str, local_path: Path) -> None:
        pass

    @abstractmethod
    async def download_url(self, url: str, local_path: Path) -> None:
        """
        Download file from URL.
        """
        pass

    @abstractmethod
    async def get_presigned_url(self, remote_key: str, expires_in: int = 3600) -> str:
        pass

    @abstractmethod
    async def delete_file(self, remote_key: str) -> None:
        pass
