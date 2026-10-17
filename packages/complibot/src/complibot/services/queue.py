import asyncio
import logging

from complibot.config import Settings
from complibot.exceptions import ServiceUnavailable
from complibot.services.aws import enqueue_review_job

logger = logging.getLogger(__name__)

_inline_tasks: set[asyncio.Task[None]] = set()


async def dispatch_review_job(settings: Settings, body: dict[str, str]) -> None:
    if settings.inline_worker:
        from complibot_worker.main import process_message

        task = asyncio.create_task(process_message(body))
        _inline_tasks.add(task)
        task.add_done_callback(_inline_tasks.discard)
        return
    try:
        await enqueue_review_job(settings, body)
    except Exception:
        logger.exception("SQS enqueue failed")
        raise ServiceUnavailable("Review queue unavailable; try again later") from None
