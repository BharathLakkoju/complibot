import json
from typing import Any

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from complibot.config import Settings
from complibot.exceptions import ServiceUnavailable


def _client_kwargs(settings: Settings) -> dict[str, Any]:
    kw: dict[str, Any] = {
        "region_name": settings.aws_region,
        "config": Config(signature_version="s3v4"),
    }
    if settings.aws_endpoint_url:
        kw["endpoint_url"] = settings.aws_endpoint_url
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kw["aws_access_key_id"] = settings.aws_access_key_id
        kw["aws_secret_access_key"] = settings.aws_secret_access_key
    return kw


def s3_client_kwargs(settings: Settings) -> dict[str, Any]:
    """Boto3 kwargs for S3 clients (presign, get_object, bucket setup).

    Real AWS: force regional virtual-hosted URLs so presigned PUTs match the
    bucket region (avoids 307 from the global s3.amazonaws.com endpoint).
    LocalStack/custom endpoint: leave path-style URLs unchanged.
    """
    kw = _client_kwargs(settings)
    if not settings.aws_endpoint_url:
        kw["config"] = Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        )
    return kw


def _bucket_missing(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code", "")
    return code in {"404", "NoSuchBucket", "NotFound"}


def presign_put_object_params(bucket: str, key: str, content_type: str) -> dict[str, str]:
    """Params passed to S3 put_object presign — shared with offline signer regression tests."""
    return {"Bucket": bucket, "Key": key, "ContentType": content_type}


async def maybe_ensure_documents_bucket(settings: Settings) -> None:
    """LocalStack/dev only: verify or create bucket. Production buckets are Terraform-managed."""
    if not settings.aws_endpoint_url:
        return
    await ensure_bucket(settings)


async def ensure_bucket(settings: Settings) -> None:
    """Verify the documents bucket exists. Auto-create only against LocalStack-style endpoints."""
    session = aioboto3.Session()
    async with session.client("s3", **s3_client_kwargs(settings)) as s3:
        try:
            await s3.head_bucket(Bucket=settings.s3_bucket)
        except ClientError as exc:
            if not _bucket_missing(exc):
                # HeadBucket is authorized via s3:ListBucket on the bucket ARN in production IAM.
                raise ServiceUnavailable("Document storage is unavailable.") from exc
            if not settings.aws_endpoint_url:
                raise ServiceUnavailable("Document storage is not configured.") from exc
            await s3.create_bucket(Bucket=settings.s3_bucket)


async def get_object_bytes(settings: Settings, key: str) -> bytes:
    session = aioboto3.Session()
    async with session.client("s3", **s3_client_kwargs(settings)) as s3:
        try:
            resp = await s3.get_object(Bucket=settings.s3_bucket, Key=key)
        except ClientError as exc:
            raise ServiceUnavailable("Could not read uploaded document.") from exc
        body = await resp["Body"].read()
        return bytes(body)


async def put_object_bytes(settings: Settings, key: str, data: bytes, content_type: str) -> None:
    session = aioboto3.Session()
    async with session.client("s3", **s3_client_kwargs(settings)) as s3:
        try:
            await s3.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except ClientError as exc:
            raise ServiceUnavailable("Could not store document content.") from exc


async def presign_put(settings: Settings, key: str, content_type: str) -> str:
    session = aioboto3.Session()
    async with session.client("s3", **s3_client_kwargs(settings)) as s3:
        try:
            return await s3.generate_presigned_url(
                "put_object",
                Params=presign_put_object_params(settings.s3_bucket, key, content_type),
                ExpiresIn=settings.presign_ttl_seconds,
            )
        except ClientError as exc:
            raise ServiceUnavailable("Could not prepare upload URL.") from exc


async def enqueue_review_job(settings: Settings, body: dict[str, Any]) -> None:
    session = aioboto3.Session()
    async with session.client("sqs", **_client_kwargs(settings)) as sqs:
        await sqs.send_message(QueueUrl=settings.sqs_queue_url, MessageBody=json.dumps(body))
