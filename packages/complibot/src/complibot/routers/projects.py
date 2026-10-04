from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, current_user
from complibot.auth.roles import require_project_role
from complibot.db.models import Document, Project, ProjectMember, Review
from complibot.db.session import get_db
from complibot.exceptions import BadRequest
from complibot.ids import new_id, new_document_id, new_project_id, new_review_id
from complibot.schemas import ProjectCreate, ProjectOut, ReviewCreate, ReviewOut
from complibot.services.queue import dispatch_review_job
from complibot.services.demo import load_sample_contract
from complibot.config import get_settings

router = APIRouter(prefix="/v1/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectOut]:
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id, Project.tenant_id == user.tenant_id)
    )
    projects = result.scalars().all()
    return [
        ProjectOut(
            id=p.id,
            tenant_id=p.tenant_id,
            name=p.name,
            framework_codes=p.framework_codes,
            created_by=p.created_by,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.post("", response_model=ProjectOut)
async def create_project(
    body: ProjectCreate,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    if not body.framework_codes:
        raise BadRequest("Select at least one framework")
    project = Project(
        id=new_project_id(),
        tenant_id=user.tenant_id,
        name=body.name,
        framework_codes=list(body.framework_codes),
        created_by=user.id,
        created_at=datetime.now(UTC),
    )
    db.add(project)
    member = ProjectMember(
        id=new_id("mbr"),
        tenant_id=user.tenant_id,
        project_id=project.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)
    await db.commit()
    await db.refresh(project)
    return ProjectOut(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        framework_codes=project.framework_codes,
        created_by=project.created_by,
        created_at=project.created_at,
    )


@router.post("/{project_id}/demo", response_model=ReviewOut)
async def try_sample_contract(
    project_id: str,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewOut:
    await require_project_role(project_id, "reviewer", user, db)
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == user.tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        from complibot.exceptions import NotFound

        raise NotFound()
    text = load_sample_contract()
    doc = Document(
        id=new_document_id(),
        tenant_id=user.tenant_id,
        project_id=project_id,
        filename="synthetic-dpa.txt",
        mime_type="text/plain",
        s3_key=f"{user.tenant_id}/{project_id}/synthetic-dpa.txt",
        status="parsed",
        normalized_text=text,
        page_count=1,
        uploaded_by=user.id,
        created_at=datetime.now(UTC),
    )
    db.add(doc)
    review = Review(
        id=new_review_id(),
        tenant_id=user.tenant_id,
        project_id=project_id,
        document_ids=[doc.id],
        framework_codes=project.framework_codes,
        status="queued",
        last_seq=0,
        created_at=datetime.now(UTC),
    )
    db.add(review)
    await db.commit()
    settings = get_settings()
    await dispatch_review_job(
        settings,
        {"reviewId": review.id, "tenantId": user.tenant_id, "projectId": project_id},
    )
    return ReviewOut(
        id=review.id,
        project_id=review.project_id,
        document_ids=review.document_ids,
        framework_codes=review.framework_codes,
        status=review.status,
        last_seq=review.last_seq,
        created_at=review.created_at,
    )


@router.post("/{project_id}/reviews", response_model=ReviewOut)
async def start_review(
    project_id: str,
    body: ReviewCreate,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewOut:
    await require_project_role(project_id, "reviewer", user, db)
    if not body.document_ids:
        raise BadRequest("document_ids required")
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == user.tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        from complibot.exceptions import NotFound

        raise NotFound()
    for doc_id in body.document_ids:
        doc_res = await db.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.project_id == project_id,
                Document.tenant_id == user.tenant_id,
                Document.status == "parsed",
            )
        )
        if doc_res.scalar_one_or_none() is None:
            raise BadRequest(f"Document {doc_id} is not ready")
    review = Review(
        id=new_review_id(),
        tenant_id=user.tenant_id,
        project_id=project_id,
        document_ids=body.document_ids,
        framework_codes=project.framework_codes,
        status="queued",
        last_seq=0,
        created_at=datetime.now(UTC),
    )
    db.add(review)
    await db.commit()
    settings = get_settings()
    await dispatch_review_job(
        settings,
        {"reviewId": review.id, "tenantId": user.tenant_id, "projectId": project_id},
    )
    return ReviewOut(
        id=review.id,
        project_id=review.project_id,
        document_ids=review.document_ids,
        framework_codes=review.framework_codes,
        status=review.status,
        last_seq=review.last_seq,
        created_at=review.created_at,
    )
