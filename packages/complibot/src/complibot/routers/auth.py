from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, create_dev_token, current_user
from complibot.config import get_settings
from complibot.db.models import Tenant, User
from complibot.db.session import get_db
from complibot.ids import new_tenant_id, new_user_id
from complibot.schemas import DevLoginIn, DevLoginOut

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/dev-login", response_model=DevLoginOut)
async def dev_login(body: DevLoginIn, db: AsyncSession = Depends(get_db)) -> DevLoginOut:
    settings = get_settings()
    if settings.app_env not in ("local", "demo"):
        from complibot.exceptions import Forbidden

        raise Forbidden("Dev login disabled")
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None:
        tenant = Tenant(id=new_tenant_id(), name="Demo Org")
        db.add(tenant)
        user = User(
            id=new_user_id(),
            tenant_id=tenant.id,
            email=body.email,
            name=body.name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_dev_token(user.id, user.tenant_id, user.email, user.name)
    return DevLoginOut(access_token=token, user=AuthUser(user).to_out())


@router.get("/me")
async def me(user: AuthUser = Depends(current_user)) -> dict:
    return user.to_out().model_dump(by_alias=True)
