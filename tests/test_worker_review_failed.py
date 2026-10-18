import pytest
from complibot.db.models import Review
from complibot.db.session import SessionLocal
from complibot_worker.main import process_message
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_pipeline_failure_marks_review_failed_on_final_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def boom(*_a, **_k):
        raise RuntimeError("pipeline blew up")

    async def skip_dispatch(_settings, _body):
        return None

    async def noop_bucket(*_a, **_k):
        return None

    async def fake_put(*_a, **_k):
        return None

    monkeypatch.setattr("complibot_worker.main.run_mock_review", boom)
    monkeypatch.setattr("complibot.routers.projects.dispatch_review_job", skip_dispatch)
    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fake_put)

    from complibot.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/dev-login",
            json={"email": "fail-pipe@complibot.local", "name": "Fail"},
        )
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "F", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=headers,
            json={"title": "t", "text": "sub-processor personal data breach notify"},
        )
        doc_id = pasted.json()["id"]
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]

    async with SessionLocal() as db:
        row = await db.execute(select(Review).where(Review.id == review_id))
        tenant_id = row.scalar_one().tenant_id

    body = {"reviewId": review_id, "tenantId": tenant_id}
    with pytest.raises(RuntimeError):
        await process_message(body, final_attempt=True)

    async with SessionLocal() as db:
        row = await db.execute(select(Review).where(Review.id == review_id))
        assert row.scalar_one().status == "failed"
