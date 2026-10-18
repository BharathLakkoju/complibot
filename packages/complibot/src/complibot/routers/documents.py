from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, current_user
from complibot.auth.roles import require_project_role
from complibot.config import get_settings
from complibot.db.models import Document
from complibot.db.session import get_db
from complibot.exceptions import BadRequest, NotFound, ServiceUnavailable
from complibot.ids import new_document_id
from complibot.schemas import DocumentOut, DocumentPasteIn, DocumentPresignIn, PresignOut
from complibot.services.aws import (
    get_object_bytes,
    maybe_ensure_documents_bucket,
    presign_put,
    put_object_bytes,
)
from complibot.services.document_ingest import MAX_BYTES, normalize_mime
from complibot.services.document_text import has_usable_text, persist_parsed_upload

router = APIRouter(prefix="/v1", tags=["documents"])


def _doc_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        project_id=doc.project_id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status,
        page_count=doc.page_count,
        created_at=doc.created_at,
    )


@router.get("/projects/{project_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    project_id: str,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentOut]:
    await require_project_role(project_id, "viewer", user, db)
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id, Document.tenant_id == user.tenant_id)
        .order_by(Document.created_at.desc())
    )
    return [_doc_out(d) for d in result.scalars().all()]


@router.post("/projects/{project_id}/documents/presign", response_model=PresignOut)
async def presign_upload(
    project_id: str,
    body: DocumentPresignIn,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> PresignOut:
    await require_project_role(project_id, "reviewer", user, db)
    if body.size_bytes <= 0 or body.size_bytes > MAX_BYTES:
        raise BadRequest("File must be between 1 byte and 10 MB.")
    safe_name = body.filename.replace("/", "_").replace("\\", "_")[:200]
    mime = normalize_mime(safe_name, body.content_type)
    settings = get_settings()
    await maybe_ensure_documents_bucket(settings)
    doc_id = new_document_id()
    key = f"{user.tenant_id}/{project_id}/{doc_id}/{safe_name}"
    doc = Document(
        id=doc_id,
        tenant_id=user.tenant_id,
        project_id=project_id,
        filename=safe_name,
        mime_type=mime,
        s3_key=key,
        status="uploaded",
        uploaded_by=user.id,
        created_at=datetime.now(UTC),
    )
    db.add(doc)
    await db.commit()
    try:
        url = await presign_put(settings, key, mime)
    except ServiceUnavailable:
        await db.delete(doc)
        await db.commit()
        raise
    return PresignOut(upload_url=url, document_id=doc_id, s3_key=key)


@router.post("/projects/{project_id}/documents/paste", response_model=DocumentOut)
async def paste_document(
    project_id: str,
    body: DocumentPasteIn,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    await require_project_role(project_id, "reviewer", user, db)
    text = body.text.strip()
    if not text:
        raise BadRequest("Paste some contract or policy text.")
    if len(text) > MAX_BYTES:
        raise BadRequest("Text exceeds the 10 MB limit.")
    title = body.title.strip() or "pasted-document.txt"
    if not title.endswith(".txt"):
        title = f"{title}.txt"
    doc_id = new_document_id()
    key = f"{user.tenant_id}/{project_id}/{doc_id}/{title}"
    data = text.encode("utf-8")
    settings = get_settings()
    await maybe_ensure_documents_bucket(settings)
    try:
        await put_object_bytes(settings, key, data, "text/plain")
    except ServiceUnavailable:
        raise
    doc = Document(
        id=doc_id,
        tenant_id=user.tenant_id,
        project_id=project_id,
        filename=title[:500],
        mime_type="text/plain",
        s3_key=key,
        status="uploaded",
        uploaded_by=user.id,
        created_at=datetime.now(UTC),
    )
    db.add(doc)
    await db.commit()
    await persist_parsed_upload(db, doc, data)
    return _doc_out(doc)


@router.post("/documents/{document_id}/complete", response_model=DocumentOut)
async def complete_upload(
    document_id: str,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.tenant_id == user.tenant_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise NotFound()
    await require_project_role(doc.project_id, "reviewer", user, db)
    if doc.status == "parsed" and has_usable_text(doc.normalized_text):
        return _doc_out(doc)
    if doc.status == "failed":
        raise BadRequest("Document already failed processing; upload again.")
    settings = get_settings()
    raw = await get_object_bytes(settings, doc.s3_key)
    if len(raw) > MAX_BYTES:
        doc.status = "failed"
        await db.commit()
        raise BadRequest("File exceeds the 10 MB limit.")
    await persist_parsed_upload(db, doc, raw)
    return _doc_out(doc)
