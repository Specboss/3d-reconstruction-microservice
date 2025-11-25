"""Reconstruction service - orchestrates reconstruction providers."""

from __future__ import annotations

from typing import Any, Literal

from app.core.logger import get_logger
from app.core.reconstruction.base import BaseReconstructProvider
from app.core.reconstruction.meshroom import MeshroomReconstructProvider
from app.core.reconstruction.nerfstudio import NerfstudioReconstructProvider
from app.core.settings import MeshroomConfigModel
from app.core.storage.base.storage import BaseStorage

logger = get_logger(__name__)

ProviderType = Literal["meshroom", "nerfstudio"]

# Provider registry - простой словарь вместо factory
PROVIDERS: dict[str, type[BaseReconstructProvider]] = {
    "meshroom": MeshroomReconstructProvider,
    "nerfstudio": NerfstudioReconstructProvider,
}


class ReconstructionService:
    """
    Service for 3D reconstruction using pluggable providers.
    
    This service acts as an orchestrator that:
    - Creates the appropriate provider based on type
    - Manages the reconstruction workflow
    - Handles errors and logging
    """

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
            storage: Storage backend for file operations
        """
        self.provider_type = provider_type
        self.config = config
        self.storage = storage
        self.logger = get_logger(self.__class__.__name__)

        # Create provider instance
        provider_class = PROVIDERS.get(provider_type)
        if not provider_class:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available: {list(PROVIDERS.keys())}"
            )

        # Initialize provider with config and storage
        self.provider: BaseReconstructProvider = provider_class(
            config=config,
            logger=self.logger,
        )

        self.logger.info(
            f"Initialized ReconstructionService with provider: {provider_type}",
        )

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
            ValueError: If provider type is invalid
        """
        self.logger.info(
            f"Starting reconstruction for model_id={model_id} "
            f"using provider={self.provider_type}",
        )

        try:
            # Call provider's process method
            result = await self.provider.process(
                model_id=model_id,
                images_zip_url=images_zip_url,
                storage=self.storage,
                **kwargs,
            )

            self.logger.info(
                f"Reconstruction completed successfully for model_id={model_id}",
            )

            return result

        except Exception as exc:
            self.logger.error(
                f"Reconstruction failed for model_id={model_id}: {exc}",
                exc_info=True,
            )
            raise


__all__ = ["ReconstructionService", "ProviderType"]

