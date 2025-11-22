"""Factory for creating reconstruction providers."""

from __future__ import annotations

from typing import Literal

from app.core.logger import get_logger
from app.core.reconstruct_provider.base.provider import BaseReconstructProvider
from app.core.reconstruct_provider.meshroom import MeshroomProvider
from app.core.settings import MeshroomConfigModel
from app.core.storage.base.storage import BaseStorage

logger = get_logger(__name__)

ProviderType = Literal["meshroom"]


class ProviderFactory:
    """Factory for creating reconstruction providers."""

    @staticmethod
    def create_provider(
        provider_type: ProviderType,
        config: MeshroomConfigModel,
        storage: BaseStorage,
    ) -> BaseReconstructProvider:
        """
        Create a reconstruction provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider configuration
            storage: Storage backend

        Returns:
            Reconstruction provider instance

        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type == "meshroom":
            logger.info("Creating Meshroom provider")
            return MeshroomProvider(config=config, storage=storage)
        
        # Future providers can be added here:
        # elif provider_type == "colmap":
        #     return ColmapProvider(config=config, storage=storage)
        # elif provider_type == "realitycapture":
        #     return RealityCaptureProvider(config=config, storage=storage)
        
        raise ValueError(f"Unsupported provider type: {provider_type}")


__all__ = ["ProviderFactory", "ProviderType"]

