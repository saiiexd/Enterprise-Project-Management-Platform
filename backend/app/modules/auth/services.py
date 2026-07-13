import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import User, UserOrganization
from app.modules.auth.schemas import UserRegister
from app.modules.auth.security import get_password_hash, verify_password
from app.modules.organizations.models import Organization


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
    # Check if user already exists
    existing_user = await get_user_by_email(db, register_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Generate slug for organization name
    org_slug = slugify(register_data.organization_name)

    # Verify slug uniqueness or adjust
    stmt = select(Organization).where(Organization.slug == org_slug)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        # Append some random characters or counter if not unique
        import uuid

        org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"

    # Create Organization
    org = Organization(name=register_data.organization_name, slug=org_slug)
    db.add(org)
    await db.flush()  # populate org.id

    # Create User
    hashed_pwd = get_password_hash(register_data.password)
    user = User(
        email=register_data.email,
        hashed_password=hashed_pwd,
        full_name=register_data.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()  # populate user.id

    # Associate User and Organization as Owner
    user_org = UserOrganization(user_id=user.id, organization_id=org.id, role="owner")
    db.add(user_org)
    await db.commit()

    # Load relationships for serialization
    stmt_user = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.organizations).selectinload(
                UserOrganization.organization
            )
        )
    )
    result_user = await db.execute(stmt_user)
    return result_user.scalar_one()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
