"""Reconstruction API endpoints."""

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
    description="Submit ZIP archive with images for 3D reconstruction. Job will be queued and processed asynchronously.",
)
async def create_reconstruction_job(
    request: ReconstructRequest,
    broker: Annotated[RabbitMQBroker, Depends(get_broker)],
) -> ReconstructResponse:
    """
    Create a new 3D reconstruction job.

    The job will be queued and processed by available workers.
    When complete, the model will be saved to MinIO and your callback will be notified.
    """
    # Build job message
    job_message = {
        "model_id": request.model_id,
        "images_url": str(request.images_url),
        "callback_url": str(request.callback_url) if request.callback_url else None,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Publish to RabbitMQ
    await broker.connect()
    await broker.publish(job_message)

    logger.info(
        "Created reconstruction job for model_id=%s from %s",
        request.model_id,
        request.images_url,
    )

    return ReconstructResponse(
        model_id=request.model_id,
        status="queued",
    )


__all__ = ["router"]

