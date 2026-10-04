from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, current_user
from complibot.db.models import ProjectMember
from complibot.db.session import get_db
from complibot.exceptions import Forbidden, NotFound
from complibot.schemas import ProjectRole


class ProjectAccess:
    def __init__(self, role: ProjectRole) -> None:
        self.role = role


async def require_project_role(
    project_id: str,
    min_role: ProjectRole,
    user: AuthUser = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectAccess:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.tenant_id == user.tenant_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise NotFound()
    role = member.role
    order = {"viewer": 0, "reviewer": 1, "owner": 2}
    if order[role] < order[min_role]:
        raise Forbidden()
    return ProjectAccess(role=role)  # type: ignore[arg-type]
