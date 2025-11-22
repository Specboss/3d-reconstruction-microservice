from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.broker import RabbitMQBroker
from app.core.settings import AppSettings, get_settings
from app.core.storage.minio import MinioStorage


def get_broker(settings: Annotated[AppSettings, Depends(get_settings)]) -> RabbitMQBroker:
    return RabbitMQBroker(settings.broker)


def get_storage(settings: Annotated[AppSettings, Depends(get_settings)]) -> MinioStorage:
    return MinioStorage(
        config=settings.aws,
        access_key=settings.secrets.aws_access_key_id,
        secret_key=settings.secrets.aws_secret_access_key,
    )


async def verify_api_key(
        x_api_key: Annotated[str, Header()],
        settings: Annotated[AppSettings, Depends(get_settings)],
) -> None:
    if x_api_key != settings.secrets.x_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
