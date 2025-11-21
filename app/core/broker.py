"""RabbitMQ broker service for job queue management."""

from __future__ import annotations

import json
from typing import Any, Callable

import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
)

from app.core.logger import get_logger
from app.core.settings import BrokerConfigModel


class RabbitMQBroker:
    """RabbitMQ connection manager and message broker."""

    def __init__(self, config: BrokerConfigModel) -> None:
        """
        Initialize broker with configuration.

        Args:
            config: Broker configuration model
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchange: AbstractExchange | None = None
        self._queue: AbstractQueue | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ server."""
        if self._connection and not self._connection.is_closed:
            self.logger.debug("Already connected to RabbitMQ")
            return

        self.logger.info(
            "Connecting to RabbitMQ at %s:%s",
            self.config.host,
            self.config.port,
        )

        self._connection = await aio_pika.connect_robust(
            self.config.url,
            timeout=30,
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self.config.prefetch_count)

        # Declare exchange
        self._exchange = await self._channel.declare_exchange(
            self.config.exchange_name,
            ExchangeType.DIRECT,
            durable=True,
        )

        # Declare queue
        self._queue = await self._channel.declare_queue(
            self.config.queue_name,
            durable=True,
        )

        # Bind queue to exchange
        await self._queue.bind(self._exchange, routing_key=self.config.queue_name)

        self.logger.info("Connected to RabbitMQ queue: %s", self.config.queue_name)

    async def publish(self, message_data: dict[str, Any]) -> None:
        """
        Publish message to queue.

        Args:
            message_data: Dictionary to publish as JSON

        Raises:
            RuntimeError: If not connected
        """
        if not self._exchange:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")

        message = Message(
            body=json.dumps(message_data).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self._exchange.publish(
            message,
            routing_key=self.config.queue_name,
        )

        job_id = message_data.get("job_id", "unknown")
        self.logger.info("Published job %s to queue", job_id)

    async def consume(
        self,
        callback: Callable[[AbstractIncomingMessage], Any],
    ) -> None:
        """
        Start consuming messages from queue.

        Args:
            callback: Async function to handle incoming messages
        """
        if not self._queue:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")

        self.logger.info("Starting to consume messages from queue...")
        await self._queue.consume(callback)

    async def close(self) -> None:
        """Close RabbitMQ connection gracefully."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self.logger.info("RabbitMQ connection closed")


__all__ = ["RabbitMQBroker"]

