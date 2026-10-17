import asyncio
import contextlib
import json
import logging
from typing import Any

import aioboto3
from complibot.config import get_settings
from complibot.db.models import Review
from complibot.db.session import SessionLocal
from complibot.services.review_status import set_review_status
from sqlalchemy import select

from complibot_worker.pipeline.mock_review import run_mock_review

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

VISIBILITY_SECONDS = 120
HEARTBEAT_INTERVAL_SEC = 40
# Must match maxReceiveCount on the SQS redrive policy (infra/terraform/envs/demo/sqs.tf).
MAX_RECEIVES = 3


async def process_message(body: dict[str, Any], *, final_attempt: bool = False) -> None:
    settings = get_settings()
    review_id = body["reviewId"]
    tenant_id = body["tenantId"]
    async with SessionLocal() as db:
        res = await db.execute(
            select(Review).where(Review.id == review_id, Review.tenant_id == tenant_id)
        )
        review = res.scalar_one_or_none()
        if review is None:
            return
        if review.status == "completed":
            logger.info("Review %s already completed; skipping duplicate job", review_id)
            return
        await set_review_status(
            db,
            tenant_id=tenant_id,
            review_id=review_id,
            status="running",
            progress={"stage": "ingest", "done": 0, "total": 5},
        )
        await db.commit()
    try:
        async with SessionLocal() as db:
            await run_mock_review(
                db,
                tenant_id=tenant_id,
                review_id=review_id,
                frameworks_path=settings.frameworks_path,
                token_streaming=settings.token_streaming_enabled,
            )
    except Exception:
        async with SessionLocal() as db:
            res = await db.execute(
                select(Review).where(Review.id == review_id, Review.tenant_id == tenant_id)
            )
            review = res.scalar_one_or_none()
            if review is not None and review.status in ("running", "queued"):
                if final_attempt:
                    await set_review_status(
                        db,
                        tenant_id=tenant_id,
                        review_id=review_id,
                        status="failed",
                        progress={"stage": "assess", "done": 0, "total": 5},
                        failure={
                            "stage": "assess",
                            "errorCode": "pipeline_error",
                            "retryable": False,
                        },
                    )
                else:
                    review.status = "queued"
                await db.commit()
        raise


async def _visibility_heartbeat(
    sqs: Any,
    queue_url: str,
    receipt_handle: str,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)
        if stop.is_set():
            break
        try:
            await sqs.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=VISIBILITY_SECONDS,
            )
        except Exception:
            logger.warning("SQS visibility heartbeat failed", exc_info=True)


async def _handle_sqs_message(sqs: Any, queue_url: str, msg: dict[str, Any]) -> None:
    receipt = msg["ReceiptHandle"]
    stop = asyncio.Event()
    heartbeat = asyncio.create_task(_visibility_heartbeat(sqs, queue_url, receipt, stop))
    try:
        body = json.loads(msg["Body"])
        receives = int(msg.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
        await process_message(body, final_attempt=receives >= MAX_RECEIVES)
        await sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
    except Exception:
        logger.exception("Failed processing SQS message")
    finally:
        stop.set()
        heartbeat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat


async def poll_loop() -> None:
    settings = get_settings()
    session = aioboto3.Session()
    client_kw: dict[str, str] = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        client_kw["endpoint_url"] = settings.aws_endpoint_url
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kw["aws_access_key_id"] = settings.aws_access_key_id
        client_kw["aws_secret_access_key"] = settings.aws_secret_access_key
    logger.info("Worker polling %s", settings.sqs_queue_url)
    while True:
        try:
            async with session.client("sqs", **client_kw) as sqs:
                resp = await sqs.receive_message(
                    QueueUrl=settings.sqs_queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=10,
                    VisibilityTimeout=VISIBILITY_SECONDS,
                    AttributeNames=["ApproximateReceiveCount"],
                )
                for msg in resp.get("Messages", []):
                    await _handle_sqs_message(sqs, settings.sqs_queue_url, msg)
        except Exception:
            logger.exception("Worker poll error")
            await asyncio.sleep(2)


def main() -> None:
    asyncio.run(poll_loop())


if __name__ == "__main__":
    main()
