"""Regression: QA state parsed + empty DB text while S3 holds bytes."""

import asyncio
from typing import Any

import pytest
from complibot.db.models import Document, Review
from complibot.db.session import SessionLocal
from complibot.exceptions import ServiceUnavailable
from complibot.main import app
from complibot_worker.main import process_message
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

SAMPLE_TEXT = (
    "The Processor shall not engage another processor (sub-processor) without prior "
    "written authorisation. The Processor shall notify the Controller without undue "
    "delay after becoming aware of a personal data breach. Technical and organisational "
    "measures including encryption shall be implemented."
)


async def _register(client: AsyncClient, email: str) -> dict[str, str]:
    res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "securepass1"},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def _s3_mocks(monkeypatch: pytest.MonkeyPatch, s3_store: dict[str, bytes]) -> None:
    async def noop_bucket(*_a: Any, **_k: Any) -> None:
        return None

    async def fake_presign(_settings: Any, key: str, _ct: str) -> str:
        return f"https://mock/{key}"

    async def fake_get(_settings: Any, key: str) -> bytes:
        return s3_store[key]

    async def fake_put(_settings: Any, key: str, data: bytes, _ct: str) -> None:
        s3_store[key] = data

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)
    monkeypatch.setattr("complibot.routers.documents.get_object_bytes", fake_get)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fake_put)
    monkeypatch.setattr("complibot.services.document_text.get_object_bytes", fake_get)


@pytest.mark.asyncio
async def test_qa_parsed_null_text_complete_reingests_from_s3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pre-#8: complete short-circuited on status=parsed and never refilled normalized_text."""
    s3_store: dict[str, bytes] = {}
    _s3_mocks(monkeypatch, s3_store)

    async def skip_dispatch(_settings, _body):
        return None

    monkeypatch.setattr("complibot.services.queue.dispatch_review_job", skip_dispatch)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "qa-recomplete@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        presign = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "policy.txt",
                "contentType": "text/plain",
                "sizeBytes": len(SAMPLE_TEXT.encode()),
            },
        )
        doc_id = presign.json()["documentId"]
        s3_key = presign.json()["s3Key"]
        s3_store[s3_key] = SAMPLE_TEXT.encode("utf-8")
        await client.post(f"/v1/documents/{doc_id}/complete", headers=headers)

        async with SessionLocal() as db:
            doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
            doc.normalized_text = None
            await db.commit()

        again = await client.post(f"/v1/documents/{doc_id}/complete", headers=headers)
        assert again.status_code == 200

        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]

    async with SessionLocal() as db:
        tenant_id = (
            (await db.execute(select(Review).where(Review.id == review_id))).scalar_one().tenant_id
        )

    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "qa-recomplete@example.com", "password": "securepass1"},
        )
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        fc = len((await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)).json())
        assert fc > 0


@pytest.mark.asyncio
async def test_qa_parsed_null_text_worker_recovers_via_s3_not_zero_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s3_store: dict[str, bytes] = {}
    _s3_mocks(monkeypatch, s3_store)

    async def skip_dispatch(_settings, _body):
        return None

    monkeypatch.setattr("complibot.services.queue.dispatch_review_job", skip_dispatch)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "qa-worker@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        presign = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "policy.txt",
                "contentType": "text/plain",
                "sizeBytes": len(SAMPLE_TEXT.encode()),
            },
        )
        doc_id = presign.json()["documentId"]
        s3_key = presign.json()["s3Key"]
        s3_store[s3_key] = SAMPLE_TEXT.encode("utf-8")
        await client.post(f"/v1/documents/{doc_id}/complete", headers=headers)

        async with SessionLocal() as db:
            doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
            doc.normalized_text = None
            await db.commit()

        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]

    async with SessionLocal() as db:
        tenant_id = (
            (await db.execute(select(Review).where(Review.id == review_id))).scalar_one().tenant_id
        )

    await process_message(
        {"reviewId": review_id, "tenantId": tenant_id},
        final_attempt=True,
    )

    async with SessionLocal() as db:
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        assert review_row.status == "completed"
        doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        assert doc.normalized_text and "sub-processor" in doc.normalized_text

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "qa-worker@example.com", "password": "securepass1"},
        )
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        findings = await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)
        assert len(findings.json()) > 0


@pytest.mark.asyncio
async def test_snapshot_maps_s3_read_failure_to_document_errors_not_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s3_store: dict[str, bytes] = {}
    _s3_mocks(monkeypatch, s3_store)

    async def deny_get(*_a, **_k):
        raise ServiceUnavailable("Could not read uploaded document.")

    monkeypatch.setattr("complibot.services.document_text.get_object_bytes", deny_get)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "snap-err@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        presign = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "policy.txt",
                "contentType": "text/plain",
                "sizeBytes": len(SAMPLE_TEXT.encode()),
            },
        )
        doc_id = presign.json()["documentId"]
        s3_key = presign.json()["s3Key"]
        s3_store[s3_key] = SAMPLE_TEXT.encode("utf-8")
        await client.post(f"/v1/documents/{doc_id}/complete", headers=headers)

        async with SessionLocal() as db:
            doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
            doc.normalized_text = None
            await db.commit()

        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]
        snap = await client.get(f"/v1/reviews/{review_id}/snapshot", headers=headers)
        assert snap.status_code == 200
        body = snap.json()
        assert doc_id not in body.get("documents", {})
        assert "documentErrors" in body
        assert body["documentErrors"][doc_id]


@pytest.mark.asyncio
async def test_paste_succeeds_when_s3_mirror_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop_bucket(*_a, **_k):
        return None

    async def fail_put(*_a, **_k):
        raise ServiceUnavailable("Could not store document content.")

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fail_put)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "paste-no-s3@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=headers,
            json={"title": "policy", "text": SAMPLE_TEXT},
        )
        assert pasted.status_code == 200
        assert pasted.json()["status"] == "parsed"
        doc_id = pasted.json()["id"]
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]
        for _ in range(40):
            st = (await client.get(f"/v1/reviews/{review_id}", headers=headers)).json()["status"]
            if st == "completed":
                break
            await asyncio.sleep(0.05)
        snap = await client.get(f"/v1/reviews/{review_id}/snapshot", headers=headers)
        assert SAMPLE_TEXT in snap.json()["documents"][doc_id]
