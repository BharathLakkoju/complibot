"""Worker entrypoint used by SQS (INLINE_WORKER=false) must fail reviews with events."""

import pytest
from complibot.db.models import Document, Review, ReviewEvent
from complibot.db.session import SessionLocal
from complibot_worker.main import process_message
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_document_text_error_on_process_message_emits_failed_status_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def noop_bucket(*_a, **_k):
        return None

    async def fail_put(*_a, **_k):
        return None

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fail_put)

    async def skip_dispatch(_settings, _body):
        return None

    monkeypatch.setattr("complibot.services.queue.dispatch_review_job", skip_dispatch)

    from complibot.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post(
            "/v1/auth/register",
            json={"email": "sqs-fail@example.com", "password": "securepass1"},
        )
        headers = {"Authorization": f"Bearer {reg.json()['accessToken']}"}
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=headers,
            json={"title": "t", "text": "sub-processor breach"},
        )
        doc_id = pasted.json()["id"]
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]

    async with SessionLocal() as db:
        doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        doc.normalized_text = None
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        tenant_id = review_row.tenant_id
        review_row.status = "queued"
        await db.commit()

    async def empty_s3(_settings, key):
        return b""

    monkeypatch.setattr("complibot.services.document_text.get_object_bytes", empty_s3)

    await process_message(
        {"reviewId": review_id, "tenantId": tenant_id},
        final_attempt=True,
    )

    async with SessionLocal() as db:
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        assert review_row.status == "failed"
        events = (
            await db.execute(
                select(ReviewEvent)
                .where(ReviewEvent.review_id == review_id, ReviewEvent.type == "review.status")
                .order_by(ReviewEvent.seq.desc())
            )
        ).scalars()
        failed_payload = next(
            (e.payload for e in events if e.payload.get("status") == "failed"),
            None,
        )
        assert failed_payload is not None
        assert failed_payload["failure"]["errorCode"] == "empty_text"
        assert failed_payload["failure"]["message"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        detail = await client.get(f"/v1/reviews/{review_id}", headers=headers)
        assert detail.json()["status"] == "failed"
        assert detail.json()["failure"]["message"]
