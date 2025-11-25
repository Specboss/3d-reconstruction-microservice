"""Meshroom Processing Microservice - REST API Gateway."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.models import HealthResponse
from app.api.v1.routers import reconstruct
from app.core.logger import configure_logging, get_logger
from app.core.settings import AppSettings, get_settings

# Initialize settings and logging
app_settings = get_settings()
configure_logging(app_settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Meshroom Processing Microservice")
    logger.info(f"Meshroom binary: {app_settings.meshroom.binary}")
    logger.info(f"Pipeline: {app_settings.meshroom.pipeline_path}")
    logger.info(f"Celery broker: {app_settings.broker.host}:{app_settings.broker.port}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Meshroom Processing Microservice")


# Create FastAPI application
app = FastAPI(
    title="Meshroom Processing Microservice",
    description="3D reconstruction service using Meshroom photogrammetry",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Include routers
app.include_router(reconstruct.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(
    settings: AppSettings = Depends(get_settings),
) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        meshroom_binary=settings.meshroom.binary,
        bucket=settings.aws.bucket_name,
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "Meshroom Processing Microservice",
        "version": "1.0.0",
        "docs": "/docs",
    }


__all__ = ["app"]

