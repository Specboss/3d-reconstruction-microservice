from typing import Any

from app.core.reconstruction.base import BaseReconstructProvider
from app.core.logger import Logger


class NerfstudioReconstructProvider(BaseReconstructProvider):
    provider_code = 'nerfstudio'

    def __init__(
            self,
            input_dir: str | None = None,
            output_dir: str | None = None,
            cache_dir: str | None = None,
            logger: Logger | None = None,
            # config: NerfstudioConfigModel | None = None,
    ):
        super().__init__(input_dir, output_dir, cache_dir, logger)

    async def process(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}
