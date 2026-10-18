"""OpenRouter LLM provider: parsing, citation gating, fallback, and failure paths."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from complibot.config import get_settings
from complibot.db.models import Document, FindingRow, Review
from complibot.db.session import SessionLocal
from complibot.services.queue import _inline_tasks
from complibot_worker.main import process_message
from complibot_worker.pipeline.citations import locate_verified_citation
from complibot_worker.pipeline.openrouter_review import (
    OpenRouterReviewError,
    _build_control_alias_index,
    _parse_response_payload,
    _resolve_control_ref,
    _word_count,
)
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

QA_POLICY_PATH = Path(__file__).resolve().parent / "fixtures" / "test-compliance-policy.txt"
QA_POLICY_TEXT = QA_POLICY_PATH.read_text(encoding="utf-8")
FRAMEWORKS_PATH = Path(__file__).resolve().parents[1] / "ai" / "frameworks"
DPA_QUOTE = "Data Processing Agreement (DPA)"
GDPR_VENDOR_REF = "Art. 28(3)"
GDPR_RETENTION_REF = "Art. 5(1)(e)"
GDPR_SECURITY_COMPOSITE_REF = "Art. 32; Art. 28(3)(c)"
GDPR_SECURITY_SHORT_REF = "Art. 32"


class _FakeHttpResponse:
    def __init__(self, status_code: int, json_body: dict | None = None) -> None:
        self.status_code = status_code
        self._json_body = json_body or {}

    def json(self) -> dict:
        return self._json_body


class _FakeHttpClient:
    def __init__(self, responses: list[_FakeHttpResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def post(self, url: str, **kwargs: object) -> _FakeHttpResponse:
        self.calls.append({"url": url, **kwargs})
        if not self._responses:
            raise RuntimeError("no fake responses queued")
        return self._responses.pop(0)


def _chat_body(payload: dict) -> dict:
    return {"choices": [{"message": {"content": json.dumps(payload)}}]}


def _valid_findings_payload(
    *,
    document_type: str = "processor_dpa",
    extra_findings: list[dict] | None = None,
) -> dict:
    findings = [
        {
            "controlRef": GDPR_VENDOR_REF,
            "kind": "partial",
            "severity": "medium",
            "quote": DPA_QUOTE,
            "support": "The policy requires vendors to sign a DPA before onboarding.",
            "title": "Vendor DPA required",
            "rationale": "The policy requires a DPA before vendor onboarding.",
            "remediationSummary": "Ensure DPAs are executed before access.",
        },
        {
            "controlRef": GDPR_VENDOR_REF,
            "kind": "partial",
            "severity": "high",
            "quote": "too short",
            "support": "Should be discarded for short quote.",
            "title": "Short quote",
            "rationale": "Should be discarded.",
        },
        {
            "controlRef": GDPR_VENDOR_REF,
            "kind": "partial",
            "severity": "high",
            "quote": "this text is not in the document at all here",
            "support": "Quote is not present in the source document.",
            "title": "Bad quote",
            "rationale": "Should be discarded.",
        },
        {
            "controlRef": "Art. 999",
            "kind": "partial",
            "severity": "high",
            "quote": DPA_QUOTE,
            "support": "Unknown control reference should be dropped.",
            "title": "Unknown control",
            "rationale": "Should be discarded.",
        },
    ]
    if extra_findings:
        findings.extend(extra_findings)
    return {"documentType": document_type, "findings": findings}


def test_parse_response_payload_rejects_invalid_json() -> None:
    with pytest.raises(OpenRouterReviewError) as exc:
        _parse_response_payload("not json")
    assert exc.value.code == "openrouter_malformed_output"


def test_word_count_minimum_four() -> None:
    assert _word_count("one two three") == 3
    assert _word_count(DPA_QUOTE) >= 4


async def _drain_inline_worker() -> None:
    if _inline_tasks:
        await asyncio.gather(*list(_inline_tasks), return_exceptions=True)
        _inline_tasks.clear()


async def _seed_review(monkeypatch: pytest.MonkeyPatch, email: str) -> tuple[str, str, str]:
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

    from complibot.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/dev-login",
            json={"email": email, "name": "OpenRouter"},
        )
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "OpenRouter GDPR", "frameworkCodes": ["GDPR"]},
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

    return review_id, tenant_id, doc_id


@pytest.mark.asyncio
async def test_openrouter_review_publishes_verified_findings_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _doc_id = await _seed_review(monkeypatch, "openrouter-ok@complibot.local")

    payload = _valid_findings_payload()
    fake = _FakeHttpClient([_FakeHttpResponse(200, _chat_body(payload))])
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
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
        rows = [
            f for f in findings if f.payload.get("provenance", {}).get("provider") == "openrouter"
        ]
        assert len(rows) == 1
        payload_out = rows[0].payload
        assert payload_out["controlRef"] == GDPR_VENDOR_REF
        assert payload_out["provenance"]["provider"] == "openrouter"
        cite = payload_out["citations"][0]
        assert cite["quote"] == DPA_QUOTE
        assert cite["quote"] == QA_POLICY_TEXT[cite["charStart"] : cite["charEnd"]]
        assert "document_type:processor_dpa" in payload_out.get("systemFlags", [])


@pytest.mark.asyncio
async def test_openrouter_controller_notice_discards_art28(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(monkeypatch, "openrouter-notice@complibot.local")

    payload = _valid_findings_payload(document_type="controller_notice")
    fake = _FakeHttpClient([_FakeHttpResponse(200, _chat_body(payload))])
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    async with SessionLocal() as db:
        findings = (
            (await db.execute(select(FindingRow).where(FindingRow.review_id == review_id)))
            .scalars()
            .all()
        )
        for row in findings:
            assert not str(row.payload.get("controlRef", "")).startswith("Art. 28")


@pytest.mark.asyncio
async def test_openrouter_429_on_primary_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(monkeypatch, "openrouter-fallback@complibot.local")

    payload = _valid_findings_payload()
    fake = _FakeHttpClient(
        [
            _FakeHttpResponse(429, {}),
            _FakeHttpResponse(200, _chat_body(payload)),
        ]
    )
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENROUTER_MODEL", "primary-model")
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODEL", "fallback-model")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    assert len(fake.calls) == 2
    assert fake.calls[0]["json"]["model"] == "primary-model"
    assert fake.calls[1]["json"]["model"] == "fallback-model"

    async with SessionLocal() as db:
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        assert review_row.status == "completed"


@pytest.mark.asyncio
async def test_openrouter_missing_api_key_marks_review_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(monkeypatch, "openrouter-nokey@complibot.local")

    fake = _FakeHttpClient([])
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    async with SessionLocal() as db:
        review_row = (await db.execute(select(Review).where(Review.id == review_id))).scalar_one()
        assert review_row.status == "failed"


def test_openrouter_malformed_findings_array_raises() -> None:
    with pytest.raises(OpenRouterReviewError):
        _parse_response_payload('{"findings": "nope"}')


def test_locate_verified_citation_openrouter_fixture() -> None:
    span = locate_verified_citation(QA_POLICY_TEXT, DPA_QUOTE)
    assert span is not None


def test_resolve_control_ref_art32_maps_to_composite_pack_key() -> None:
    index = _build_control_alias_index(["GDPR"], str(FRAMEWORKS_PATH))
    resolved = _resolve_control_ref(GDPR_SECURITY_SHORT_REF, index)
    assert resolved is not None
    canonical, _fw, ctrl = resolved
    assert canonical == GDPR_SECURITY_COMPOSITE_REF
    assert ctrl.get("id") == "GDPR-32"


def test_locate_verified_citation_case_and_whitespace_insensitive() -> None:
    span = locate_verified_citation(QA_POLICY_TEXT, "data   processing agreement (dpa)")
    assert span is not None
    start, end, quote = span
    assert quote == QA_POLICY_TEXT[start:end]
    assert quote == DPA_QUOTE


def test_locate_verified_citation_rejects_fabricated_quote() -> None:
    assert locate_verified_citation(QA_POLICY_TEXT, "fabricated quote not in document") is None


@pytest.mark.asyncio
async def test_openrouter_art32_short_ref_maps_to_composite_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(
        monkeypatch, "openrouter-art32@complibot.local"
    )

    payload = {
        "documentType": "processor_dpa",
        "findings": [
            {
                "controlRef": GDPR_SECURITY_SHORT_REF,
                "kind": "partial",
                "severity": "medium",
                "quote": "multi-factor authentication (MFA) to access production systems",
                "support": "MFA is required for production access.",
                "title": "MFA for production",
                "rationale": (
                    "Access control requires MFA on production systems per security measures."
                ),
                "remediationSummary": "Maintain MFA enforcement.",
            }
        ],
    }
    fake = _FakeHttpClient([_FakeHttpResponse(200, _chat_body(payload))])
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    async with SessionLocal() as db:
        findings = (
            (await db.execute(select(FindingRow).where(FindingRow.review_id == review_id)))
            .scalars()
            .all()
        )
        rows = [
            f for f in findings if f.payload.get("provenance", {}).get("provider") == "openrouter"
        ]
        assert len(rows) == 1
        assert rows[0].payload["controlRef"] == GDPR_SECURITY_COMPOSITE_REF


@pytest.mark.asyncio
async def test_openrouter_discard_reasons_logged_when_all_candidates_dropped(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(
        monkeypatch, "openrouter-discard-log@complibot.local"
    )

    payload = {
        "documentType": "processor_dpa",
        "findings": [
            {
                "controlRef": "Art. 999",
                "kind": "partial",
                "severity": "high",
                "quote": DPA_QUOTE,
                "support": "Unknown control.",
                "title": "Bad ref",
                "rationale": "Should be discarded for unknown control ref.",
            }
        ],
    }
    fake = _FakeHttpClient([_FakeHttpResponse(200, _chat_body(payload))])
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    get_settings.cache_clear()

    with caplog.at_level(logging.WARNING):
        await process_message(
            {"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True
        )
    get_settings.cache_clear()

    assert any(
        "discarded all model candidates" in record.message for record in caplog.records
    )


def _gap_finding_payload(control_ref: str = GDPR_RETENTION_REF) -> dict:
    return {
        "documentType": "internal_policy",
        "findings": [
            {
                "controlRef": control_ref,
                "kind": "gap",
                "severity": "medium",
                "title": "Retention principle not addressed",
                "rationale": (
                    "After reviewing the full document text, no clause limits retention "
                    "or defines storage duration for personal data."
                ),
                "remediationSummary": "Add explicit retention limits aligned with purpose.",
            }
        ],
    }


@pytest.mark.asyncio
async def test_openrouter_single_chunk_publishes_gap_finding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(monkeypatch, "openrouter-gap@complibot.local")

    payload = _gap_finding_payload()
    fake = _FakeHttpClient([_FakeHttpResponse(200, _chat_body(payload))])
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review._split_document_chunks",
        lambda _text: [QA_POLICY_TEXT],
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    async with SessionLocal() as db:
        findings = (
            (await db.execute(select(FindingRow).where(FindingRow.review_id == review_id)))
            .scalars()
            .all()
        )
        gap_rows = [f for f in findings if f.payload.get("kind") == "gap"]
        assert len(gap_rows) == 1
        assert gap_rows[0].payload["controlRef"] == GDPR_RETENTION_REF


@pytest.mark.asyncio
async def test_openrouter_multi_chunk_discards_gap_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _drain_inline_worker()
    review_id, tenant_id, _ = await _seed_review(
        monkeypatch, "openrouter-chunk-gap@complibot.local"
    )

    gap_payload = _gap_finding_payload()
    empty_payload = {"documentType": "internal_policy", "findings": []}
    fake = _FakeHttpClient(
        [
            _FakeHttpResponse(200, _chat_body(gap_payload)),
            _FakeHttpResponse(200, _chat_body(empty_payload)),
        ]
    )
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review.create_openrouter_http_client",
        lambda _s: fake,
    )
    monkeypatch.setattr(
        "complibot_worker.pipeline.openrouter_review._split_document_chunks",
        lambda _text: ["first chunk text", "second chunk text"],
    )
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    await process_message({"reviewId": review_id, "tenantId": tenant_id}, final_attempt=True)
    get_settings.cache_clear()

    assert len(fake.calls) == 2

    async with SessionLocal() as db:
        findings = (
            (await db.execute(select(FindingRow).where(FindingRow.review_id == review_id)))
            .scalars()
            .all()
        )
        assert not any(f.payload.get("kind") == "gap" for f in findings)
