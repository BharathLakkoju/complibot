import json
from typing import Any

import aioboto3
from botocore.config import Config
from complibot.config import Settings


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


async def ensure_bucket(settings: Settings) -> None:
    session = aioboto3.Session()
    async with session.client("s3", **_client_kwargs(settings)) as s3:
        buckets = await s3.list_buckets()
        names = [b["Name"] for b in buckets.get("Buckets", [])]
        if settings.s3_bucket not in names:
            await s3.create_bucket(Bucket=settings.s3_bucket)


async def get_object_bytes(settings: Settings, key: str) -> bytes:
    session = aioboto3.Session()
    async with session.client("s3", **_client_kwargs(settings)) as s3:
        resp = await s3.get_object(Bucket=settings.s3_bucket, Key=key)
        body = await resp["Body"].read()
        return bytes(body)


async def presign_put(settings: Settings, key: str, content_type: str) -> str:
    session = aioboto3.Session()
    async with session.client("s3", **_client_kwargs(settings)) as s3:
        return await s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=settings.presign_ttl_seconds,
        )


async def enqueue_review_job(settings: Settings, body: dict[str, Any]) -> None:
    session = aioboto3.Session()
    async with session.client("sqs", **_client_kwargs(settings)) as sqs:
        await sqs.send_message(QueueUrl=settings.sqs_queue_url, MessageBody=json.dumps(body))
