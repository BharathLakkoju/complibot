"""Upload (S3-backed) document path must match paste for review findings."""

import asyncio
from typing import Any

import pytest
from complibot.main import app
from httpx import ASGITransport, AsyncClient

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


@pytest.mark.asyncio
async def test_upload_complete_stores_normalized_text_and_review_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s3_store: dict[str, bytes] = {}

    async def noop_bucket(*_a: Any, **_k: Any) -> None:
        return None

    async def fake_presign(_settings: Any, key: str, content_type: str) -> str:
        return f"https://mock-s3.test/{key}?ct={content_type}"

    async def fake_get_object(_settings: Any, key: str) -> bytes:
        if key not in s3_store:
            raise AssertionError(f"missing s3 object {key}")
        return s3_store[key]

    async def fake_put(_settings: Any, key: str, data: bytes, _ct: str) -> None:
        s3_store[key] = data

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)
    monkeypatch.setattr("complibot.routers.documents.get_object_bytes", fake_get_object)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fake_put)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "upload-review@example.com")
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
        assert presign.status_code == 200
        upload_doc_id = presign.json()["documentId"]
        s3_key = presign.json()["s3Key"]
        s3_store[s3_key] = SAMPLE_TEXT.encode("utf-8")

        complete = await client.post(f"/v1/documents/{upload_doc_id}/complete", headers=headers)
        assert complete.status_code == 200
        assert complete.json()["status"] == "parsed"

        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [upload_doc_id]},
        )
        assert review.status_code == 200
        review_id = review.json()["id"]

        findings: list[dict[str, Any]] = []
        for _ in range(40):
            res = await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)
            findings = res.json()
            status = (await client.get(f"/v1/reviews/{review_id}", headers=headers)).json()[
                "status"
            ]
            if status == "completed" and findings:
                break
            await asyncio.sleep(0.05)

        assert findings, "uploaded document review produced no findings"
        snap = await client.get(f"/v1/reviews/{review_id}/snapshot", headers=headers)
        doc_text = snap.json()["documents"][upload_doc_id]
        assert SAMPLE_TEXT in doc_text


@pytest.mark.asyncio
async def test_paste_and_upload_produce_same_finding_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s3_store: dict[str, bytes] = {}

    async def noop_bucket(*_a: Any, **_k: Any) -> None:
        return None

    async def fake_presign(_settings: Any, key: str, content_type: str) -> str:
        return f"https://mock-s3.test/{key}"

    async def fake_get_object(_settings: Any, key: str) -> bytes:
        return s3_store[key]

    async def fake_put(_settings: Any, key: str, data: bytes, _ct: str) -> None:
        s3_store[key] = data

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)
    monkeypatch.setattr("complibot.routers.documents.get_object_bytes", fake_get_object)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", fake_put)

    async def findings_for_doc(
        client: AsyncClient, headers: dict[str, str], doc_id: str, pid: str
    ) -> int:
        review = await client.post(
            f"/v1/projects/{pid}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]
        for _ in range(40):
            status = (await client.get(f"/v1/reviews/{review_id}", headers=headers)).json()[
                "status"
            ]
            count = len(
                (await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)).json()
            )
            if status == "completed":
                return count
            await asyncio.sleep(0.05)
        return 0

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "parity@example.com")
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
        paste_id = pasted.json()["id"]
        paste_count = await findings_for_doc(client, headers, paste_id, project_id)

        presign = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "policy.txt",
                "contentType": "text/plain",
                "sizeBytes": len(SAMPLE_TEXT.encode()),
            },
        )
        s3_key = presign.json()["s3Key"]
        upload_id = presign.json()["documentId"]
        s3_store[s3_key] = SAMPLE_TEXT.encode("utf-8")
        await client.post(f"/v1/documents/{upload_id}/complete", headers=headers)
        upload_count = await findings_for_doc(client, headers, upload_id, project_id)

    assert paste_count > 0
    assert upload_count == paste_count
