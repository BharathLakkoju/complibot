"""Deterministic demo pipeline: seeds findings with verified citations (local / mock LLM)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.db.models import Document, FindingRow, Review
from complibot.ids import new_finding_id, new_id
from complibot.schemas import Citation, Confidence, Finding, FindingProvenance, Remediation
from complibot.services.events import append_review_event
from complibot.ws.hub import review_hub


def _load_pack_controls(framework: str, frameworks_path: str) -> list[dict[str, Any]]:
    folder = {
        "GDPR": "gdpr",
        "SOC2": "soc2",
        "ISO27001": "iso27001",
        "HIPAA": "hipaa",
        "INTERNAL": "internal-policy",
    }.get(framework)
    if not folder:
        return []
    pack_path = Path(frameworks_path) / folder / "pack.yaml"
    if not pack_path.exists():
        return []
    data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    return data.get("controls", [])[:5]


def _coerce_severity(value: object) -> str:
    allowed = {"critical", "high", "medium", "low", "info"}
    s = str(value or "medium").lower()
    return s if s in allowed else "medium"


def _find_quote(text: str, needles: list[str]) -> tuple[int, int, str] | None:
    for needle in needles:
        idx = text.find(needle)
        if idx >= 0:
            return idx, idx + len(needle), text[idx : idx + len(needle)]
    return None


async def run_mock_review(
    db: AsyncSession,
    *,
    tenant_id: str,
    review_id: str,
    frameworks_path: str,
    token_streaming: bool,
) -> None:
    review_res = await db.execute(select(Review).where(Review.id == review_id))
    review = review_res.scalar_one()
    doc_id = review.document_ids[0]
    doc_res = await db.execute(select(Document).where(Document.id == doc_id))
    document = doc_res.scalar_one()
    text = document.normalized_text or ""

    await append_review_event(
        db,
        tenant_id=tenant_id,
        review_id=review_id,
        event_type="review.status",
        payload={
            "status": "running",
            "progress": {"stage": "ingest", "done": 1, "total": 5},
            "findingsSoFar": 0,
        },
    )
    await db.commit()

    chunk_id = new_id("chk")
    findings_count = 0
    discarded = 0

    for fw in review.framework_codes:
        controls = _load_pack_controls(fw, frameworks_path)
        for ctrl in controls:
            ref = ctrl.get("ref") or ctrl.get("id", "")
            keywords = ctrl.get("keywords") or [ctrl.get("title", "")]
            span = _find_quote(text, [str(k) for k in keywords if k])
            if span is None:
                continue
            char_start, char_end, quote = span
            if quote != text[char_start:char_end]:
                discarded += 1
                continue
            draft_id = new_id("dft")
            rationale = (
                f"The cited text addresses control {ref}. "
                "This is a synthetic assessment for demo purposes only."
            )
            remediation_text = (
                "Consider aligning contractual language with the referenced control expectation."
            )
            if token_streaming:
                for field, chunk in [("rationale", rationale), ("remediation", remediation_text)]:
                    for i in range(0, len(chunk), 40):
                        part = chunk[i : i + 40]
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
                                    "field": field,
                                    "text": part,
                                },
                            },
                        )
            finding = Finding(
                id=new_finding_id(),
                tenant_id=tenant_id,
                project_id=review.project_id,
                review_id=review_id,
                framework=fw,
                control_id=str(ctrl.get("id", ref)),
                control_ref=ref,
                kind="partial",
                title=f"Review needed: {ctrl.get('title', ref)[:120]}",
                severity=_coerce_severity(ctrl.get("defaultSeverity") or ctrl.get("default_severity")),
                confidence=Confidence(
                    score=0.78,
                    band="medium",
                    reason="Mock pipeline estimate",
                    calibrated=False,
                ),
                rationale=rationale,
                remediation=Remediation(summary=remediation_text[:400]),
                citations=[
                    Citation(
                        document_id=doc_id,
                        chunk_id=chunk_id,
                        char_start=char_start,
                        char_end=char_end,
                        quote=quote,
                    )
                ],
                status="open",
                version=1,
                provenance=FindingProvenance(
                    provider="mock",
                    model_id="mock-v0",
                    prompt_version="mock-1",
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
