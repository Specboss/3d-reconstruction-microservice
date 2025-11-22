"""MinIO/S3 storage implementation."""

from pathlib import Path

import httpx
from aiobotocore.session import get_session

from app.core.logger import get_logger
from app.core.settings import AwsConfigModel
from app.core.storage.base.storage import BaseStorage


class MinioStorage(BaseStorage):
    """MinIO/S3 storage provider implementation."""

    def __init__(self, config: AwsConfigModel, access_key: str, secret_key: str) -> None:
        """
        Initialize MinIO storage.

        Args:
            config: AWS/MinIO configuration
            access_key: Access key ID
            secret_key: Secret access key
        """
        self.config = config
        self.access_key = access_key
        self.secret_key = secret_key
        self.logger = get_logger(self.__class__.__name__)

    async def upload_file(self, local_path: Path, remote_key: str) -> str:
        """Upload file to MinIO bucket."""
        session = get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.config.default_region,
            use_ssl=self.config.use_ssl,
        ) as client:
            with local_path.open("rb") as file_data:
                await client.put_object(
                    Bucket=self.config.bucket_name,
                    Key=remote_key,
                    Body=file_data.read(),
                )

        url = f"{self.config.endpoint_url}/{self.config.bucket_name}/{remote_key}"
        self.logger.info("Uploaded %s to %s", local_path, url)
        return url

    async def download_file(self, remote_key: str, local_path: Path) -> None:
        """Download file from MinIO bucket."""
        session = get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.config.default_region,
            use_ssl=self.config.use_ssl,
        ) as client:
            response = await client.get_object(
                Bucket=self.config.bucket_name,
                Key=remote_key,
            )
            async with response["Body"] as stream:
                data = await stream.read()
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(data)

        self.logger.info("Downloaded %s to %s", remote_key, local_path)

    async def download_url(self, url: str, local_path: Path) -> None:
        """Download file from HTTP(S) URL."""
        self.logger.info("Downloading %s to %s", url, local_path)
        
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with local_path.open("wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        self.logger.info("Downloaded %s (%d bytes)", local_path.name, local_path.stat().st_size)

    async def get_presigned_url(self, remote_key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for MinIO object."""
        session = get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.config.default_region,
            use_ssl=self.config.use_ssl,
        ) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.config.bucket_name, "Key": remote_key},
                ExpiresIn=expires_in,
            )

        return url

    async def delete_file(self, remote_key: str) -> None:
        """Delete file from MinIO bucket."""
        session = get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.config.default_region,
            use_ssl=self.config.use_ssl,
        ) as client:
            await client.delete_object(
                Bucket=self.config.bucket_name,
                Key=remote_key,
            )

        self.logger.info("Deleted %s from storage", remote_key)