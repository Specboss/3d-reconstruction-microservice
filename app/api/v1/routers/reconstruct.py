from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.api.models import ReconstructRequest, ReconstructResponse
from app.core.logger import get_logger
from app.tasks import process_reconstruction

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
) -> ReconstructResponse:
    """
    Create a new 3D reconstruction job.

    The job will be queued in Celery and processed asynchronously by workers.
    If a callback_url is provided, a webhook will be sent upon completion.
    """
    # Submit Celery task
    task = process_reconstruction.apply_async(
        kwargs={
            "model_id": request.model_id,
            "images_zip_url": str(request.images_url),
        },
        task_id=f"model_{request.model_id}",
    )

    logger.info(
        "Queued reconstruction job for model_id=%s (task_id=%s)",
        request.model_id,
        task.id,
    )

    return ReconstructResponse(
        model_id=request.model_id,
        status="queued",
    )
