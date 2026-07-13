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
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
    OrganizationSettingsUpdate,
    OrganizationMemberOut,
)
from app.modules.organizations.services import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await OrganizationService.create_organization(db, data, current_user.id)


@router.get("/", response_model=list[OrganizationOut])
async def list_organizations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await OrganizationService.list_user_organizations(db, current_user.id)


@router.get("/active", response_model=OrganizationOut)
async def get_active_organization(
    org: Organization = Depends(get_current_organization),
) -> Any:
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("org:view")),
) -> Any:
    org = await OrganizationService.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: uuid.UUID,
    data: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("org:update")),
) -> Any:
    return await OrganizationService.update_organization(db, org_id, data, current_user.id)


@router.put("/{org_id}/settings", response_model=OrganizationOut)
async def update_organization_settings(
    org_id: uuid.UUID,
    data: OrganizationSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("org:update")),
) -> Any:
    return await OrganizationService.update_settings(db, org_id, data.model_dump(), current_user.id)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("org:delete")),
) -> None:
    await OrganizationService.delete_organization(db, org_id, current_user.id)


@router.get("/{org_id}/members")
async def list_organization_members(
    org_id: uuid.UUID,
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:view")),
) -> Any:
    members, total = await OrganizationService.list_members(db, org_id, search, skip, limit)
    return {"members": members, "total": total}


@router.put("/{org_id}/members/{user_id}/role", status_code=status.HTTP_200_OK)
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    role_name: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:update_role")),
) -> Any:
    await OrganizationService.update_member_role(db, org_id, user_id, role_name, current_user.id)
    return {"message": "Member role updated successfully."}


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("member:remove")),
) -> None:
    await OrganizationService.remove_member(db, org_id, user_id, current_user.id)
