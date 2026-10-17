import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, create_dev_token, current_user
from complibot.config import get_settings
from complibot.db.models import Tenant, User
from complibot.db.session import get_db
from complibot.exceptions import Forbidden
from complibot.ids import new_tenant_id, new_user_id
from complibot.schemas import DevLoginIn, DevLoginOut

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_LOGIN_WINDOW_SEC = 60
_LOGIN_MAX_PER_WINDOW = 20
_login_attempts: dict[str, list[float]] = defaultdict(list)


def _rate_limit_client(ip: str) -> None:
    now = time.time()
    window = [t for t in _login_attempts[ip] if now - t < _LOGIN_WINDOW_SEC]
    _login_attempts[ip] = window
    if len(window) >= _LOGIN_MAX_PER_WINDOW:
        raise Forbidden("Too many login attempts; try again later")
    _login_attempts[ip].append(now)


@router.post("/dev-login", response_model=DevLoginOut)
async def dev_login(
    body: DevLoginIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DevLoginOut:
    settings = get_settings()
    if not settings.dev_login_enabled or settings.app_env not in ("local", "demo"):
        raise Forbidden("Dev login disabled")
    client_ip = request.client.host if request.client else "unknown"
    _rate_limit_client(client_ip)
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
