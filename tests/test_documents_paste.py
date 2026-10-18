import pytest
from complibot.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_paste_document_and_list(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop_bucket(*_a, **_k):
        return None

    async def fake_put(*_a, **_k):
        return None

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fake_put)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/register",
            json={"email": "doc@example.com", "password": "securepass1"},
        )
        token = login.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "Docs", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=headers,
            json={"title": "policy", "text": "record of processing activities"},
        )
        assert pasted.status_code == 200
        assert pasted.json()["status"] == "parsed"
        listed = await client.get(f"/v1/projects/{project_id}/documents", headers=headers)
        assert listed.status_code == 200
        assert len(listed.json()) == 1
