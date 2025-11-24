from abc import ABC, abstractmethod
from typing import Any

from app.core.logger import Logger, get_logger


class BaseReconstructProvider(ABC):
    def __init__(
        self,
        input_dir: str | None = None,
        output_dir: str | None = None,
        cache_dir: str | None = None,
        logger: Logger | None = None
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        self.logger = logger or get_logger(self.__class__.__name__)

    @abstractmethod
    async def process(self, *args: Any, **kwargs: Any) -> Any:
        """Базовый process"""
        pass
