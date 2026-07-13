import logging
import re
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.modules.auth.models import User, UserOrganization
from app.modules.auth.schemas import UserRegister
from app.modules.auth.security import (
    ALGORITHM,
    create_verification_token,
    get_password_hash,
    verify_password,
)
from app.modules.organizations.models import Organization
from app.services.email.email_service import email_service

logger = logging.getLogger("epmp.auth_service")


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = (
        select(User)
        .where(User.email == email)
        .options(
            selectinload(User.organizations).selectinload(UserOrganization.organization)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, register_data: UserRegister) -> User:
    existing_user = await get_user_by_email(db, register_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    org_slug = slugify(register_data.organization_name)
    stmt = select(Organization).where(Organization.slug == org_slug)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        import uuid

        org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(name=register_data.organization_name, slug=org_slug)
    db.add(org)
    await db.flush()

    hashed_pwd = get_password_hash(register_data.password)
    user = User(
        email=register_data.email,
        hashed_password=hashed_pwd,
        full_name=register_data.full_name,
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()

    user_org = UserOrganization(
        user_id=user.id, organization_id=org.id, role_name="owner"
    )
    db.add(user_org)
    await db.commit()

    # Send verification email
    v_token = create_verification_token(user.email)
    email_service.send_verification_email(user.email, v_token)
    logger.info(f"Registered user {user.email}. Verification email dispatched.")

    # Load relationships for serialization
    stmt_user = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.organizations).selectinload(UserOrganization.organization)
        )
    )
    result_user = await db.execute(stmt_user)
    return result_user.scalar_one()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None

    # Check lockout status
    if user.locked_until and user.locked_until > datetime.now(UTC):
        logger.warning(f"Auth attempt on locked account: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked. Try again after {user.locked_until.strftime('%H:%M:%S')} UTC.",
        )

    # Validate password
    if not verify_password(password, user.hashed_password):
        # Track lockout attempt
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
            user.account_status = "locked"
            logger.critical(f"Account locked due to brute force: {email}")
        await db.commit()
        return None

    # Success, reset attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.account_status = "active"
    user.last_login_at = datetime.now(UTC)
    user.login_count += 1
    await db.commit()
    return user


async def verify_user_email(db: AsyncSession, token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            return False
        email = payload.get("sub")
        if not email:
            return False
    except (jwt.PyJWTError, ValueError):
        return False

    user = await get_user_by_email(db, email)
    if not user:
        return False

    if not user.is_verified:
        user.is_verified = True
        await db.commit()
        logger.info(f"Verified user email: {email}")
    return True


async def process_password_reset_request(db: AsyncSession, email: str) -> None:
    user = await get_user_by_email(db, email)
    if not user:
        # Prevent email enumeration attacks by silently returning
        logger.warning(f"Password reset requested for non-existent account: {email}")
        return

    from app.modules.auth.security import create_reset_token

    token = create_reset_token(email)
    email_service.send_reset_password_email(email, token)


async def execute_password_reset(
    db: AsyncSession, token: str, new_password: str
) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return False
        email = payload.get("sub")
        if not email:
            return False
    except (jwt.PyJWTError, ValueError):
        return False

    user = await get_user_by_email(db, email)
    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.account_status = "active"
    await db.commit()
    logger.info(f"Successfully reset password for user: {email}")
    return True


async def handle_google_user_provisioning(db: AsyncSession, profile: dict) -> User:
    email = profile.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google profile must provide a verified email address.",
        )

    user = await get_user_by_email(db, email)
    if user:
        # Link accounts if email matches but provider was email
        if user.provider != "google":
            user.provider = "google"
            user.profile_image_url = profile.get("picture", user.profile_image_url)
            user.is_verified = True  # Verified by Google OAuth
            await db.commit()
            logger.info(f"Linked existing email {email} with Google provider.")
        return user

    # Create new user & organization workspace
    full_name = profile.get("name", "Google User")
    org_name = f"{full_name}'s Workspace"
    org_slug = slugify(org_name)

    # Ensure unique slug
    stmt = select(Organization).where(Organization.slug == org_slug)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        import uuid

        org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(name=org_name, slug=org_slug)
    db.add(org)
    await db.flush()

    # Create randomized password block since they login via OAuth
    import secrets

    random_password = secrets.token_urlsafe(32)

    user = User(
        email=email,
        hashed_password=get_password_hash(random_password),
        full_name=full_name,
        provider="google",
        profile_image_url=profile.get("picture"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()

    user_org = UserOrganization(
        user_id=user.id, organization_id=org.id, role_name="owner"
    )
    db.add(user_org)
    await db.commit()

    logger.info(f"Provisioned new user account via Google login: {email}")

    # Load relationships
    stmt_user = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.organizations).selectinload(UserOrganization.organization)
        )
    )
    result_user = await db.execute(stmt_user)
    return result_user.scalar_one()
