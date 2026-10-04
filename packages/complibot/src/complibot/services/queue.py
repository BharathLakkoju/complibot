import asyncio
import logging

from complibot.config import Settings
from complibot.services.aws import enqueue_review_job

logger = logging.getLogger(__name__)


async def dispatch_review_job(settings: Settings, body: dict[str, str]) -> None:
    if settings.inline_worker:
        from complibot_worker.main import process_message

        asyncio.create_task(process_message(body))
        return
    try:
        await enqueue_review_job(settings, body)
    except Exception:
        logger.warning("SQS unavailable; running review inline")
        from complibot_worker.main import process_message

        asyncio.create_task(process_message(body))
