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
from app.modules.organizations.models import Organization

# Token URL points to the login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
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


async def get_current_organization(
    request: Request, current_user: User = Depends(get_current_active_user)
) -> Organization:
    # 1. Look for organization ID in header
    org_id_str = request.headers.get("X-Organization-ID")

    if not org_id_str:
        # Fallback to the first organization membership if header is missing
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

    # Verify membership
    for user_org in current_user.organizations:
        if user_org.organization_id == org_uuid:
            return user_org.organization

    # If the user is active but doesn't belong to the requested organization, deny access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access to this organization's data is denied.",
    )
