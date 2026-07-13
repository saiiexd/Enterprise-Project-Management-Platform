import uuid
import re
from datetime import datetime, UTC
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import HTTPException, status
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.organizations.schemas import OrganizationCreate, OrganizationUpdate
from app.modules.auth.models import Role, User
from app.modules.audit_logs.services import AuditLogService

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s

class OrganizationService:
    @staticmethod
    async def create_organization(
        db: AsyncSession, data: OrganizationCreate, creator_id: uuid.UUID
    ) -> Organization:
        slug = data.slug or slugify(data.name)
        # Check slug collision
        stmt = select(Organization).where(Organization.slug == slug)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        default_settings = {
            "timezone": "UTC",
            "locale": "en",
            "working_days": [1, 2, 3, 4, 5],
            "business_hours": {"start": "09:00", "end": "17:00"},
            "branding": {"primary_color": "#4F46E5", "logo_url": data.logo_url}
        }
        if data.settings:
            default_settings.update(data.settings)

        org = Organization(
            name=data.name,
            slug=slug,
            description=data.description,
            logo_url=data.logo_url,
            status="active",
            subscription_tier="free",
            subscription_status="active",
            owner_id=creator_id,
            settings=default_settings,
            created_by_id=creator_id
        )
        db.add(org)
        await db.flush()

        # Fetch Owner Role
        stmt_role = select(Role).where(Role.name == "Organization Owner")
        res_role = await db.execute(stmt_role)
        owner_role = res_role.scalar_one_or_none()
        role_id = owner_role.id if owner_role else None
        role_name = owner_role.name if owner_role else "Organization Owner"

        member = OrganizationMember(
            user_id=creator_id,
            organization_id=org.id,
            role_id=role_id,
            role_name=role_name,
            invitation_status="accepted",
            joined_at=datetime.utcnow()
        )
        db.add(member)
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=creator_id,
            organization_id=org.id,
            action="organization:create",
            resource_type="organization",
            resource_id=str(org.id),
            details={"name": org.name, "slug": org.slug}
        )

        return org

    @staticmethod
    async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization | None:
        stmt = select(Organization).where(
            Organization.id == org_id, Organization.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_user_organizations(db: AsyncSession, user_id: uuid.UUID) -> list[Organization]:
        stmt = (
            select(Organization)
            .join(OrganizationMember)
            .where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.invitation_status == "accepted",
                Organization.is_deleted == False
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_organization(
        db: AsyncSession, org_id: uuid.UUID, data: OrganizationUpdate, updater_id: uuid.UUID
    ) -> Organization:
        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(org, k, v)
        org.updated_by_id = updater_id
        org.updated_at = datetime.utcnow()
        
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=updater_id,
            organization_id=org.id,
            action="organization:update",
            resource_type="organization",
            resource_id=str(org.id),
            details=update_dict
        )
        return org

    @staticmethod
    async def update_settings(
        db: AsyncSession, org_id: uuid.UUID, settings_dict: dict, updater_id: uuid.UUID
    ) -> Organization:
        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        current_settings = org.settings or {}
        current_settings.update(settings_dict)
        org.settings = current_settings
        org.updated_by_id = updater_id
        org.updated_at = datetime.utcnow()

        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=updater_id,
            organization_id=org.id,
            action="organization:settings_update",
            resource_type="organization",
            resource_id=str(org.id),
            details=settings_dict
        )
        return org

    @staticmethod
    async def delete_organization(db: AsyncSession, org_id: uuid.UUID, deleter_id: uuid.UUID) -> None:
        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        org.is_deleted = True
        org.deleted_at = datetime.utcnow()
        org.updated_by_id = deleter_id
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=deleter_id,
            organization_id=org.id,
            action="organization:delete",
            resource_type="organization",
            resource_id=str(org.id)
        )

    @staticmethod
    async def list_members(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[dict], int]:
        stmt = (
            select(OrganizationMember)
            .join(User)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.is_deleted == False
            )
        )
        if search:
            stmt = stmt.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )

        # Count total
        # We can compile count via standard func.count or len
        res_all = await db.execute(stmt.options(selectinload(OrganizationMember.user)))
        all_members = res_all.scalars().all()
        
        # Paginate manually or in SQL
        paginated = all_members[skip : skip + limit]

        out = []
        for m in paginated:
            out.append({
                "user_id": m.user_id,
                "email": m.user.email,
                "full_name": m.user.full_name,
                "role_name": m.role_name,
                "invitation_status": m.invitation_status,
                "joined_at": m.joined_at
            })
        return out, len(all_members)

    @staticmethod
    async def update_member_role(
        db: AsyncSession, org_id: uuid.UUID, target_user_id: uuid.UUID, role_name: str, updater_id: uuid.UUID
    ) -> None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target_user_id
        )
        res = await db.execute(stmt)
        member = res.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        stmt_role = select(Role).where(Role.name == role_name)
        res_role = await db.execute(stmt_role)
        role = res_role.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")

        member.role_id = role.id
        member.role_name = role.name
        member.updated_by_id = updater_id
        member.updated_at = datetime.utcnow()
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=updater_id,
            organization_id=org_id,
            action="member:role_update",
            resource_type="member",
            resource_id=str(target_user_id),
            details={"role_name": role_name}
        )

    @staticmethod
    async def remove_member(
        db: AsyncSession, org_id: uuid.UUID, target_user_id: uuid.UUID, remover_id: uuid.UUID
    ) -> None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target_user_id
        )
        res = await db.execute(stmt)
        member = res.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        await db.delete(member)
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=remover_id,
            organization_id=org_id,
            action="member:remove",
            resource_type="member",
            resource_id=str(target_user_id)
        )
