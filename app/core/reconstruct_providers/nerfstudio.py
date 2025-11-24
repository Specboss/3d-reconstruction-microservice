from app.core.reconstruct_providers.base.provider import BaseReconstructProvider
from app.core.logger import Logger

class NerfstudioReconstructProvider(BaseReconstructProvider):
    provider_code = 'nerfstudio'
    
    def __init__(
        self,
        input_dir: str | None = None,
        output_dir: str | None = None,
        cache_dir: str | None = None,
        logger: Logger | None = None,
        #config: NerfstudioConfigModel | None = None,
    ):
        super().__init__(input_dir, output_dir, cache_dir, logger)