"""Load normalized document text for ingest, reviews, and the worker pipeline."""

from __future__ import annotations

import hashlib

from complibot.config import Settings
from complibot.db.models import Document
from complibot.exceptions import BadRequest, ServiceUnavailable
from complibot.services.aws import get_object_bytes
from complibot.services.document_ingest import parse_document
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentTextError(Exception):
    """Document text could not be loaded (worker should fail the review)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def has_usable_text(text: str | None) -> bool:
    return bool(text and text.strip())


async def persist_parsed_upload(
    db: AsyncSession,
    doc: Document,
    raw: bytes,
) -> str:
    """Parse raw bytes, persist metadata on ``doc``, return normalized text."""
    parsed = parse_document(doc.filename, doc.mime_type, raw)
    if not has_usable_text(parsed.text):
        doc.status = "failed"
        await db.commit()
        raise BadRequest("Document has no extractable text. Use a text-based PDF, DOCX, or TXT.")
    doc.sha256 = hashlib.sha256(raw).hexdigest()
    doc.normalized_text = parsed.text
    doc.page_count = parsed.page_count
    doc.pii_detected = parsed.pii_detected
    doc.status = "parsed"
    await db.commit()
    await db.refresh(doc)
    return parsed.text


async def resolve_document_text(
    db: AsyncSession,
    settings: Settings,
    doc: Document,
    *,
    persist: bool = False,
) -> str:
    """Return normalized text from DB or S3. Optionally backfill ``normalized_text``."""
    if has_usable_text(doc.normalized_text):
        return doc.normalized_text or ""

    if not doc.s3_key:
        raise DocumentTextError("missing_storage_key", "Document has no stored content.")

    try:
        raw = await get_object_bytes(settings, doc.s3_key)
    except ServiceUnavailable as exc:
        raise DocumentTextError(
            "storage_unavailable",
            "Could not read uploaded document from storage.",
        ) from exc
    parsed = parse_document(doc.filename, doc.mime_type, raw)
    if not has_usable_text(parsed.text):
        raise DocumentTextError(
            "empty_text",
            "Uploaded document has no extractable text after storage fetch.",
        )

    if persist:
        doc.sha256 = hashlib.sha256(raw).hexdigest()
        doc.normalized_text = parsed.text
        doc.page_count = parsed.page_count
        doc.pii_detected = parsed.pii_detected
        if doc.status != "failed":
            doc.status = "parsed"
        await db.commit()
        await db.refresh(doc)

    return parsed.text
