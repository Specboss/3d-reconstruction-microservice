"""Meshroom worker - consumes jobs from RabbitMQ and processes them."""

import asyncio
import json
import sys

import httpx
from aio_pika.abc import AbstractIncomingMessage

from app.core.broker import RabbitMQBroker
from app.core.logger import configure_logging, get_logger
from app.core.settings import get_settings
from app.core.storage.minio import MinioStorage
from app.services.meshroom_service import MeshroomService

# Initialize settings and logging
settings = get_settings()
configure_logging(settings.logging)
logger = get_logger(__name__)

# Initialize services
broker = RabbitMQBroker(settings.broker)
storage = MinioStorage(
    config=settings.aws,
    access_key=settings.secrets.aws_access_key_id,
    secret_key=settings.secrets.aws_secret_access_key,
)
meshroom_service = MeshroomService(
    config=settings.meshroom,
    storage=storage,
)


async def process_message(message: AbstractIncomingMessage) -> None:
    """
    Process a job message from RabbitMQ.

    Args:
        message: Incoming message from queue
    """
    async with message.process():
        try:
            # Parse job data
            job_data = json.loads(message.body.decode("utf-8"))
            model_id = job_data["model_id"]
            images_url = job_data["images_url"]
            callback_url = job_data.get("callback_url")

            logger.info(
                "Processing model_id=%s from %s",
                model_id,
                images_url,
            )

            # Process the reconstruction
            status, result = await meshroom_service.process_job(model_id, images_url)

            # Build callback payload
            if status == "completed":
                callback_payload = {
                    "model_id": model_id,
                    "status": "success",
                    "model_url": result,
                }
                logger.info("Model %s completed successfully: %s", model_id, result)
            else:
                callback_payload = {
                    "model_id": model_id,
                    "status": "error",
                    "error": result,
                }
                logger.error("Model %s failed: %s", model_id, result)

            # Send webhook if callback_url provided
            if callback_url:
                await send_webhook(callback_url, callback_payload)
            else:
                logger.info("No callback_url provided. Result: %s", callback_payload)

        except Exception as exc:
            logger.error("Failed to process message: %s", exc, exc_info=True)
            # Message will be requeued automatically since we didn't ack it


async def send_webhook(url: str, payload: dict) -> None:
    """
    Send webhook notification to callback URL.

    Args:
        url: Callback URL
        payload: Payload to send
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook sent to %s: %s", url, response.status_code)
    except Exception as exc:
        logger.error("Failed to send webhook to %s: %s", url, exc)


async def main() -> None:
    """Main worker loop."""
    logger.info("=" * 60)
    logger.info("Starting Meshroom Worker")
    logger.info("=" * 60)
    logger.info("Meshroom binary: %s", settings.meshroom.binary)
    logger.info("Workspace: %s", settings.meshroom.workspace_dir)
    logger.info("Broker: %s:%s", settings.broker.host, settings.broker.port)
    logger.info("Queue: %s", settings.broker.queue_name)
    logger.info("=" * 60)

    try:
        # Connect to RabbitMQ
        await broker.connect()
        logger.info("Connected to RabbitMQ, waiting for jobs...")

        # Start consuming messages
        await broker.consume(process_message)

        # Keep running
        await asyncio.Future()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as exc:
        logger.error("Worker error: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        await broker.close()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")

