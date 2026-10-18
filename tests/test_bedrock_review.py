"""Bedrock LLM provider: parsing, citation gating, and failure paths."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
from complibot.config import get_settings
from complibot.db.models import Document, FindingRow, Review
from complibot.db.session import SessionLocal
from complibot.services.queue import _inline_tasks
from complibot_worker.main import process_message
from complibot_worker.pipeline.bedrock_review import (
    BedrockReviewError,
    _parse_findings_payload,
)
from complibot_worker.pipeline.citations import locate_verified_citation
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

QA_POLICY_PATH = Path(__file__).resolve().parent / "fixtures" / "test-compliance-policy.txt"
QA_POLICY_TEXT = QA_POLICY_PATH.read_text(encoding="utf-8")
DPA_QUOTE = "Data Processing Agreement (DPA)"
GDPR_VENDOR_REF = "Art. 28(3)"


def test_locate_verified_citation_exact_slice() -> None:
    text = "before " + DPA_QUOTE + " after"
    span = locate_verified_citation(text, DPA_QUOTE)
    assert span is not None
    start, end, quote = span
    assert quote == text[start:end]
    assert quote == DPA_QUOTE


def test_parse_findings_payload_rejects_invalid_json() -> None:
    with pytest.raises(BedrockReviewError) as exc:
        _parse_findings_payload("not json")
    assert exc.value.code == "bedrock_malformed_output"


def test_parse_findings_payload_strips_code_fence() -> None:
    raw = '```json\n{"findings": [{"controlRef": "Art. 28(3)"}]}\n```'
    items = _parse_findings_payload(raw)
    assert len(items) == 1


class _FakeBedrockClient:
    def __init__(self, payload: dict | None = None, error: ClientError | None = None) -> None:
        self._payload = payload
        self._error = error

    def converse(self, **_kwargs: object) -> dict:
        if self._error is not None:
            raise self._error
        assert self._payload is not None
        return {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(self._payload)}],
                }
            }
        }


def _valid_findings_payload() -> dict:
    return {
        "findings": [
            {
                "controlRef": GDPR_VENDOR_REF,
                "kind": "partial",
                "severity": "medium",
                "quote": DPA_QUOTE,
                "title": "Vendor DPA required",
                "rationale": "The policy requires a DPA before vendor onboarding.",
                "remediationSummary": "Ensure DPAs are executed before access.",
            },
            {
                "controlRef": "Art. 999",
                "kind": "partial",
                "severity": "high",
                "quote": DPA_QUOTE,
                "title": "Unknown control",
                "rationale": "Should be discarded.",
            },
            {
                "controlRef": GDPR_VENDOR_REF,
                "kind": "partial",
                "severity": "high",
                "quote": "this text is not in the document",
                "title": "Bad quote",
                "rationale": "Should be discarded.",
            },
            {
                "controlRef": GDPR_VENDOR_REF,
                "kind": "not-a-kind",
                "severity": "high",
                "quote": DPA_QUOTE,
                "title": "Bad kind",
                "rationale": "Should be discarded.",
            },
        ]
    }


async def _drain_inline_worker() -> None:
    if _inline_tasks:
        await asyncio.gather(*list(_inline_tasks), return_exceptions=True)
        _inline_tasks.clear()


@pytest.mark.asyncio
async def test_bedrock_review_publishes_verified_findings_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()

    async def skip_dispatch(_settings, _body):
        return None

    async def noop_bucket(*_a, **_k):
        return None

    async def noop_put(*_a, **_k):
        return None

    async def fake_get_object(_settings, _key: str) -> bytes:
        return QA_POLICY_TEXT.encode("utf-8")

    monkeypatch.setattr("complibot.services.queue.dispatch_review_job", skip_dispatch)
    monkeypatch.setattr("complibot.routers.projects.dispatch_review_job", skip_dispatch)
    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", noop_put)
    monkeypatch.setattr("complibot.services.document_text.get_object_bytes", fake_get_object)
    monkeypatch.setattr("complibot.routers.auth._rate_limit_client", lambda _ip: None)

    fake = _FakeBedrockClient(_valid_findings_payload())
    monkeypatch.setattr(
        "complibot_worker.pipeline.bedrock_review.create_bedrock_runtime_client",
        lambda _s: fake,
    )

    from complibot.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/dev-login",
            json={"email": "bedrock-ok@complibot.local", "name": "Bedrock"},
        )
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "Bedrock GDPR", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        pasted = await client.post(
            f"/v1/projects/{project_id}/documents/paste",
            headers=headers,
            json={"title": "policy", "text": QA_POLICY_TEXT},
        )
        assert pasted.status_code == 200
        doc_id = pasted.json()["id"]
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]

    async with SessionLocal() as db:
        doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        if not doc.normalized_text:
            doc.normalized_text = QA_POLICY_TEXT
        row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        tenant_id = row.tenant_id
        row.status = "queued"
        await db.execute(delete(FindingRow).where(FindingRow.review_id == review_id))
        await db.commit()

    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    await _drain_inline_worker()
    get_settings.cache_clear()

    async with SessionLocal() as db:
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        assert review_row.status == "completed"
        findings = (
            (await db.execute(select(FindingRow).where(FindingRow.review_id == review_id)))
            .scalars()
            .all()
        )
        bedrock_rows = [
            f
            for f in findings
            if f.payload.get("provenance", {}).get("provider") == "bedrock"
        ]
        assert len(bedrock_rows) == 1
        payload = bedrock_rows[0].payload
        assert payload["controlRef"] == GDPR_VENDOR_REF
        assert payload["provenance"]["provider"] == "bedrock"
        cite = payload["citations"][0]
        assert cite["quote"] == DPA_QUOTE
        assert cite["quote"] == QA_POLICY_TEXT[cite["charStart"] : cite["charEnd"]]


@pytest.mark.asyncio
async def test_bedrock_access_denied_marks_review_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()

    async def noop_bucket(*_a, **_k):
        return None

    async def noop_put(*_a, **_k):
        return None

    async def fake_get_object(_settings, _key: str) -> bytes:
        return QA_POLICY_TEXT.encode("utf-8")

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.put_object_bytes", noop_put)
    monkeypatch.setattr("complibot.services.document_text.get_object_bytes", fake_get_object)
    monkeypatch.setattr("complibot.services.queue.dispatch_review_job", lambda _s, _b: None)

    err = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "not allowed"}},
        "Converse",
    )
    fake = _FakeBedrockClient(error=err)
    monkeypatch.setattr(
        "complibot_worker.pipeline.bedrock_review.create_bedrock_runtime_client",
        lambda _s: fake,
    )
    monkeypatch.setattr("complibot.services.queue.dispatch_review_job", lambda _s, _b: None)
    monkeypatch.setattr("complibot.routers.auth._rate_limit_client", lambda _ip: None)

    from complibot.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/dev-login",
            json={"email": "bedrock-denied@complibot.local", "name": "Denied"},
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
            json={"title": "t", "text": QA_POLICY_TEXT},
        )
        assert pasted.status_code == 200
        doc_id = pasted.json()["id"]
        review = await client.post(
            f"/v1/projects/{project_id}/reviews",
            headers=headers,
            json={"documentIds": [doc_id]},
        )
        review_id = review.json()["id"]

    async with SessionLocal() as db:
        doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        if not doc.normalized_text:
            doc.normalized_text = QA_POLICY_TEXT
        row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        tenant_id = row.tenant_id
        row.status = "queued"
        await db.commit()

    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    async with SessionLocal() as db:
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        assert review_row.status == "failed"


def test_bedrock_malformed_findings_array_raises() -> None:
    with pytest.raises(BedrockReviewError):
        _parse_findings_payload('{"findings": "nope"}')
