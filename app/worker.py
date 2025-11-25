"""Celery worker entrypoint - processes reconstruction tasks."""

import sys

from app.celery_app import celery_app
from app.core.logger import configure_logging, get_logger
from app.core.settings import get_settings

# Initialize settings and logging
settings = get_settings()
configure_logging(settings.logging)
logger = get_logger(__name__)

logger.info("=" * 80)
logger.info("Starting Celery Worker for 3D Reconstruction")
logger.info("=" * 80)
logger.info(f"Meshroom binary: {settings.meshroom.binary}")
logger.info(f"Workspace: {settings.meshroom.workspace_dir}")
logger.info(f"Broker: {settings.broker.celery_broker_url}")
logger.info(f"Result backend: {settings.broker.celery_result_backend}")
logger.info("=" * 80)

if __name__ == "__main__":
    try:
        # Start Celery worker
        argv = [
            "worker",
            "--loglevel=info",
            "--concurrency=1",  # One task at a time due to resource-intensive processing
            "--max-tasks-per-child=10",  # Restart worker after 10 tasks to prevent memory leaks
        ]
        celery_app.worker_main(argv)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Worker error: {exc}", exc_info=True)
        sys.exit(1)
