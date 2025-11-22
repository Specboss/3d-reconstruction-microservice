from abc import ABC, abstractmethod
from typing import Any


class BaseReconstructProvider(ABC):
    @abstractmethod
    async def reconstruct(self, *args: Any, **kwargs: Any) -> Any:
        pass
