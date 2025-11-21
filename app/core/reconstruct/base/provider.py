"""Base reconstruction provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseReconstructProvider(ABC):
    """Abstract base class for reconstruction providers."""

    @abstractmethod
    async def reconstruct(self, *args: Any, **kwargs: Any) -> Any:
        """Execute reconstruction."""
        pass


__all__ = ["BaseReconstructProvider"]