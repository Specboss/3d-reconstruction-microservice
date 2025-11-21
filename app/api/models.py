"""API request and response models."""

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class ReconstructRequest(BaseModel):
    """Request to create a reconstruction job."""

    model_id: int = Field(
        description="Unique model identifier from your system",
        gt=0,
    )
    images_url: AnyHttpUrl = Field(
        description="MinIO URL to ZIP archive with photos (e.g., https://minio/bucket-name/photos.zip)",
    )
    callback_url: AnyHttpUrl | None = Field(
        default=None,
        description="Optional webhook URL to receive completion notification",
    )


class ReconstructResponse(BaseModel):
    """Response after creating a reconstruction job."""

    model_id: int = Field(description="Model identifier from request")
    status: Literal["queued"] = Field(default="queued", description="Job queued for processing")


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["ok"] = "ok"
    meshroom_binary: str
    bucket: str


class WebhookPayload(BaseModel):
    """Payload sent to callback URL when job completes."""

    model_id: int = Field(description="Model identifier from request")
    status: Literal["success", "error"] = Field(description="Processing result")
    model_url: str | None = Field(
        default=None,
        description="MinIO URL to resulting model (e.g., https://minio/bucket-name/model.gltf)",
    )
    error: str | None = Field(default=None, description="Error message if status=error")


__all__ = [
    "ReconstructRequest",
    "ReconstructResponse",
    "HealthResponse",
    "WebhookPayload",
]

