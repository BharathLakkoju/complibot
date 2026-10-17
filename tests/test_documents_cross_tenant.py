import pytest
from complibot.main import app
from httpx import ASGITransport, AsyncClient


async def _register(client: AsyncClient, email: str) -> dict[str, str]:
    res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "securepass1"},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


@pytest.mark.asyncio
async def test_other_tenant_cannot_access_document_or_start_review() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        owner = await _register(client, "owner-doc@example.com")
        intruder = await _register(client, "intruder-doc@example.com")
        project = await client.post(
            "/v1/projects",
            headers=owner,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=owner,
            json={"title": "t", "text": "sub-processor breach notification"},
        )
        doc_id = pasted.json()["id"]
        list_intruder = await client.get(
            f"/v1/projects/{project_id}/documents",
            headers=intruder,
        )
        assert list_intruder.status_code == 404
        complete = await client.post(f"/v1/documents/{doc_id}/complete", headers=intruder)
        assert complete.status_code == 404
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=intruder,
            json={"documentIds": [doc_id]},
        )
        assert review.status_code == 404


@pytest.mark.asyncio
async def test_cannot_start_review_on_unparsed_document(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop_bucket(*_a, **_k):
        return None

    async def fake_presign(*_a, **_k):
        return "http://test.invalid/upload"

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "upload-only@example.com")
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
                "filename": "x.txt",
                "contentType": "text/plain",
                "sizeBytes": 10,
            },
        )
        doc_id = presign.json()["documentId"]
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        assert review.status_code == 400
