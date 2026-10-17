import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.auth.jwt import AuthUser, create_dev_token, current_user
from complibot.auth.passwords import hash_password, validate_password_strength, verify_password
from complibot.config import get_settings
from complibot.db.models import Tenant, User
from complibot.db.session import get_db
from complibot.exceptions import Conflict, Forbidden, TooManyRequests, Unauthorized
from complibot.ids import new_tenant_id, new_user_id
from complibot.schemas import DevLoginIn, DevLoginOut, LoginIn, RegisterIn

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_LOGIN_WINDOW_SEC = 60
_LOGIN_MAX_PER_WINDOW = 20
_login_attempts: dict[str, list[float]] = {}


def _rate_limit_client(ip: str) -> None:
    now = time.monotonic()
    for key in [k for k, ts in _login_attempts.items() if now - ts[-1] >= _LOGIN_WINDOW_SEC]:
        del _login_attempts[key]
    window = [t for t in _login_attempts.get(ip, []) if now - t < _LOGIN_WINDOW_SEC]
    if len(window) >= _LOGIN_MAX_PER_WINDOW:
        _login_attempts[ip] = window
        raise TooManyRequests("Too many login attempts; try again later")
    window.append(now)
    _login_attempts[ip] = window


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def _provision_user(
    db: AsyncSession,
    *,
    email: str,
    name: str,
    password_hash: str | None,
) -> User:
    tenant = Tenant(id=new_tenant_id(), name=f"{name}'s organization")
    db.add(tenant)
    user = User(
        id=new_user_id(),
        tenant_id=tenant.id,
        email=email,
        name=name,
        password_hash=password_hash,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _issue_token(user: User) -> DevLoginOut:
    token = create_dev_token(user.id, user.tenant_id, user.email, user.name)
    return DevLoginOut(access_token=token, user=AuthUser(user).to_out())


@router.post("/register", response_model=DevLoginOut)
async def register(
    body: RegisterIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DevLoginOut:
    _rate_limit_client(_client_ip(request))
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise Forbidden("Invalid email")
    pwd_err = validate_password_strength(body.password)
    if pwd_err:
        raise Forbidden(pwd_err)
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise Conflict("An account with this email already exists")
    name = (body.name or email.split("@")[0])[:200]
    user = await _provision_user(
        db,
        email=email,
        name=name,
        password_hash=hash_password(body.password),
    )
    return _issue_token(user)


@router.post("/login", response_model=DevLoginOut)
async def login(
    body: LoginIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DevLoginOut:
    _rate_limit_client(_client_ip(request))
    email = body.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise Unauthorized()
    return _issue_token(user)


@router.post("/dev-login", response_model=DevLoginOut)
async def dev_login(
    body: DevLoginIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DevLoginOut:
    settings = get_settings()
    if not settings.dev_login_enabled or settings.app_env not in ("local", "demo"):
        raise Forbidden("Dev login disabled")
    _rate_limit_client(_client_ip(request))
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None:
        user = await _provision_user(
            db,
            email=body.email,
            name=body.name,
            password_hash=None,
        )
    return _issue_token(user)


@router.get("/me")
async def me(user: AuthUser = Depends(current_user)) -> dict:
    return user.to_out().model_dump(by_alias=True)
