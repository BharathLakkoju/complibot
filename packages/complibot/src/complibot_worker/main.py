import asyncio
import json
import logging

import aioboto3
from botocore.config import Config
from sqlalchemy import select

from complibot.config import get_settings
from complibot.db.models import Review
from complibot.db.session import SessionLocal
from complibot_worker.pipeline.mock_review import run_mock_review

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


async def process_message(body: dict) -> None:
    settings = get_settings()
    review_id = body["reviewId"]
    tenant_id = body["tenantId"]
    async with SessionLocal() as db:
        res = await db.execute(select(Review).where(Review.id == review_id))
        review = res.scalar_one_or_none()
        if review is None:
            return
        review.status = "running"
        await db.commit()
    async with SessionLocal() as db:
        await run_mock_review(
            db,
            tenant_id=tenant_id,
            review_id=review_id,
            frameworks_path=settings.frameworks_path,
            token_streaming=settings.token_streaming_enabled,
        )


async def poll_loop() -> None:
    settings = get_settings()
    session = aioboto3.Session()
    client_kw = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_endpoint_url:
        client_kw["endpoint_url"] = settings.aws_endpoint_url
    logger.info("Worker polling %s", settings.sqs_queue_url)
    while True:
        try:
            async with session.client("sqs", **client_kw) as sqs:
                resp = await sqs.receive_message(
                    QueueUrl=settings.sqs_queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=10,
                    VisibilityTimeout=120,
                )
                for msg in resp.get("Messages", []):
                    body = json.loads(msg["Body"])
                    await process_message(body)
                    await sqs.delete_message(
                        QueueUrl=settings.sqs_queue_url,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
        except Exception:
            logger.exception("Worker poll error")
            await asyncio.sleep(2)


def main() -> None:
    asyncio.run(poll_loop())


if __name__ == "__main__":
    main()
