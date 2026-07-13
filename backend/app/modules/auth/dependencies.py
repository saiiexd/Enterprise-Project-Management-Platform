import uuid

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.security import ALGORITHM
from app.modules.auth.services import get_user_by_email
from app.modules.organizations.models import Organization, OrganizationMember
from app.services.redis_service import redis_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")



async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Verify token is not blacklisted in Redis
    if await redis_service.is_token_blacklisted(token):
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type", "")
        if token_type != "access":
            raise credentials_exception
        email: str = payload.get("sub", "")
        if not email:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = await get_user_by_email(db, email)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address to access this feature.",
        )
    return current_user


async def get_current_organization(
    request: Request, current_user: User = Depends(get_current_active_user)
) -> Organization:
    org_id_str = request.headers.get("X-Organization-ID")

    if not org_id_str:
        if not current_user.organizations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with any organization. Please join or create one.",
            )
        return current_user.organizations[0].organization

    try:
        org_uuid = uuid.UUID(org_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Organization-ID header format. Must be UUID.",
        )

    for user_org in current_user.organizations:
        if user_org.organization_id == org_uuid:
            return user_org.organization

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access to this organization's data is denied.",
    )


# Reusable permission dependency creator
def requires_permission(permission_name: str):
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        org: Organization = Depends(get_current_organization),
    ) -> None:
        if current_user.is_superuser:
            return

        for user_org in current_user.organizations:
            if user_org.organization_id == org.id:
                if user_org.role_name.lower() in ("owner", "organization owner"):
                    return
                # Check actual role permission tables
                if user_org.role and user_org.role.permissions:
                    for perm in user_org.role.permissions:
                        if perm.name == permission_name:
                            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have the required permission: {permission_name}",
        )

    return permission_dependency


# Rate limit dependency creator
def check_rate_limit(limit: int, window: int):
    async def rate_limiter(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"{client_ip}:{path}"
        if not await redis_service.rate_limit_check(key, limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
            )

    return rate_limiter
