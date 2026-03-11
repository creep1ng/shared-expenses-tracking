from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import boto3
from botocore.config import Config as BotocoreConfig
from botocore.exceptions import ClientError

from app.core.config import Settings


class ObjectStorageNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class StoredObject:
    content: bytes
    content_type: str


class ObjectStorage(Protocol):
    def put_object(self, *, key: str, content: bytes, content_type: str) -> None: ...

    def get_object(self, *, key: str) -> StoredObject: ...

    def delete_object(self, *, key: str) -> None: ...


class InMemoryObjectStorage:
    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}

    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        self._objects[key] = StoredObject(content=content, content_type=content_type)

    def get_object(self, *, key: str) -> StoredObject:
        stored_object = self._objects.get(key)
        if stored_object is None:
            raise ObjectStorageNotFoundError
        return stored_object

    def delete_object(self, *, key: str) -> None:
        self._objects.pop(key, None)

    def clear(self) -> None:
        self._objects.clear()


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._region = settings.s3_region
        self._bucket_ready = False
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
            region_name=settings.s3_region,
            use_ssl=settings.s3_use_ssl,
            config=BotocoreConfig(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path" if settings.s3_force_path_style else "auto",
                },
            ),
        )

    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        self._ensure_bucket()
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    def get_object(self, *, key: str) -> StoredObject:
        self._ensure_bucket()
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if _is_not_found_error(exc):
                raise ObjectStorageNotFoundError from exc
            raise

        body = response["Body"].read()
        content_type = response.get("ContentType") or "application/octet-stream"
        return StoredObject(content=body, content_type=content_type)

    def delete_object(self, *, key: str) -> None:
        self._ensure_bucket()
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return

        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            if not _is_not_found_error(exc):
                raise

            create_bucket_kwargs: dict[str, Any] = {"Bucket": self._bucket}
            if self._region != "us-east-1":
                create_bucket_kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": self._region,
                }
            self._client.create_bucket(**create_bucket_kwargs)

        self._bucket_ready = True


def _is_not_found_error(exc: ClientError) -> bool:
    error_code = str(exc.response.get("Error", {}).get("Code", ""))
    return error_code in {"404", "NoSuchBucket", "NoSuchKey", "NotFound"}
