"""Reconstruction API endpoints."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_broker, verify_api_key
from app.api.models import ReconstructRequest, ReconstructResponse
from app.core.broker import RabbitMQBroker
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reconstruct", tags=["reconstruction"])


@router.post(
    "",
    response_model=ReconstructResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Create 3D reconstruction job",
    description="Submit images for 3D reconstruction. Job will be queued and processed asynchronously.",
)
async def create_reconstruction_job(
    request: ReconstructRequest,
    broker: Annotated[RabbitMQBroker, Depends(get_broker)],
) -> ReconstructResponse:
    """
    Create a new 3D reconstruction job.

    The job will be queued and processed by available workers.
    When complete, a webhook will be sent to the provided callback_url.
    """
    job_id = uuid.uuid4().hex

    # Build job message
    job_message = {
        "job_id": job_id,
        "image_urls": [str(url) for url in request.image_urls],
        "callback_url": str(request.callback_url),
        "metadata": request.metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    # Publish to RabbitMQ
    await broker.connect()
    await broker.publish(job_message)

    logger.info(
        "Created reconstruction job %s with %d images",
        job_id,
        len(request.image_urls),
    )

    return ReconstructResponse(
        job_id=job_id,
        status="queued",
        message=f"Job {job_id} has been queued for processing",
    )


__all__ = ["router"]

