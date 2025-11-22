from typing import Any

from app.core.reconstruct_provider.base.provider import BaseReconstructProvider


class MeshroomProvider(BaseReconstructProvider):
    async def reconstruct(self, *args: Any, **kwargs: Any) -> Any:
        pass
