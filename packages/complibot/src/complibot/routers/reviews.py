from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, current_user
from complibot.db.models import Document, FindingRow, ProjectMember, Review
from complibot.db.session import get_db
from complibot.exceptions import NotFound
from complibot.schemas import Finding

router = APIRouter(prefix="/v1/reviews", tags=["reviews"])


async def _get_review_access(
    review_id: str,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Review:
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.tenant_id == user.tenant_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise NotFound()
    mem = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == review.project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if mem.scalar_one_or_none() is None:
        raise NotFound()
    return review


@router.get("/{review_id}")
async def get_review(
    review: Review = Depends(_get_review_access),
) -> dict:
    return {
        "id": review.id,
        "projectId": review.project_id,
        "documentIds": review.document_ids,
        "frameworkCodes": review.framework_codes,
        "status": review.status,
        "lastSeq": review.last_seq,
        "createdAt": review.created_at.isoformat(),
    }


@router.get("/{review_id}/findings", response_model=list[Finding])
async def list_findings(
    review: Review = Depends(_get_review_access),
    db: AsyncSession = Depends(get_db),
) -> list[Finding]:
    result = await db.execute(select(FindingRow).where(FindingRow.review_id == review.id))
    rows = result.scalars().all()
    return [Finding.model_validate(row.payload) for row in rows]


@router.get("/{review_id}/snapshot")
async def snapshot(
    review: Review = Depends(_get_review_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    findings = await list_findings(review, db)
    doc_texts: dict[str, str] = {}
    for doc_id in review.document_ids:
        res = await db.execute(select(Document).where(Document.id == doc_id))
        doc = res.scalar_one_or_none()
        if doc and doc.normalized_text:
            doc_texts[doc_id] = doc.normalized_text
    return {
        "reviewId": review.id,
        "currentSeq": review.last_seq,
        "findings": [f.model_dump(by_alias=True) for f in findings],
        "documents": doc_texts,
    }
