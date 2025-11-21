"""API request and response models."""

from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class ReconstructRequest(BaseModel):
    """Request to create a reconstruction job."""

    image_urls: list[AnyHttpUrl] = Field(
        min_length=1,
        description="List of image URLs to download and process",
    )
    callback_url: AnyHttpUrl = Field(
        description="URL to call when job is completed or failed",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata to include in callback",
    )


class ReconstructResponse(BaseModel):
    """Response after creating a reconstruction job."""

    job_id: str = Field(description="Unique job identifier")
    status: Literal["queued"] = Field(description="Initial job status")
    message: str = Field(description="Human-readable status message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["ok"] = "ok"
    meshroom_binary: str
    bucket: str


class WebhookPayload(BaseModel):
    """Payload sent to callback URL when job completes."""

    job_id: str
    status: Literal["completed", "failed"]
    result_url: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    "ReconstructRequest",
    "ReconstructResponse",
    "HealthResponse",
    "WebhookPayload",
]

