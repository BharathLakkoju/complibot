"""Regression: policy-style GDPR text must yield verified mock findings (QA round 4)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from complibot.main import app
from httpx import ASGITransport, AsyncClient

QA_POLICY_PATH = Path(__file__).resolve().parent / "fixtures" / "test-compliance-policy.txt"
QA_POLICY_TEXT = QA_POLICY_PATH.read_text(encoding="utf-8")


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    login = await client.post(
        "/v1/auth/dev-login",
        json={"email": email, "name": "QA Policy"},
    )
    assert login.status_code == 200
    token = login.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def _wait_for_completed_review(
    client: AsyncClient, headers: dict[str, str], review_id: str
) -> dict:
    status = "queued"
    for _ in range(40):
        res = await client.get(f"/v1/reviews/{review_id}", headers=headers)
        assert res.status_code == 200
        status = res.json()["status"]
        if status == "completed":
            break
        await asyncio.sleep(0.1)
    assert status == "completed"
    return res.json()


def _patch_policy_storage(monkeypatch: pytest.MonkeyPatch, raw: bytes) -> None:
    async def fake_get_object(_settings, key: str) -> bytes:
        assert key
        return raw

    async def fake_presign(_settings, key, content_type):
        assert content_type == "text/plain"
        return "https://s3.example/upload"

    async def noop_put(*_a, **_k):
        return None

    async def noop_bucket(*_a, **_k):
        return None

    monkeypatch.setattr("complibot.routers.documents.get_object_bytes", fake_get_object)
    monkeypatch.setattr("complibot.services.document_text.get_object_bytes", fake_get_object)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", noop_put)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)
    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)


def _assert_verified_findings(findings: list[dict], doc_text: str, document_id: str) -> None:
    assert len(findings) >= 1
    for finding in findings:
        for cite in finding["citations"]:
            assert cite["documentId"] == document_id
            quote = cite["quote"]
            assert quote == doc_text[cite["charStart"] : cite["charEnd"]]
            assert quote in doc_text


@pytest.mark.asyncio
async def test_qa_policy_upload_path_produces_verified_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = QA_POLICY_TEXT.encode("utf-8")
    _patch_policy_storage(monkeypatch, raw)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client, "qa-upload@complibot.local")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "QA GDPR", "frameworkCodes": ["GDPR"]},
        )
        assert project.status_code == 200
        project_id = project.json()["id"]

        presign = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "test-compliance-policy.txt",
                "contentType": "text/plain",
                "sizeBytes": len(raw),
            },
        )
        assert presign.status_code == 200
        doc_id = presign.json()["documentId"]

        complete = await client.post(f"/v1/documents/{doc_id}/complete", headers=headers)
        assert complete.status_code == 200
        assert complete.json()["status"] == "parsed"

        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        assert review.status_code == 200
        review_id = review.json()["id"]

        await _wait_for_completed_review(client, headers, review_id)

        findings_res = await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)
        assert findings_res.status_code == 200
        findings = findings_res.json()

        snap = await client.get(f"/v1/reviews/{review_id}/snapshot", headers=headers)
        assert snap.status_code == 200
        snap_body = snap.json()
        doc_text = snap_body["documents"][doc_id]
        assert doc_text == QA_POLICY_TEXT
        assert snap_body.get("documentErrors", {}).get(doc_id) in (None, "")

        _assert_verified_findings(findings, doc_text, doc_id)


async def _run_review_for_text(
    client: AsyncClient,
    headers: dict[str, str],
    project_id: str,
    doc_id: str,
) -> list[dict]:
    review = await client.post(
        f"/v1/projects/{project_id}/reviews",
        headers=headers,
        json={"documentIds": [doc_id]},
    )
    review_id = review.json()["id"]
    await _wait_for_completed_review(client, headers, review_id)
    return (await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)).json()


@pytest.mark.asyncio
async def test_qa_policy_paste_matches_upload_findings_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = QA_POLICY_TEXT.encode("utf-8")
    _patch_policy_storage(monkeypatch, raw)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client, "qa-parity@complibot.local")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "QA parity", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]

        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=headers,
            json={"title": "test-compliance-policy", "text": QA_POLICY_TEXT},
        )
        paste_doc_id = pasted.json()["id"]
        paste_findings = await _run_review_for_text(client, headers, project_id, paste_doc_id)

        presign = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "test-compliance-policy.txt",
                "contentType": "text/plain",
                "sizeBytes": len(raw),
            },
        )
        upload_doc_id = presign.json()["documentId"]
        await client.post(f"/v1/documents/{upload_doc_id}/complete", headers=headers)
        upload_findings = await _run_review_for_text(client, headers, project_id, upload_doc_id)

        assert len(paste_findings) >= 1
        assert len(paste_findings) == len(upload_findings)
        assert sorted(f["controlRef"] for f in paste_findings) == sorted(
            f["controlRef"] for f in upload_findings
        )


@pytest.mark.asyncio
async def test_qa_policy_keyword_slice_repro_pre_fix_behavior() -> None:
    """Documents why the first-five DPA-only keywords yielded zero matches on QA text."""
    from complibot_worker.pipeline.mock_review import _find_quote

    first_five_needles = [
        "annex",
        "instructions",
        "confidentiality",
        "encryption",
        "sub-processor",
    ]
    assert _find_quote(QA_POLICY_TEXT, first_five_needles) is None
    assert _find_quote(QA_POLICY_TEXT, ["retention"]) is not None
