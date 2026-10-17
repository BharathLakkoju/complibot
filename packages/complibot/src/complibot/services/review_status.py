from typing import Any

from complibot.db.models import Review
from complibot.services.events import append_review_event
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def set_review_status(
    db: AsyncSession,
    *,
    tenant_id: str,
    review_id: str,
    status: str,
    progress: dict[str, Any] | None = None,
    failure: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    res = await db.execute(
        select(Review).where(Review.id == review_id, Review.tenant_id == tenant_id)
    )
    review = res.scalar_one_or_none()
    if review is None:
        return
    review.status = status
    payload: dict[str, Any] = {
        "status": status,
        "progress": progress or {"stage": "assess", "done": 0, "total": 5},
    }
    if failure:
        payload["failure"] = failure
    if extra:
        payload.update(extra)
    await append_review_event(
        db,
        tenant_id=tenant_id,
        review_id=review_id,
        event_type="review.status",
        payload=payload,
    )
