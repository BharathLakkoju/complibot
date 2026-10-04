from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from complibot.config import get_settings
from complibot.db.models import User
from complibot.db.session import get_db
from complibot.exceptions import Forbidden, NotFound
from complibot.schemas import UserOut


class AuthUser:
    def __init__(self, user: User) -> None:
        self.id = user.id
        self.tenant_id = user.tenant_id
        self.email = user.email
        self.name = user.name

    def to_out(self) -> UserOut:
        return UserOut(id=self.id, email=self.email, name=self.name)


def create_dev_token(user_id: str, tenant_id: str, email: str, name: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "name": name,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(hours=12),
    }
    return jwt.encode(payload, settings.dev_auth_secret, algorithm="HS256")


async def current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise Forbidden("Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.dev_auth_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError:
        raise Forbidden("Invalid token") from None
    user_id = str(payload.get("sub", ""))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFound("User not found")
    return AuthUser(user)
