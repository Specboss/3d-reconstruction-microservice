from typing import Annotated

from fastapi import Depends

from app.core.settings import AppSettings, get_settings
from app.core.storage.minio import MinioStorage


def get_storage(settings: Annotated[AppSettings, Depends(get_settings)]) -> MinioStorage:
    return MinioStorage(
        config=settings.aws,
        access_key=settings.secrets.aws_access_key_id,
        secret_key=settings.secrets.aws_secret_access_key,
    )
