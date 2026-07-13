import secrets
import uuid
from datetime import datetime, timedelta, UTC
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.invitations.models import Invitation
from app.modules.invitations.schemas import InvitationCreate
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.auth.models import Role, User
from app.modules.audit_logs.services import AuditLogService
from app.services.email.email_service import email_service

class InvitationService:
    @staticmethod
    async def create_invitation(
        db: AsyncSession, org_id: uuid.UUID, data: InvitationCreate, sender_id: uuid.UUID
    ) -> Invitation:
        # Check active org
        org_stmt = select(Organization).where(Organization.id == org_id, Organization.is_deleted == False)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        # Check existing member
        member_stmt = select(OrganizationMember).join(User).where(
            OrganizationMember.organization_id == org_id,
            User.email == data.email
        )
        member_res = await db.execute(member_stmt)
        if member_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization."
            )

        # Check existing pending invitation
        inv_stmt = select(Invitation).where(
            Invitation.organization_id == org_id,
            Invitation.email == data.email,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.utcnow()
        )
        inv_res = await db.execute(inv_stmt)
        if inv_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pending invitation already exists for this email address."
            )

        # Get role
        role_stmt = select(Role).where(Role.name == data.role_name)
        role_res = await db.execute(role_stmt)
        role = role_res.scalar_one_or_none()
        role_id = role.id if role else None
        role_name = role.name if role else "Viewer"

        # Generate token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = Invitation(
            organization_id=org_id,
            email=data.email,
            role_id=role_id,
            role_name=role_name,
            token=token,
            status="pending",
            expires_at=expires_at,
            created_by_id=sender_id
        )
        db.add(invitation)
        await db.commit()

        email_service.send_invitation_email(data.email, org.name, token)

        await AuditLogService.log_event(
            db=db,
            user_id=sender_id,
            organization_id=org_id,
            action="invitation:create",
            resource_type="invitation",
            resource_id=str(invitation.id),
            details={"email": data.email, "role": role_name}
        )

        return invitation

    @staticmethod
    async def cancel_invitation(db: AsyncSession, invitation_id: uuid.UUID, canceller_id: uuid.UUID) -> None:
        stmt = select(Invitation).where(Invitation.id == invitation_id)
        res = await db.execute(stmt)
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

        invitation.status = "cancelled"
        invitation.updated_by_id = canceller_id
        invitation.updated_at = datetime.utcnow()
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=canceller_id,
            organization_id=invitation.organization_id,
            action="invitation:cancel",
            resource_type="invitation",
            resource_id=str(invitation.id)
        )

    @staticmethod
    async def resend_invitation(db: AsyncSession, invitation_id: uuid.UUID, sender_id: uuid.UUID) -> Invitation:
        stmt = select(Invitation).where(Invitation.id == invitation_id)
        res = await db.execute(stmt)
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

        org = await db.get(Organization, invitation.organization_id)

        invitation.token = secrets.token_urlsafe(32)
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation.status = "pending"
        invitation.updated_by_id = sender_id
        invitation.updated_at = datetime.utcnow()
        await db.commit()

        email_service.send_invitation_email(invitation.email, org.name, invitation.token)

        await AuditLogService.log_event(
            db=db,
            user_id=sender_id,
            organization_id=invitation.organization_id,
            action="invitation:resend",
            resource_type="invitation",
            resource_id=str(invitation.id)
        )
        return invitation

    @staticmethod
    async def accept_invitation(db: AsyncSession, token: str, user_id: uuid.UUID) -> None:
        stmt = select(Invitation).where(Invitation.token == token)
        res = await db.execute(stmt)
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token.")

        if invitation.status != "pending" or invitation.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is expired, cancelled, or already accepted."
            )

        # Get User details to ensure correct mapping
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Verify email matches invitation email
        if user.email.lower() != invitation.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authenticated user's email does not match invitation email."
            )

        # Create membership
        member = OrganizationMember(
            user_id=user_id,
            organization_id=invitation.organization_id,
            role_id=invitation.role_id,
            role_name=invitation.role_name,
            invitation_status="accepted",
            joined_at=datetime.utcnow()
        )
        db.add(member)
        invitation.status = "accepted"
        invitation.updated_at = datetime.utcnow()
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=user_id,
            organization_id=invitation.organization_id,
            action="invitation:accept",
            resource_type="invitation",
            resource_id=str(invitation.id)
        )

    @staticmethod
    async def reject_invitation(db: AsyncSession, token: str, user_id: uuid.UUID) -> None:
        stmt = select(Invitation).where(Invitation.token == token)
        res = await db.execute(stmt)
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token.")

        if invitation.status != "pending" or invitation.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is expired or already processed."
            )

        invitation.status = "rejected"
        invitation.updated_at = datetime.utcnow()
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=user_id,
            organization_id=invitation.organization_id,
            action="invitation:reject",
            resource_type="invitation",
            resource_id=str(invitation.id)
        )

    @staticmethod
    async def list_invitations(
        db: AsyncSession, org_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Invitation], int]:
        stmt = select(Invitation).where(Invitation.organization_id == org_id)
        res_all = await db.execute(stmt)
        all_invs = res_all.scalars().all()
        paginated = all_invs[skip : skip + limit]
        return list(paginated), len(all_invs)
