"""Base reconstruction service interface."""

from abc import ABC, abstractmethod

from app.core.reconstruct_providers.base.provider import BaseReconstructProvider


class BaseReconstructService(ABC):
    def __init__(self, reconstruct_provider: BaseReconstructProvider):
        self.reconstruct_provider = reconstruct_provider

    @abstractmethod
    async def process(self, job_id: str, image_urls: list[str]) -> tuple[str, str | None]:
        pass
