"""Celery tasks for 3D reconstruction processing."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from celery import Task

from app.celery_app import celery_app
from app.core.logger import get_logger
from app.core.settings import get_settings
from app.core.storage.minio import MinioStorage
from app.services.reconstruction_service import ReconstructionService

logger = get_logger(__name__)


class ReconstructionTask(Task):
    """Base task with retry configuration for reconstruction jobs."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=ReconstructionTask,
    name="app.tasks.process_reconstruction",
)
def process_reconstruction(
    self: Task,
    model_id: int,
    images_zip_url: str,
    callback_url: str | None = None,
) -> dict[str, Any]:
    """
    Process 3D reconstruction job.

    Args:
        self: Celery task instance
        model_id: Unique model identifier
        images_zip_url: URL to ZIP archive with input images
        callback_url: Optional webhook URL for completion notification

    Returns:
        Dictionary with reconstruction results

    Raises:
        Exception: If reconstruction fails after all retries
    """
    logger.info("=" * 80)
    logger.info("Processing reconstruction task for model_id=%s", model_id)
    logger.info("Task ID: %s", self.request.id)
    logger.info("Retry: %s/%s", self.request.retries, self.max_retries)
    logger.info("=" * 80)

    # Initialize settings and services
    settings = get_settings()
    
    storage = MinioStorage(
        config=settings.aws,
        access_key=settings.secrets.aws_access_key_id,
        secret_key=settings.secrets.aws_secret_access_key,
    )
    
    reconstruction_service = ReconstructionService(
        provider_type="meshroom",
        config=settings.meshroom,
        storage=storage,
    )

    try:
        # Run async reconstruction in event loop
        result = asyncio.run(
            reconstruction_service.process_reconstruction(
                model_id=model_id,
                images_zip_url=images_zip_url,
            )
        )

        logger.info("Reconstruction completed successfully for model_id=%s", model_id)

        # Send success webhook if provided
        if callback_url:
            asyncio.run(
                send_webhook(
                    url=callback_url,
                    payload={
                        "model_id": model_id,
                        "status": "success",
                        "model_url": result["model_url"],
                        "texture_urls": result.get("texture_urls", []),
                        "stats": result.get("stats", {}),
                    },
                )
            )

        return result

    except Exception as exc:
        logger.error(
            "Reconstruction failed for model_id=%s: %s",
            model_id,
            exc,
            exc_info=True,
        )

        # Send error webhook if provided
        if callback_url:
            try:
                asyncio.run(
                    send_webhook(
                        url=callback_url,
                        payload={
                            "model_id": model_id,
                            "status": "error",
                            "error": str(exc),
                        },
                    )
                )
            except Exception as webhook_exc:
                logger.error(
                    "Failed to send error webhook: %s",
                    webhook_exc,
                    exc_info=True,
                )

        # Re-raise for Celery retry mechanism
        raise


async def send_webhook(url: str, payload: dict[str, Any]) -> None:
    """
    Send webhook notification.

    Args:
        url: Webhook URL
        payload: JSON payload to send

    Raises:
        httpx.HTTPError: If webhook request fails
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook sent successfully to %s: %s", url, response.status_code)
    except Exception as exc:
        logger.error("Failed to send webhook to %s: %s", url, exc)
        raise


__all__ = ["process_reconstruction"]

