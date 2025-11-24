from app.core.reconstruct_providers.base.provider import BaseReconstructProvider
from typing import TypedDict, Any

from app.core.logger import Logger


class MeshroomReconstructProvider(BaseReconstructProvider):
    provider_code = 'meshroom'
    
    def __init__(
        self,
        input_dir: str | None = None,
        output_dir: str | None = None,
        cache_dir: str | None = None,
        logger: Logger | None = None
    ):
        super().__init__(input_dir, output_dir, cache_dir, logger)

    async def process(self, *args: Any, **kwargs: Any) -> dict[str, Any]: :
        """Process the reconstruction."""
        pass
