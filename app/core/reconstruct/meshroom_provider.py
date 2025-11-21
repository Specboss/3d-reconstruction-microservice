"""Meshroom reconstruction provider."""

from typing import Any

from app.core.reconstruct.base.provider import BaseReconstructProvider


class MeshroomProvider(BaseReconstructProvider):
    """Meshroom-based reconstruction provider."""

    async def reconstruct(self, *args: Any, **kwargs: Any) -> Any:
        """Execute Meshroom reconstruction."""
        # Implementation delegated to MeshroomService
        pass


__all__ = ["MeshroomProvider"]