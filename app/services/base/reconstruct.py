"""Base reconstruction service interface."""

from abc import ABC, abstractmethod


class BaseReconstructService(ABC):
    """Abstract base class for reconstruction services."""

    @abstractmethod
    async def process_job(self, job_id: str, image_urls: list[str]) -> tuple[str, str | None]:
        """Process reconstruction job."""
        pass


__all__ = ["BaseReconstructService"]