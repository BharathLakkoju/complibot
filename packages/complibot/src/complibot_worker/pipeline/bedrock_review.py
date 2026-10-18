"""Bedrock Converse review pipeline with citation verification."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from complibot.config import Settings, get_settings
from complibot.db.models import Document, FindingRow, Review
from complibot.ids import new_finding_id, new_id
from complibot.schemas import Citation, Confidence, Finding, FindingProvenance, Remediation
from complibot.services.document_text import DocumentTextError, resolve_document_text
from complibot.services.events import append_review_event
from complibot.ws.hub import review_hub
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot_worker.pipeline.citations import (
    coerce_kind,
    coerce_severity,
    locate_verified_citation,
)
from complibot_worker.pipeline.pack_controls import control_ref, load_pack_controls
from complibot_worker.pipeline.prompting import wrap_document

logger = logging.getLogger(__name__)

PROMPT_VERSION = "bedrock-converse-1"
_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class BedrockReviewError(Exception):
    """Bedrock LLM failure (worker should fail the review)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def create_bedrock_runtime_client(settings: Settings) -> Any:
    kwargs: dict[str, Any] = {
        "region_name": settings.bedrock_region,
        "config": Config(read_timeout=120, connect_timeout=10, retries={"max_attempts": 2}),
    }
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("bedrock-runtime", **kwargs)


def _map_client_error(exc: ClientError) -> BedrockReviewError:
    code = exc.response.get("Error", {}).get("Code", "ClientError")
    message = exc.response.get("Error", {}).get("Message", str(exc))
    lowered = code.lower()
    if "accessdenied" in lowered or code == "AccessDeniedException":
        return BedrockReviewError("bedrock_access_denied", f"Bedrock access denied: {message}")
    if "throttl" in lowered or code in ("ThrottlingException", "TooManyRequestsException"):
        return BedrockReviewError("bedrock_throttled", f"Bedrock throttled: {message}")
    if "timeout" in lowered or "timedout" in lowered:
        return BedrockReviewError("bedrock_timeout", f"Bedrock timed out: {message}")
    return BedrockReviewError("bedrock_invoke_failed", f"Bedrock error ({code}): {message}")


def _strip_json_fences(raw: str) -> str:
    return _JSON_FENCE.sub("", raw.strip()).strip()


def _parse_findings_payload(text: str) -> list[dict[str, Any]]:
    cleaned = _strip_json_fences(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise BedrockReviewError(
            "bedrock_malformed_output",
            "Model response was not valid JSON.",
        ) from exc
    if not isinstance(data, dict):
        raise BedrockReviewError(
            "bedrock_malformed_output",
            "Model JSON root must be an object.",
        )
    findings = data.get("findings")
    if findings is None:
        raise BedrockReviewError(
            "bedrock_malformed_output",
            'Model JSON must include a "findings" array.',
        )
    if not isinstance(findings, list):
        raise BedrockReviewError(
            "bedrock_malformed_output",
            '"findings" must be an array.',
        )
    return [f for f in findings if isinstance(f, dict)]


def _build_control_index(
    framework_codes: list[str], frameworks_path: str
) -> dict[str, tuple[str, dict[str, Any]]]:
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for fw in framework_codes:
        for ctrl in load_pack_controls(fw, frameworks_path):
            ref = control_ref(ctrl)
            if ref:
                index[ref] = (fw, ctrl)
    return index


def _build_prompt(
    *,
    framework_codes: list[str],
    frameworks_path: str,
    document_text: str,
) -> str:
    controls_lines: list[str] = []
    for fw in framework_codes:
        for ctrl in load_pack_controls(fw, frameworks_path):
            ref = control_ref(ctrl)
            title = ctrl.get("title", ref)
            req = str(ctrl.get("requirement", "")).strip().replace("\n", " ")[:500]
            controls_lines.append(f"- {ref} ({fw}): {title}. {req}")

    controls_block = "\n".join(controls_lines)
    return (
        "You are a compliance reviewer. Assess the document only against the listed controls.\n"
        'Return a single JSON object with key "findings" (array). Each finding must include:\n'
        "- controlRef: one of the control refs listed below\n"
        "- kind: violation | gap | partial | compliant\n"
        "- severity: critical | high | medium | low | info\n"
        "- quote: exact verbatim substring copied from the document (required for non-gap kinds)\n"
        "- title: short headline\n"
        "- rationale: why this matters for the control\n"
        "- remediationSummary: suggested fix (plain text)\n"
        "Skip controls with no evidence. Do not invent quotes.\n\n"
        f"Frameworks: {', '.join(framework_codes)}\n"
        f"Controls:\n{controls_block}\n\n"
        f"Document:\n{wrap_document(document_text)}\n"
    )


def _invoke_converse(client: Any, settings: Settings, prompt: str) -> str:
    try:
        response = client.converse(
            modelId=settings.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 4096, "temperature": 0},
        )
    except ClientError as exc:
        raise _map_client_error(exc) from exc
    except BotoCoreError as exc:
        err = str(exc).lower()
        if "timeout" in err or "timed out" in err:
            raise BedrockReviewError("bedrock_timeout", "Bedrock request timed out.") from exc
        raise BedrockReviewError("bedrock_invoke_failed", f"Bedrock client error: {exc}") from exc

    output = response.get("output", {}).get("message", {}).get("content", [])
    parts: list[str] = []
    for block in output:
        if isinstance(block, dict) and "text" in block:
            parts.append(str(block["text"]))
    text = "".join(parts).strip()
    if not text:
        raise BedrockReviewError(
            "bedrock_malformed_output",
            "Model returned an empty response.",
        )
    return text


def _field(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


async def run_bedrock_review(
    db: AsyncSession,
    *,
    tenant_id: str,
    review_id: str,
    frameworks_path: str,
    token_streaming: bool,
    bedrock_client: Any | None = None,
) -> None:
    review_res = await db.execute(select(Review).where(Review.id == review_id))
    review = review_res.scalar_one()
    doc_id = review.document_ids[0]
    doc_res = await db.execute(select(Document).where(Document.id == doc_id))
    document = doc_res.scalar_one()
    settings = get_settings()
    text = await resolve_document_text(db, settings, document, persist=True)
    if not text.strip():
        raise DocumentTextError("empty_text", "Document text is empty; cannot run review.")

    control_index = _build_control_index(review.framework_codes, frameworks_path)
    prompt = _build_prompt(
        framework_codes=review.framework_codes,
        frameworks_path=frameworks_path,
        document_text=text,
    )
    client = bedrock_client or create_bedrock_runtime_client(settings)
    raw_response = await asyncio.to_thread(_invoke_converse, client, settings, prompt)
    raw_findings = _parse_findings_payload(raw_response)

    chunk_id = new_id("chk")
    findings_count = 0
    discarded = 0

    for raw in raw_findings:
        ref = str(_field(raw, "controlRef", "control_ref") or "").strip()
        if not ref or ref not in control_index:
            discarded += 1
            continue
        fw, ctrl = control_index[ref]
        kind = coerce_kind(_field(raw, "kind"))
        if kind is None:
            discarded += 1
            continue
        quote = str(_field(raw, "quote") or "")
        if kind != "gap":
            span = locate_verified_citation(text, quote)
            if span is None:
                discarded += 1
                continue
            char_start, char_end, verified_quote = span
        else:
            char_start, char_end, verified_quote = 0, 0, ""
            if quote:
                span = locate_verified_citation(text, quote)
                if span is None:
                    discarded += 1
                    continue
                char_start, char_end, verified_quote = span

        title = str(_field(raw, "title") or f"Review: {ctrl.get('title', ref)}")[:200]
        rationale = str(_field(raw, "rationale") or "")[:4000]
        if not rationale.strip():
            discarded += 1
            continue
        remediation_text = str(
            _field(raw, "remediationSummary", "remediation_summary", "remediation") or ""
        )[:400]

        draft_id = new_id("dft")
        if token_streaming and rationale:
            for i in range(0, len(rationale), 40):
                part = rationale[i : i + 40]
                await review_hub.broadcast_ephemeral(
                    review_id,
                    {
                        "v": 1,
                        "type": "finding.delta",
                        "id": new_id("evt"),
                        "reviewId": review_id,
                        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "payload": {
                            "draftId": draft_id,
                            "controlRef": ref,
                            "field": "rationale",
                            "text": part,
                        },
                    },
                )

        citations: list[Citation] = []
        if verified_quote:
            citations.append(
                Citation(
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    char_start=char_start,
                    char_end=char_end,
                    quote=verified_quote,
                )
            )

        finding = Finding(
            id=new_finding_id(),
            tenant_id=tenant_id,
            project_id=review.project_id,
            review_id=review_id,
            framework=fw,
            control_id=str(ctrl.get("id", ref)),
            control_ref=ref,
            kind=kind,
            title=title,
            severity=coerce_severity(_field(raw, "severity")),
            confidence=Confidence(
                score=0.72,
                band="medium",
                reason="Bedrock assessment (pre-calibration)",
                calibrated=False,
            ),
            rationale=rationale,
            remediation=Remediation(summary=remediation_text or "Review contractual alignment."),
            citations=citations,
            status="open",
            version=1,
            provenance=FindingProvenance(
                provider="bedrock",
                model_id=settings.bedrock_model_id,
                prompt_version=PROMPT_VERSION,
                pack_version="pack-yaml",
            ),
            created_at=datetime.now(UTC),
        )
        db.add(
            FindingRow(
                id=finding.id,
                tenant_id=tenant_id,
                project_id=review.project_id,
                review_id=review_id,
                payload=finding.model_dump(by_alias=True, mode="json"),
                version=1,
            )
        )
        await append_review_event(
            db,
            tenant_id=tenant_id,
            review_id=review_id,
            event_type="finding.created",
            payload={"finding": finding.model_dump(by_alias=True, mode="json")},
        )
        findings_count += 1
        await db.commit()

    review.status = "completed"
    await append_review_event(
        db,
        tenant_id=tenant_id,
        review_id=review_id,
        event_type="review.status",
        payload={
            "status": "completed",
            "progress": {"stage": "remediate", "done": 5, "total": 5},
            "findingsSoFar": findings_count,
            "discardedCount": discarded,
        },
    )
    await db.commit()
    logger.info(
        "Bedrock review completed",
        extra={
            "review_id": review_id,
            "findings_count": findings_count,
            "discarded_count": discarded,
        },
    )
