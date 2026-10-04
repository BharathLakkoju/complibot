import json
from typing import Any

import aioboto3
from botocore.config import Config

from complibot.config import Settings


def _client_kwargs(settings: Settings) -> dict[str, Any]:
    kw: dict[str, Any] = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "config": Config(signature_version="s3v4"),
    }
    if settings.aws_endpoint_url:
        kw["endpoint_url"] = settings.aws_endpoint_url
    return kw


async def ensure_bucket(settings: Settings) -> None:
    session = aioboto3.Session()
    async with session.client("s3", **_client_kwargs(settings)) as s3:
        buckets = await s3.list_buckets()
        names = [b["Name"] for b in buckets.get("Buckets", [])]
        if settings.s3_bucket not in names:
            await s3.create_bucket(Bucket=settings.s3_bucket)


async def presign_put(settings: Settings, key: str, content_type: str) -> str:
    session = aioboto3.Session()
    async with session.client("s3", **_client_kwargs(settings)) as s3:
        return await s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=3600,
        )


async def enqueue_review_job(settings: Settings, body: dict[str, Any]) -> None:
    session = aioboto3.Session()
    async with session.client("sqs", **_client_kwargs(settings)) as sqs:
        await sqs.send_message(QueueUrl=settings.sqs_queue_url, MessageBody=json.dumps(body))
