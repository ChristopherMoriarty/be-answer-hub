import logging
from typing import Any

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.settings import S3Settings

logger = logging.getLogger(__name__)


class MinioClient:
    """Async S3-compatible client for MinIO and AWS S3."""

    def __init__(self, settings: S3Settings) -> None:
        self._settings = settings
        self._session = aioboto3.Session()

    def _client_kwargs(self) -> dict[str, Any]:
        return {
            "service_name": "s3",
            "endpoint_url": self._settings.endpoint_url,
            "aws_access_key_id": self._settings.access_key,
            "aws_secret_access_key": self._settings.secret_key,
            "region_name": self._settings.region,
            "config": Config(s3={"addressing_style": "path"}),
        }

    async def ensure_bucket(self) -> None:
        """Create the configured bucket when it does not exist."""
        async with self._session.client(**self._client_kwargs()) as client:
            try:
                await client.head_bucket(Bucket=self._settings.bucket)
            except ClientError:
                await client.create_bucket(Bucket=self._settings.bucket)
                logger.info("Created S3 bucket %s", self._settings.bucket)

    async def put_object(self, key: str, body: bytes, *, content_type: str) -> None:
        """Upload an object to the configured bucket."""
        async with self._session.client(**self._client_kwargs()) as client:
            await client.put_object(
                Bucket=self._settings.bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )

    async def delete_object(self, key: str) -> None:
        """Delete an object from the configured bucket."""
        async with self._session.client(**self._client_kwargs()) as client:
            await client.delete_object(Bucket=self._settings.bucket, Key=key)

    async def get_object(self, key: str) -> bytes:
        """Download an object body from the configured bucket."""
        async with self._session.client(**self._client_kwargs()) as client:
            response = await client.get_object(Bucket=self._settings.bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def presigned_get_url(
        self,
        key: str,
        *,
        expires_in: int | None = None,
    ) -> str:
        """Return a temporary download URL for an object."""
        ttl = expires_in if expires_in is not None else self._settings.presigned_ttl
        async with self._session.client(**self._client_kwargs()) as client:
            return await client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self._settings.bucket, "Key": key},
                ExpiresIn=ttl,
            )
