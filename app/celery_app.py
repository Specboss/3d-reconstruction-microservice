"""Celery application configuration."""

from celery import Celery

from app.core.logger import configure_logging, get_logger
from app.core.settings import get_settings

# Initialize settings
settings = get_settings()
configure_logging(settings.logging)
logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "meshroom_reconstruction",
    broker=settings.broker.celery_broker_url,
    backend=settings.broker.celery_result_backend,
    include=["app.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.meshroom.resources.timeout_seconds,
    task_soft_time_limit=settings.meshroom.resources.timeout_seconds - 300,  # 5 min before hard limit
    task_acks_late=True,  # Acknowledge after task completion
    worker_prefetch_multiplier=1,  # One task at a time
    result_expires=86400,  # Results expire after 24 hours
    task_reject_on_worker_lost=True,
)

logger.info("Celery app configured with broker: %s", settings.broker.host)

__all__ = ["celery_app"]

