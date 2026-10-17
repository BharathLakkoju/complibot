"""Parse uploaded document bytes into normalized plain text."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from complibot.exceptions import BadRequest

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 50

ALLOWED_MIME = {
    "text/plain": {".txt", ".md", ".markdown"},
    "text/markdown": {".md", ".markdown", ".txt"},
    "application/pdf": {".pdf"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
}


@dataclass
class ParseResult:
    text: str
    page_count: int
    pii_detected: bool


def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot >= 0 else ""


def normalize_mime(filename: str, content_type: str) -> str:
    ct = content_type.split(";")[0].strip().lower()
    ext = _extension(filename)
    if ct in ALLOWED_MIME and ext in ALLOWED_MIME[ct]:
        return ct
    for mime, exts in ALLOWED_MIME.items():
        if ext in exts:
            return mime
    raise BadRequest(
        "Unsupported file type. Use PDF (text layer), DOCX, or TXT/Markdown up to 10 MB / 50 pages."
    )


def _detect_pii(text: str) -> bool:
    return bool(re.search(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", text))


def _parse_txt(data: bytes) -> ParseResult:
    text = data.decode("utf-8", errors="replace")
    return ParseResult(text=text, page_count=1, pii_detected=_detect_pii(text))


def _parse_pdf(data: bytes) -> ParseResult:
    from pypdf import PdfReader

    if len(data) > MAX_BYTES:
        raise BadRequest("File exceeds the 10 MB limit.")
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise BadRequest("This PDF is password-protected. Remove the password and upload again.")
    page_count = len(reader.pages)
    if page_count > MAX_PAGES:
        raise BadRequest(f"PDF has {page_count} pages. The limit is {MAX_PAGES} pages.")
    parts: list[str] = []
    empty_pages = 0
    for page in reader.pages:
        extracted = (page.extract_text() or "").strip()
        if len(extracted) < 50:
            empty_pages += 1
        parts.append(extracted)
    if page_count > 0 and empty_pages > page_count // 2:
        raise BadRequest(
            "This PDF looks like a scanned image without a text layer. "
            "Upload a text-based PDF, DOCX, or TXT."
        )
    text = "\n\n".join(parts)
    return ParseResult(text=text, page_count=page_count, pii_detected=_detect_pii(text))


def _parse_docx(data: bytes) -> ParseResult:
    from docx import Document as DocxDocument

    if len(data) > MAX_BYTES:
        raise BadRequest("File exceeds the 10 MB limit.")
    doc = DocxDocument(io.BytesIO(data))
    text = "\n".join(p.text for p in doc.paragraphs if p.text)
    return ParseResult(text=text, page_count=1, pii_detected=_detect_pii(text))


def parse_document(filename: str, content_type: str, data: bytes) -> ParseResult:
    if len(data) > MAX_BYTES:
        raise BadRequest("File exceeds the 10 MB limit.")
    mime = normalize_mime(filename, content_type)
    if mime in ("text/plain", "text/markdown"):
        return _parse_txt(data)
    if mime == "application/pdf":
        return _parse_pdf(data)
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _parse_docx(data)
    raise BadRequest("Unsupported file type.")
