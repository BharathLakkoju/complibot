"""OpenRouter chat-completions review pipeline with citation verification."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
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

PROMPT_VERSION = "openrouter-chat-1"
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_CHUNK_CHAR_LIMIT = 12_000
_MAX_CHUNKS = 8
_DOC_TYPES = frozenset(
    {"processor_dpa", "controller_notice", "internal_policy", "guidance", "other"}
)


class OpenRouterReviewError(Exception):
    """OpenRouter LLM failure (worker should fail the review)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class HttpPostClient(Protocol):
    def post(self, url: str, **kwargs: Any) -> Any: ...


def create_openrouter_http_client(settings: Settings) -> httpx.Client:
    return httpx.Client(timeout=settings.openrouter_timeout_seconds)


def _strip_json_fences(raw: str) -> str:
    return _JSON_FENCE.sub("", raw.strip()).strip()


def _parse_response_payload(text: str) -> tuple[str | None, list[dict[str, Any]]]:
    cleaned = _strip_json_fences(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            "Model response was not valid JSON.",
        ) from exc
    if not isinstance(data, dict):
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            "Model JSON root must be an object.",
        )
    raw_doc_type = data.get("documentType") or data.get("document_type")
    doc_type: str | None = None
    if raw_doc_type is not None:
        candidate = str(raw_doc_type).strip().lower()
        if candidate in _DOC_TYPES:
            doc_type = candidate
    findings = data.get("findings")
    if findings is None:
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            'Model JSON must include a "findings" array.',
        )
    if not isinstance(findings, list):
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            '"findings" must be an array.',
        )
    return doc_type, [f for f in findings if isinstance(f, dict)]


def _normalize_control_ref_alias(ref: str) -> str:
    s = ref.strip()
    s = re.sub(
        r"^(?:GDPR\s+)?(?:Article\s+|Art\.?\s*)",
        "",
        s,
        flags=re.IGNORECASE,
    ).strip()
    return re.sub(r"\s+", " ", s)


def _control_ref_alias_segments(canonical_ref: str, ctrl: dict[str, Any]) -> list[str]:
    segments = [canonical_ref]
    ctrl_id = str(ctrl.get("id", "")).strip()
    if ctrl_id:
        segments.append(ctrl_id)
    for part in re.split(r"[;,]", canonical_ref):
        part = part.strip()
        if part:
            segments.append(part)
    return segments


def _build_control_alias_index(
    framework_codes: list[str], frameworks_path: str
) -> dict[str, tuple[str, str, dict[str, Any]]]:
    """Map normalized ref aliases to (canonical_ref, framework, control)."""
    index: dict[str, tuple[str, str, dict[str, Any]]] = {}
    for fw in framework_codes:
        for ctrl in load_pack_controls(fw, frameworks_path):
            canonical = control_ref(ctrl)
            if not canonical:
                continue
            for segment in _control_ref_alias_segments(canonical, ctrl):
                key = _normalize_control_ref_alias(segment)
                if key and key not in index:
                    index[key] = (canonical, fw, ctrl)
    return index


def _resolve_control_ref(
    raw_ref: str, alias_index: dict[str, tuple[str, str, dict[str, Any]]]
) -> tuple[str, str, dict[str, Any]] | None:
    key = _normalize_control_ref_alias(raw_ref)
    if not key:
        return None
    return alias_index.get(key)


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
        "First classify the document as exactly one documentType:\n"
        "processor_dpa | controller_notice | internal_policy | guidance | other\n"
        "If documentType is controller_notice, do NOT report Art. 28 processor obligations; "
        "focus on Arts. 5, 6, and 12-22 instead.\n"
        'Return a single JSON object with keys "documentType" and "findings" (array). '
        "Each finding must include:\n"
        "- controlRef: one of the control refs listed below\n"
        "- kind: violation | gap | partial | compliant\n"
        "- severity: critical | high | medium | low | info\n"
        "- quote: exact verbatim clause or full sentence from the document (minimum four words; "
        "required for non-gap kinds)\n"
        "- support: one line explaining how the quote satisfies or violates the control\n"
        "- title: short headline\n"
        "- rationale: why this matters for the control\n"
        "- remediationSummary: suggested fix (plain text)\n"
        "For kind=gap, omit quote; rationale must explain the absence only after judging "
        "against the entire provided document text in this message (not a subsection). "
        "Skip controls with no evidence. Do not invent quotes.\n\n"
        f"Frameworks: {', '.join(framework_codes)}\n"
        f"Controls:\n{controls_block}\n\n"
        f"Document:\n{wrap_document(document_text)}\n"
    )


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w])


def _is_art28_processor_ref(ref: str) -> bool:
    return ref.startswith("Art. 28")


def _split_document_chunks(text: str) -> list[str]:
    if len(text) <= _CHUNK_CHAR_LIMIT:
        return [text]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return [text[:_CHUNK_CHAR_LIMIT]]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for para in paragraphs:
        extra = 2 if current else 0
        if current and current_len + extra + len(para) > _CHUNK_CHAR_LIMIT:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += extra + len(para)
    if current:
        chunks.append("\n\n".join(current))
    if len(chunks) > _MAX_CHUNKS:
        logger.warning(
            "Document exceeds chunk cap; truncating coverage",
            extra={"chunk_count": len(chunks), "chunk_cap": _MAX_CHUNKS},
        )
        chunks = chunks[:_MAX_CHUNKS]
    return chunks


def _extract_message_content(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            "OpenRouter response missing choices.",
        )
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        text = "".join(parts).strip()
    else:
        text = str(content).strip()
    if not text:
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            "Model returned an empty response.",
        )
    return text


def _invoke_chat(
    client: HttpPostClient,
    settings: Settings,
    *,
    model: str,
    prompt: str,
) -> str:
    api_key = (settings.openrouter_api_key or "").strip()
    if not api_key:
        raise OpenRouterReviewError(
            "openrouter_missing_api_key",
            "OPENROUTER_API_KEY is not set.",
        )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": settings.openrouter_max_tokens,
        "temperature": 0,
    }
    try:
        response = client.post(_OPENROUTER_URL, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise OpenRouterReviewError("openrouter_timeout", "OpenRouter request timed out.") from exc
    except httpx.HTTPError as exc:
        raise OpenRouterReviewError(
            "openrouter_invoke_failed",
            f"OpenRouter HTTP error: {exc}",
        ) from exc

    status = response.status_code
    if status == 429 or status >= 500:
        raise OpenRouterReviewError(
            "openrouter_retryable",
            f"OpenRouter HTTP {status} for model {model}.",
        )
    if status >= 400:
        raise OpenRouterReviewError(
            "openrouter_invoke_failed",
            f"OpenRouter HTTP {status} for model {model}.",
        )
    try:
        body = response.json()
    except json.JSONDecodeError as exc:
        raise OpenRouterReviewError(
            "openrouter_malformed_output",
            "OpenRouter response was not valid JSON.",
        ) from exc
    return _extract_message_content(body)


def _invoke_with_fallback(
    client: HttpPostClient,
    settings: Settings,
    prompt: str,
) -> tuple[str, str]:
    primary = settings.openrouter_model
    fallback = settings.openrouter_fallback_model
    try:
        text = _invoke_chat(client, settings, model=primary, prompt=prompt)
        return text, primary
    except OpenRouterReviewError as primary_exc:
        if primary_exc.code != "openrouter_retryable":
            raise
        text = _invoke_chat(client, settings, model=fallback, prompt=prompt)
        return text, fallback


def _field(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def _merge_raw_findings(
    chunk_results: list[tuple[str | None, list[dict[str, Any]]]],
) -> tuple[str | None, list[dict[str, Any]]]:
    doc_type: str | None = None
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for dt, items in chunk_results:
        if doc_type is None and dt is not None:
            doc_type = dt
        for raw in items:
            ref = str(_field(raw, "controlRef", "control_ref") or "").strip()
            quote = str(_field(raw, "quote") or "")
            key = (ref, quote)
            if key in seen:
                continue
            seen.add(key)
            merged.append(raw)
    return doc_type, merged


async def run_openrouter_review(
    db: AsyncSession,
    *,
    tenant_id: str,
    review_id: str,
    frameworks_path: str,
    token_streaming: bool,
    http_client: HttpPostClient | None = None,
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

    control_alias_index = _build_control_alias_index(review.framework_codes, frameworks_path)
    chunks = _split_document_chunks(text)
    client = http_client or create_openrouter_http_client(settings)

    chunk_results: list[tuple[str | None, list[dict[str, Any]]]] = []
    model_used = settings.openrouter_model
    for chunk in chunks:
        prompt = _build_prompt(
            framework_codes=review.framework_codes,
            frameworks_path=frameworks_path,
            document_text=chunk,
        )
        raw_response, model_used = await asyncio.to_thread(
            _invoke_with_fallback, client, settings, prompt
        )
        chunk_results.append(_parse_response_payload(raw_response))

    doc_type, raw_findings = _merge_raw_findings(chunk_results)

    chunk_id = new_id("chk")
    findings_count = 0
    discarded = 0
    discard_reasons: Counter[str] = Counter()
    gaps_suppressed_chunked = len(chunks) > 1

    for raw in raw_findings:
        raw_ref = str(_field(raw, "controlRef", "control_ref") or "").strip()
        resolved = _resolve_control_ref(raw_ref, control_alias_index)
        if resolved is None:
            discarded += 1
            discard_reasons["unknown_control_ref"] += 1
            continue
        ref, fw, ctrl = resolved
        if doc_type == "controller_notice" and _is_art28_processor_ref(raw_ref):
            discarded += 1
            discard_reasons["art28_suppressed_controller_notice"] += 1
            continue
        kind = coerce_kind(_field(raw, "kind"))
        if kind is None:
            discarded += 1
            discard_reasons["invalid_kind"] += 1
            continue
        if gaps_suppressed_chunked and kind == "gap":
            discarded += 1
            discard_reasons["gap_suppressed_chunked"] += 1
            continue
        quote = str(_field(raw, "quote") or "")
        support = str(_field(raw, "support") or "").strip()
        if kind != "gap":
            if _word_count(quote) < 4:
                discarded += 1
                discard_reasons["quote_too_short"] += 1
                continue
            if not support:
                discarded += 1
                discard_reasons["missing_support"] += 1
                continue
            span = locate_verified_citation(text, quote)
            if span is None:
                discarded += 1
                discard_reasons["citation_not_found"] += 1
                continue
            char_start, char_end, verified_quote = span
        else:
            char_start, char_end, verified_quote = 0, 0, ""
            if quote:
                if _word_count(quote) < 4:
                    discarded += 1
                    discard_reasons["quote_too_short"] += 1
                    continue
                span = locate_verified_citation(text, quote)
                if span is None:
                    discarded += 1
                    discard_reasons["citation_not_found"] += 1
                    continue
                char_start, char_end, verified_quote = span
        title = str(_field(raw, "title") or f"Review: {ctrl.get('title', ref)}")[:200]
        rationale = str(_field(raw, "rationale") or "")[:4000]
        if not rationale.strip():
            discarded += 1
            discard_reasons["missing_rationale"] += 1
            continue
        if kind == "gap" and len(rationale.strip()) < 20:
            discarded += 1
            discard_reasons["gap_rationale_too_short"] += 1
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

        system_flags: list[str] = []
        if doc_type:
            system_flags.append(f"document_type:{doc_type}")

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
                reason="OpenRouter assessment (pre-calibration)",
                calibrated=False,
            ),
            rationale=rationale,
            remediation=Remediation(summary=remediation_text or "Review contractual alignment."),
            citations=citations,
            status="open",
            version=1,
            system_flags=system_flags,
            provenance=FindingProvenance(
                provider="openrouter",
                model_id=model_used,
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
    status_payload: dict[str, Any] = {
        "status": "completed",
        "progress": {"stage": "remediate", "done": 5, "total": 5},
        "findingsSoFar": findings_count,
        "discardedCount": discarded,
        "discardReasons": dict(discard_reasons),
    }
    if gaps_suppressed_chunked:
        status_payload["gapsSuppressedChunked"] = True
    await append_review_event(
        db,
        tenant_id=tenant_id,
        review_id=review_id,
        event_type="review.status",
        payload=status_payload,
    )
    await db.commit()
    log_extra: dict[str, Any] = {
        "review_id": review_id,
        "findings_count": findings_count,
        "discarded_count": discarded,
        "discard_reasons": dict(discard_reasons),
        "document_type": doc_type,
        "chunk_count": len(chunks),
        "candidate_count": len(raw_findings),
    }
    if gaps_suppressed_chunked:
        log_extra["gaps_suppressed_chunked"] = True
    if raw_findings and findings_count == 0:
        logger.warning(
            "OpenRouter review discarded all model candidates",
            extra=log_extra,
        )
    logger.info("OpenRouter review completed", extra=log_extra)
