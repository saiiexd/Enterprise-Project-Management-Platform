import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.dependencies import (
    get_current_active_user,
    get_current_organization,
    requires_permission,
)
from app.modules.auth.models import User
from app.modules.organizations.models import Organization
from app.modules.invitations.schemas import (
    InvitationCreate,
    InvitationOut,
    InvitationAccept,
    InvitationReject,
    InvitationPagination,
)
from app.modules.invitations.services import InvitationService

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("/", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    data: InvitationCreate,
    current_user: User = Depends(get_current_active_user),
    org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:invite")),
) -> Any:
    return await InvitationService.create_invitation(db, org.id, data, current_user.id)


@router.get("/", response_model=InvitationPagination)
async def list_invitations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:view")),
) -> Any:
    invitations, total = await InvitationService.list_invitations(db, org.id, skip, limit)
    return {"invitations": invitations, "total": total}


@router.post("/{invitation_id}/resend", response_model=InvitationOut)
async def resend_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:invite")),
) -> Any:
    return await InvitationService.resend_invitation(db, invitation_id, current_user.id)


@router.post("/{invitation_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:invite")),
) -> None:
    await InvitationService.cancel_invitation(db, invitation_id, current_user.id)


@router.post("/accept", status_code=status.HTTP_200_OK)
async def accept_invitation(
    data: InvitationAccept,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await InvitationService.accept_invitation(db, data.token, current_user.id)
    return {"message": "Invitation accepted successfully."}


@router.post("/reject", status_code=status.HTTP_200_OK)
async def reject_invitation(
    data: InvitationReject,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await InvitationService.reject_invitation(db, data.token, current_user.id)
    return {"message": "Invitation rejected successfully."}
