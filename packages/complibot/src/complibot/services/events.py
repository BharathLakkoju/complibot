from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.db.models import Review, ReviewEvent
from complibot.ids import new_event_id
from complibot.ws.hub import review_hub


async def append_review_event(
    db: AsyncSession,
    *,
    tenant_id: str,
    review_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> ReviewEvent:
    result = await db.execute(select(Review).where(Review.id == review_id, Review.tenant_id == tenant_id))
    review = result.scalar_one()
    next_seq = int(review.last_seq) + 1
    event = ReviewEvent(
        id=new_event_id(),
        tenant_id=tenant_id,
        review_id=review_id,
        seq=next_seq,
        type=event_type,
        payload=payload,
        ts=datetime.now(UTC),
    )
    db.add(event)
    await db.execute(update(Review).where(Review.id == review_id).values(last_seq=next_seq))
    await db.flush()
    envelope = {
        "v": 1,
        "type": event_type,
        "id": event.id,
        "seq": next_seq,
        "reviewId": review_id,
        "ts": event.ts.isoformat().replace("+00:00", "Z"),
        "payload": payload,
    }
    await review_hub.broadcast(review_id, envelope)
    return event
