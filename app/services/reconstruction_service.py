"""Universal reconstruction service that works with any provider."""

from __future__ import annotations

from typing import Any

from app.core.logger import get_logger
from app.core.reconstruction.base import BaseReconstructProvider
from app.core.reconstruct_providers.factory import ProviderFactory, ProviderType
from app.core.settings import MeshroomConfigModel
from app.core.storage.base.storage import BaseStorage

logger = get_logger(__name__)


class ReconstructionService:
    def __init__(
        self,
        provider_type: ProviderType,
        config: MeshroomConfigModel,
        storage: BaseStorage,
    ) -> None:
        """
        Initialize reconstruction service.

        Args:
            provider_type: Type of reconstruction provider to use
            config: Provider configuration
            storage: Storage backend
        """
        self.provider_type = provider_type
        self.config = config
        self.storage = storage
        self.logger = get_logger(self.__class__.__name__)
        
        # Create provider instance
        self.provider: BaseReconstructProvider = ProviderFactory.create_provider(
            provider_type=provider_type,
            config=config,
            storage=storage,
        )
        
        self.logger.info("Initialized ReconstructionService with provider: %s", provider_type)

    async def process_reconstruction(
        self,
        model_id: int,
        images_zip_url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Process 3D reconstruction job.

        Args:
            model_id: Unique model identifier
            images_zip_url: URL to ZIP archive with input images
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary with reconstruction results:
            {
                "model_url": str,      # URL to resulting 3D model
                "texture_urls": list,  # URLs to texture files
                "stats": dict,         # Reconstruction statistics
            }

        Raises:
            RuntimeError: If reconstruction fails
        """
        self.logger.info(
            "Starting reconstruction for model_id=%s using provider=%s",
            model_id,
            self.provider_type,
        )
        
        try:
            result = await self.provider.reconstruct(
                model_id=model_id,
                images_zip_url=images_zip_url,
                **kwargs,
            )
            
            self.logger.info(
                "Reconstruction completed successfully for model_id=%s",
                model_id,
            )
            
            return result
            
        except Exception as exc:
            self.logger.error(
                "Reconstruction failed for model_id=%s: %s",
                model_id,
                exc,
                exc_info=True,
            )
            raise

